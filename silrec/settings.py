from django.core.exceptions import ImproperlyConfigured

import os, hashlib
import sys
import confy
from confy import env, database
import dj_database_url
import json
import decouple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
confy.read_environment_file(BASE_DIR+"/.env")
os.environ.setdefault("BASE_DIR", BASE_DIR)

#from ledger_api_client.settings_base import *
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG', False)
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', False)
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', [])
SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', False)
CORS_ALLOW_ALL_ORIGINS = env('CORS_ALLOW_ALL_ORIGINS', False)
SHOW_MENUS = env('SHOW_MENUS', True)

if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = env('ALLOWED_HOSTS', [])

ROOT_URLCONF = 'silrec.urls'
SITE_ID = 1
DEPT_DOMAINS = env('DEPT_DOMAINS', ['dpaw.wa.gov.au', 'dbca.wa.gov.au'])
SYSTEM_MAINTENANCE_WARNING = env('SYSTEM_MAINTENANCE_WARNING', 24) # hours
#SHOW_DEBUG_TOOLBAR = env('SHOW_DEBUG_TOOLBAR', False)
BUILD_TAG = env('BUILD_TAG', hashlib.md5(os.urandom(32)).hexdigest())  # URL of the Dev app.js served by webpack & express
ENABLE_DJANGO_LOGIN = env('ENABLE_DJANGO_LOGIN', False)
LOGIN_REDIRECT_URL = "/"  # new

INCLUDE_ROOT_VIEW = env("INCLUDE_ROOT_VIEW", False)

REQUEST_TIMEOUT = env('REQUEST_TIMEOUT', 300) # 20 secs

CRS = env('CRS', 'epsg:4326')
CRS_CARTESIAN = env('CRS_CARTESIAN', 'epsg:3043')
CRS_GDA94 = env('CRS_GDA94', 'epsg:28350')
OGR2OGR = env('OGR2OGR', '/usr/bin/ogr2ogr')

SLIVER_AREALENGTH_THRESHOLD=5 # Polygon AREA/LENGTH

#KMI_SERVER_URL = env("KMI_SERVER_URL", "https://kmi.dbca.wa.gov.au")
#
#GIS_SERVER_URL = env(
#            "GIS_SERVER_URL", "https://kaartdijin-boodja-geoserver.dbca.wa.gov.au"
#            )
#GIS_LANDS_AND_WATERS_LAYER_NAME = env(
#            "GIS_LANDS_AND_WATERS_LAYER_NAME",
#                "kaartdijin-boodja-public:CPT_DBCA_LEGISLATED_TENURE",
#                )

#KMI_AUTH_USERNAME = env("KMI_AUTH_USERNAME")
#KMI_AUTH_PASSWORD = env("KMI_AUTH_PASSWORD")



LANGUAGE_CODE = 'en-AU'
TIME_ZONE = 'Australia/Perth'
USE_I18N = True
USE_L10N = True
USE_TZ = False

#SHELL_PLUS_POST_IMPORTS = [
#    'import pandas as pd',
#    'import geopandas as gpd',
#    'import matplotlib.pyplot as plt',
#    'from silrec.utils.plot_utils import plot_gdf, plot_overlay',
#    'from silrec.utils.shapefile_silvers_merger import ShapefileSliversMerger',
#]

# For Auto Reloading
#~/.ipython/profile_default/ipython_config.py
#c.InteractiveShellApp.extensions = ['autoreload']
#c.InteractiveShellApp.exec_lines = ['%autoreload 2']

# Custom Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if env('CONSOLE_EMAIL_BACKEND', False) else 'silrec.backend_email.SilrecEmailBackend'
PRODUCTION_EMAIL = env('PRODUCTION_EMAIL', False)
# Intercept and forward email recipient for non-production instances
# Send to list of NON_PROD_EMAIL users instead
EMAIL_INSTANCE = env('EMAIL_INSTANCE','PROD')
NON_PROD_EMAIL = env('NON_PROD_EMAIL')
if not PRODUCTION_EMAIL:
    if not NON_PROD_EMAIL:
        raise ImproperlyConfigured('NON_PROD_EMAIL must not be empty if PRODUCTION_EMAIL is set to False')
    if EMAIL_INSTANCE not in ['PROD','DEV','TEST','UAT']:
        raise ImproperlyConfigured('EMAIL_INSTANCE must be either "PROD","DEV","TEST","UAT"')
    if EMAIL_INSTANCE == 'PROD':
        raise ImproperlyConfigured('EMAIL_INSTANCE cannot be \'PROD\' if PRODUCTION_EMAIL is set to False')

STATIC_URL = '/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

#INSTALLED_APPS += [
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    #'django.contrib.gis',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    #'corsheaders',
    #'django_cron',

    'reversion',
    #'reversion_compare',
    'bootstrap3',
    'webtemplate_dbca',
    'silrec',
    'silrec.components.users',
    'silrec.components.forest_blocks',
    'silrec.components.lookups',
    'silrec.components.proposals',
    'silrec.components.main',
    'rest_framework',
    #'rest_framework.authtoken',
    'rest_framework_gis',
    #'rest_framework_swagger',
    #"debug_toolbar",
    #'pympler',

    #'appmonitor_client',
    'django_vite',
]

ADD_REVERSION_ADMIN=True

WSGI_APPLICATION = 'silrec.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_datatables.filters.DatatablesFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework_datatables.pagination.DatatablesPageNumberPagination',
    'PAGE_SIZE': 10,
    #'EXCEPTION_HANDLER': 'utils.rest_framework.views.exception_handler'
}

#MIDDLEWARE_CLASSES = [
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'dbca_utils.middleware.SSOLoginMiddleware',
    'silrec.middleware.CacheControlMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

SHOW_DEBUG_TOOLBAR = env('SHOW_DEBUG_TOOLBAR', False)
if SHOW_DEBUG_TOOLBAR:
#    INTERNAL_IPS = [
#        "127.0.0.1",
#    ]

#    import socket
#    # Dynamically add the Docker gateway IP
#    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
#    INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1"]

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }

    INSTALLED_APPS = [
        *INSTALLED_APPS,
        "debug_toolbar",
    ]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'silrec', 'templates'),
            os.path.join(BASE_DIR, 'silrec', 'templates', 'silrec'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'silrec.context_processors.silrec_url',
            ],
        },
    },
]

#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#        'LOCATION': os.path.join(BASE_DIR, 'silrec', 'cache'),
#    }
#}

#CACHE_KEY_MAP_PROPOSALS = "map-proposals"

STATIC_ROOT=os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
        os.path.join(
            os.path.join(BASE_DIR, "silrec", "static", "silrec_vue")
        ),
        os.path.join(os.path.join(BASE_DIR, "silrec", "static")),
        os.path.join(os.path.join(BASE_DIR, "silrec", "static", "silrec")),
    ]

DEV_STATIC = env('DEV_STATIC',False)
DEV_STATIC_URL = env('DEV_STATIC_URL')
if DEV_STATIC and not DEV_STATIC_URL:
    raise ImproperlyConfigured('If running in DEV_STATIC, DEV_STATIC_URL has to be set')
DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# Department details
LAST_UPDATED = env('LAST_UPDATED', '05/2025')
SYSTEM_NAME = env('SYSTEM_NAME', 'SILvicultural RECording System')
SYSTEM_NAME_TITLE = SYSTEM_NAME.title()
SYSTEM_NAME_SHORT = env('SYSTEM_NAME_SHORT', 'SILREC')
SITE_PREFIX = env('SITE_PREFIX')
SITE_DOMAIN = env('SITE_DOMAIN')
SUPPORT_EMAIL = env('SUPPORT_EMAIL', 'silrec@' + SITE_DOMAIN).lower()
DEP_URL = env('DEP_URL','www.' + SITE_DOMAIN)
DEP_PHONE = env('DEP_PHONE','(08) 9219 9978')
DEP_PHONE_SUPPORT = env('DEP_PHONE_SUPPORT','(08) 9219 9000')
DEP_FAX = env('DEP_FAX','(08) 9423 8242')
DEP_POSTAL = env('DEP_POSTAL','Locked Bag 104, Bentley Delivery Centre, Western Australia 6983')
DEP_NAME = env('DEP_NAME','Department of Biodiversity, Conservation and Attractions')
DEP_NAME_SHORT = env('DEP_NAME_SHORT','DBCA')
BRANCH_NAME = env('BRANCH_NAME','Forest Management Branch')
DIVISION_NAME = env('BRANCH_NAME','Conservation and Ecosystem Management Division')
DEP_ADDRESS = env('DEP_ADDRESS','17 Dick Perry Avenue, Kensington WA 6151')
SITE_URL = env('SITE_URL', 'https://' + SITE_PREFIX + '.' + SITE_DOMAIN)
PUBLIC_URL=env('PUBLIC_URL', SITE_URL)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@' + SITE_DOMAIN).lower()
MEDIA_APP_DIR = env('MEDIA_APP_DIR', 'silrec')
ADMIN_GROUP = env('ADMIN_GROUP', 'SILREC Admin')
CRON_RUN_AT_TIMES = env('CRON_RUN_AT_TIMES', '04:05')
CRON_EMAIL = env('CRON_EMAIL', 'cron@' + SITE_DOMAIN).lower()
# for ORACLE Job Notification - override settings_base.py
#PAYMENT_SYSTEM_ID = env('PAYMENT_SYSTEM_ID', 'S999')
EMAIL_FROM = DEFAULT_FROM_EMAIL
NOTIFICATION_EMAIL=env('NOTIFICATION_EMAIL')
CRON_NOTIFICATION_EMAIL = env('CRON_NOTIFICATION_EMAIL', NOTIFICATION_EMAIL).lower()
EMAIL_HOST = env('EMAIL_HOST', 'smtp.lan.fyi')

PROTECTED_MEDIA = "protected_media"
PROTECTED_MEDIA_ROOT = env(
    "PROTECTED_MEDIA_ROOT", os.path.join(BASE_DIR, PROTECTED_MEDIA)
)
SECURE_FILE_API_BASE_PATH = "/api/main/secure_file/"
SECURE_DOCUMENT_API_BASE_PATH = "/api/main/secure_document/"

API_EXCEPTION_MESSAGE = (
    "An error occurred while processing your request, "
    f"please try again and if the problem persists contact {SUPPORT_EMAIL}"
)

#AFFECTED_TABLES = ['polygon', 'cohort', 'assign_cht_to_ply', 'treatment', 'treatment_xtra']
AFFECTED_TABLES = ['silrec.polygon', 'silrec.cohort', 'silrec.assign_cht_to_ply']

# Database
DATABASES = {
    # Defined in the DATABASE_URL env variable.
    'default': database.config()
}
# DATABASES['default'].update(OPTIONS={'options': '-c search_path=silrec'})
# DATABASES['default'].update(OPTIONS={'options': '-c search_path=silrec,public'})
PGSQL_OPTIONS = env('PGSQL_OPTIONS', {'options': '-c search_path=public,silrec'})
DATABASES['default'].update(OPTIONS=PGSQL_OPTIONS)

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#        'TEST': {'NAME': os.path.join(BASE_DIR, 'test.sqlite3')},
#    }
#}

CRON_CLASSES = [
    'appmonitor_client.cron.CronJobAppMonitorClient',
]

BASE_URL=env('BASE_URL')

RUNNING_DEVSERVER = len(sys.argv) > 1 and sys.argv[1] == "runserver"

# Make sure this returns true when in local development
# so you can use the vite dev server with hot module reloading
USE_VITE_DEV_SERVER = RUNNING_DEVSERVER and EMAIL_INSTANCE == "DEV" and DEBUG is True

STATIC_URL_PREFIX = (
    "/static/silrec_vue/" if USE_VITE_DEV_SERVER else "silrec_vue/"
)

DJANGO_VITE = {
    "default": {
        "dev_mode": USE_VITE_DEV_SERVER,
        "dev_server_host": "localhost",  # Default host for vite (can change if needed)
        #"dev_server_host": "10.17.0.11",  # Default host for vite (can change if needed)
        "dev_server_port": 5183,  # Default port for vite (can change if needed)
        "static_url_prefix": STATIC_URL_PREFIX,
    }
}

VUE3_ENTRY_SCRIPT = env(
    "VUE3_ENTRY_SCRIPT",
    default="src/main.js",  # This path will be auto prefixed with the       static_url_prefix from DJANGO_VITE above
)  # Path of the vue3 entry point script served by vite

#print(f'{VUE3_ENTRY_SCRIPT}')


if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.mkdir(os.path.join(BASE_DIR, 'logs'))
LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': env('LOG_CONSOLE_LEVEL', 'INFO'),
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'silrec.log'),
            'formatter': 'verbose',
            'maxBytes': 5242880
        },
        'debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'sys_stats.log'),
            'formatter': 'verbose',
            'maxBytes': 5242880
        },
        'request_stats': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'requests.log'),
            'formatter': 'verbose',
            'maxBytes': 5242880
        },

    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': env('LOG_CONSOLE_LEVEL', 'WARNING'),
            'propagate': True
        },
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
#        'log': {
#            'handlers': ['console'],
#            'level': 'INFO'
#        },
        'silrec': {
            'handlers': ['file'],
            'level': 'INFO'
        },
        'sys_stats': {
            'handlers': ['debug'],
            'level': 'DEBUG'
        },
        'request_stats': {
            'handlers': ['request_stats'],
            'level': 'INFO'
        },

    }
}

DEFAULT_AUTO_FIELD='django.db.models.AutoField'

#CSRF_TRUSTED_ORIGINS_STRING = decouple.config("CSRF_TRUSTED_ORIGINS", default='[]')
#CSRF_TRUSTED_ORIGINS = json.loads(str(CSRF_TRUSTED_ORIGINS_STRING))

# This is needed so that the chmod is not called in django/core/files/storage.py
# (_save method of FileSystemStorage class)
# As it causes a permission exception when using azure network drives
#FILE_UPLOAD_PERMISSIONS = None

TEMPLATE_HEADER_LOGO = "/static/silrec/img/logo-park-stay-trunc.gif"

SHAPEFILE_PROCESSING_STORE = env('SHAPEFILE_PROCESSING_STORE', 'protected_media/shapefile_processing')


