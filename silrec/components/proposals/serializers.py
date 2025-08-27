import datetime
import logging

from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext as _
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.managed_models import SystemGroup
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from leaseslicensing.components.competitive_processes.models import CompetitiveProcess
from leaseslicensing.components.invoicing.serializers import InvoicingDetailsSerializer
from leaseslicensing.components.main.serializers import (
    ApplicationTypeSerializer,
    CommunicationLogEntrySerializer,
    EmailUserSerializer,
)
from leaseslicensing.components.main.utils import get_secure_file_url
from leaseslicensing.components.organisations.models import Organisation
from leaseslicensing.components.organisations.serializers import OrganisationSerializer
from leaseslicensing.components.proposals.models import (
    AdditionalDocument,
    AdditionalDocumentType,
    AmendmentRequest,
    ChecklistQuestion,
    ExternalRefereeInvite,
    Proposal,
    ProposalAct,
    ProposalAdditionalDocumentType,
    ProposalApplicant,
    ProposalApplicantDetails,
    ProposalAssessment,
    ProposalAssessmentAnswer,
    ProposalCategory,
    ProposalDeclinedDetails,
    ProposalDistrict,
    ProposalGeometry,
    ProposalIdentifier,
    ProposalLGA,
    ProposalLogEntry,
    ProposalName,
    ProposalOtherDetails,
    ProposalRegion,
    ProposalRequirement,
    ProposalStandardRequirement,
    ProposalTenure,
    ProposalType,
    ProposalUserAction,
    ProposalVesting,
    Referral,
    RequirementDocument,
    SectionChecklist,
)
from leaseslicensing.components.tenure.models import (
    LGA,
    Act,
    Category,
    District,
    Group,
    Identifier,
    Name,
    Region,
    Tenure,
    Vesting,
)
from leaseslicensing.components.tenure.serializers import GroupSerializer
from leaseslicensing.components.users.serializers import (
    ProposalApplicantSerializer,
    UserAddressSerializer,
    UserSerializer,
)
from leaseslicensing.helpers import (
    is_assessor,
    is_finance_officer,
    is_internal,
    is_referee,
)
from leaseslicensing.ledger_api_utils import retrieve_email_user
from leaseslicensing.settings import GROUP_NAME_CHOICES

logger = logging.getLogger(__name__)


class ProposalGeometrySaveSerializer(GeoFeatureModelSerializer):
    proposal_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ProposalGeometry
        geo_field = "polygon"
        fields = (
            "id",
            "proposal_id",
            "polygon",
            "intersects",
            "drawn_by",
            "locked",
        )
        read_only_fields = ("id",)

    def save(self, **kwargs):
        from reversion import revisions

        if kwargs.pop("no_revision", False):
            return super().save(**kwargs)
        else:
            with revisions.create_revision():
                if "version_user" in kwargs:
                    revisions.set_user(kwargs.pop("version_user", None))
                if "version_comment" in kwargs:
                    revisions.set_comment(kwargs.pop("version_comment", ""))
                return super().save(**kwargs)


class ProposalGeometrySerializer(GeoFeatureModelSerializer):
    proposal_id = serializers.IntegerField(write_only=True, required=False)
    polygon_source = serializers.SerializerMethodField()
    proposal_copied_from = serializers.SerializerMethodField(read_only=True)
    polygon_source = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProposalGeometry
        geo_field = "polygon"
        fields = (
            "id",
            "proposal_id",
            "polygon",
            "area_sqm",
            "area_sqhm",
            "intersects",
            "polygon_source",
            "locked",
            "proposal_copied_from",
        )
        read_only_fields = ("id",)

    def get_polygon_source(self, obj):
        polygon_source = f"{obj.get_source_type_display()}"
        if obj.source_name:
            polygon_source += f" ({obj.source_name})"
        return polygon_source

    def get_proposal_copied_from(self, obj):
        if obj.copied_from:
            return ListProposalMinimalSerializer(
                obj.copied_from.proposal, context=self.context
            ).data

        return None


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


class EmailUserAppViewSerializer(serializers.ModelSerializer):
    residential_address = UserAddressSerializer()
    # identification = DocumentSerializer()

    class Meta:
        model = EmailUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "dob",
            "title",
            "organisation",
            "residential_address",
            "email",
            "phone_number",
            "mobile_number",
        )


class ProposalApplicantDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalApplicantDetails
        fields = ("id", "first_name")


class ProposalOtherDetailsSerializer(serializers.ModelSerializer):
    # park=ParkSerializer()
    # accreditation_type= serializers.SerializerMethodField()
    # accreditation_expiry = serializers.DateField
    # (format="%d/%m/%Y",input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    nominated_start_date = serializers.DateField(
        format="%d/%m/%Y", input_formats=["%d/%m/%Y"], required=False, allow_null=True
    )
    insurance_expiry = serializers.DateField(
        format="%d/%m/%Y", input_formats=["%d/%m/%Y"], required=False, allow_null=True
    )
    preferred_licence_period = serializers.CharField(allow_blank=True, allow_null=True)
    proposed_end_date = serializers.DateField(format="%d/%m/%Y", read_only=True)

    class Meta:
        model = ProposalOtherDetails
        fields = (
            "id",
            "preferred_licence_period",
            "nominated_start_date",
            "insurance_expiry",
            "other_comments",
            "credit_fees",
            "credit_docket_books",
            "docket_books_number",
            "mooring",
            "proposed_end_date",
        )


class SaveProposalOtherDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalOtherDetails
        fields = (
            "preferred_licence_period",
            "nominated_start_date",
            "insurance_expiry",
            "other_comments",
            "credit_fees",
            "credit_docket_books",
            "proposal",
        )


class ChecklistQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistQuestion
        fields = (
            "id",
            "text",
            "answer_type",
        )


class ProposalAssessmentAnswerSerializer(serializers.ModelSerializer):
    checklist_question = ChecklistQuestionSerializer(read_only=True)
    accessing_user_can_answer = serializers.SerializerMethodField()
    accessing_user_can_view = serializers.SerializerMethodField()

    class Meta:
        model = ProposalAssessmentAnswer
        fields = (
            "id",
            "checklist_question",
            "answer_yes_no",
            "answer_text",
            "accessing_user_can_answer",
            "accessing_user_can_view",
        )

    def get_accessing_user_can_answer(self, answer):
        accessing_user_can_answer = self.context.get(
            "assessment_answerable_by_accessing_user_now", False
        )
        return accessing_user_can_answer

    def get_accessing_user_can_view(self, answer):
        assessment_belongs_to_accessing_user = self.context.get(
            "assessment_belongs_to_accessing_user", False
        )
        if assessment_belongs_to_accessing_user:
            # this assessment is for the accessing user. Therefore, the user should be able to see QAs anyway.
            return True
        else:
            # this assessment is not for the accessing user. Show/Hide questions according to the configurations
            if answer.shown_to_others:
                return True
            else:
                return False


class ReferralSimpleSerializer(serializers.ModelSerializer):
    referral = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = (
            "id",
            "referral",
        )

    def get_referral(self, obj):
        email_user = retrieve_email_user(obj.referral)
        return EmailUserSerializer(email_user).data


class ProposalAssessmentSerializer(serializers.ModelSerializer):
    section_answers = serializers.SerializerMethodField()
    referral = ReferralSimpleSerializer(allow_null=True, read_only=True)
    answerable_by_accessing_user = serializers.SerializerMethodField()
    belongs_to_accessing_user = serializers.SerializerMethodField()

    class Meta:
        model = ProposalAssessment
        fields = (
            "id",
            "proposal",
            "completed",
            "submitter",
            "referral_assessment",
            "referral",
            "section_answers",
            "answerable_by_accessing_user",
            "belongs_to_accessing_user",
            "assessor_comment_map",
            "assessor_comment_tourism_proposal_details",
            "assessor_comment_general_proposal_details",
            "assessor_comment_proposal_details",
            "assessor_comment_proposal_impact",
            "assessor_comment_gis_data",
            "assessor_comment_categorisation",
            "assessor_comment_deed_poll",
            "assessor_comment_additional_documents",
            "deficiency_comment_map",
            "deficiency_comment_tourism_proposal_details",
            "deficiency_comment_general_proposal_details",
            "deficiency_comment_proposal_details",
            "deficiency_comment_proposal_impact",
            "deficiency_comment_gis_data",
            "deficiency_comment_categorisation",
            "deficiency_comment_deed_poll",
            "deficiency_comment_additional_documents",
        )

    def get_answerable_by_accessing_user(self, proposal_assessment):
        request = self.context.get("request")
        answerable_by_accessing_user = False
        belongs_to_accessing_user = self.get_belongs_to_accessing_user(
            proposal_assessment
        )
        if not belongs_to_accessing_user:
            return False

        if proposal_assessment.referral:
            if (
                request.user.is_authenticated
                and proposal_assessment.referral.referral == request.user.id
            ):
                if (
                    proposal_assessment.proposal.processing_status
                    == Proposal.PROCESSING_STATUS_WITH_REFERRAL
                ):
                    if not proposal_assessment.completed:
                        answerable_by_accessing_user = True
        else:
            if request.user.is_authenticated and is_assessor(request):
                if (
                    proposal_assessment.proposal.processing_status
                    == Proposal.PROCESSING_STATUS_WITH_ASSESSOR
                ):
                    if not proposal_assessment.completed:
                        answerable_by_accessing_user = True

        return answerable_by_accessing_user

    def get_belongs_to_accessing_user(self, proposal_assessment):
        request = self.context.get("request")
        assessment_belongs_to_accessing_user = False
        if proposal_assessment.referral:
            # This assessment is for referrals
            if (
                request.user.is_authenticated
                and proposal_assessment.referral.referral == request.user.id
            ):
                # This assessment is for the accessing user
                assessment_belongs_to_accessing_user = True
        else:
            # This assessment is for assessors
            if request.user.is_authenticated and is_assessor(request):
                assessment_belongs_to_accessing_user = True

        return assessment_belongs_to_accessing_user

    def get_section_answers(self, proposal_assessment):
        ret_dict = {}

        assessment_belongs_to_accessing_user = self.get_belongs_to_accessing_user(
            proposal_assessment
        )
        assessment_answerable_by_accessing_user_now = (
            self.get_answerable_by_accessing_user(proposal_assessment)
        )

        # Retrieve all the SectionChecklist objects used for this ProposalAssessment
        section_checklists_used = SectionChecklist.objects.filter(
            id__in=(
                proposal_assessment.answers.values_list(
                    "checklist_question__section_checklist", flat=True
                ).distinct()
            )
        )
        for section_checklist in section_checklists_used:
            # Retrieve all the answers for this section_checklist
            answers = proposal_assessment.answers.filter(
                checklist_question__section_checklist=section_checklist
            ).order_by("checklist_question__order")
            ret_dict[section_checklist.section] = ProposalAssessmentAnswerSerializer(
                answers,
                context={
                    "assessment_answerable_by_accessing_user_now": assessment_answerable_by_accessing_user_now,
                    "assessment_belongs_to_accessing_user": assessment_belongs_to_accessing_user,
                },
                many=True,
            ).data

        return ret_dict


class ProposalAdditionalDocumentTypeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="additional_document_type.name")
    help_text = serializers.CharField(source="additional_document_type.help_text")

    class Meta:
        model = ProposalAdditionalDocumentType
        fields = [
            "id",
            "name",
            "help_text",
        ]


class BaseProposalSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(read_only=True)
    readonly = serializers.SerializerMethodField(read_only=True)
    documents_url = serializers.SerializerMethodField()
    proposal_type = ProposalTypeSerializer()
    application_type = ApplicationTypeSerializer()
    accessing_user_roles = serializers.SerializerMethodField()
    proposalgeometry = ProposalGeometrySerializer(many=True, read_only=True)
    applicant = serializers.SerializerMethodField()
    lodgement_date_display = serializers.SerializerMethodField()
    applicant_type = serializers.SerializerMethodField()
    applicant_obj = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField(read_only=True)
    allowed_assessors = EmailUserSerializer(many=True)
    site_name = serializers.CharField(source="site_name.name", read_only=True)
    details_url = serializers.SerializerMethodField(read_only=True)
    competitive_process = serializers.SerializerMethodField(read_only=True)
    can_edit_invoicing_details = serializers.SerializerMethodField(read_only=True)
    approval = serializers.SerializerMethodField(read_only=True, allow_null=True)
    # Gis data fields
    identifiers = serializers.SerializerMethodField()
    vestings = serializers.SerializerMethodField()
    names = serializers.SerializerMethodField()
    acts = serializers.SerializerMethodField()
    tenures = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    regions = serializers.SerializerMethodField()
    districts = serializers.SerializerMethodField()
    lgas = serializers.SerializerMethodField()
    proposal_applicant = ProposalApplicantSerializer()

    class Meta:
        model = Proposal
        fields = (
            "id",
            "model_name",
            "allowed_assessors",
            "application_type",
            "applicant_type",
            "applicant_obj",
            "proposal_type",
            "title",
            "processing_status",
            "applicant",
            "submitter",
            "assigned_officer",
            "previous_application",
            "get_history",
            "lodgement_date",
            "supporting_documents",
            "requirements",
            "readonly",
            "can_user_edit",
            "can_user_view",
            "documents_url",
            "reference",
            "lodgement_number",
            "can_officer_process",
            "accessing_user_roles",
            "added_internally",
            # 'allowed_assessors',
            # 'is_qa_officer',
            # 'pending_amendment_request',
            # 'is_amendment_proposal',
            # tab field models
            "applicant_details",
            "details_text",
            "proposalgeometry",
            "proposal_applicant",
            "approval",
            # additional form fields for registration of interest
            "exclusive_use",
            "long_term_use",
            "consistent_purpose",
            "consistent_plan",
            "clearing_vegetation",
            "ground_disturbing_works",
            "heritage_site",
            "environmentally_sensitive",
            "wetlands_impact",
            "building_required",
            "significant_change",
            "aboriginal_site",
            "native_title_consultation",
            "mining_tenement",
            "exclusive_use_text",
            "long_term_use_text",
            "consistent_purpose_text",
            "consistent_plan_text",
            "clearing_vegetation_text",
            "ground_disturbing_works_text",
            "heritage_site_text",
            "environmentally_sensitive_text",
            "wetlands_impact_text",
            "building_required_text",
            "significant_change_text",
            "aboriginal_site_text",
            "native_title_consultation_text",
            "mining_tenement_text",
            # additional form fields for lease_licence
            "profit_and_loss_text",
            "cash_flow_text",
            "capital_investment_text",
            "financial_capacity_text",
            "available_activities_text",
            "market_analysis_text",
            "staffing_text",
            "key_personnel_text",
            "key_milestones_text",
            "risk_factors_text",
            "legislative_requirements_text",
            "lodgement_date_display",
            # Gis data fields
            "identifiers",
            "vestings",
            "names",
            "acts",
            "tenures",
            "categories",
            "regions",
            "districts",
            "lgas",
            # Categorisation fields
            "groups",
            "site_name",
            "proponent_reference_number",
            "details_url",
            "competitive_process",
        )
        read_only_fields = ("supporting_documents",)

    def get_approval(self, obj):
        from leaseslicensing.components.approvals.serializers import (
            ApprovalBasicSerializer,
        )

        if obj.approval:
            request = self.context["request"]
            return ApprovalBasicSerializer(
                obj.approval, context={"request": request}
            ).data
        return None

    def get_identifiers(self, obj):
        ids = ProposalIdentifier.objects.filter(proposal=obj).values_list(
            "identifier__id", flat=True
        )
        return Identifier.objects.filter(id__in=ids).values("id", "name")

    def get_vestings(self, obj):
        ids = ProposalVesting.objects.filter(proposal=obj).values_list(
            "vesting__id", flat=True
        )
        return Vesting.objects.filter(id__in=ids).values("id", "name")

    def get_names(self, obj):
        ids = ProposalName.objects.filter(proposal=obj).values_list(
            "name__id", flat=True
        )
        return Name.objects.filter(id__in=ids).values("id", "name")

    def get_acts(self, obj):
        ids = ProposalAct.objects.filter(proposal=obj).values_list("act__id", flat=True)
        return Act.objects.filter(id__in=ids).values("id", "name")

    def get_tenures(self, obj):
        ids = ProposalTenure.objects.filter(proposal=obj).values_list(
            "tenure__id", flat=True
        )
        return Tenure.objects.filter(id__in=ids).values("id", "name")

    def get_categories(self, obj):
        ids = ProposalCategory.objects.filter(proposal=obj).values_list(
            "category__id", flat=True
        )
        return Category.objects.filter(id__in=ids).values("id", "name")

    def get_regions(self, obj):
        ids = ProposalRegion.objects.filter(proposal=obj).values_list(
            "region__id", flat=True
        )
        return Region.objects.filter(id__in=ids).values("id", "name")

    def get_districts(self, obj):
        ids = ProposalDistrict.objects.filter(proposal=obj).values_list(
            "district__id", flat=True
        )
        return District.objects.filter(id__in=ids).values("id", "name")

    def get_lgas(self, obj):
        ids = ProposalLGA.objects.filter(proposal=obj).values_list("lga__id", flat=True)
        return LGA.objects.filter(id__in=ids).values("id", "name")

    def get_details_url(self, obj):
        request = self.context["request"]
        if request.user.is_authenticated:
            if is_internal(request):
                return reverse("internal-proposal-detail", kwargs={"pk": obj.id})
            else:
                return reverse(
                    "external-proposal-detail", kwargs={"proposal_pk": obj.id}
                )

    def get_groups(self, obj):
        group_ids = obj.groups.values_list("group__id", flat=True)
        group_qs = Group.objects.filter(id__in=group_ids).values("id", "name")
        return GroupSerializer(group_qs, many=True).data

    def get_lodgement_date_display(self, obj):
        if obj.lodgement_date:
            return (
                obj.lodgement_date.strftime("%d/%m/%Y")
                + " at "
                + obj.lodgement_date.strftime("%-I:%M %p")
            )

    def get_applicant_type(self, obj):
        if isinstance(obj.applicant, Organisation):
            return "organisation"
        elif isinstance(obj.applicant, ProposalApplicant):
            return "individual"
        elif isinstance(obj.applicant, EmailUser):
            return "individual"
        else:
            return "Applicant not yet assigned"

    def get_applicant(self, obj):
        if isinstance(obj.applicant, Organisation):
            return obj.applicant.ledger_organisation_name
        elif isinstance(obj.applicant, ProposalApplicant):
            return obj.applicant.full_name
        elif isinstance(obj.applicant, EmailUser):
            return f"{obj.applicant.first_name} {obj.applicant.last_name}"
        else:
            return "Applicant not yet assigned"

    def get_applicant_obj(self, obj):
        if isinstance(obj.applicant, Organisation):
            return OrganisationSerializer(obj.applicant).data
        return UserSerializer(obj.applicant).data

    def get_documents_url(self, obj):
        return "/media/{}/proposals/{}/documents/".format(
            settings.MEDIA_APP_DIR, obj.id
        )

    def get_readonly(self, obj):
        return False

    def get_processing_status(self, obj):
        return obj.get_processing_status_display()

    def get_review_status(self, obj):
        return obj.get_review_status_display()

    def get_customer_status(self, obj):
        return obj.get_processing_status_display()

    def get_accessing_user_roles(self, proposal):
        request = self.context.get("request")
        accessing_user = request.user
        roles = []

        for choice in GROUP_NAME_CHOICES:
            group = SystemGroup.objects.get(name=choice[0])
            ids = group.get_system_group_member_ids()
            if accessing_user.id in ids:
                roles.append(group.name)

        referral_ids = list(proposal.referrals.values_list("referral", flat=True))
        if accessing_user.id in referral_ids:
            roles.append("referral")

        return roles

    def get_can_edit_invoicing_details(self, obj):
        request = self.context["request"]
        return (
            Proposal.PROCESSING_STATUS_APPROVED_EDITING_INVOICING
            == obj.processing_status
            and is_finance_officer(request)
        )

    def get_competitive_process(self, obj):
        if obj.originating_competitive_process:
            return CompetitiveProcessSerializer(
                obj.originating_competitive_process, context=self.context
            ).data
        else:
            return None


class CompetitiveProcessSerializer(serializers.ModelSerializer):
    competitive_process_geometries = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    created_at_display = serializers.DateTimeField(
        read_only=True, format="%d/%m/%Y", source="created_at"
    )
    label = serializers.SerializerMethodField(read_only=True)
    details_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CompetitiveProcess
        fields = (
            "id",
            "lodgement_number",
            "competitive_process_geometries",
            "status_display",
            "created_at_display",
            "label",  # A static value to be used on the map
            "details_url",
        )

    def get_status_display(self, obj):
        return {i[0]: i[1] for i in CompetitiveProcess.STATUS_CHOICES}.get(
            obj.status, None
        )

    def get_competitive_process_geometries(self, obj):
        """
        Returns geometries for this Competitive Process as FeatureCollection dict
        """

        from leaseslicensing.components.competitive_processes.serializers import (
            CompetitiveProcessGeometrySaveSerializer,
        )

        geometry_data = {"type": "FeatureCollection", "features": []}
        for geometry in obj.competitive_process_geometries.all():
            pg_serializer = CompetitiveProcessGeometrySaveSerializer(geometry)
            geometry_data["features"].append(pg_serializer.data)

        return geometry_data

    def get_label(self, obj):
        return "Competitive Process"

    def get_details_url(self, obj):
        request = self.context["request"]
        if request.user.is_authenticated:
            if is_internal(request):
                return reverse(
                    "internal-competitiveprocess-detail", kwargs={"pk": obj.id}
                )
            else:
                return ""


class ListProposalMinimalSerializer(serializers.ModelSerializer):
    proposalgeometry = ProposalGeometrySerializer(many=True, read_only=True)
    application_type_name_display = serializers.CharField(
        read_only=True, source="application_type.name_display"
    )
    processing_status_display = serializers.CharField(
        read_only=True, source="get_processing_status_display"
    )
    lodgement_date_display = serializers.DateTimeField(
        read_only=True, format="%d/%m/%Y", source="lodgement_date"
    )
    details_url = serializers.SerializerMethodField(read_only=True)
    competitive_process = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proposal
        fields = (
            "id",
            "processing_status",
            "processing_status_display",
            "proposalgeometry",
            "application_type_name_display",
            "application_type_id",
            "lodgement_number",
            "lodgement_date",
            "lodgement_date_display",
            "details_url",
            "competitive_process",
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

    def get_competitive_process(self, obj):
        if obj.originating_competitive_process:
            return CompetitiveProcessSerializer(
                obj.originating_competitive_process,
                context=self.context,
            ).data
        else:
            return None


class ListProposalSerializer(BaseProposalSerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    applicant_name = serializers.CharField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    assigned_officer = serializers.SerializerMethodField(read_only=True)
    allowed_assessors = EmailUserSerializer(many=True)
    accessing_user_can_process = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
            "id",
            "application_type",
            "proposal_type",
            "approval_level",
            "title",
            "customer_status",
            "processing_status",
            "review_status",
            "applicant",
            "applicant_name",
            "proxy_applicant",
            "submitter",
            "assigned_officer",
            "previous_application",
            "get_history",
            "lodgement_date",
            "readonly",
            "can_user_edit",
            "can_user_view",
            "can_edit_invoicing_details",
            "reference",
            "lodgement_number",
            "lodgement_sequence",
            "can_officer_process",
            "allowed_assessors",
            "proposal_type",
            "accessing_user_can_process",
            "site_name",
            "groups",
            "details_url",
        )
        # the serverSide functionality of datatables is such that only columns that have
        # field 'data' defined are requested from the serializer. We
        # also require the following additional fields for some of the mRender functions
        datatables_always_serialize = (
            "id",
            "application_type",
            "proposal_type",
            "title",
            "customer_status",
            "processing_status",
            "applicant",
            "applicant_name",
            "submitter",
            "assigned_officer",
            "lodgement_date",
            "can_user_edit",
            "can_user_view",
            "reference",
            "lodgement_number",
            "can_officer_process",
            "accessing_user_can_process",
            "can_edit_invoicing_details",
            "site_name",
            "groups",
        )

    def get_accessing_user_can_process(self, proposal):
        request = self.context["request"]
        user = request.user
        accessing_user_can_process = False

        if proposal.processing_status in [
            Proposal.PROCESSING_STATUS_WITH_ASSESSOR,
            Proposal.PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
        ]:
            if user.id in proposal.get_assessor_group().get_system_group_member_ids():
                accessing_user_can_process = True
        elif proposal.processing_status in [
            Proposal.PROCESSING_STATUS_WITH_APPROVER,
        ]:
            if user.id in proposal.get_approver_group().get_system_group_member_ids():
                accessing_user_can_process = True
        elif proposal.processing_status in [
            Proposal.PROCESSING_STATUS_WITH_REFERRAL,
        ]:
            if proposal.referrals.filter(
                Q(referral=user.id),
                Q(processing_status=Referral.PROCESSING_STATUS_WITH_REFERRAL),
            ):
                accessing_user_can_process = True

        return accessing_user_can_process

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return ""

    def get_assigned_officer(self, obj):
        if (
            obj.processing_status == Proposal.PROCESSING_STATUS_WITH_APPROVER
            and obj.assigned_approver
        ):
            email_user = retrieve_email_user(obj.assigned_approver)
            return EmailUserSerializer(email_user).data
        if obj.assigned_officer:
            email_user = retrieve_email_user(obj.assigned_officer)
            return EmailUserSerializer(email_user).data
        return None


class ListProposalReferralSerializer(ListProposalSerializer):
    referral_processing_status = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = ListProposalSerializer.Meta.fields + ("referral_processing_status",)
        datatables_always_serialize = (
            ListProposalSerializer.Meta.datatables_always_serialize
            + ("referral_processing_status",)
        )

    def get_referral_processing_status(self, obj):
        if hasattr(obj, "referral_processing_status"):
            return obj.referral_processing_status
        return None


class ProposalReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source="get_processing_status_display")
    referral_obj = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = "__all__"

    def get_referral_obj(self, obj):
        referral_email_user = retrieve_email_user(obj.referral)
        serializer = EmailUserSerializer(referral_email_user)
        return serializer.data


class AdditionalDocumentSerializer(serializers.ModelSerializer):
    secure_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AdditionalDocument
        fields = "__all__"

    def get_secure_url(self, obj):
        return [get_secure_file_url(obj, "_file")]


class AdditionalDocumentTypeSerializer(serializers.ModelSerializer):
    text = serializers.CharField(source="name")

    class Meta:
        model = AdditionalDocumentType
        fields = "__all__"


class ProposalSerializer(BaseProposalSerializer):
    submitter = serializers.SerializerMethodField(read_only=True)
    processing_status = serializers.SerializerMethodField(read_only=True)
    # Had to add assessor mode and lodgement versions for this serializer to work for
    # external user that is a referral
    assessor_mode = serializers.SerializerMethodField(read_only=True)
    lodgement_versions = serializers.SerializerMethodField(read_only=True)
    referrals = ProposalReferralSerializer(many=True)
    processing_status_id = serializers.SerializerMethodField(read_only=True)
    additional_document_types = ProposalAdditionalDocumentTypeSerializer(
        many=True, read_only=True
    )
    assessor_assessment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proposal
        fields = "__all__"
        extra_fields = [
            "details_text",
            "model_name",
            "assessor_mode",
            "lodgement_versions",
            "referrals",
            "processing_status_id",
            "additional_document_types",
        ]

    def get_field_names(self, declared_fields, info):
        expanded_fields = super().get_field_names(declared_fields, info)
        if getattr(self.Meta, "extra_fields", None):
            return expanded_fields + self.Meta.extra_fields
        return expanded_fields

    def get_readonly(self, obj):
        return obj.can_user_view

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return email_user.get_full_name()
        else:
            return None

    def get_assessor_mode(self, obj):
        request = self.context["request"]
        user = (
            request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
        )
        return {
            "assessor_mode": True,
            "has_assessor_mode": obj.has_assessor_mode(user),
            "assessor_can_assess": obj.can_assess(user),
            "assessor_level": "assessor",
            "assessor_box_view": obj.assessor_comments_view(user),
            "is_referee": obj.is_referee(user),
            "referee_can_edit": obj.referee_can_edit_referral(user),
        }

    def get_lodgement_versions(self, obj):
        # Just return the current version so that the frontend doesn't break
        return [obj.lodgement_versions[0]]

    def get_processing_status_id(self, obj):
        return obj.processing_status

    def get_assessor_assessment(self, obj):
        request = self.context["request"]
        if is_referee(request):
            # External users that are referees should be able to see the assessor assessment
            return ProposalAssessmentSerializer(
                obj.assessor_assessment, context=self.context
            ).data
        return None


class CreateProposalSerializer(BaseProposalSerializer):
    application_type_id = serializers.IntegerField(write_only=True, required=False)
    proposal_type_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Proposal
        fields = (
            "id",
            "application_type_id",
            "submitter",
            "ind_applicant",
            "org_applicant",
            "proposal_type_id",
        )
        read_only_fields = ("id",)


class MigrateProposalSerializer(CreateProposalSerializer):
    class Meta:
        model = Proposal
        fields = (
            "id",
            "added_internally",
            "application_type_id",
            "ind_applicant",
            "org_applicant",
            "proposal_type_id",
            "processing_status",
            "submitter",
            "migrated",
            "original_leaselicence_number",
        )
        read_only_fields = ["id"]


class SaveLeaseLicenceSerializer(BaseProposalSerializer):
    class Meta:
        model = Proposal
        fields = (
            "id",
            "details_text",
            # additional form fields for lease_licence
            "profit_and_loss_text",
            "cash_flow_text",
            "capital_investment_text",
            "financial_capacity_text",
            "available_activities_text",
            "market_analysis_text",
            "staffing_text",
            "key_personnel_text",
            "key_milestones_text",
            "risk_factors_text",
            "legislative_requirements_text",
            "proponent_reference_number",
        )
        read_only_fields = ("id",)


class SubmitLeaseLicenceSerializer(SaveLeaseLicenceSerializer):
    def update(self, instance, validated_data):
        errors = []

        logger.debug(validated_data)

        mandatory_fields = [
            "key_personnel_text",
            "key_milestones_text",
            "risk_factors_text",
            "legislative_requirements_text",
        ]

        if instance.groups.filter(group__name__iexact="tourism").exists():
            tourism_mandatory_fields = [
                "profit_and_loss_text",
                "cash_flow_text",
                "capital_investment_text",
                "financial_capacity_text",
                "available_activities_text",
                "market_analysis_text",
                "staffing_text",
            ]
            mandatory_fields = tourism_mandatory_fields + mandatory_fields

        for mandatory_field in mandatory_fields:
            if not validated_data[mandatory_field]:
                errors.append(
                    _(
                        "Please provide details for {}".format(
                            mandatory_field.replace("_", " ").replace("text", "")
                        )
                    )
                )

        if not instance.deed_poll_documents.count():
            errors.append(_("Please upload a deed poll document"))

        if errors:
            raise serializers.ValidationError(errors)

        return super().update(instance, validated_data)


class SaveRegistrationOfInterestSerializer(BaseProposalSerializer):
    class Meta:
        model = Proposal
        fields = (
            "id",
            "details_text",
            # additional form fields
            "exclusive_use",
            "long_term_use",
            "consistent_purpose",
            "consistent_plan",
            "clearing_vegetation",
            "ground_disturbing_works",
            "heritage_site",
            "environmentally_sensitive",
            "wetlands_impact",
            "building_required",
            "significant_change",
            "aboriginal_site",
            "native_title_consultation",
            "mining_tenement",
            "exclusive_use_text",
            "long_term_use_text",
            "consistent_purpose_text",
            "consistent_plan_text",
            "clearing_vegetation_text",
            "ground_disturbing_works_text",
            "heritage_site_text",
            "environmentally_sensitive_text",
            "wetlands_impact_text",
            "building_required_text",
            "significant_change_text",
            "aboriginal_site_text",
            "native_title_consultation_text",
            "mining_tenement_text",
            "groups",
            "site_name",
        )
        read_only_fields = ("id",)


class SubmitRegistrationOfInterestSerializer(SaveRegistrationOfInterestSerializer):
    """Whilst we may want to allow the user to save their ROI proposal with fields empty,
    we want to be able to request that they are filled out when submitting to avoid wasting time.
    """

    def update(self, instance, validated_data):
        errors = []

        if not instance.proposalgeometry.filter(polygon__isnull=False).count():
            errors.append(
                _(
                    "Please either draw a polygon on the map or upload and process a shapefile"
                )
            )

        if errors:
            raise serializers.ValidationError(errors)

        return super().update(instance, validated_data)

    def validate(self, attrs):
        """If the user has selected yes for any of the questions, they must provide details"""
        errors = []

        logger.debug(attrs)

        if not attrs["details_text"]:
            errors.append(_("Please provide a description of your proposal"))

        question_fields = [
            "exclusive_use",
            "long_term_use",
            "consistent_purpose",
            "consistent_plan",
            "clearing_vegetation",
            "ground_disturbing_works",
            "heritage_site",
            "environmentally_sensitive",
            "wetlands_impact",
            "building_required",
            "significant_change",
            "aboriginal_site",
            "native_title_consultation",
            "mining_tenement",
        ]

        for question_field in question_fields:
            if attrs[question_field] and not attrs.get(f"{question_field}_text", None):
                errors.append(
                    _(
                        "Please provide details for {}".format(
                            question_field.replace("_", " ")
                        )
                    )
                )

        if errors:
            raise serializers.ValidationError(errors)

        return super().validate(attrs)


class SaveProposalSerializer(BaseProposalSerializer):
    proxy_applicant = serializers.IntegerField(required=False)
    assigned_officer = serializers.IntegerField(required=False)

    class Meta:
        model = Proposal
        fields = (
            "id",
            "application_type",
            "title",
            "processing_status",
            "applicant_type",
            "applicant",
            "org_applicant",
            "proxy_applicant",
            "submitter",
            "assigned_officer",
            "previous_application",
            "lodgement_date",
            "requirements",
            "readonly",
            "can_user_edit",
            "can_user_view",
            "reference",
            "lodgement_number",
            "can_officer_process",
            "applicant_details",
            "details_text",
        )
        read_only_fields = ("requirements",)


class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = (
            "id",
            "name",
            "abn",
            "email",
            "phone_number",
        )


class ProposalReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source="get_processing_status_display")
    referral_obj = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = "__all__"

    def get_referral_obj(self, obj):
        referral_email_user = retrieve_email_user(obj.referral)
        serializer = EmailUserSerializer(referral_email_user)
        return serializer.data


class ProposalDeclinedDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalDeclinedDetails
        fields = "__all__"


class ProposalParkSerializer(BaseProposalSerializer):
    applicant = ApplicantSerializer()
    processing_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    submitter = serializers.CharField(source="submitter.get_full_name")
    application_type = serializers.CharField(
        source="application_type.name", read_only=True
    )
    licence_number = serializers.SerializerMethodField(read_only=True)
    licence_number_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proposal
        fields = (
            "id",
            "licence_number",
            "licence_number_id",
            "application_type",
            "approval_level",
            "title",
            "customer_status",
            "processing_status",
            "applicant",
            "proxy_applicant",
            "submitter",
            "lodgement_number",
        )

    def get_licence_number(self, obj):
        return obj.approval.lodgement_number

    def get_licence_number_id(self, obj):
        return obj.approval.id


class ExternalRefereeInviteSerializer(serializers.ModelSerializer):
    proposal_id = serializers.IntegerField(required=False)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = ExternalRefereeInvite
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "organisation",
            "invite_text",
            "proposal_id",
        ]


class RequirementDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequirementDocument
        fields = ("id", "name", "_file")
        # fields = '__all__'


class ProposalStandardRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalStandardRequirement
        fields = ("id", "code", "text", "gross_turnover_required")


class ProposalRequirementSerializer(serializers.ModelSerializer):
    can_referral_edit = serializers.SerializerMethodField()
    requirement_documents = RequirementDocumentSerializer(many=True, read_only=True)
    source = serializers.SerializerMethodField(read_only=True)
    standard_requirement = ProposalStandardRequirementSerializer(read_only=True)
    standard_requirement_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ProposalRequirement
        fields = (
            "id",
            "due_date",
            "reminder_date",
            "free_requirement",
            "standard_requirement",
            "standard_requirement_id",
            "standard",
            "req_order",
            "proposal",
            "recurrence",
            "recurrence_schedule",
            "recurrence_pattern",
            "requirement",
            "is_deleted",
            "copied_from",
            "can_referral_edit",
            "requirement_documents",
            "require_due_date",
            "copied_for_renewal",
            "notification_only",
            "referral",
            "source",
        )
        read_only_fields = ("req_order", "requirement", "copied_from")

    def get_can_referral_edit(self, obj):
        request = self.context["request"]
        user = (
            request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
        )
        return obj.can_referral_edit(user)

    def get_source(self, obj):
        """
        Returns the user who created this proposal requirement
        """

        if obj.source:
            email_user = retrieve_email_user(obj.source)
            return EmailUserSerializer(email_user).data
        else:
            return None


class InternalProposalSerializer(BaseProposalSerializer):
    applicant = serializers.CharField(read_only=True)
    org_applicant = OrganisationSerializer()
    processing_status = serializers.SerializerMethodField(read_only=True)
    processing_status_id = serializers.SerializerMethodField()
    review_status = serializers.SerializerMethodField(read_only=True)
    submitter = serializers.SerializerMethodField(read_only=True)
    proposaldeclineddetails = ProposalDeclinedDetailsSerializer()
    assessor_mode = serializers.SerializerMethodField()
    can_edit_period = serializers.SerializerMethodField()
    current_assessor = serializers.SerializerMethodField()
    latest_referrals = ProposalReferralSerializer(many=True)
    referrals = ProposalReferralSerializer(many=True)
    external_referral_invites = ExternalRefereeInviteSerializer(many=True)
    allowed_assessors = EmailUserSerializer(many=True)
    approval_level_document = serializers.SerializerMethodField()
    # application_type = serializers.CharField(source='application_type.name', read_only=True)
    # reversion_ids = serializers.SerializerMethodField()
    assessor_assessment = ProposalAssessmentSerializer(read_only=True)
    referral_assessments = ProposalAssessmentSerializer(read_only=True, many=True)
    # fee_invoice_url = serializers.SerializerMethodField()

    applicant_obj = serializers.SerializerMethodField()

    approval_issue_date = serializers.SerializerMethodField()
    invoicing_details = InvoicingDetailsSerializer()
    all_lodgement_versions = serializers.SerializerMethodField()
    approved_on = serializers.SerializerMethodField()
    approved_by = serializers.SerializerMethodField()
    site_name = serializers.CharField(source="site_name.name", read_only=True)
    requirements = ProposalRequirementSerializer(many=True, read_only=True)
    can_edit_invoicing_details = serializers.SerializerMethodField()
    additional_document_types = serializers.SerializerMethodField()
    additional_documents = AdditionalDocumentSerializer(many=True, read_only=True)
    additional_documents_missing = serializers.ListField(read_only=True)
    original_leaselicence_number = serializers.CharField(read_only=True)

    class Meta:
        model = Proposal
        fields = (
            "id",
            "model_name",
            "application_type",
            "approval_level",
            "approval_level_document",
            "title",
            "processing_status",
            "review_status",
            "applicant",
            "applicant_obj",
            "org_applicant",
            "proxy_applicant",
            "submitter",
            "applicant_type",
            "assigned_officer",
            "assigned_approver",
            "previous_application",
            "get_history",
            "lodgement_versions",
            "lodgement_date",
            "requirements",
            "readonly",
            "can_user_edit",
            "can_user_view",
            "can_edit_invoicing_details",
            "documents_url",
            "assessor_mode",
            "current_assessor",
            "latest_referrals",
            "referrals",
            "allowed_assessors",
            "accessing_user_roles",
            "proposed_issuance_approval",
            "proposed_decline_status",
            "proposaldeclineddetails",
            "permit",
            "reference",
            "lodgement_number",
            "original_leaselicence_number",
            "lodgement_sequence",
            "can_officer_process",
            "proposal_type",
            "applicant_details",
            "other_details",
            "can_edit_period",
            "assessor_assessment",
            "referral_assessments",
            "proposalgeometry",
            "processing_status_id",
            "details_text",
            "added_internally",
            "competitive_process_to_copy_to",
            "proposal_applicant",
            # additional form fields for registration of interest
            "exclusive_use",
            "long_term_use",
            "consistent_purpose",
            "consistent_plan",
            "clearing_vegetation",
            "ground_disturbing_works",
            "heritage_site",
            "environmentally_sensitive",
            "wetlands_impact",
            "building_required",
            "significant_change",
            "aboriginal_site",
            "native_title_consultation",
            "mining_tenement",
            "exclusive_use_text",
            "long_term_use_text",
            "consistent_purpose_text",
            "consistent_plan_text",
            "clearing_vegetation_text",
            "ground_disturbing_works_text",
            "heritage_site_text",
            "environmentally_sensitive_text",
            "wetlands_impact_text",
            "building_required_text",
            "significant_change_text",
            "aboriginal_site_text",
            "native_title_consultation_text",
            "mining_tenement_text",
            # additional form fields for lease_licence
            "profit_and_loss_text",
            "cash_flow_text",
            "capital_investment_text",
            "financial_capacity_text",
            "available_activities_text",
            "market_analysis_text",
            "staffing_text",
            "key_personnel_text",
            "key_milestones_text",
            "risk_factors_text",
            "legislative_requirements_text",
            "approval_issue_date",
            "invoicing_details",
            "all_lodgement_versions",
            "approved_on",
            "approved_by",
            "identifiers",
            "vestings",
            "names",
            "acts",
            "tenures",
            "categories",
            "regions",
            "districts",
            "lgas",
            "groups",
            "proponent_reference_number",
            "site_name",
            "details_url",
            "external_referral_invites",
            "competitive_process",
            "approval",
            "additional_document_types",
            "additional_documents",
            "additional_documents_missing",
        )

        datatables_always_serialize = {
            "current_assessor",
        }
        read_only_fields = ("requirements",)

    def get_applicant_obj(self, obj):
        if isinstance(obj.applicant, Organisation):
            return OrganisationSerializer(obj.applicant).data
        return EmailUserSerializer(obj.applicant).data

    def get_processing_status_id(self, obj):
        return obj.processing_status

    def get_submitter(self, obj):
        if obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return None

    def get_approval_level_document(self, obj):
        if obj.approval_level_document is not None:
            return [
                obj.approval_level_document.name,
                obj.approval_level_document._file.url,
            ]
        else:
            return obj.approval_level_document

    def get_assessor_mode(self, obj):
        request = self.context["request"]
        user = (
            request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
        )
        return {
            "assessor_mode": True,
            "has_assessor_mode": obj.has_assessor_mode(user),
            "assessor_can_assess": obj.can_assess(user),
            "assessor_level": "assessor",
            "assessor_box_view": obj.assessor_comments_view(user),
            "is_referee": obj.is_referee(user),
            "referee_can_edit": obj.referee_can_edit_referral(user),
        }

    def get_can_edit_period(self, obj):
        request = self.context["request"]
        user = (
            request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
        )
        return obj.can_edit_period(user)

    def get_readonly(self, obj):
        return True

    def get_current_assessor(self, obj):
        return {
            "id": self.context["request"].user.id,
            "name": self.context["request"].user.get_full_name(),
            "email": self.context["request"].user.email,
        }

    def get_reversion_ids(self, obj):
        return obj.reversion_ids[:5]

    def get_approval_issue_date(self, obj):
        if obj.approval:
            return obj.approval.issue_date.strftime("%d/%m/%Y")

    def get_all_lodgement_versions(self, obj):
        """
        Returns all lodgement versions of a proposal, when browsing in debug mode
        """

        query_params = self.context.get("request").query_params
        if query_params.get("debug", False):
            return obj.versions_to_lodgement_dict(obj.revision_versions())
        else:
            return []

    def get_approved_on(self, obj):
        """
        Returns date of approval in DD/MM/YY format if the information is available
        """

        ts = None
        if obj.proposed_issuance_approval:
            ts = obj.proposed_issuance_approval.get("approved_on", None)

        if ts:
            return datetime.datetime.fromtimestamp(ts).date().strftime("%d/%m/%Y")

    def get_approved_by(self, obj):
        """
        Returns the user who approved this proposal if available
        """

        user = None
        if obj.proposed_issuance_approval:
            user = obj.proposed_issuance_approval.get("approved_by", None)

        if user:
            email_user = retrieve_email_user(user)
            return f"{email_user.first_name} {email_user.last_name}"

    def get_additional_document_types(self, obj):
        return obj.additional_document_types.all().values_list(
            "additional_document_type__id", flat=True
        )


class ProposalUserActionSerializer(serializers.ModelSerializer):
    who = serializers.SerializerMethodField()

    class Meta:
        model = ProposalUserAction
        fields = "__all__"

    def get_who(self, proposal_user_action):
        email_user = retrieve_email_user(proposal_user_action.who)
        fullname = email_user.get_full_name()
        return fullname


class ProposalLogEntrySerializer(CommunicationLogEntrySerializer):
    class Meta:
        model = ProposalLogEntry
        fields = "__all__"
        read_only_fields = ("customer",)


class SendReferralSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=True)
    text = serializers.CharField(allow_blank=True)

    def validate(self, data):
        non_field_errors = []

        request = self.context.get("request")
        if request.user.email == data["email"]:
            non_field_errors.append("You cannot send referral to yourself.")

        try:
            EmailUser.objects.get(email=data["email"])
        except EmailUser.DoesNotExist:
            non_field_errors.append("Referral not found.")

        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)

        return data


class DTReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(
        source="proposal.get_processing_status_display"
    )
    application_type = serializers.CharField(source="proposal.application_type.name")
    referral_status = serializers.CharField(source="get_processing_status_display")
    proposal_lodgement_date = serializers.CharField(source="proposal.lodgement_date")
    proposal_lodgement_number = serializers.CharField(
        source="proposal.lodgement_number"
    )
    submitter = serializers.SerializerMethodField()
    # egion = serializers.CharField(source='region.name', read_only=True)
    # referral = EmailUserSerializer()
    referral = serializers.SerializerMethodField()
    # referral = serializers.CharField(source='referral_group.name')
    document = serializers.SerializerMethodField()
    can_user_process = serializers.SerializerMethodField()
    assigned_officer = serializers.CharField(
        source="assigned_officer.get_full_name", allow_null=True
    )

    class Meta:
        model = Referral
        fields = (
            "id",
            "title",
            "submitter",
            "processing_status",
            "application_type",
            "referral_status",
            "lodged_on",
            "proposal",
            "can_be_processed",
            "referral",
            "proposal_lodgement_date",
            "proposal_lodgement_number",
            "text",
            "referral_text",
            "document",
            "assigned_officer",
            "can_user_process",
        )

    def get_referral(self, obj):
        serializer = EmailUserSerializer(retrieve_email_user(obj.referral))
        return serializer.data

    def get_submitter(self, obj):
        # if obj.submitter:
        if hasattr(obj, "submitter") and obj.submitter:
            email_user = retrieve_email_user(obj.submitter)
            return EmailUserSerializer(email_user).data
        else:
            return ""

    def get_document(self, obj):
        # doc = obj.referral_documents.last()
        return [obj.document.name, obj.document._file.url] if obj.document else None

    def get_can_user_process(self, obj):
        request = self.context["request"]
        user = (
            request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
        )
        if obj.can_process(user) and obj.can_be_completed:
            if obj.assigned_officer:
                if obj.assigned_officer == user:
                    return True
            else:
                return True
        return False


class ProposedApprovalROISerializer(serializers.Serializer):
    decision = serializers.CharField(allow_null=False)
    details = serializers.CharField(allow_null=False)
    bcc_email = serializers.CharField(required=False, allow_null=True)


class ProposedApprovalSerializer(serializers.Serializer):
    approval_type = serializers.IntegerField()
    details = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)
    expiry_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    start_date = serializers.DateField(input_formats=["%Y-%m-%d"])
    selected_document_types = serializers.ListField()
    record_management_number = serializers.CharField(allow_null=False)


class ProposalDeclineSerializer(serializers.Serializer):
    reason = serializers.CharField()
    cc_email = serializers.CharField(required=False, allow_null=True)


class OnHoldSerializer(serializers.Serializer):
    comment = serializers.CharField()


class AmendmentRequestSerializer(serializers.ModelSerializer):
    # reason = serializers.SerializerMethodField()

    class Meta:
        model = AmendmentRequest
        fields = "__all__"

    # def get_reason (self,obj):
    # return obj.get_reason_display()
    # return obj.reason.reason


class AmendmentRequestDisplaySerializer(serializers.ModelSerializer):
    reason = serializers.SerializerMethodField()

    class Meta:
        model = AmendmentRequest
        fields = "__all__"

    def get_reason(self, obj):
        # return obj.get_reason_display()
        return obj.reason.reason if obj.reason else None


class SearchKeywordSerializer(serializers.Serializer):
    number = serializers.CharField()
    id = serializers.IntegerField()
    type = serializers.CharField()
    applicant = serializers.CharField()
    # text = serializers.CharField(required=False,allow_null=True)
    text = serializers.JSONField(required=False)


class SearchReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()


class ReferralProposalSerializer(InternalProposalSerializer):
    def get_assessor_mode(self, obj):
        request = self.context["request"]
        user = (
            request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
        )
        referral = Referral.objects.filter(proposal=obj, referral=user).first()

        return {
            "assessor_mode": True,
            "assessor_can_assess": (
                referral.can_assess_referral(user) if referral else None
            ),
            "assessor_level": "referral",
            "assessor_box_view": obj.assessor_comments_view(user),
        }


class ReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source="get_processing_status_display")
    can_be_completed = serializers.BooleanField()
    can_process = serializers.SerializerMethodField()
    assessment = ProposalAssessmentSerializer(many=True, read_only=True)
    application_type = serializers.CharField(read_only=True)
    allowed_assessors = EmailUserSerializer(many=True)
    current_assessor = serializers.SerializerMethodField()
    referral_obj = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = "__all__"

    def get_referral_obj(self, obj):
        referral_email_user = retrieve_email_user(obj.referral)
        serializer = EmailUserSerializer(referral_email_user)
        return serializer.data

    def get_current_assessor(self, obj):
        return {
            "id": self.context["request"].user.id,
            "name": self.context["request"].user.get_full_name(),
            "email": self.context["request"].user.email,
        }

    def get_can_process(self, obj):
        request = self.context["request"]
        user = (
            request.user._wrapped if hasattr(request.user, "_wrapped") else request.user
        )
        return obj.can_process(user)


class ProposalGisDataSerializer(BaseProposalSerializer):
    class Meta:
        model = Proposal
        fields = (
            "identifiers",
            "vestings",
            "names",
            "acts",
            "tenures",
            "categories",
            "regions",
            "districts",
            "lgas",
        )


class ProposalMapFeatureInfoSerializer(ListProposalMinimalSerializer):
    class Meta:
        model = Proposal
        fields = (
            "id",
            "application_type_name_display",
            "details_url",
            "lodgement_number",
            "lodgement_date_display",
            "processing_status_display",
        )
