from django.contrib.auth.models import User

from django.utils import timezone
from django.db.models import Q

from rest_framework import serializers
from silrec.components.lookups.models import (
    CohortMetricsLkp,
    MachineLkp,
    ObjectiveLkp,
    OrganisationLkp,
    RegenerationMethodsLkp,
    RescheduleReasonsLkp,
    SpatialPrecisionLkp,
    SpeciesApiLkp,
    TaskLkp,
    TasksAttLkp,
    TreatmentStatusLkp,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']

class UserSerializerSimple(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "last_name", "first_name", "email", "full_name")

    def get_full_name(self, obj):
        return obj.get_full_name()



class CohortMetricsLkpSerializer(serializers.ModelSerializer):
    """Serializer for Cohort Metrics Lookup"""
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = CohortMetricsLkp
        fields = [
            'metric_id',
            'name',
            'definition',
            'rating',
            'rating_display',
            'value',
            'method',
            'reference',
            'version',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
            'effective_from',
            'effective_to',
            'is_active',
        ]
        read_only_fields = ['metric_id', 'created_on', 'created_by', 'updated_on', 'updated_by']

    def get_is_active(self, obj):
        return obj.effective_to is None


class MachineLkpSerializer(serializers.ModelSerializer):
    """Serializer for Machine Lookup"""
    felling_head_herbicide_display = serializers.SerializerMethodField()

    class Meta:
        model = MachineLkp
        fields = [
            'machine_id',
            'manufacturer',
            'model',
            'machine_type',
            'felling_head_model',
            'felling_head_herbicide_spray',
            'felling_head_herbicide_display',
        ]

    def get_felling_head_herbicide_display(self, obj):
        return "Yes" if obj.felling_head_herbicide_spray else "No"


class ObjectiveLkpSerializer(serializers.ModelSerializer):
    """Serializer for Objective Lookup"""
    cut_display = serializers.CharField(source='get_cut_display', read_only=True)
    is_active = serializers.SerializerMethodField()
    has_prescription = serializers.BooleanField(source='prescription', read_only=True)
    has_additional_attributes = serializers.BooleanField(source='addition_attribs', read_only=True)

    class Meta:
        model = ObjectiveLkp
        fields = [
            'obj_code',
            'description',
            'definition',
            'cut',
            'cut_display',
            'forest_type',
            'fmis_code',
            'resid_ba_ge15',
            'prescription',
            'has_prescription',
            'untreated_outcome',
            'auth_source',
            'record_stds',
            'addition_attribs',
            'has_additional_attributes',
            'type',
            'reference1_label',
            'reference2_label',
            'category1_label',
            'category2_label',
            'qty1_label',
            'qty2_label',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
            'effective_from',
            'effective_to',
            'authorised_by',
            'revoked_by',
            'is_active',
        ]
        read_only_fields = ['created_on', 'created_by', 'updated_on', 'updated_by']

    def get_is_active(self, obj):
        return obj.effective_to is None


class ObjectiveLkpDetailSerializer(ObjectiveLkpSerializer):
    """Detailed serializer for Objective Lookup with additional computed fields"""
    attribute_summary = serializers.SerializerMethodField()

    class Meta(ObjectiveLkpSerializer.Meta):
        fields = ObjectiveLkpSerializer.Meta.fields + ['attribute_summary']

    def get_attribute_summary(self, obj):
        """Provide summary of available additional attributes"""
        return {
            'has_categories': bool(obj.category1_label or obj.category2_label),
            'has_references': bool(obj.reference1_label or obj.reference2_label),
            'has_quantities': bool(obj.qty1_label or obj.qty2_label),
            'has_subtype': bool(obj.type),
        }


class OrganisationLkpSerializer(serializers.ModelSerializer):
    """Serializer for Organisation Lookup"""

    class Meta:
        model = OrganisationLkp
        fields = [
            'organisation',
            'description',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
        ]
        read_only_fields = ['created_on', 'created_by', 'updated_on', 'updated_by']


class RegenerationMethodsLkpSerializer(serializers.ModelSerializer):
    """Serializer for Regeneration Methods Lookup"""

    class Meta:
        model = RegenerationMethodsLkp
        fields = [
            'regen_method',
            'description',
        ]


class RescheduleReasonsLkpSerializer(serializers.ModelSerializer):
    """Serializer for Reschedule Reasons Lookup"""

    class Meta:
        model = RescheduleReasonsLkp
        fields = [
            'rescheduled_reason',
            'description',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
        ]
        read_only_fields = ['created_on', 'created_by', 'updated_on', 'updated_by']


class SpatialPrecisionLkpSerializer(serializers.ModelSerializer):
    """Serializer for Spatial Precision Lookup"""

    class Meta:
        model = SpatialPrecisionLkp
        fields = [
            'precision_code',
            'resolution',
            'description',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
        ]
        read_only_fields = ['created_on', 'created_by', 'updated_on', 'updated_by']


class SpeciesApiLkpSerializer(serializers.ModelSerializer):
    """Serializer for Species API Lookup"""
    species_name = serializers.CharField(source='short_description', read_only=True)

    class Meta:
        model = SpeciesApiLkp
        fields = [
            'species',
            'species_name',
            'short_description',
            'full_description',
            'fmismiscode_species',
            'fmisdescription_type',
            'fmismiscode_type',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
        ]
        read_only_fields = ['created_on', 'created_by', 'updated_on', 'updated_by']


class TaskLkpSerializer(serializers.ModelSerializer):
    """Serializer for Task Lookup"""
    is_active = serializers.SerializerMethodField()
    #requires_extra_info = serializers.BooleanField(source='addition_attribs', read_only=True)
    initiates_regeneration = serializers.BooleanField(source='regen_init', read_only=True)

    class Meta:
        model = TaskLkp
        fields = [
            'task',
            'task_name',
            'definition',
            'category1_label',
            'category2_label',
            'category3_label',
            'category4_label',
            'qty1_label',
            'qty2_label',
            'qty3_label',
            'qty4_label',
            'record_standard',
            'only_1silvic',
            'financial_activity',
            'forest_type',
            'default_organisation',
            #'addition_attribs',
            #'requires_extra_info',
            'regen_init',
            'initiates_regeneration',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
            'auth_on',
            'auth_by',
            'revoked_on',
            'revoked_by',
            'effective_from',
            'effective_to',
            'is_active',
        ]
        read_only_fields = ['created_on', 'created_by', 'updated_on', 'updated_by']

    def get_is_active(self, obj):
        return obj.effective_to is None


class TaskLkpDetailSerializer(TaskLkpSerializer):
    """Detailed serializer for Task Lookup with additional computed fields"""
    attribute_labels_summary = serializers.SerializerMethodField()
    organisation_info = serializers.SerializerMethodField()

    class Meta(TaskLkpSerializer.Meta):
        fields = TaskLkpSerializer.Meta.fields + ['attribute_labels_summary', 'organisation_info']

    def get_attribute_labels_summary(self, obj):
        """Provide summary of available attribute labels"""
        return {
            'categories': {
                'category1': obj.category1_label,
                'category2': obj.category2_label,
                'category3': obj.category3_label,
                'category4': obj.category4_label,
            },
            'quantities': {
                'qty1': obj.qty1_label,
                'qty2': obj.qty2_label,
                'qty3': obj.qty3_label,
                'qty4': obj.qty4_label,
            }
        }

    def get_organisation_info(self, obj):
        """Get organisation information if available"""
        if obj.default_organisation:
            from silrec.components.lookups.models import OrganisationLkp
            try:
                org = OrganisationLkp.objects.get(organisation=obj.default_organisation)
                return {
                    'code': org.organisation,
                    'description': org.description
                }
            except OrganisationLkp.DoesNotExist:
                return None
        return None


class TasksAttLkpSerializer(serializers.ModelSerializer):
    """Serializer for Task Attributes Lookup"""

    class Meta:
        model = TasksAttLkp
        fields = [
            'addition_attrib',
            'description',
        ]


class TreatmentStatusLkpSerializer(serializers.ModelSerializer):
    """Serializer for Treatment Status Lookup"""
    status_display = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = TreatmentStatusLkp
        fields = [
            'status',
            'status_display',
            'name',
            'definition',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
        ]
        read_only_fields = ['created_on', 'created_by', 'updated_on', 'updated_by']


# List serializers for efficient dropdowns and selections
class SimpleCohortMetricsLkpSerializer(serializers.ModelSerializer):
    """Simplified serializer for dropdowns"""
    class Meta:
        model = CohortMetricsLkp
        fields = ['metric_id', 'name', 'value', 'rating']


class SimpleObjectiveLkpSerializer(serializers.ModelSerializer):
    """Simplified serializer for dropdowns"""
    class Meta:
        model = ObjectiveLkp
        fields = ['obj_code', 'description', 'cut', 'forest_type']


class SimpleTaskLkpSerializer(serializers.ModelSerializer):
    """Simplified serializer for dropdowns"""
    class Meta:
        model = TaskLkp
        fields = ['task', 'task_name', 'forest_type', 'default_organisation']


class SimpleSpeciesApiLkpSerializer(serializers.ModelSerializer):
    """Simplified serializer for dropdowns"""
    class Meta:
        model = SpeciesApiLkp
        fields = ['species', 'short_description', 'fmis_code_species']


class SimpleRegenerationMethodsLkpSerializer(serializers.ModelSerializer):
    """Simplified serializer for dropdowns"""
    class Meta:
        model = RegenerationMethodsLkp
        fields = ['regen_method', 'description']


class SimpleTreatmentStatusLkpSerializer(serializers.ModelSerializer):
    """Simplified serializer for dropdowns"""
    class Meta:
        model = TreatmentStatusLkp
        fields = ['status', 'name']



class CombinedLkpSerializer(serializers.Serializer):
    """ Combined serializer for all lookup tables
    """
    cohort_metrics = serializers.SerializerMethodField()
    machines = serializers.SerializerMethodField()
    objectives = serializers.SerializerMethodField()
    organisations = serializers.SerializerMethodField()
    regeneration_methods = serializers.SerializerMethodField()
    reschedule_reasons = serializers.SerializerMethodField()
    spatial_precision = serializers.SerializerMethodField()
    species = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    task_attributes = serializers.SerializerMethodField()
    treatment_statuses = serializers.SerializerMethodField()

    def get_cohort_metrics(self, obj):
        """Get first 4 fields from CohortMetricsLkp with effective date filtering"""
        from silrec.components.forest_blocks.models import CohortMetricsLkp
        from django.utils import timezone

        current_date = timezone.now()
        queryset = CohortMetricsLkp.objects.filter(
            Q(effective_from__lte=current_date) &
            Q(effective_to__gte=current_date) |
            Q(effective_from__isnull=True) &
            Q(effective_to__isnull=True)
        )

        return [
            {
                'id': item.pk,
                'name': getattr(item, 'name', None),
                'definition': getattr(item, 'definition', None),
                'rating': getattr(item, 'rating', None),
            }
            for item in queryset
        ]

    def get_machines(self, obj):
        """Get first 4 fields from MachineLkp"""
        from silrec.components.forest_blocks.models import MachineLkp
        queryset = MachineLkp.objects.all()
        return [
            {
                'id': item.pk,
                'manufacturer': getattr(item, 'manufacturer', None),
                'model': getattr(item, 'model', None),
                'machine_type': getattr(item, 'machine_type', None),
            }
            for item in queryset
        ]

    def get_objectives(self, obj):
        """Get first 4 fields from ObjectiveLkp with effective date filtering"""
        from silrec.components.forest_blocks.models import ObjectiveLkp
        from django.utils import timezone

        current_date = timezone.now()
        queryset = ObjectiveLkp.objects.filter(
            Q(effective_from__lte=current_date) &
            Q(effective_to__gte=current_date) |
            Q(effective_from__isnull=True) &
            Q(effective_to__isnull=True)
        )

        return [
            {
                'id': item.obj_code,
                'obj_code': item.obj_code,
                'description': getattr(item, 'description', None),
                'definition': getattr(item, 'definition', None),
            }
            for item in queryset
        ]

    def get_organisations(self, obj):
        """Get first 4 fields from OrganisationLkp"""
        from silrec.components.forest_blocks.models import OrganisationLkp
        queryset = OrganisationLkp.objects.all()
        return [
            {
                'id': item.organisation,
                'organisation': item.organisation,
                'description': getattr(item, 'description', None),
                'created_on': getattr(item, 'created_on', None),
            }
            for item in queryset
        ]

    def get_regeneration_methods(self, obj):
        """Get first 4 fields from RegenerationMethodsLkp"""
        from silrec.components.forest_blocks.models import RegenerationMethodsLkp
        queryset = RegenerationMethodsLkp.objects.all()
        return [
            {
                'id': item.regen_method,
                'regen_method': item.regen_method,
                'description': getattr(item, 'description', None),
            }
            for item in queryset
        ]

    def get_reschedule_reasons(self, obj):
        """Get first 4 fields from RescheduleReasonsLkp"""
        from silrec.components.forest_blocks.models import RescheduleReasonsLkp
        queryset = RescheduleReasonsLkp.objects.all()
        return [
            {
                'id': item.rescheduled_reason,
                'rescheduled_reason': item.rescheduled_reason,
                'description': getattr(item, 'description', None),
                'created_on': getattr(item, 'created_on', None),
            }
            for item in queryset
        ]

    def get_spatial_precision(self, obj):
        """Get first 4 fields from SpatialPrecisionLkp"""
        from silrec.components.forest_blocks.models import SpatialPrecisionLkp
        queryset = SpatialPrecisionLkp.objects.all()
        return [
            {
                'id': item.precision_code,
                'precision_code': item.precision_code,
                'resolution': getattr(item, 'resolution', None),
                'description': getattr(item, 'description', None),
            }
            for item in queryset
        ]

    def get_species(self, obj):
        """Get first 4 fields from SpeciesApiLkp"""
        from silrec.components.forest_blocks.models import SpeciesApiLkp
        queryset = SpeciesApiLkp.objects.all()
        return [
            {
                'id': item.species,
                'species': item.species,
                'short_description': getattr(item, 'short_description', None),
                'full_description': getattr(item, 'full_description', None),
            }
            for item in queryset
        ]

    def get_tasks(self, obj):
        """Get first 4 fields from TaskLkp with effective date filtering"""
        from silrec.components.forest_blocks.models import TaskLkp
        from django.utils import timezone

        current_date = timezone.now()
        queryset = TaskLkp.objects.filter(
            Q(effective_from__lte=current_date) &
            Q(effective_to__gte=current_date) |
            Q(effective_from__isnull=True) &
            Q(effective_to__isnull=True)
        )

        return [
            {
                'id': item.task,
                'task': item.task,
                'task_name': getattr(item, 'task_name', None),
                'definition': getattr(item, 'definition', None),
            }
            for item in queryset
        ]

    def get_task_attributes(self, obj):
        """Get first 4 fields from TasksAttLkp"""
        from silrec.components.forest_blocks.models import TasksAttLkp
        queryset = TasksAttLkp.objects.all()
        return [
            {
                'id': item.addition_attrib,
                'addition_attrib': item.addition_attrib,
                'description': getattr(item, 'description', None),
            }
            for item in queryset
        ]

    def get_treatment_statuses(self, obj):
        """Get first 4 fields from TreatmentStatusLkp"""
        from silrec.components.forest_blocks.models import TreatmentStatusLkp
        queryset = TreatmentStatusLkp.objects.all()
        return [
            {
                'id': item.status,
                'status': item.status,
                'name': getattr(item, 'name', None),
                'definition': getattr(item, 'definition', None),
            }
            for item in queryset
        ]
