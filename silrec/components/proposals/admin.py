from typing import Any

from django.contrib import admin
from django.db.models import TextField
from django.forms import Textarea
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.urls import re_path

from leaseslicensing import helpers
from leaseslicensing.components.main.models import ApplicationType, SystemMaintenance
from leaseslicensing.components.proposals import forms, models
from leaseslicensing.components.proposals.forms import SectionChecklistForm
from leaseslicensing.components.proposals.models import ChecklistQuestion
from leaseslicensing.utils import create_helppage_object


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


@admin.register(models.AdditionalDocumentType)
class AdditionalDocumentTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "help_text",
        "enabled",
    ]
    list_filter = ("enabled",)
    ordering = ("name",)


@admin.register(models.Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = [
        "lodgement_number",
        "application_type",
        "proposal_type",
        "processing_status",
        "submitter",
        "assigned_officer",
        "applicant",
    ]
    inlines = [
        ProposalDocumentInline,
    ]


@admin.register(models.ProposalStandardRequirement)
class ProposalStandardRequirementAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "text",
        "obsolete",
        "application_type",
        "default",
    ]
    exclude = ["gross_turnover_required"]

    def get_exclude(self, request: HttpRequest, obj: Any | None = ...) -> Any:
        if request.user.is_superuser:
            return []
        return super().get_exclude(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return []

        if helpers.is_leaseslicensing_admin(request):
            if obj and obj.gross_turnover_required:
                return [
                    "code",
                    "text",
                    "obsolete",
                    "application_type",
                    "gross_turnover_required",
                    "default",
                ]

        return super().get_readonly_fields(request, obj)


class HelpPageAdmin(admin.ModelAdmin):
    list_display = ["application_type", "help_type", "description", "version"]
    form = forms.LeasesLicensingHelpPageAdminForm
    change_list_template = "leaseslicensing/help_page_changelist.html"
    ordering = ("application_type", "help_type", "-version")
    list_filter = ("application_type", "help_type")

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            re_path(
                "create_leaseslicensing_help/",
                self.admin_site.admin_view(self.create_leaseslicensing_help),
            ),
            re_path(
                "create_leaseslicensing_help_assessor/",
                self.admin_site.admin_view(self.create_leaseslicensing_help_assessor),
            ),
        ]
        return my_urls + urls

    def create_leaseslicensing_help(self, request):
        create_helppage_object(
            application_type="T Class", help_type=models.HelpPage.HELP_TEXT_EXTERNAL
        )
        return HttpResponseRedirect("../")

    def create_leaseslicensing_help_assessor(self, request):
        create_helppage_object(
            application_type="T Class", help_type=models.HelpPage.HELP_TEXT_INTERNAL
        )
        return HttpResponseRedirect("../")


class ChecklistQuestionInline(admin.TabularInline):
    model = ChecklistQuestion
    extra = 0
    can_delete = False
    ordering = [
        "order",
    ]
    formfield_overrides = {
        TextField: {"widget": Textarea(attrs={"rows": 3, "cols": 60})},
    }
    fields = [
        "text",
        "answer_type",
        "enabled",
        "shown_to_others",
        "order",
    ]


@admin.register(models.SectionChecklist)
class SectionChecklistAdmin(admin.ModelAdmin):
    list_display = [
        "list_type_name",
        "application_type_name",
        "section_name",
        "enabled",
        "number_of_questions",
    ]
    list_filter = [
        "application_type",
        "section",
        "list_type",
        "enabled",
    ]
    inlines = [
        ChecklistQuestionInline,
    ]
    form = SectionChecklistForm

    def application_type_name(self, obj):
        return obj.application_type.get_name_display()

    def list_type_name(self, obj):
        return obj.get_list_type_display()

    def section_name(self, obj):
        return obj.get_section_display()

    # Configure column titles
    application_type_name.short_description = "Proposal Type"
    list_type_name.short_description = "List Type"


@admin.register(SystemMaintenance)
class SystemMaintenanceAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "start_date", "end_date", "duration"]
    ordering = ("start_date",)
    readonly_fields = ("duration",)
    form = forms.SystemMaintenanceAdminForm


@admin.register(ApplicationType)
class ApplicationTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name_display",
        "order",
        "visible",
        "is_gst_exempt",
    ]
    ordering = ("order",)
    readonly_fields = ["name"]


@admin.register(models.ExternalRefereeInvite)
class ExternalRefereeInviteAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ProposalApplicant)
class ProposalApplicantAdmin(admin.ModelAdmin):
    pass
