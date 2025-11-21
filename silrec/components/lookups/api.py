#import traceback
#from django.db.models import Q, Min
#from django.db import transaction
#from django.http import HttpResponse
#from django.conf import settings
#from django.contrib import messages
#from django.views.decorators.csrf import csrf_exempt
#from django.utils import timezone
from django.contrib.auth.models import User
#
#from rest_framework import viewsets, serializers, status, generics, views
##from rest_framework.decorators import detail_route, list_route,renderer_classes
#from rest_framework.decorators import action
#from rest_framework.decorators import action as detail_route
#from rest_framework.decorators import action as list_route
#from rest_framework.decorators import renderer_classes
#from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
#from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission
#from rest_framework.pagination import PageNumberPagination
#from datetime import datetime, timedelta, date

from silrec.helpers import is_customer, is_internal

#from disturbance.helpers import is_customer, is_internal

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from silrec.components.users.serializers import   (
    UserSerializer,
    UserSerializerSimple,
)
from silrec.components.lookups.models import (
    CohortMetricsLkp,
    MachineLkp,
    ObjectiveLkp,
    OrganisationLkp,
    RegenerationMethodsLkp,
    RescheduleReasonsLkp,
    SpatialPrecisionLkp,
    SpeciesApiLkp,
    TaskLkp,
    TasksAttLkp,
    TreatmentStatusLkp,
)
from silrec.components.lookups.serializers import (
    CohortMetricsLkpSerializer,
    MachineLkpSerializer,
    ObjectiveLkpSerializer,
    OrganisationLkpSerializer,
    RegenerationMethodsLkpSerializer,
    RescheduleReasonsLkpSerializer,
    SpatialPrecisionLkpSerializer,
    SpeciesApiLkpSerializer,
    TaskLkpSerializer,
    TasksAttLkpSerializer,
    TreatmentStatusLkpSerializer,
    ObjectiveLkpDetailSerializer,
    TaskLkpDetailSerializer,
    CombinedLkpSerializer,
)



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



class CohortMetricsLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Cohort Metrics Lookup
    Provides success measures and metrics for cohorts
    """
    queryset = CohortMetricsLkp.objects.filter(effective_to__isnull=True)
    serializer_class = CohortMetricsLkpSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['rating', 'version']
    search_fields = ['name', 'definition', 'value', 'method']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by rating type if provided
        rating = self.request.query_params.get('rating_type')
        if rating is not None:
            if rating.lower() == 'true':
                queryset = queryset.filter(rating=True)
            elif rating.lower() == 'false':
                queryset = queryset.filter(rating=False)

        return queryset.order_by('name')

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active cohort metrics"""
        active_metrics = self.get_queryset().filter(effective_to__isnull=True)
        serializer = self.get_serializer(active_metrics, many=True)
        return Response(serializer.data)


class MachineLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Machine Lookup
    Provides machine types and specifications for thinning/coppice control
    """
    queryset = MachineLkp.objects.all()
    serializer_class = MachineLkpSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['machine_type', 'felling_head_herbicide_spray']
    search_fields = ['manufacturer', 'model', 'machine_type', 'felling_head_model']

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get machines grouped by type"""
        machine_types = MachineLkp.objects.values_list('machine_type', flat=True).distinct()
        result = {}

        for machine_type in machine_types:
            if machine_type:
                machines = MachineLkp.objects.filter(machine_type=machine_type)
                serializer = self.get_serializer(machines, many=True)
                result[machine_type] = serializer.data

        return Response(result)


class ObjectiveLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Objective Lookup
    Provides silvicultural and management objectives
    """
    queryset = ObjectiveLkp.objects.filter(effective_to__isnull=True)
    serializer_class = ObjectiveLkpSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['cut', 'forest_type', 'prescription', 'resid_ba_ge15']
    search_fields = ['obj_code', 'description', 'definition', 'fmis_code']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ObjectiveLkpDetailSerializer
        return ObjectiveLkpSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by forest type if provided
        forest_type = self.request.query_params.get('forest_type')
        if forest_type:
            queryset = queryset.filter(forest_type=forest_type)

        # Filter by cut type if provided
        cut_type = self.request.query_params.get('cut_type')
        if cut_type:
            queryset = queryset.filter(cut=cut_type)

        return queryset.order_by('obj_code')

    @action(detail=False, methods=['get'])
    def with_prescriptions(self, request):
        """Get objectives that have prescriptions

           http://localhost:8001/api/lookups/objectives/with_prescriptions/
        """
        objectives = self.get_queryset().filter(prescription=True)
        serializer = self.get_serializer(objectives, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_forest_type(self, request):
        """Get objectives grouped by forest type

           http://localhost:8001/api/lookups/objectives/by_forest_type/
        """
        forest_types = ObjectiveLkp.objects.values_list('forest_type', flat=True).distinct()
        result = {}

        for forest_type in forest_types:
            if forest_type:
                objectives = ObjectiveLkp.objects.filter(forest_type=forest_type, effective_to__isnull=True)
                serializer = self.get_serializer(objectives, many=True)
                result[forest_type] = serializer.data

        return Response(result)


class OrganisationLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Organisation Lookup
    Provides organisation codes and descriptions
    """
    queryset = OrganisationLkp.objects.all()
    serializer_class = OrganisationLkpSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['organisation', 'description']


class RegenerationMethodsLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Regeneration Methods Lookup
    Provides regeneration method codes and descriptions matching FMIS
    """
    queryset = RegenerationMethodsLkp.objects.all()
    serializer_class = RegenerationMethodsLkpSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['regen_method', 'description']


class RescheduleReasonsLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Reschedule Reasons Lookup
    Provides standard reasons for rescheduling treatments
    """
    queryset = RescheduleReasonsLkp.objects.all()
    serializer_class = RescheduleReasonsLkpSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['rescheduled_reason', 'description']


class SpatialPrecisionLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Spatial Precision Lookup
    Provides mapping precision codes and descriptions
    """
    queryset = SpatialPrecisionLkp.objects.all()
    serializer_class = SpatialPrecisionLkpSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['precision_code', 'resolution', 'description']


class SpeciesApiLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Species API Lookup
    Provides API species codes and descriptions for forest types
    """
    queryset = SpeciesApiLkp.objects.all()
    serializer_class = SpeciesApiLkpSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['species', 'short_description', 'full_description', 'fmismiscode_species', 'fmisdescription_type']

    @action(detail=False, methods=['get'])
    def by_fmis_type(self, request):
        """Get species grouped by FMIS type"""
        fmis_types = SpeciesApiLkp.objects.values_list('fmismiscode_type', flat=True).distinct()
        result = {}

        for fmis_type in fmis_types:
            if fmis_type:
                species = SpeciesApiLkp.objects.filter(fmis_code_type=fmis_type)
                serializer = self.get_serializer(species, many=True)
                result[fmis_type] = serializer.data

        return Response(result)


class TaskLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Task Lookup
    Provides task codes, definitions and specifications
    """
    queryset = TaskLkp.objects.filter(effective_to__isnull=True)
    serializer_class = TaskLkpSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['forest_type', 'regen_init', 'addition_attribs', 'zavailable']
    search_fields = ['task', 'task_name', 'definition', 'financial_activity']
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TaskLkpDetailSerializer
        return TaskLkpSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by forest type if provided
        forest_type = self.request.query_params.get('forest_type')
        if forest_type:
            queryset = queryset.filter(forest_type=forest_type)

        # Filter by regeneration initiation
        regen_init = self.request.query_params.get('regen_init')
        if regen_init is not None:
            if regen_init.lower() == 'true':
                queryset = queryset.filter(regen_init=True)
            elif regen_init.lower() == 'false':
                queryset = queryset.filter(regen_init=False)

        return queryset.order_by('task')

    @action(detail=False, methods=['get'])
    def regeneration_tasks(self, request):
        """Get tasks that initiate regeneration"""
        tasks = self.get_queryset().filter(regen_init=True)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_forest_type(self, request):
        """Get tasks grouped by forest type"""
        forest_types = TaskLkp.objects.values_list('forest_type', flat=True).distinct()
        result = {}

        for forest_type in forest_types:
            if forest_type:
                tasks = TaskLkp.objects.filter(forest_type=forest_type, effective_to__isnull=True)
                serializer = self.get_serializer(tasks, many=True)
                result[forest_type] = serializer.data

        return Response(result)

    @action(detail=True, methods=['get'])
    def categories(self, request, pk=None):
        """Get categories for a specific task"""
        task = self.get_object()
        # This would typically fetch from TaskCategory model
        return Response({
            'task': task.task,
            'task_name': task.task_name,
            'category_labels': {
                'category1': task.category1_label,
                'category2': task.category2_label,
                'category3': task.category3_label,
                'category4': task.category4_label,
            },
            'quantity_labels': {
                'qty1': task.qty1_label,
                'qty2': task.qty2_label,
                'qty3': task.qty3_label,
                'qty4': task.qty4_label,
            }
        })


class TasksAttLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Task Attributes Lookup
    Provides additional attribute flags for tasks
    """
    queryset = TasksAttLkp.objects.all()
    serializer_class = TasksAttLkpSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['addition_attrib', 'description']


class TreatmentStatusLkpViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Treatment Status Lookup
    Provides treatment status codes and definitions
    """
    queryset = TreatmentStatusLkp.objects.all()
    serializer_class = TreatmentStatusLkpSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['status', 'name', 'definition']


class LookupSummaryViewSet(viewsets.ViewSet):
    """
    API endpoint providing summary of all lookup tables with URLs
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get counts, basic info, and URLs for all lookup tables"""
        base_url = request.build_absolute_uri('/api/')

        summary = {
            'cohort_metrics': {
                'count': CohortMetricsLkp.objects.filter(effective_to__isnull=True).count(),
                'description': 'Success measures and metrics for cohorts',
                'url': f"{base_url}lookups/cohort-metrics/",
                'detail_url_template': f"{base_url}lookups/cohort-metrics/{{id}}/",
                'filters': {
                    'rating_type': 'Filter by rating type (true/false)',
                    'search': 'Search in name, definition, value, method'
                }
            },
            'machines': {
                'count': MachineLkp.objects.count(),
                'description': 'Machine types and specifications for thinning/coppice control',
                'url': f"{base_url}lookups/machines/",
                'detail_url_template': f"{base_url}lookups/machines/{{id}}/",
                'filters': {
                    'machine_type': 'Filter by machine type',
                    'felling_head_herbicide_spray': 'Filter by herbicide spray capability',
                    'search': 'Search in manufacturer, model, machine_type'
                },
                'custom_endpoints': {
                    'by_type': f"{base_url}lookups/machines/by_type/"
                }
            },
            'objectives': {
                'count': ObjectiveLkp.objects.filter(effective_to__isnull=True).count(),
                'description': 'Silvicultural and management objectives',
                'url': f"{base_url}lookups/objectives/",
                'detail_url_template': f"{base_url}lookups/objectives/{{id}}/",
                'filters': {
                    'cut': 'Filter by cut type',
                    'forest_type': 'Filter by forest type',
                    'prescription': 'Filter by prescription availability',
                    'search': 'Search in obj_code, description, definition'
                },
                'custom_endpoints': {
                    'with_prescriptions': f"{base_url}lookups/objectives/with_prescriptions/",
                    'by_forest_type': f"{base_url}lookups/objectives/by_forest_type/"
                }
            },
            'organisations': {
                'count': OrganisationLkp.objects.count(),
                'description': 'Organisation codes and descriptions',
                'url': f"{base_url}lookups/organisations/",
                'detail_url_template': f"{base_url}lookups/organisations/{{id}}/",
                'filters': {
                    'search': 'Search in organisation, description'
                }
            },
            'regeneration_methods': {
                'count': RegenerationMethodsLkp.objects.count(),
                'description': 'Regeneration method codes matching FMIS',
                'url': f"{base_url}lookups/regeneration-methods/",
                'detail_url_template': f"{base_url}lookups/regeneration-methods/{{id}}/",
                'filters': {
                    'search': 'Search in regen_method, description'
                }
            },
            'reschedule_reasons': {
                'count': RescheduleReasonsLkp.objects.count(),
                'description': 'Standard reasons for rescheduling treatments',
                'url': f"{base_url}lookups/reschedule-reasons/",
                'detail_url_template': f"{base_url}lookups/reschedule-reasons/{{id}}/",
                'filters': {
                    'search': 'Search in rescheduled_reason, description'
                }
            },
            'spatial_precision': {
                'count': SpatialPrecisionLkp.objects.count(),
                'description': 'Mapping precision codes and descriptions',
                'url': f"{base_url}lookups/spatial-precision/",
                'detail_url_template': f"{base_url}lookups/spatial-precision/{{id}}/",
                'filters': {
                    'search': 'Search in precision_code, resolution, description'
                }
            },
            'species': {
                'count': SpeciesApiLkp.objects.count(),
                'description': 'API species codes and descriptions for forest types',
                'url': f"{base_url}lookups/species/",
                'detail_url_template': f"{base_url}lookups/species/{{id}}/",
                'filters': {
                    'search': 'Search in species, short_description, full_description'
                },
                'custom_endpoints': {
                    'by_fmis_type': f"{base_url}lookups/species/by_fmis_type/"
                }
            },
            'tasks': {
                'count': TaskLkp.objects.filter(effective_to__isnull=True).count(),
                'description': 'Task codes, definitions and specifications',
                'url': f"{base_url}lookups/tasks/",
                'detail_url_template': f"{base_url}lookups/tasks/{{id}}/",
                'filters': {
                    'forest_type': 'Filter by forest type',
                    'regen_init': 'Filter by regeneration initiation',
                    'addition_attribs': 'Filter by additional attributes requirement',
                    'search': 'Search in task, task_name, definition, financial_activity'
                },
                'custom_endpoints': {
                    'regeneration_tasks': f"{base_url}lookups/tasks/regeneration_tasks/",
                    'by_forest_type': f"{base_url}lookups/tasks/by_forest_type/",
                    'categories': f"{base_url}lookups/tasks/{{id}}/categories/"
                }
            },
            'task_attributes': {
                'count': TasksAttLkp.objects.count(),
                'description': 'Additional task attribute flags',
                'url': f"{base_url}lookups/task-attributes/",
                'detail_url_template': f"{base_url}lookups/task-attributes/{{id}}/",
                'filters': {
                    'search': 'Search in addition_attrib, description'
                }
            },
            'treatment_statuses': {
                'count': TreatmentStatusLkp.objects.count(),
                'description': 'Treatment status codes and definitions',
                'url': f"{base_url}lookups/treatment-statuses/",
                'detail_url_template': f"{base_url}lookups/treatment-statuses/{{id}}/",
                'filters': {
                    'search': 'Search in status, name, definition'
                }
            },
        }

        # Add simplified endpoints for common use cases
        summary['simplified_endpoints'] = {
            'all_objectives': f"{base_url}lookups/objectives/?format=json",
            'all_tasks': f"{base_url}lookups/tasks/?format=json",
            'all_species': f"{base_url}lookups/species/?format=json",
            'active_items_only': 'Add ?active=true to any endpoint to get only active records',
            'search_hint': 'Add ?search=term to any endpoint to search across fields'
        }

        return Response(summary)

    @action(detail=False, methods=['get'])
    def quick_links(self, request):
        """Get quick links to commonly used lookup endpoints"""
        base_url = request.build_absolute_uri('/api/')

        quick_links = {
            'dropdown_data': {
                'objectives': f"{base_url}lookups/objectives/?fields=obj_code,description,cut,forest_type",
                'tasks': f"{base_url}lookups/tasks/?fields=task,task_name,forest_type,default_organisation",
                'species': f"{base_url}lookups/species/?fields=species,short_description,fmis_code_species",
                'regeneration_methods': f"{base_url}lookups/regeneration-methods/",
                'treatment_statuses': f"{base_url}lookups/treatment-statuses/",
            },
            'filtered_views': {
                'regeneration_tasks': f"{base_url}lookups/tasks/regeneration_tasks/",
                'objectives_with_prescriptions': f"{base_url}lookups/objectives/with_prescriptions/",
                'active_cohort_metrics': f"{base_url}lookups/cohort-metrics/active/",
            },
            'grouped_data': {
                'tasks_by_forest_type': f"{base_url}lookups/tasks/by_forest_type/",
                'objectives_by_forest_type': f"{base_url}lookups/objectives/by_forest_type/",
                'species_by_fmis_type': f"{base_url}lookups/species/by_fmis_type/",
                'machines_by_type': f"{base_url}lookups/machines/by_type/",
            }
        }

        return Response(quick_links)

    @action(detail=False, methods=['get'])
    def usage_examples(self, request):
        """Provide usage examples for the lookup APIs"""
        base_url = request.build_absolute_uri('/api/')

        examples = {
            'get_all_active_objectives': {
                'url': f"{base_url}lookups/objectives/",
                'description': 'Get all active silvicultural objectives',
                'query_params': '?format=json'
            },
            'search_tasks_by_name': {
                'url': f"{base_url}lookups/tasks/",
                'description': 'Search for tasks containing "thin"',
                'query_params': '?search=thin'
            },
            'filter_tasks_by_forest_type': {
                'url': f"{base_url}lookups/tasks/",
                'description': 'Get tasks for Jarrah forest type',
                'query_params': '?forest_type=Jarrah'
            },
            'get_regeneration_tasks': {
                'url': f"{base_url}lookups/tasks/regeneration_tasks/",
                'description': 'Get tasks that initiate regeneration',
                'query_params': ''
            },
            'get_objectives_with_prescriptions': {
                'url': f"{base_url}lookups/objectives/with_prescriptions/",
                'description': 'Get objectives that have prescriptions',
                'query_params': ''
            },
            'get_simplified_list_for_dropdown': {
                'url': f"{base_url}lookups/objectives/",
                'description': 'Get simplified list for dropdown (using fields parameter)',
                'query_params': '?fields=obj_code,description,cut,forest_type'
            },
            'get_specific_objective_details': {
                'url': f"{base_url}lookups/objectives/K-ETHIN1/",
                'description': 'Get detailed information for specific objective',
                'query_params': ''
            },
            'get_task_categories': {
                'url': f"{base_url}lookups/tasks/E-THIN-K1/categories/",
                'description': 'Get category information for specific task',
                'query_params': ''
            }
        }

        return Response(examples)


class CombinedLkpView(views.APIView):
    """ http://localhost:8001/api/combined_lookups/
    """
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get(self, request):
        serializer = CombinedLkpSerializer({})
        return Response(serializer.data)

