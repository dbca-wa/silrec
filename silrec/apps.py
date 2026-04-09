from __future__ import unicode_literals
from django.conf import settings

from django.apps import AppConfig

class SilrecConfig(AppConfig):
    name = 'silrec'
    #verbose_name = settings.SYSTEM_NAME

    run_once = False
    def ready(self):
#        if not self.run_once:
        import silrec.components.proposals.signals
        #import silrec.utils.audit_signals

        #self.run_once = True
        pass
