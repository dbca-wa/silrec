from django.contrib import admin
from django.conf import settings
from django import forms

from django.utils import timezone
from datetime import datetime, timedelta

from silrec.components.main.models import (
    ApplicationType,
    SystemMaintenance,
    GlobalSettings,
)
from silrec.components.proposals import forms as proposal_forms

admin.autodiscover()


class GlobalSettingsAdminForm(forms.ModelForm):
    class Meta:
        model = GlobalSettings
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        key = self.initial.get('key') or self.data.get('key') or ''
        if key in GlobalSettings.BOOLEAN_KEYS:
            self.fields['value'].widget = forms.Select(
                choices=[('True', 'True'), ('False', 'False')]
            )


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value']
    form = GlobalSettingsAdminForm

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

    def has_module_permission(self, request):
        return request.user.is_superuser
