from rest_framework import serializers
from django.contrib.auth.models import User

from silrec.components.proposals.models import (
    ApplicationType,
)



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
    name = serializers.CharField()
    #confirmation_text = serializers.CharField()

    class Meta:
        model = ApplicationType
        fields = "__all__"
        #read_only_fields = ["name", "confirmation_text"]
        read_only_fields = ["name"]

class ApplicationTypeKeyValueSerializer(serializers.ModelSerializer):
    name_display = serializers.SerializerMethodField()
        
    class Meta:
        model = ApplicationType
        fields = ["id", "name"]
        read_only_fields = ["id", "name"]

    def get_name_display(self, obj):
        #return obj.get_name_display()
        return obj.name

