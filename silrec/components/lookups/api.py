import traceback
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User

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

from silrec.components.users.serializers import   (   
    UserSerializer,
    UserSerializerSimple,
)
#from disturbance.helpers import is_customer, is_internal


class GetProfile(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        serializer  = UserSerializer(request.user,
                context={'request': request}
                )
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializerSimple

    def get_queryset(self):
        #import ipdb; ipdb.set_trace()
        user = self.request.user
        if is_internal(self.request):
            return User.objects.all()
        elif is_customer(self.request):
            qs = User.objects.filter(Q(id=user.id))
            return qs
        return EmailUser.objects.none()

    def list(self, request, *args, **kwargs):            
        """ http://localhost:8001/api/users/
        """
        qs = User.objects.filter().order_by('id')[:5]
        return Response(qs.values('id', 'first_name', 'last_name', 'email'))

    @action(detail=True, methods=['GET'])
    def custom(self, request, *args, **kwargs):
        '''
        http://localhost:8001/api/users/1/custom/
        '''
        obj = self.get_object()
        return Response(UserSerializer(obj, context={'request': request}).data)
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


