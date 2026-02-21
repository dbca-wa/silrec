from django.contrib import admin
from django.conf import settings

from django.utils import timezone
from datetime import datetime, timedelta

from silrec.components.main.models import (
    ApplicationType,
    SystemMaintenance,
)
from silrec.components.proposals import forms as proposal_forms

admin.autodiscover()

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


