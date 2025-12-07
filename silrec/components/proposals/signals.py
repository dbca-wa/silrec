from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

from silrec.components.proposals.models import (
    TextSearchModelConfig,
    TextSearchFieldDisplay
)
from silrec.components.proposals.service import SearchConfigService

import logging
logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=TextSearchModelConfig)
def invalidate_model_config_cache(sender, **kwargs):
    """Clear cache when model config changes"""
    SearchConfigService.invalidate_cache()

@receiver([post_save, post_delete], sender=TextSearchFieldDisplay)
def invalidate_field_display_cache(sender, **kwargs):
    """Clear cache when field display changes"""
    SearchConfigService.invalidate_cache()
