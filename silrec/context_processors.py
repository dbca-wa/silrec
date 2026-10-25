from confy import env
from django.conf import settings
import logging


logger = logging.getLogger(__name__)

def silrec_url(request):
    PUBLIC_URL = 'https://silrec.dbca.wa.gov.au'
    displayed_system_name = settings.SYSTEM_NAME
    support_email = settings.SUPPORT_EMAIL

    return {
        'DJANGO_SETTINGS': settings,
        'template_header_logo': settings.TEMPLATE_HEADER_LOGO,

        #'DOMAIN_DETECTED': settings.DOMAIN_DETECTED,
        'DEBUG': settings.DEBUG,
        'DEV_STATIC': settings.DEV_STATIC,
        'DEV_STATIC_URL': settings.DEV_STATIC_URL,
        #'TEMPLATE_GROUP': settings.DOMAIN_DETECTED,
        'SYSTEM_NAME_SHORT': settings.SYSTEM_NAME_SHORT,
        'SYSTEM_NAME': settings.SYSTEM_NAME,
        'PUBLIC_URL': PUBLIC_URL,
        #'APPLICATION_GROUP': settings.DOMAIN_DETECTED,
        'DISPLAYED_SYSTEM_NAME': displayed_system_name,
        'SUPPORT_EMAIL': support_email,
        'build_tag': settings.BUILD_TAG,
        #'SHOW_DAS_MAP': settings.SHOW_DAS_MAP,
        #'MAX_LAYERS_PER_SQQ': settings.MAX_LAYERS_PER_SQQ,
        'vue3_entry_script': settings.VUE3_ENTRY_SCRIPT,
        'use_vite_dev_server': settings.USE_VITE_DEV_SERVER,
    }


def global_settings(request):
    from silrec.components.main.models import GlobalSettings

    defaults = {
        GlobalSettings.SHOW_HISTORY_JN_ICON_IN_DASHBOARD: settings.SHOW_HISTORY_JN_ICON_IN_DASHBOARD,
        GlobalSettings.SHOW_HISTORY_PROPOSAL_ICON_IN_DASHBOARD: settings.SHOW_HISTORY_PROPOSAL_ICON_IN_DASHBOARD,
        GlobalSettings.EXCLUDE_FIRST_RECORDED_VERSIONS: True,
        GlobalSettings.EXCLUDE_EMPTY_RECORDS: True,
    }

    try:
        values = {row.key: row.value for row in GlobalSettings.objects.all()}
    except Exception:
        # Table may not exist yet (e.g. before migrations are applied)
        values = {}

    def _bool(key):
        raw = values.get(key)
        if raw is None:
            return bool(defaults[key])
        return str(raw).strip().lower() in ('true', '1', 'yes', 'on')

    return {
        'show_history_jn_icon_in_dashboard': _bool(GlobalSettings.SHOW_HISTORY_JN_ICON_IN_DASHBOARD),
        'show_history_proposal_icon_in_dashboard': _bool(GlobalSettings.SHOW_HISTORY_PROPOSAL_ICON_IN_DASHBOARD),
        'exclude_first_recorded_versions': _bool(GlobalSettings.EXCLUDE_FIRST_RECORDED_VERSIONS),
        'exclude_empty_records': _bool(GlobalSettings.EXCLUDE_EMPTY_RECORDS),
    }
