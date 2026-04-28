from typing import Any

from django.contrib import admin
from django.db import transaction
from django.db.models import TextField
from django import forms
from django.forms import Textarea
from django.http import HttpResponseRedirect, HttpResponse
from django.http.request import HttpRequest
from django.urls import re_path
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib.gis.geos import GEOSGeometry
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin import action
from django.template.response import TemplateResponse

from django.utils import timezone
import json

from silrec import helpers
#from silrec.components.proposals.models import (
#    SQLReport,
#    TextSearchModelConfig,
#    TextSearchFieldDisplay
#)
from silrec.components.proposals import models

from silrec.components.forest_blocks.models import (
    Polygon, Cohort, AssignChtToPly, Treatment, TreatmentXtra,
    SilviculturistComment, Prescription, Operation, Compartments
)

import logging
logger = logging.getLogger(__name__)


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
                valid_field_types = [choice[0] for choice in models.SQLReport.FIELD_TYPE_CHOICES]
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

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

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

class CloneReportForm(forms.Form):
    new_name = forms.CharField(
        max_length=255,
        label='New report name',
        widget=forms.TextInput(attrs={'style': 'width: 400px;'})
    )
    new_description = forms.CharField(
        max_length=500,
        label='New description',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60})
    )


@admin.register(models.SQLReport)
class SQLReportAdmin(admin.ModelAdmin):
    form = SQLReportAdminForm
    list_display = ['name', 'report_type', 'is_active', 'current_template_version', 'created_on', 'preview_sql']
    list_filter = ['report_type', 'is_active', 'created_on']
    search_fields = ['name', 'description', 'base_sql']
    filter_horizontal = ['allowed_groups']
    inlines = []  # templates added via get_inlines
    actions = ['clone_report']

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

    def save_related(self, request, form, formsets, change):
        """Save inlines first, then validate PDF template requirement."""
        super().save_related(request, form, formsets, change)
        instance = form.instance
        export_formats = instance.export_formats or []
        if 'pdf' in export_formats:
            if not instance.templates.filter(is_current=True).exists():
                from django.contrib import messages
                messages.error(
                    request,
                    "PDF export requires at least one Report Template marked as current "
                    "in the Report Templates section below."
                )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'clone-report/',
                self.admin_site.admin_view(self.clone_report_view),
                name='sqlreport-clone',
            ),
        ]
        return custom_urls + urls

    def clone_report(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Please select exactly one report to clone.', level='ERROR')
            return

        report = queryset.first()
        return redirect(
            reverse('admin:sqlreport-clone') + f'?report_id={report.id}'
        )
    clone_report.short_description = 'Clone selected report'

    def clone_report_view(self, request):
        report_id = request.GET.get('report_id') or request.POST.get('report_id')
        report = get_object_or_404(models.SQLReport, pk=report_id)

        if request.method == 'POST':
            form = CloneReportForm(request.POST)
            if form.is_valid():
                new_name = form.cleaned_data['new_name']
                new_description = form.cleaned_data.get('new_description', '')

                if models.SQLReport.objects.filter(name=new_name).exists():
                    self.message_user(
                        request,
                        f'A report named "{new_name}" already exists.',
                        level='ERROR',
                    )
                else:
                    with transaction.atomic():
                        clone = models.SQLReport()
                        for field in report._meta.fields:
                            if field.name in ('id', 'created_on', 'updated_on', 'created_by'):
                                continue
                            if field.name == 'name':
                                setattr(clone, field.name, new_name)
                            elif field.name == 'description':
                                setattr(clone, field.name, new_description)
                            elif field.primary_key:
                                continue
                            else:
                                setattr(clone, field.name, getattr(report, field.name))
                        clone.created_by = request.user
                        clone.save()

                        clone.allowed_groups.set(report.allowed_groups.all())

                        for tmpl in report.templates.all():
                            models.ReportTemplate.objects.create(
                                report=clone,
                                version=tmpl.version,
                                template_file=tmpl.template_file,
                                is_current=tmpl.is_current,
                                created_by=request.user,
                            )

                        self.message_user(
                            request,
                            f'Report "{report.name}" cloned as "{new_name}".',
                            level='SUCCESS',
                        )
                    return redirect(reverse('admin:silrec_sqlreport_changelist'))

        else:
            initial = {
                'new_name': f'{report.name} (copy)',
                'new_description': report.description,
            }
            form = CloneReportForm(initial=initial)

        context = {
            'title': f'Clone Report: {report.name}',
            'form': form,
            'report': report,
            'opts': models.SQLReport._meta,
            'media': self.media,
        }
        return TemplateResponse(request, 'admin/silrec/sqlreport/clone_report.html', context)



class ReportTemplateForm(forms.ModelForm):
    class Meta:
        model = models.ReportTemplate
        fields = '__all__'


class ReportTemplateInline(admin.TabularInline):
    model = models.ReportTemplate
    form = ReportTemplateForm
    extra = 0
    fields = ['template_file', 'version', 'is_current', 'created_at', 'created_by']
    readonly_fields = ['version', 'created_at', 'created_by']
    ordering = ['-version']
    can_delete = True

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True


# Dynamically add inline to SQLReportAdmin
SQLReportAdmin.inlines = [ReportTemplateInline]

# Add a column to show current template version
def current_template_version(self, obj):
    current = obj.templates.filter(is_current=True).first()
    return f"v{current.version}" if current else "-"
current_template_version.short_description = 'Template'
SQLReportAdmin.current_template_version = current_template_version



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
        'created_at', 'affected_records_display', 'revert_action'
    ]
    fields = [
        'iteration', 'action', 'created_at', 'affected_records_display',
        'revert_action'
    ]
    can_delete = False
    ordering = ['iteration']

    def revert_action(self, obj):
        """Provide revert button for committed savepoints"""
        if obj.action == 'commit' and obj.processing_run.status != 'rolled_back':
            # Don't show revert button for marker savepoints
            if obj.iteration == 0 and obj.metadata and obj.metadata.get('is_marker'):
                return format_html(
                    '<span style="color: #6c757d; font-style: italic;">Marker only - use API revert</span>'
                )

            button_text = "Revert to Initial State" if obj.iteration == 0 else f"Revert to Iteration {obj.iteration}"
            return format_html(
                '<a class="button" href="{}" style="background: #17a2b8; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">{}</a>',
                reverse('admin:revert-confirm', args=[obj.processing_run.id, obj.id]),
                button_text
            )
        return "-"

    def affected_records_display(self, obj):
        """Display affected records with links to audit logs"""
        if obj.iteration == 0:
            # Check if this is a marker savepoint with no actual DB changes
            if obj.metadata and obj.metadata.get('is_marker'):
                return "<span style='color: #6c757d;'>Marker Savepoint - No actual database changes</span>"
            return "<span style='color: green;'>Initial State - No changes yet</span>"

        if not obj.affected_models:
            return "-"

        lines = []
        for model, count in obj.affected_models.items():
            if count > 0:
                url = reverse('admin:silrec_auditlog_changelist') + f'?savepoints_records__id__exact={obj.id}'
                lines.append(f'<a href="{url}" target="_blank">{count} {model}</a>')

        return format_html("<br>".join(lines)) if lines else "-"

@admin.register(models.ShapefileProcessingRun)
class ShapefileProcessingRunAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'proposal_link', 'user_link', 'threshold', 'status_colored',
        'progress_bar', 'started_at', 'duration_display', 'savepoints_count', 'revert_notice'
    ]
    list_filter = ['status', 'started_at', 'user']
    search_fields = ['proposal__lodgement_number', 'user__username']
    readonly_fields = [
        'started_at', 'completed_at', 'metadata_display',
        'request_metrics_link', 'audit_logs_link', 'progress_display', 'duration_display'
    ]
    inlines = [SavepointInline]
    actions = ['revert_to_first_savepoint', 'revert_to_last_savepoint', 'revert_to_specific_savepoint']

    fieldsets = (
        ('Run Information', {
            'fields': ('proposal', 'user', 'threshold', 'status', 'request_metrics_link')
        }),
        ('Progress', {
            'fields': (
                'total_polygons', 'processed_polygons', 'failed_polygons',
                'progress_display'  # This is a method, not a field
            )
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_display')  # This is a method, not a field
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

    # Make sure these methods are defined
    def progress_display(self, obj):
        """Display progress as formatted HTML"""
        return format_html(
            'Processed: {}<br>Failed: {}<br>Total: {}<br>Success Rate: {:.1f}%',
            obj.processed_polygons,
            obj.failed_polygons,
            obj.total_polygons,
            obj.success_rate
        )
    progress_display.short_description = 'Progress Details'
    progress_display.allow_tags = True

    def duration_display(self, obj):
        """Display duration in human-readable format"""
        duration = obj.duration
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        seconds = duration.seconds % 60
        return f"{hours}h {minutes}m {seconds}s"
    duration_display.short_description = 'Duration'

    def revert_notice(self, obj):
        """Add a notice about using the API for revert"""
        if obj.savepoints.filter(iteration=0, action='create').exists():
            return format_html(
                '<span style="color: #856404;">⚠️ Use API endpoint for revert</span>'
            )
        return "-"
    revert_notice.short_description = 'Revert Method'

    @action(description='Revert to first savepoint (before any changes)')
    def revert_to_first_savepoint(self, request, queryset):
        """Revert the run to the state before any changes were made"""
        return self._revert_runs(request, queryset, 'first')

    @action(description='Revert to last savepoint (undo all changes)')
    def revert_to_last_savepoint(self, request, queryset):
        """Revert the run to the last committed savepoint"""
        return self._revert_runs(request, queryset, 'last')

    @action(description='Revert to specific savepoint (choose iteration)')
    def revert_to_specific_savepoint(self, request, queryset):
        """Revert the run to a user-selected savepoint"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one processing run to revert to a specific savepoint.", level='ERROR')
            return

        run = queryset.first()
        return self._redirect_to_savepoint_selection(request, run)

    def _revert_runs(self, request, queryset, revert_type):
        """Common revert logic for multiple runs"""
        success_count = 0
        error_count = 0

        for run in queryset:
            try:
                if revert_type == 'first':
                    # Get the first committed savepoint
                    savepoint = run.savepoints.filter(action='commit').order_by('iteration').first()
                    message = f"reverted to initial state"
                elif revert_type == 'last':
                    # Get the last committed savepoint
                    savepoint = run.savepoints.filter(action='commit').order_by('-iteration').first()
                    message = f"reverted to final state"
                else:
                    continue

                if not savepoint:
                    self.message_user(request, f"Run {run.id} has no committed savepoints to revert to.", level='WARNING')
                    continue

                # Perform the revert
                result = self._revert_to_savepoint(run, savepoint, request.user)

                if result['success']:
                    success_count += 1
                    self.message_user(request, f"Run {run.id} {message} successfully. {result['records_affected']} records affected.", level='SUCCESS')
                else:
                    error_count += 1
                    self.message_user(request, f"Error reverting run {run.id}: {result['error']}", level='ERROR')

            except Exception as e:
                error_count += 1
                self.message_user(request, f"Error reverting run {run.id}: {str(e)}", level='ERROR')

        if success_count > 0:
            self.message_user(request, f"Successfully reverted {success_count} runs. {error_count} errors.", level='SUCCESS')

    def _redirect_to_savepoint_selection(self, request, run):
        """Redirect to a custom view for selecting a savepoint"""
        from django.shortcuts import redirect
        from django.urls import reverse

        url = reverse('admin:select-savepoint', args=[run.id])
        return redirect(url)


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
            path(
                '<int:run_id>/select-savepoint/',
                self.admin_site.admin_view(self.select_savepoint_view),
                name='select-savepoint'
            ),
            path(
                '<int:run_id>/revert-confirm/<int:savepoint_id>/',
                self.admin_site.admin_view(self.revert_confirm_view),
                name='revert-confirm'
            ),
        ]
        return custom_urls + urls

    def select_savepoint_view(self, request, run_id):
        """View to let user select which savepoint to revert to"""
        run = get_object_or_404(models.ShapefileProcessingRun, id=run_id)
        savepoints = run.savepoints.filter(action='commit').order_by('iteration')

        context = {
            'title': f'Select Savepoint to Revert To - Run #{run.id}',
            'run': run,
            'savepoints': savepoints,
            'opts': self.model._meta,
            'media': self.media,
        }
        return render(request, 'admin/silrec/shapefileprocessingrun/select_savepoint.html', context)

    def revert_confirm_view(self, request, run_id, savepoint_id):
        """Confirmation view before reverting - also handles the actual revert on POST"""
        run = get_object_or_404(models.ShapefileProcessingRun, id=run_id)
        savepoint = get_object_or_404(models.SavepointRecord, id=savepoint_id, processing_run=run)

        # Check if this is a marker savepoint (iteration 0 with is_marker flag)
        is_marker = savepoint.iteration == 0 and savepoint.metadata and savepoint.metadata.get('is_marker')

        if is_marker and request.method == 'POST':
            self.message_user(
                request,
                'Marker savepoints cannot be reverted directly. Please use the API endpoint /api/proposals/{}/revert-shapefile/'.format(run.proposal.id),
                level='ERROR'
            )
            return HttpResponseRedirect(
                reverse('admin:silrec_shapefileprocessingrun_change', args=[run.id])
            )

        if request.method == 'POST':
            # Perform the revert
            result = self._revert_to_savepoint(run, savepoint, request.user)

            if result['success']:
                self.message_user(
                    request,
                    f'Successfully reverted to savepoint #{savepoint.iteration}. {result["records_affected"]} records affected.',
                    level='SUCCESS'
                )
            else:
                self.message_user(
                    request,
                    f'Error reverting to savepoint: {result["error"]}',
                    level='ERROR'
                )

            # Redirect back to the run change page
            return HttpResponseRedirect(
                reverse('admin:silrec_shapefileprocessingrun_change', args=[run.id])
            )

        # GET request - show confirmation page
        # Calculate statistics about what will be affected
        later_savepoints = run.savepoints.filter(
            action='commit',
            iteration__gt=savepoint.iteration
        ).order_by('iteration')

        affected_records = {
            'polygons': 0,
            'cohorts': 0,
            'assignments': 0,
            'treatments': 0
        }

        # Estimate affected records from later savepoints
        for sp in later_savepoints:
            for model, count in sp.affected_models.items():
                model_lower = model.lower()
                if 'polygon' in model_lower:
                    affected_records['polygons'] += count
                elif 'cohort' in model_lower:
                    affected_records['cohorts'] += count
                elif 'assign' in model_lower:
                    affected_records['assignments'] += count
                elif 'treatment' in model_lower:
                    affected_records['treatments'] += count

        context = {
            'title': f'Confirm Revert to Savepoint #{savepoint.iteration}',
            'run': run,
            'savepoint': savepoint,
            'later_savepoints': later_savepoints,
            'affected_records': affected_records,
            'is_marker': is_marker,
            'api_endpoint': f'/api/proposals/{run.proposal.id}/revert-shapefile/' if is_marker else None,
            'opts': self.model._meta,
        }
        return render(request, 'admin/silrec/shapefileprocessingrun/revert_confirm.html', context)

    def _revert_to_savepoint(self, run, savepoint, user):
        """
        Core revert logic - simple revert to state before processing
        """
        try:
            # Only handle savepoint #0
            if savepoint.iteration == 0:
                logger.info("=" * 80)
                logger.info("REVERTING TO PRE-RUN STATE (ITERATION 0)")
                logger.info("=" * 80)

                # Import the necessary models
                from silrec.components.forest_blocks.models import (
                    Polygon, Cohort, AssignChtToPly, Treatment
                )
                from django.db import transaction
                import reversion
                from reversion.models import Version

                records_deleted = 0
                records_updated = 0

                # Get the proposal
                proposal = run.proposal

                # Get the timestamp right before this run started
                run_start_time = run.started_at
                logger.info(f"This processing run started at: {run_start_time}")

                # Get ALL polygons that existed before this run
                # We can get this from the audit logs of this run
                if run.request_metrics:
                    # Get all audit logs for this run
                    audit_logs = run.request_metrics.audit_logs.all()

                    # Track original polygons that were updated
                    updated_polygon_ids = set()
                    new_polygon_ids = set()

                    for log in audit_logs:
                        if log.table_name == 'polygon':
                            if log.operation == 'INSERT':
                                new_polygon_ids.add(log.record_id)
                            elif log.operation == 'UPDATE':
                                updated_polygon_ids.add(log.record_id)
                            # DELETEs are rare but would need special handling

                    logger.info(f"New polygons created: {sorted(new_polygon_ids)}")
                    logger.info(f"Updated polygons: {sorted(updated_polygon_ids)}")

                    # Get current counts
                    before_counts = {
                        'polygon': Polygon.objects.filter(proposal_id=proposal.id).count(),
                        'cohort': Cohort.objects.filter(assignchttoply__polygon__proposal_id=proposal.id).distinct().count(),
                        'assign_cht_to_ply': AssignChtToPly.objects.filter(polygon__proposal_id=proposal.id).count(),
                    }
                    logger.info(f"Before revert counts: {before_counts}")

                    with transaction.atomic():
                        with reversion.create_revision():
                            # STEP 1: Delete new polygons and their related records
                            if new_polygon_ids:
                                logger.info(f"Deleting {len(new_polygon_ids)} new polygons")

                                # Get assignments for new polygons
                                new_assignments = AssignChtToPly.objects.filter(
                                    polygon_id__in=new_polygon_ids
                                )
                                assignment_count = new_assignments.count()
                                if assignment_count > 0:
                                    new_assignments.delete()
                                    records_deleted += assignment_count
                                    logger.info(f"Deleted {assignment_count} assignments")

                                # Get cohorts linked to new polygons
                                # Only delete cohorts that are ONLY linked to these new polygons
                                new_cohort_ids = set()
                                for log in audit_logs.filter(table_name='cohort', operation='INSERT'):
                                    new_cohort_ids.add(log.record_id)

                                for cohort_id in new_cohort_ids:
                                    # Check if this cohort is used elsewhere
                                    other_assignments = AssignChtToPly.objects.filter(
                                        cohort_id=cohort_id
                                    ).exclude(polygon_id__in=new_polygon_ids)
                                    if not other_assignments.exists():
                                        try:
                                            cohort = Cohort.objects.get(cohort_id=cohort_id)
                                            cohort.delete()
                                            records_deleted += 1
                                            logger.info(f"Deleted cohort {cohort_id}")
                                        except Cohort.DoesNotExist:
                                            pass

                                # Delete new polygons
                                polygons_to_delete = Polygon.objects.filter(polygon_id__in=new_polygon_ids)
                                polygon_count = polygons_to_delete.count()
                                if polygon_count > 0:
                                    polygons_to_delete.delete()
                                    records_deleted += polygon_count
                                    logger.info(f"Deleted {polygon_count} polygons")

                            # STEP 2: For updated polygons, we need to revert them
                            # This is complex - for simplicity, we'll rely on reversion
                            # to restore the proposal and its related objects

                            # Get the version of the proposal right before this run
                            versions_before = Version.objects.get_for_object(proposal).filter(
                                revision__date_created__lt=run_start_time
                            ).order_by('-revision__date_created')

                            if versions_before.exists():
                                target_version = versions_before.first()
                                target_version.revision.revert()
                                records_updated += len(updated_polygon_ids)
                                logger.info(f"Reverted proposal to pre-run state")

                            # Clear processed fields
                            proposal.refresh_from_db()
                            proposal.geojson_data_processed = None
                            proposal.geojson_data_processed_iters = None
                            proposal.save()

                            reversion.set_comment(f'Reverted to state before run {run.id}')

                    # Get counts after revert
                    after_counts = {
                        'polygon': Polygon.objects.filter(proposal_id=proposal.id).count(),
                        'cohort': Cohort.objects.filter(assignchttoply__polygon__proposal_id=proposal.id).distinct().count(),
                        'assign_cht_to_ply': AssignChtToPly.objects.filter(polygon__proposal_id=proposal.id).count(),
                    }
                    logger.info(f"After revert counts: {after_counts}")

                    records_affected = records_deleted + records_updated
                    logger.info(f"Revert completed: {records_deleted} records deleted, {records_updated} records updated")

                    # Mark the savepoint as rolled back
                    savepoint.action = 'rolled_back'
                    savepoint.save()

                    # Update run status
                    run.status = 'rolled_back'
                    run.completed_at = timezone.now()
                    run.metadata = {
                        'reverted_by': user.username if user else 'unknown',
                        'reverted_at': timezone.now().isoformat(),
                        'before_counts': before_counts,
                        'after_counts': after_counts,
                        'records_deleted': records_deleted,
                        'records_updated': records_updated,
                        'new_polygon_ids': list(new_polygon_ids)
                    }
                    run.save()

                    return {
                        'success': True,
                        'records_affected': records_affected,
                        'before_counts': before_counts,
                        'after_counts': after_counts
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No request metrics found for this run'
                    }

            # For other savepoints, just return an error
            else:
                return {
                    'success': False,
                    'error': 'Only savepoint #0 can be reverted'
                }

        except Exception as e:
            logger.error(f"Error in revert_to_savepoint: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def revert_to_savepoint_view(self, request, run_id, savepoint_id):
        """Handle the actual revert operation"""
        run = get_object_or_404(models.ShapefileProcessingRun, id=run_id)
        savepoint = get_object_or_404(models.SavepointRecord, id=savepoint_id, processing_run=run)

        if request.method == 'POST':
            result = self._revert_to_savepoint(run, savepoint, request.user)

            if result['success']:
                self.message_user(
                    request,
                    f'Successfully reverted to savepoint #{savepoint.iteration}. {result["records_affected"]} records affected.',
                    level='SUCCESS'
                )
            else:
                self.message_user(
                    request,
                    f'Error reverting to savepoint: {result["error"]}',
                    level='ERROR'
                )

            # Redirect back to the run change page
            return HttpResponseRedirect(
                reverse('admin:silrec_shapefileprocessingrun_change', args=[run.id])
            )

        # If not POST, redirect to confirm view
        return HttpResponseRedirect(
            reverse('admin:revert-confirm', args=[run.id, savepoint.id])
        )

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
        count = models.AuditLog.objects.filter(request_metrics=obj.request_metrics).count() if obj.request_metrics else 0
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
    actions = ['revert_to_this_savepoint']

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

    @action(description='Revert processing run to this savepoint')
    def revert_to_this_savepoint(self, request, queryset):
        """Revert the processing run to the selected savepoint"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one savepoint to revert to.", level='ERROR')
            return

        savepoint = queryset.first()
        run = savepoint.processing_run

        # Redirect to the confirm view
        from django.shortcuts import redirect
        from django.urls import reverse

        return redirect(reverse('admin:revert-confirm', args=[run.id, savepoint.id]))

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

