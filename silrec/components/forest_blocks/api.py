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


