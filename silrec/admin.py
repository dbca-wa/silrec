from django.contrib.gis import admin
from django.contrib.gis.db import models
from django.contrib.gis.db.models.fields import GeometryField

from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from django.db.models import Q, Max

from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from django.http import HttpResponse, JsonResponse
from django.apps import apps

from copy import deepcopy

admin.site.index_template = 'admin-index.html'
admin.autodiscover()

from silrec.components.proposals.models import FormValidationRule
from silrec.helpers import VALID_GROUPS


def _get_available_fields_for_model(model_name):
    """Return list of field names from the model not yet in FormValidationRule."""
    try:
        app_label, model_class_name = model_name.split('.')
        model_class = apps.get_model(app_label, model_class_name)
        if model_class is None:
            return []
    except (ValueError, LookupError):
        return []

    existing = set(
        FormValidationRule.objects.filter(
            model_name=model_name,
            is_active=True,
        ).values_list('field_name', flat=True)
    )

    skip_types = (models.AutoField, models.ForeignKey, models.OneToOneField,
                  models.ManyToManyField, GeometryField)
    skip_names = {'created_on', 'created_by', 'updated_on', 'updated_by',
                  'cohort_id', 'treatment_id', 'treatment_xtra_id',
                  'op_id', 'prescription_id', 'document_id', 's_comment_id',
                  'cr_id', 'polygon_id', 'id'}

    fields = []
    for f in model_class._meta.get_fields():
        if f.name in skip_names:
            continue
        if isinstance(f, skip_types):
            continue
        if f.name in existing:
            continue
        fields.append(f.name)
    return sorted(fields)


@admin.register(FormValidationRule)
class FormValidationRuleAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'field_name', 'field_label', 'is_required', 'status_values', 'is_active', 'order')
    list_filter = ('model_name', 'is_required', 'is_active')
    search_fields = ('model_name', 'field_name', 'field_label')
    list_editable = ('is_required', 'is_active', 'order')
    ordering = ('model_name', 'order', 'field_name')
    actions = ['clone_rule']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'clone-rule/<int:rule_id>/',
                self.admin_site.admin_view(self.clone_rule_view),
                name='clone-form-validation-rule',
            ),
            path(
                'available-fields/',
                self.admin_site.admin_view(self.available_fields_json),
                name='form-validation-rule-available-fields',
            ),
        ]
        return custom_urls + urls

    def available_fields_json(self, request):
        model_name = request.GET.get('model', '').strip()
        if not model_name:
            return JsonResponse({'fields': [], 'error': 'model parameter required'}, status=400)
        fields = _get_available_fields_for_model(model_name)
        return JsonResponse({'fields': fields})

    def clone_rule(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                'Please select exactly one rule to clone.',
                level=messages.WARNING,
            )
            return

        rule = queryset.first()
        return redirect(
            'admin:clone-form-validation-rule',
            rule_id=rule.rule_id,
        )
    clone_rule.short_description = 'Clone selected rule'

    def clone_rule_view(self, request, rule_id):
        try:
            original = FormValidationRule.objects.get(rule_id=rule_id)
        except FormValidationRule.DoesNotExist:
            self.message_user(request, 'Rule not found.', level=messages.ERROR)
            return redirect('..')

        available_fields = _get_available_fields_for_model(original.model_name)

        if request.method == 'POST':
            field_name = request.POST.get('field_name', '').strip()
            field_label = request.POST.get('field_label', '').strip()

            if not field_name:
                self.message_user(
                    request,
                    'Field name is required.',
                    level=messages.WARNING,
                )
                return render(
                    request,
                    'admin/clone_form_validation_rule.html',
                    {
                        'original': original,
                        'available_fields': available_fields,
                        'error': 'Field name is required.',
                    },
                )

            max_order = FormValidationRule.objects.filter(
                model_name=original.model_name
            ).aggregate(Max('order'))['order__max'] or 0

            clone = FormValidationRule.objects.create(
                model_name=original.model_name,
                field_name=field_name,
                field_label=field_label or field_name,
                is_required=False,
                status_field=original.status_field,
                status_values=original.status_values,
                order=max_order + 1,
                is_active=True,
            )

            self.message_user(
                request,
                f'Cloned rule #{original.rule_id} → new rule #{clone.rule_id} '
                f'(field: {clone.field_name}, order: {clone.order}, required: False)',
                level=messages.SUCCESS,
            )
            return redirect('..')

        return render(
            request,
            'admin/clone_form_validation_rule.html',
            {
                'original': original,
                'available_fields': available_fields,
            },
        )

##@admin.register(models.EmailUser)
#@admin.register(EmailUser)
#class EmailUserAdmin(admin.ModelAdmin):
#    list_display = ('email','first_name','last_name','is_staff','is_active',)
#    ordering = ('email',)
#    search_fields = ('id','email','first_name','last_name')
#
#    def has_change_permission(self, request, obj=None):
#        if obj is None: # and obj.status > 1:
#            return True
#        return None
#    def has_delete_permission(self, request, obj=None):
#        return None

