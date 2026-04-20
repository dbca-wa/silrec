from collections import OrderedDict
from datetime import date, datetime, timedelta
from django.utils import timezone
import copy


from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import CharField, F, Func, Q, Value
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.cache import cache_page
from django.http import HttpResponse
from django.db import connection
from django.core.exceptions import PermissionDenied
from django.apps import apps

from rest_framework.views import APIView
from rest_framework import serializers, status, views, viewsets
from rest_framework.decorators import action as detail_route
from rest_framework.decorators import action as list_route
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.renderers import DatatablesRenderer
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework.throttling import UserRateThrottle

from reversion.models import Version

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission, SAFE_METHODS

import json
import pandas as pd
from shapely import wkt
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

from silrec.components.proposals.models import (
    Proposal,
    ProposalType,
    SQLReport,
    TextSearchFieldDisplay,
    TextSearchModelConfig,
    ShapefileDocument,
)

from silrec.components.main.models import (
    ApplicationType,
)

from silrec.components.main.process_document import (
    process_generic_document,
)

from silrec.components.main.utils import (
    validate_map_files,
    populate_gis_data,
)
from silrec.components.proposals.serializers import (
    ProposalSerializer,
    ListProposalMinimalSerializer,
    ListProposalSerializer,
    ProposalTypeSerializer,
    SQLReportSerializer,
    TextSearchRequestSerializer,
    TextSearchResultSerializer,
    TextSearchSimpleSerializer,
    TextSearchFieldDisplaySerializer,
    TextSearchModelConfigSerializer,
    ShapefileUploadSerializer,
    ShapefileProcessResultSerializer,
    ShapefileProcessRequestSerializer,
)
from silrec.components.main.api import (
    UserActionLoggingViewset,
)
from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger
from silrec.components.main.decorators import basic_exception_handler

import logging
logger = logging.getLogger(__name__)


class GetApplicationTypeDict(views.APIView):
    renderer_classes = [JSONRenderer,]

    def get(self, request):
        types = ApplicationType.objects.filter(enabled=True)
        if types:
            serializers = ApplicationTypeSerializer(types, many=True)
            return Response(serializers.data)
        else:
            return Response({})


class GetApplicationStatusesDict(views.APIView):
    ''' http://localhost:8001/api/application_statuses_dict?for_filter=true
    '''
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
            data["internal_statuses"] = internal_application_statuses

#            external_application_statuses = [
#                {"code": i[0], "description": i[1]}
#                for i in Proposal.PROCESSING_STATUS_CHOICES
#            ]
#            data["external_statuses"] = external_application_statuses

            return Response(data)


class GetProposalType(views.APIView):
    renderer_classes = [JSONRenderer,]

    def get(self, request):
        _type = ProposalType.objects.first()
        if _type:
            serializers = ProposalTypeSerializer(_type)
            return Response(serializers.data)
        else:
            return Response(
                {"error": "There is currently no proposal type."},
                status=status.HTTP_404_NOT_FOUND,
            )



#class ProposalFilterBackend(LedgerDatatablesFilterBackend):
class ProposalFilterBackend(DatatablesFilterBackend):
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
#        if is_internal(request):
#            ledger_lookup_fields += ["assigned_officer", "assigned_approver"]

#        queryset = self.apply_request(
#            request,
#            queryset,
#            view,
#            ledger_lookup_fields=ledger_lookup_fields,
#        )

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
#        if not is_internal(self.request) and not is_customer(self.request):
#            return Proposal.objects.none()

        qs = Proposal.objects.exclude(processing_status__in=[
                 Proposal.PROCESSING_STATUS_DISCARDED,
                 Proposal.PROCESSING_STATUS_TEMP,
             ])
#        if is_assessor(self.request) or is_approver(self.request):
#            target_email_user_id = self.request.query_params.get(
#                "target_email_user_id", None
#            )
#            if (
#                target_email_user_id
#                and target_email_user_id.isnumeric()
#                and int(target_email_user_id) > 0
#            ):
#                qs = qs.filter(submitter=target_email_user_id)
#        elif is_finance_officer(self.request):
#            qs = qs.filter(
#                processing_status=Proposal.PROCESSING_STATUS_APPROVED_EDITING_INVOICING
#            )
#        else:
#            qs = Proposal.objects.none()

        return qs

    def get_serializer_class(self):
#        email_user_id_assigned = self.request.query_params.get(
#            "email_user_id_assigned", None
#        )
#        if self.action == "list" and email_user_id_assigned:
#            return ListProposalReferralSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        ''' http://localhost:8001/api/proposal_paginated/?draw=1&length=10
        '''
        qs = self.get_queryset()

#        email_user_id_assigned = int(
#            request.query_params.get("email_user_id_assigned", "0")
#        )
#
#        if email_user_id_assigned:
#            qs = Proposal.objects.filter(
#                Q(
#                    referrals__in=Referral.objects.exclude(
#                        processing_status=Referral.PROCESSING_STATUS_RECALLED
#                    ).filter(referral=email_user_id_assigned)
#                ),
#                referrals__referral=email_user_id_assigned,
#            ).annotate(referral_processing_status=F("referrals__processing_status"))

        qs = self.filter_queryset(qs)

        self.paginator.page_size = qs.count()
        result_page = self.paginator.paginate_queryset(qs, request)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            result_page, context={"request": request}, many=True
        )

        return self.paginator.get_paginated_response(serializer.data)


class ProposalViewSet(UserActionLoggingViewset):
    ''' http://localhost:8001/api/proposal/1/  <-- calls retrieve()
    '''
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
        return Proposal.objects.all()

    def get_serializer_class(self):
#        if is_internal(self.request):
#            return InternalProposalSerializer
        return ProposalSerializer

    @list_route(methods=["GET"], detail=False)
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

    @basic_exception_handler
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new proposal with default values"""
        try:
            from silrec.components.main.models import ApplicationType
            from silrec.components.proposals.models import ProposalType

            # Get default objects
            try:
                # Try to get or create default application type
                application_type, _ = ApplicationType.objects.get_or_create(
                    id=1,
                    defaults={'name': 'Default', 'visible': True}
                )
            except Exception as e:
                logger.error(f"Error with application type: {e}")
                # Try to get the first available application type
                application_type = ApplicationType.objects.first()
                if not application_type:
                    return Response(
                        {'error': 'No application type found in the system'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            try:
                # Try to get or create default proposal type
                proposal_type, _ = ProposalType.objects.get_or_create(
                    id=1,
                    defaults={'code': 'new', 'description': 'New Proposal'}
                )
            except Exception as e:
                logger.error(f"Error with proposal type: {e}")
                # Try to get the first available proposal type
                proposal_type = ProposalType.objects.first()
                if not proposal_type:
                    return Response(
                        {'error': 'No proposal type found in the system'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Create a new proposal with default values
            proposal = Proposal.objects.create(
                proposal_type=proposal_type,
                application_type=application_type,
                processing_status=Proposal.PROCESSING_STATUS_DRAFT,
                submitter=request.user.id,
                title=f"Proposal {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"  # Add a default title
            )

            # Ensure lodgement number is generated
            if not proposal.lodgement_number:
                proposal.lodgement_number = f'P{proposal.id:06d}'
                proposal.save()

            logger.info(f"New proposal created by user {request.user.id} with ID {proposal.id}")

            # Return the created proposal data
            serializer = self.get_serializer(proposal, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating new proposal: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error creating proposal: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def transition_status(self, request, *args, **kwargs):
        """
        Transition proposal to a new status
        """
        proposal = self.get_object()
        target_status = request.data.get('target_status')
        comment = request.data.get('comment', '')

        if not target_status:
            return Response(
                {'error': 'target_status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            allowed, message = proposal.can_transition_to(target_status, request.user)
            if not allowed:
                return Response(
                    {'error': message},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Define forward and backward transitions
            forward_transitions = {
                'with_assessor': ['draft'],  # from draft to with_assessor
                'with_reviewer': ['with_assessor'],  # from with_assessor to with_reviewer
                'review_completed': ['with_reviewer']  # from with_reviewer to review_completed
            }

            backward_transitions = {
                'draft': ['with_assessor'],  # from with_assessor to draft
                'with_assessor': ['with_reviewer', 'review_completed'],  # from with_reviewer or review_completed to with_assessor
                'with_reviewer': ['review_completed']  # from review_completed to with_reviewer
            }

            current_status = proposal.processing_status
            is_forward = False

            # Check if this is a forward transition
            if target_status in forward_transitions:
                if current_status in forward_transitions[target_status]:
                    is_forward = True

            # Clear the comment if moving forward
            if is_forward:
                proposal.latest_transition_comment = ''
                logger.info(f"Clearing comment for forward transition: {current_status} -> {target_status}")

            # Save the comment if provided (only for backward transitions)
            if comment and not is_forward:
                proposal.latest_transition_comment = comment

            # Perform the transition
            proposal.transition_to(target_status, request.user, comment if not is_forward else '')

            # Return updated proposal
            serializer = self.get_serializer(proposal, context={"request": request})
            return Response({
                'success': True,
                'message': message,
                'proposal': serializer.data
            })

        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error transitioning proposal {proposal.id}: {str(e)}")
            return Response(
                {'error': f'Error transitioning proposal: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='workflow_options')
    def workflow_options(self, request, id=None):
        """
        Get available workflow transitions for the current user
        """
        proposal = self.get_object()
        current_status = proposal.processing_status

        # Define all possible transitions
        transition_options = {
            'draft': [
                {'key': 'to_assessor', 'label': 'Send to Assessor', 'target': 'with_assessor'}
            ],
            'with_assessor': [
                {'key': 'to_reviewer', 'label': 'Send to Reviewer', 'target': 'with_reviewer'},
                {'key': 'to_draft', 'label': 'Return to Draft', 'target': 'draft'}
            ],
            'with_reviewer': [
                {'key': 'to_review_completed', 'label': 'Send to Review Completed', 'target': 'review_completed'},
                {'key': 'to_assessor', 'label': 'Return to Assessor', 'target': 'with_assessor'}
            ],
            'review_completed': [
                {'key': 'to_reviewer', 'label': 'Return to Reviewer', 'target': 'with_reviewer'}
            ]
        }

        # Get available transitions for current status
        available = []
        for option in transition_options.get(current_status, []):
            allowed, message = proposal.can_transition_to(option['target'], request.user)
            if allowed:
                available.append({
                    **option,
                    'message': message
                })

        return Response({
            'current_status': current_status,
            'available_transitions': available
        })

#    @detail_route(methods=["GET"], detail=True)
#    def compare_list(self, request, *args, **kwargs):
#        """Returns the reversion-compare urls --> list"""
#        current_revision_id = (
#            Version.objects.get_for_object(self.get_object()).first().revision_id
#        )
#        versions = (
#            Version.objects.get_for_object(self.get_object())
#            .select_related("revision__user")
#            .filter(
#                Q(revision__comment__icontains="status")
#                | Q(revision_id=current_revision_id)
#            )
#        )
#        version_ids = [i.id for i in versions]
#        urls = [
#            f"?version_id2={version_ids[0]}&version_id1={version_ids[i + 1]}"
#            for i in range(len(version_ids) - 1)
#        ]
#        return Response(urls)

#    @detail_route(methods=["POST"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def process_shapefile_document(self, request, *args, **kwargs):
#        instance = self.get_object()
#        returned_data = process_generic_document(
#            request, instance, document_type="shapefile_document"
#        )
#        if returned_data:
#            return Response(returned_data)
#        else:
#            return Response()

    def list(self, request, *args, **kwargs):
        ''' http://localhost:8001/api/proposal/
        '''
        proposals = self.get_queryset()

        statuses = list(map(lambda x: x[0], Proposal.PROCESSING_STATUS_CHOICES))
        types = list(map(lambda x: x[0], ApplicationType.APPLICATION_TYPES))
        type = request.query_params.get("type", "")
        status = request.query_params.get("status", "")
        if status in statuses and type in types:
            # both status and type exists
            proposals = proposals.filter(
                Q(processing_status=status) & Q(application_type__name=type)
            )
        #serializer = ListProposalMinimalSerializer(
        serializer = ListProposalSerializer(
            proposals, context={"request": request}, many=True
        )
        return Response(serializer.data)

    @list_route(methods=["GET"], detail=False)
    def list_for_map(self, request, *args, **kwargs):
        """Returns the proposals for the map"""
        #import ipdb; ipdb.set_trace()
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

    @detail_route(methods=["post"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def validate_map_files(self, request, *args, **kwargs):
        instance = self.get_object()
        valid_geometry_saved = validate_map_files(request, instance)
        #import ipdb;ipdb.set_trace()
        instance.save()
        if valid_geometry_saved:
            populate_gis_data(instance, "proposalgeometry")
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @detail_route(methods=["POST"], detail=True)
    @renderer_classes((JSONRenderer,))
    @basic_exception_handler
    def process_shapefile_document(self, request, *args, **kwargs):
        #import ipdb; ipdb.set_trace()
        instance = self.get_object()
        returned_data = process_generic_document(
            request, instance, document_type="shapefile_document"
        )
        if returned_data:
            return Response(returned_data)
        else:
            return Response()



#    @detail_route(methods=["GET"], detail=True)
#    @basic_exception_handler
#    def action_log(self, request, *args, **kwargs):
#        #import ipdb; ipdb.set_trace()
#        instance = self.get_object()
#        qs = instance.action_logs.all()
#        serializer = ProposalUserActionSerializer(qs, many=True)
#        return Response(serializer.data)
#
#    @detail_route(methods=["GET"], detail=True)
#    @basic_exception_handler
#    def comms_log(self, request, *args, **kwargs):
#        instance = self.get_object()
#        qs = instance.comms_logs.all()
#        serializer = ProposalLogEntrySerializer(qs, many=True)
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def add_comms_log(self, request, *args, **kwargs):
#        with transaction.atomic():
#            instance = self.get_object()
#            mutable = request.data._mutable
#            request.data._mutable = True
#            request.data["proposal"] = f"{instance.id}"
#            request.data["staff"] = f"{request.user.id}"
#            request.data._mutable = mutable
#            serializer = ProposalLogEntrySerializer(data=request.data)
#            serializer.is_valid(raise_exception=True)
#            comms = serializer.save()
#
#            # Save the files
#            for f in request.FILES.getlist("files"):
#                document = comms.documents.create()
#                document.name = str(f)
#                document._file = f
#                document.save()
#
#            return Response(serializer.data)
#
#    @detail_route(methods=["GET"], detail=True)
#    @basic_exception_handler
#    def revision_version(self, request, *args, **kwargs):
#        """
#        Returns the version of this model at `revision_id`
#        """
#
#        # The django reversion revision id to return the model for
#        revision_id = request.query_params.get("revision_id", None)
#        # The model instance
#        instance = self.get_object()
#        # This model's class
#        model_class = instance.__class__
#        # The serializer to apply
#        serializer_class = self.get_serializer_class()
#        if not revision_id:
#            logger.warning(
#                f"Request does not contain revision_id. Returning {model_class.__name__}"
#            )
#            serializer = serializer_class(instance, context={"request": request})
#            return Response(serializer.data)
#
#        try:
#            # This model's version for `revision_id`
#            version = self.get_object().revision_version(revision_id)
#        except IndexError:
#            raise serializers.ValidationError(f"Revision {revision_id} does not exist")
#
#        version.revision.version_set.all()
#
#        # An instance of the model version
#        instance = model_class(**version.field_dict)
#        # Serialize the instance
#        serializer = serializer_class(instance, context={"request": request})
#
#        # Feature collection to return as proposal's proposalgeometry property
#        geometry_data = {"type": "FeatureCollection", "features": []}
#        # Build geometry data structure containing only the geometry versions at `revision_id`
#        proposalgeometries = instance.proposalgeometry.all()
#        for geometry in proposalgeometries:
#            # Get associated proposal geometry at the time of `revision_id`
#            pg_versions = (
#                Version.objects.get_for_object(geometry)
#                .filter(Q(revision_id__lte=revision_id))
#                .order_by("-revision__date_created")
#            )
#            pg_version = pg_versions.first()
#            if not pg_version:
#                # Geometry might not have existed back then
#                continue
#            # Build a proposal geometry instance from the version
#            proposalgeometry = ProposalGeometry(**pg_version.field_dict)
#            pg_serializer = ProposalGeometrySerializer(
#                proposalgeometry, context={"request": request}
#            )
#            # Append the geometry to the feature collection
#            geometry_data["features"].append(pg_serializer.data)
#
#        revision_data = serializer.data.copy()
#        revision_data["proposalgeometry"] = OrderedDict(geometry_data)
#
#        return Response(revision_data)
#
#    @list_route(methods=["GET"], detail=False)
#    def user_list(self, request, *args, **kwargs):
#        qs = self.get_queryset().exclude(processing_status="discarded")
#        serializer = ListProposalSerializer(qs, context={"request": request}, many=True)
#        return Response(serializer.data)
#
#    @list_route(methods=["GET"], detail=False)
#    def user_list_paginated(self, request, *args, **kwargs):
#        """
#        Placing Paginator class here (instead of settings.py) allows specific method for desired behaviour),
#        otherwise all serializers will use the default pagination class
#
#        https://stackoverflow.com/questions/29128225/django-rest-framework-3-1-breaks-pagination-paginationserializer
#        """
#        proposals = self.get_queryset().exclude(processing_status="discarded")
#        paginator = DatatablesPageNumberPagination()
#        paginator.page_size = proposals.count()
#        result_page = paginator.paginate_queryset(proposals, request)
#        serializer = ListProposalSerializer(
#            result_page, context={"request": request}, many=True
#        )
#        return paginator.get_paginated_response(serializer.data)
#
#    @list_route(methods=["GET"], detail=False)
#    def list_paginated(self, request, *args, **kwargs):
#        """
#        Placing Paginator class here (instead of settings.py) allows specific method for desired behaviour),
#        otherwise all serializers will use the default pagination class
#
#        https://stackoverflow.com/questions/29128225/django-rest-framework-3-1-breaks-pagination-paginationserializer
#        """
#        proposals = self.get_queryset()
#        paginator = DatatablesPageNumberPagination()
#        paginator.page_size = proposals.count()
#        result_page = paginator.paginate_queryset(proposals, request)
#        serializer = ListProposalSerializer(
#            result_page, context={"request": request}, many=True
#        )
#        return paginator.get_paginated_response(serializer.data)
#
#    @detail_route(methods=["GET", "POST"], detail=True)
#    def internal_proposal(self, request, *args, **kwargs):
#        instance = self.get_object()
#        serializer = InternalProposalSerializer(instance, context={"request": request})
#        #import ipdb; ipdb.set_trace()
#        return Response(serializer.data)
#
#    @detail_route(methods=["post"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def submit(self, request, *args, **kwargs):
#        instance = self.get_object()
#        save_proponent_data(instance, request, self)
#        instance = proposal_submit(instance, request)
#        serializer = self.get_serializer(instance)
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def validate_map_files(self, request, *args, **kwargs):
#        instance = self.get_object()
#        valid_geometry_saved = validate_map_files(request, instance)
#        instance.save()
#        if valid_geometry_saved:
#            populate_gis_data(instance, "proposalgeometry")
#        serializer = self.get_serializer(instance)
#        return Response(serializer.data)
#
#    @detail_route(methods=["GET"], detail=True)
#    @basic_exception_handler
#    def assign_request_user(self, request, *args, **kwargs):
#        instance = self.get_object()
#        instance.assign_officer(request, request.user)
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @basic_exception_handler
#    def assign_to(self, request, *args, **kwargs):
#        instance = self.get_object()
#        user_id = request.data.get("assessor_id", None)
#        user = None
#        if not user_id:
#            raise serializers.ValidationError("An assessor id is required")
#        try:
#            user = EmailUser.objects.get(id=user_id)
#        except EmailUser.DoesNotExist:
#            raise serializers.ValidationError(
#                "A user with the id passed in does not exist"
#            )
#        instance.assign_officer(request, user)
#        # serializer = InternalProposalSerializer(instance,context={'request':request})
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["GET"], detail=True)
#    @basic_exception_handler
#    def unassign(self, request, *args, **kwargs):
#        instance = self.get_object()
#        instance.unassign(request)
#        # serializer = InternalProposalSerializer(instance,context={'request':request})
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["PATCH"], detail=True)
#    @basic_exception_handler
#    def back_to_assessor(self, request, *args, **kwargs):
#        instance = self.get_object()
#        instance.processing_status = Proposal.PROCESSING_STATUS_WITH_ASSESSOR
#        # Reset fields related to the propose approve / decline so that the assessor must
#        # make a new proposal to approve or deline (since the last one was rejected)
#        instance.proposed_decline_status = False
#        instance.proposed_issuance_approval = None
#        instance.save()
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @basic_exception_handler
#    def switch_status(self, request, *args, **kwargs):
#        instance = self.get_object()
#        status = request.data.get("status")
#        approver_comment = request.data.get("approver_comment")
#        if not status:
#            raise serializers.ValidationError("Status is required")
#        else:
#            if status not in [
#                Proposal.PROCESSING_STATUS_WITH_ASSESSOR,
#                Proposal.PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
#                Proposal.PROCESSING_STATUS_WITH_APPROVER,
#                Proposal.PROCESSING_STATUS_WITH_REFERRAL,
#            ]:
#                raise serializers.ValidationError("The status provided is not allowed")
#        instance.move_to_status(request, status, approver_comment)
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @basic_exception_handler
#    def reissue_approval(self, request, *args, **kwargs):
#        instance = self.get_object()
#        if not is_assessor(request):
#            raise PermissionDenied(
#                "Assessor permissions are required to reissue approval"
#            )
#
#        instance.reissue_approval()
#        instance.log_user_action(
#            ProposalUserAction.ACTION_REISSUE_APPROVAL.format(instance.id), request
#        )
#        serializer = InternalProposalSerializer(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @basic_exception_handler
#    def renew_approval(self, request, *args, **kwargs):
#        instance = self.get_object()
#        instance = instance.renew_approval(request)
#        serializer = SaveProposalSerializer(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["GET"], detail=True)
#    @basic_exception_handler
#    def amend_approval(self, request, *args, **kwargs):
#        instance = self.get_object()
#        error_msg = _("Not allowed to amend this approval.")
#
#        if not is_customer(request):
#            raise serializers.ValidationError(error_msg, code="invalid")
#
#        proposals = Proposal.get_proposals_for_emailuser(request.user.id)
#        if not proposals.filter(id=instance.id).exists():
#            raise serializers.ValidationError(error_msg, code="invalid")
#
#        instance = instance.amend_approval(request)
#        serializer = SaveProposalSerializer(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @basic_exception_handler
#    @detail_route(methods=["POST"], detail=True)
#    # store comments, deficiencies, etc
#    def internal_save(self, request, *args, **kwargs):
#        instance = self.get_object()
#        # Was previously InternalSaveProposalSerializer however no such serializer exists
#        serializer = SaveProposalSerializer(instance, data=request.data)
#        serializer.is_valid(raise_exception=True)
#        save_site_name(instance, request.data["site_name"])
#        serializer.save()
#
#        save_assessor_data(instance, request, self)
#
#        # serializer_class = self.get_serializer_class()
#        # serializer = serializer_class(instance, context={"request": request})
#        # return Response(serializer.data)
#        return Response()
#
#    @basic_exception_handler
#    @detail_route(methods=["POST"], detail=True)
#    def proposed_approval(self, request, *args, **kwargs):
#        instance = self.get_object()
#        approval_type = request.data.get("approval_type", None)
#        if not approval_type:
#            serializer = ProposedApprovalROISerializer(data=request.data)
#        else:
#            serializer = ProposedApprovalSerializer(data=request.data)
#        serializer.is_valid(raise_exception=True)
#        instance.proposed_approval(request, request.data)
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @basic_exception_handler
#    @detail_route(methods=["POST"], detail=True)
#    def final_approval(self, request, *args, **kwargs):
#        instance = self.get_object()
#        approval_type = request.data.get("approval_type", None)
#        if not approval_type:
#            serializer = ProposedApprovalROISerializer(data=request.data)
#        else:
#            serializer = ProposedApprovalSerializer(data=request.data)
#        serializer.is_valid(raise_exception=True)
#        instance.final_approval(request, request.data)
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @basic_exception_handler
#    def proposed_decline(self, request, *args, **kwargs):
#        instance = self.get_object()
#        instance.proposed_decline(request, request.data)
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["PATCH"], detail=True)
#    @basic_exception_handler
#    def final_decline(self, request, *args, **kwargs):
#        instance = self.get_object()
#        serializer = ProposalDeclineSerializer(instance.proposaldeclineddetails)
#        instance.final_decline(request, serializer.data)
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def draft(self, request, *args, **kwargs):
#        instance = self.get_object()
#        save_proponent_data(instance, request, self)
#        # return redirect(reverse('external'))
#        serializer = self.get_serializer(instance)
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def complete_referral(self, request, *args, **kwargs):
#        instance = self.get_object()
#        referee_id = request.data.get("referee_id", None)
#        if not referee_id:
#            raise serializers.ValidationError(
#                _("referee_id is required"), code="required"
#            )
#
#        if not instance.referrals.filter(referral=referee_id).exists():
#            msg = _(
#                f"There is no referral for application: {instance.lodgement_number} "
#                f"and referee (email user): {referee_id}"
#            )
#            raise serializers.ValidationError(msg, code="invalid")
#
#        save_referral_data(instance, request)
#
#        referral = instance.referrals.get(referral=referee_id)
#        referral.complete(request)
#
#        serializer = self.get_serializer(instance)
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def referral_save(self, request, *args, **kwargs):
#        instance = self.get_object()
#        save_referral_data(instance, request)
#
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @detail_route(methods=["POST"], detail=True)
#    @renderer_classes((JSONRenderer,))
#    @basic_exception_handler
#    def assessor_save(self, request, *args, **kwargs):
#        instance = self.get_object()
#        save_assessor_data(instance, request, self)
#
#        serializer_class = self.get_serializer_class()
#        serializer = serializer_class(instance, context={"request": request})
#        return Response(serializer.data)
#
#    @basic_exception_handler
#    @transaction.atomic
#    def create(self, request, *args, **kwargs):
#        application_type_str = request.data.get("application_type", {}).get("code")
#        application_type = ApplicationType.objects.get(name=application_type_str)
#        proposal_type = ProposalType.objects.get(code=ProposalType.PROPOSAL_TYPE_NEW)
#
#        data = {
#            "applicant": (request.user.id),
#            "application_type_id": application_type.id,
#            "proposal_type_id": proposal_type.id,
#        }
#
#        serializer = CreateProposalSerializer(data=data)
#        serializer.is_valid(raise_exception=True)
#        instance = serializer.save()
#
#        make_proposal_applicant_ready(instance, request.user)
#
#        serializer = SaveProposalSerializer(instance)
#        return Response(serializer.data)
#
#    @basic_exception_handler
#    def update(self, request, *args, **kwargs):
#        instance = self.get_object()
#        serializer = SaveProposalSerializer(instance, data=request.data)
#        serializer.is_valid(raise_exception=True)
#        self.perform_update(serializer)
#        return Response(serializer.data)
#
#    @detail_route(methods=["patch"], detail=True)
#    @basic_exception_handler
#    def discard(self, request, *args, **kwargs):
#        instance = self.get_object()
#        if not instance.can_discard(request):
#            raise serializers.ValidationError("Not allowed to discard this proposal.")
#
#        serializer = SaveProposalSerializer(
#            instance,
#            {
#                "processing_status": Proposal.PROCESSING_STATUS_DISCARDED,
#                "previous_application": None,
#            },
#            partial=True,
#        )
#        serializer.is_valid(raise_exception=True)
#        self.perform_update(serializer)
#
#        return Response(
#            ProposalSerializer(instance, context={"request": request}).data,
#            status=status.HTTP_200_OK,
#        )
#
#    @detail_route(methods=["GET"], detail=True)
#    @basic_exception_handler
#    def get_related_items(self, request, *args, **kwargs):
#        instance = self.get_object()
#        related_items = instance.get_related_items()
#        serializer = RelatedItemsSerializer(related_items, many=True)
#        return Response(serializer.data)
#
#    @detail_route(
#        methods=["GET"],
#        detail=True,
#        renderer_classes=[DatatablesRenderer],
#        pagination_class=DatatablesPageNumberPagination,
#    )
#    def related_items(self, request, *args, **kwargs):
#        """Uses union to combine a queryset of multiple different model types
#        and uses a generic related item serializer to return the data"""
#        instance = self.get_object()
#        proposals_queryset = (
#            Proposal.objects.filter(
#                Q(generated_proposal=instance) | Q(originating_proposal=instance)
#            )
#            .annotate(
#                description=F("processing_status"),
#                type=Value("proposal", output_field=CharField()),
#            )
#            .values("id", "lodgement_number", "description", "type")
#        )
#        competitive_process_queryset = (
#            CompetitiveProcess.objects.filter(
#                id__in=[
#                    instance.generated_competitive_process_id,
#                    instance.originating_competitive_process_id,
#                ]
#            )
#            .annotate(
#                description=F("status"),
#                type=Value("competitiveprocess", output_field=CharField()),
#            )
#            .values("id", "lodgement_number", "description", "type")
#        )
#        approval_queryset = (
#            Approval.objects.filter(id=instance.approval_id)
#            .annotate(
#                description=Func(
#                    F("expiry_date"),
#                    Value("DD/MM/YYYY"),
#                    function="to_char",
#                    output_field=CharField(),
#                ),
#                type=Value("approval", output_field=CharField()),
#            )
#            .values("id", "lodgement_number", "description", "type")
#        )
#        queryset = proposals_queryset.union(
#            competitive_process_queryset, approval_queryset
#        ).order_by("lodgement_number")
#        serializer = RelatedItemSerializer(queryset, many=True)
#        data = {}
#        # Add the fields that the datatables renderer expects
#        data["data"] = serializer.data
#        data["recordsFiltered"] = queryset.count()
#        data["recordsTotal"] = queryset.count()
#        return Response(data=data)
#
#    @detail_route(methods=["POST"], detail=True)
#    def preview_document(self, request, *args, **kwargs):
#        instance = self.get_object()
#        try:
#            document = instance.preview_document(request, request.data)
#        except NotImplementedError as e:
#            e.args[0]
#            raise serializers.ValidationError(e.args[0])
#
#        return Response({document})


#class SearchReferenceView(views.APIView):
#    renderer_classes = [
#        JSONRenderer,
#    ]
#
#    def get(self, request, format=None):
#        search_term = request.GET.get("term", "")
#        proposals = Proposal.objects.filter(
#            Q(lodgement_number__icontains=search_term)
#            | Q(original_leaselicence_number__icontains=search_term)
#        )[:4]
#        proposal_results = [
#            {
#                "id": proposal.id,
#                "text": f"{ proposal.lodgement_number }"
#                + f" - { proposal.application_type.name_display }"
#                + f" - { proposal.proposal_type.description } [Proposal]",
#                "redirect_url": reverse(
#                    "internal-proposal-detail", kwargs={"pk": proposal.id}
#                ),
#            }
#            for proposal in proposals
#        ]
#        approvals = Approval.objects.filter(
#            Q(lodgement_number__icontains=search_term)
#            | Q(original_leaselicence_number__icontains=search_term)
#        )[:4]
#        approval_results = [
#            {
#                "id": approval.id,
#                "text": f"{ approval.lodgement_number } [Approval]",
#                "redirect_url": reverse(
#                    "internal-approval-detail", kwargs={"pk": approval.id}
#                ),
#            }
#            for approval in approvals
#        ]
#        compliances = Compliance.objects.filter(
#            lodgement_number__icontains=search_term
#        )[:4]
#        compliance_results = [
#            {
#                "id": compliance.id,
#                "text": f"{ compliance.lodgement_number } [Compliance]",
#                "redirect_url": reverse(
#                    "internal-compliance-detail",
#                    kwargs={"pk": compliance.id},
#                ),
#            }
#            for compliance in compliances
#        ]
#        data_transform = proposal_results + approval_results + compliance_results
#
#        return Response({"results": data_transform})


class SQLReportViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SQL Reports"""
    queryset = SQLReport.objects.filter(is_active=True)
    serializer_class = SQLReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter reports by user permissions"""
        qs = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return qs

        # Filter by allowed groups
        user_groups = user.groups.all()
        return qs.filter(
            Q(allowed_groups__in=user_groups) |
            Q(allowed_groups__isnull=True)
        ).distinct()

    @action(detail=False, methods=['get'])
    def list_reports(self, request):
        """Get list of available reports with metadata"""
        reports = self.get_queryset()
        data = []

        for report in reports:
            data.append({
                'id': report.id,
                'name': report.name,
                'description': report.description,
                'report_type': report.report_type,
                'export_formats': report.export_formats,
                'parameters': [
                    {
                        'name': clause['parameter_name'],
                        'label': clause['label'],
                        'field_type': clause['field_type'],
                        'required': clause.get('required', False),
                        'default_value': clause.get('default_value'),
                        'options': report.get_parameter_options(clause['parameter_name'])
                    }
                    for clause in report.where_clauses
                ]
            })

        return Response(data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a report with parameters"""
        report = self.get_object()

        # Check permissions
        if not self.has_report_permission(request.user, report):
            raise PermissionDenied("You don't have permission to run this report")

        # Get parameters from request
        parameters = request.data.get('parameters', {})

        # Handle array parameters from frontend
        processed_parameters = {}
        for key, value in parameters.items():
            if isinstance(value, list):
                # Filter out empty strings and None values
                filtered_values = [v for v in value if v is not None and v != '']
                if filtered_values:
                    processed_parameters[key] = filtered_values
            elif value is not None and value != '':
                processed_parameters[key] = value

        custom_clauses = request.data.get('custom_clauses', [])
        export_format = request.data.get('export_format', 'excel')

        logger.info(f"Processed parameters: {processed_parameters}")
        logger.info(f"Custom clauses: {custom_clauses}")

        # Validate export format
        if export_format not in report.export_formats:
            return Response(
                {'error': f'Export format {export_format} not allowed for this report'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate SQL
        try:
            # First get the base SQL from report
            sql, params = report.get_full_sql(processed_parameters)

            # Add custom clauses if provided
            if custom_clauses:
                sql = self._add_custom_clauses(sql, custom_clauses, params)

            logger.info(f"Final SQL: {sql}")
            logger.info(f"Final params: {params}")

            # Execute query
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

            # Convert to DataFrame for easier export
            df = pd.DataFrame(rows, columns=columns)

            # Export based on format
            if export_format == 'excel':
                return self.export_excel(df, report.name)
            elif export_format == 'csv':
                return self.export_csv(df, report.name)
            elif export_format == 'pdf':
                return self.export_pdf(df, report.name, processed_parameters)
            elif export_format == 'shapefile':
                # Shapefile export would go here
                return self.export_csv(df, report.name)  # Fallback to CSV
            else:
                # Return JSON as fallback
                data = df.to_dict('records')
                return Response({
                    'report_name': report.name,
                    'parameters': processed_parameters,
                    'custom_clauses': custom_clauses,
                    'sql': sql,
                    'data': data,
                    'columns': columns,
                    'row_count': len(rows)
                })

        except Exception as e:
            logger.error(f"Error executing report: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error executing report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _add_custom_clauses(self, sql, custom_clauses, params):
        """Add custom WHERE clauses to SQL query"""
        if not custom_clauses:
            return sql

        # Filter out empty clauses
        valid_clauses = [
            clause for clause in custom_clauses
            if clause.get('field') and clause.get('value') and str(clause.get('value')).strip()
        ]

        if not valid_clauses:
            return sql

        # Convert SQL to uppercase for case-insensitive search
        sql_upper = sql.upper()

        # Check if WHERE already exists
        if "WHERE" in sql_upper:
            # Find WHERE position
            where_pos = sql_upper.find("WHERE")

            # Extract the part after WHERE
            after_where = sql[where_pos + 5:]  # +5 for "WHERE"

            # Get existing conditions
            # Find the next GROUP BY, ORDER BY, or end of string
            group_by_pos = after_where.upper().find("GROUP BY")
            order_by_pos = after_where.upper().find("ORDER BY")

            end_pos = len(after_where)
            if group_by_pos != -1:
                end_pos = group_by_pos
            elif order_by_pos != -1:
                end_pos = order_by_pos

            existing_conditions = after_where[:end_pos].strip()
            after_conditions = after_where[end_pos:] if end_pos < len(after_where) else ""

            # Build new conditions with custom clauses
            new_conditions = existing_conditions

            for clause in valid_clauses:
                field = clause.get('field', '').strip()
                operator = clause.get('operator', '=').strip().upper()
                value = clause.get('value', '').strip()
                condition = clause.get('condition', 'AND').strip().upper()

                # Add the custom clause
                if operator == 'LIKE':
                    new_conditions += f" {condition} {field} ILIKE %s"
                    params.append(f"%{value}%")
                elif operator == 'NOT LIKE':
                    new_conditions += f" {condition} {field} NOT ILIKE %s"
                    params.append(f"%{value}%")
                elif operator == 'IN':
                    # Handle IN operator (expects comma-separated values)
                    values = [v.strip() for v in str(value).split(',')]
                    placeholders = ','.join(['%s'] * len(values))
                    new_conditions += f" {condition} {field} IN ({placeholders})"
                    params.extend(values)
                elif operator in ['IS NULL', 'IS NOT NULL']:
                    new_conditions += f" {condition} {field} {operator}"
                else:
                    new_conditions += f" {condition} {field} {operator} %s"
                    params.append(value)

            # Replace the WHERE clause with new conditions
            before_where = sql[:where_pos + 5]  # Include "WHERE"

            # Ensure there's a space between new_conditions and after_conditions
            if after_conditions and not after_conditions.startswith(' '):
                after_conditions = ' ' + after_conditions

            new_sql = before_where + " " + new_conditions.strip() + after_conditions
            return new_sql.strip()
        else:
            # No WHERE clause exists, need to add one
            # Find where to insert WHERE (before GROUP BY or ORDER BY)
            group_by_pos = sql_upper.find("GROUP BY")
            order_by_pos = sql_upper.find("ORDER BY")

            insert_pos = len(sql)
            if group_by_pos != -1:
                insert_pos = group_by_pos
            elif order_by_pos != -1:
                insert_pos = order_by_pos

            before_insert = sql[:insert_pos].strip()
            after_insert = sql[insert_pos:] if insert_pos < len(sql) else ""

            # Build WHERE clause with custom conditions
            where_conditions = []
            first_condition = True

            for clause in valid_clauses:
                field = clause.get('field', '').strip()
                operator = clause.get('operator', '=').strip().upper()
                value = clause.get('value', '').strip()

                if first_condition:
                    condition = "WHERE"
                    first_condition = False
                else:
                    condition = clause.get('condition', 'AND').strip().upper()

                if operator == 'LIKE':
                    where_conditions.append(f"{condition} {field} ILIKE %s")
                    params.append(f"%{value}%")
                elif operator == 'NOT LIKE':
                    where_conditions.append(f"{condition} {field} NOT ILIKE %s")
                    params.append(f"%{value}%")
                elif operator == 'IN':
                    values = [v.strip() for v in str(value).split(',')]
                    placeholders = ','.join(['%s'] * len(values))
                    where_conditions.append(f"{condition} {field} IN ({placeholders})")
                    params.extend(values)
                elif operator in ['IS NULL', 'IS NOT NULL']:
                    where_conditions.append(f"{condition} {field} {operator}")
                else:
                    where_conditions.append(f"{condition} {field} {operator} %s")
                    params.append(value)

            if where_conditions:
                where_clause = " ".join(where_conditions)

                # Ensure proper spacing
                new_sql = before_insert + " " + where_clause.strip()
                if after_insert:
                    if after_insert and not after_insert[0].isspace():
                        new_sql += " "
                    new_sql += after_insert
                return new_sql.strip()
            else:
                return sql

    def has_report_permission(self, user, report):
        """Check if user has permission to run report"""
        if user.is_superuser:
            return True

        if not report.allowed_groups.exists():
            return True

        user_groups = user.groups.all()
        return report.allowed_groups.filter(id__in=user_groups.values_list('id', flat=True)).exists()

    def export_excel(self, df, report_name):
        """Export DataFrame to Excel"""
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Report', index=False)

        output.seek(0)

        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{report_name}.xlsx"'
        return response

    def export_csv(self, df, report_name):
        """Export DataFrame to CSV"""
        output = io.StringIO()
        df.to_csv(output, index=False)

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{report_name}.csv"'
        return response

    def export_pdf(self, df, report_name, parameters):
        """Export DataFrame to PDF"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Add title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, report_name)

        # Add parameters
        p.setFont("Helvetica", 10)
        y = height - 80

        if parameters:
            p.drawString(50, y, "Parameters:")
            y -= 20

            for key, value in parameters.items():
                if value:
                    p.drawString(70, y, f"{key}: {value}")
                    y -= 15

        # Add table
        y -= 30

        # Convert DataFrame to list of lists for table
        table_data = [df.columns.tolist()] + df.head(100).values.tolist()  # Limit to 100 rows for PDF

        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        # Draw table
        table.wrapOn(p, width - 100, height)
        table.drawOn(p, 50, y - table._height)

        p.showPage()
        p.save()

        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{report_name}.pdf"'
        return response

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Preview report with sample data (first 10 rows)"""
        report = self.get_object()

        # Check permissions
        if not self.has_report_permission(request.user, report):
            raise PermissionDenied("You don't have permission to preview this report")

        # Get parameters from query params
        parameters = {}
        custom_clauses = []

        # Group parameters by name (handle multiple values for same parameter)
        for key, value in request.query_params.items():
            if key.startswith('param_'):
                param_name = key[6:]  # Remove 'param_' prefix

                # Clean up the value (remove extra plus signs)
                clean_value = value.replace('+', ' ').strip()
                if clean_value:
                    if param_name not in parameters:
                        parameters[param_name] = []
                    parameters[param_name].append(clean_value)
            elif key == 'custom_clauses':
                try:
                    custom_clauses = json.loads(value)
                except json.JSONDecodeError:
                    custom_clauses = []

        # Check field_type from report configuration
        # For multiselect fields, keep as list even if only one value
        field_types = {}
        for clause in report.where_clauses:
            if 'parameter_name' in clause:
                field_types[clause['parameter_name']] = clause.get('field_type', 'select')

        logger.info(f"Field types from report: {field_types}")
        logger.info(f"Raw parameters before conversion: {parameters}")

        # Convert parameters based on field_type
        for key in list(parameters.keys()):
            if key in field_types and field_types[key] == 'multiselect':
                # For multiselect, always keep as list
                # Filter out empty values
                filtered_values = [v for v in parameters[key] if v and str(v).strip()]
                if filtered_values:
                    parameters[key] = filtered_values
                else:
                    del parameters[key]
            elif len(parameters[key]) == 1:
                # For other field types, use single value
                parameters[key] = parameters[key][0]
            else:
                # Multiple values for non-multiselect field - keep as array
                # Filter out empty values
                filtered_values = [v for v in parameters[key] if v and str(v).strip()]
                if filtered_values:
                    parameters[key] = filtered_values
                else:
                    del parameters[key]

        logger.info(f"Processed parameters for preview: {parameters}")

        try:
            sql, params = report.get_full_sql(parameters)

            # Add custom clauses if provided
            if custom_clauses:
                sql = self._add_custom_clauses(sql, custom_clauses, params)

            # Add LIMIT for preview
            if "LIMIT" not in sql.upper():
                sql += " LIMIT 10"

            logger.info(f"Preview SQL: {sql}")
            logger.info(f"Preview params: {params}")

            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))

            return Response({
                'report_name': report.name,
                'sql': sql,
                'parameters': parameters,
                'custom_clauses': custom_clauses,
                'data': data,
                'columns': columns,
                'row_count': len(rows)
            })

        except Exception as e:
            logger.error(f'Error previewing report: {e}')
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error previewing report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def available_fields(self, request, pk=None):
        """Get available fields from the SQL query for dropdown"""
        report = self.get_object()

        try:
            # Get fields from the SELECT clause
            select_fields = report.get_available_fields()

            # Combine and format for dropdown
            fields = []

            # Add SELECT fields first
            for field in select_fields:
                fields.append({
                    'value': field,
                    'label': field,
                    'type': 'select_field'
                })

            return Response(fields)

        except Exception as e:
            logger.error(f"Error getting available fields: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Error getting available fields: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class SearchThrottle(UserRateThrottle):
    rate = '500/hour'

class SearchByTextView(APIView):
    """API endpoint for searching text across multiple models"""

    throttle_classes = [SearchThrottle]

    def post(self, request):
        """Handle POST request for text search"""
        # Merge POST data with query params for flexibility
        data = request.data.copy()
        logger.info(f'POST: Request Data: {request.data}')

        # Also check query params for datatable parameters
        for key in ['draw', 'start', 'length', 'order[0][column]', 'order[0][dir]', 'search[value]']:
            if key in request.query_params:
                data[key] = request.query_params.get(key)

        serializer = TextSearchRequestSerializer(data=data)

        if not serializer.is_valid():
            logger.warning(f"Text search validation errors: {serializer.errors}")
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        try:
            results, total_records, filtered_records = self.perform_search(data)

            # Serialize the results
            serialized_results = []
            for result in results:
                # Build details string based on available fields
                details = []
                if result.get('obj_code'):
                    details.append(f"Objective: {result['obj_code']}")
                if result.get('task_name'):
                    details.append(f"Task: {result['task_name']}")
                if result.get('polygon_name'):
                    details.append(f"Polygon: {result['polygon_name']}")
                if result.get('compartment'):
                    details.append(f"Compartment: {result['compartment']}")

                # Add the details field to the result
                result['details'] = '<br/>'.join(details) if details else 'No additional details'
                serialized_results.append(result)

            # Prepare response for datatable
            response_data = {
                'draw': data.get('draw', 1),
                'recordsTotal': total_records,
                'recordsFiltered': filtered_records,
                'data': serialized_results
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error performing text search: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Search failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request):
        """Handle GET request for text search"""
        # Convert GET params to match POST format
        data = request.GET.dict()

        # Handle fields parameter - it might come as fields[]=value1&fields[]=value2
        # or as fields=value1,value2,value3
        fields = []

        # Check for array format: fields[]=value1&fields[]=value2
        if 'fields[]' in data:
            # Handle array format
            fields_param = request.GET.getlist('fields[]')
            fields = [field.strip() for field in fields_param if field.strip()]
        elif 'fields' in data and data['fields']:
            # Handle comma-separated format
            fields = [field.strip() for field in data['fields'].split(',') if field.strip()]

        # If no fields specified, use default
        if not fields:
            fields = ['comments', 'description', 'title', 'name', 'results']

        data['fields'] = fields

        # Parse JSON strings for order and search parameters
        if 'order' in data and data['order']:
            try:
                data['order'] = json.loads(data['order'])
            except (json.JSONDecodeError, TypeError):
                data['order'] = []

        if 'search' in data and data['search']:
            try:
                data['search'] = json.loads(data['search'])
            except (json.JSONDecodeError, TypeError):
                data['search'] = {}

        # Handle datatable parameters
        if 'draw' in data:
            try:
                data['draw'] = int(data['draw'])
            except (ValueError, TypeError):
                data['draw'] = 1

        if 'start' in data:
            try:
                data['start'] = int(data['start'])
            except (ValueError, TypeError):
                data['start'] = 0

        if 'length' in data:
            try:
                data['length'] = int(data['length'])
            except (ValueError, TypeError):
                data['length'] = 25

        serializer = TextSearchRequestSerializer(data=data)

        if not serializer.is_valid():
            logger.warning(f"GET text search validation errors: {serializer.errors}")
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        try:
            results, total_records, filtered_records = self.perform_search(data)

            # Serialize the results
            serialized_results = []
            for result in results:
                # Build details string
                details = []
                if result.get('obj_code'):
                    details.append(f"Objective: {result['obj_code']}")
                if result.get('task_name'):
                    details.append(f"Task: {result['task_name']}")
                if result.get('polygon_name'):
                    details.append(f"Polygon: {result['polygon_name']}")
                if result.get('compartment'):
                    details.append(f"Compartment: {result['compartment']}")

                result['details'] = '<br/>'.join(details) if details else 'No additional details'
                serialized_results.append(result)

            response_data = {
                'draw': int(data.get('draw', 1)),
                'recordsTotal': total_records,
                'recordsFiltered': filtered_records,
                'data': serialized_results
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error performing text search: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Search failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_model_config_from_db(self):
        """Get model configuration from database"""
        from silrec.components.proposals.models import (
            TextSearchModelConfig,
            TextSearchFieldDisplay
        )

        config = {}
        try:
            # Get all active model configurations
            model_configs = TextSearchModelConfig.objects.filter(
                is_active=True
            ).order_by('order')

            for db_config in model_configs:
                config[db_config.key] = {
                    'model': db_config.model_name,
                    'display_name': db_config.display_name,
                    'search_fields': db_config.get_search_fields_list(),
                    'date_field': db_config.date_field,
                    'id_field': db_config.id_field,
                    'detail_fields': db_config.detail_fields or [],
                    'url_pattern': db_config.url_pattern,
                }
        except Exception as e:
            logger.warning(f"Error loading model config from DB: {e}")
            # Fallback to default configuration if DB is not ready
            config = self.get_default_model_config()

        return config

    def get_field_display_from_db(self):
        """Get field display names from database"""
        from silrec.components.proposals.models import TextSearchFieldDisplay

        field_display = {}
        try:
            # Get all active field displays
            field_displays = TextSearchFieldDisplay.objects.filter(
                is_active=True
            ).order_by('order')

            for field_display_obj in field_displays:
                field_display[field_display_obj.field_name] = field_display_obj.display_name
        except Exception as e:
            logger.warning(f"Error loading field display from DB: {e}")
            # Fallback to default if DB is not ready
            field_display = self.get_default_field_display()

        return field_display

    def get_default_model_config(self):
        """Default fallback configuration"""
        return {
            'proposal': {
                'model': 'silrec.Proposal',
                'display_name': 'Proposals',
                'search_fields': ['processing_status', 'title'],
                'date_field': 'created_date',
                'id_field': 'id',
                'detail_fields': ['title'],
                'url_pattern': '/internal/proposal/{id}/'
            },
            'polygon': {
                'model': 'silrec.Polygon',
                'display_name': 'Polygons',
                'search_fields': ['name'],
                'date_field': 'created_on',
                'id_field': 'polygon_id',
                'detail_fields': ['compartment', 'polygon_name'],
                'url_pattern': '/internal/polygon/{id}/'
            },
            'cohort': {
                'model': 'silrec.Cohort',
                'display_name': 'Cohorts',
                'search_fields': ['comments', 'obj_code', 'species'],
                'date_field': 'created_on',
                'id_field': 'cohort_id',
                'detail_fields': [],
                'url_pattern': '/internal/cohort/{id}/'
            },
            'treatment': {
                'model': 'silrec.Treatment',
                'display_name': 'Treatments',
                'search_fields': ['results', 'reference'],
                'date_field': 'created_on',
                'id_field': 'treatment_id',
                'detail_fields': ['task_name'],
                'url_pattern': '/internal/treatment/{id}/'
            },
            'treatment_xtra': {
                'model': 'silrec.Treatmentxtra',
                'display_name': 'Treatment Extras',
                'search_fields': ['zresult_standard'],
                'date_field': 'treatment__created_on',
                'id_field': 'treatment_xtra_id',
                'detail_fields': [],
                'url_pattern': '/internal/treatment-extra/{id}/'
            },
            'survey_assessment_document': {
                'model': 'silrec.SurveyAssessmentDocument',
                'display_name': 'Survey Documents',
                'search_fields': ['description', 'title'],
                'date_field': 'created_on',
                'id_field': 'document_id',
                'detail_fields': [],
                'url_pattern': '/internal/survey-document/{id}/'
            },
            'silviculturist_comment': {
                'model': 'silrec.SilviculturistComment',
                'display_name': 'Silviculturist Comments',
                'search_fields': ['comment'],
                'date_field': 'created_on',
                'id_field': 's_comment_id',
                'detail_fields': [],
                'url_pattern': '/internal/silviculturist-comment/{id}/'
            },
            'prescription': {
                'model': 'silrec.Prescription',
                'display_name': 'Prescriptions',
                'search_fields': ['comment'],
                'date_field': 'task__created_on',
                'id_field': 'prescription_id',
                'detail_fields': [],
                'url_pattern': '/internal/prescription/{id}/'
            }
        }

    def get_default_field_display(self):
        """Default fallback field display names"""
        return {
            'comment': 'Comments',
            'comments': 'Comments',
            'description': 'Description',
            'title': 'Title',
            'name': 'Name',
            'results': 'Results',
            'reference': 'Reference',
            'extra_info': 'Extra Info',
            'herbicide_app_spec': 'Herbicide Spec',
            'obj_code': 'Obj Code',
            'species': 'Species',
            'task_description': 'Task Description',
            'processing_status': 'Processing Status',
            'zresult_standard': 'Z Result Standard',
        }

    def perform_search(self, params):
        """Perform the actual text search across models"""
        search_text = params['search_text']
        match_type = params['match_type']
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        case_sensitive = params.get('case_sensitive', False)
        model_filter = params.get('model', 'all')
        fields_filter = params.get('fields', [])

        # Pagination parameters
        start = params.get('start', 0)
        length = params.get('length', 25)

        all_results = []
        total_records = 0
        filtered_records = 0

        # Get configurations from database (with fallback)
        MODEL_CONFIG = self.get_model_config_from_db()
        FIELD_DISPLAY_NAMES = self.get_field_display_from_db()

        #import ipdb; ipdb.set_trace()
        # Determine which models to search
        models_to_search = MODEL_CONFIG.keys() if model_filter == 'all' else [model_filter]

        logger.info(f'Search Text: {search_text}')
        logger.info(f'Fields Filter: {fields_filter}')
        logger.info(f'Model Filter: {model_filter}')
        logger.info(f'Models To Search: {models_to_search}')

        for model_key in models_to_search:
            if model_key not in MODEL_CONFIG:
                continue

            config = MODEL_CONFIG[model_key]

            try:
                # Get the actual model class
                app_label, model_name = config['model'].split('.')
                model_class = apps.get_model(app_label, model_name)

                # Build the queryset
                queryset = model_class.objects.all()

                # Apply date filters if provided
                date_field = config.get('date_field', 'created_on')

                # Handle foreign key date fields (like 'task__created_on')
                if '__' in date_field:
                    # For filtering, we can use the double underscore directly
                    if date_from:
                        queryset = queryset.filter(**{f"{date_field}__gte": date_from})
                    if date_to:
                        date_to_plus_one = date_to + timedelta(days=1)
                        queryset = queryset.filter(**{f"{date_field}__lt": date_to_plus_one})
                else:
                    # For simple date fields
                    if date_from:
                        queryset = queryset.filter(**{f"{date_field}__gte": date_from})
                    if date_to:
                        date_to_plus_one = date_to + timedelta(days=1)
                        queryset = queryset.filter(**{f"{date_field}__lt": date_to_plus_one})

                # Get total records count for this model
                total_records += queryset.count()

                # Build search conditions
                search_conditions = Q()

                # Determine which fields to search in this model
                model_search_fields = []
                if fields_filter:
                    # Only search fields that are both in the model and in the filter
                    model_search_fields = [f for f in fields_filter if f in config['search_fields']]
                else:
                    model_search_fields = config['search_fields']

                # Add config search fields if not present
                #model_search_fields = set(config.get('search_fields', []) + list(model_search_fields))
                if not model_search_fields:
                    continue

                # Create search conditions for each field
                for field in model_search_fields:
                    if hasattr(model_class, field):
                        field_lookup = f"{field}__"

                        # Apply the appropriate lookup based on match type and case sensitivity
                        if match_type == 'exact':
                            if case_sensitive:
                                field_lookup += 'exact'
                            else:
                                field_lookup += 'iexact'
                        elif match_type == 'starts_with':
                            if case_sensitive:
                                field_lookup += 'startswith'
                            else:
                                field_lookup += 'istartswith'
                        elif match_type == 'ends_with':
                            if case_sensitive:
                                field_lookup += 'endswith'
                            else:
                                field_lookup += 'iendswith'
                        else:  # contains (default)
                            if case_sensitive:
                                field_lookup += 'contains'
                            else:
                                field_lookup += 'icontains'

                        search_conditions |= Q(**{field_lookup: search_text})

                # Apply the search conditions
                queryset = queryset.filter(search_conditions)

                # Get filtered count for this model
                filtered_count = queryset.count()
                filtered_records += filtered_count
                logger.info(f'{model_name}({filtered_count}) - Search Conditions: {search_conditions}')

                # Process results (with limit for performance)
                max_results_per_model = 1000  # Limit results per model for performance
                for obj in queryset[:max_results_per_model]:
                    # Find which field(s) contain the search text
                    matching_fields = []

                    for field in model_search_fields:
                        if hasattr(obj, field):
                            field_value = getattr(obj, field)
                            if field_value:
                                field_str = str(field_value)
                                search_text_lower = search_text.lower()
                                field_value_lower = field_str.lower()

                                if match_type == 'exact':
                                    matches = (field_str == search_text) if case_sensitive else (
                                        field_value_lower == search_text_lower)
                                elif match_type == 'starts_with':
                                    if case_sensitive:
                                        matches = field_str.startswith(search_text)
                                    else:
                                        matches = field_value_lower.startswith(search_text_lower)
                                elif match_type == 'ends_with':
                                    if case_sensitive:
                                        matches = field_str.endswith(search_text)
                                    else:
                                        matches = field_value_lower.endswith(search_text_lower)
                                else:  # contains
                                    if case_sensitive:
                                        matches = search_text in field_str
                                    else:
                                        matches = search_text_lower in field_value_lower

                                if matches:
                                    matching_fields.append(field)

                    # Create a result for each matching field
                    for field in matching_fields:
                        field_value = getattr(obj, field)

                        # Get preview text
                        preview = str(field_value)
                        if len(preview) > 200:
                            preview = preview[:200] + '...'

                        # Get date field value - handle foreign key traversal
                        date_field = config.get('date_field', 'created_on')
                        created_date = None

                        try:
                            if '__' in date_field:
                                # Traverse foreign key relationship
                                parts = date_field.split('__')
                                current_obj = obj
                                for part in parts:
                                    if hasattr(current_obj, part):
                                        current_obj = getattr(current_obj, part)
                                    else:
                                        current_obj = None
                                        break
                                if current_obj:
                                    created_date = current_obj
                            else:
                                # Simple field
                                if hasattr(obj, date_field):
                                    created_date = getattr(obj, date_field, None)
                        except Exception as e:
                            logger.warning(f"Error getting date for {model_key}: {e}")
                            created_date = None

                        # Get ID field value
                        id_field = config.get('id_field', 'id')
                        record_id = getattr(obj, id_field, None)

                        if record_id is None:
                            continue

                        # Build result object
                        result = {
                            'model_type': model_key,
                            'model_display': config['display_name'],
                            'record_id': record_id,
                            'field_found': field,
                            'field_display': FIELD_DISPLAY_NAMES.get(field, field),
                            'text_preview': preview,
                            'matching_text': str(field_value),
                            'created_on': created_date,
                            'created_by': self._get_created_by(obj),
                            'action_url': config['url_pattern'].format(id=record_id)
                        }

                        # Add detail fields if they exist
                        for detail_field in config.get('detail_fields', []):
                            if hasattr(obj, detail_field):
                                detail_value = getattr(obj, detail_field, None)
                                if detail_value:
                                    result[detail_field] = str(detail_value)

                        all_results.append(result)

            except Exception as e:
                logger.warning(f"Error searching model {model_key}: {str(e)}", exc_info=True)
                continue

        # Fix for sorting: Convert all dates to proper datetime objects or None
        for result in all_results:
            created_on = result.get('created_on')
            if created_on:
                # Check if it's a date/datetime object
                if isinstance(created_on, (date, datetime)):
                    # It's already a date/datetime, keep it
                    pass
                elif hasattr(created_on, 'date') and callable(getattr(created_on, 'date', None)):
                    # It might be a model instance with a date() method
                    try:
                        result['created_on'] = created_on.date()
                    except:
                        result['created_on'] = None
                else:
                    # Not a date, set to None
                    result['created_on'] = None

        # Apply ordering (by created date desc by default)
        # Handle None dates by putting them at the end
        all_results.sort(key=lambda x: (
            x['created_on'] if x['created_on'] and isinstance(x['created_on'], (date, datetime))
            else datetime.min
        ), reverse=True)

        # Apply pagination
        if start < len(all_results):
            end = min(start + length, len(all_results))
            paginated_results = all_results[start:end]
        else:
            paginated_results = []

        return paginated_results, total_records, filtered_records

    # Keep the rest of the methods (_get_created_by, post, get) unchanged


    def _get_created_by(self, obj):
        """Extract created by information from object"""
        # Try common field names
        for field in ['created_by', 'creator', 'author', 'user', 'created_by_user']:
            if hasattr(obj, field):
                creator = getattr(obj, field)
                if creator:
                    if hasattr(creator, 'username'):
                        return creator.username
                    elif hasattr(creator, 'get_full_name'):
                        full_name = creator.get_full_name()
                        if full_name.strip():
                            return full_name
                        else:
                            return creator.username if hasattr(creator, 'username') else str(creator)
                    else:
                        return str(creator)

        # Check for foreign key to User
        for field in obj._meta.get_fields():
            if field.is_relation and field.related_model:
                related_model_name = field.related_model._meta.model_name.lower()
                if 'user' in related_model_name:
                    try:
                        user = getattr(obj, field.name)
                        if user:
                            if hasattr(user, 'username'):
                                return user.username
                    except:
                        pass

        # Try to get from common methods
        if hasattr(obj, 'get_created_by'):
            try:
                creator = obj.get_created_by()
                if creator:
                    return str(creator)
            except:
                pass

        return 'Unknown'


class TextSearchFieldDisplayViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TextSearchFieldDisplay model"""
    queryset = TextSearchFieldDisplay.objects.filter(is_active=True)
    serializer_class = TextSearchFieldDisplaySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by model key if provided"""
        queryset = super().get_queryset()

        model_key = self.request.query_params.get('model', None)
        if model_key and model_key != 'all':
            # Get the model config for this key
            try:
                model_config = TextSearchModelConfig.objects.get(
                    key=model_key,
                    is_active=True
                )
                # Get search fields for this model
                search_fields = model_config.get_search_fields_list()
                if search_fields:
                    # Filter field displays to only include fields in this model
                    queryset = queryset.filter(field_name__in=search_fields)
            except TextSearchModelConfig.DoesNotExist:
                pass

        return queryset.order_by('order')


class TextSearchModelConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for TextSearchModelConfig model"""
    queryset = TextSearchModelConfig.objects.filter(is_active=True)
    serializer_class = TextSearchModelConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Order by order field"""
        return super().get_queryset().order_by('order')


class TextSearchFieldsByModelView(APIView):
    """API endpoint to get search fields for a specific model"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get search fields for a specific model"""
        model_key = request.query_params.get('model', 'all')
        logger.info(f'GET: Request Data: {request.GET}')

        if model_key == 'all':
            # Get all active field displays across all models
            field_displays = TextSearchFieldDisplay.objects.filter(
                is_active=True
            ).order_by('order')

            # Also get all model configs to show which fields belong to which models
            model_configs = TextSearchModelConfig.objects.filter(
                is_active=True
            ).order_by('order')

            return Response({
                'fields': TextSearchFieldDisplaySerializer(field_displays, many=True).data,
                'models': TextSearchModelConfigSerializer(model_configs, many=True).data,
                'model_key': 'all'
            })

        # Get specific model config
        try:
            model_config = TextSearchModelConfig.objects.get(
                key=model_key,
                is_active=True
            )

            # Get search fields for this model
            search_fields = model_config.get_search_fields_list()

            # Get field displays for these search fields
            field_displays = TextSearchFieldDisplay.objects.filter(
                field_name__in=search_fields,
                is_active=True
            ).order_by('order')

            return Response({
                'fields': TextSearchFieldDisplaySerializer(field_displays, many=True).data,
                'model': TextSearchModelConfigSerializer(model_config).data,
                'model_key': model_key
            })

        except TextSearchModelConfig.DoesNotExist:
            return Response({
                'fields': [],
                'model': None,
                'model_key': model_key,
                'error': f'Model config for {model_key} not found'
            }, status=status.HTTP_404_NOT_FOUND)


class TextSearchAvailableModelsView(APIView):
    """API endpoint to get all available models for search"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all available models for search"""
        model_configs = TextSearchModelConfig.objects.filter(
            is_active=True
        ).order_by('order')

        data = [
            {
                'key': config.key,
                'display_name': config.display_name,
                'search_fields_count': len(config.get_search_fields_list()),
                'order': config.order
            }
            for config in model_configs
        ]

        # Add 'all' option
        data.insert(0, {
            'key': 'all',
            'display_name': 'All Records',
            'search_fields_count': TextSearchFieldDisplay.objects.filter(is_active=True).count(),
            'order': 0
        })

        return Response(data)


# Add imports at the top of api.py
import zipfile
import tempfile
import os
import geopandas as gpd
from django.contrib.gis.geos import GEOSGeometry
import json
from shapely.geometry import shape as shapely_shape
import fiona
from fiona.io import ZipMemoryFile
import traceback
from django.core.files.base import ContentFile


class ShapefileUploadView(APIView):
    """API endpoint for uploading and processing shapefiles - accepts zip OR individual components"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Handle shapefile upload and processing - accepts zip file OR individual components"""
        try:
            # Validate request data
            serializer = ShapefileUploadSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid request', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            proposal_id = request.data.get('proposal_id')
            confirm_replace = request.data.get('confirm_replace', 'false').lower() == 'true'

            # Get proposal instance
            try:
                proposal = Proposal.objects.get(id=proposal_id)
            except Proposal.DoesNotExist:
                return Response(
                    {'error': f'Proposal with ID {proposal_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check permissions
            if not request.user.is_superuser and proposal.submitter != request.user.id:
                return Response(
                    {'error': 'You do not have permission to modify this proposal'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if there's an existing shapefile and confirmation is required
            existing_shapefile = proposal.shapefile_documents.last()
            if existing_shapefile and not confirm_replace:
                return Response({
                    'requires_confirmation': True,
                    'message': 'This will replace the existing shapefile and all processed data. Continue?',
                    'existing_filename': existing_shapefile.input_name
                }, status=status.HTTP_200_OK)

            # Determine if we're dealing with a zip file or individual components
            if 'shapefile' in request.FILES:
                # Legacy zip file upload
                shapefile = request.FILES['shapefile']
                if not shapefile.name.lower().endswith('.zip'):
                    return Response(
                        {'error': 'File must be a .zip file'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                result = self.process_shapefile_from_zip(shapefile)
            else:
                # Individual components upload
                result = self.process_shapefile_components(request.FILES)

            if not result['success']:
                return Response(
                    {'error': result['message'], 'details': result.get('errors', [])},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Delete existing shapefile if it exists
            if existing_shapefile:
                self.delete_existing_shapefile(proposal)

            # Save the new shapefile components
            self.save_shapefile_components(proposal, request.FILES, result)

            # Save GeoJSON to proposal
            proposal.shapefile_json = result['geojson']
            proposal.geojson_data_processed = None  # Clear processed data
            proposal.geojson_data_processed_iters = None
            proposal.save()

            # Serialize and return the updated proposal
            serializer = ProposalSerializer(proposal, context={'request': request})

            return Response({
                'success': True,
                'message': f'Shapefile processed successfully. {result["feature_count"]} features loaded.',
                'proposal': serializer.data,
                'feature_count': result['feature_count'],
                'warnings': result.get('warnings', [])
            })

        except Exception as e:
            logger.error(f"Error processing shapefile: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error processing shapefile: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def process_shapefile_components(self, files):
        """
        Process shapefile from individual component files
        """
        try:
            import tempfile
            import os
            import geopandas as gpd
            import json
            import shutil

            # Extract component files
            shp_file = None
            shx_file = None
            dbf_file = None
            prj_file = None

            for key, file_obj in files.items():
                if key.endswith('.shp') or key == 'shp':
                    shp_file = file_obj
                elif key.endswith('.shx') or key == 'shx':
                    shx_file = file_obj
                elif key.endswith('.dbf') or key == 'dbf':
                    dbf_file = file_obj
                elif key.endswith('.prj') or key == 'prj':
                    prj_file = file_obj

            if not shp_file:
                return {
                    'success': False,
                    'message': 'Missing .shp file',
                    'errors': ['No shapefile (.shp) found in upload'],
                    'feature_count': 0
                }

            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()

            try:
                # Base name from the shp file
                base_name = os.path.splitext(shp_file.name)[0]

                # Save all files
                shp_path = os.path.join(temp_dir, f"{base_name}.shp")
                with open(shp_path, 'wb') as f:
                    for chunk in shp_file.chunks():
                        f.write(chunk)

                if shx_file:
                    shx_path = os.path.join(temp_dir, f"{base_name}.shx")
                    with open(shx_path, 'wb') as f:
                        for chunk in shx_file.chunks():
                            f.write(chunk)

                if dbf_file:
                    dbf_path = os.path.join(temp_dir, f"{base_name}.dbf")
                    with open(dbf_path, 'wb') as f:
                        for chunk in dbf_file.chunks():
                            f.write(chunk)

                if prj_file:
                    prj_path = os.path.join(temp_dir, f"{base_name}.prj")
                    with open(prj_path, 'wb') as f:
                        for chunk in prj_file.chunks():
                            f.write(chunk)

                # Read the shapefile
                gdf = gpd.read_file(shp_path)

                # Process the GeoDataFrame
                return self._process_geodataframe(gdf)

            finally:
                # Clean up
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error processing shapefile components: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Error processing shapefile: {str(e)}',
                'errors': [str(e)],
                'feature_count': 0
            }

    def process_shapefile_from_zip(self, shapefile):
        """
        Process shapefile from a zip file (legacy support)
        """
        try:
            import tempfile
            import os
            import geopandas as gpd
            import json
            import zipfile
            import shutil

            # Save zip to temp file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                for chunk in shapefile.chunks():
                    tmp_file.write(chunk)
                zip_path = tmp_file.name

            # Create temp directory for extraction
            extract_dir = tempfile.mkdtemp()

            try:
                # Extract the zip
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Find the .shp file
                shp_files = []
                for file in os.listdir(extract_dir):
                    if file.lower().endswith('.shp'):
                        shp_files.append(os.path.join(extract_dir, file))

                if not shp_files:
                    return {
                        'success': False,
                        'message': 'No .shp file found in zip',
                        'errors': ['Zip file must contain a .shp file'],
                        'feature_count': 0
                    }

                # Read the shapefile
                gdf = gpd.read_file(shp_files[0])

                # Process the GeoDataFrame
                return self._process_geodataframe(gdf)

            finally:
                # Clean up
                try:
                    os.unlink(zip_path)
                except:
                    pass
                try:
                    shutil.rmtree(extract_dir)
                except:
                    pass

        except Exception as e:
            logger.error(f"Error processing shapefile from zip: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Error processing shapefile: {str(e)}',
                'errors': [str(e)],
                'feature_count': 0
            }

    def _process_geodataframe(self, gdf):
        """
        Common GeoDataFrame processing logic
        """
        import json
        import numpy as np
        from shapely.validation import make_valid

        if gdf.empty:
            return {
                'success': False,
                'message': 'Shapefile contains no features',
                'errors': ['No valid features found in shapefile'],
                'feature_count': 0
            }

        # Transform to system CRS if needed
        if hasattr(settings, 'CRS') and settings.CRS:
            try:
                gdf.to_crs(settings.CRS, inplace=True)
            except:
                logger.warning("Could not transform CRS, keeping original")

        # Store original CRS
        original_crs = gdf.crs
        logger.info(f"Original CRS: {original_crs}")

        # Log geometry types
        geom_types = gdf.geometry.type.value_counts()
        logger.info(f"Geometry types: {dict(geom_types)}")

        # Filter to polygon geometries
        polygon_mask = gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])
        if not polygon_mask.any():
            return {
                'success': False,
                'message': 'No Polygon or MultiPolygon geometries found',
                'errors': ['Shapefile contains no polygon geometries'],
                'feature_count': 0
            }

        gdf = gdf[polygon_mask].copy()

        # Validate geometries (minimal fixing)
        invalid_count = 0
        fixed_count = 0
        warnings = []

        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                invalid_count += 1
                continue

            if not geom.is_valid:
                try:
                    geom = make_valid(geom)
                    fixed_count += 1
                    gdf.at[idx, 'geometry'] = geom
                except:
                    invalid_count += 1

        # Remove any remaining invalid geometries
        gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.is_valid].copy()

        if gdf.empty:
            return {
                'success': False,
                'message': 'No valid geometries after processing',
                'errors': ['All geometries were invalid'],
                'feature_count': 0
            }

        # Add warnings
        if invalid_count > 0:
            warnings.append(f"Skipped {invalid_count} invalid geometries")
        if fixed_count > 0:
            warnings.append(f"Fixed {fixed_count} invalid geometries")

        # Convert to GeoJSON
        geojson_str = gdf.to_json()
        geojson = json.loads(geojson_str)

        # Add CRS info
        if original_crs:
            geojson['crs'] = {
                'type': 'name',
                'properties': {
                    'name': original_crs.to_string()
                }
            }

        return {
            'success': True,
            'message': 'Shapefile processed successfully',
            'feature_count': len(gdf),
            'geojson': geojson,
            'warnings': warnings
        }

    def save_shapefile_components(self, proposal, files, result):
        """
        Save shapefile components to the database
        """
        # If it's a zip upload, we need to save the zip file
        if 'shapefile' in files:
            shapefile = files['shapefile']
            shapefile.seek(0)
            ShapefileDocument.objects.create(
                proposal=proposal,
                _file=shapefile,
                name=f"Shapefile Upload - {shapefile.name}",
                input_name=shapefile.name,
                can_delete=True,
                can_hide=True,
                hidden=False
            )
        else:
            # Save individual components
            base_name = None
            for key, file_obj in files.items():
                if key.endswith('.shp') or key == 'shp':
                    base_name = os.path.splitext(file_obj.name)[0]
                    break

            if base_name:
                for key, file_obj in files.items():
                    file_obj.seek(0)
                    extension = os.path.splitext(file_obj.name)[1] or f".{key}"
                    doc_name = f"{base_name}{extension}"

                    ShapefileDocument.objects.create(
                        proposal=proposal,
                        _file=file_obj,
                        name=f"Shapefile Component - {doc_name}",
                        input_name=doc_name,
                        can_delete=True,
                        can_hide=True,
                        hidden=False
                    )

    def delete_existing_shapefile(self, proposal):
        """Delete existing shapefile documents and clear related fields"""
        try:
            existing_docs = ShapefileDocument.objects.filter(proposal=proposal)
            for doc in existing_docs:
                if doc._file:
                    doc._file.delete(save=False)
                doc.delete()
            logger.info(f"Deleted {existing_docs.count()} existing shapefile(s) for proposal {proposal.id}")
        except Exception as e:
            logger.error(f"Error deleting existing shapefile: {str(e)}")


class DeleteShapefileView(APIView):
    """API endpoint for deleting shapefile"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        """Delete shapefile for a proposal"""
        try:
            # Get proposal instance
            try:
                proposal = Proposal.objects.get(id=pk)
            except Proposal.DoesNotExist:
                return Response(
                    {'error': f'Proposal with ID {pk} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check permissions
            if not request.user.is_superuser and proposal.submitter != request.user.id:
                return Response(
                    {'error': 'You do not have permission to modify this proposal'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Delete shapefile documents
            shapefile_docs = ShapefileDocument.objects.filter(proposal=proposal)
            for doc in shapefile_docs:
                if doc._file:
                    doc._file.delete(save=False)
                doc.delete()

            # Clear proposal geometry fields
            proposal.shapefile_json = None
            proposal.geojson_data_hist = None
            proposal.geojson_data_processed = None
            proposal.geojson_data_processed_iters = None
            proposal.save()

            # Serialize and return the updated proposal
            serializer = ProposalSerializer(proposal, context={'request': request})

            return Response({
                'success': True,
                'message': 'Shapefile deleted successfully',
                'proposal': serializer.data
            })

        except Exception as e:
            logger.error(f"Error deleting shapefile: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error deleting shapefile: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MergePolygonView(APIView):
    """
    POST: Receive merged polygon GeoJSON and return it for inspection.
    Optional: save to a temporary table.
    """
    permission_classes = [IsAuthenticated]  # or whatever fits your project

    def post(self, request):
        data = request.data
        polygon_ids = data.get('polygon_ids', [])
        merged_geojson = data.get('merged_geojson')

        if not polygon_ids or len(polygon_ids) != 2:
            return Response({'error': 'Two polygon IDs required'}, status=status.HTTP_400_BAD_REQUEST)
        if not merged_geojson:
            return Response({'error': 'Missing merged_geojson'}, status=status.HTTP_400_BAD_REQUEST)

        # Optional: Validate that the GeoJSON is a valid geometry
        try:
            #geom = GEOSGeometry(json.dumps(merged_geojson))  # converts to GEOS
            geom = GEOSGeometry(json.dumps(merged_geojson['geometry']))

            shapely_geom = wkt.loads(geom.wkt)
            gdf = gpd.GeoDataFrame(geometry=[shapely_geom], crs='EPSG:4326')
            #gdf.to_crs(settings.CRS_GDA94)
            #plot_gdf(gdf.to_crs(settings.CRS_GDA94))

            #from silrec.utils.helper import polygons_to_gdf
            #plot_gdf(polygons_to_gdf(polygon_ids))
            #plot_gdf(polygons_to_gdf([458402, 424215]))
#

        except Exception as e:
            return Response({'error': f'Invalid geometry: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # If you want to save it to the database, create a model (see step 2)
        # merged = MergedPolygon.objects.create(
        #     polygon1_id=polygon_ids[0],
        #     polygon2_id=polygon_ids[1],
        #     merged_geometry=geom
        # )
        # return Response({'id': merged.id, 'geometry': merged_geojson})

        # For simple inspection, just return the geometry
        #import ipdb; ipdb.set_trace()
        return Response({
            'polygon_ids': polygon_ids,
            'merged_geojson': merged_geojson,
            'message': 'Merge received successfully'
        })


class SaveMergedGeometryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            proposal = Proposal.objects.get(id=pk)
        except Proposal.DoesNotExist:
            return Response({'error': 'Proposal not found'}, status=404)

        # Permission check
        if not request.user.is_superuser and proposal.submitter != request.user.id:
            return Response({'error': 'Permission denied'}, status=403)

        data = request.data
        updated_geojson = data.get('updated_geojson')
        original_ids = data.get('original_polygon_ids')
        merged_id = data.get('merged_polygon_id')

        if not updated_geojson:
            return Response({'error': 'Missing updated_geojson'}, status=400)

        # Save to proposal
        proposal.geojson_data_processed = updated_geojson
        proposal.save()

        # Optionally log the merge event (could store in another model)
        # For now, just return success

        # Serialize updated proposal
        serializer = ProposalSerializer(proposal, context={'request': request})
        return Response({'success': True, 'proposal': serializer.data})


class SaveCutGeometryView(APIView):
    """
    POST: Save cut geometry results to the proposal's geojson_data_processed field
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            proposal = Proposal.objects.get(id=pk)
        except Proposal.DoesNotExist:
            return Response({'error': 'Proposal not found'}, status=status.HTTP_404_NOT_FOUND)

        # Permission check
        if not request.user.is_superuser and proposal.submitter != request.user.id:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        updated_geojson = data.get('updated_geojson')
        original_polygon_ids = data.get('original_polygon_ids', [])
        new_polygon_ids = data.get('new_polygon_ids', [])
        cut_line = data.get('cut_line', [])

        if not updated_geojson:
            return Response({'error': 'Missing updated_geojson'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the GeoJSON
        try:
            # Optional: Validate geometry structure
            if not isinstance(updated_geojson, dict) or 'features' not in updated_geojson:
                return Response({'error': 'Invalid GeoJSON format'}, status=status.HTTP_400_BAD_REQUEST)

            # Save to proposal
            proposal.geojson_data_processed = updated_geojson
            proposal.save()

            # Log the cut operation (you can expand this to a separate log model if needed)
            logger.info(f"Cut operation saved for proposal {proposal.id}. "
                       f"Original polygons: {original_polygon_ids}, "
                       f"New polygons: {new_polygon_ids}")

            # Serialize updated proposal
            from silrec.components.proposals.serializers import ProposalSerializer
            serializer = ProposalSerializer(proposal, context={'request': request})

            return Response({
                'success': True,
                'message': 'Cut geometry saved successfully',
                'proposal': serializer.data,
                'original_polygon_ids': original_polygon_ids,
                'new_polygon_ids': new_polygon_ids
            })

        except Exception as e:
            logger.error(f"Error saving cut geometry: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error saving cut geometry: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProcessShapefileView(APIView):
    """API endpoint for processing an uploaded shapefile with sliver removal"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Handle shapefile processing request"""
        try:
            # Validate request data
            serializer = ShapefileProcessRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'error': 'Invalid request', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            threshold = serializer.validated_data['threshold']
            user_id = serializer.validated_data['user_id']
            proposal_id = serializer.validated_data['proposal_id']

            # Verify user matches authenticated user
            if request.user.id != user_id and not request.user.is_superuser:
                return Response(
                    {'error': 'User ID mismatch'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get proposal instance
            try:
                proposal = Proposal.objects.get(id=proposal_id)
            except Proposal.DoesNotExist:
                return Response(
                    {'error': f'Proposal with ID {proposal_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check permissions
            if not request.user.is_superuser and proposal.submitter != request.user.id:
                return Response(
                    {'error': 'You do not have permission to modify this proposal'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if shapefile exists
            if not proposal.shapefile_json:
                return Response(
                    {'error': 'No shapefile has been uploaded for this proposal'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process the shapefile with the given threshold
            result = self.process_shapefile_with_threshold(proposal, threshold, user_id)

            if not result['success']:
                return Response(
                    {'error': result['message'], 'details': result.get('errors', [])},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save the processed geometries to the proposal
#            proposal.geojson_data_processed = result['processed_geometries']
#            proposal.save()

            # Create a processing log entry (optional)
            logger.info(f"Shapefile processed for proposal {proposal_id} with threshold {threshold} by user {user_id}")

            # Serialize and return the updated proposal
            proposal_serializer = ProposalSerializer(proposal, context={'request': request})

            response_data = {
                'success': True,
                'message': f'Shapefile processed successfully with threshold {threshold}. {result["feature_count"]} features processed.',
                'proposal': proposal_serializer.data,
                'feature_count_orig': result['feature_count_orig'],
                'feature_count': result['feature_count'],
                #'processed_geometries': result['processed_geometries'],
                'warnings': result.get('warnings', [])
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error processing shapefile: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error processing shapefile: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def process_shapefile_with_threshold(self, proposal, threshold, user_id):
        """
        Process shapefile with sliver removal based on threshold
        Uses a single savepoint #0 for the entire run
        """
        try:
            import reversion
            from django.db import transaction, DatabaseError
            from silrec.components.proposals.models import ShapefileProcessingRun, SavepointRecord, AuditLog

            if not proposal.shapefile_json or not proposal.shapefile_json.get('features'):
                return {
                    'success': False,
                    'message': 'No valid features found in shapefile',
                    'errors': ['Shapefile contains no features']
                }

            # Start a transaction that will encompass everything
#            with transaction.atomic():
            if True:
                # Main logic to cookie-cut User provided shapefile geometries with silrec historical polygon
                ssm = ShapefileSliversMerger(proposal_id=proposal.id, threshold=threshold, user_id=user_id)

#                # Get total number of polygons to process
#                total_polygons = len(ssm.gdf_shpfile)
#
#                # Create the processing run record
#                processing_run = ShapefileProcessingRun.objects.create(
#                    proposal=proposal,
#                    user_id=user_id,
#                    threshold=threshold,
#                    total_polygons=total_polygons,
#                    status='running'
#                )
#
#                # Create a SINGLE savepoint #0 for the entire run
#                pre_run_savepoint = transaction.savepoint()
#                logger.info("Created pre-run savepoint #0")
#
#                # Create the savepoint record
#                pre_run_savepoint_record = SavepointRecord.objects.create(
#                    processing_run=processing_run,
#                    iteration=0,
#                    polygon_index=0,
#                    action='create',  # Will be updated to 'commit' on success
#                    affected_models={},
#                    metadata={
#                        'description': 'Pre-run initial state',
#                        'row_data': {},
#                        'is_marker': False  # This is a real savepoint
#                    }
#                )
#                logger.info("Created savepoint record for pre-run state (iteration 0)")

                try:
                    # Process all polygons - NO savepoint handler needed
                    list_state = ssm.create_gdf(savepoint_callback=None)  # Remove callback

                    # Link the request metrics to the processing run
#                    if ssm.request_metrics:
#                        processing_run.request_metrics = ssm.request_metrics
#                        processing_run.save()

                    # If we get here, all iterations succeeded
                    #import ipdb; ipdb.set_trace()
                    geom_data = ssm.set_proposal_data(list_state)

                    # Update proposal with results
                    proposal.geojson_data_processed = json.loads(
                        list_state[0]['GDF_RESULT_COMBINED'].to_crs(settings.CRS).to_json()
                    )
                    proposal.geojson_data_hist = json.loads(
                        list_state[0]['GDF_HIST'].to_crs(settings.CRS).to_json()
                    )
                    proposal.geojson_data_processed_iters = geom_data
                    proposal.save()

#                    # Get audit logs for this run
#                    audit_logs = AuditLog.objects.filter(
#                        request_metrics=ssm.request_metrics
#                    )

#                    # Count affected records per model
#                    affected_models = {}
#                    for log in audit_logs:
#                        model_name = log.table_name
#                        affected_models[model_name] = affected_models.get(model_name, 0) + 1
#
#                    # Update savepoint record with affected models
#                    pre_run_savepoint_record.affected_models = affected_models
#                    pre_run_savepoint_record.action = 'commit'
#                    pre_run_savepoint_record.metadata['committed_at'] = timezone.now().isoformat()
#                    pre_run_savepoint_record.save()
#
#                    # Link audit logs to savepoint
#                    if audit_logs.exists():
#                        pre_run_savepoint_record.audit_logs.set(audit_logs)

#                    # Update processing run progress
#                    processing_run.processed_polygons = len(ssm.gdf_shpfile)  # All succeeded
#                    processing_run.status = 'completed'
#                    processing_run.completed_at = timezone.now()
#                    processing_run.save()

#                    # Commit the pre-run savepoint
#                    transaction.savepoint_commit(pre_run_savepoint)

#                    logger.info(f"Processing completed: {affected_models}")

                except Exception as e:
                    # Something went wrong in processing
                    logger.error(f"Error during shapefile processing: {str(e)}")

#                    # Update savepoint record to 'rollback'
#                    pre_run_savepoint_record.action = 'rollback'
#                    pre_run_savepoint_record.metadata['rolled_back_at'] = timezone.now().isoformat()
#                    pre_run_savepoint_record.metadata['error'] = str(e)
#                    pre_run_savepoint_record.save()
#
#                    # Rollback the pre-run savepoint to revert all changes
#                    transaction.savepoint_rollback(pre_run_savepoint)
#                    logger.info("Rolled back pre-run savepoint - all changes reverted")
#
#                    # Mark processing run as failed
#                    processing_run.status = 'failed'
#                    processing_run.error_message = str(e)
#                    processing_run.completed_at = timezone.now()
#                    processing_run.failed_polygons = total_polygons
#                    processing_run.save()

                    # Re-raise to trigger transaction rollback
                    raise

            # If we get here, the transaction was committed
            warnings = []
            feature_count = len(proposal.geojson_data_processed['features'])
            feature_count_orig = len(proposal.shapefile_json['features'])

            warnings.append(f"Processed {feature_count} features with threshold {threshold}")

            return {
                'success': True,
                'message': 'Shapefile processed successfully',
                'feature_count_orig': feature_count_orig,
                'feature_count': feature_count,
                'warnings': warnings,
#                'processing_run_id': #processing_run.id
                'processing_run_id': 0
            }

        except DatabaseError as e:
            logger.error(f"Database error in process_shapefile_with_threshold: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Database error processing shapefile geometries',
                'errors': [str(e)]
            }
        except Exception as e:
            logger.error(f"Error in process_shapefile_with_threshold: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error processing shapefile geometries',
                'errors': [str(e)]
            }

class RevertShapefileProcessingView(APIView):
    """API endpoint for reverting shapefile processing changes using only django-reversion"""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Handle shapefile processing revert request"""
        try:
            # Validate request data
            user_id = request.data.get('user_id')
            proposal_id = request.data.get('proposal_id')

            if not user_id or not proposal_id:
                return Response(
                    {'error': 'Missing required parameters: user_id and proposal_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify user matches authenticated user
            if request.user.id != user_id and not request.user.is_superuser:
                return Response(
                    {'error': 'User ID mismatch'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get proposal instance
            try:
                proposal = Proposal.objects.get(id=proposal_id)
            except Proposal.DoesNotExist:
                return Response(
                    {'error': f'Proposal with ID {proposal_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check permissions
            if not request.user.is_superuser and proposal.submitter != request.user.id:
                return Response(
                    {'error': 'You do not have permission to modify this proposal'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Perform revert operation
            result = self.revert_shapefile_processing(proposal, user_id)

            if not result['success']:
                return Response(
                    {'error': result['message'], 'details': result.get('errors', [])},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Serialize and return the updated proposal
            proposal_serializer = ProposalSerializer(proposal, context={'request': request})

            response_data = {
                'success': True,
                'message': result['message'],
                'proposal': proposal_serializer.data,
                'records_removed': result.get('records_removed', 0),
                'warnings': result.get('warnings', [])
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error reverting shapefile processing: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error reverting shapefile processing: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def revert_shapefile_processing(self, proposal, user_id):
        """
        Revert shapefile processing changes using django-reversion
        """
        try:
            import reversion
            from django.db import transaction
            from reversion.models import Version
            from django.contrib.contenttypes.models import ContentType
            from silrec.components.forest_blocks.models import (
                Polygon, Cohort, AssignChtToPly, Treatment, TreatmentXtra
            )
            from django.db.models import Q

            records_removed = 0
            warnings = []

            # Get all versions for this proposal
            versions = Version.objects.get_for_object(proposal).order_by('-revision__date_created')

            logger.info(f"Found {versions.count()} versions for proposal {proposal.id}")

            if versions.count() <= 1:
                warnings.append('Not enough versions to revert - clearing processed fields only')
                with transaction.atomic():
                    proposal.geojson_data_processed = None
                    proposal.geojson_data_processed_iters = None
                    proposal.save()

                return {
                    'success': True,
                    'message': 'Cleared processed fields (no previous version found)',
                    'records_removed': 0,
                    'warnings': warnings
                }

            # Get the version right before the shapefile processing
            target_version = None
            for version in versions:
                if version.revision.comment and 'Shapefile processing' in version.revision.comment:
                    idx = list(versions).index(version)
                    if idx + 1 < len(versions):
                        target_version = versions[idx + 1]
                        break

            if not target_version:
                target_version = versions[1]

            target_timestamp = target_version.revision.date_created
            logger.info(f"Target version timestamp: {target_timestamp}")

            # CRITICAL FIX: Get original polygon IDs from the VERSION HISTORY, not from current shapefile_json
            # The version at target_timestamp contains the original state
            original_polygon_ids = []

            # Get all polygons that existed at target_timestamp
            # First, get the revision at target_timestamp
            target_revision = target_version.revision

            # Find all polygon versions in that revision
            polygon_versions = Version.objects.filter(
                content_type=ContentType.objects.get_for_model(Polygon),
                revision=target_revision
            )

            for pv in polygon_versions:
                # These are the polygons that existed before processing
                original_polygon_ids.append(int(pv.object_id))

            logger.info(f"Original polygon IDs from version history: {original_polygon_ids}")

            # Get all polygon IDs that exist NOW after processing
            current_polygon_ids = list(Polygon.objects.filter(
                proposal_id=proposal.id
            ).values_list('polygon_id', flat=True))

            logger.info(f"Current polygon IDs: {current_polygon_ids}")

            # NEW polygons are those in current but NOT in original
            new_polygon_ids = list(set(current_polygon_ids) - set(original_polygon_ids))
            logger.info(f"New polygon IDs to delete: {new_polygon_ids}")

            # UPDATED polygons are those in both sets
            updated_polygon_ids = list(set(current_polygon_ids) & set(original_polygon_ids))
            logger.info(f"Updated polygon IDs to revert: {updated_polygon_ids}")

            # Store counts before revert for logging
            before_counts = {
                'polygon': Polygon.objects.filter(proposal_id=proposal.id).count(),
                'cohort': Cohort.objects.filter(assignchttoply__polygon__proposal_id=proposal.id).distinct().count(),
                'assign_cht_to_ply': AssignChtToPly.objects.filter(polygon__proposal_id=proposal.id).count(),
                'treatment': Treatment.objects.filter(cohort__assignchttoply__polygon__proposal_id=proposal.id).distinct().count(),
            }
            logger.info(f"Before revert counts: {before_counts}")

            # Perform the revert
            with transaction.atomic():
                with reversion.create_revision():
                    # STEP 1: Handle NEW polygons (created during processing)
                    if new_polygon_ids:
                        logger.info(f"Processing {len(new_polygon_ids)} new polygons")

                        # Get assignments for new polygons
                        new_assignments = AssignChtToPly.objects.filter(
                            polygon_id__in=new_polygon_ids
                        )

                        # Get cohort IDs from these assignments
                        new_cohort_ids = list(new_assignments.values_list('cohort_id', flat=True).distinct())
                        logger.info(f"Cohorts linked to new polygons: {new_cohort_ids}")

                        # Get treatments linked to these cohorts and disconnect them
                        if new_cohort_ids:
                            affected_treatments = Treatment.objects.filter(cohort_id__in=new_cohort_ids)
                            if affected_treatments.exists():
                                treatment_count = affected_treatments.count()
                                logger.info(f"Disconnecting {treatment_count} treatments from new cohorts")
                                affected_treatments.update(cohort=None)

                        # Delete assignments for new polygons
                        assignment_count = new_assignments.count()
                        if assignment_count > 0:
                            new_assignments.delete()
                            records_removed += assignment_count
                            warnings.append(f"Deleted {assignment_count} assignments for new polygons")

                        # Delete new cohorts
                        if new_cohort_ids:
                            cohorts_to_delete = Cohort.objects.filter(cohort_id__in=new_cohort_ids)
                            cohort_count = cohorts_to_delete.count()
                            if cohort_count > 0:
                                cohorts_to_delete.delete()
                                records_removed += cohort_count
                                warnings.append(f"Deleted {cohort_count} new cohorts")

                        # Delete new polygons
                        polygons_to_delete = Polygon.objects.filter(polygon_id__in=new_polygon_ids)
                        polygon_count = polygons_to_delete.count()
                        if polygon_count > 0:
                            polygons_to_delete.delete()
                            records_removed += polygon_count
                            warnings.append(f"Deleted {polygon_count} new polygons")

                    # STEP 2: Handle UPDATED polygons (revert to pre-processing state)
                    if updated_polygon_ids:
                        logger.info(f"Processing {len(updated_polygon_ids)} updated polygons")

                        # Get all cohorts linked to these polygons
                        updated_cohort_ids = list(AssignChtToPly.objects.filter(
                            polygon_id__in=updated_polygon_ids,
                            status_current=True
                        ).values_list('cohort_id', flat=True).distinct())

                        # Revert each updated polygon to its state at target_timestamp
                        for polygon_id in updated_polygon_ids:
                            try:
                                polygon = Polygon.objects.get(polygon_id=polygon_id)
                                # Get the version of this polygon at target_timestamp
                                polygon_versions = Version.objects.get_for_object(polygon).filter(
                                    revision__date_created__lte=target_timestamp
                                ).order_by('-revision__date_created')

                                if polygon_versions.exists():
                                    # Store the field values from that version
                                    version_data = polygon_versions.first().field_dict

                                    # Update the polygon with the version data
                                    for field, value in version_data.items():
                                        if field != 'id' and hasattr(polygon, field):
                                            setattr(polygon, field, value)

                                    polygon.save()
                                    logger.info(f"Reverted polygon {polygon_id} to pre-processing state")
                                    records_removed += 1
                                else:
                                    logger.warning(f"No version found for polygon {polygon_id}")
                            except Polygon.DoesNotExist:
                                logger.warning(f"Polygon {polygon_id} not found")

                        # Revert each updated cohort
                        for cohort_id in updated_cohort_ids:
                            try:
                                cohort = Cohort.objects.get(cohort_id=cohort_id)
                                cohort_versions = Version.objects.get_for_object(cohort).filter(
                                    revision__date_created__lte=target_timestamp
                                ).order_by('-revision__date_created')

                                if cohort_versions.exists():
                                    # Store the field values from that version
                                    version_data = cohort_versions.first().field_dict

                                    # Update the cohort with the version data
                                    for field, value in version_data.items():
                                        if field != 'id' and hasattr(cohort, field):
                                            setattr(cohort, field, value)

                                    cohort.save()
                                    logger.info(f"Reverted cohort {cohort_id} to pre-processing state")
                                    records_removed += 1
                                else:
                                    logger.warning(f"No version found for cohort {cohort_id}")
                            except Cohort.DoesNotExist:
                                logger.warning(f"Cohort {cohort_id} not found")

                    # STEP 3: Now revert the proposal itself
                    target_version.revision.revert()
                    proposal.refresh_from_db()

                    # Ensure processed fields are cleared
                    proposal.geojson_data_processed = None
                    proposal.geojson_data_processed_iters = None
                    proposal.save()

                    reversion.set_comment(f'Reverted shapefile processing to state from {target_timestamp.strftime("%Y-%m-%d %H:%M:%S")}')

            # Get counts after revert
            after_counts = {
                'polygon': Polygon.objects.filter(proposal_id=proposal.id).count(),
                'cohort': Cohort.objects.filter(assignchttoply__polygon__proposal_id=proposal.id).distinct().count(),
                'assign_cht_to_ply': AssignChtToPly.objects.filter(polygon__proposal_id=proposal.id).count(),
                'treatment': Treatment.objects.filter(cohort__assignchttoply__polygon__proposal_id=proposal.id).distinct().count(),
            }
            logger.info(f"After revert counts: {after_counts}")

            # Calculate total records removed/changed
            total_changes = (
                (before_counts['polygon'] - after_counts['polygon']) +
                (before_counts['cohort'] - after_counts['cohort']) +
                (before_counts['assign_cht_to_ply'] - after_counts['assign_cht_to_ply']) +
                (before_counts['treatment'] - after_counts['treatment'])
            )

            logger.info(f"Revert completed: {records_removed} records affected")

            return {
                'success': True,
                'message': f'Successfully reverted to state from {target_timestamp.strftime("%Y-%m-%d %H:%M:%S")}',
                'records_removed': records_removed,
                'warnings': warnings,
                'before_counts': before_counts,
                'after_counts': after_counts,
                'details': {
                    'original_polygon_count': len(original_polygon_ids),
                    'new_polygon_count': len(new_polygon_ids),
                    'updated_polygon_count': len(updated_polygon_ids),
                    'new_polygons_deleted': new_polygon_ids,
                    'updated_polygons_reverted': updated_polygon_ids
                }
            }

        except Exception as e:
            logger.error(f"Error in revert_shapefile_processing: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error reverting shapefile processing',
                'errors': [str(e)]
            }


class SnapshotDebugView(APIView):
    """API endpoint for snapshot debugging and testing"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Handle GET requests - list snapshots or get snapshot details"""
        from silrec.utils.snapshot_utils import SnapshotManager

        sm = SnapshotManager()
        action = request.query_params.get('action', 'list')
        proposal_id = request.query_params.get('proposal_id')
        snapshot_id = request.query_params.get('snapshot_id')

        if action == 'list':
            # List all snapshots
            snapshots = sm.list_snapshots(
                proposal_id=int(proposal_id) if proposal_id else None
            )
            return Response({
                'success': True,
                'snapshots': snapshots
            })

        elif action == 'get' and snapshot_id:
            # Get specific snapshot
            snapshot = sm.get_snapshot(snapshot_id)
            if snapshot:
                return Response({
                    'success': True,
                    'snapshot': snapshot
                })
            else:
                return Response({
                    'success': False,
                    'error': f'Snapshot {snapshot_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)

        elif action == 'compare':
            # Compare two snapshots
            snapshot1_id = request.query_params.get('snapshot1')
            snapshot2_id = request.query_params.get('snapshot2')

            if not snapshot1_id or not snapshot2_id:
                return Response({
                    'success': False,
                    'error': 'Both snapshot1 and snapshot2 parameters are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            comparison = sm.compare_snapshots(snapshot1_id, snapshot2_id)
            return Response({
                'success': True,
                'comparison': comparison
            })

        return Response({
            'success': False,
            'error': 'Invalid action'
        }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        """Handle POST requests - create snapshots"""
        from silrec.utils.snapshot_utils import SnapshotManager

        sm = SnapshotManager()

        proposal_id = request.data.get('proposal_id')
        user_id = request.data.get('user_id')
        tag = request.data.get('tag', 'manual_snapshot')

        if not proposal_id or not user_id:
            return Response({
                'success': False,
                'error': 'proposal_id and user_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify user permissions
        if request.user.id != user_id and not request.user.is_superuser:
            return Response({
                'success': False,
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            snapshot = sm.create_snapshot(proposal_id, user_id, tag)

            return Response({
                'success': True,
                'message': f'Snapshot {snapshot["id"]} created successfully',
                'snapshot': {
                    'id': snapshot['id'],
                    'tag': snapshot['tag'],
                    'timestamp': snapshot['timestamp'],
                    'record_counts': snapshot['metadata']['record_counts']
                }
            })

        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': f'Error creating snapshot: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

