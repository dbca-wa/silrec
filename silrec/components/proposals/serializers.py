import datetime
import logging

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

import re
import json



from silrec.components.main.serializers import (
    UserSerializerSimple,
    ApplicationTypeSerializer,
    #CommunicationLogEntrySerializer,
    #EmailUserSerializer,
)
from silrec.components.proposals.models import (
    #AmendmentRequest,
    Proposal,
    #ProposalGeometry,
    ProposalType,
    #ProposalUserAction,
    #Referral,
    #SectionChecklist,
    SQLReport,
    TextSearchFieldDisplay,
    TextSearchModelConfig,
)

from silrec.helpers import (
    is_internal,
)

User = get_user_model()


class ProposalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalType
        fields = (
            "id",
            "code",
            "description",
        )

    def get_activities(self, obj):
        return obj.activities.names()


class BaseProposalSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(read_only=True)
    proposal_type = ProposalTypeSerializer()
    application_type = ApplicationTypeSerializer()
    #accessing_user_roles = serializers.SerializerMethodField()
    #proposalgeometry = ProposalGeometrySerializer(many=True, read_only=True)
    #applicant = serializers.SerializerMethodField()
    lodgement_date_display = serializers.SerializerMethodField()
    #applicant = serializers.SerializerMethodField()
    submitter_obj = UserSerializerSimple()
    #groups = serializers.SerializerMethodField(read_only=True)
    #allowed_assessors = EmailUserSerializer(many=True)
    #details_url = serializers.SerializerMethodField(read_only=True)
    details_url = serializers.SerializerMethodField(read_only=True)
    readonly = serializers.SerializerMethodField(read_only=True)
    shapefile_name = serializers.SerializerMethodField(read_only=True)
    #approval = serializers.SerializerMethodField(read_only=True, allow_null=True)
    # Gis data fields
#    identifiers = serializers.SerializerMethodField()
#    names = serializers.SerializerMethodField()
#    acts = serializers.SerializerMethodField()
#    tenures = serializers.SerializerMethodField()
#    categories = serializers.SerializerMethodField()
#    regions = serializers.SerializerMethodField()
#    districts = serializers.SerializerMethodField()
#    lgas = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
            "id",
            "model_name",
            #"allowed_assessors",
            "application_type",
            "proposal_type",
            "title",
            "processing_status",
            "processing_status_id",
            #"submitter_obj",
            #"assigned_officer",
            "previous_application",
            #"get_history",
            "lodgement_date",
            "lodgement_number",
            "details_url",
            #"supporting_documents",
            #"requirements",
            "readonly",
            "shapefile_name",
            #"approval",
#            "can_user_edit",
#            "can_user_view",
#            "documents_url",
#            "reference",
#            "can_officer_process",
#            "accessing_user_roles",
#            "added_internally",
#            "details_text",
#            "proposalgeometry",
#            "groups",
#            "details_url",
        )
        #read_only_fields = ("supporting_documents",)

#    def get_groups(self, obj):
#        group_ids = obj.groups.values_list("group__id", flat=True)
#        group_qs = Group.objects.filter(id__in=group_ids).values("id", "name")
#        return GroupSerializer(group_qs, many=True).data

    def get_shapefile_name(self, obj):
        doc = obj.shapefile_documents.last()
        return doc.input_name if doc else None

    def get_lodgement_date_display(self, obj):
        if obj.lodgement_date:
            return (
                obj.lodgement_date.strftime("%d/%m/%Y")
                + " at "
                + obj.lodgement_date.strftime("%-I:%M %p")
            )

    def get_details_url(self, obj):
        request = self.context["request"]
        if request.user.is_authenticated:
            if is_internal(request):
                return reverse("internal-proposal-detail", kwargs={"pk": obj.id})
            else:
                return reverse(
                    "external-proposal-detail", kwargs={"proposal_pk": obj.id}
                )

#    def get_applicant(self, obj):
#        if isinstance(obj.applicant, Organisation):
#            return obj.applicant.ledger_organisation_name
#        elif isinstance(obj.applicant, ProposalApplicant):
#            return obj.applicant.full_name
#        elif isinstance(obj.applicant, EmailUser):
#            return f"{obj.applicant.first_name} {obj.applicant.last_name}"
#        else:
#            return "Applicant not yet assigned"

#    def get_applicant(self, obj):
#        return UserSerializerSimple(obj.applicant).data

#    def get_documents_url(self, obj):
#        return "/media/{}/proposals/{}/documents/".format(
#            settings.MEDIA_APP_DIR, obj.id
#        )

    def get_readonly(self, obj):
        return False

    def get_submitter_obj(self, obj):
        if obj.submitter:
            return obj.submitter_obj
        else:
            return None

    def get_processing_status(self, obj):
        #return obj.get_processing_status_display()
        return obj.get_processing_status_display()

#    def get_accessing_user_roles(self, proposal):
#        request = self.context.get("request")
#        accessing_user = request.user
#        roles = []
#
#        for choice in GROUP_NAME_CHOICES:
#            group = SystemGroup.objects.get(name=choice[0])
#            ids = group.get_system_group_member_ids()
#            if accessing_user.id in ids:
#                roles.append(group.name)
#
#        referral_ids = list(proposal.referrals.values_list("referral", flat=True))
#        if accessing_user.id in referral_ids:
#            roles.append("referral")
#
#        return roles

#class ProposalSerializer(serializers.ModelSerializer):
#
#    class Meta:
#        model = Proposal
#        #fields = "__all__"
#        fields = (
#            "id",
#            "model_name",
#        )

#
class ProposalSerializer(BaseProposalSerializer):
    #submitter_obj = serializers.SerializerMethodField(read_only=True)
    model_name = serializers.SerializerMethodField(read_only=True)
    submitter_obj = UserSerializerSimple()
    processing_status = serializers.SerializerMethodField(read_only=True)
    processing_status_id = serializers.SerializerMethodField(read_only=True)
    # Had to add assessor mode and lodgement versions for this serializer to work for
    # external user that is a referral
    assessor_mode = serializers.SerializerMethodField(read_only=True)
    details_url = serializers.SerializerMethodField(read_only=True)
    shapefile_name = serializers.SerializerMethodField(read_only=True)
    #lodgement_versions = serializers.SerializerMethodField(read_only=True)
    #referrals = ProposalReferralSerializer(many=True)
    #additional_document_types = ProposalAdditionalDocumentTypeSerializer(
    #    many=True, read_only=True
    #)
    #assessor_assessment = serializers.SerializerMethodField(read_only=True)
    proposalgeometry = serializers.SerializerMethodField(read_only=True)
    proposalgeometry_hist = serializers.SerializerMethodField(read_only=True)
    proposalgeometry_processed = serializers.SerializerMethodField(read_only=True)
    proposalgeometry_processed_iters = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proposal
        #fields = "__all__"
        fields = (
            "id",
            "model_name",
            #"allowed_assessors",
            "application_type",
            "proposal_type",
            "title",
            "processing_status",
            "processing_status_id",
            "submitter_obj",
            "previous_application",
            "lodgement_date",
            "lodgement_number",
            "details_url",
            "readonly",
            "assessor_mode",
            "processing_status_id",
            "shapefile_name",
            "proposalgeometry",
            "proposalgeometry_hist",
            "proposalgeometry_processed",
            "proposalgeometry_processed_iters",
        )

    def get_shapefile_name(self, obj):
        doc = obj.shapefile_documents.last()
        return doc.input_name if doc else None

    def get_proposalgeometry(self, obj):
        return obj.shapefile_json

    def get_proposalgeometry_hist(self, obj):
        return obj.geojson_data_hist

    def get_proposalgeometry_processed(self, obj):
        return obj.geojson_data_processed

    def get_proposalgeometry_processed_iters(self, obj):
        return obj.geojson_data_processed_iters

    def get_model_name(self, obj):
        return obj._meta.model_name

    def get_processing_status_id(self, obj):
        return obj.get_processing_status_display()

    def get_assessor_mode(self, obj):
        return True

    def get_readonly(self, obj):
        return obj.can_user_view

    def get_submitter_obj(self, obj):
        if obj.submitter:
            return obj.submitter_obj
        else:
            return None

    def get_details_url(self, obj):
        request = self.context["request"]
        if request.user.is_authenticated:
            if is_internal(request):
                return reverse("internal-proposal-detail", kwargs={"pk": obj.id})
            else:
                return reverse(
                    "external-proposal-detail", kwargs={"proposal_pk": obj.id}
                )


#    def get_proposalgeometry(self, obj):
#        # TODO - JM
#        return {}

class ListProposalMinimalSerializer(serializers.ModelSerializer):
    #proposalgeometry = ProposalGeometrySerializer(many=True, read_only=True)
#    application_type_name_display = serializers.CharField(
#        read_only=True, source="application_type.name"
#    )
    processing_status_display = serializers.CharField(
        read_only=True, source="get_processing_status"
    )
    lodgement_date_display = serializers.DateTimeField(
        read_only=True, format="%d/%m/%Y", source="lodgement_date"
    )

    class Meta:
        model = Proposal
        fields = (
            "id",
            "processing_status",
            "processing_status_display",
            #"proposalgeometry",
            #"application_type_name_display",
            "application_type_id",
            "lodgement_number",
            "lodgement_date",
            "lodgement_date_display",
        )

class ListProposalSerializer(BaseProposalSerializer):
    #submitter = serializers.SerializerMethodField(read_only=True)
    processing_status_id = serializers.SerializerMethodField(read_only=True)
    proposalgeometry = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proposal
        fields = (
            "id",
            "application_type",
            "proposal_type",
            "title",
            "processing_status",
            "processing_status_id",
            #"review_status",
            "submitter_obj",
            "previous_application",
            #"get_history",
            "lodgement_date",
            "lodgement_number",
            "readonly",
            #"can_user_edit",
            #"can_user_view",
            #"can_officer_process",
            #"allowed_assessors",
            "proposal_type",
            #"accessing_user_can_process",
            #"groups",
            "proposalgeometry",
        )
        # the serverSide functionality of datatables is such that only columns that have
        # field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
            "id",
            "application_type",
            "proposal_type",
            "title",
            "processing_status",
            "processing_status_id",
            "submitter_obj",
            "previous_application",
            "lodgement_date",
            "lodgement_number",
            #"can_user_edit",
            #"can_user_view",
            #"can_officer_process",
            #"accessing_user_can_process",
            #"groups",
        )

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return ""

    def get_processing_status_id(self, obj):
        return obj.processing_status

    def get_proposalgeometry(self, obj):
        # TODO - JM
        return {}


class SQLReportSerializer(serializers.ModelSerializer):
    """Serializer for SQL Report model"""

    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    allowed_groups_display = serializers.SerializerMethodField()

    class Meta:
        model = SQLReport
        fields = [
            'id', 'name', 'description', 'report_type', 'base_sql',
            'where_clauses', 'order_by', 'export_formats', 'columns',
            'allowed_groups', 'allowed_groups_display', 'is_active',
            'created_by', 'created_by_name', 'created_on', 'updated_on'
        ]
        read_only_fields = ['created_by', 'created_on', 'updated_on']

    def get_allowed_groups_display(self, obj):
        """Get display names for allowed groups"""
        return [group.name for group in obj.allowed_groups.all()]

    def validate_where_clauses(self, value):
        """Validate WHERE clauses JSON"""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError("WHERE clauses must be a list")

            for i, clause in enumerate(value):
                if not isinstance(clause, dict):
                    raise serializers.ValidationError(f"Clause {i+1} must be a dictionary")

                required_fields = ['field', 'operator', 'parameter_name', 'label', 'field_type']
                for field in required_fields:
                    if field not in clause:
                        raise serializers.ValidationError(f"Clause {i+1} missing '{field}' field")

                # Validate field_type
                valid_field_types = [choice[0] for choice in SQLReport.FIELD_TYPE_CHOICES]
                if clause['field_type'] not in valid_field_types:
                    raise serializers.ValidationError(
                        f"Clause {i+1}: Invalid field_type '{clause['field_type']}'. "
                        f"Must be one of {valid_field_types}"
                    )

        return value

    def validate_export_formats(self, value):
        """Validate export formats"""
        valid_formats = ['excel', 'csv', 'pdf', 'shapefile']
        for fmt in value:
            if fmt not in valid_formats:
                raise serializers.ValidationError(f"Invalid export format: {fmt}")
        return value



from rest_framework import serializers
from django.db import models
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone
from django.utils.dateparse import parse_date
import re
from datetime import datetime

User = get_user_model()


class FlexibleDateField(serializers.DateField):
    """Custom DateField that accepts multiple formats and handles empty/blank values"""

    def to_internal_value(self, value):
        # Handle empty/blank values
        if value in [None, '', 'null', 'undefined']:
            return None

        # If it's already a date object, return it
        if isinstance(value, datetime.date):
            return value

        # Try to parse common date formats
        if isinstance(value, str):
            # Trim whitespace
            value = value.strip()

            # List of possible date formats to try
            date_formats = [
                '%Y-%m-%d',  # 2024-01-15 (ISO format - HTML date input)
                '%d/%m/%Y',  # 15/01/2024
                '%m/%d/%Y',  # 01/15/2024
                '%d-%m-%Y',  # 15-01-2024
                '%m-%d-%Y',  # 01-15-2024
                '%Y/%m/%d',  # 2024/01/15
                '%d.%m.%Y',  # 15.01.2024
                '%m.%d.%Y',  # 01.15.2024
                '%b %d, %Y', # Jan 15, 2024
                '%B %d, %Y', # January 15, 2024
            ]

            for date_format in date_formats:
                try:
                    return datetime.strptime(value, date_format).date()
                except (ValueError, TypeError):
                    continue

            # If all parsing attempts fail, use Django's parse_date
            parsed_date = parse_date(value)
            if parsed_date:
                return parsed_date

            # If we can't parse it, return None (or raise validation error)
            # For backward compatibility, we'll return None
            return None

        # For any other type, use parent's implementation
        return super().to_internal_value(value)

    def to_representation(self, value):
        # Return ISO format for API responses
        if value is None:
            return None
        return value.isoformat()


class TextSearchResultSerializer(serializers.Serializer):
    """Serializer for text search results"""
    model_type = serializers.CharField()
    model_display = serializers.CharField()
    record_id = serializers.IntegerField()
    field_found = serializers.CharField()
    field_display = serializers.CharField()
    text_preview = serializers.CharField()
    matching_text = serializers.CharField()
    created_on = serializers.DateTimeField()
    created_by = serializers.CharField()
    action_url = serializers.CharField()

    # Optional detail fields
    obj_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    task_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    polygon_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    compartment = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def to_representation(self, instance):
        """Custom representation to ensure all fields are included"""
        data = super().to_representation(instance)

        # Add details field
        details = []
        if instance.get('obj_code'):
            details.append(f"Objective: {instance['obj_code']}")
        if instance.get('task_name'):
            details.append(f"Task: {instance['task_name']}")
        if instance.get('polygon_name'):
            details.append(f"Polygon: {instance['polygon_name']}")
        if instance.get('compartment'):
            details.append(f"Compartment: {instance['compartment']}")

        data['details'] = '<br/>'.join(details) if details else 'No additional details'
        return data


class JSONStringField(serializers.Field):
    """Custom field to handle JSON strings"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {} if 'search' in self.field_name else []
        elif data is None:
            return {} if 'search' in self.field_name else []
        return data

    def to_representation(self, value):
        return value


class TextSearchRequestSerializer(serializers.Serializer):
    """Serializer for text search request parameters"""
    search_text = serializers.CharField(min_length=2, required=True, allow_blank=False)
    field = serializers.CharField(required=False, default='all', allow_blank=True)
    match_type = serializers.ChoiceField(
        choices=['contains', 'exact', 'starts_with', 'ends_with'],
        default='contains'
    )
    date_from = FlexibleDateField(required=False, allow_null=True, default=None)
    date_to = FlexibleDateField(required=False, allow_null=True, default=None)
    case_sensitive = serializers.BooleanField(default=False)
    model = serializers.ChoiceField(
        choices=[
            'all', 'proposal', 'polygon', 'cohort', 'treatment',
            'treatment_xtra', 'survey_assessment_document',
            'silviculturist_comment', 'prescription'
        ],
        default='all'
    )
    fields = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=['comments', 'description', 'title', 'name', 'results']
    )
    search_terms = serializers.CharField(required=False, default='', allow_blank=True)

    # Datatable parameters
    draw = serializers.IntegerField(required=False, default=1, min_value=0)
    start = serializers.IntegerField(required=False, default=0, min_value=0)
    length = serializers.IntegerField(required=False, default=25, min_value=1, max_value=1000)

    # Use custom JSON fields for order and search
    order = JSONStringField(required=False, default=[])
    search = JSONStringField(required=False, default={})

    def validate_fields(self, value):
        """Ensure fields is always a list, even if empty"""
        if isinstance(value, str):
            if value:
                return [field.strip() for field in value.split(',') if field.strip()]
            else:
                return ['comments', 'description', 'title', 'name', 'results']
        elif value is None:
            return ['comments', 'description', 'title', 'name', 'results']
        return value

    def validate(self, data):
        """Additional validation for date range"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                "date_from": "Date From cannot be after Date To",
                "date_to": "Date To cannot be before Date From"
            })

        return data


class TextSearchSimpleSerializer(serializers.Serializer):
    """Simplified serializer for quick search (GET requests)"""
    search_text = serializers.CharField(min_length=2, required=True)
    model = serializers.CharField(required=False, default='all')
    fields = serializers.CharField(required=False, default='comments,description,title,name,results')

    def to_internal_value(self, data):
        # Convert query params to internal format
        internal_data = {}

        # Handle search_text
        if 'search_text' in data:
            internal_data['search_text'] = data['search_text']

        # Handle model
        if 'model' in data:
            internal_data['model'] = data['model']

        # Handle fields (convert comma-separated string to list)
        if 'fields' in data and data['fields']:
            internal_data['fields'] = [field.strip() for field in data['fields'].split(',')]

        # Handle date fields
        if 'date_from' in data and data['date_from']:
            field = FlexibleDateField()
            internal_data['date_from'] = field.to_internal_value(data['date_from'])

        if 'date_to' in data and data['date_to']:
            field = FlexibleDateField()
            internal_data['date_to'] = field.to_internal_value(data['date_to'])

        # Handle other fields
        for field in ['field', 'match_type', 'case_sensitive']:
            if field in data:
                internal_data[field] = data[field]

        return internal_data


class TextSearchFieldDisplaySerializer(serializers.ModelSerializer):
    """Serializer for TextSearchFieldDisplay model"""

    class Meta:
        model = TextSearchFieldDisplay
        fields = ['id', 'field_name', 'display_name', 'is_active', 'order', 'description']
        read_only_fields = ['created_on', 'updated_on', 'created_by']


class TextSearchModelConfigSerializer(serializers.ModelSerializer):
    """Serializer for TextSearchModelConfig model"""
    search_fields_list = serializers.SerializerMethodField()
    field_displays = serializers.SerializerMethodField()

    class Meta:
        model = TextSearchModelConfig
        fields = [
            'id', 'key', 'display_name', 'model_name', 'search_fields',
            'search_fields_list', 'field_displays', 'is_active', 'order',
            'date_field', 'id_field', 'detail_fields', 'url_pattern'
        ]

    def get_search_fields_list(self, obj):
        """Get search fields as a list"""
        return obj.get_search_fields_list()

    def get_field_displays(self, obj):
        """Get related field displays for this model"""
        search_fields = obj.get_search_fields_list()

        # Get all active field displays
        field_displays = TextSearchFieldDisplay.objects.filter(
            is_active=True
        ).order_by('order')

        # Filter to only include fields that are in this model's search_fields
        # or if no specific search_fields are defined, include all
        if search_fields:
            field_displays = field_displays.filter(field_name__in=search_fields)

        return TextSearchFieldDisplaySerializer(field_displays, many=True).data


# Add to serializers.py after existing serializers
import zipfile
import tempfile
import os
import geopandas as gpd
from django.core.files.base import ContentFile

class ShapefileUploadSerializer(serializers.Serializer):
    """Serializer for shapefile upload validation"""
    shapefile = serializers.FileField(
        required=True,
        allow_empty_file=False,
        #max_upload_size=52428800,  # 50MB limit
    )
    proposal_id = serializers.IntegerField(required=True)

    def validate_shapefile(self, value):
        # Check file extension
        if not value.name.lower().endswith('.zip'):
            raise serializers.ValidationError("File must be a .zip file")

        # Check file size (already handled by max_upload_size)

        return value

    def validate(self, data):
        # Additional validation can be done here
        return data


# TODO check if this class can be removed
class ShapefileProcessResultSerializer(serializers.Serializer):
    """Serializer for shapefile processing results"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    feature_count = serializers.IntegerField()
    geojson = serializers.DictField(required=False)
    errors = serializers.ListField(child=serializers.CharField(), required=False)

# Add to serializers.py after ShapefileProcessResultSerializer

class ShapefileProcessRequestSerializer(serializers.Serializer):
    """Serializer for shapefile processing request"""
    threshold = serializers.FloatField(required=False, default=5.0, min_value=0.1, max_value=100)
    user_id = serializers.IntegerField(required=True)
    proposal_id = serializers.IntegerField(required=True)

    def validate_threshold(self, value):
        if value < 0.1:
            raise serializers.ValidationError("Threshold must be at least 0.1")
        if value > 100:
            raise serializers.ValidationError("Threshold must not exceed 100")
        return value


class ShapefileProcessResponseSerializer(serializers.Serializer):
    """Serializer for shapefile processing response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    proposal = serializers.DictField(required=False)
    feature_count = serializers.IntegerField(required=False)
    processed_geometries = serializers.DictField(required=False)
    warnings = serializers.ListField(child=serializers.CharField(), required=False)

