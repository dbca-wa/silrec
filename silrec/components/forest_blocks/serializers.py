from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.auth.models import User
from django.contrib.gis.db.models.functions import Area
from django.db.models import F
from silrec.components.forest_blocks.models import (
    Polygon,
    Cohort,
    Treatment,
    TreatmentXtra,
    Compartments,
    AssignChtToPly,
    TaskCategory,
    TaskLkp,
    ObjectiveLkp,
    RegenerationMethodsLkp,
    OrganisationLkp,
    SpeciesApiLkp,
)


class CohortSerializer(serializers.ModelSerializer):
    # Read-only fields for display
    polygon_names = serializers.SerializerMethodField()
    assigned_polygons = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    treatment_count = serializers.SerializerMethodField()

    # Foreign key display fields
    obj_code_display = serializers.CharField(source='obj_code.description', read_only=True)
    species_display = serializers.CharField(source='species.species_name', read_only=True)
    regen_method_display = serializers.CharField(source='regen_method.description', read_only=True)

    class Meta:
        model = Cohort
        fields = [
            'cohort_id',
            'obj_code',
            'obj_code_display',
            'op_id',
            'op_date',
            'pct_area',
            'year_last_cut',
            'treatments',
            'regen_date',
            'regen_date2',
            'species',
            'species_display',
            'regen_method',
            'regen_method_display',
            'regen_done',
            'complete_date',
            'resid_ba_m2ha',
            'target_ba_m2ha',
            'resid_spha',
            'target_spha',
            'site_quality',
            'herbicide_app_spec',
            'vrp',
            'vrp_tot_area',
            'comments',
            'extra_info',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
            'stand',
            # Computed fields
            'polygon_names',
            'assigned_polygons',
            'task_count',
            'treatment_count',
        ]
        read_only_fields = [
            'cohort_id', 'created_on', 'created_by', 'updated_on', 'updated_by',
            'polygon_names', 'assigned_polygons', 'task_count', 'treatment_count'
        ]

    def get_polygon_names(self, obj):
        """Get names of polygons this cohort is assigned to"""
        assignments = AssignChtToPly.objects.filter(
            cohort=obj,
            status_current=True
        ).select_related('polygon')
        return [ass.polygon.name for ass in assignments if ass.polygon.name]

    def get_assigned_polygons(self, obj):
        """Get detailed polygon assignment information"""
        assignments = AssignChtToPly.objects.filter(
            cohort=obj
        ).select_related('polygon').annotate(
            area_ha=F('polygon__area_ha')
        )

        return [
            {
                'polygon_id': ass.polygon.polygon_id,
                'name': ass.polygon.name,
                'area_ha': ass.polygon.area_ha,
                'status_current': ass.status_current,
                'cohort_closed': ass.cohort_closed,
                'compartment': ass.polygon.compartment.compartment if ass.polygon.compartment else None
            }
            for ass in assignments
        ]

    def get_task_count(self, obj):
        """Count of distinct tasks for this cohort"""
        return Treatment.objects.filter(cohort=obj).values('task').distinct().count()

    def get_treatment_count(self, obj):
        """Count of all treatments for this cohort"""
        return Treatment.objects.filter(cohort=obj).count()

    def validate_pct_area(self, value):
        """Validate percentage area is between 0 and 100"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Percentage area must be between 0 and 100")
        return value

    def validate_resid_ba_m2ha(self, value):
        """Validate residual BA is non-negative"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Residual basal area cannot be negative")
        return value

    def validate_target_ba_m2ha(self, value):
        """Validate target BA is non-negative"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Target basal area cannot be negative")
        return value

    def validate_resid_spha(self, value):
        """Validate residual SPHA is non-negative"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Residual stems per hectare cannot be negative")
        return value

    def validate_target_spha(self, value):
        """Validate target SPHA is non-negative"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Target stems per hectare cannot be negative")
        return value

    def create(self, validated_data):
        """Create a new cohort with current user info"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user.username
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update cohort with current user info"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user.username
        return super().update(instance, validated_data)


class TreatmentSerializer(serializers.ModelSerializer):
    # Read-only display fields
    task_name = serializers.CharField(source='task.name', read_only=True)
    task_description = serializers.CharField(source='task.description', read_only=True)
    cohort_info = serializers.SerializerMethodField()
    treatment_extras_count = serializers.SerializerMethodField()

    # Foreign key fields (writeable)
    prescription_id = serializers.PrimaryKeyRelatedField(
        source='prescription',
        queryset=Treatment.objects.all(),
        required=False,
        allow_null=True
    )

    # Status choices for frontend
    status_choices = serializers.SerializerMethodField()

    class Meta:
        model = Treatment
        fields = [
            'treatment_id',
            'prescription',
            'prescription_id',
            'cohort',
            'cohort_info',
            'task',
            'task_name',
            'task_description',
            'plan_mth',
            'plan_yr',
            'pct_area',
            'complete_date',
            'results',
            'status',
            'changed_by',
            'reference',
            'organisation',
            'initial_plan_yr',
            'can_reschedule',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
            'ztreatment_method',
            'zoperation',
            'zstand',
            'zsilvic',
            'ztreatno',
            'zcomplmo',
            'zcompl_yr',
            'zscheduleconfirmed',
            'zextra_info',
            # Computed fields
            'treatment_extras_count',
            'status_choices',
        ]
        read_only_fields = [
            'treatment_id', 'created_on', 'created_by', 'updated_on', 'updated_by',
            'treatment_extras_count', 'status_choices'
        ]

    def get_cohort_info(self, obj):
        """Get basic cohort information"""
        if obj.cohort:
            return {
                'cohort_id': obj.cohort.cohort_id,
                'obj_code': obj.cohort.obj_code,
                'species': obj.cohort.species,
            }
        return None

    def get_treatment_extras_count(self, obj):
        """Count of treatment extras for this treatment"""
        return TreatmentXtra.objects.filter(treatment=obj).count()

    def get_status_choices(self, obj):
        """Get status choices for frontend dropdown"""
        return {
            'P': 'Planned',
            'D': 'Completed',
            'C': 'Cancelled',
            'F': 'Failed',
            'W': 'Written Off',
            'X': 'Not Required'
        }

    def validate_pct_area(self, value):
        """Validate percentage area is between 0 and 100"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Percentage area must be between 0 and 100")
        return value

    def validate_plan_mth(self, value):
        """Validate planned month is between 1 and 12"""
        if value is not None and (value < 1 or value > 12):
            raise serializers.ValidationError("Planned month must be between 1 and 12")
        return value

    def validate_plan_yr(self, value):
        """Validate planned year is reasonable"""
        if value is not None and value < 2000:
            raise serializers.ValidationError("Planned year seems too far in the past")
        return value

    def validate_complete_date(self, value):
        """Validate complete date is not in the future"""
        from django.utils import timezone
        if value and value > timezone.now():
            raise serializers.ValidationError("Complete date cannot be in the future")
        return value

    def validate(self, data):
        """Cross-field validation"""
        # If status is completed, complete_date should be set
        if data.get('status') == 'D' and not data.get('complete_date'):
            raise serializers.ValidationError({
                'complete_date': 'Complete date is required when status is "Completed"'
            })

        # If complete_date is set, status should probably be completed
        if data.get('complete_date') and data.get('status') != 'D':
            # This is just a warning, not an error
            pass

        return data

    def create(self, validated_data):
        """Create a new treatment with current user info"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user.username
            # Set changed_by if not provided
            if not validated_data.get('changed_by'):
                validated_data['changed_by'] = request.user.username

        # Set extra_info flag based on task type or other criteria
        task = validated_data.get('task')
#        if task and task.requires_extra_info:  # Assuming TaskLkp has this field
#            validated_data['zextra_info'] = True

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update treatment with current user info"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user.username
            # Update changed_by if status or timing changes
            if any(field in validated_data for field in ['status', 'plan_yr', 'plan_mth', 'complete_date']):
                validated_data['changed_by'] = request.user.username

        return super().update(instance, validated_data)


class TreatmentXtraSerializer(serializers.ModelSerializer):
    # Read-only display fields
    treatment_info = serializers.SerializerMethodField()
    category1_display = serializers.CharField(source='category1.category_value', read_only=True)
    category2_display = serializers.CharField(source='category2.category_value', read_only=True)
    category3_display = serializers.CharField(source='category3.category_value', read_only=True)
    category4_display = serializers.CharField(source='category4.category_value', read_only=True)

    # Foreign key fields (writeable)
    category1_id = serializers.PrimaryKeyRelatedField(
        source='category1',
        queryset=TaskCategory.objects.all(),
        required=False,
        allow_null=True
    )
    category2_id = serializers.PrimaryKeyRelatedField(
        source='category2',
        queryset=TaskCategory.objects.all(),
        required=False,
        allow_null=True
    )
    category3_id = serializers.PrimaryKeyRelatedField(
        source='category3',
        queryset=TaskCategory.objects.all(),
        required=False,
        allow_null=True
    )
    category4_id = serializers.PrimaryKeyRelatedField(
        source='category4',
        queryset=TaskCategory.objects.all(),
        required=False,
        allow_null=True
    )

    # Species display
    api_species_assessed_display = serializers.CharField(
        source='api_species_assessed.species_name',
        read_only=True
    )

    # Reschedule reasons choices
    reschedule_reason_choices = serializers.SerializerMethodField()

    class Meta:
        model = TreatmentXtra
        fields = [
            'treatment_xtra_id',
            'treatment',
            'treatment_info',
            'rescheduled_reason',
            'success_rate_pct',
            'stocking_rate_spha',
            'api_species_assessed',
            'api_species_assessed_display',
            'category1',
            'category1_id',
            'category1_display',
            'category2',
            'category2_id',
            'category2_display',
            'category3',
            'category3_id',
            'category3_display',
            'category4',
            'category4_id',
            'category4_display',
            'qty1',
            'qty2',
            'qty3',
            'qty4',
            'zmachine_id',
            'zseed_source',
            'zassessment_type',
            'zspecies1_planted',
            'zplanting_rate1_spha',
            'zspecies2_planted',
            'zplanting_rate2_spha',
            'zresult_standard',
            'zpatch',
            'zsilvic',
            'ztaskid',
            'ztreatno',
            # Computed fields
            'reschedule_reason_choices',
        ]
        read_only_fields = [
            'treatment_xtra_id', 'treatment_info', 'reschedule_reason_choices'
        ]

    def get_treatment_info(self, obj):
        """Get basic treatment information"""
        if obj.treatment:
            return {
                'treatment_id': obj.treatment.treatment_id,
                'task_name': obj.treatment.task.task_name if obj.treatment.task else None,
                'cohort_id': obj.treatment.cohort.cohort_id if obj.treatment.cohort else None,
            }
        return None

    def get_reschedule_reason_choices(self, obj):
        """Get reschedule reason choices for frontend"""
        # You might want to get these from a lookup table or hardcode common reasons
        return [
            {'value': 'weather', 'label': 'Weather Conditions'},
            {'value': 'resource', 'label': 'Resource Availability'},
            {'value': 'operational', 'label': 'Operational Issues'},
            {'value': 'biological', 'label': 'Biological Factors'},
            {'value': 'other', 'label': 'Other'},
        ]

    def validate_success_rate_pct(self, value):
        """Validate success rate percentage"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Success rate must be between 0 and 100 percent")
        return value

    def validate_stocking_rate_spha(self, value):
        """Validate stocking rate"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Stocking rate cannot be negative")
        return value

    def validate_qty1(self, value):
        """Validate quantity fields"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value

    def validate_qty2(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value

    def validate_qty3(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value

    def validate_qty4(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value

    def validate_zplanting_rate1_spha(self, value):
        """Validate planting rates"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Planting rate cannot be negative")
        return value

    def validate_zplanting_rate2_spha(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Planting rate cannot be negative")
        return value

    def validate(self, data):
        """Cross-field validation"""
        # If success rate is provided, it should be accompanied by assessment type
        if data.get('success_rate_pct') is not None and not data.get('zassessment_type'):
            raise serializers.ValidationError({
                'zassessment_type': 'Assessment type is required when success rate is provided'
            })

        # If planting rates are provided, species should be specified
        if (data.get('zplanting_rate1_spha') is not None or
            data.get('zplanting_rate2_spha') is not None):
            if not data.get('zspecies1_planted') and not data.get('zspecies2_planted'):
                raise serializers.ValidationError({
                    'zspecies1_planted': 'At least one species must be specified when planting rates are provided'
                })

        return data

    def create(self, validated_data):
        """Create treatment extra with validation"""
        # Ensure the treatment exists and belongs to the user's accessible data
        treatment = validated_data.get('treatment')
        if treatment:
            # Add any business logic here for creation
            pass

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update treatment extra with validation"""
        return super().update(instance, validated_data)



class _TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
#        fields = (
#            'treatment_id',
#            'prescription_id',
#            'cohort_id',
#        )
        fields = '__all__'


class PolygonSerializer(serializers.ModelSerializer):
    ''' http://localhost:8001/api/polygon.json
        http://localhost:8001/api/polygon
    '''
    class Meta:
        model = Polygon
#        fields = (
#            'polygon_id',
#            'name',
#        )
        fields = '__all__'


class CompartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compartments
        fields = '__all__'


class PolygonGeometrySerializer(GeoFeatureModelSerializer):
    compartments = CompartmentsSerializer(source='compartment', many=False)

    class Meta:
        model = Polygon
        geo_field = "geom"
        fields = (
            "polygon_id",
            "name",
            "area_ha",
            "created_on",
            "created_by",
            "closed",
            "reason_closed",
            "zfea_id",
            "compartments",
            "geom",
        )
        read_only_fields = ("polygon_id",)


class Polygon2Serializer(serializers.ModelSerializer):
    ''' http://localhost:8001/api/polygon2.json
        http://localhost:8001/api/polygon2
    '''
    #cohorts = serializers.SerializerMethodField()
    polygongeometry = PolygonGeometrySerializer(many=True, read_only=True)

    def get_cohorts(self,obj):
        assignchttoply_qs = obj.assignchttoply_set.all()
        cohorts = [cohort.cohort for cohort in assignchttoply_qs] # map to cohort objects
        #import ipdb; ipdb.set_trace()
        #serializer = CohortSerializer(cohorts, many=True)
        serializer = SimpleCohortSerializer(cohorts, many=True)

        return serializer.data

    class Meta:
        model = Polygon
        fields = "__all__"
#        extra_fields = [
#            "polygongeometry",
#        ]
#        fields = (
#            #'polygon_id',
#            #'name',
#            #'cohorts',
#            'polygongeometry',
#        )
        datatables_always_serialize = (
            'polygon_id',
            'name',
            #'cohorts',
            'polygongeometry',
        )


class PolygonCohortSerializer(serializers.ModelSerializer):
    polygon = PolygonSerializer()
    cohort = CohortSerializer()

    class Meta:
        model = AssignChtToPly
        fields = (
            'cht2ply_id',
            'polygon',
            'cohort',
            #'polygon_id',
            #'cohort_id',
        )


class UserSerializerSimple(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "last_name", "first_name", "email", "full_name")

    def get_full_name(self, obj):
        return obj.get_full_name()


# 16-Nov-2025 -------------------

from silrec.components.forest_blocks.models import Polygon, AssignChtToPly, Cohort
class CohortDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = (
            'cohort_id',
            'obj_code',
            'target_ba_m2ha',
            'resid_ba_m2ha',
            'target_spha',
            'resid_spha',
            'species',
            'regen_method',
            'site_quality',
            'regen_date',
            'complete_date'
        )

class AssignChtToPlySerializer(serializers.ModelSerializer):
    cohort_details = CohortDataSerializer(source='cohort', read_only=True)

    class Meta:
        model = AssignChtToPly
        fields = (
            'cht2ply_id',
            'cohort',
            'cohort_details',
            'cohort_closed',
            'status_current',
            'created_on',
            'updated_on'
        )

class PolygonCohortDataSerializer(serializers.ModelSerializer):
    assigned_cohorts = serializers.SerializerMethodField()
    proposal_id = serializers.IntegerField(source='proposal.id', read_only=True)

    class Meta:
        model = Polygon
        fields = (
            'polygon_id',
            'proposal_id',
            'name',
            'compartment',
            'area_ha',
            'zfea_id',
            'created_on',
            'updated_on',
            'assigned_cohorts'
        )

    def get_assigned_cohorts(self, obj):
        # Use the correct related name
        assigned_cht = obj.assignchttoply_set.filter(status_current=True).select_related('cohort')
        return AssignChtToPlySerializer(assigned_cht, many=True).data


class SimpleCohortSerializer(serializers.ModelSerializer):
    """Simplified cohort serializer for nested representations"""
    class Meta:
        model = Cohort
        fields = ['cohort_id', 'obj_code', 'species', 'site_quality']

class SimpleTreatmentSerializer(serializers.ModelSerializer):
    """Simplified treatment serializer for nested representations"""
    task_name = serializers.CharField(source='task.name', read_only=True)

    class Meta:
        model = Treatment
        fields = ['treatment_id', 'task', 'task_name', 'status', 'complete_date']

class TaskCategorySerializer(serializers.ModelSerializer):
    """Serializer for task categories"""
    class Meta:
        model = TaskCategory
        fields = ['tsk_cat_id', 'task', 'target_column', 'category_value', 'description']

# List serializers for efficient listing
class CohortListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for cohort lists"""
    polygon_count = serializers.SerializerMethodField()
    treatment_count = serializers.SerializerMethodField()

    class Meta:
        model = Cohort
        fields = [
            'cohort_id', 'obj_code', 'species', 'site_quality',
            'resid_ba_m2ha', 'target_ba_m2ha', 'complete_date',
            'polygon_count', 'treatment_count'
        ]

    def get_polygon_count(self, obj):
        return AssignChtToPly.objects.filter(cohort=obj, status_current=True).count()

    def get_treatment_count(self, obj):
        return Treatment.objects.filter(cohort=obj).count()

class TreatmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for treatment lists"""
    task_name = serializers.CharField(source='task.name', read_only=True)
    has_extras = serializers.SerializerMethodField()

    class Meta:
        model = Treatment
        fields = [
            'treatment_id', 'task', 'task_name', 'status',
            'plan_yr', 'plan_mth', 'complete_date', 'has_extras'
        ]

    def get_has_extras(self, obj):
        return TreatmentXtra.objects.filter(treatment=obj).exists()


