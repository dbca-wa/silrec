from typing import Any

from django.contrib import admin
from django.db.models import TextField
from django import forms
from django.forms import Textarea
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.urls import re_path
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.gis.geos import GEOSGeometry

from django.utils import timezone
import json


from silrec import helpers
#from silrec.components.proposals.models import (
#    SQLReport,
#    TextSearchModelConfig,
#    TextSearchFieldDisplay
#)
from silrec.components.proposals import models



@admin.register(models.ProposalType)
class ProposalTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "description"]
    ordering = ("code",)
    list_filter = ("code",)


#class ProposalDocumentInline(admin.TabularInline):
#    model = models.ProposalDocument
#    extra = 0
#
#
#@admin.register(models.AmendmentReason)
#class AmendmentReasonAdmin(admin.ModelAdmin):
#    list_display = ["reason"]



class SQLReportAdminForm(forms.ModelForm):
    """Form for SQL Report with enhanced validation"""

    where_clauses_display = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 15, 'cols': 100, 'style': 'font-family: monospace;'}),
        required=False,
        help_text="""
        JSON array of WHERE clause definitions. Field types:
        - select: Single selection dropdown
        - multiselect: Multiple selection using Select2 (values become IN clause)
        - text: Text input
        - number: Number input
        - date: Date picker
        - year: Year selector
        - month: Month selector
        - range: Two values for BETWEEN operator

        Example:
        [
            {
                "field": "year",
                "operator": "YEAR",
                "parameter_name": "year",
                "label": "Select Year",
                "field_type": "select",
                "options_query": "SELECT DISTINCT EXTRACT(YEAR FROM date_column) FROM table ORDER BY 1 DESC",
                "default_value": "2024",
                "required": true
            },
            {
                "field": "supply",
                "operator": "IN",
                "parameter_name": "supply",
                "label": "Select Supply(s)",
                "field_type": "multiselect",
                "options_query": "SELECT DISTINCT supply FROM compartments ORDER BY supply",
                "required": true
            }
        ]
        """
    )

    class Meta:
        model = models.SQLReport
        fields = '__all__'
        widgets = {
            'base_sql': forms.Textarea(attrs={'rows': 10, 'cols': 100, 'style': 'font-family: monospace;'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'order_by': forms.TextInput(attrs={'style': 'width: 100%;'}),
            'export_formats': forms.TextInput(attrs={'placeholder': '["excel", "csv", "pdf", "shapefile"]'}),
            'columns': forms.Textarea(attrs={'rows': 5, 'cols': 100, 'style': 'font-family: monospace;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If we have an instance, convert where_clauses list to JSON string for display
        if self.instance and self.instance.where_clauses:
            try:
                self.initial['where_clauses_display'] = json.dumps(
                    self.instance.where_clauses,
                    indent=2,
                    ensure_ascii=False
                )
            except (TypeError, ValueError):
                self.initial['where_clauses_display'] = str(self.instance.where_clauses)

    def clean_where_clauses_display(self):
        """Validate and convert WHERE clauses JSON string to list"""
        data = self.cleaned_data.get('where_clauses_display', '')
        if not data:
            return []

        try:
            clauses = json.loads(data)
            if not isinstance(clauses, list):
                raise forms.ValidationError("WHERE clauses must be a JSON array")

            # Validate each clause
            for i, clause in enumerate(clauses):
                if not isinstance(clause, dict):
                    raise forms.ValidationError(f"Clause {i+1} must be a JSON object")

                required_fields = ['field', 'operator', 'parameter_name', 'label', 'field_type']
                for field in required_fields:
                    if field not in clause:
                        raise forms.ValidationError(f"Clause {i+1} missing '{field}' field")

                # Validate field_type
                valid_field_types = [choice[0] for choice in SQLReport.FIELD_TYPE_CHOICES]
                if clause['field_type'] not in valid_field_types:
                    raise forms.ValidationError(
                        f"Clause {i+1}: Invalid field_type '{clause['field_type']}'. "
                        f"Must be one of {valid_field_types}"
                    )

                # For multiselect, operator should typically be IN
                if clause['field_type'] == 'multiselect' and clause.get('operator') not in ['IN', 'NOT IN']:
                    clause['operator'] = 'IN'  # Auto-correct
                    clause['recommended_operator'] = 'IN'

                # For range field_type, operator should be BETWEEN
                if clause['field_type'] == 'range' and clause.get('operator') != 'BETWEEN':
                    clause['operator'] = 'BETWEEN'  # Auto-correct

            return clauses

        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON: {str(e)}")

    def clean_export_formats(self):
        """Validate export formats JSON string"""
        data = self.cleaned_data.get('export_formats')
        if data:
            if isinstance(data, str):
                try:
                    formats = json.loads(data)
                    if not isinstance(formats, list):
                        raise forms.ValidationError("Export formats must be a JSON array")
                    return formats
                except json.JSONDecodeError as e:
                    raise forms.ValidationError(f"Invalid JSON: {str(e)}")
        return data or []

    def clean_columns(self):
        """Validate columns JSON string"""
        data = self.cleaned_data.get('columns')
        if data:
            if isinstance(data, str):
                try:
                    columns = json.loads(data)
                    if not isinstance(columns, list):
                        raise forms.ValidationError("Columns must be a JSON array")
                    return columns
                except json.JSONDecodeError as e:
                    raise forms.ValidationError(f"Invalid JSON: {str(e)}")
        return data or []

    def save(self, commit=True):
        """Save the form, converting where_clauses_display to where_clauses"""
        # Get the cleaned where_clauses from the display field
        where_clauses = self.cleaned_data.get('where_clauses_display', [])
        self.instance.where_clauses = where_clauses

        # Handle export_formats and columns if they're strings
        if isinstance(self.instance.export_formats, str):
            try:
                self.instance.export_formats = json.loads(self.instance.export_formats)
            except json.JSONDecodeError:
                self.instance.export_formats = []

        if isinstance(self.instance.columns, str):
            try:
                self.instance.columns = json.loads(self.instance.columns)
            except json.JSONDecodeError:
                self.instance.columns = []

        return super().save(commit)

@admin.register(models.SQLReport)
class SQLReportAdmin(admin.ModelAdmin):
    form = SQLReportAdminForm
    list_display = ['name', 'report_type', 'is_active', 'created_on', 'preview_sql']
    list_filter = ['report_type', 'is_active', 'created_on']
    search_fields = ['name', 'description', 'base_sql']
    filter_horizontal = ['allowed_groups']

    # Customize the fields to use our display field instead of the actual field
    fieldsets = (
        ('Report Information', {
            'fields': ('name', 'description', 'report_type', 'is_active', 'allowed_groups')
        }),
        ('SQL Configuration', {
            'fields': ('base_sql', 'where_clauses_display', 'order_by'),
            'description': """
            <div style="background: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin-bottom: 15px;">
                <strong>SQL Configuration Guide:</strong>
                <ul>
                    <li>Use <code>{where_clause}</code> as a placeholder for dynamic WHERE conditions</li>
                    <li>WHERE clauses JSON must be a valid array of objects with: field, operator, parameter_name, label, field_type</li>
                    <li>For multiselect parameters, use IN operator</li>
                    <li>For range parameters, use BETWEEN operator</li>
                    <li>Use PostgreSQL syntax</li>
                </ul>
            </div>
            """
        }),
        ('Output Options', {
            'fields': ('export_formats', 'columns'),
            'description': 'Configure export formats and column display options'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_on', 'updated_on']

    def preview_sql(self, obj):
        """Display a preview of the SQL"""
        preview = obj.base_sql[:100] + "..." if len(obj.base_sql) > 100 else obj.base_sql
        return format_html(
            '<code style="background: #f8f9fa; padding: 2px 5px; border-radius: 3px; font-size: 0.9em;">{}</code>',
            preview
        )
    preview_sql.short_description = 'SQL Preview'

    def save_model(self, request, obj, form, change):
        """Set created_by user"""
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)



class TextSearchModelConfigForm(forms.ModelForm):
    """Form for TextSearchModelConfig with enhanced JSON field editing"""

    detail_fields_json = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        required=False,
        help_text="Enter as JSON list, e.g., [\"title\", \"name\", \"compartment\"]"
    )

    class Meta:
        model = models.TextSearchModelConfig
        fields = '__all__'
        widgets = {
            'search_fields': forms.Textarea(attrs={'rows': 3, 'cols': 50}),
            'url_pattern': forms.TextInput(attrs={'style': 'width: 80%;'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-populate JSON field if instance exists
        if self.instance and self.instance.pk and self.instance.detail_fields:
            try:
                self.initial['detail_fields_json'] = json.dumps(
                    self.instance.detail_fields,
                    indent=2
                )
            except:
                self.initial['detail_fields_json'] = str(self.instance.detail_fields)

    def clean_detail_fields_json(self):
        """Validate and convert JSON string"""
        data = self.cleaned_data.get('detail_fields_json', '')
        if not data or data == 'null':
            return []

        try:
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                raise forms.ValidationError("Must be a JSON array (list)")

            # Validate each item is a string
            for i, item in enumerate(parsed):
                if not isinstance(item, str):
                    raise forms.ValidationError(
                        f"Item {i} must be a string, got {type(item).__name__}"
                    )

            return parsed
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f"Invalid JSON: {str(e)}")

    def save(self, commit=True):
        # Get the JSON data from the form field
        detail_fields_json = self.cleaned_data.get('detail_fields_json', '')
        if detail_fields_json and detail_fields_json != 'null':
            try:
                self.instance.detail_fields = json.loads(detail_fields_json)
            except:
                self.instance.detail_fields = []

        return super().save(commit)


@admin.register(models.TextSearchModelConfig)
class TextSearchModelConfigAdmin(admin.ModelAdmin):
    form = TextSearchModelConfigForm
    list_display = [
        'key', 'display_name', 'model_name',
        'is_active', 'order', 'search_fields', 'get_search_fields_count'
    ]
    list_filter = ['is_active', 'key']
    search_fields = ['key', 'display_name', 'model_name']
    list_editable = ['is_active', 'order']

    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'display_name', 'model_name', 'is_active', 'order')
        }),
        ('Field Configuration', {
            'fields': ('search_fields', 'date_field', 'id_field')
        }),
        ('Display Configuration', {
            'fields': ('detail_fields_json', 'url_pattern')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_on', 'updated_on']

    def get_search_fields_count(self, obj):
        return len(obj.get_search_fields_list())
    get_search_fields_count.short_description = 'Search Fields'

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.TextSearchFieldDisplay)
class TextSearchFieldDisplayAdmin(admin.ModelAdmin):
    list_display = [
        'field_name', 'display_name', 'is_active', 'order', 'description_short'
    ]
    list_filter = ['is_active']
    search_fields = ['field_name', 'display_name', 'description']
    list_editable = ['display_name', 'is_active', 'order']

    fieldsets = (
        ('Basic Information', {
            'fields': ('field_name', 'display_name', 'is_active', 'order')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_on', 'updated_on']

    def description_short(self, obj):
        if obj.description and len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description or "-"
    description_short.short_description = 'Description'

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.ShapefileAttributeConfig)
class ShapefileAttributeConfigAdmin(admin.ModelAdmin):
    list_display = [
        'application_type', 'field_name', 'display_name',
        'target_db_field', 'is_mandatory', 'is_reserved', 'data_type', 'order'
    ]
    list_filter = ['application_type', 'is_mandatory', 'data_type']
    search_fields = ['field_name', 'display_name', 'target_db_field']
    list_editable = ['is_mandatory', 'is_reserved', 'order', 'data_type']  # target_db_field not editable here due to length
    ordering = ['application_type', 'order', 'field_name']
    fieldsets = (
        (None, {
            'fields': ('application_type', 'field_name', 'display_name')
        }),
        ('Validation', {
            'fields': ('is_mandatory', 'is_reserved', 'data_type', 'order')
        }),
        ('Database Mapping', {
            'fields': ('target_db_field',),
            'description': (
                "Optionally link this shapefile attribute to a database field. "
                "Use the format <code>app_base.app_label.model_name.field_name</code> (e.g., <code>silrec.forest_blocks.polygon.name</code>)."
            )
        }),
    )



@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for analysing audit logs.
    Provides rich display of changes, filtering by table/operation/user,
    and links to related proposal and user records.
    """
    change_form_template = "admin/silrec/auditlog/change_form.html"

    list_display = [
        'id',
        'timestamp',
        'table_name',
        'record_id',
        'operation',
        'user_link',
        'proposal_link',
        'changes_summary'
    ]
    list_filter = [
        'table_name',
        'operation',
        'user',
        ('timestamp', admin.DateFieldListFilter),   # explicit date range filter
        ('proposal', admin.RelatedOnlyFieldListFilter),  # proposal dropdown
    ]
    search_fields = [
        'table_name',
        'record_id',
        'user__username',
        'proposal__lodgement_number',
    ]
    date_hierarchy = 'timestamp'          # Quick date drill-down
    readonly_fields = [
        'table_name',
        'record_id',
        'proposal',
        'operation',
        'user',
        'timestamp',
        'formatted_old_values',
        'formatted_new_values',
    ]
    fieldsets = (
        (None, {
            'fields': ('timestamp', 'user', 'proposal')
        }),
        ('Operation Details', {
            'fields': ('table_name', 'record_id', 'operation')
        }),
        ('Data Changes', {
            'fields': ('formatted_old_values', 'formatted_new_values'),
            'description': 'Old and new values shown as formatted JSON. '
                           'For INSERT operations old_values is null; for DELETE new_values is null.'
        }),
    )

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # Prepare the extra context dictionary (or use an empty one)
        extra_context = extra_context or {}

        # If we are editing an existing object (object_id is not None)
        if object_id:
            # Retrieve the audit log instance
            obj = self.get_object(request, object_id)
            if obj:
                # Add the geometry strings to the context
                extra_context['old_geometry'] = self.old_geometry(obj)
                extra_context['new_geometry'] = self.new_geometry(obj)

        # Call the parent class method to continue normal rendering
        return super().changeform_view(request, object_id, form_url, extra_context)

    def user_link(self, obj):
        """Link to the User admin page."""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_username())
        return "-"
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user'

    def proposal_link(self, obj):
        """Link to the internal proposal detail page (opens in new tab)."""
        if obj.proposal:
            url = reverse('internal-proposal-detail', args=[obj.proposal.id])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.proposal.lodgement_number)
        return "-"
    proposal_link.short_description = 'Proposal'
    proposal_link.admin_order_field = 'proposal'

    def changes_summary(self, obj):
        """Short summary of what changed."""
        if obj.operation == 'INSERT':
            return "New record created"
        elif obj.operation == 'DELETE':
            return "Record deleted"
        elif obj.operation == 'UPDATE' and obj.old_values and obj.new_values:
            changed = set(obj.old_values.keys()) & set(obj.new_values.keys())
            return f"{len(changed)} field(s) changed"
        return "-"
    changes_summary.short_description = 'Changes'

    def formatted_old_values(self, obj):
        """Pretty‑printed JSON for old values."""
        if obj.old_values:
            return format_html(
                '<pre style="max-height: 300px; overflow: auto; background: #f8f9fa; padding: 5px;">{}</pre>',
                json.dumps(obj.old_values, indent=2)
            )
        return "-"
    formatted_old_values.short_description = 'Old Values'

    def formatted_new_values(self, obj):
        """Pretty‑printed JSON for new values."""
        if obj.new_values:
            return format_html(
                '<pre style="max-height: 300px; overflow: auto; background: #f8f9fa; padding: 5px;">{}</pre>',
                json.dumps(obj.new_values, indent=2)
            )
        return "-"
    formatted_new_values.short_description = 'New Values'

    def old_geometry(self, obj):
        """Return a GeoJSON Feature with geometry and properties from old_values."""
        if obj.table_name == 'polygon' and obj.old_values:
            geom = obj.old_values.get('geom')
            if geom:
                try:
                    g = GEOSGeometry(json.dumps(geom))
                    g.srid = 28350
                    g.transform(4326)
                    # Extract properties from old_values
                    polygon_id = obj.old_values.get('polygon_id')
                    area_ha = obj.old_values.get('area_ha')
                    feature = {
                        'type': 'Feature',
                        'geometry': json.loads(g.geojson),
                        'properties': {
                            'polygon_id': polygon_id,
                            'area_ha': area_ha,
                        }
                    }
                    return json.dumps(feature)
                except Exception as e:
                    # Optionally log the error
                    return None
        return None

    def new_geometry(self, obj):
        """Return a GeoJSON Feature with geometry and properties from new_values."""
        if obj.table_name == 'polygon' and obj.new_values:
            geom = obj.new_values.get('geom')
            if geom:
                try:
                    g = GEOSGeometry(json.dumps(geom))
                    g.srid = 28350
                    g.transform(4326)
                    polygon_id = obj.new_values.get('polygon_id')
                    area_ha = obj.new_values.get('area_ha')
                    feature = {
                        'type': 'Feature',
                        'geometry': json.loads(g.geojson),
                        'properties': {
                            'polygon_id': polygon_id,
                            'area_ha': area_ha,
                        }
                    }
                    return json.dumps(feature)
                except Exception as e:
                    return None
        return None

    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',)
        }
        js = (
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
        )

        # ---------- Permission overrides ----------
        def has_add_permission(self, request):
            return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'proposal')

