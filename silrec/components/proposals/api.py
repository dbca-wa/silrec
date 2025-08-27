import logging
from collections import OrderedDict
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import CharField, F, Func, Q, Value
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.utils import get_or_create as get_or_create_emailuser
from rest_framework import serializers, status, views, viewsets
from rest_framework.decorators import action as detail_route
from rest_framework.decorators import action as list_route
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.renderers import DatatablesRenderer
from reversion.models import Version

from leaseslicensing.components.approvals.models import Approval
from leaseslicensing.components.competitive_processes.models import CompetitiveProcess
from leaseslicensing.components.compliances.models import Compliance
from leaseslicensing.components.main.api import (
    LicensingViewSet,
    UserActionLoggingViewset,
)
from leaseslicensing.components.main.decorators import basic_exception_handler
from leaseslicensing.components.main.filters import LedgerDatatablesFilterBackend
from leaseslicensing.components.main.models import ApplicationType
from leaseslicensing.components.main.process_document import process_generic_document
from leaseslicensing.components.main.related_item import RelatedItemsSerializer
from leaseslicensing.components.main.serializers import (
    NewEmailuserSerializer,
    RelatedItemSerializer,
)
from leaseslicensing.components.main.utils import save_site_name, validate_map_files
from leaseslicensing.components.organisations.models import Organisation
from leaseslicensing.components.proposals.email import (
    send_external_referee_invite_email,
)
from leaseslicensing.components.proposals.models import (
    AdditionalDocumentType,
    AmendmentReason,
    AmendmentRequest,
    ChecklistQuestion,
    ExternalRefereeInvite,
    Proposal,
    ProposalAssessment,
    ProposalAssessmentAnswer,
    ProposalGeometry,
    ProposalRequirement,
    ProposalStandardRequirement,
    ProposalType,
    ProposalUserAction,
    Referral,
    ReferralRecipientGroup,
    RequirementDocument,
)
from leaseslicensing.components.proposals.serializers import (  # InternalSaveProposalSerializer,
    AdditionalDocumentTypeSerializer,
    AmendmentRequestDisplaySerializer,
    AmendmentRequestSerializer,
    ChecklistQuestionSerializer,
    CreateProposalSerializer,
    DTReferralSerializer,
    ExternalRefereeInviteSerializer,
    InternalProposalSerializer,
    ListProposalMinimalSerializer,
    ListProposalReferralSerializer,
    ListProposalSerializer,
    MigrateProposalSerializer,
    ProposalAssessmentAnswerSerializer,
    ProposalAssessmentSerializer,
    ProposalDeclineSerializer,
    ProposalGeometrySerializer,
    ProposalLogEntrySerializer,
    ProposalRequirementSerializer,
    ProposalSerializer,
    ProposalStandardRequirementSerializer,
    ProposalTypeSerializer,
    ProposalUserActionSerializer,
    ProposedApprovalROISerializer,
    ProposedApprovalSerializer,
    ReferralSerializer,
    SaveProposalSerializer,
    SendReferralSerializer,
)
from leaseslicensing.components.proposals.utils import (
    make_proposal_applicant_ready,
    populate_gis_data,
    proposal_submit,
    save_assessor_data,
    save_proponent_data,
    save_referral_data,
)
from leaseslicensing.components.users.serializers import ProposalApplicantSerializer
from leaseslicensing.helpers import (
    is_approver,
    is_assessor,
    is_customer,
    is_finance_officer,
    is_internal,
    is_referee,
)
from leaseslicensing.ledger_api_utils import retrieve_email_user
from leaseslicensing.permissions import (
    HasObjectPermission,
    IsAssessor,
    IsAssignedReferee,
)
from leaseslicensing.settings import APPLICATION_TYPES

logger = logging.getLogger(__name__)


class GetAdditionalDocumentTypeDict(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(
        self,
        request,
    ):
        types = AdditionalDocumentType.objects.filter(enabled=True)
        if types:
            serializers = AdditionalDocumentTypeSerializer(types, many=True)
            return Response(serializers.data)
        else:
            return Response({})


class GetApplicationTypeDict(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    @method_decorator(cache_page(60))
    def get(self, request, format=None):
        for_filter = request.query_params.get("for_filter", "")
        for_filter = True if for_filter == "true" else False

        if for_filter:
            application_types = [
                {"id": app_type[0], "text": app_type[1]}
                for app_type in settings.APPLICATION_TYPES
            ]
        else:
            application_types = [
                {"code": app_type[0], "description": app_type[1]}
                for app_type in settings.APPLICATION_TYPES
                if app_type[0] == settings.APPLICATION_TYPE_REGISTRATION_OF_INTEREST
            ]

        return Response(application_types)


class GetApplicationTypeDescriptions(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        data = [app_type[1] for app_type in settings.APPLICATION_TYPES]
        return Response(data)


class GetApplicationStatusesDict(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        data = {}

        for_filter = request.query_params.get("for_filter", "")
        for_filter = True if for_filter == "true" else False

        if for_filter:
            application_statuses = [
                {"id": i[0], "text": i[1]} for i in Proposal.PROCESSING_STATUS_CHOICES
            ]

            return Response(application_statuses)
        else:
            internal_application_statuses = [
                {"code": i[0], "description": i[1]}
                for i in Proposal.PROCESSING_STATUS_CHOICES
            ]

            external_application_statuses = [
                {"code": i[0], "description": i[1]}
                for i in Proposal.PROCESSING_STATUS_CHOICES
            ]

            data["external_statuses"] = external_application_statuses
            data["internal_statuses"] = internal_application_statuses
            return Response(data)


class GetProposalType(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        _type = ProposalType.objects.first()
        if _type:
            serializer = ProposalTypeSerializer(_type)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "There is currently no proposal type."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ProposalFilterBackend(LedgerDatatablesFilterBackend):
    """
    Custom filters
    """

    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        filter_lodged_from = request.GET.get("filter_lodged_from")
        filter_lodged_to = request.GET.get("filter_lodged_to")
        filter_application_type = (
            request.GET.get("filter_application_type")
            if request.GET.get("filter_application_type") != "all"
            else ""
        )
        filter_application_status = (
            request.GET.get("filter_application_status")
            if request.GET.get("filter_application_status") != "all"
            else ""
        )

        if queryset.model is Proposal:
            if filter_lodged_from:
                filter_lodged_from = datetime.strptime(filter_lodged_from, "%Y-%m-%d")
                queryset = queryset.filter(lodgement_date__gte=filter_lodged_from)
            if filter_lodged_to:
                filter_lodged_to = datetime.strptime(filter_lodged_to, "%Y-%m-%d")
                queryset = queryset.filter(lodgement_date__lte=filter_lodged_to)
            if filter_application_type:
                queryset = queryset.filter(application_type_id=filter_application_type)
            if filter_application_status:
                queryset = queryset.filter(processing_status=filter_application_status)

        ledger_lookup_fields = [
            "submitter",
        ]
        # Prevent the external user from searching for officers
        if is_internal(request):
            ledger_lookup_fields += ["assigned_officer", "assigned_approver"]

        queryset = self.apply_request(
            request,
            queryset,
            view,
            ledger_lookup_fields=ledger_lookup_fields,
        )

        setattr(view, "_datatables_filtered_count", queryset.count())
        setattr(view, "_datatables_total_count", total_count)

        return queryset


class ProposalRenderer(DatatablesRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if "view" in renderer_context and hasattr(
            renderer_context["view"], "_datatables_total_count"
        ):
            data["recordsTotal"] = renderer_context["view"]._datatables_total_count
        return super().render(data, accepted_media_type, renderer_context)


class ProposalPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (ProposalFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    renderer_classes = (ProposalRenderer,)
    queryset = Proposal.objects.none()
    serializer_class = ListProposalSerializer
    page_size = 10

    def get_queryset(self):
        user = self.request.user
        if not is_internal(self.request) and not is_customer(self.request):
            return Proposal.objects.none()

        if is_internal(self.request):
            qs = Proposal.objects.all()
            if is_assessor(self.request) or is_approver(self.request):
                target_email_user_id = self.request.query_params.get(
                    "target_email_user_id", None
                )
                if (
                    target_email_user_id
                    and target_email_user_id.isnumeric()
                    and int(target_email_user_id) > 0
                ):
                    qs = qs.filter(submitter=target_email_user_id)
            elif is_finance_officer(self.request):
                qs = qs.filter(
                    processing_status=Proposal.PROCESSING_STATUS_APPROVED_EDITING_INVOICING
                )
            else:
                qs = Proposal.objects.none()

        if is_customer(self.request):
            # Queryset for proposals referred to external user
            email_user_id_assigned = int(
                self.request.query_params.get("email_user_id_assigned", "0")
            )
            if email_user_id_assigned:
                logger.debug(f"email_user_id_assigned: {email_user_id_assigned}")
                qs = Proposal.objects.filter(
                    Q(
                        referrals__in=Referral.objects.filter(
                            referral=email_user_id_assigned,
                            processing_status=Referral.PROCESSING_STATUS_WITH_REFERRAL,
                        )
                    )
                ).annotate(referral_processing_status=F("referrals__processing_status"))
            else:
                qs = Proposal.get_proposals_for_emailuser(user.id)

        target_organisation_id = self.request.query_params.get(
            "target_organisation_id", None
        )
        if (
            target_organisation_id
            and target_organisation_id.isnumeric()
            and int(target_organisation_id) > 0
        ):
            target_organisation_id = int(target_organisation_id)
            qs = qs.exclude(org_applicant__isnull=True).filter(
                org_applicant__id=target_organisation_id
            )
        return qs

    def get_serializer_class(self):
        email_user_id_assigned = self.request.query_params.get(
            "email_user_id_assigned", None
        )
        if self.action == "list" and email_user_id_assigned:
            return ListProposalReferralSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        email_user_id_assigned = int(
            request.query_params.get("email_user_id_assigned", "0")
        )

        if email_user_id_assigned:
            qs = Proposal.objects.filter(
                Q(
                    referrals__in=Referral.objects.exclude(
                        processing_status=Referral.PROCESSING_STATUS_RECALLED
                    ).filter(referral=email_user_id_assigned)
                ),
                referrals__referral=email_user_id_assigned,
            ).annotate(referral_processing_status=F("referrals__processing_status"))

        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            result_page, context={"request": request}, many=True
        )

        return self.paginator.get_paginated_response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def proposals_external(self, request, *args, **kwargs):
        """
        Used by the external dashboard

        http://localhost:8499/api/proposal_paginated/proposal_paginated_external/?format=datatables&draw=1&length=2
        """
        qs = self.get_queryset().exclude(processing_status="discarded")
        # qs = self.filter_queryset(self.request, qs, self)
        qs = self.filter_queryset(qs)

        # on the internal organisations dashboard, filter the Proposal/Approval/Compliance
        # datatables by applicant/organisation
        applicant_id = request.GET.get("org_id")
        if applicant_id:
            qs = qs.filter(org_applicant_id=applicant_id)
        submitter_id = request.GET.get("submitter_id", None)
        if submitter_id:
            qs = qs.filter(submitter=submitter_id)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer = ListProposalSerializer(
            result_page, context={"request": request}, many=True
        )
        return self.paginator.get_paginated_response(serializer.data)


class ProposalViewSet(UserActionLoggingViewset):
    queryset = Proposal.objects.none()
    serializer_class = ProposalSerializer
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        #import ipdb; ipdb.set_trace()
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        return Response(serializer.data)


#    def retrieve(self, request, *args, **kwargs):
#        instance = self.get_object()
#        return super().retrieve(request, *args, **kwargs)


    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return Proposal.objects.all()
        elif is_customer(self.request):
            qs = Proposal.get_proposals_for_emailuser(user.id)
            if Referral.objects.filter(referral=user.id).exists():
                # Allow external user access to proposals they have been referred
                qs = qs | Proposal.objects.filter(
                    processing_status__in=[
                        Proposal.PROCESSING_STATUS_WITH_REFERRAL,
                    ],
                    referrals__in=Referral.objects.filter(referral=user.id),
                )
                return qs.distinct()
            return qs

        logger.warning(
            "User is neither customer nor internal user: {} <{}>".format(
                user.get_full_name(), user.email
            )
        )
        return Proposal.objects.none()

    def get_serializer_class(self):
        if is_internal(self.request):
            return InternalProposalSerializer

        return ProposalSerializer

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def filter_list(self, request, *args, **kwargs):
        """Used by the internal/external dashboard filters"""
        #import ipdb; ipdb.set_trace()
        submitter_qs = (
            self.get_queryset()
            .filter(submitter__isnull=False)
            .distinct("submitter__email")
            .values_list(
                "submitter__first_name", "submitter__last_name", "submitter__email"
            )
        )
        submitters = [
            dict(email=i[2], search_term=f"{i[0]} {i[1]} ({i[2]})")
            for i in submitter_qs
        ]
        application_types = ApplicationType.objects.filter(visible=True).values_list(
            "name", flat=True
        )
        data = dict(
            submitters=submitters,
            application_types=application_types,
            approval_status_choices=[i[1] for i in Approval.STATUS_CHOICES],
        )
        return Response(data)

    @list_route(methods=["GET"], detail=False)
    def list_for_map(self, request, *args, **kwargs):
        """Returns the proposals for the map"""
        proposal_ids = [
            int(id)
            for id in request.query_params.get("proposal_ids", "").split(",")
            if id.lstrip("-").isnumeric()
        ]
        application_type = request.query_params.get("application_type", None)
        processing_status = request.query_params.get("processing_status", None)

        cache_key = settings.CACHE_KEY_MAP_PROPOSALS
        qs = cache.get(cache_key)
        if qs is None:
            qs = (
                self.get_queryset()
                .exclude(proposalgeometry__isnull=True)
                .prefetch_related("proposalgeometry")
            )
            cache.set(cache_key, qs, settings.CACHE_TIMEOUT_2_HOURS)

        if len(proposal_ids) > 0:
            qs = qs.filter(id__in=proposal_ids)

        if (
            application_type
            and application_type.isnumeric()
            and int(application_type) > 0
        ):
            qs = qs.filter(application_type_id=application_type)

        if processing_status:
            qs = qs.filter(processing_status=processing_status)

        serializer = ListProposalMinimalSerializer(
            qs, context={"request": request}, many=True
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def compare_list(self, request, *args, **kwargs):
        """Returns the reversion-compare urls --> list"""
        current_revision_id = (
            Version.objects.get_for_object(self.get_object()).first().revision_id
        )
        versions = (
            Version.objects.get_for_object(self.get_object())
            .select_related("revision__user")
            .filter(
                Q(revision__comment__icontains="status")
                | Q(revision_id=current_revision_id)
            )
        )
        version_ids = [i.id for i in versions]
        urls = [
            f"?version_id2={version_ids[0]}&version_id1={version_ids[i + 1]}"
            for i in range(len(version_ids) - 1)
        ]
        return Response(urls)

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_shapefile_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="shapefile_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_legislative_requirements_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="legislative_requirements_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_risk_factors_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="risk_factors_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_key_milestones_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="key_milestones_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_key_personnel_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="key_personnel_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_staffing_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="staffing_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_market_analysis_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="market_analysis_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_available_activities_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="available_activities_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_financial_capacity_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="financial_capacity_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_capital_investment_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="capital_investment_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_cash_flow_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="cash_flow_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_profit_and_loss_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="profit_and_loss_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_deed_poll_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="deed_poll_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_proposed_approval_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="proposed_approval_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_supporting_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="supporting_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_exclusive_use_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="exclusive_use_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_long_term_use_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="long_term_use_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_consistent_purpose_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="consistent_purpose_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_consistent_plan_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="consistent_plan_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_clearing_vegetation_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="clearing_vegetation_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_ground_disturbing_works_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="ground_disturbing_works_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_heritage_site_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="heritage_site_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_environmentally_sensitive_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="environmentally_sensitive_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_wetlands_impact_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="wetlands_impact_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_building_required_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="building_required_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_significant_change_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="significant_change_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_aboriginal_site_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="aboriginal_site_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_native_title_consultation_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="native_title_consultation_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_mining_tenement_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="mining_tenement_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_proposed_decline_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="proposed_decline_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_lease_licence_approval_document(self, request, *args, **kwargs):
        instance = self.get_object()

        returned_data = process_generic_document(
            request, instance, document_type="lease_licence_approval_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_additional_document(self, request, *args, **kwargs):
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="additional_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()

    def list(self, request, *args, **kwargs):
        proposals = self.get_queryset()

        statuses = list(map(lambda x: x[0], Proposal.PROCESSING_STATUS_CHOICES))
        types = list(map(lambda x: x[0], APPLICATION_TYPES))
        type = request.query_params.get("type", "")
        status = request.query_params.get("status", "")
        if status in statuses and type in types:
            # both status and type exists
            proposals = proposals.filter(
                Q(processing_status=status) & Q(application_type__name=type)
            )
        serializer = ListProposalMinimalSerializer(
            proposals, context={"request": request}, many=True
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def action_log(self, request, *args, **kwargs):
        #import ipdb; ipdb.set_trace()
        instance = self.get_object()
        qs = instance.action_logs.all()
        serializer = ProposalUserActionSerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def comms_log(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.comms_logs.all()
        serializer = ProposalLogEntrySerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def add_comms_log(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            mutable = request.data._mutable
            request.data._mutable = True
            request.data["proposal"] = f"{instance.id}"
            request.data["staff"] = f"{request.user.id}"
            request.data._mutable = mutable
            serializer = ProposalLogEntrySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            comms = serializer.save()

            # Save the files
            for f in request.FILES.getlist("files"):
                document = comms.documents.create()
                document.name = str(f)
                document._file = f
                document.save()

            return Response(serializer.data)

    @detail_route(
        methods=["GET"],
        detail=True,
    )
    @basic_exception_handler
    def revision_version(self, request, *args, **kwargs):
        """
        Returns the version of this model at `revision_id`
        """

        # The django reversion revision id to return the model for
        revision_id = request.query_params.get("revision_id", None)
        # The model instance
        instance = self.get_object()
        # This model's class
        model_class = instance.__class__
        # The serializer to apply
        serializer_class = self.get_serializer_class()
        if not revision_id:
            logger.warning(
                f"Request does not contain revision_id. Returning {model_class.__name__}"
            )
            serializer = serializer_class(instance, context={"request": request})
            return Response(serializer.data)

        try:
            # This model's version for `revision_id`
            version = self.get_object().revision_version(revision_id)
        except IndexError:
            raise serializers.ValidationError(f"Revision {revision_id} does not exist")

        version.revision.version_set.all()

        # An instance of the model version
        instance = model_class(**version.field_dict)
        # Serialize the instance
        serializer = serializer_class(instance, context={"request": request})

        # Feature collection to return as proposal's proposalgeometry property
        geometry_data = {"type": "FeatureCollection", "features": []}
        # Build geometry data structure containing only the geometry versions at `revision_id`
        proposalgeometries = instance.proposalgeometry.all()
        for geometry in proposalgeometries:
            # Get associated proposal geometry at the time of `revision_id`
            pg_versions = (
                Version.objects.get_for_object(geometry)
                .filter(Q(revision_id__lte=revision_id))
                .order_by("-revision__date_created")
            )
            pg_version = pg_versions.first()
            if not pg_version:
                # Geometry might not have existed back then
                continue
            # Build a proposal geometry instance from the version
            proposalgeometry = ProposalGeometry(**pg_version.field_dict)
            pg_serializer = ProposalGeometrySerializer(
                proposalgeometry, context={"request": request}
            )
            # Append the geometry to the feature collection
            geometry_data["features"].append(pg_serializer.data)

        revision_data = serializer.data.copy()
        revision_data["proposalgeometry"] = OrderedDict(geometry_data)

        return Response(revision_data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def requirements(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.requirements.exclude(
            standard_requirement__gross_turnover_required=True
        ).exclude(is_deleted=True)
        serializer = ProposalRequirementSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
        permission_classes=[IsAssessor | HasObjectPermission],
    )
    @basic_exception_handler
    def amendment_request(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = instance.amendment_requests
        qs = qs.filter(status="requested")
        serializer = AmendmentRequestDisplaySerializer(qs, many=True)
        return Response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def user_list(self, request, *args, **kwargs):
        qs = self.get_queryset().exclude(processing_status="discarded")
        serializer = ListProposalSerializer(qs, context={"request": request}, many=True)
        return Response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def user_list_paginated(self, request, *args, **kwargs):
        """
        Placing Paginator class here (instead of settings.py) allows specific method for desired behaviour),
        otherwise all serializers will use the default pagination class

        https://stackoverflow.com/questions/29128225/django-rest-framework-3-1-breaks-pagination-paginationserializer
        """
        proposals = self.get_queryset().exclude(processing_status="discarded")
        paginator = DatatablesPageNumberPagination()
        paginator.page_size = proposals.count()
        result_page = paginator.paginate_queryset(proposals, request)
        serializer = ListProposalSerializer(
            result_page, context={"request": request}, many=True
        )
        return paginator.get_paginated_response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def list_paginated(self, request, *args, **kwargs):
        """
        Placing Paginator class here (instead of settings.py) allows specific method for desired behaviour),
        otherwise all serializers will use the default pagination class

        https://stackoverflow.com/questions/29128225/django-rest-framework-3-1-breaks-pagination-paginationserializer
        """
        proposals = self.get_queryset()
        paginator = DatatablesPageNumberPagination()
        paginator.page_size = proposals.count()
        result_page = paginator.paginate_queryset(proposals, request)
        serializer = ListProposalSerializer(
            result_page, context={"request": request}, many=True
        )
        return paginator.get_paginated_response(serializer.data)

    @detail_route(
        methods=["GET", "POST"],
        detail=True,
    )
    def internal_proposal(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = InternalProposalSerializer(instance, context={"request": request})
        #import ipdb; ipdb.set_trace()
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def submit(self, request, *args, **kwargs):
        instance = self.get_object()
        save_proponent_data(instance, request, self)
        instance = proposal_submit(instance, request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def validate_map_files(self, request, *args, **kwargs):
        instance = self.get_object()
        valid_geometry_saved = validate_map_files(request, instance)
        instance.save()
        if valid_geometry_saved:
            populate_gis_data(instance, "proposalgeometry")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def assign_request_user(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.assign_officer(request, request.user)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def assign_to(self, request, *args, **kwargs):
        instance = self.get_object()
        user_id = request.data.get("assessor_id", None)
        user = None
        if not user_id:
            raise serializers.ValidationError("An assessor id is required")
        try:
            user = EmailUser.objects.get(id=user_id)
        except EmailUser.DoesNotExist:
            raise serializers.ValidationError(
                "A user with the id passed in does not exist"
            )
        instance.assign_officer(request, user)
        # serializer = InternalProposalSerializer(instance,context={'request':request})
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def unassign(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.unassign(request)
        # serializer = InternalProposalSerializer(instance,context={'request':request})
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    @basic_exception_handler
    def back_to_assessor(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.processing_status = Proposal.PROCESSING_STATUS_WITH_ASSESSOR
        # Reset fields related to the propose approve / decline so that the assessor must
        # make a new proposal to approve or deline (since the last one was rejected)
        instance.proposed_decline_status = False
        instance.proposed_issuance_approval = None
        instance.save()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def switch_status(self, request, *args, **kwargs):
        instance = self.get_object()
        status = request.data.get("status")
        approver_comment = request.data.get("approver_comment")
        if not status:
            raise serializers.ValidationError("Status is required")
        else:
            if status not in [
                Proposal.PROCESSING_STATUS_WITH_ASSESSOR,
                Proposal.PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
                Proposal.PROCESSING_STATUS_WITH_APPROVER,
                Proposal.PROCESSING_STATUS_WITH_REFERRAL,
            ]:
                raise serializers.ValidationError("The status provided is not allowed")
        instance.move_to_status(request, status, approver_comment)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def reissue_approval(self, request, *args, **kwargs):
        instance = self.get_object()
        if not is_assessor(request):
            raise PermissionDenied(
                "Assessor permissions are required to reissue approval"
            )

        instance.reissue_approval()
        instance.log_user_action(
            ProposalUserAction.ACTION_REISSUE_APPROVAL.format(instance.id), request
        )
        serializer = InternalProposalSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def renew_approval(self, request, *args, **kwargs):
        instance = self.get_object()
        instance = instance.renew_approval(request)
        serializer = SaveProposalSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def amend_approval(self, request, *args, **kwargs):
        instance = self.get_object()
        error_msg = _("Not allowed to amend this approval.")

        if not is_customer(request):
            raise serializers.ValidationError(error_msg, code="invalid")

        proposals = Proposal.get_proposals_for_emailuser(request.user.id)
        if not proposals.filter(id=instance.id).exists():
            raise serializers.ValidationError(error_msg, code="invalid")

        instance = instance.amend_approval(request)
        serializer = SaveProposalSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @basic_exception_handler
    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    # store comments, deficiencies, etc
    def internal_save(self, request, *args, **kwargs):
        instance = self.get_object()
        # Was previously InternalSaveProposalSerializer however no such serializer exists
        serializer = SaveProposalSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        save_site_name(instance, request.data["site_name"])
        serializer.save()

        save_assessor_data(instance, request, self)

        # serializer_class = self.get_serializer_class()
        # serializer = serializer_class(instance, context={"request": request})
        # return Response(serializer.data)
        return Response()

    @basic_exception_handler
    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    def proposed_approval(self, request, *args, **kwargs):
        instance = self.get_object()
        approval_type = request.data.get("approval_type", None)
        if not approval_type:
            serializer = ProposedApprovalROISerializer(data=request.data)
        else:
            serializer = ProposedApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.proposed_approval(request, request.data)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @basic_exception_handler
    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    def update_lease_licence_approval_documents_approval_type(
        self, request, *args, **kwargs
    ):
        """Used when the user changes the approval type on the proposed approval modal
        so that any uploaded documents are associated with the correct approval type"""
        instance = self.get_object()
        approval_type = request.data.get("approval_type", None)
        # Remove any previously uploaded licence documents
        instance.lease_licence_approval_documents.exclude(
            approval_type_id=approval_type
        ).filter(approval_type_document_type__is_license_document=True).delete()
        # Update the approval type for any remaining (non licence) documents
        instance.lease_licence_approval_documents.update(approval_type_id=approval_type)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def approval_level_document(self, request, *args, **kwargs):
        instance = self.get_object()
        instance = instance.assing_approval_level_document(request)
        serializer = InternalProposalSerializer(instance, context={"request": request})
        return Response(serializer.data)

    @basic_exception_handler
    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    def final_approval(self, request, *args, **kwargs):
        instance = self.get_object()
        approval_type = request.data.get("approval_type", None)
        if not approval_type:
            serializer = ProposedApprovalROISerializer(data=request.data)
        else:
            serializer = ProposedApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.final_approval(request, request.data)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def proposed_decline(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.proposed_decline(request, request.data)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "PATCH",
        ],
        detail=True,
    )
    @basic_exception_handler
    def final_decline(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ProposalDeclineSerializer(instance.proposaldeclineddetails)
        instance.final_decline(request, serializer.data)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def draft(self, request, *args, **kwargs):
        instance = self.get_object()
        save_proponent_data(instance, request, self)
        # return redirect(reverse('external'))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def external_referee_invite(self, request, *args, **kwargs):
        instance = self.get_object()
        request.data["proposal_id"] = instance.id
        serializer = ExternalRefereeInviteSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        if ExternalRefereeInvite.objects.filter(
            archived=False, email=request.data["email"]
        ).exists():
            raise serializers.ValidationError(
                _(
                    "An external referee invitation has already been sent to {email}".format(
                        email=request.data["email"]
                    )
                ),
                code="invalid",
            )
        external_referee_invite = ExternalRefereeInvite.objects.create(
            sent_by=request.user.id, **request.data
        )
        send_external_referee_invite_email(instance, request, external_referee_invite)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def complete_referral(self, request, *args, **kwargs):
        instance = self.get_object()
        referee_id = request.data.get("referee_id", None)
        if not referee_id:
            raise serializers.ValidationError(
                _("referee_id is required"), code="required"
            )

        if not instance.referrals.filter(referral=referee_id).exists():
            msg = _(
                f"There is no referral for application: {instance.lodgement_number} "
                f"and referee (email user): {referee_id}"
            )
            raise serializers.ValidationError(msg, code="invalid")

        save_referral_data(instance, request)

        referral = instance.referrals.get(referral=referee_id)
        referral.complete(request)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def referral_save(self, request, *args, **kwargs):
        instance = self.get_object()
        save_referral_data(instance, request)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def assessor_save(self, request, *args, **kwargs):
        instance = self.get_object()
        save_assessor_data(instance, request, self)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def finance_save(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.save_invoicing_details(request, self.action)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def finance_complete_editing(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.finance_complete_editing(request, self.action)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=["post"], detail=True)
    @basic_exception_handler
    def assessor_send_referral(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SendReferralSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        instance.send_referral(
            request,
            serializer.validated_data["email"],
            serializer.validated_data["text"],
        )
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    @basic_exception_handler
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        application_type_str = request.data.get("application_type", {}).get("code")
        application_type = ApplicationType.objects.get(name=application_type_str)
        proposal_type = ProposalType.objects.get(code=settings.PROPOSAL_TYPE_NEW)

        org_applicant = request.data.get("org_applicant", None)

        data = {
            "org_applicant": org_applicant,
            "ind_applicant": (
                request.user.id if not request.data.get("org_applicant") else None
            ),  # if no org_applicant, assume this proposal is for individual.
            "application_type_id": application_type.id,
            "proposal_type_id": proposal_type.id,
        }

        serializer = CreateProposalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if not org_applicant:
            make_proposal_applicant_ready(instance, request.user)

        serializer = SaveProposalSerializer(instance)
        return Response(serializer.data)

    @basic_exception_handler
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SaveProposalSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @detail_route(methods=["patch"], detail=True)
    @basic_exception_handler
    def discard(self, request, *args, **kwargs):
        http_status = status.HTTP_200_OK
        instance = self.get_object()
        if not instance.can_discard(request):
            raise serializers.ValidationError("Not allowed to discard this proposal.")

        serializer = SaveProposalSerializer(
            instance,
            {
                "processing_status": Proposal.PROCESSING_STATUS_DISCARDED,
                "previous_application": None,
            },
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            ProposalSerializer(instance, context={"request": request}).data,
            status=http_status,
        )

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def update_personal(self, request, *args, **kwargs):
        proposal = self.get_object()
        data = {}
        logger.debug(f"request.data = {request.data}")
        data["first_name"] = request.data.get("first_name")
        data["last_name"] = request.data.get("last_name")

        serializer = ProposalApplicantSerializer(proposal.proposal_applicant, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            f"Personal details of the proposal: {proposal} have been updated with the data: {data}"
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def update_contact(self, request, *args, **kwargs):
        proposal = self.get_object()
        data = {}
        if request.data.get("mobile_number", ""):
            data["mobile_number"] = request.data.get("mobile_number")
        if request.data.get("phone_number", ""):
            data["phone_number"] = request.data.get("phone_number")

        serializer = ProposalApplicantSerializer(proposal.proposal_applicant, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            f"Contact details of the proposal: {proposal} have been updated with the data: {data}"
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def update_address(self, request, *args, **kwargs):
        proposal = self.get_object()
        data = {}
        if "residential_line1" in request.data:
            data["residential_line1"] = request.data.get("residential_line1")
        if "residential_locality" in request.data:
            data["residential_locality"] = request.data.get("residential_locality")
        if "residential_state" in request.data:
            data["residential_state"] = request.data.get("residential_state")
        if "residential_postcode" in request.data:
            data["residential_postcode"] = request.data.get("residential_postcode")
        if "residential_country" in request.data:
            data["residential_country"] = request.data.get("residential_country")
        if request.data.get("postal_same_as_residential"):
            data["postal_same_as_residential"] = True
            data["postal_line1"] = ""
            data["postal_locality"] = ""
            data["postal_state"] = ""
            data["postal_postcode"] = ""
            data["postal_country"] = data["residential_country"]
        else:
            data["postal_same_as_residential"] = False
            if "postal_line1" in request.data:
                data["postal_line1"] = request.data.get("postal_line1")
            if "postal_locality" in request.data:
                data["postal_locality"] = request.data.get("postal_locality")
            if "postal_state" in request.data:
                data["postal_state"] = request.data.get("postal_state")
            if "postal_postcode" in request.data:
                data["postal_postcode"] = request.data.get("postal_postcode")
            if "postal_country" in request.data:
                data["postal_country"] = request.data.get("postal_country")

        serializer = ProposalApplicantSerializer(proposal.proposal_applicant, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        logger.info(
            f"Address details of the proposal: {proposal} have been updated with the data: {data}"
        )
        return Response(serializer.data)

    @detail_route(methods=["get"], detail=True)
    @basic_exception_handler
    def get_related_items(self, request, *args, **kwargs):
        instance = self.get_object()
        related_items = instance.get_related_items()
        serializer = RelatedItemsSerializer(related_items, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=["GET"],
        detail=True,
        renderer_classes=[DatatablesRenderer],
        pagination_class=DatatablesPageNumberPagination,
    )
    def related_items(self, request, *args, **kwargs):
        """Uses union to combine a queryset of multiple different model types
        and uses a generic related item serializer to return the data"""
        instance = self.get_object()
        proposals_queryset = (
            Proposal.objects.filter(
                Q(generated_proposal=instance) | Q(originating_proposal=instance)
            )
            .annotate(
                description=F("processing_status"),
                type=Value("proposal", output_field=CharField()),
            )
            .values("id", "lodgement_number", "description", "type")
        )
        competitive_process_queryset = (
            CompetitiveProcess.objects.filter(
                id__in=[
                    instance.generated_competitive_process_id,
                    instance.originating_competitive_process_id,
                ]
            )
            .annotate(
                description=F("status"),
                type=Value("competitiveprocess", output_field=CharField()),
            )
            .values("id", "lodgement_number", "description", "type")
        )
        approval_queryset = (
            Approval.objects.filter(id=instance.approval_id)
            .annotate(
                description=Func(
                    F("expiry_date"),
                    Value("DD/MM/YYYY"),
                    function="to_char",
                    output_field=CharField(),
                ),
                type=Value("approval", output_field=CharField()),
            )
            .values("id", "lodgement_number", "description", "type")
        )
        queryset = proposals_queryset.union(
            competitive_process_queryset, approval_queryset
        ).order_by("lodgement_number")
        serializer = RelatedItemSerializer(queryset, many=True)
        data = {}
        # Add the fields that the datatables renderer expects
        data["data"] = serializer.data
        data["recordsFiltered"] = queryset.count()
        data["recordsTotal"] = queryset.count()
        return Response(data=data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    def preview_document(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            document = instance.preview_document(request, request.data)
        except NotImplementedError as e:
            e.args[0]
            raise serializers.ValidationError(e.args[0])

        return Response({document})

    @detail_route(
        methods=[
            "POST",
        ],
        detail=False,
    )
    @transaction.atomic
    def migrate(self, request, *args, **kwargs):
        migrated = request.data.get("migrated", False)
        original_leaselicence_number = request.data.get(
            "original_leaselicence_number", None
        )
        org_applicant = request.data.get("org_applicant", None)
        ind_applicant = request.data.get("ind_applicant", None)

        if migrated and not original_leaselicence_number:
            raise serializers.ValidationError(
                _(r"Original lease\licence number is required for migration proposal"),
                code="required",
            )

        if org_applicant:
            try:
                Organisation.objects.get(id=org_applicant)
            except Organisation.DoesNotExist:
                raise serializers.ValidationError(
                    _(
                        f"No organisation with id {org_applicant} exists in the leases licensing database"
                    ),
                    code="invalid",
                )
        else:
            try:
                emailuser = retrieve_email_user(ind_applicant)
            except EmailUser.DoesNotExist:
                raise serializers.ValidationError(
                    _(
                        f"No email user with id {ind_applicant} exists in the ledger database"
                    ),
                    code="invalid",
                )

        lease_license_applicant_type = ApplicationType.objects.get(
            name=settings.APPLICATION_TYPE_LEASE_LICENCE
        )

        if migrated:
            proposal_type = ProposalType.objects.get(
                code=settings.PROPOSAL_TYPE_MIGRATION
            )
        else:
            proposal_type = ProposalType.objects.get(code=settings.PROPOSAL_TYPE_NEW)

        data = {
            "added_internally": True,
            "org_applicant": org_applicant,
            "ind_applicant": ind_applicant,
            "application_type_id": lease_license_applicant_type.id,
            "proposal_type_id": proposal_type.id,
            "processing_status": Proposal.PROCESSING_STATUS_WITH_ASSESSOR,
            # Lease/Licence proposals created internally have the assessor as the submitters
            "submitter": request.user.id,
        }

        if migrated:
            data["migrated"] = migrated
            data["original_leaselicence_number"] = original_leaselicence_number

        serializer = MigrateProposalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        if not org_applicant:
            make_proposal_applicant_ready(instance, emailuser)

        serializer = SaveProposalSerializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=False,
    )
    def add_new_ledger_emailuser(self, request, *args, **kwargs):
        serializer = NewEmailuserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = get_or_create_emailuser(serializer.validated_data["email"])
        return Response(response)


class ReferralViewSet(LicensingViewSet):
    queryset = Referral.objects.none()
    serializer_class = ReferralSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and is_internal(self.request):
            queryset = Referral.objects.all()
            return queryset
        return Referral.objects.none()

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def filter_list(self, request, *args, **kwargs):
        """Used by the external dashboard filters"""
        qs = self.get_queryset()
        submitter_qs = (
            qs.filter(proposal__submitter__isnull=False)
            .order_by("proposal__submitter")
            .distinct("proposal__submitter")
            .values_list(
                "proposal__submitter__first_name",
                "proposal__submitter__last_name",
                "proposal__submitter__email",
            )
        )
        submitters = [
            dict(email=i[2], search_term=f"{i[0]} {i[1]} ({i[2]})")
            for i in submitter_qs
        ]
        processing_status_qs = (
            qs.filter(proposal__processing_status__isnull=False)
            .order_by("proposal__processing_status")
            .distinct("proposal__processing_status")
            .values_list("proposal__processing_status", flat=True)
        )
        processing_status = [
            dict(value=i, name="{}".format(" ".join(i.split("_")).capitalize()))
            for i in processing_status_qs
        ]
        application_types = ApplicationType.objects.filter(visible=True).values_list(
            "name", flat=True
        )
        data = dict(
            submitters=submitters,
            processing_status_choices=processing_status,
            application_types=application_types,
        )
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        return Response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def user_list(self, request, *args, **kwargs):
        qs = self.get_queryset().filter(referral=request.user)
        serializer = DTReferralSerializer(qs, many=True)
        return Response(serializer.data)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def user_group_list(self, request, *args, **kwargs):
        qs = ReferralRecipientGroup.objects.filter().values_list("name", flat=True)
        return Response(qs)

    @list_route(
        methods=[
            "GET",
        ],
        detail=False,
    )
    def datatable_list(self, request, *args, **kwargs):
        proposal = request.GET.get("proposal", None)
        qs = self.get_queryset().all()
        if proposal:
            qs = qs.filter(proposal_id=int(proposal))
        serializer = DTReferralSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    def referral_list(self, request, *args, **kwargs):
        instance = self.get_object()
        qs = Referral.objects.filter(
            referral_group__in=request.user.referralrecipientgroup_set.all(),
            proposal=instance.proposal,
        )
        serializer = DTReferralSerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def remind(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.remind(request)
        serializer = InternalProposalSerializer(
            instance.proposal, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def recall(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.recall(request)
        serializer = InternalProposalSerializer(
            instance.proposal, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def resend(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.resend(request)
        serializer = InternalProposalSerializer(
            instance.proposal, context={"request": request}
        )
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def assign_request_user(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.assign_officer(request, request.user)
        # serializer = InternalProposalSerializer(instance,context={'request':request})
        serializer = self.get_serializer(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @basic_exception_handler
    def assign_to(self, request, *args, **kwargs):
        instance = self.get_object()
        user_id = request.data.get("user_id", None)
        user = None
        if not user_id:
            raise serializers.ValidationError("An assessor id is required")
        try:
            user = EmailUser.objects.get(id=user_id)
        except EmailUser.DoesNotExist:
            raise serializers.ValidationError(
                "A user with the id passed in does not exist"
            )
        instance.assign_officer(request, user)
        # serializer = InternalProposalSerializer(instance,context={'request':request})
        serializer = self.get_serializer(instance, context={"request": request})
        return Response(serializer.data)

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def unassign(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.unassign(request)
        # serializer = InternalProposalSerializer(instance,context={'request':request})
        serializer = self.get_serializer(instance, context={"request": request})
        return Response(serializer.data)


class ProposalRequirementViewSet(LicensingViewSet):
    queryset = ProposalRequirement.objects.none()
    serializer_class = ProposalRequirementSerializer

    def get_queryset(self):
        user_id = self.request.user.id
        if is_internal(self.request):
            return ProposalRequirement.objects.all().exclude(is_deleted=True)
        if is_referee(self.request):
            proposal_ids = list(
                Referral.objects.filter(referral=user_id).values_list(
                    "proposal_id", flat=True
                )
            )
            return ProposalRequirement.objects.filter(
                proposal_id__in=proposal_ids
            ).exclude(is_deleted=True)
        return self.queryset

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def move_up(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.move_up()
        return Response()

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def move_down(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.move_down()
        return Response()

    @detail_route(
        methods=[
            "GET",
        ],
        detail=True,
    )
    @basic_exception_handler
    def discard(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(
        methods=[
            "POST",
        ],
        detail=True,
    )
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def delete_document(self, request, *args, **kwargs):
        instance = self.get_object()
        RequirementDocument.objects.get(id=request.data.get("id")).delete()
        return Response(
            [
                dict(id=i.id, name=i.name, _file=i._file.url)
                for i in instance.requirement_documents.all()
            ]
        )

    @basic_exception_handler
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @basic_exception_handler
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        try:
            referral = Referral.objects.get(
                referral=user.id, proposal=request.data["proposal"]
            )
        except Referral.DoesNotExist:
            referral = None

        # Set associated referral and source user on requirement creation
        serializer.save(referral=referral, source=user.id)

        return Response(serializer.data)


class ProposalStandardRequirementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProposalStandardRequirement.objects.all()
    serializer_class = ProposalStandardRequirementSerializer
    permission_classes = [IsAssessor]

    @list_route(
        methods=[
            "POST",
        ],
        detail=False,
    )
    def application_type_standard_requirements(self, request, *args, **kwargs):
        application_type_id = request.data.get("application_type_id")
        queryset = ProposalStandardRequirement.objects.filter(
            application_type__id=application_type_id
        )
        # Don't show gross turnover related requirements on the front end
        # as they are managed by the system automatically based on the invoicing
        # method that is selected
        queryset = queryset.exclude(gross_turnover_required=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AmendmentRequestViewSet(LicensingViewSet):
    queryset = AmendmentRequest.objects.all()
    serializer_class = AmendmentRequestSerializer
    permission_classes = [IsAssessor | HasObjectPermission]

    @basic_exception_handler
    def create(self, request, *args, **kwargs):
        reason_id = request.data.get("reason_id")
        data = {
            "text": request.data.get("text"),
            "proposal": request.data.get("proposal_id"),
            "officer": request.user.id,
            "reason": reason_id if reason_id else None,
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        instance.generate_amendment(request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AmendmentRequestReasonChoicesView(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        choices_list = []
        # choices = AmendmentRequest.REASON_CHOICES
        choices = AmendmentReason.objects.all()
        if choices:
            for c in choices:
                # choices_list.append({'key': c[0],'value': c[1]})
                choices_list.append({"key": c.id, "value": c.reason})
        return Response(choices_list)


class SearchReferenceView(views.APIView):
    renderer_classes = [
        JSONRenderer,
    ]

    def get(self, request, format=None):
        search_term = request.GET.get("term", "")
        proposals = Proposal.objects.filter(
            Q(lodgement_number__icontains=search_term)
            | Q(original_leaselicence_number__icontains=search_term)
        )[:4]
        proposal_results = [
            {
                "id": proposal.id,
                "text": f"{ proposal.lodgement_number }"
                + f" - { proposal.application_type.name_display }"
                + f" - { proposal.proposal_type.description } [Proposal]",
                "redirect_url": reverse(
                    "internal-proposal-detail", kwargs={"pk": proposal.id}
                ),
            }
            for proposal in proposals
        ]
        approvals = Approval.objects.filter(
            Q(lodgement_number__icontains=search_term)
            | Q(original_leaselicence_number__icontains=search_term)
        )[:4]
        approval_results = [
            {
                "id": approval.id,
                "text": f"{ approval.lodgement_number } [Approval]",
                "redirect_url": reverse(
                    "internal-approval-detail", kwargs={"pk": approval.id}
                ),
            }
            for approval in approvals
        ]
        compliances = Compliance.objects.filter(
            lodgement_number__icontains=search_term
        )[:4]
        compliance_results = [
            {
                "id": compliance.id,
                "text": f"{ compliance.lodgement_number } [Compliance]",
                "redirect_url": reverse(
                    "internal-compliance-detail",
                    kwargs={"pk": compliance.id},
                ),
            }
            for compliance in compliances
        ]
        data_transform = proposal_results + approval_results + compliance_results

        return Response({"results": data_transform})


class AssessorChecklistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChecklistQuestion.objects.none()
    serializer_class = ChecklistQuestionSerializer

    def get_queryset(self):
        qs = ChecklistQuestion.objects.filter(
            Q(list_type="assessor_list") & Q(obsolete=False)
        )
        return qs


class ProposalAssessmentViewSet(LicensingViewSet):
    queryset = ProposalAssessment.objects.all()
    serializer_class = ProposalAssessmentSerializer
    permission_classes = [IsAssessor | IsAssignedReferee]

    @detail_route(methods=["post"], detail=True)
    @basic_exception_handler
    def update_assessment(self, request, *args, **kwargs):
        instance = self.get_object()
        request.data["submitter"] = request.user.id
        serializer = ProposalAssessmentSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        checklist = request.data["checklist"]
        if checklist:
            for chk in checklist:
                try:
                    chk_instance = ProposalAssessmentAnswer.objects.get(id=chk["id"])
                    serializer_chk = ProposalAssessmentAnswerSerializer(
                        chk_instance, data=chk
                    )
                    serializer_chk.is_valid(raise_exception=True)
                    serializer_chk.save()
                except ProposalAssessmentAnswer.DoesNotExist:
                    logger.warning(
                        f"ProposalAssessmentAnswer: {chk['id']} does not exist"
                    )
        # instance.proposal.log_user_action(ProposalUserAction.ACTION_EDIT_VESSEL.format(instance.id),request)
        return Response(serializer.data)


class ExternalRefereeInviteViewSet(LicensingViewSet):
    queryset = ExternalRefereeInvite.objects.filter(archived=False)
    serializer_class = ExternalRefereeInviteSerializer
    # TODO: Fix permission for this viewset
    permission_classes = [IsAssessor | HasObjectPermission]

    @detail_route(methods=["post"], detail=True)
    @basic_exception_handler
    def remind(self, request, *args, **kwargs):
        instance = self.get_object()
        send_external_referee_invite_email(
            instance.proposal, request, instance, reminder=True
        )
        return Response(
            status=status.HTTP_200_OK,
            data={"message": f"Reminder sent to {instance.email} successfully"},
        )

    @detail_route(methods=["patch"], detail=True)
    @basic_exception_handler
    def retract(self, request, *args, **kwargs):
        instance = self.get_object()
        proposal = instance.proposal
        instance.archived = True
        instance.save()
        serializer = InternalProposalSerializer(proposal, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
