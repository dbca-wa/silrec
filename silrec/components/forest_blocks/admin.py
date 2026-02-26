from django.contrib import admin
from django.conf import settings

import reversion
from silrec.components.forest_blocks.models import (
    Polygon,
    Cohort,
    AssignChtToPly,
)

admin.autodiscover()

#@admin.register(Polygon)
#class PolygonAdmin(admin.ModelAdmin):
#    list_display = ["polygon_id"]

@admin.register(Polygon)
class PolygonAdmin(reversion.admin.VersionAdmin):
    #list_display = ['polygon_id', 'name', 'proposal']  # your fields
    list_display = ['polygon_id', 'name']  # your fields

@admin.register(Cohort)
class CohortAdmin(reversion.admin.VersionAdmin):
    list_display = ['cohort_id', 'obj_code', 'species']

@admin.register(AssignChtToPly,)
class AssignChtToPlyAdmin(reversion.admin.VersionAdmin):
    list_display = ['cht2ply_id', 'polygon', 'cohort']

#admin.site.register(Polygon, PolygonAdmin)
#admin.site.register(Cohort, CohortAdmin)
#admin.site.register(AssignChtToPly, AssignChtToPlyAdmin)


