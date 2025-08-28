import datetime
import logging

from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from leaseslicensing.components.main.serializers import (
    UserSerializerSimple,
    ApplicationTypeSerializer,
    #CommunicationLogEntrySerializer,
    #EmailUserSerializer,
)
from leaseslicensing.components.proposals.models import (
    AmendmentRequest,
    Proposal,
    ProposalGeometry,
    ProposalType,
    #ProposalUserAction,
    #Referral,
    #SectionChecklist,
)


class ProposalTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalType
        fields = (
            "id",
            "code",
            "description",
        )

    def get_activities(self, obj):
        return obj.activities.names()


class BaseProposalSerializer(serializers.ModelSerializer):
    proposal_type = ProposalTypeSerializer()
    application_type = ApplicationTypeSerializer()
    #accessing_user_roles = serializers.SerializerMethodField()
    proposalgeometry = ProposalGeometrySerializer(many=True, read_only=True)
    #applicant = serializers.SerializerMethodField()
    lodgement_date_display = serializers.SerializerMethodField()
    #applicant = serializers.SerializerMethodField()
    applicant = UserSerializerSimple()
    #groups = serializers.SerializerMethodField(read_only=True)
    #allowed_assessors = EmailUserSerializer(many=True)
    #details_url = serializers.SerializerMethodField(read_only=True)
    readonly = serializers.SerializerMethodField(read_only=True)
    #approval = serializers.SerializerMethodField(read_only=True, allow_null=True)
    # Gis data fields
#    identifiers = serializers.SerializerMethodField()
#    names = serializers.SerializerMethodField()
#    acts = serializers.SerializerMethodField()
#    tenures = serializers.SerializerMethodField()
#    categories = serializers.SerializerMethodField()
#    regions = serializers.SerializerMethodField()
#    districts = serializers.SerializerMethodField()
#    lgas = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
            "id",
            #"allowed_assessors",
            "application_type",
            "applicant",
            "proposal_type",
            "title",
            "processing_status",
            "applicant",
            "submitter",
            #"assigned_officer",
            "previous_application",
            #"get_history",
            "lodgement_date",
            "lodgement_number",
            #"supporting_documents",
            #"requirements",
            "readonly",
            #"approval",
#            "can_user_edit",
#            "can_user_view",
#            "documents_url",
#            "reference",
#            "can_officer_process",
#            "accessing_user_roles",
#            "added_internally",
#            "details_text",
#            "proposalgeometry",
#            "groups",
#            "details_url",
        )
        #read_only_fields = ("supporting_documents",)

#    def get_groups(self, obj):
#        group_ids = obj.groups.values_list("group__id", flat=True)
#        group_qs = Group.objects.filter(id__in=group_ids).values("id", "name")
#        return GroupSerializer(group_qs, many=True).data

    def get_lodgement_date_display(self, obj):
        if obj.lodgement_date:
            return (
                obj.lodgement_date.strftime("%d/%m/%Y")
                + " at "
                + obj.lodgement_date.strftime("%-I:%M %p")
            )

#    def get_applicant(self, obj):
#        if isinstance(obj.applicant, Organisation):
#            return obj.applicant.ledger_organisation_name
#        elif isinstance(obj.applicant, ProposalApplicant):
#            return obj.applicant.full_name
#        elif isinstance(obj.applicant, EmailUser):
#            return f"{obj.applicant.first_name} {obj.applicant.last_name}"
#        else:
#            return "Applicant not yet assigned"

#    def get_applicant(self, obj):
#        return UserSerializerSimple(obj.applicant).data

#    def get_documents_url(self, obj):
#        return "/media/{}/proposals/{}/documents/".format(
#            settings.MEDIA_APP_DIR, obj.id
#        )

    def get_readonly(self, obj):
        return False

    def get_processing_status(self, obj):
        return obj.get_processing_status_display()

#    def get_accessing_user_roles(self, proposal):
#        request = self.context.get("request")
#        accessing_user = request.user
#        roles = []
#
#        for choice in GROUP_NAME_CHOICES:
#            group = SystemGroup.objects.get(name=choice[0])
#            ids = group.get_system_group_member_ids()
#            if accessing_user.id in ids:
#                roles.append(group.name)
#
#        referral_ids = list(proposal.referrals.values_list("referral", flat=True))
#        if accessing_user.id in referral_ids:
#            roles.append("referral")
#
#        return roles



