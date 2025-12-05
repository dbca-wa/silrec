from typing import Any

from django.contrib import admin
from django.db.models import TextField
from django import forms
from django.forms import Textarea
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.urls import re_path
from django.utils.html import format_html
import json

from silrec import helpers
from silrec.components.main.models import (
    ApplicationType,
    SystemMaintenance,
)
from silrec.components.proposals.models import (
    SQLReport,
)
from silrec.components.proposals import forms as proposal_forms
from silrec.components.proposals import models


@admin.register(models.ProposalType)
class ProposalTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "description"]
    ordering = ("code",)
    list_filter = ("code",)


class ProposalDocumentInline(admin.TabularInline):
    model = models.ProposalDocument
    extra = 0


@admin.register(models.AmendmentReason)
class AmendmentReasonAdmin(admin.ModelAdmin):
    list_display = ["reason"]


@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "start_date", "end_date", "duration"]
    ordering = ("start_date",)
    readonly_fields = ("duration",)
    form = proposal_forms.SystemMaintenanceAdminForm


@admin.register(ApplicationType)
class ApplicationTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "order",
        "visible",
    ]
    ordering = ("order",)
    readonly_fields = ["name"]


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
        model = SQLReport
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

@admin.register(SQLReport)
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

