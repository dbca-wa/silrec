from datetime import date, datetime, timedelta
import json

from django.core.files.storage import default_storage
from django.db import connection
from django.shortcuts import get_object_or_404, render
from django.views import View

from silrec.components.forest_blocks.models import Polygon


# Nested follow graph from a polygon. Each entry:
# (journal table, live table, key column, link column, key-set name, label).
# `link_col` is the column in this table that references one of the resolved
# key sets (see _resolve_related_keys). Depth 1 (direct to polygon) through
# depth 4 (treatment -> prescription/xtra, cohort -> vrp).
RELATED = [
    ('assign_cht_to_ply_jn', 'assign_cht_to_ply', 'cht2ply_id', 'polygon_id', 'polygon', 'Cohort assignment'),
    ('cohort_jn', 'cohort', 'cohort_id', 'cohort_id', 'cohort', 'Cohort'),
    ('operation_jn', 'operation', 'op_id', 'op_id', 'op', 'Operation'),
    ('treatment_jn', 'treatment', 'treatment_id', 'cohort_id', 'cohort', 'Treatment'),
    ('cohort_xtra_jn', 'cohort_xtra', 'cohort_extra_id', 'cohort_id', 'cohort', 'Cohort extra'),
    ('cohort_result_jn', 'cohort_result', 'cr_id', 'cohort_id', 'cohort', 'Cohort result'),
    ('treatment_xtra_jn', 'treatment_xtra', 'treatment_xtra_id', 'treatment_id', 'treatment', 'Treatment extra'),
    ('prescription_jn', 'prescription', 'prescription_id', 'prescription_id', 'prescription', 'Prescription'),
    ('veg_ret_patch_jn', 'veg_ret_patch', 'vrp_id', 'vrp_id', 'vrp', 'Veg retention patch'),
]


class PolygonJournalHistoryView(View):
    """Server-rendered history + compare for a single Polygon using the
    Postgres journal tables (polygon_jn) rather than django-reversion.

    The ply_jn_func trigger records the OLD values of each row on UPDATE and
    DELETE (INSERT is not recorded). Each journal row is therefore a snapshot
    of the polygon at the moment before a change. The "current" state is read
    from the live polygon table.

    The comparison also "follows" the polygon's reverse FKs (cohort
    assignment, cohort, treatment, operation) and lists any related journal
    entries within a window of the selected snapshot's timestamp.
    """

    template_name = 'silrec/polygon_journal_history.html'

    # Fields written by ply_jn_func (excluding polygon_id, which is the key).
    JOURNAL_FIELDS = [
        'name', 'compartment', 'area_ha', 'sp_code',
        'created_on', 'created_by', 'updated_on', 'updated_by',
    ]

    # Subset of JOURNAL_FIELDS that carry real data (updated_on/updated_by are
    # bumped on every UPDATE, so they are excluded when detecting "noise"
    # records produced by changes to non-journaled columns).
    DATA_FIELDS = ['name', 'compartment', 'area_ha', 'sp_code', 'created_on', 'created_by']

    # Binary file fields that store a path under default_storage (MEDIA_ROOT)
    # and can be rendered as links when the underlying file still exists.
    FILE_FIELDS = {'silvic_plan_map', 'silvic_plan_doc'}

    def get(self, request, polygon_id):
        polygon = get_object_or_404(Polygon, pk=polygon_id)

        geom_geojson, geom_summary = self._current_geometry(polygon)

        records = self._journal_records(polygon_id)

        exclude_nontracked = request.GET.get('exclude_nontracked', '1') == '1'
        if exclude_nontracked:
            records = self._filter_nontracked(records, polygon)

        action_list = [
            {
                'key': self._record_key(r),
                'operation': r['jn_operation'],
                'date': r['jn_date'],
                'db_user': r['jn_db_user'],
            }
            for r in records
        ]

        version = request.GET.get('version')
        to_version = request.GET.get('to_version')
        updates_only = 'updates_only' in request.GET
        compare_with_current_only = request.GET.get('compare_with_current_only', '1') == '1'
        single_record = len(action_list) <= 1
        if single_record:
            compare_with_current_only = True

        # Default the "From" selection on first load (no explicit version in the
        # URL): with a single record select the only one, otherwise select the
        # second record (skip the most recent entry, which is often a noise
        # record with no tracked data change).
        if not version and action_list:
            default_index = 0 if single_record else 1
            version = action_list[default_index]['key']
        try:
            window_days = int(request.GET.get('window_days', '1'))
        except (TypeError, ValueError):
            window_days = 1

        compare = None
        related = []
        if version:
            compare = self._compare(
                polygon, records, version, to_version,
                updates_only, compare_with_current_only,
            )
            if compare:
                related = self._related_changes(polygon_id, compare['from_meta']['date'], window_days)

        return render(request, self.template_name, {
            'polygon': polygon,
            'action_list': action_list,
            'version': version,
            'to_version': to_version,
            'updates_only': updates_only,
            'updates_checked': updates_only or not version,
            'compare_with_current_only': compare_with_current_only,
            'compare_with_current_checked': compare_with_current_only,
            'single_record': single_record,
            'exclude_nontracked': exclude_nontracked,
            'compare': compare,
            'related': related,
            'window_days': window_days,
            'geom_geojson': geom_geojson,
            'geom_summary': geom_summary,
        })

    def _journal_records(self, polygon_id):
        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT jn_operation, jn_date, jn_db_user, name,
                       compartment, area_ha, sp_code, created_on, created_by,
                       updated_on, updated_by
                FROM silrec.polygon_jn
                WHERE polygon_id = %s
                ORDER BY jn_date DESC
                """,
                [polygon_id],
            )
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    @staticmethod
    def _record_key(record):
        # jn_date has microsecond precision; format it URL-safely and uniquely.
        return record['jn_date'].strftime('%Y%m%d%H%M%S%f')

    def _filter_nontracked(self, records, polygon):
        """Remove journal records whose tracked data fields are unchanged from
        the newer snapshot. Those records were produced by updates to
        non-journaled columns (geom, layer, path, ...), so they carry no
        visible tracked change."""
        current_values = self._current_polygon_values(polygon)
        kept = []
        for i, record in enumerate(records):
            newer = current_values if i == 0 else records[i - 1]
            if not self._data_equal(record, newer):
                kept.append(record)
        return kept

    def _data_equal(self, a, b):
        for f in self.DATA_FIELDS:
            if self._norm(a.get(f)) != self._norm(b.get(f)):
                return False
        return True

    def _compare(self, polygon, records, version, to_version, updates_only, compare_with_current_only):
        from_record = next(
            (r for r in records if self._record_key(r) == version), None
        )
        if from_record is None:
            return None

        if compare_with_current_only or not to_version:
            to_values = self._current_polygon_values(polygon)
            to_meta = {'is_current': True, 'operation': None, 'date': None, 'user': None}
        else:
            to_record = next(
                (r for r in records if self._record_key(r) == to_version), None
            )
            if to_record is None:
                to_values = self._current_polygon_values(polygon)
                to_meta = {'is_current': True, 'operation': None, 'date': None, 'user': None}
            else:
                to_values = {f: to_record[f] for f in self.JOURNAL_FIELDS}
                to_meta = {
                    'is_current': False,
                    'operation': to_record['jn_operation'],
                    'date': to_record['jn_date'],
                    'user': to_record['jn_db_user'],
                }

        from_values = {f: from_record[f] for f in self.JOURNAL_FIELDS}

        changes = []
        for f in self.JOURNAL_FIELDS:
            old = self._norm(from_values.get(f))
            new = self._norm(to_values.get(f))
            if old != new:
                if updates_only and old is None:
                    continue
                changes.append({
                    'field': f,
                    'label': self._field_label(f),
                    'old': old,
                    'new': new,
                })

        return {
            'from_meta': {
                'operation': from_record['jn_operation'],
                'date': from_record['jn_date'],
                'user': from_record['jn_db_user'],
            },
            'to_meta': to_meta,
            'changes': changes,
        }

    def _resolve_related_keys(self, polygon_id):
        """Resolve key sets for every level of the nested FK graph from the
        live tables (current linkage): polygon -> assign_cht_to_ply -> cohort /
        operation -> treatment / prescription / vrp."""
        keys = {'polygon': [int(polygon_id)]}
        with connection.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT cohort_id FROM silrec.assign_cht_to_ply "
                "WHERE polygon_id = %s AND cohort_id IS NOT NULL", [polygon_id])
            cohort = [r[0] for r in cur.fetchall()]
            keys['cohort'] = cohort

            cur.execute(
                "SELECT DISTINCT op_id FROM silrec.assign_cht_to_ply "
                "WHERE polygon_id = %s AND op_id IS NOT NULL", [polygon_id])
            ops = [r[0] for r in cur.fetchall()]

            treatment, prescription, vrp = [], [], []
            if cohort:
                cur.execute(
                    "SELECT DISTINCT op_id FROM silrec.cohort "
                    "WHERE cohort_id = ANY(%s) AND op_id IS NOT NULL", [cohort])
                ops.extend(r[0] for r in cur.fetchall())
                cur.execute(
                    "SELECT DISTINCT treatment_id FROM silrec.treatment "
                    "WHERE cohort_id = ANY(%s) AND treatment_id IS NOT NULL", [cohort])
                treatment = [r[0] for r in cur.fetchall()]
                cur.execute(
                    "SELECT DISTINCT prescription_id FROM silrec.treatment "
                    "WHERE cohort_id = ANY(%s) AND prescription_id IS NOT NULL", [cohort])
                prescription = [r[0] for r in cur.fetchall()]
                cur.execute(
                    "SELECT DISTINCT vrp_id FROM silrec.cohort "
                    "WHERE cohort_id = ANY(%s) AND vrp_id IS NOT NULL", [cohort])
                vrp = [r[0] for r in cur.fetchall()]

            keys['op'] = sorted(set(ops))
            keys['treatment'] = treatment
            keys['prescription'] = prescription
            keys['vrp'] = vrp
        return keys

    def _related_changes(self, polygon_id, timestamp, window_days=1):
        """Find journal entries in the nested related (reverse-FK) tables within
        `window_days` of `timestamp`, each diffed against its live row."""
        keys = self._resolve_related_keys(polygon_id)
        window = timedelta(days=window_days)
        start = timestamp - window
        end = timestamp + window
        exclude = {'jn_operation', 'jn_date', 'jn_db_user', 'updated_on', 'updated_by'}

        # (jn_table, live_table, key_col, label, [(link_col, key_set), ...])
        entries = [
            ('silviculturist_comment_jn', 'silviculturist_comment', 's_comment_id', 'Comment',
             [('polygon_id', 'polygon'), ('cohort_id', 'cohort'), ('op_id', 'op'), ('treatment_id', 'treatment')]),
        ]
        entries += [
            (jn_table, live_table, key_col, label, [(link_col, key_set)])
            for (jn_table, live_table, key_col, link_col, key_set, label) in RELATED
        ]

        results = []
        with connection.cursor() as cur:
            for jn_table, live_table, key_col, label, links in entries:
                results.extend(self._query_related(
                    cur, jn_table, live_table, key_col, label, links,
                    keys, start, end, exclude))
        return results

    def _query_related(self, cur, jn_table, live_table, key_col, label, links, keys, start, end, exclude):
        conds, params = [], []
        for link_col, key_set in links:
            vals = keys[key_set]
            if not vals:
                continue
            conds.append(f'{link_col} = ANY(%s)')
            params.append(vals)
        if not conds:
            return []
        where = ' OR '.join(conds)

        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'silrec' AND table_name = %s", [jn_table])
        jn_cols = [r[0] for r in cur.fetchall()]
        tracked = [c for c in jn_cols if c not in exclude and c != key_col]

        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'silrec' AND table_name = %s", [live_table])
        live_cols = {r[0] for r in cur.fetchall()}
        tracked = [c for c in tracked if c in live_cols]
        if not tracked:
            return []

        sql = (
            f"SELECT DISTINCT jn_operation, jn_date, jn_db_user, {key_col}, {', '.join(tracked)} "
            f"FROM silrec.{jn_table} "
            f"WHERE ({where}) AND jn_date >= %s AND jn_date <= %s "
            f"ORDER BY jn_date DESC"
        )
        cur.execute(sql, params + [start, end])
        cols = [c[0] for c in cur.description]
        out = []
        for row in cur.fetchall():
            rec = dict(zip(cols, row))
            key = rec[key_col]
            cur.execute(
                f"SELECT {', '.join(tracked)} FROM silrec.{live_table} WHERE {key_col} = %s", [key])
            live_row = cur.fetchone()
            changes = []
            if live_row is None:
                status = 'deleted'
            else:
                status = 'updated'
                live_vals = dict(zip(tracked, live_row))
                for f in tracked:
                    old = self._norm(rec.get(f))
                    new = self._norm(live_vals.get(f))
                    if old != new:
                        change = {
                            'field': f,
                            'label': self._humanize(f),
                            'old': old,
                            'new': new,
                        }
                        if f in self.FILE_FIELDS:
                            change['old_url'] = self._file_url(old)
                            change['new_url'] = self._file_url(new)
                        changes.append(change)
            if status == 'updated' and not changes:
                continue
            out.append({
                'table': label,
                'key_col': key_col,
                'key': key,
                'operation': rec['jn_operation'],
                'date': rec['jn_date'],
                'date_str': self._fmt_ts(rec['jn_date']),
                'db_user': rec['jn_db_user'],
                'status': status,
                'changes': changes,
            })
        return out

    @staticmethod
    def _current_geometry(polygon):
        """Serialize the polygon's CURRENT geometry to GeoJSON (reprojected to
        EPSG:4326 for Leaflet) plus a human summary. Returns (geojson, summary)
        or (None, None) when the polygon has no geometry / it is unserializable."""
        if polygon.geom is None:
            return None, None
        try:
            geojson = json.dumps(json.loads(polygon.geom.transform(4326, clone=True).geojson))
        except Exception:
            return None, None
        try:
            summary = f'{polygon.geom.geom_type}, {polygon.geom.num_geom} feature(s), {polygon.geom.area / 10000.0:.2f} ha'
        except Exception:
            summary = polygon.geom.geom_type
        return geojson, summary

    @staticmethod
    def _fmt_ts(value):
        if isinstance(value, datetime):
            return value.strftime('%d %b %Y, %I:%M:%S %p')
        if isinstance(value, date):
            return value.strftime('%d %b %Y')
        return str(value)

    @staticmethod
    def _humanize(field):
        return field.replace('_', ' ').strip()

    def _current_polygon_values(self, polygon):
        return {
            'name': polygon.name,
            'compartment': polygon.compartment_id,
            'area_ha': polygon.area_ha,
            'sp_code': polygon.sp_code_id,
            'created_on': polygon.created_on,
            'created_by': polygon.created_by,
            'updated_on': polygon.updated_on,
            'updated_by': polygon.updated_by,
        }

    @staticmethod
    def _field_label(field):
        try:
            return Polygon._meta.get_field(field).verbose_name
        except Exception:
            return field

    @staticmethod
    def _norm(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, (bytes, memoryview)):
            # bytea columns (silvic_plan_map/silvic_plan_doc) come back as
            # memoryview from psycopg2 and would otherwise render as
            # "<memory at 0x...>". They store UTF-8 file paths, so decode them.
            raw = bytes(value)
            try:
                text = raw.decode('utf-8').strip()
                return text or None
            except UnicodeDecodeError:
                return f'(binary data, {len(raw)} bytes)'
        if isinstance(value, str):
            value = value.strip()
            return value if value != '' else None
        if isinstance(value, float):
            return round(value, 4)
        return value

    @staticmethod
    def _file_url(value):
        """Return a storage URL for a file-field path, or None when the file no
        longer exists (so the template renders it as plain, unclickable text)."""
        if not value:
            return None
        try:
            if default_storage.exists(value):
                return default_storage.url(value)
        except Exception:
            pass
        return None
