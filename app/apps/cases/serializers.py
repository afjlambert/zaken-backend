from apps.cases.models import Address, Case, CaseType, State, StateType
from rest_framework import serializers


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "bag_id",
            "id",
            "full_address",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "full_address",
        )
        read_only_fields = (
            "id",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "full_address",
        )
        extra_kwargs = {"bag_id": {"validators": []}}


class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = "__all__"
        read_only_fields = ("id",)
        extra_kwargs = {"name": {"validators": []}}


class CaseSerializer(serializers.ModelSerializer):
    case_type = CaseTypeSerializer(required=True)
    address = AddressSerializer(required=True)

    class Meta:
        model = Case
        fields = "__all__"

    def update(self, instance, validated_data):
        case_type_data = validated_data.pop("case_type", None)
        address_data = validated_data.pop("address", None)

        if case_type_data:
            case_type = CaseType.get(case_type_data.get("name"))
            instance.case_type = case_type

        if address_data:
            address = Address.get(address_data.get("bag_id"))
            instance.address = address

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance

    def create(self, validated_data):
        case_type_data = validated_data.pop("case_type")
        case_type = CaseType.get(case_type_data.get("name"))

        address_data = validated_data.pop("address")
        address = Address.get(address_data.get("bag_id"))

        case = Case.objects.create(
            **validated_data, case_type=case_type, address=address
        )

        return case


class StateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateType
        fields = "__all__"
        read_only_fields = ("id",)


class StateSerializer(serializers.ModelSerializer):
    state_type = StateTypeSerializer(required=True)
    case = CaseSerializer(required=True)

    class Meta:
        model = State
        fields = "__all__"
        read_only_fields = ("id",)


class FineSerializer(serializers.Serializer):
    identificatienummer = serializers.CharField(max_length=15)
    vorderingnummer = serializers.IntegerField()
    jaar = serializers.IntegerField(max_value=9999)
    soort_vordering = serializers.ChoiceField(choices=("PBF", "PBN", "PRV", "SOC"))
    omschrijving_soort_vordering = serializers.CharField(max_length=50)
    indicatie_publiekrechtelijk = serializers.ChoiceField(choices=("J", "N"))
    subjectnr = serializers.IntegerField(max_value=9999999999)
    opgemaaktenaam = serializers.CharField(max_length=4000)
    subjectnr_opdrachtgever = serializers.IntegerField()
    opgemaaktenaam_opdrachtgever = serializers.CharField(max_length=4000)
    runnr = serializers.IntegerField()
    omschrijving_run = serializers.CharField(max_length=40)
    code_runwijze = serializers.CharField(max_length=3)
    omschrijving_runwijze = serializers.CharField(max_length=40)
    dagtekening = serializers.DateTimeField()
    vervaldatum = serializers.DateTimeField()
    indicatie_combi_dwangbevel = serializers.ChoiceField(choices=("J", "N", "O"))
    notatekst = serializers.CharField(max_length=2000, allow_null=True)
    omschrijving = serializers.CharField(max_length=100, allow_null=True)
    invorderingstatus = serializers.CharField()
    indicatie_bet_hern_bevel = serializers.ChoiceField(choices=("J", "N"))
    landcode = serializers.CharField(max_length="3", allow_null=True)
    kenteken = serializers.CharField(allow_null=True)
    bonnummer = serializers.CharField(allow_null=True)
    bedrag_opgelegd = serializers.DecimalField(max_digits=12, decimal_places=2)
    bedrag_open_post_incl_rente = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    totaalbedrag_open_kosten = serializers.DecimalField(max_digits=12, decimal_places=2)
    bedrag_open_rente = serializers.DecimalField(max_digits=12, decimal_places=2)
    reden_opschorting = serializers.CharField(max_length=4000, allow_null=True)
    omschrijving_1 = serializers.CharField(max_length=4000, allow_null=True)
    omschrijving_2 = serializers.CharField(max_length=4000, allow_null=True)


class FineListSerializer(serializers.Serializer):
    items = FineSerializer(required=True, many=True)