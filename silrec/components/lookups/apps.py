from __future__ import unicode_literals
from django.conf import settings

from django.apps import AppConfig

class LookupsConfig(AppConfig):
    name = 'silrec.components.lookups'
    #verbose_name = settings.SYSTEM_NAME

    run_once = False
    def ready(self):
        #self.run_once = True
        pass
