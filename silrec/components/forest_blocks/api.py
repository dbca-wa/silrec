import traceback
import geojson
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from rest_framework import viewsets, serializers, status, generics, views
#from rest_framework.decorators import detail_route, list_route,renderer_classes
from rest_framework.decorators import action
from rest_framework.decorators import action as detail_route
from rest_framework.decorators import action as list_route
from rest_framework.decorators import renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission
from rest_framework.pagination import PageNumberPagination
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from datetime import datetime, timedelta, date

from silrec.helpers import is_customer, is_internal

from silrec.components.forest_blocks.models import   (   
    Polygon,
    Cohort,
    Treatment,
    AssignChtToPly,
)
from silrec.components.users.serializers import   (   
    UserSerializer,
    UserSerializerSimple,
)
from silrec.components.forest_blocks.serializers import   (   
    TreatmentSerializer,
    CohortSerializer,
    SimpleCohortSerializer,
    PolygonSerializer,
    Polygon2Serializer,
    PolygonCohortSerializer,
)


class GetProfile(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        serializer  = UserSerializer(request.user,
                context={'request': request}
                )
        return Response(serializer.data)


class CohortViewSet(viewsets.ModelViewSet):
    queryset = Cohort.objects.none()
    serializer_class = CohortSerializer

    def get_queryset(self):
        import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return Cohort.objects.all()
        elif is_customer(self.request):
            qs = Cohort.objects.filter(Q(id=user.id))
            return qs
        return Cohort.objects.none()

    def list(self, request, *args, **kwargs):            
        """ http://localhost:8001/api/cohorts.json
        """
        #qs = Cohort.objects.filter().order_by('cohort_id')[:5]
        qs = self.get_queryset().order_by('cohort_id')[:5]
        return Response(qs.values('cohort_id', 'obj_code', 'op_id', 'op_date', 'pct_area'))

    @action(detail=True, methods=['GET'])
    def get_cohort(self, request, *args, **kwargs):
        """ http://localhost:8001/api/cohorts/116011/get_cohort/
        """
        try:
            #import ipdb; ipdb.set_trace()
            #instance = self.get_object()
            cohort_id = self.kwargs['pk']
            instance = Cohort.objects.get(cohort_id=cohort_id)

            serializer = CohortSerializer(instance, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['GET'])
    def get_simple_cohort(self, request, *args, **kwargs):
        """ http://localhost:8001/api/cohorts/116011/get_simple_cohort/
        """
        try:
            import ipdb; ipdb.set_trace()
            #instance = self.get_object()
            cohort_id = self.kwargs['pk']
            instance = Cohort.objects.filter(cohort_id=cohort_id)

            serializer = SimpleCohortSerializer(instance, many=True, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


    @action(detail=True, methods=['GET'])
    def custom(self, request, *args, **kwargs):
        '''
        http://localhost:8001/api/users/1/custom/
        '''
        import ipdb; ipdb.set_trace()
        obj = self.get_object()
        return Response(CohortSerializer(obj, context={'request': request}).data)
        #return Response(self.queryset.values('id', 'first_name', 'last_name', 'email'))
#        serializer  = UserSerializer(request.user,
#                context={'request': request}
#                )
#        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def get_department_users(self, request, *args, **kwargs):
        try:
            search_term = request.GET.get('term', '')
            #serializer = UserSerializer(
            #        staff,
            #        many=True
            #        )
            #return Response(serializer.data)
            data = self.get_queryset().filter(is_staff=True). \
                filter(Q(first_name__icontains=search_term) | Q(last_name__icontains=search_term)). \
                values('email', 'first_name', 'last_name')[:10]
            data_transform = [{'id': person['email'], 'text': person['first_name'] + ' ' + person['last_name']} for person in data]
            return Response({"results": data_transform})
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.none()
    serializer_class = TreatmentSerializer

    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return Cohort.objects.all()
        elif is_customer(self.request):
            qs = Cohort.objects.filter(Q(id=user.id))
            return qs
        return Cohort.objects.none()

    def list(self, request, *args, **kwargs):            
        """ http://localhost:8001/api/cohorts.json
        """
        #qs = Cohort.objects.filter().order_by('cohort_id')[:5]
        qs = self.get_queryset().order_by('cohort_id')[:5]
        return Response(qs.values('cohort_id', 'obj_code', 'op_id', 'op_date', 'pct_area'))

    @action(detail=True, methods=['GET'])
    def get_treatment(self, request, *args, **kwargs):
        """ http://localhost:8001/api/treatment/116011/get_treatment/
        """
        try:
            import ipdb; ipdb.set_trace()
            #instance = self.get_object()
            cohort_id = self.kwargs['pk']
            qs = Treatment.objects.filter(cohort_id=cohort_id)

            serializer = TreatmentSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

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

    def list(self, request, *args, **kwargs):            
        """ http://localhost:8001/api/polygon.json
        """
        serializer = Polygon2Serializer(self.get_queryset()[:5], many=True)
        import ipdb; ipdb.set_trace()

        return Response(serializer.data)


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


