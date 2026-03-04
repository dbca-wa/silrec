from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.auth.models import User
from django.contrib.gis.db.models.functions import Area
from django.db.models import F
from django.core.files.storage import default_storage
from silrec.components.forest_blocks.models import (
    Polygon,
    #TmpPolygon,
    Cohort,
    Treatment,
    TreatmentXtra,
    Compartments,
    Operation,
    AssignChtToPly,
    TaskCategory,
    TaskLkp,
    ObjectiveLkp,
    RegenerationMethodsLkp,
    OrganisationLkp,
    SpeciesApiLkp,
    Prescription,
    SilviculturistComment,
    SurveyAssessmentDocument,
)

class SurveyAssessmentDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_display = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    #uploaded_by_display = serializers.CharField(source='uploaded_by', read_only=True)
    file_size_display = serializers.SerializerMethodField()
    file_icon = serializers.SerializerMethodField()
    is_image_file = serializers.SerializerMethodField()

    # Foreign key fields (writeable)
    treatment_id = serializers.PrimaryKeyRelatedField(
        source='treatment',
        queryset=Treatment.objects.all(),
        required=True
    )


    class Meta:
        model = SurveyAssessmentDocument
        fields = [
            'document_id',
            'treatment',
            'treatment_id',
            'document_type',
            'title',
            'description',
            'file',
            'file_url',
            'file_size',
            'file_size_display',
            'file_name',
            'file_type',
            'status',
            'document_date',
            'marked_deleted',
            'uploaded_by',
            'uploaded_by_display',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
            # Computed fields
            'file_icon',
            'is_image_file',
        ]
        read_only_fields = [
            'document_id', 'file_size', 'file_name', 'file_type',
            'created_on', 'created_by', 'updated_on', 'updated_by',
            'file_icon', 'file_size_display', 'is_image_file', 'uploaded_by_display'
        ]


    def get_is_image_file(self, obj):
        return obj.is_image()

    def get_file_size_display(self, obj):
        if obj.file_size:
            for unit in ['B', 'KB', 'MB', 'GB']:
                if obj.file_size < 1024.0:
                    return f"{obj.file_size:.2f} {unit}"
                obj.file_size /= 1024.0
        return '0 B'

    def get_file_icon(self, obj):
        if obj.file_name:
            extension = obj.file_name.split('.')[-1].lower()
            icon_map = {
                'pdf': 'bi-file-pdf',
                'doc': 'bi-file-word',
                'docx': 'bi-file-word',
                'xls': 'bi-file-excel',
                'xlsx': 'bi-file-excel',
                'jpg': 'bi-file-image',
                'jpeg': 'bi-file-image',
                'png': 'bi-file-image',
                'gif': 'bi-file-image',
                'bmp': 'bi-file-image',
                'zip': 'bi-file-zip',
                'rar': 'bi-file-zip',
                '7z': 'bi-file-zip',
            }
            return icon_map.get(extension, 'bi-file-earmark')
        return 'bi-file-earmark'

    def validate(self, data):
        """
        Validate that either file or file_url is provided on CREATE,
        but not required on UPDATE/PATCH (partial updates).
        """
        # If this is a create (POST) operation
        if self.instance is None:
            # Check if either file or file_url is provided
            if not data.get('file') and not data.get('file_url'):
                raise serializers.ValidationError(
                    {'file': 'Either a file or a URL must be provided'}
                )

        # If this is an update (PUT/PATCH) and we're changing the file source
        # but not providing a new file or URL
        elif self.instance and 'file' in data and 'file_url' in data:
            if data['file'] is None and data['file_url'] is None:
                # Check if instance already has a file or URL
                if not self.instance.file and not self.instance.file_url:
                    raise serializers.ValidationError(
                        {'file': 'Either a file or a URL must be provided'}
                    )

        return data

    def create(self, validated_data):
        # Extract treatment_id if provided
        treatment_id = validated_data.pop('treatment_id', None)

        # Set uploaded_by to current user
        validated_data['uploaded_by'] = self.context['request'].user

        # Handle treatment if treatment_id is provided
        if treatment_id:
            treatment = Treatment.objects.get(pk=treatment_id)
            validated_data['treatment'] = treatment

        # Handle file upload with original name preservation
        file_obj = validated_data.get('file')
        if file_obj and hasattr(file_obj, 'name'):
            # Save original filename
            original_name = file_obj.name
            validated_data['file_name'] = original_name

            # Generate unique filename while preserving extension
            import os
            from uuid import uuid4
            name, ext = os.path.splitext(original_name)
            unique_id = uuid4().hex[:8]

            # Create safe filename
            safe_name = original_name.replace(' ', '_').replace('(', '').replace(')', '')
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-', '.'])

            if ext:
                new_name = f"{safe_name.rsplit('.', 1)[0]}_{unique_id}{ext}"
            else:
                new_name = f"{safe_name}_{unique_id}"

            # Rename the file
            file_obj.name = new_name

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Extract treatment_id if provided
        treatment_id = validated_data.pop('treatment_id', None)

        # Handle treatment if treatment_id is provided
        if treatment_id:
            treatment = Treatment.objects.get(pk=treatment_id)
            validated_data['treatment'] = treatment

        # Handle new file upload
        file_obj = validated_data.get('file')
        if file_obj and hasattr(file_obj, 'name'):
            # Save original filename
            original_name = file_obj.name
            validated_data['file_name'] = original_name

            # Generate unique filename while preserving extension
            import os
            from uuid import uuid4
            name, ext = os.path.splitext(original_name)
            unique_id = uuid4().hex[:8]

            # Create safe filename
            safe_name = original_name.replace(' ', '_').replace('(', '').replace(')', '')
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-', '.'])

            if ext:
                new_name = f"{safe_name.rsplit('.', 1)[0]}_{unique_id}{ext}"
            else:
                new_name = f"{safe_name}_{unique_id}"

            # Rename the file
            file_obj.name = new_name

        # If file is being removed (set to None), clear file_name and file_size
        elif 'file' in validated_data and validated_data['file'] is None:
            validated_data['file_name'] = None
            validated_data['file_size'] = None
            validated_data['file_type'] = None

        return super().update(instance, validated_data)

class __SurveyAssessmentDocumentSerializer(serializers.ModelSerializer):
    # Read-only display fields
    file_icon = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    is_image_file = serializers.SerializerMethodField()
    uploaded_by_display = serializers.CharField(source='uploaded_by', read_only=True)

    # Foreign key fields (writeable)
    treatment_id = serializers.PrimaryKeyRelatedField(
        source='treatment',
        queryset=Treatment.objects.all(),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make file and file_url not required for partial updates
        import ipdb; ipdb.set_trace()
        if self.partial:
            self.fields['file'].required = False
            self.fields['file_url'].required = False

    class Meta:
        model = SurveyAssessmentDocument
        fields = [
            'document_id',
            'treatment',
            'treatment_id',
            'document_type',
            'title',
            'description',
            'file',
            'file_url',
            'file_size',
            'file_size_display',
            'file_name',
            'file_type',
            'status',
            'document_date',
            'marked_deleted',
            'uploaded_by',
            'uploaded_by_display',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by',
            # Computed fields
            'file_icon',
            'is_image_file',
        ]
        read_only_fields = [
            'document_id', 'file_size', 'file_name', 'file_type',
            'created_on', 'created_by', 'updated_on', 'updated_by',
            'file_icon', 'file_size_display', 'is_image_file', 'uploaded_by_display'
        ]

    def get_file_icon(self, obj):
        return obj.get_file_icon()

    def get_file_size_display(self, obj):
        return obj.get_file_size_display()

    def get_is_image_file(self, obj):
        return obj.is_image()

    def validate(self, data):
        """Validate that either file or file_url is provided"""
        if not data.get('file') and not data.get('file_url'):
            raise serializers.ValidationError({
                'file': 'Either a file or a URL must be provided'
            })

        if data.get('file') and data.get('file_url'):
            raise serializers.ValidationError({
                'file': 'Cannot provide both a file and a URL'
            })

        return data

    def validate_file(self, value):
        """Validate file upload"""
        if value:
            # Check file size (50MB limit)
            max_size = 50 * 1024 * 1024  # 50MB
            if value.size > max_size:
                raise serializers.ValidationError(f'File size must be less than 50MB. Current size: {value.size}')

            # Check file extensions
            allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'zip', 'rar', '7z']
            file_extension = value.name.split('.')[-1].lower() if '.' in value.name else ''
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}')

        return value

    def validate_file_url(self, value):
        """Validate URL"""
        if value:
            import re
            url_pattern = re.compile(
                r'^(https?://)?'  # http:// or https://
                r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'  # domain
                r'(:[0-9]+)?'  # port
                r'(/.*)?$'  # path
            )
            if not url_pattern.match(value):
                raise serializers.ValidationError('Enter a valid URL')

        return value

    def create(self, validated_data):
        """Create treatment document with current user info"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user.username
            validated_data['uploaded_by'] = request.user.username
            if not validated_data.get('updated_by'):
                validated_data['updated_by'] = request.user.username

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update treatment document with current user info"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user.username

        return super().update(instance, validated_data)


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
                #'cohort_closed': ass.cohort_closed,
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


class PrescriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Prescription
        fields = "__all__"


class TreatmentXtra2Serializer(serializers.ModelSerializer):

    class Meta:
        model = TreatmentXtra
        fields = "__all__"


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


class TreatmentSerializer(serializers.ModelSerializer):
    #prescription = PrescriptionSerializer()
    # Read-only display fields
    task_name = serializers.CharField(source='task.name', read_only=True)
    task_description = serializers.CharField(source='task.description', read_only=True)
    cohort_info = serializers.SerializerMethodField()
    treatment_extras_count = serializers.SerializerMethodField()
    #treatment_extras = serializers.SerializerMethodField()
    #treatment_extras = TreatmentXtra2Serializer(many=True)

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
            #'treatment_extras',
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

    def _get_treatment_extras(self, obj):
        """Count of treatment extras for this treatment"""
        return TreatmentXtra.objects.filter(treatment=obj)

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
            #"closed",
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
            #'cohort_closed',
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
        assigned_cht = obj.tmpassignchttoply_set.filter(status_current=True).select_related('cohort')
        return AssignChtToPlySerializer(assigned_cht, many=True).data


class SimpleCohortSerializer(serializers.ModelSerializer):
    """Simplified cohort serializer for search results"""
    class Meta:
        model = Cohort
        fields = [
            'cohort_id', 'obj_code', 'species', 'target_ba_m2ha',
            'resid_ba_m2ha', 'site_quality', 'regen_date', 'complete_date',
            'regen_method', 'year_last_cut', 'treatments'
        ]


class SimpleTreatmentSerializer(serializers.ModelSerializer):
    """Simplified treatment serializer for search results"""
    task_name = serializers.CharField(source='task.name', read_only=True)
    task_description = serializers.CharField(source='task.description', read_only=True)

    class Meta:
        model = Treatment
        fields = [
            'treatment_id', 'task', 'task_name', 'task_description',
            'status', 'plan_yr', 'plan_mth', 'complete_date',
            'pct_area', 'results', 'organisation'
        ]


class SimpleAssignChtToPlySerializer(serializers.ModelSerializer):
    """Simplified assignment serializer for search results"""
    cohort_details = SimpleCohortSerializer(source='cohort', read_only=True)

    class Meta:
        model = AssignChtToPly
        fields = [
            'cht2ply_id', 'cohort', 'cohort_details',
            'status_current', 'created_on', 'updated_on'
        ]


class CompartmentSerializer(serializers.ModelSerializer):
    """Serializer for compartment details"""
    class Meta:
        model = Compartments
        fields = ['compartment', 'block', 'district', 'supply', 'region']


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


class SilviculturistCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SilviculturistComment
        fields = [
            's_comment_id',
            'comment',
            'scope',
            'required_action',
            'action_complete',
            'treatment',
            'easting_note_taken',
            'northing_note_taken',
            'created_on',
            'created_by',
            'updated_on',
            'updated_by'
        ]
        read_only_fields = [
            's_comment_id', 'created_on', 'created_by', 'updated_on', 'updated_by'
        ]


class PolygonSearchSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for polygon search with related data"""
    # Basic polygon fields
    compartment_details = CompartmentSerializer(source='compartment', read_only=True)

    # Related data
    assigned_cohorts = serializers.SerializerMethodField()
    treatments = serializers.SerializerMethodField()
    cohorts_count = serializers.SerializerMethodField()
    treatments_count = serializers.SerializerMethodField()
    active_cohorts_count = serializers.SerializerMethodField()

    # Computed fields for easy access in datatable
    obj_codes = serializers.SerializerMethodField()
    species_list = serializers.SerializerMethodField()
    treatment_statuses = serializers.SerializerMethodField()

    # Formatted dates
    created_on_formatted = serializers.SerializerMethodField()
    updated_on_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Polygon
        fields = [
            # Basic polygon info
            'polygon_id', 'name', 'area_ha', 'created_on', 'updated_on',
            'created_by', 'updated_by', 'reason_closed',
            'zcoupeid', 'zstandno', 'zmslink', 'zfea_id', 'geom',

            # Compartment details
            'compartment', 'compartment_details',

            # Spatial precision
            'sp_code',

            # Proposal relation
            'proposal',

            # Computed fields for datatable
            'obj_codes', 'species_list', 'treatment_statuses',
            'created_on_formatted', 'updated_on_formatted',

            # Related data
            'assigned_cohorts', 'treatments',
            'cohorts_count', 'treatments_count', 'active_cohorts_count'
        ]

    def get_assigned_cohorts(self, obj):
        """Get all cohort assignments for this polygon"""
        assignments = obj.assignchttoply_set.all().select_related('cohort')
        return SimpleAssignChtToPlySerializer(assignments, many=True).data

    def get_treatments(self, obj):
        """Get all treatments for cohorts assigned to this polygon"""
        # Get all cohort IDs assigned to this polygon
        cohort_ids = obj.assignchttoply_set.values_list('cohort_id', flat=True)

        # Get treatments for these cohorts
        treatments = Treatment.objects.filter(
            cohort_id__in=cohort_ids
        ).select_related('task').order_by('-complete_date', '-plan_yr', '-plan_mth')

        return SimpleTreatmentSerializer(treatments, many=True).data

    def get_cohorts_count(self, obj):
        """Count of all cohorts assigned to this polygon"""
        return obj.assignchttoply_set.count()

    def get_treatments_count(self, obj):
        """Count of all treatments for cohorts in this polygon"""
        cohort_ids = obj.assignchttoply_set.values_list('cohort_id', flat=True)
        return Treatment.objects.filter(cohort_id__in=cohort_ids).count()

    def get_active_cohorts_count(self, obj):
        """Count of active cohorts assigned to this polygon"""
        return obj.assignchttoply_set.filter(status_current=True).count()

    def get_obj_codes(self, obj):
        """Get list of unique objective codes for datatable display"""
        assignments = obj.assignchttoply_set.filter(status_current=True).select_related('cohort')
        obj_codes = list(set(ass.cohort.obj_code for ass in assignments if ass.cohort.obj_code))
        return ', '.join(obj_codes) if obj_codes else 'N/A'

    def get_species_list(self, obj):
        """Get list of unique species for datatable display"""
        assignments = obj.assignchttoply_set.filter(status_current=True).select_related('cohort')
        species_list = list(set(ass.cohort.species for ass in assignments if ass.cohort.species))
        return ', '.join(species_list) if species_list else 'N/A'

    def get_treatment_statuses(self, obj):
        """Get list of unique treatment statuses for datatable display"""
        cohort_ids = obj.assignchttoply_set.values_list('cohort_id', flat=True)
        treatments = Treatment.objects.filter(cohort_id__in=cohort_ids)

        status_map = {
            'P': 'Planned',
            'D': 'Completed',
            'C': 'Cancelled',
            'F': 'Failed',
            'W': 'Written Off',
            'X': 'Not Required'
        }

        statuses = list(set(
            status_map.get(treat.status, treat.status)
            for treat in treatments
            if treat.status
        ))
        return ', '.join(statuses) if statuses else 'N/A'

    def get_created_on_formatted(self, obj):
        """Get formatted created date"""
        if obj.created_on:
            return obj.created_on.strftime('%Y-%m-%d')
        return None

    def get_updated_on_formatted(self, obj):
        """Get formatted updated date"""
        if obj.updated_on:
            return obj.updated_on.strftime('%Y-%m-%d')
        return None

    def to_representation(self, instance):
        """Custom representation to optimize data structure"""
        data = super().to_representation(instance)

        # Add some computed fields for easier access in frontend
        data['has_active_cohorts'] = self.get_active_cohorts_count(instance) > 0
        data['has_treatments'] = self.get_treatments_count(instance) > 0

        # Add first cohort details for quick access (useful for polygons with single cohort)
        assignments = instance.assignchttoply_set.filter(status_current=True).select_related('cohort').first()
        if assignments and assignments.cohort:
            data['primary_cohort'] = {
                'cohort_id': assignments.cohort.cohort_id,
                'obj_code': assignments.cohort.obj_code,
                'species': assignments.cohort.species,
                'target_ba_m2ha': assignments.cohort.target_ba_m2ha,
                'resid_ba_m2ha': assignments.cohort.resid_ba_m2ha,
                'site_quality': assignments.cohort.site_quality
            }
        else:
            data['primary_cohort'] = None

        return data


class __OperationSerializer(serializers.ModelSerializer):
    # Read-only display fields
    cohort_count = serializers.SerializerMethodField()
    polygon_count = serializers.SerializerMethodField()

    # File upload fields
    silvic_plan_map_file = serializers.FileField(write_only=True, required=False)
    silvic_plan_doc_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Operation
        fields = [
            'op_id',
            'das_id',
            'fea_id',
            'plan_release',
            'silvic_plan_map',
            'silvic_plan_doc',
            'silvic_plan_map_file',
            'silvic_plan_doc_file',
            'cohort_count',
            'polygon_count',
        ]
        read_only_fields = ['op_id', 'silvic_plan_map', 'silvic_plan_doc']

    def get_cohort_count(self, obj):
        """Count of cohorts related to this operation"""
        return Cohort.objects.filter(op_id=obj.op_id).count()

    def get_polygon_count(self, obj):
        """Count of polygons related to this operation via cohorts"""
        # Get polygons through cohort assignments
        cohort_ids = Cohort.objects.filter(op_id=obj.op_id).values_list('cohort_id', flat=True)
        polygon_count = AssignChtToPly.objects.filter(
            cohort_id__in=cohort_ids
        ).values('polygon').distinct().count()
        return polygon_count

    def handle_file_upload(self, file, subdirectory):
        """Handle file upload and return file path/URL"""
        from django.utils import timezone
        import os
        from django.core.files.storage import default_storage

        # Generate unique filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        original_name = file.name
        name, ext = os.path.splitext(original_name)

        # Sanitize filename
        safe_name = name.replace(' ', '_').replace('(', '').replace(')', '')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-'])

        filename = f"{subdirectory}/{safe_name}_{timestamp}{ext}"

        # Save file to storage
        saved_name = default_storage.save(filename, file)

        # Return the saved filename
        return saved_name

    def create(self, validated_data):
        """Handle file uploads during creation"""
        # Extract file data
        map_file = validated_data.pop('silvic_plan_map_file', None)
        doc_file = validated_data.pop('silvic_plan_doc_file', None)

        # Create operation
        operation = super().create(validated_data)

        # Handle file uploads
        if map_file:
            operation.silvic_plan_map = self.handle_file_upload(map_file, 'silvic_plan_maps')

        if doc_file:
            operation.silvic_plan_doc = self.handle_file_upload(doc_file, 'silvic_plan_docs')

        if map_file or doc_file:
            operation.save()

        return operation

    def update(self, instance, validated_data):
        """Handle file uploads during update"""
        # Extract file data
        map_file = validated_data.pop('silvic_plan_map_file', None)
        doc_file = validated_data.pop('silvic_plan_doc_file', None)

        # Update the instance with the remaining validated data
        operation = super().update(instance, validated_data)

        # Handle file uploads if provided
        if map_file:
            operation.silvic_plan_map = self.handle_file_upload(map_file, 'silvic_plan_maps')

        if doc_file:
            operation.silvic_plan_doc = self.handle_file_upload(doc_file, 'silvic_plan_docs')

        if map_file or doc_file:
            operation.save()

        return operation


class OperationSerializer(serializers.ModelSerializer):
    # Read-only display fields
    cohort_count = serializers.SerializerMethodField()
    polygon_count = serializers.SerializerMethodField()

    # File upload fields (write-only for file uploads)
    silvic_plan_map_file = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True
    )
    silvic_plan_doc_file = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Operation
        fields = [
            'op_id',
            'das_id',
            'fea_id',
            'plan_release',
            'silvic_plan_map',
            'silvic_plan_doc',
            'silvic_plan_map_file',
            'silvic_plan_doc_file',
            'cohort_count',
            'polygon_count',
        ]
        read_only_fields = [
            'op_id',
            'silvic_plan_map',
            'silvic_plan_doc',
            'cohort_count',
            'polygon_count'
        ]

    def get_cohort_count(self, obj):
        """Count of cohorts related to this operation"""
        return Cohort.objects.filter(op_id=obj.op_id).count()

    def get_polygon_count(self, obj):
        """Count of polygons related to this operation via cohorts"""
        # Get polygons through cohort assignments
        cohort_ids = Cohort.objects.filter(op_id=obj.op_id).values_list('cohort_id', flat=True)
        polygon_count = AssignChtToPly.objects.filter(
            cohort_id__in=cohort_ids
        ).values('polygon').distinct().count()
        return polygon_count


    def handle_file_upload(self, file, subdirectory, instance=None, field_name=None):
        """Handle file upload and return file path/URL"""
        import os
        from django.utils import timezone
        from django.core.files.storage import default_storage

        # Generate unique filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        original_name = file.name
        name, ext = os.path.splitext(original_name)

        # Sanitize filename
        safe_name = name.replace(' ', '_').replace('(', '').replace(')', '')
        safe_name = ''.join(c for c in safe_name if c.isalnum() or c in ['_', '-', '.'])

        filename = f"{subdirectory}/{safe_name}_{timestamp}{ext}"

        # Delete old file if exists and we're updating
        if instance and field_name:
            old_file = getattr(instance, field_name, None)
            if old_file:
                try:
                    # If old_file is bytes, decode it to get the path string
                    if isinstance(old_file, bytes):
                        old_file_path = old_file.decode('utf-8')
                    elif isinstance(old_file, memoryview):
                        old_file_path = old_file.tobytes().decode('utf-8')
                    else:
                        old_file_path = str(old_file)

                    # Check if it's not empty and exists in storage
                    if old_file_path and default_storage.exists(old_file_path):
                        default_storage.delete(old_file_path)
                        print(f"Deleted old file: {old_file_path}")
                except Exception as e:
                    print(f"Error deleting old file: {e}")

        # Save file to storage
        saved_name = default_storage.save(filename, file)

        return saved_name

    def update(self, instance, validated_data):
        """Handle file uploads during update"""
        import os

        # Extract file data from validated_data
        map_file = validated_data.pop('silvic_plan_map_file', None)
        doc_file = validated_data.pop('silvic_plan_doc_file', None)

        # Get request for user info
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user.username

        # Also check request.FILES as fallback
        if not map_file and request and hasattr(request, 'FILES'):
            map_file = request.FILES.get('silvic_plan_map_file')

        if not doc_file and request and hasattr(request, 'FILES'):
            doc_file = request.FILES.get('silvic_plan_doc_file')

        # Update the instance with the remaining validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle file uploads if provided
        if map_file:
            try:
                saved_map = self.handle_file_upload(
                    map_file,
                    'silvic_plan_maps',
                    instance,
                    'silvic_plan_map'
                )
                # Convert string to bytes for BinaryField
                if saved_map:
                    instance.silvic_plan_map = saved_map.encode('utf-8')
                else:
                    instance.silvic_plan_map = None
                print(f"Updated map file: {saved_map}")
            except Exception as e:
                print(f"Error updating map file: {e}")

        if doc_file:
            try:
                saved_doc = self.handle_file_upload(
                    doc_file,
                    'silvic_plan_docs',
                    instance,
                    'silvic_plan_doc'
                )
                # Convert string to bytes for BinaryField
                if saved_doc:
                    instance.silvic_plan_doc = saved_doc.encode('utf-8')
                else:
                    instance.silvic_plan_doc = None
                print(f"Updated doc file: {saved_doc}")
            except Exception as e:
                print(f"Error updating doc file: {e}")

        # Save the instance
        instance.save()

        return instance

    def create(self, validated_data):
        """Handle file uploads during creation"""
        import os
        from django.utils import timezone
        from django.core.files.storage import default_storage

        # Extract file data from validated_data
        map_file = validated_data.pop('silvic_plan_map_file', None)
        doc_file = validated_data.pop('silvic_plan_doc_file', None)

        # Get request for user info
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user.username
            validated_data['updated_by'] = request.user.username

        # Create operation
        operation = Operation.objects.create(**validated_data)

        # Handle file uploads
        if map_file:
            try:
                saved_map = self.handle_file_upload(map_file, 'silvic_plan_maps')
                if saved_map:
                    operation.silvic_plan_map = saved_map.encode('utf-8')
                print(f"Created map file: {saved_map}")
            except Exception as e:
                print(f"Error saving map file: {e}")

        if doc_file:
            try:
                saved_doc = self.handle_file_upload(doc_file, 'silvic_plan_docs')
                if saved_doc:
                    operation.silvic_plan_doc = saved_doc.encode('utf-8')
                print(f"Created doc file: {saved_doc}")
            except Exception as e:
                print(f"Error saving doc file: {e}")

        if map_file or doc_file:
            operation.save()

        return operation

    def _binary_to_str(self, binary_data):
        """Convert binary data to string if needed"""
        if not binary_data:
            return None

        try:
            if isinstance(binary_data, bytes):
                return binary_data.decode('utf-8')
            elif isinstance(binary_data, memoryview):
                return binary_data.tobytes().decode('utf-8')
            else:
                return str(binary_data)
        except Exception as e:
            print(f"Error converting binary to string: {e}")
            return None

    def to_representation(self, instance):
        """Custom representation to add full URLs for files"""
        representation = super().to_representation(instance)

        # Add full URLs for file fields
        request = self.context.get('request')

        # Convert binary data to string for file paths
        map_path = self._binary_to_str(instance.silvic_plan_map)
        if map_path:
            try:
                if request:
                    representation['silvic_plan_map'] = request.build_absolute_uri(
                        default_storage.url(map_path)
                    )
                else:
                    representation['silvic_plan_map'] = map_path
            except Exception as e:
                print(f"Error generating map URL: {e}")
                representation['silvic_plan_map'] = map_path
        else:
            representation['silvic_plan_map'] = None

        doc_path = self._binary_to_str(instance.silvic_plan_doc)
        if doc_path:
            try:
                if request:
                    representation['silvic_plan_doc'] = request.build_absolute_uri(
                        default_storage.url(doc_path)
                    )
                else:
                    representation['silvic_plan_doc'] = doc_path
            except Exception as e:
                print(f"Error generating doc URL: {e}")
                representation['silvic_plan_doc'] = doc_path
        else:
            representation['silvic_plan_doc'] = None

        return representation

    def validate_fea_id(self, value):
        """Validate FEA ID"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("FEA ID is required")
        return value.strip()

    def validate_das_id(self, value):
        """Validate DAS ID"""
        if value is not None:
            if not isinstance(value, (int, str)):
                raise serializers.ValidationError("DAS ID must be a number or string")
            if isinstance(value, str) and not value.isdigit():
                raise serializers.ValidationError("DAS ID must contain only digits")
        return value

    def validate(self, data):
        """Cross-field validation"""
        # Add any cross-field validation here
        return data
