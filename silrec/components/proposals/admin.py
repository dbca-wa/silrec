from typing import Any

from django.contrib import admin
from django.db.models import TextField
from django import forms
from django.forms import Textarea
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.urls import re_path
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib.gis.geos import GEOSGeometry
from django.shortcuts import render, get_object_or_404

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


class SimpleProposalAdmin(admin.ModelAdmin):
    list_display = ['id', 'lodgement_number', 'title']

# Register if not already registered
if not admin.site.is_registered(models.Proposal):
    admin.site.register(models.Proposal, SimpleProposalAdmin)

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


# ---------- Inline for AuditLog within RequestMetrics ----------
class AuditLogInline(admin.TabularInline):
    model = models.AuditLog
    fk_name = 'request_metrics'           # ForeignKey field name in AuditLog
    extra = 0
    readonly_fields = [
        'table_name', 'record_id', 'operation', 'iter_seq',
        'start_time', 'end_time', 'changes_summary', 'formatted_old_values_preview',
        'formatted_new_values_preview'
    ]
    fields = [
        'table_name', 'record_id', 'operation', 'iter_seq',
        'start_time', 'end_time', 'changes_summary'
    ]
    can_delete = False
    show_change_link = True                # Provides a link to the full AuditLog change form

    def changes_summary(self, obj):
        if obj.operation == 'INSERT':
            return "New record created"
        elif obj.operation == 'DELETE':
            return "Record deleted"
        elif obj.operation == 'UPDATE' and obj.old_values and obj.new_values:
            changed = set(obj.old_values.keys()) & set(obj.new_values.keys())
            return f"{len(changed)} field(s) changed"
        return "-"
    changes_summary.short_description = 'Changes'

    def formatted_old_values_preview(self, obj):
        """Truncated preview of old values (optional)."""
        if obj.old_values:
            preview = json.dumps(obj.old_values, indent=2)[:100]
            return format_html('<pre style="margin:0; font-size:0.9em;">{}…</pre>', preview)
        return "-"
    formatted_old_values_preview.short_description = 'Old Values (preview)'

    def formatted_new_values_preview(self, obj):
        if obj.new_values:
            preview = json.dumps(obj.new_values, indent=2)[:100]
            return format_html('<pre style="margin:0; font-size:0.9em;">{}…</pre>', preview)
        return "-"
    formatted_new_values_preview.short_description = 'New Values (preview)'


@admin.register(models.RequestMetrics)
class RequestMetricsAdmin(admin.ModelAdmin):
    list_display = ['proposal', 'user', 'timestamp', 'audit_logs_count_link', 'planar_enforcement_link']
    list_filter = ['user', 'timestamp']
    search_fields = ['proposal__lodgement_number', 'user__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    inlines = [AuditLogInline]                # Add the inline here

    # Permission overrides
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow viewing (detail page) for all authenticated staff
        #return request.user.is_authenticated and request.user.is_staff
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers may delete
        return request.user.is_superuser

    def audit_logs_count_link(self, obj):
        """Show the number of audit logs and link to filtered changelist."""
        count = obj.audit_logs.count()
        url = reverse('admin:silrec_auditlog_changelist') + f'?request_metrics__id__exact={obj.id}'
        return format_html('<a href="{}">{} Logs</a>', url, count)
    audit_logs_count_link.short_description = 'Audit Logs'
    audit_logs_count_link.admin_order_field = 'audit_logs__count'  # not directly orderable

#    def planar_enforcement_link(self, obj):
#        """Link to the planar enforcement detail view."""
#        url = reverse('admin:requestmetrics-planar-enforcement', args=[obj.pk])
#        return format_html('<a href="{}">Check Planar Enforcement</a>', url)
#    planar_enforcement_link.short_description = 'Planar Enforcement'

    def planar_enforcement_link(self, obj):
        """Display boolean for planar enforcement with color and link to detail view."""
        result = obj.check_planar_enforcement(operation='ALL')
        if result['gdf'] is None:
            return format_html('<span style="color: grey;">–</span>')
        has_intersections = result['has_intersections']
        passed = not has_intersections
        color = 'green' if passed else 'red'
        text = 'True' if passed else 'False'
        url = reverse('admin:requestmetrics-planar-enforcement', args=[obj.pk])
        return format_html('<a href="{}" style="color: {};">{}</a>', url, color, text)
    planar_enforcement_link.short_description = 'Planar Enforcement'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:requestmetrics_id>/planar-enforcement/',
                 self.admin_site.admin_view(self.planar_enforcement_view),
                 name='requestmetrics-planar-enforcement'),
        ]
        return custom_urls + urls

    def planar_enforcement_view(self, request, requestmetrics_id):
        """Custom view to display planar enforcement check results."""
        obj = get_object_or_404(self.model, pk=requestmetrics_id)

        # Optionally allow operation filtering via GET parameter
        operation = request.GET.get('operation', 'ALL')
        if operation not in ['ALL', 'INSERT', 'UPDATE', 'DELETE']:
            operation = 'ALL'

        # Run the check (this may be heavy)
        result = obj.check_planar_enforcement(operation=operation)

        # Sort intersections by area descending (largest first)
        if result['intersections']:
            result['intersections'].sort(key=lambda x: x[2], reverse=True)

        context = {
            'original': obj,
            'result': result,
            'operation': operation,
            'title': f'Planar Enforcement for RequestMetrics #{obj.pk}',
            'opts': self.model._meta,
        }
        return render(request, 'admin/silrec/requestmetrics/planar_enforcement.html', context)

# ---------- Updated AuditLogAdmin (no major changes) ----------
@admin.register(models.AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for analysing audit logs.
    Provides rich display of changes, filtering by table/operation/user,
    and links to related proposal and user records via RequestMetrics.
    """
    change_form_template = "admin/silrec/auditlog/change_form.html"

    list_display = [
        'id',
        'start_time',
        'table_name',
        'record_id',
        'operation',
        'iter_seq',
        'user_link',
        'proposal_link',
        'changes_summary'
    ]
    list_filter = [
        'table_name',
        'operation',
        'request_metrics__user',          # filter by user through request_metrics
        ('start_time', admin.DateFieldListFilter),
        ('request_metrics__proposal', admin.RelatedOnlyFieldListFilter),  # proposal dropdown
        'iter_seq',
    ]
    search_fields = [
        'table_name',
        'record_id',
        'request_metrics__user__username',
        'request_metrics__proposal__lodgement_number',
        'iter_seq',
    ]
    date_hierarchy = 'start_time'          # Quick date drill-down
    readonly_fields = [
        'table_name',
        'record_id',
        'request_metrics',
        'operation',
        'iter_seq',
        'start_time',
        'end_time',
        'formatted_old_values',
        'formatted_new_values',
    ]
    fieldsets = (
        (None, {
            'fields': ('start_time', 'end_time', 'request_metrics', 'iter_seq')
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

    # Permission overrides
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow viewing (detail page) for all authenticated staff
        #return request.user.is_authenticated and request.user.is_staff
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers may delete
        return request.user.is_superuser

    def has_module_permission(self, request):
        ''' Hide from a=Admin console '''
        return False

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                extra_context['old_geometry'] = self.old_geometry(obj)
                extra_context['new_geometry'] = self.new_geometry(obj)
        return super().changeform_view(request, object_id, form_url, extra_context)

#    def user_link(self, obj):
#        """Link to the User admin page via request_metrics."""
#        if obj.request_metrics and obj.request_metrics.user:
#            url = reverse('admin:auth_user_change', args=[obj.request_metrics.user.id])
#            return format_html('<a href="{}">{}</a>', url, obj.request_metrics.user.get_username())
#        return "-"
#    user_link.short_description = 'User'
#    user_link.admin_order_field = 'request_metrics__user'
#
#    def proposal_link(self, obj):
#        """Link to the internal proposal detail page (opens in new tab) via request_metrics."""
#        if obj.request_metrics and obj.request_metrics.proposal:
#            url = reverse('internal-proposal-detail', args=[obj.request_metrics.proposal.id])
#            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.request_metrics.proposal.lodgement_number)
#        return "-"
#    proposal_link.short_description = 'Proposal'
#    proposal_link.admin_order_field = 'request_metrics__proposal'

    def user_link(self, obj):
        """Link to the User admin page via request_metrics."""
        if obj.request_metrics and obj.request_metrics.user:
            url = reverse('admin:auth_user_change', args=[obj.request_metrics.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.request_metrics.user.get_username())
        return "-"
    user_link.short_description = 'User'
    user_link.admin_order_field = 'request_metrics__user'

    def proposal_link(self, obj):
        """Link to the Proposal admin page via request_metrics."""
        if obj.request_metrics and obj.request_metrics.proposal:
            url = reverse('admin:silrec_proposal_change', args=[obj.request_metrics.proposal.id])
            return format_html('<a href="{}">{}</a>', url, obj.request_metrics.proposal.lodgement_number)
        return "-"
    proposal_link.short_description = 'Proposal'
    proposal_link.admin_order_field = 'request_metrics__proposal'

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
                    polygon_id = obj.old_values.get('polygon_id')
                    area_ha = obj.old_values.get('area_ha')
                    # Convert area_ha to float if possible
                    if area_ha is not None:
                        try:
                            area_ha = float(area_ha)
                        except (ValueError, TypeError):
                            area_ha = None  # or keep as string? Better to use None.
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
                    if area_ha is not None:
                        try:
                            area_ha = float(area_ha)
                        except (ValueError, TypeError):
                            area_ha = None
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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'request_metrics__user',
            'request_metrics__proposal'
        )


#from django.contrib import admin
#from django.urls import path, reverse
#from django.utils.html import format_html
#from django.shortcuts import render, get_object_or_404, redirect
#from django.contrib import messages
#from django.db import transaction
#from django.http import HttpResponseRedirect
#from django.utils import timezone
#import json
#
#from silrec.components.proposals.models import (
#    ShapefileProcessingRun,
#    SavepointRecord,
#    AuditLog,
#    RequestMetrics,
#    Polygon,
#    Cohort,
#    AssignChtToPly,
#)


class SavepointInline(admin.TabularInline):
    """Inline display of savepoints within a processing run"""
    model = models.SavepointRecord
    extra = 0
    readonly_fields = [
        'iteration', 'polygon_index', 'polygon_id', 'action',
        'created_at', 'affected_records_display', 'undo_action'
    ]
    fields = [
        'iteration', 'action', 'created_at', 'affected_records_display',
        'undo_action'
    ]
    can_delete = False
    ordering = ['iteration']

    def affected_records_display(self, obj):
        """Display affected records with links to audit logs"""
        if not obj.affected_models:
            return "-"

        lines = []
        for model, count in obj.affected_models.items():
            if count > 0:
                # Link to audit logs for this savepoint
                url = reverse('admin:silrec_auditlog_changelist') + f'?savepoints_records__id__exact={obj.id}'
                lines.append(f'<a href="{url}" target="_blank">{count} {model}</a>')

        return format_html("<br>".join(lines)) if lines else "-"
    affected_records_display.short_description = 'Affected Records'

    def undo_action(self, obj):
        """Provide undo button for committed savepoints"""
        if obj.can_undo:
            return format_html(
                '<a class="button" href="{}" style="background: #dc3545; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;" onclick="return confirm(\'Are you sure you want to undo this savepoint? This will revert all changes made in this iteration.\');">Undo</a>',
                reverse('admin:savepoint-undo', args=[obj.id])
            )
        return "-"
    undo_action.short_description = 'Actions'


@admin.register(models.ShapefileProcessingRun)
class ShapefileProcessingRunAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'proposal_link', 'user_link', 'threshold', 'status_colored',
        'progress_bar', 'started_at', 'duration_display', 'savepoints_count'
    ]
    list_filter = ['status', 'started_at', 'user']
    search_fields = ['proposal__lodgement_number', 'user__username']
    readonly_fields = [
        'started_at', 'completed_at', 'metadata_display',
        'request_metrics_link', 'audit_logs_link'
    ]
    inlines = [SavepointInline]

    fieldsets = (
        ('Run Information', {
            'fields': ('proposal', 'user', 'threshold', 'status', 'request_metrics_link')
        }),
        ('Progress', {
            'fields': (
                'total_polygons', 'processed_polygons', 'failed_polygons',
                'progress_display'
            )
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_display')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata_display', 'audit_logs_link'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:run_id>/revert-to-savepoint/<int:savepoint_id>/',
                self.admin_site.admin_view(self.revert_to_savepoint_view),
                name='revert-to-savepoint'
            ),
            path(
                'savepoint/<int:savepoint_id>/undo/',
                self.admin_site.admin_view(self.undo_savepoint_view),
                name='savepoint-undo'
            ),
            path(
                '<int:run_id>/compare/',
                self.admin_site.admin_view(self.compare_view),
                name='processing-run-compare'
            ),
        ]
        return custom_urls + urls

    def proposal_link(self, obj):
        # Use the correct admin URL pattern with namespace
        url = reverse('admin:silrec_proposal_change', args=[obj.proposal.id])
        return format_html('<a href="{}">{}</a>', url, obj.proposal.lodgement_number)
    proposal_link.short_description = 'Proposal'
    proposal_link.admin_order_field = 'proposal'

    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.get_username())
        return "-"
    user_link.short_description = 'User'

    def status_colored(self, obj):
        colors = {
            'running': '#ffc107',
            'completed': '#28a745',
            'failed': '#dc3545',
            'rolled_back': '#6c757d',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'

    def progress_bar(self, obj):
        if obj.total_polygons == 0:
            return "-"

        processed = obj.processed_polygons
        failed = obj.failed_polygons
        total = obj.total_polygons
        success_pct = (processed / total) * 100
        failed_pct = (failed / total) * 100

        return format_html(
            '<div style="width: 200px; background: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background: #28a745; height: 20px; float: left; text-align: center; color: white; font-size: 11px; line-height: 20px;">{}</div>'
            '<div style="width: {}%; background: #dc3545; height: 20px; float: left; text-align: center; color: white; font-size: 11px; line-height: 20px;">{}</div>'
            '</div>',
            success_pct, f"{processed}/{total}" if success_pct > 10 else "",
            failed_pct, f"{failed}" if failed_pct > 10 else ""
        )
    progress_bar.short_description = 'Progress'

    def progress_display(self, obj):
        return format_html(
            'Processed: {}<br>Failed: {}<br>Total: {}<br>Success Rate: {:.1f}%',
            obj.processed_polygons,
            obj.failed_polygons,
            obj.total_polygons,
            obj.success_rate
        )
    progress_display.short_description = 'Progress Details'

    def duration_display(self, obj):
        duration = obj.duration
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        return f"{hours}h {minutes}m {seconds}s"
    duration_display.short_description = 'Duration'

    def savepoints_count(self, obj):
        count = obj.savepoints.filter(action='commit').count()
        url = reverse('admin:silrec_savepointrecord_changelist') + f'?processing_run__id__exact={obj.id}'
        return format_html('<a href="{}">{} savepoints</a>', url, count)
    savepoints_count.short_description = 'Savepoints'

    def request_metrics_link(self, obj):
        if obj.request_metrics:
            url = reverse('admin:silrec_requestmetrics_change', args=[obj.request_metrics.id])
            return format_html('<a href="{}">View Request Metrics #{}</a>', url, obj.request_metrics.id)
        return "-"
    request_metrics_link.short_description = 'Request Metrics'

    def audit_logs_link(self, obj):
        count = AuditLog.objects.filter(request_metrics=obj.request_metrics).count() if obj.request_metrics else 0
        if count > 0:
            url = reverse('admin:silrec_auditlog_changelist') + f'?request_metrics__id__exact={obj.request_metrics.id}'
            return format_html('<a href="{}" target="_blank">View {} Audit Logs</a>', url, count)
        return "No audit logs"
    audit_logs_link.short_description = 'Audit Logs'

    def metadata_display(self, obj):
        """Display metadata as formatted JSON"""
        if obj.metadata:
            return format_html(
                '<pre style="max-height: 300px; overflow: auto; background: #f8f9fa; padding: 10px;">{}</pre>',
                json.dumps(obj.metadata, indent=2)
            )
        return "-"
    metadata_display.short_description = 'Metadata'

    def revert_to_savepoint_view(self, request, run_id, savepoint_id):
        """View to revert entire run to a specific savepoint"""
        run = get_object_or_404(ShapefileProcessingRun, id=run_id)
        savepoint = get_object_or_404(SavepointRecord, id=savepoint_id, processing_run=run)

        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Get all audit logs up to this savepoint
                    audit_logs = AuditLog.objects.filter(
                        request_metrics=run.request_metrics,
                        id__in=savepoint.audit_logs.all().values_list('id', flat=True)
                    )

                    # Revert logic here - you'll need to implement this based on your data model
                    # This is a placeholder for the actual revert logic

                    messages.success(request, f'Successfully reverted to savepoint {savepoint.iteration}')

                    # Mark later savepoints as rolled back
                    later_savepoints = SavepointRecord.objects.filter(
                        processing_run=run,
                        iteration__gt=savepoint.iteration
                    )
                    for sp in later_savepoints:
                        sp.action = 'rollback'
                        sp.save()

                    return HttpResponseRedirect(
                        reverse('admin:silrec_shapefileprocessingrun_change', args=[run.id])
                    )

            except Exception as e:
                messages.error(request, f'Error reverting to savepoint: {str(e)}')

        context = {
            'title': f'Revert to Savepoint #{savepoint.iteration}',
            'run': run,
            'savepoint': savepoint,
            'opts': self.model._meta,
        }
        return render(request, 'admin/silrec/shapefileprocessingrun/revert_confirm.html', context)

    def undo_savepoint_view(self, request, savepoint_id):
        """View to undo a single savepoint"""
        savepoint = get_object_or_404(SavepointRecord, id=savepoint_id)

        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Get audit logs for this savepoint
                    audit_logs = savepoint.audit_logs.all()

                    # Revert logic here - undo the changes made in this savepoint
                    # This is a placeholder for the actual revert logic

                    messages.success(request, f'Successfully undid savepoint #{savepoint.iteration}')

                    # Mark as rolled back
                    savepoint.action = 'rollback'
                    savepoint.save()

            except Exception as e:
                messages.error(request, f'Error undoing savepoint: {str(e)}')

        return HttpResponseRedirect(
            reverse('admin:silrec_shapefileprocessingrun_change', args=[savepoint.processing_run.id])
        )

    def compare_view(self, request, run_id):
        """View to compare before/after state of a processing run"""
        run = get_object_or_404(ShapefileProcessingRun, id=run_id)

        # Get first and last savepoints
        first_savepoint = run.savepoints.filter(action='commit').order_by('iteration').first()
        last_savepoint = run.savepoints.filter(action='commit').order_by('-iteration').first()

        context = {
            'title': f'Compare Run #{run.id}',
            'run': run,
            'first_savepoint': first_savepoint,
            'last_savepoint': last_savepoint,
            'opts': self.model._meta,
        }
        return render(request, 'admin/silrec/shapefileprocessingrun/compare.html', context)


@admin.register(models.SavepointRecord)
class SavepointRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'processing_run_link', 'iteration', 'polygon_index',
        'action_colored', 'created_at', 'affected_records_count'
    ]
    list_filter = ['action', 'created_at', 'processing_run__proposal']
    search_fields = [
        'processing_run__proposal__lodgement_number',
        'polygon_id'
    ]
    readonly_fields = [
        'processing_run', 'iteration', 'polygon_index', 'polygon_id',
        'action', 'created_at', 'affected_models_display',
        'audit_logs_link', 'metadata_display'
    ]

    fieldsets = (
        ('Savepoint Information', {
            'fields': ('processing_run', 'iteration', 'polygon_index', 'polygon_id', 'action', 'created_at')
        }),
        ('Affected Data', {
            'fields': ('affected_models_display', 'audit_logs_link')
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        }),
    )

    def processing_run_link(self, obj):
        url = reverse('admin:silrec_shapefileprocessingrun_change', args=[obj.processing_run.id])
        return format_html('<a href="{}">Run #{}</a>', url, obj.processing_run.id)
    processing_run_link.short_description = 'Processing Run'

    def action_colored(self, obj):
        colors = {
            'create': '#ffc107',
            'commit': '#28a745',
            'rollback': '#dc3545',
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.action, '#000'),
            obj.get_action_display()
        )
    action_colored.short_description = 'Action'

    def affected_records_count(self, obj):
        total = sum(obj.affected_models.values())
        url = reverse('admin:silrec_auditlog_changelist') + f'?savepoints_records__id__exact={obj.id}'
        return format_html('<a href="{}">{} records</a>', url, total)
    affected_records_count.short_description = 'Affected Records'

    def affected_models_display(self, obj):
        if not obj.affected_models:
            return "-"

        lines = []
        for model, count in obj.affected_models.items():
            if count > 0:
                url = reverse('admin:silrec_auditlog_changelist') + f'?savepoints_records__id__exact={obj.id}&table_name={model.lower()}'
                lines.append(format_html('<a href="{}" target="_blank">{}: {}</a>', url, model, count))

        return format_html("<br>".join(lines)) if lines else "-"
    affected_models_display.short_description = 'Affected Models'

    def audit_logs_link(self, obj):
        count = obj.audit_logs.count()
        if count > 0:
            url = reverse('admin:silrec_auditlog_changelist') + f'?savepoints_records__id__exact={obj.id}'
            return format_html('<a href="{}" target="_blank">View {} Audit Logs</a>', url, count)
        return "No audit logs"
    audit_logs_link.short_description = 'Audit Logs'

    def metadata_display(self, obj):
        if obj.metadata:
            return format_html(
                '<pre style="max-height: 200px; overflow: auto; background: #f8f9fa; padding: 5px;">{}</pre>',
                json.dumps(obj.metadata, indent=2)
            )
        return "-"
    metadata_display.short_description = 'Metadata'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

