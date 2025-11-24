import traceback
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

#from rest_framework import viewsets, permissions


from rest_framework import viewsets, serializers, status, generics, views
#from rest_framework.decorators import detail_route, list_route,renderer_classes
from rest_framework.decorators import action
from rest_framework.decorators import action as detail_route
from rest_framework.decorators import action as list_route
from rest_framework.decorators import renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission, SAFE_METHODS
from rest_framework.pagination import PageNumberPagination
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend

from datetime import datetime, timedelta, date

from silrec.helpers import is_customer, is_internal

from silrec.components.forest_blocks.models import   (
    Polygon,
    Cohort,
    Treatment,
    TreatmentXtra,
    AssignChtToPly,
    Prescription,
    SilviculturistComment,
)
from silrec.components.users.serializers import   (
    UserSerializer,
    UserSerializerSimple,
)
from silrec.components.forest_blocks.serializers import   (
    TreatmentSerializer,
    TreatmentXtraSerializer,
    CohortSerializer,
    PrescriptionSerializer,
    SilviculturistCommentSerializer,
    SimpleCohortSerializer,
    PolygonSerializer,
    Polygon2Serializer,
    PolygonCohortSerializer,
    PolygonGeometrySerializer,
    PolygonCohortDataSerializer,
)

#from .models import Cohort, Treatment, TreatmentXtra
#from .serializers import CohortSerializer, TreatmentSerializer, TreatmentXtraSerializer

class GetProfile(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        serializer  = UserSerializer(request.user,
                context={'request': request}
                )
        return Response(serializer.data)


class PolygonCohortViewSet(viewsets.ModelViewSet):
    queryset = AssignChtToPly.objects.none()
    serializer_class = PolygonCohortSerializer

    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        return AssignChtToPly.objects.all() #[:5]

    def list(self, request, *args, **kwargs):
        """ http://localhost:8001/api/polygoncohorts.json
        """
        serializer = PolygonCohortSerializer(self.get_queryset()[:5], many=True)
        return Response(serializer.data)

class PolygonViewSet(viewsets.ModelViewSet):
    queryset = Polygon.objects.none()
    serializer_class = PolygonSerializer

    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        return Polygon.objects.all() #[:5]

    def list(self, request, *args, **kwargs):
        """ http://localhost:8001/api/polygon.json
        """
        serializer = PolygonSerializer(self.get_queryset()[:5], many=True)
        return Response(serializer.data)


class Polygon2ViewSet(viewsets.ModelViewSet):
    queryset = Polygon.objects.none()
    serializer_class = Polygon2Serializer

    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        return Polygon.objects.all() #[:5]

#    def list(self, request, *args, **kwargs):
#        """ http://localhost:8001/api/polygon.json
#        """
#        serializer = Polygon2Serializer(self.get_queryset()[:5], many=True)
#        import ipdb; ipdb.set_trace()
#
#        return Response(serializer.data)


class PolygonGeometryViewSet(viewsets.ModelViewSet):
    queryset = Polygon.objects.none()
    serializer_class = PolygonGeometrySerializer

    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        return Polygon.objects.all() #[:5]

#    def list(self, request, *args, **kwargs):
#        """ http://localhost:8001/api/polygon.json
#        """
#        serializer = PolygonGeometrySerializer(self.get_queryset()[:5], many=True)
#        import ipdb; ipdb.set_trace()
#
#        return Response(serializer.data)



class PolygonPaginatedViewSet(viewsets.ModelViewSet):
    filter_backends = (DatatablesFilterBackend,)
    #filter_backends = (ProposalFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    #renderer_classes = (ProposalRenderer,)
    #queryset = Polygon.objects.none()
    queryset = Polygon.objects.filter(polygon_id__lt=392915)
    #serializer_class = ListProposalSerializer
    serializer_class = Polygon2Serializer
    search_fields = ['polygon_id',]
    #serializer_class = DTProposalSerializer
    page_size = 10

    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        #return Polygon.objects.all() #[:5]
        #return Polygon.objects.all()[:25]
        return Polygon.objects.filter(polygon_id__lt=392915)

    #@list_route(methods=['GET', ])
#    @action(detail=False, methods=['GET'])
#    @list_route(
#        methods=[
#            "GET",
#        ],
#        detail=False,
#    )
    @list_route(detail=False, methods=['GET', ])
    def ply_datatable_list(self, request, *args, **kwargs):
        """ http://localhost:8001/api/ply_paginated/ply_datatable_list/?format=datatables&draw=1&length=10
        """
        #self.serializer_class = DTSpatialQueryLayersUsedSerializer
        self.serializer_class = Polygon2Serializer
        #queryset = self.get_queryset().filter(layer_data__isnull=False, processing_status=Proposal.PROCESSING_STATUS_APPROVED)
        queryset = self.get_queryset().filter()

        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        # self.paginator.page_size = 0
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = Polygon2Serializer(
            result_page, context={'request': request}, many=True
        )
        data = serializer.data

        response = self.paginator.get_paginated_response(data)
        return response

    #@list_route(methods=['GET',])
    @list_route(detail=False, methods=['GET', ])
    def list_paginated(self, request, *args, **kwargs):
        """
        http://localhost:8001/api/ply_paginated/list_paginated/?format=datatables&draw=1&length=10
        """
        #import ipdb; ipdb.set_trace()
        proposals = self.get_queryset()
        paginator = PageNumberPagination()
        #paginator = LimitOffsetPagination()
        paginator.page_size = 2
        result_page = paginator.paginate_queryset(proposals, request)
        serializer = Polygon2Serializer(result_page, context={'request':request}, many=True)
        return paginator.get_paginated_response(serializer.data)


from silrec.components.forest_blocks.models import Polygon, AssignChtToPly, Cohort
class DebugPolygonRelationsView(views.APIView):
    ''' Check relation names
        http://localhost:8001/api/debug-polygon-relations/
    '''

    def get(self, request):
        from django.db.models.fields.related import ForeignObjectRel
        from silrec.components.forest_blocks.models import Polygon

        polygon = Polygon.objects.first()
        if polygon:
            # Get all related fields
            related_objects = [
                f for f in polygon._meta.get_fields()
                if (f.one_to_many or f.one_to_one) and f.auto_created
            ]

            relations_info = []
            for rel in related_objects:
                relations_info.append({
                    'name': rel.get_accessor_name(),
                    'related_model': rel.related_model.__name__,
                    'field_name': rel.field.name if hasattr(rel, 'field') else 'N/A'
                })

            return Response({
                'polygon_id': polygon.polygon_id,
                'related_fields': relations_info
            })
        return Response({'error': 'No Polygon objects found'})


class DatatablesPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'length'
    page_query_param = 'page'
    max_page_size = 1000
    page_size = 10

    def get_page_number(self, request, paginator):
        # Calculate page number from DataTables 'start' parameter
        start = request.query_params.get('start')
        length = request.query_params.get('length', self.page_size)

        if start and length:
            try:
                start = int(start)
                length = int(length)
                if length > 0:
                    page_number = (start // length) + 1
                    return max(1, page_number)
            except (ValueError, TypeError):
                pass

        # Fallback to default page number
        return super().get_page_number(request, paginator)

    def get_paginated_response(self, data):
        # Get datatables parameters
        draw = int(self.request.query_params.get('draw', 1))

        # Get counts
        total_count = getattr(self.request, '_datatables_total_count', self.page.paginator.count)
        filtered_count = getattr(self.request, '_datatables_filtered_count', self.page.paginator.count)

        return Response({
            'draw': draw,
            'recordsTotal': total_count,
            'recordsFiltered': filtered_count,
            'data': data
        })


class DatatablesFilterBackend(DatatablesFilterBackend):
    """
    Custom filter backend for datatables
    """
    def filter_queryset(self, request, queryset, view):
        total_count = queryset.count()

        # Apply your custom filters here
        filter_polygon_name = request.query_params.get('filter_polygon_name', '')
        filter_species = request.query_params.get('filter_species', '')
        filter_min_area = request.query_params.get('filter_min_area', '')
        filter_cohort_status = request.query_params.get('filter_cohort_status', 'all')

        if filter_polygon_name:
            queryset = queryset.filter(name__icontains=filter_polygon_name)

        if filter_min_area:
            try:
                min_area = float(filter_min_area)
                queryset = queryset.filter(area_ha__gte=min_area)
            except ValueError:
                pass

        if filter_species:
            queryset = queryset.filter(
                assignchttoply__cohort__species__icontains=filter_species,
                assignchttoply__status_current=True
            ).distinct()

        if filter_cohort_status != 'all':
            status_active = filter_cohort_status == 'active'
            queryset = queryset.filter(
                assignchttoply__status_current=status_active
            ).distinct()

        filtered_count = queryset.count()

        setattr(view, '_datatables_total_count', total_count)
        setattr(view, '_datatables_filtered_count', filtered_count)

        return queryset

class PolygonCohortTableViewSet(viewsets.ModelViewSet):
    queryset = Polygon.objects.none()
    serializer_class = PolygonCohortDataSerializer
    pagination_class = DatatablesPageNumberPagination
    filter_backends = (DatatablesFilterBackend,)  # Use custom filter backend
    #page_size = 2

    def get_queryset(self):
        proposal_id = self.request.query_params.get('proposal_id')
        if proposal_id:
            return Polygon.objects.filter(
                proposal_id=proposal_id
            ).prefetch_related(
                'assignchttoply_set',
                'assignchttoply_set__cohort'
            )
        return Polygon.objects.none()

#    def _list(self, request, *args, **kwargs):
#        """
#        http://localhost:8001/api/ply_paginated/list_paginated/?format=datatables&draw=1&length=10
#        http://localhost:8001/api/polygon_cohort_table/?fmt=datatables&draw=3&length=10
#        """
#        #import ipdb; ipdb.set_trace()
#        polygons = self.get_queryset()
#        paginator = PageNumberPagination()
#        #paginator = LimitOffsetPagination()
#        paginator.page_size = 2
#        result_page = paginator.paginate_queryset(polygons, request)
#        serializer = PolygonCohortDataSerializer(result_page, context={'request':request}, many=True)
#        return paginator.get_paginated_response(serializer.data)

class IsOfficer(BasePermission):
    def has_permission(self, request, view):
        #return request.user.groups.filter(name='Officers').exists()
        return True

class IsAssessor(BasePermission):
    def has_permission(self, request, view):
        #return request.user.groups.filter(name='Assessors').exists()
        return True

class IsReviewer(BasePermission):
    def has_permission(self, request, view):
        #return request.user.groups.filter(name='Reviewers').exists()
        return True

class IsSilrecAdmin(BasePermission):
    def has_permission(self, request, view):
        #return request.user.groups.filter(name='Silrec Admin').exists()
        return True

class ReadOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        return True
#        if request.method in SAFE_METHODS:
#            return True
#        return False

class CohortViewSet(viewsets.ModelViewSet):
    queryset = Cohort.objects.all()
    serializer_class = CohortSerializer

#    def get_queryset(self):
#        #import ipdb; ipdb.set_trace()
#        print(self.request.query_params)
#        pass

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated & (IsAssessor | IsReviewer | IsSilrecAdmin)]
        return [permission() for permission in permission_classes]


class TreatmentDatatablesFilterBackend(DatatablesFilterBackend):
    """
    Custom filter backend for datatables treatment filtering
    """
    def filter_queryset(self, request, queryset, view):
        # Get total count before filtering
        total_count = queryset.count()

        # Apply custom filters for treatments
        filter_task = request.query_params.get('filter_task', '')
        filter_status = request.query_params.get('filter_status', 'all')
        filter_plan_year = request.query_params.get('filter_plan_year', '')
        filter_plan_month = request.query_params.get('filter_plan_month', 'all')
        filter_complete_date_from = request.query_params.get('filter_complete_date_from', '')
        filter_complete_date_to = request.query_params.get('filter_complete_date_to', '')
        filter_machine = request.query_params.get('filter_machine', '')
        filter_operator = request.query_params.get('filter_operator', '')

        # Filter by task
        if filter_task:
            queryset = queryset.filter(task__task=filter_task)

        # Filter by status
        if filter_status != 'all':
            queryset = queryset.filter(status=filter_status)

        # Filter by planned year
        if filter_plan_year:
            try:
                plan_year = int(filter_plan_year)
                queryset = queryset.filter(plan_yr=plan_year)
            except ValueError:
                pass

        # Filter by planned month
        if filter_plan_month != 'all':
            try:
                plan_month = int(filter_plan_month)
                queryset = queryset.filter(plan_mth=plan_month)
            except ValueError:
                pass

        # Filter by complete date range
        if filter_complete_date_from:
            try:
                complete_date_from = datetime.strptime(filter_complete_date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(complete_date__gte=complete_date_from)
            except ValueError:
                pass

        if filter_complete_date_to:
            try:
                complete_date_to = datetime.strptime(filter_complete_date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(complete_date__lte=complete_date_to)
            except ValueError:
                pass

        # Filter by machine (from TreatmentXtra)
        if filter_machine:
            queryset = queryset.filter(
                treatmentxtra__zmachine_id__icontains=filter_machine
            ).distinct()

        # Filter by operator
        if filter_operator:
            queryset = queryset.filter(
                changed_by__icontains=filter_operator
            )

        filtered_count = queryset.count()

        # Set counts on the request for the paginator to use
        setattr(request, '_datatables_total_count', total_count)
        setattr(request, '_datatables_filtered_count', filtered_count)

        return queryset


class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    pagination_class = DatatablesPageNumberPagination
    filter_backends = (TreatmentDatatablesFilterBackend,)

    def get_queryset(self):
        # Start with a properly ordered queryset
        queryset = Treatment.objects.all().select_related('task', 'cohort').order_by('treatment_id')

        # Handle cohort filtering
        cohort_id = self.request.query_params.get('cohort_id')
        if cohort_id:
            queryset = queryset.filter(cohort_id=cohort_id)

        return queryset

    def list(self, request, *args, **kwargs):
        # Always use datatables format for list requests
        return self.datatables_list(request, *args, **kwargs)

    def datatables_list(self, request, *args, **kwargs):
        """Custom list method for datatables format"""
        queryset = self.filter_queryset(self.get_queryset())

        # Apply ordering from DataTables if provided
        ordering = self.get_ordering(request, queryset)
        if ordering:
            queryset = queryset.order_by(*ordering)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_ordering(self, request, queryset):
        """Extract ordering from DataTables request"""
        order_column_index = request.query_params.get('order[0][column]')
        order_direction = request.query_params.get('order[0][dir]', 'asc')

        if order_column_index is not None:
            # Map DataTables column index to model field
            column_map = {
                '0': 'treatment_id',  # ID column
                '1': 'task__name',     # Task column
                '2': 'plan_yr',        # Planned Year column
                '3': 'plan_mth',       # Planned Month column
                '4': 'status',         # Status column
                '5': 'complete_date',  # Complete Date column
            }

            field_name = column_map.get(order_column_index)
            if field_name:
                if order_direction == 'desc':
                    field_name = '-' + field_name
                return [field_name]

        # Default ordering if none specified
        return ['treatment_id']

    def get_permissions(self):
        print(f"TreatmentViewSet - Action: {self.action}")
        print(f"TreatmentViewSet - User: {self.request.user}")

        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated & (IsAssessor | IsReviewer | IsSilrecAdmin)]

        return [permission() for permission in permission_classes]


class TreatmentXtraViewSet(viewsets.ModelViewSet):
    queryset = TreatmentXtra.objects.all()
    serializer_class = TreatmentXtraSerializer

#    def get_permissions(self):
#        import ipdb; ipdb.set_trace()
#        if self.action in ['list', 'retrieve', 'update', 'partial_update']:
#            permission_classes = [IsAuthenticated]
#        else:
#            permission_classes = [IsAuthenticated & (IsAssessor | IsReviewer | IsSilrecAdmin)]
#        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = TreatmentXtra.objects.all()
        treatment_id = self.request.query_params.get('treatment_id')
        if treatment_id:
            queryset = queryset.filter(treatment_id=treatment_id)
        return queryset


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated & (IsAssessor | IsReviewer | IsSilrecAdmin)]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = Prescription.objects.all()
        #prescription_id = self.request.query_params.get('prescription_id')
        prescription_id = self.request.query_params.get('prescription')
        if prescription_id:
            queryset = queryset.filter(prescription_id=prescription_id)
        return queryset


class SilviculturistCommentViewSet(viewsets.ModelViewSet):
    queryset = SilviculturistComment.objects.all()
    serializer_class = SilviculturistCommentSerializer

    def get_queryset(self):
        queryset = SilviculturistComment.objects.all()
        treatment_id = self.request.query_params.get('treatment')
        if treatment_id:
            queryset = queryset.filter(treatment_id=treatment_id)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated & (IsAssessor | IsReviewer | IsSilrecAdmin)]
        return [permission() for permission in permission_classes]
