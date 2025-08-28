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


class ApplicationTypeSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField()
    confirmation_text = serializers.CharField()

    class Meta:
        model = ApplicationType
        fields = "__all__"
        read_only_fields = ["name_display", "confirmation_text"]


