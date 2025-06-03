from rest_framework import serializers
from django.contrib.auth.models import User
from silrec.components.forest_blocks.models import Polygon, Cohort, Treatment, AssignChtToPly

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
    class Meta:
        model = Polygon
#        fields = (
#            'polygon_id',
#            'name',
#        )
        fields = '__all__'

class Polygon2Serializer(serializers.ModelSerializer):
    cohorts = serializers.SerializerMethodField()

    def get_cohorts(self,obj):
        cohort_qs = obj.assignchttoply_set.all()
        cohorts = [cohort.cohort for cohort in cohort_qs]
        #return cohort_qs
        import ipdb; ipdb.set_trace()
        serializer = CohortSerializer(cohorts, many=True)

        return serializer.data

    class Meta:
        model = Polygon
        fields = (
            'polygon_id',
            'name',
            'cohorts',
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


