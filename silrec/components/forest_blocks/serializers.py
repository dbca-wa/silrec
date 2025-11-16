from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.auth.models import User
from silrec.components.forest_blocks.models import Polygon, Cohort, Treatment, Compartments, AssignChtToPly

class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
#        fields = (
#            'treatment_id',
#            'prescription_id',
#            'cohort_id',
#        )
        fields = '__all__'


class PolygonSerializer(serializers.ModelSerializer):
    ''' http://localhost:8001/api/polygon.json
        http://localhost:8001/api/polygon
    '''
    class Meta:
        model = Polygon
#        fields = (
#            'polygon_id',
#            'name',
#        )
        fields = '__all__'


class CompartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compartments
        fields = '__all__'


class PolygonGeometrySerializer(GeoFeatureModelSerializer):
    compartments = CompartmentsSerializer(source='compartment', many=False)

    class Meta:
        model = Polygon
        geo_field = "geom"
        fields = (
            "polygon_id",
            "name",
            "area_ha",
            "created_on",
            "created_by",
            "closed",
            "reason_closed",
            "zfea_id",
            "compartments",
            "geom",
        )
        read_only_fields = ("polygon_id",)


class Polygon2Serializer(serializers.ModelSerializer):
    ''' http://localhost:8001/api/polygon2.json
        http://localhost:8001/api/polygon2
    '''
    #cohorts = serializers.SerializerMethodField()
    polygongeometry = PolygonGeometrySerializer(many=True, read_only=True)

    def get_cohorts(self,obj):
        assignchttoply_qs = obj.assignchttoply_set.all()
        cohorts = [cohort.cohort for cohort in assignchttoply_qs] # map to cohort objects
        #import ipdb; ipdb.set_trace()
        #serializer = CohortSerializer(cohorts, many=True)
        serializer = SimpleCohortSerializer(cohorts, many=True)

        return serializer.data

    class Meta:
        model = Polygon
        fields = "__all__"
#        extra_fields = [
#            "polygongeometry",
#        ]
#        fields = (
#            #'polygon_id',
#            #'name',
#            #'cohorts',
#            'polygongeometry',
#        )
        datatables_always_serialize = (
            'polygon_id',
            'name',
            #'cohorts',
            'polygongeometry',
        )



class CohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        #fields = ['id', 'first_name', 'last_name', 'email']
        fields = '__all__'


class SimpleCohortSerializer(serializers.ModelSerializer):
    treatments = TreatmentSerializer(source='treatment_set', many=True)

    class Meta:
        model = Cohort
        #fields = '__all__'
        fields = (
			"obj_code",
			"op_id",
			"op_date",
			"pct_area",
			"year_last_cut",
			"regen_date",

			"treatments",
        )

class PolygonCohortSerializer(serializers.ModelSerializer):
    polygon = PolygonSerializer()
    cohort = CohortSerializer()

    class Meta:
        model = AssignChtToPly
        fields = (
            'cht2ply_id',
            'polygon',
            'cohort',
            #'polygon_id',
            #'cohort_id',
        )


class UserSerializerSimple(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "last_name", "first_name", "email", "full_name")

    def get_full_name(self, obj):
        return obj.get_full_name()


# 16-Nov-2025 -------------------

from silrec.components.forest_blocks.models import Polygon, AssignChtToPly, Cohort

#class CohortDataSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Cohort
#        fields = (
#            'cohort_id',
#            'obj_code',
#            'target_ba_m2ha',
#            'resid_ba_m2ha',
#            'target_spha',
#            'resid_spha',
#            'species',
#            'regen_method',
#            'site_quality'
#        )
#
#class AssignChtToPlySerializer(serializers.ModelSerializer):
#    cohort_details = CohortDataSerializer(source='cohort', read_only=True)
#
#    class Meta:
#        model = AssignChtToPly
#        fields = (
#            'cht2ply_id',
#            'cohort',
#            'cohort_details',
#            'cohort_closed',
#            'status_current',
#            'created_on',
#            'updated_on'
#        )
#
#class PolygonCohortDataSerializer(serializers.ModelSerializer):
#    assigned_cohorts = serializers.SerializerMethodField()
#    proposal_id = serializers.IntegerField(source='proposal.id', read_only=True)
#
#    class Meta:
#        model = Polygon
#        fields = (
#            'polygon_id',
#            'proposal_id',
#            'name',
#            'compartment',
#            'area_ha',
#            'zfea_id',
#            'created_on',
#            'updated_on',
#            'assigned_cohorts'
#        )
#
#    def get_assigned_cohorts(self, obj):
#        assigned_cht = AssignChtToPly.objects.filter(
#            polygon=obj,
#            status_current=True
#        ).select_related('cohort')
#        return AssignChtToPlySerializer(assigned_cht, many=True).data

class CohortDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cohort
        fields = (
            'cohort_id',
            'obj_code',
            'target_ba_m2ha',
            'resid_ba_m2ha',
            'target_spha',
            'resid_spha',
            'species',
            'regen_method',
            'site_quality',
            'regen_date',
            'complete_date'
        )

class AssignChtToPlySerializer(serializers.ModelSerializer):
    cohort_details = CohortDataSerializer(source='cohort', read_only=True)

    class Meta:
        model = AssignChtToPly
        fields = (
            'cht2ply_id',
            'cohort',
            'cohort_details',
            'cohort_closed',
            'status_current',
            'created_on',
            'updated_on'
        )

class PolygonCohortDataSerializer(serializers.ModelSerializer):
    assigned_cohorts = serializers.SerializerMethodField()
    proposal_id = serializers.IntegerField(source='proposal.id', read_only=True)

    class Meta:
        model = Polygon
        fields = (
            'polygon_id',
            'proposal_id',
            'name',
            'compartment',
            'area_ha',
            'zfea_id',
            'created_on',
            'updated_on',
            'assigned_cohorts'
        )

    def get_assigned_cohorts(self, obj):
        # Use the correct related name
        assigned_cht = obj.assignchttoply_set.filter(status_current=True).select_related('cohort')
        return AssignChtToPlySerializer(assigned_cht, many=True).data


