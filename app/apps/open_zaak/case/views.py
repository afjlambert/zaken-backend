from rest_framework import viewsets

from apps.open_zaak.case.serializers import CaseSerializer
from apps.open_zaak.case.wrappers import Case
from apps.open_zaak.view_helpers import retrieve_helper, list_helper, create_helper, destroy_helper, update_helper


class CaseViewSet(viewsets.ViewSet):
    serializer_class = CaseSerializer
    data_wrapper = Case
    lookup_field = 'uuid'

    def retrieve(self, request, uuid):
        return retrieve_helper(self, uuid)

    def list(self, request):
        return list_helper(self)

    def create(self, request):
        return create_helper(self, request.data)

    def destroy(self, request, uuid):
        return destroy_helper(self, uuid)

    def update(self, request, uuid):
        return update_helper(self, uuid, request.data)