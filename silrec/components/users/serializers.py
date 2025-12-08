from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email']

class UserSerializerSimple(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "last_name", "first_name", "email", "full_name")

    def get_full_name(self, obj):
        return obj.get_full_name()


class SearchByUserRequestSerializer(serializers.Serializer):
    """Serializer for user search request parameters"""
    from silrec.components.proposals.serializers import FlexibleDateField, JSONStringField
    user_id = serializers.IntegerField(required=True, min_value=1)
    search_mode = serializers.ChoiceField(
        choices=['created_by', 'updated_by', 'submitted_by', 'assigned_to', 'referral', 'all'],
        default='all'
    )
    model_type = serializers.ChoiceField(
        choices=[
            'all', 'proposal', 'polygon', 'cohort', 'treatment',
            'treatment_xtra', 'survey_assessment_document',
            'silviculturist_comment', 'prescription'
        ],
        default='all'
    )
    date_from = FlexibleDateField(required=False, allow_null=True, default=None)
    date_to = FlexibleDateField(required=False, allow_null=True, default=None)
    include_inactive = serializers.BooleanField(default=False)

    # Datatable parameters
    draw = serializers.IntegerField(required=False, default=1, min_value=0)
    start = serializers.IntegerField(required=False, default=0, min_value=0)
    length = serializers.IntegerField(required=False, default=25, min_value=1, max_value=1000)
    order = JSONStringField(required=False, default=[])
    search = JSONStringField(required=False, default={})

    def validate(self, data):
        """Additional validation for date range"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                "date_from": "Date From cannot be after Date To",
                "date_to": "Date To cannot be before Date From"
            })

        return data


class SearchByUserResultSerializer(serializers.Serializer):
    """Serializer for user search results"""
    model_type = serializers.CharField()
    record_id = serializers.IntegerField()
    user_role = serializers.CharField()
    user_role_display = serializers.CharField()
    title = serializers.CharField(allow_null=True, allow_blank=True)
    status = serializers.CharField(allow_null=True, allow_blank=True)
    status_display = serializers.CharField(allow_null=True, allow_blank=True)
    created_on = serializers.DateTimeField(allow_null=True)
    action_url = serializers.CharField()
    user_name = serializers.CharField()
    user_email = serializers.EmailField()

