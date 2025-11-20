from django.contrib.auth.models import User

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

