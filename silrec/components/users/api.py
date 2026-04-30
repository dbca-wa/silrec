import traceback
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import User
from django.apps import apps

from rest_framework.views import APIView
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

import logging
logger = logging.getLogger(__name__)


class GetProfile(views.APIView):
    renderer_classes = [JSONRenderer,]
    def get(self, request, format=None):
        serializer  = UserSerializer(request.user,
                context={'request': request}
                )
        return Response(serializer.data)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        groups = list(user.groups.values_list('name', flat=True))
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'groups': groups,
            'is_readonly_user': ('User' in groups or 'Reviewer' in groups) and not any(
                g in groups for g in ['Operator', 'Assessor', 'Silrec Admin']
            ),
            'is_operator_user': 'Operator' in groups,
        })

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

    @action(detail=False, methods=['GET'])
    def current(self, request, *args, **kwargs):
        '''
        http://localhost:8001/api/users/current/
        '''
        user = request.user
        groups = list(user.groups.values_list('name', flat=True))
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'groups': groups,
            'is_readonly_user': ('User' in groups or 'Reviewer' in groups) and not any(
                g in groups for g in ['Operator', 'Assessor', 'Silrec Admin']
            ),
            'is_operator_user': 'Operator' in groups,
        })

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


from silrec.components.users.serializers import SearchByUserRequestSerializer, SearchByUserResultSerializer

class SearchByUserView(APIView):
    """API endpoint for searching records by user across multiple models"""
    from silrec.components.proposals.api import SearchThrottle

    permission_classes = [IsAuthenticated]
    throttle_classes = [SearchThrottle]

    def get(self, request):
        """Handle GET request for user search"""
        # Convert GET params to internal format
        data = request.GET.dict()

        # Handle array parameters
        serializer = SearchByUserRequestSerializer(data=data)

        if not serializer.is_valid():
            logger.warning(f"User search validation errors: {serializer.errors}")
            return Response(
                {'error': 'Invalid request', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        try:
            results, total_records, filtered_records = self.perform_user_search(data)

            # Prepare response for datatable
            response_data = {
                'draw': data.get('draw', 1),
                'recordsTotal': total_records,
                'recordsFiltered': filtered_records,
                'data': results
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"Error performing user search: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Search failed', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_user_search(self, params):
        """Perform the actual user search across models"""
        user_id = params['user_id']
        search_mode = params.get('search_mode', 'all')
        model_type = params.get('model_type', 'all')
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        include_inactive = params.get('include_inactive', False)

        # Pagination parameters
        start = params.get('start', 0)
        length = params.get('length', 25)

        all_results = []
        total_records = 0
        filtered_records = 0

        # Get user object
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User with ID {user_id} does not exist")

        # Get configurations from database (with fallback)
        MODEL_CONFIG = self.get_model_config_from_db()

        # Determine which models to search
        models_to_search = MODEL_CONFIG.keys() if model_type == 'all' else [model_type]

        logger.info(f'Searching for user: {user.get_full_name()} (ID: {user_id})')
        logger.info(f'Search mode: {search_mode}')
        logger.info(f'Model type: {model_type}')

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

                if date_from:
                    queryset = queryset.filter(**{f"{date_field}__gte": date_from})
                if date_to:
                    date_to_plus_one = date_to + timedelta(days=1)
                    queryset = queryset.filter(**{f"{date_field}__lt": date_to_plus_one})

                # Filter out inactive records if needed
                if not include_inactive:
                    if hasattr(model_class, 'is_active'):
                        queryset = queryset.filter(is_active=True)
                    elif hasattr(model_class, 'active'):
                        queryset = queryset.filter(active=True)

                # Get total records count for this model
                total_records += queryset.count()

                # Build user search conditions based on search mode
                search_conditions = Q()

                # Define user fields to search based on mode
                user_fields = []

                if search_mode == 'all' or search_mode == 'created_by':
                    user_fields.extend(['created_by', 'creator', 'author', 'created_by_user'])

                if search_mode == 'all' or search_mode == 'updated_by':
                    user_fields.extend(['updated_by', 'modified_by', 'last_modified_by'])

                if search_mode == 'all' or search_mode == 'submitted_by':
                    user_fields.extend(['submitter', 'submitted_by', 'lodged_by'])

                if search_mode == 'all' or search_mode == 'assigned_to':
                    user_fields.extend(['assigned_to', 'assigned_officer', 'assigned_approver', 'assigned_user'])

                if search_mode == 'all' or search_mode == 'referral':
                    user_fields.extend(['referral', 'referred_to', 'reviewer'])

                # Remove duplicates
                user_fields = list(set(user_fields))

                # Create search conditions for each field
                for field in user_fields:
                    if hasattr(model_class, field):
                        # Check if it's a ForeignKey to User
                        field_obj = model_class._meta.get_field(field)
                        import ipdb; ipdb.set_trace()
                        if hasattr(field_obj, 'related_model') and field_obj.related_model == User:
                            search_conditions |= Q(**{f"{field}_id": user_id})
                        elif hasattr(field_obj, 'remote_field') and field_obj.remote_field.model == User:
                            search_conditions |= Q(**{f"{field}_id": user_id})

                # Also check for fields that might reference User through string (like submitter field in Proposal)
                if hasattr(model_class, 'submitter') and model_key == 'proposal':
                    search_conditions |= Q(submitter=user_id)

                # Apply the search conditions
                queryset = queryset.filter(search_conditions)

                # Get filtered count for this model
                filtered_count = queryset.count()
                filtered_records += filtered_count

                logger.info(f'{model_name}({filtered_count}) - Search Conditions: {search_conditions}')

                # Process results
                max_results_per_model = 1000
                for obj in queryset[:max_results_per_model]:
                    # Determine user role
                    user_role = 'Unknown'
                    user_role_display = 'Unknown'

                    for field in user_fields:
                        if hasattr(obj, field):
                            field_value = getattr(obj, field)
                            if field_value and (isinstance(field_value, User) or
                                                (isinstance(field_value, int) and field_value == user_id)):
                                # Map field name to display name
                                role_map = {
                                    'created_by': 'Creator',
                                    'creator': 'Creator',
                                    'author': 'Author',
                                    'created_by_user': 'Creator',
                                    'updated_by': 'Last Modified By',
                                    'modified_by': 'Last Modified By',
                                    'last_modified_by': 'Last Modified By',
                                    'submitter': 'Submitter',
                                    'submitted_by': 'Submitter',
                                    'lodged_by': 'Submitter',
                                    'assigned_to': 'Assigned To',
                                    'assigned_officer': 'Assigned Officer',
                                    'assigned_approver': 'Assigned Approver',
                                    'assigned_user': 'Assigned User',
                                    'referral': 'Referral',
                                    'referred_to': 'Referral',
                                    'reviewer': 'Reviewer'
                                }
                                user_role = field
                                user_role_display = role_map.get(field, field.replace('_', ' ').title())
                                break

                    # Get date field value
                    date_field = config.get('date_field', 'created_on')
                    created_date = None

                    try:
                        if '__' in date_field:
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

                    # Get title/name/description
                    title = None
                    for field in ['title', 'name', 'description']:
                        if hasattr(obj, field):
                            value = getattr(obj, field, None)
                            if value:
                                title = str(value)
                                break

                    # Get status
                    status = None
                    status_display = None
                    for field in ['status', 'processing_status', 'review_status']:
                        if hasattr(obj, field):
                            value = getattr(obj, field, None)
                            if value:
                                status = value
                                # Try to get display value
                                if hasattr(obj, f'get_{field}_display'):
                                    status_display = getattr(obj, f'get_{field}_display')()
                                else:
                                    status_display = str(value)
                                break

                    # Build result object
                    result = {
                        'model_type': model_key,
                        'record_id': record_id,
                        'user_role': user_role,
                        'user_role_display': user_role_display,
                        'title': title,
                        'status': status,
                        'status_display': status_display,
                        'created_on': created_date,
                        'action_url': config['url_pattern'].format(id=record_id),
                        'user_name': user.get_full_name(),
                        'user_email': user.email
                    }

                    all_results.append(result)

            except Exception as e:
                logger.warning(f"Error searching model {model_key} for user: {str(e)}", exc_info=True)
                continue

        # Sort by created date desc
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

    def get_model_config_from_db(self):
        """Get model configuration from database"""
        # This should be the same as in SearchByTextView
        # You might want to refactor this into a shared method
        from silrec.components.proposals.models import TextSearchModelConfig

        config = {}
        try:
            model_configs = TextSearchModelConfig.objects.filter(
                is_active=True
            ).order_by('order')

            for db_config in model_configs:
                config[db_config.key] = {
                    'model': db_config.model_name,
                    'display_name': db_config.display_name,
                    'date_field': db_config.date_field,
                    'id_field': db_config.id_field,
                    'url_pattern': db_config.url_pattern,
                }
        except Exception as e:
            logger.warning(f"Error loading model config from DB: {e}")
            # Fallback to default configuration
            config = {
                'proposal': {
                    'model': 'silrec.Proposal',
                    'display_name': 'Proposals',
                    'date_field': 'created_date',
                    'id_field': 'id',
                    'url_pattern': '/internal/proposal/{id}/'
                },
                'polygon': {
                    'model': 'silrec.Polygon',
                    'display_name': 'Polygons',
                    'date_field': 'created_on',
                    'id_field': 'polygon_id',
                    'url_pattern': '/internal/polygon/{id}/'
                },
                'cohort': {
                    'model': 'silrec.Cohort',
                    'display_name': 'Cohorts',
                    'date_field': 'created_on',
                    'id_field': 'cohort_id',
                    'url_pattern': '/internal/cohort/{id}/'
                },
                'treatment': {
                    'model': 'silrec.Treatment',
                    'display_name': 'Treatments',
                    'date_field': 'created_on',
                    'id_field': 'treatment_id',
                    'url_pattern': '/internal/treatment/{id}/'
                },
                'treatment_xtra': {
                    'model': 'silrec.Treatmentxtra',
                    'display_name': 'Treatment Extras',
                    'date_field': 'treatment__created_on',
                    'id_field': 'treatment_xtra_id',
                    'url_pattern': '/internal/treatment-extra/{id}/'
                },
                'survey_assessment_document': {
                    'model': 'silrec.SurveyAssessmentDocument',
                    'display_name': 'Survey Documents',
                    'date_field': 'created_on',
                    'id_field': 'document_id',
                    'url_pattern': '/internal/survey-document/{id}/'
                },
                'silviculturist_comment': {
                    'model': 'silrec.SilviculturistComment',
                    'display_name': 'Silviculturist Comments',
                    'date_field': 'created_on',
                    'id_field': 's_comment_id',
                    'url_pattern': '/internal/silviculturist-comment/{id}/'
                },
                'prescription': {
                    'model': 'silrec.Prescription',
                    'display_name': 'Prescriptions',
                    'date_field': 'task__created_on',
                    'id_field': 'prescription_id',
                    'url_pattern': '/internal/prescription/{id}/'
                }
            }

        return config

