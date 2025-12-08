from django.conf import settings
#from django.contrib import admin
from silrec.admin import admin
#from django.conf.urls import url, include
from django.conf.urls import include
from django.urls import path, re_path
from django.contrib.auth.views import LogoutView, LoginView
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import logout, login # DEV ONLY
from django.views.generic import TemplateView

from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view
from silrec import views

from silrec.components.users import api as users_api
from silrec.components.lookups import api as lookups_api
from silrec.components.forest_blocks import api as forest_blocks_api
from silrec.components.main import api as main_api
from silrec.components.proposals import api as proposal_api
#from sqs.components.gisquery import api as gisquery_api
#from sqs.components.gisquery import views as gisquery_views

from silrec.components.forest_blocks import views as forest_blocks_views

#schema_view = get_swagger_view(title='SQS API')

# API patterns
'''
router = routers.DefaultRouter()
router.register(r'layers', gisquery_api.DefaultLayerViewSet, basename='layers')
router.register(r'logs', gisquery_api.LayerRequestLogViewSet, basename='logs')
router.register(r'point_query', gisquery_api.PointQueryViewSet, basename='point_query')
router.register(r'tasks', gisquery_api.TaskViewSet, basename='tasks')
router.register(r'task_paginated', gisquery_api.TaskPaginatedViewSet, basename='task_paginated')

api_patterns = [
    re_path(r'^api/v1/',include(router.urls)),
]

# URL Patterns
urlpatterns = [
    re_path(r'admin/', admin.site.urls),
    re_path(r'^logout/$', LogoutView.as_view(), {'next_page': '/'}, name='logout'),
    re_path(r'', include(api_patterns)),
    re_path(r'^$', TemplateView.as_view(template_name='sqs/base2.html'), name='home'),

    re_path(r'api/v1/das/task_queue', csrf_exempt(gisquery_views.DisturbanceLayerQueueView.as_view()), name='das_task_queue'),
    re_path(r'api/v1/das/spatial_query', csrf_exempt(gisquery_views.DisturbanceLayerView.as_view()), name='das_spatial_query'),
    re_path(r'api/v1/add_layer', csrf_exempt(gisquery_views.DefaultLayerProviderView.as_view()), name='add_layer'),
]
'''

# API patterns
router = routers.DefaultRouter()
router.include_root_view = False

if settings.INCLUDE_ROOT_VIEW:
        router.include_root_view = True

#router.register(r"users", users_api.UserViewSet)
router.register(r'users', users_api.UserViewSet, basename='users')
router.register("proposal", proposal_api.ProposalViewSet, basename="proposal")
#router.register(r"lookup_tbls", lookups_api.MainViewSet, basename="lookup_tbls")
#router.register(r'cohorts', forest_blocks_api.CohortViewSet, basename='cohorts')
#router.register(r'treatments', forest_blocks_api.TreatmentViewSet, basename='treatments')
router.register(r'polygon', forest_blocks_api.PolygonViewSet, basename='polygon')
router.register(r'polygon2', forest_blocks_api.Polygon2ViewSet, basename='polygon2')
router.register(r'polygon3', forest_blocks_api.PolygonGeometryViewSet, basename='polygon3')
router.register(r'polygoncohorts', forest_blocks_api.PolygonCohortViewSet, basename='polygoncohorts')

router.register(r'ply_paginated',forest_blocks_api.PolygonPaginatedViewSet,"ply_paginated")
router.register(r"proposal_paginated", proposal_api.ProposalPaginatedViewSet, basename="proposal_paginated")

router.register(r"application_types", main_api.ApplicationTypeViewSet)

router.register(r'polygon_cohort_table', forest_blocks_api.PolygonCohortTableViewSet, basename='polygon_cohort_table')

router.register(r'cohorts', forest_blocks_api.CohortViewSet)
router.register(r'treatments', forest_blocks_api.TreatmentViewSet)
router.register(r'treatment-extras', forest_blocks_api.TreatmentXtraViewSet)
router.register(r'operations', forest_blocks_api.OperationViewSet, basename='operations')
router.register(r'prescriptions', forest_blocks_api.PrescriptionViewSet)
router.register(r'silviculturist-comments', forest_blocks_api.SilviculturistCommentViewSet)
router.register(r'polygon_search', forest_blocks_api.PolygonSearchViewSet, basename='polygon_search')

# Lookups
# Add to your existing urlpatterns in urls.py

router.register(r'lookups/cohort-metrics', lookups_api.CohortMetricsLkpViewSet, basename='cohort-metrics')
router.register(r'lookups/machines', lookups_api.MachineLkpViewSet, basename='machines')
router.register(r'lookups/objectives', lookups_api.ObjectiveLkpViewSet, basename='objectives')
router.register(r'lookups/organisations', lookups_api.OrganisationLkpViewSet, basename='organisations')
router.register(r'lookups/regeneration-methods', lookups_api.RegenerationMethodsLkpViewSet, basename='regeneration-methods')
router.register(r'lookups/reschedule-reasons', lookups_api.RescheduleReasonsLkpViewSet, basename='reschedule-reasons')
router.register(r'lookups/spatial-precision', lookups_api.SpatialPrecisionLkpViewSet, basename='spatial-precision')
router.register(r'lookups/species', lookups_api.SpeciesApiLkpViewSet, basename='species')
router.register(r'lookups/tasks', lookups_api.TaskLkpViewSet, basename='tasks')
router.register(r'lookups/task-attributes', lookups_api.TasksAttLkpViewSet, basename='task-attributes')
router.register(r'lookups/treatment-statuses', lookups_api.TreatmentStatusLkpViewSet, basename='treatment-statuses')
router.register(r'lookups/summary', lookups_api.LookupSummaryViewSet, basename='lookup-summary')
router.register(r'survey-assessment-documents', forest_blocks_api.SurveyAssessmentDocumentViewSet, basename='survey_assessment-documents')
router.register(r'reports', proposal_api.SQLReportViewSet, basename='reports')
router.register(r'text_search_field_displays', proposal_api.TextSearchFieldDisplayViewSet, basename='text_search_field_displays')
router.register(r'text_search_model_configs', proposal_api.TextSearchModelConfigViewSet, basename='text_search_model_configs')

api_patterns = [
    #re_path(r'api/', include(router.urls)),
    re_path(r"^api/", include(router.urls)),
    #re_path(r'api/profile$', users_api.GetProfile.as_view(), name='get-profile'),
    #re_path(r"^api/user$", users_api.UserViewSet.as_view(), name="get-user"),
    #re_path(r"^api/cohorts/<int:cohort_id>/get_cohort$", forest_blocks_api.CohortViewSet.as_view({'get': 'get_cohort'}), name="get-cohort"),
    #re_path(r'^api/cohorts/<int:cohort_id>/get_cohort$', forest_blocks_api.CohortViewSet.as_view({'get': 'get_cohort'}), name='get-cohort'),
    re_path(r"^api/proposal_type$", proposal_api.GetProposalType.as_view(), name="get-proposal-type"),
]

urlpatterns = [
    re_path(r'admin/', admin.site.urls),
    #re_path(r'', include(api_patterns)),
    re_path(r"", include(api_patterns)),
    re_path(r"^$", views.SilrecRoutingView.as_view(), name="home"),

    re_path('logout/', views.UserLogoutView.as_view(http_method_names = ['get', 'post', 'options']), name='logout'),
    #re_path(r'^$', TemplateView.as_view(template_name='base.html'), name='home'),
    #re_path(r'^$', views.SilrecRoutingView.as_view(), name='home'),

    re_path(r'^internal/', views.InternalView.as_view(), name='internal'),
    re_path(r'^external/', views.ExternalView.as_view(), name='external'),
    re_path(r'^contact/', views.SilrecContactView.as_view(), name='contact'),
    re_path(r'^further_info/', views.SilrecFurtherInformationView.as_view(), name='further_info'),
    re_path(r'^mgt-commands/$', views.ManagementCommandsView.as_view(), name='mgt-commands'),

    re_path(
        r"^internal/proposal/(?P<pk>\d+)/$",
        views.InternalProposalView.as_view(),
        name="internal-proposal-detail",
    ),
    re_path(
        r"^api/application_statuses_dict$",
        proposal_api.GetApplicationStatusesDict.as_view(),
        name="get-application-statuses-dict",
    ),
    re_path(
        r"^api/combined_lookups/$",
        lookups_api.CombinedLkpView.as_view(),
        name="combined-lookups",
    ),

#    re_path(
#        r"^api/polygon_cohort_table(?P<pk>\d+)/$",
#        forest_blocks_api.PolygonCohortTableViewSet.as_view(),
#        name="polygon_cohort_table",
#    ),
    #router.register(r'polygon_cohort_table', forest_blocks_api.PolygonCohortTableViewSet, basename='polygon_cohort_table')

#    # Cohort detail page (served by Vue frontend)
#    re_path('cohorts/<int:cohort_id>/polygon/<int:polygon_id>/',
#         views.CohortDetailView.as_view(), name='cohort-detail'),
#
#    # Alternative URL pattern without polygon_id
#    re_path('cohorts/<int:cohort_id>/',
#         views.CohortDetailView.as_view(), name='cohort-detail-simple'),

    re_path(
        r"^api/test_operation_update/$",
        forest_blocks_api.TestOperationUpdate.as_view(),
        name="test-operation-update",
    ),

    re_path(r'^api/search_by_text/', proposal_api.SearchByTextView.as_view(), name='search_by_text'),
    re_path(r'^api/text_search_fields_by_model/$', proposal_api.TextSearchFieldsByModelView.as_view(), name='text_search_fields_by_model'),
    re_path(r'^api/text_search_available_models/$', proposal_api.TextSearchAvailableModelsView.as_view(), name='text_search_available_models'),

    re_path(r'^api/search_by_user/', users_api.SearchByUserView.as_view(), name='search_by_user'),

    re_path('api/debug-polygon-relations/', forest_blocks_api.DebugPolygonRelationsView.as_view(), name='debug-polygon-relations'),
]

if settings.ENABLE_DJANGO_LOGIN:
    urlpatterns.append(
        re_path(r"^ssologin/", LoginView.as_view(), name="ssologin")
    )

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#if settings.SHOW_DEBUG_TOOLBAR:
#    from debug_toolbar.toolbar import debug_toolbar_urls
#
#    urlpatterns = [
#        *urlpatterns,
#    ] + debug_toolbar_urls()
