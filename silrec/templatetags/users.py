from django.template import Library
from django.conf import settings
from silrec import helpers as silrec_helpers
from datetime import datetime, timedelta
from django.utils import timezone
import pytz

register = Library()


@register.simple_tag(takes_context=True)
def is_silrec_admin(context):
    request = context['request']
    return silrec_helpers.is_silrec_admin(request)

@register.simple_tag(takes_context=True)
def _is_internal(context):
    request = context['request']
    return silrec_helpers.is_internal(request)

@register.simple_tag(takes_context=True)
def is_internal(context):
    request = context['request']
    return silrec_helpers.is_internal(request)

@register.simple_tag(takes_context=True)
def is_internal_path(context):
    return 'internal/' in context.request.path

@register.simple_tag(takes_context=True)
def has_access(context):
    request = context['request']
    return silrec_helpers.has_access(request.user)

@register.simple_tag()
def system_maintenance_due():
    return False


