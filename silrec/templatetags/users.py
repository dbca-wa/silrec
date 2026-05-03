from django.template import Library
from django.conf import settings
from silrec import helpers as silrec_helpers
from silrec.components.main.models import SystemMaintenance
from datetime import datetime, timedelta
from django.utils import timezone
import pytz

register = Library()
TIME_FORMAT = '%a %d-%b %Y %H:%M:%S' #'Fri 29-Oct 2021 08:30:33'


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
def _system_maintenance_due():
    return False

@register.simple_tag()
def system_maintenance_due():
    """ Returns True (actually a time str), if within <timedelta hours> of system maintenance due datetime """
    tz = pytz.timezone(settings.TIME_ZONE)
    now = timezone.now()  # returns UTC time
    qs = SystemMaintenance.objects.filter(start_date__gte=now - timedelta(minutes=1))
    if qs:
        obj = qs.earliest('start_date')
        if now >= obj.start_date - timedelta(hours=settings.SYSTEM_MAINTENANCE_WARNING) and now <= obj.start_date + timedelta(minutes=1):
            # display time in local timezone
            return '{0} - {1} (Duration: {2} mins)'.format(obj.start_date.astimezone(tz=tz).strftime(TIME_FORMAT), obj.end_date.astimezone(tz=tz).strftime(TIME_FORMAT), obj.duration())
    return False


