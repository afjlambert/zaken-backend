import logging

from apps.addresses.utils import search
from apps.camunda.models import CamundaProcess
from apps.camunda.serializers import CamundaProcessSerializer, CamundaTaskSerializer
from apps.camunda.services import CamundaService
from apps.cases.mock import mock
from apps.cases.models import Case, CaseState, CaseTeam
from apps.cases.serializers import (
    CamundaStartProcessSerializer,
    CaseCreateUpdateSerializer,
    CaseReasonSerializer,
    CaseSerializer,
    CaseStateSerializer,
    CaseStateTypeSerializer,
    CaseTeamSerializer,
    PushCaseStateSerializer,
)
from apps.cases.swagger_parameters import date as date_parameter
from apps.cases.swagger_parameters import no_pagination as no_pagination_parameter
from apps.cases.swagger_parameters import open_cases as open_cases_parameter
from apps.cases.swagger_parameters import open_status as open_status_parameter
from apps.cases.swagger_parameters import postal_code as postal_code_parameter
from apps.cases.swagger_parameters import reason as reason_parameter
from apps.cases.swagger_parameters import start_date as start_date_parameter
from apps.cases.swagger_parameters import street_name as street_name_parameter
from apps.cases.swagger_parameters import street_number as street_number_parameter
from apps.cases.swagger_parameters import suffix as suffix_parameter
from apps.cases.swagger_parameters import team as team_parameter
from apps.decisions.serializers import DecisionTypeSerializer
from apps.events.mixins import CaseEventsMixin
from apps.schedules.serializers import TeamScheduleTypesSerializer
from apps.summons.serializers import SummonTypeSerializer
from apps.users.auth_apps import TopKeyAuth
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from drf_spectacular.utils import extend_schema
from keycloak_oidc.drf.permissions import IsInAuthorizedRealm
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class CaseStateViewSet(viewsets.ViewSet):
    """
    Pushes the case state
    """

    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = CaseStateSerializer
    queryset = CaseState.objects.all()

    @action(
        detail=True,
        url_path="update-from-top",
        methods=["post"],
        serializer_class=PushCaseStateSerializer,
    )
    def update_from_top(self, request, pk):
        logger.info("Receiving pushed state update")
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            logger.error("Serializer error: {serializer.errors}")
            raise APIException(f"Serializer error: {serializer.errors}")

        try:
            case_state = CaseState.objects.get(id=pk)
            case_state.users.clear()
            user_emails = data.get("user_emails", [])
            logger.info(f"Updating CaseState {len(user_emails)} users")
            user_model = get_user_model()

            for user_email in user_emails:
                user_object, _ = user_model.objects.get_or_create(email=user_email)
                case_state.users.add(user_object)
                logger.info("Added user to CaseState")

            return Response(CaseStateSerializer(case_state).data)
        except Exception as e:
            logger.error(f"Could not process push data: {e}")
            raise logger(f"Could not push data: {e}")


class CaseViewSet(
    CaseEventsMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = CaseSerializer
    queryset = Case.objects.all()

    def get_serializer_class(self, *args, **kwargs):
        if self.action in ["create", "update"]:
            return CaseCreateUpdateSerializer

        return self.serializer_class

    @extend_schema(
        parameters=[
            date_parameter,
            start_date_parameter,
            open_cases_parameter,
            team_parameter,
            reason_parameter,
            open_status_parameter,
            no_pagination_parameter,
        ],
        description="Case filter query parameters",
        responses={200: CaseSerializer(many=True)},
    )
    def list(self, request):
        date = request.GET.get(date_parameter.name, None)
        start_date = request.GET.get(start_date_parameter.name, None)
        open_cases = request.GET.get(open_cases_parameter.name, None)
        team = request.GET.get(team_parameter.name, None)
        reason = request.GET.get(reason_parameter.name, None)
        open_status = request.GET.get(open_status_parameter.name, None)
        no_pagination = request.GET.get(no_pagination_parameter.name, None)

        queryset = self.get_queryset()

        if date:
            queryset = queryset.filter(start_date=date)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if open_cases:
            open_cases = open_cases == "true"
            queryset = queryset.filter(end_date__isnull=open_cases)
        if team:
            queryset = queryset.filter(team=team)
        if reason:
            queryset = queryset.filter(reason=reason)
        if open_status:
            queryset = queryset.filter(
                case_states__end_date__isnull=True,
                case_states__status__name=open_status,
            )

        if no_pagination == "true":
            serializer = CaseSerializer(queryset, many=True)
            return Response(serializer.data)

        paginator = PageNumberPagination()
        context = paginator.paginate_queryset(queryset, request)
        serializer = CaseSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        parameters=[
            postal_code_parameter,
            street_number_parameter,
            street_name_parameter,
            suffix_parameter,
            team_parameter,
        ],
        description="Search query parameters",
        responses={200: CaseSerializer(many=True)},
        operation=None,
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        postal_code = request.GET.get(postal_code_parameter.name, None)
        street_name = request.GET.get(street_name_parameter.name, None)
        number = request.GET.get(street_number_parameter.name, None)
        suffix = request.GET.get(suffix_parameter.name, None)
        team = request.GET.get(team_parameter.name, None)

        if postal_code is None and street_name is None:
            return HttpResponseBadRequest(
                "A postal_code or street_name queryparameter should be provided"
            )
        if postal_code is not None and number is None:
            return HttpResponseBadRequest("number queryparameter is required")
        if street_name is not None and number is None:
            return HttpResponseBadRequest("number queryparameter is required")

        address_queryset = search(
            street_name=street_name,
            postal_code=postal_code,
            number=number,
            suffix=suffix,
        )

        cases = Case.objects.none()
        for address in address_queryset:
            cases = cases | address.cases.all()

        cases = cases.filter(end_date=None)

        if team:
            cases = cases.filter(team=team)

        paginator = PageNumberPagination()
        context = paginator.paginate_queryset(cases, request)
        serializer = CaseSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["post"], url_path="generate-mock")
    def mock_cases(self, request):
        try:
            assert (
                settings.DEBUG or settings.ENVIRONMENT == "acceptance"
            ), "Incorrect enviroment"
            mock()
        except Exception as e:
            return Response(data={"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        description="Get Camunda tasks for this Case",
        responses={status.HTTP_200_OK: CamundaTaskSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="tasks")
    def get_tasks(self, request, pk):
        case = self.get_object()
        camunda_tasks = []

        for camunda_id in case.camunda_ids:
            camunda_tasks.extend(
                CamundaService().get_all_tasks_by_instance_id(camunda_id)
            )
        # Camunda tasks can be an empty list or boolean. TODO: This should just be one datatype
        if camunda_tasks is False:
            return Response(
                "Camunda service is offline",
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = CamundaTaskSerializer(camunda_tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Get Camunda processes for this Case",
        responses={status.HTTP_200_OK: CamundaProcessSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="processes",
        methods=["get"],
        serializer_class=CamundaProcessSerializer,
    )
    def get_camunda_processes(self, request, pk):
        """
        Get camunda processes for this case. Currently this case detail linking
        does not do anything. This is future proofing this rest call so that we can
        show and not show processes based on the current state of the case
        (for example not show the summon/aanschrijving process when we are in visit state)
        """
        serializer = CamundaProcessSerializer(CamundaProcess.objects.all(), many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Start a process in Camunda",
    )
    @action(
        detail=True,
        url_path="processes/start",
        methods=["post"],
        serializer_class=CamundaStartProcessSerializer,
    )
    def start_process(self, request, pk):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            instance = data["camunda_process_id"]

            response = CamundaService().send_message(
                message_name=instance.camunda_message_name
            )

            if response:
                return Response(
                    data=f"Process has started {str(response.content)}",
                    status=status.HTTP_200_OK,
                )

        return Response(
            data="Camunda process has not started.",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class CaseTeamViewSet(ListAPIView, viewsets.ViewSet):
    permission_classes = [IsInAuthorizedRealm | TopKeyAuth]
    serializer_class = CaseTeamSerializer
    queryset = CaseTeam.objects.all()

    @extend_schema(
        description="Gets the reasons associated with the requested team",
        responses={status.HTTP_200_OK: CaseReasonSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="reasons",
        methods=["get"],
    )
    def reasons(self, request, pk):
        paginator = PageNumberPagination()
        team = self.get_object()
        query_set = team.reasons.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseReasonSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the SummonTypes associated with the given team",
        responses={status.HTTP_200_OK: SummonTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="summon-types",
        methods=["get"],
    )
    def summon_types(self, request, pk):
        paginator = PageNumberPagination()
        team = self.get_object()
        query_set = team.summon_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = SummonTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the DecisionTypes associated with the given team",
        responses={status.HTTP_200_OK: DecisionTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="decision-types",
        methods=["get"],
    )
    def decision_types(self, request, pk):
        paginator = PageNumberPagination()
        team = self.get_object()
        query_set = team.decision_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = DecisionTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        description="Gets the Scheduling Types associated with the given team",
        responses={status.HTTP_200_OK: TeamScheduleTypesSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="schedule-types",
        methods=["get"],
    )
    def schedule_types(self, request, pk):
        team = self.get_object()
        serializer = TeamScheduleTypesSerializer(team)
        return Response(serializer.data)

    @extend_schema(
        description="Gets the CaseStateTypes associated with the given team",
        responses={status.HTTP_200_OK: CaseStateTypeSerializer(many=True)},
    )
    @action(
        detail=True,
        url_path="state-types",
        methods=["get"],
    )
    def state_types(self, request, pk):
        paginator = PageNumberPagination()
        team = self.get_object()
        query_set = team.state_types.all()

        context = paginator.paginate_queryset(query_set, request)
        serializer = CaseStateTypeSerializer(context, many=True)

        return paginator.get_paginated_response(serializer.data)
