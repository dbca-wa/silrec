from typing import Any

from django.contrib import admin
from django.db.models import TextField
from django.forms import Textarea
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.urls import re_path

from silrec import helpers
from silrec.components.main.models import ApplicationType, SystemMaintenance
from silrec.components.proposals import forms, models
#from silrec.components.proposals.forms import SectionChecklistForm
#from silrec.components.proposals.models import ChecklistQuestion
#from silrec.utils import create_helppage_object


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


#@admin.register(models.Proposal)
#class ProposalAdmin(admin.ModelAdmin):
#    list_display = [
#        "lodgement_number",
#        "application_type",
#        "proposal_type",
#        "processing_status",
#        "submitter",
#        #"assigned_officer",
#        #"applicant",
#    ]
#    inlines = [
#        ProposalDocumentInline,
#    ]


@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "start_date", "end_date", "duration"]
    ordering = ("start_date",)
    readonly_fields = ("duration",)
    form = forms.SystemMaintenanceAdminForm


@admin.register(ApplicationType)
class ApplicationTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "order",
        "visible",
    ]
    ordering = ("order",)
    readonly_fields = ["name"]


