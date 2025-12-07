from django.core.cache import cache

class SearchConfigService:
    """Service to manage search configurations with caching"""

    CACHE_KEY_MODEL_CONFIG = 'text_search_model_config'
    CACHE_KEY_FIELD_DISPLAY = 'text_search_field_display'
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_model_config(cls):
        """Get model configuration with caching"""
        config = cache.get(cls.CACHE_KEY_MODEL_CONFIG)
        if config is not None:
            return config

        from silrec.components.proposals.models import TextSearchModelConfig

        try:
            config = {}
            model_configs = TextSearchModelConfig.objects.filter(
                is_active=True
            ).order_by('order')

            for db_config in model_configs:
                config[db_config.key] = {
                    'model': db_config.model_name,
                    'display_name': db_config.display_name,
                    'search_fields': db_config.get_search_fields_list(),
                    'date_field': db_config.date_field,
                    'id_field': db_config.id_field,
                    'detail_fields': db_config.detail_fields or [],
                    'url_pattern': db_config.url_pattern,
                }

            cache.set(cls.CACHE_KEY_MODEL_CONFIG, config, cls.CACHE_TIMEOUT)
            return config
        except Exception as e:
            logger.error(f"Error loading model config: {e}")
            return {}

    @classmethod
    def get_field_display(cls):
        """Get field display names with caching"""
        display = cache.get(cls.CACHE_KEY_FIELD_DISPLAY)
        if display is not None:
            return display

        from silrec.components.proposals.models import TextSearchFieldDisplay

        try:
            display = {}
            field_displays = TextSearchFieldDisplay.objects.filter(
                is_active=True
            ).order_by('order')

            for field_display_obj in field_displays:
                display[field_display_obj.field_name] = field_display_obj.display_name

            cache.set(cls.CACHE_KEY_FIELD_DISPLAY, display, cls.CACHE_TIMEOUT)
            return display
        except Exception as e:
            logger.error(f"Error loading field display: {e}")
            return {}

    @classmethod
    def invalidate_cache(cls):
        """Invalidate both caches"""
        cache.delete(cls.CACHE_KEY_MODEL_CONFIG)
        cache.delete(cls.CACHE_KEY_FIELD_DISPLAY)

