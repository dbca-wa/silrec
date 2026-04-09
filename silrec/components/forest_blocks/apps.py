from __future__ import unicode_literals
from django.conf import settings

from django.apps import AppConfig

class ForestBlocksConfig(AppConfig):
    name = 'silrec.components.forest_blocks'
    #verbose_name = settings.SYSTEM_NAME

    run_once = False
    def ready(self):
        #self.run_once = True
        pass
