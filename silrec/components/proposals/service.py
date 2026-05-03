import logging
import geopandas as gpd
from django.core.cache import cache

logger = logging.getLogger(__name__)

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


def write_shapefile_attributes_to_db(proposal):
    """
    After Keep, write shapefile attribute values to DB tables per
    ShapefileAttributeConfig.target_db_field.

    For each config with target_db_field set, reads the shapefile value
    and updates the matching Polygon, Cohort, or Operation record.

    target_db_field format: ``silrec.forest_blocks.<model>.field_name``
      e.g. ``silrec.forest_blocks.polygon.zfea_id``,
           ``silrec.forest_blocks.cohort.target_ba_m2ha``,
           ``silrec.forest_blocks.operation.fea_id``

    ForeignKey fields are detected from the model's field metadata and
    assigned via the ``_id`` attribute.
    """
    from django.db import models as django_models
    from django.conf import settings
    from silrec.components.proposals.models import ShapefileAttributeConfig
    from silrec.components.forest_blocks.models import (
        Polygon, Cohort, AssignChtToPly, Operation, Compartments,
    )

    if not proposal.shapefile_json:
        return False

    configs = ShapefileAttributeConfig.objects.filter(
        application_type=proposal.application_type,
        target_db_field__isnull=False,
    ).exclude(target_db_field__exact='')

    if not configs.exists():
        return False

    gdf = gpd.GeoDataFrame.from_features(proposal.shapefile_json['features'])
    if gdf.empty:
        return False

    proposal_polygons = list(Polygon.objects.filter(proposal=proposal))
    if not proposal_polygons:
        logger.warning(
            f'write_shapefile_attributes_to_db: no polygons for proposal {proposal.id}'
        )
        return False

    # Build a lookup: zfea_id -> polygon
    poly_by_zfea = {}
    for p in proposal_polygons:
        if p.zfea_id:
            poly_by_zfea[p.zfea_id] = p

    # Pre-fetch current cohort assignments
    polygon_ids = [p.polygon_id for p in proposal_polygons]
    cht_assignments = list(
        AssignChtToPly.objects.filter(polygon_id__in=polygon_ids, status_current=True)
        .select_related('cohort')
    )
    cohort_by_polygon_id = {a.polygon_id: a.cohort for a in cht_assignments}

    # Build FK sets: field_name -> is_fk for all updateable models
    fk_fields = {}
    for model_cls in (Polygon, Cohort, Operation, Compartments):
        fields = model_cls._meta.get_fields()
        fk_fields[model_cls.__name__.lower()] = {
            f.name: True for f in fields
            if isinstance(f, (django_models.ForeignKey, django_models.OneToOneField))
        }

    # Group configs by target model
    mapped_configs = []
    for cfg in configs:
        parts = cfg.get_target_db_field_parts()
        # parts: (app_label, model_name, field_name)
        # model_name is the actual model (e.g. 'operation', 'polygon', 'cohort')
        if parts[1] and parts[2]:
            mapped_configs.append((cfg.field_name, parts[1].lower(), parts[2]))

    if not mapped_configs:
        return False

    updated_count = 0
    updated_records = []

    # Sort polygons consistently by polygon_id to match shapefile feature order
    proposal_polygons.sort(key=lambda p: p.polygon_id)

    # Build case-insensitive column lookup for the GeoDataFrame
    gdf_cols_lower = {c.lower(): c for c in gdf.columns}

    for idx, (_, feature_row) in enumerate(gdf.iterrows()):
        val_by_field = {}
        for shp_field, model_name, db_field in mapped_configs:
            actual_col = gdf_cols_lower.get(shp_field.lower())
            if actual_col:
                val = feature_row.get(actual_col)
                if val is not None:
                    val_by_field.setdefault(model_name, {})[db_field] = val

        if idx == 0:
            logger.info(
                f'write_shapefile_attributes_to_db: shp_field configs={mapped_configs}, '
                f'actual columns={list(gdf.columns)}, '
                f'feature values={dict(feature_row)}, val_by_field={val_by_field}'
            )

        if not val_by_field:
            continue

        # Identify the polygon for this shapefile feature
        polygon = None
        fea_val = feature_row.get('fea_id') or feature_row.get('zfea_id')
        if fea_val and str(fea_val).strip():
            polygon = poly_by_zfea.get(str(fea_val).strip())
        if polygon is None and idx < len(proposal_polygons):
            polygon = proposal_polygons[idx]
        if polygon is None:
            logger.debug(
                f'write_shapefile_attributes_to_db: no polygon match for feature {idx} '
                f'(fea_val={fea_val!r}, polygons={len(proposal_polygons)})'
            )
            continue

        # Update polygon fields
        poly_fields = val_by_field.get('polygon', {})
        if poly_fields:
            changed = False
            field_log = []
            for db_field, val in poly_fields.items():
                attr = db_field
                if fk_fields.get('polygon', {}).get(db_field):
                    attr = db_field + '_id'
                old_val = getattr(polygon, attr, None)
                if old_val != val:
                    setattr(polygon, attr, val)
                    changed = True
                    field_log.append(f'{db_field}: {old_val!r} -> {val!r}')
            if changed:
                polygon.save()
                updated_count += 1
                updated_records.append(
                    f'polygon {polygon.polygon_id}: {"; ".join(field_log)}'
                )

        # Update cohort fields
        cohort_fields = val_by_field.get('cohort', {})
        if cohort_fields:
            cohort = cohort_by_polygon_id.get(polygon.polygon_id)
            if cohort:
                changed = False
                field_log = []
                for db_field, val in cohort_fields.items():
                    attr = db_field
                    if fk_fields.get('cohort', {}).get(db_field):
                        attr = db_field + '_id'
                    old_val = getattr(cohort, attr, None)
                    if old_val != val:
                        setattr(cohort, attr, val)
                        changed = True
                        field_log.append(f'{db_field}: {old_val!r} -> {val!r}')
                if changed:
                    cohort.save()
                    updated_records.append(
                        f'cohort {cohort.cohort_id}: {"; ".join(field_log)}'
                    )

        # Update operation fields (match or create by fea_id)
        op_fields = val_by_field.get('operation', {})
        if op_fields:
            fea_val_op = feature_row.get('fea_id') or feature_row.get('zfea_id')
            if fea_val_op and str(fea_val_op).strip():
                fea_str = str(fea_val_op).strip()
                op = Operation.objects.filter(fea_id=fea_str).first()
                created = False
                if op is None:
                    op = Operation.objects.create(fea_id=fea_str)
                    created = True
                changed = created
                field_log = []
                if created:
                    field_log.append(f'fea_id: None -> {fea_str!r}')
                for db_field, val in op_fields.items():
                    if db_field == 'fea_id':
                        continue
                    attr = db_field
                    if fk_fields.get('operation', {}).get(db_field):
                        attr = db_field + '_id'
                    old_val = getattr(op, attr, None)
                    if old_val != val:
                        setattr(op, attr, val)
                        changed = True
                        field_log.append(f'{db_field}: {old_val!r} -> {val!r}')
                if changed:
                    op.save()
                    updated_records.append(
                        f'operation {op.op_id}: {"; ".join(field_log)}'
                    )

        # Update compartments fields (match by compartment FK from polygon)
        comp_fields = val_by_field.get('compartments', {})
        if comp_fields and polygon.compartment_id:
            comp = Compartments.objects.filter(compartment=polygon.compartment_id).first()
            if comp:
                changed = False
                field_log = []
                for db_field, val in comp_fields.items():
                    attr = db_field
                    if fk_fields.get('compartments', {}).get(db_field):
                        attr = db_field + '_id'
                    old_val = getattr(comp, attr, None)
                    if old_val != val:
                        setattr(comp, attr, val)
                        changed = True
                        field_log.append(f'{db_field}: {old_val!r} -> {val!r}')
                if changed:
                    comp.save()
                    updated_records.append(
                        f'compartments {comp.compartment}: {"; ".join(field_log)}'
                    )

    for line in updated_records:
        logger.info(
            f'write_shapefile_attributes_to_db [proposal {proposal.id}]: {line}'
        )
    logger.info(
        f'write_shapefile_attributes_to_db: updated {updated_count} records '
        f'for proposal {proposal.id}'
    )
    return updated_count > 0

