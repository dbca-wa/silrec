import json
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from django.shortcuts import get_object_or_404, render
from django.views import View

from reversion.models import Version

from silrec.components.proposals.models import Proposal


class ProposalHistoryCompareView(View):
    """Server-rendered reversion history + compare for a single Proposal.

    Shows the version history (date/user/comment) with radio buttons to pick
    two versions, then compares them — listing only the fields that changed,
    grouped by table (Proposal plus any followed related models).
    """

    template_name = 'silrec/reversion_history.html'
    model = Proposal

    def get(self, request, pk):
        proposal = get_object_or_404(self.model, pk=pk)

        versions = Version.objects.get_for_object(proposal).select_related(
            'revision', 'revision__user'
        ).order_by('-revision__date_created')

        action_list = [
            {
                'version_id': v.id,
                'date': v.revision.date_created,
                'user': v.revision.user,
                'comment': v.revision.comment or '',
            }
            for v in versions
        ]

        current_version = versions.first()
        current_id = current_version.id if current_version else None
        version_id = request.GET.get('version_id')
        to_version_id = request.GET.get('to_version_id')
        updates_only = 'updates_only' in request.GET
        compare_with_current_only = request.GET.get('compare_with_current_only', '1') == '1'

        effective_to_id = current_id
        if not compare_with_current_only and to_version_id:
            effective_to_id = to_version_id

        compare = None
        if version_id and effective_to_id:
            compare = self._compare(version_id, effective_to_id, updates_only)

        return render(request, self.template_name, {
            'proposal': proposal,
            'action_list': action_list,
            'current_version_id': current_id,
            'version_id': version_id,
            'to_version_id': to_version_id,
            'to_checked_id': to_version_id or (str(current_id) if current_id else None),
            'updates_only': updates_only,
            'updates_checked': updates_only or not version_id,
            'compare_with_current_only': compare_with_current_only,
            'compare_with_current_checked': compare_with_current_only,
            'compare': compare,
        })

    def _compare(self, version_id1, version_id2, updates_only=True):
        v1 = Version.objects.filter(pk=version_id1).select_related(
            'revision', 'revision__user', 'content_type'
        ).first()
        v2 = Version.objects.filter(pk=version_id2).select_related(
            'revision', 'revision__user', 'content_type'
        ).first()
        if v1 is None or v2 is None:
            return None

        objs1 = {
            (x.content_type_id, x.object_id): x
            for x in Version.objects.filter(revision=v1.revision).select_related('content_type')
        }
        objs2 = {
            (x.content_type_id, x.object_id): x
            for x in Version.objects.filter(revision=v2.revision).select_related('content_type')
        }

        tables = defaultdict(list)
        geometry = []
        for key in sorted(set(objs1) | set(objs2)):
            a = objs1.get(key)
            b = objs2.get(key)
            version = b or a
            model_class = version.content_type.model_class()
            table = self._table_label(version.content_type, model_class)

            changes = []
            if a is None:
                # Object present only in current (added).
                if not updates_only:
                    for f, val in (b.field_dict or {}).items():
                        changes.append(self._change(model_class, f, None, self._display_value(f, val)))
            elif b is None:
                # Object present only in selected version (removed).
                for f, val in (a.field_dict or {}).items():
                    old = self._display_value(f, val)
                    if updates_only and old is None:
                        continue
                    changes.append(self._change(model_class, f, old, None))
            else:
                old_d = a.field_dict or {}
                new_d = b.field_dict or {}
                for f in sorted(set(old_d) | set(new_d)):
                    raw_o = old_d.get(f)
                    raw_n = new_d.get(f)
                    if self._norm(raw_o) != self._norm(raw_n):
                        o = self._display_value(f, raw_o)
                        n = self._display_value(f, raw_n)
                        if updates_only and o is None:
                            continue
                        changes.append(self._change(model_class, f, o, n))
                        if self._is_geometry(f, raw_o, raw_n):
                            old_gj = self._geojson_payload(raw_o)
                            new_gj = self._geojson_payload(raw_n)
                            if old_gj or new_gj:
                                label = f
                                if model_class is not None:
                                    try:
                                        label = model_class._meta.get_field(f).verbose_name
                                    except Exception:
                                        pass
                                geometry.append({
                                    'field': f,
                                    'label': label,
                                    'object': version.object_repr,
                                    'old_geojson': old_gj,
                                    'new_geojson': new_gj,
                                    'old_summary': o,
                                    'new_summary': n,
                                })

            if changes:
                tables[table].append({
                    'object': version.object_repr,
                    'changes': changes,
                })

        return {
            'selected': {'date': v1.revision.date_created, 'user': v1.revision.user},
            'current': {'date': v2.revision.date_created, 'user': v2.revision.user},
            'tables': dict(tables),
            'geometry': geometry,
        }

    @staticmethod
    def _table_label(content_type, model_class):
        if model_class is not None:
            return str(model_class._meta.verbose_name).title()
        return content_type.name.replace('_', ' ').title()

    @staticmethod
    def _change(model_class, field, old, new):
        label = field
        if model_class is not None:
            try:
                label = model_class._meta.get_field(field).verbose_name
            except Exception:
                pass
        return {'field': field, 'label': label, 'old': old, 'new': new}

    @staticmethod
    def _norm(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if value is None or value == '':
            return None
        return value

    GEOMETRY_FIELDS = {
        'shapefile_json',
        'geojson_data_hist',
        'geojson_data_processed',
        'geojson_data_processed_iters',
    }

    @staticmethod
    def _flatten_geojson(value):
        """Normalise a GeoJSON-ish value into a single FeatureCollection.

        Handles a FeatureCollection, Feature, bare geometry, and the
        `geojson_data_processed_iters` shape (a dict mapping keys to
        FeatureCollections). Returns None when the value is not geometry.
        """
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                return None
        if not isinstance(value, dict):
            return None
        if value.get('type') == 'FeatureCollection':
            return value
        if value.get('type') == 'Feature' or 'coordinates' in value:
            return {'type': 'FeatureCollection', 'features': [value]}
        features = []
        for v in value.values():
            if isinstance(v, dict) and v.get('type') == 'FeatureCollection':
                features.extend(v.get('features', []))
        if features:
            return {'type': 'FeatureCollection', 'features': features}
        return None

    @staticmethod
    def _looks_like_geojson(value):
        return ProposalHistoryCompareView._flatten_geojson(value) is not None

    def _geojson_payload(self, value):
        fc = self._flatten_geojson(value)
        if fc is None:
            return None
        return json.dumps(fc)

    def _is_geometry(self, field, old, new):
        return (
            field in self.GEOMETRY_FIELDS
            or self._looks_like_geojson(old)
            or self._looks_like_geojson(new)
        )

    def _display_value(self, field, raw_value):
        if field in self.GEOMETRY_FIELDS or self._looks_like_geojson(raw_value):
            return self._geom_summary_str(raw_value)
        return self._norm(raw_value)

    @staticmethod
    def _geom_summary_str(value):
        """Summarise a GeoJSON geometry value as type / feature count / area."""
        if not value:
            return None
        try:
            from shapely.geometry import shape
            fc = ProposalHistoryCompareView._flatten_geojson(value)
            if fc is None:
                return '(geometry data)'
            geoms = [
                shape(f['geometry'])
                for f in fc.get('features', [])
                if f.get('geometry')
            ]
            if not geoms:
                return '(empty geometry)'
        except Exception:
            return '(geometry data)'

        geom_types = sorted({g.geom_type for g in geoms})
        n_features = len(geoms)

        area_ha = None
        try:
            import geopandas as gpd
            from django.conf import settings
            is_geo = True
            for g in geoms:
                minx, miny, maxx, maxy = g.bounds
                if (
                    abs(minx) > 180 or abs(maxx) > 180
                    or abs(miny) > 90 or abs(maxy) > 90
                ):
                    is_geo = False
                    break
            if is_geo:
                gdf = gpd.GeoDataFrame(geometry=geoms, crs=settings.CRS)
                gdf = gdf.to_crs(settings.CRS_GDA94)
                total = gdf.geometry.area.sum()
            else:
                total = sum(g.area for g in geoms)
            area_ha = round(total / 10000, 2)
        except Exception:
            area_ha = None

        parts = [', '.join(geom_types)]
        parts.append(f"{n_features} feature{'s' if n_features != 1 else ''}")
        if area_ha is not None:
            parts.append(f"{area_ha} ha")
        return ', '.join(parts)
