from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import F, JSONField, Max, Min, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers
from reversion.models import Version

from dirtyfields import DirtyFieldsMixin

from silrec.components.main.models import (
    Document,
    ApplicationType,
    SecureFileField,
    RevisionedMixin,
)


def update_proposal_doc_filename(instance, filename):
    return f"proposals/{instance.proposal.id}/documents/{filename}"

def update_proposal_comms_log_filename(instance, filename):
    return f"proposals/{instance.log_entry.proposal.id}/{filename}"

class DefaultDocument(Document):
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    visible = models.BooleanField(
        default=True
    )  # to prevent deletion on file system, hidden and still be available in history

    class Meta:
        app_label = "silrec"
        abstract = True

    def delete(self):
        if self.can_delete:
            return super().delete()
        logger.info(
            "Cannot delete existing document object after Application has been submitted "
            "(including document submitted before Application pushback to status Draft): {}".format(
                self.name
            )
        )

class ProposalDocument(Document):
    proposal = models.ForeignKey(
        "Proposal", related_name="supporting_documents", on_delete=models.CASCADE
    )
    _file = SecureFileField(upload_to=update_proposal_doc_filename, max_length=512)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    class Meta:
        app_label = "silrec"
        verbose_name = "Application Document"


class ShapefileDocumentQueryset(models.QuerySet):
    """Using a custom manager to make sure shapfiles are removed when a bulk .delete is called
    as having multiple files with the shapefile extensions in the same folder causes issues.
    """

    def delete(self):
        for obj in self:
            obj._file.delete()
        super().delete()


class ShapefileDocument(Document):
    objects = ShapefileDocumentQueryset.as_manager()

    proposal = models.ForeignKey(
        "Proposal", related_name="shapefile_documents", on_delete=models.CASCADE
    )
    _file = SecureFileField(upload_to=update_proposal_doc_filename, max_length=500)
    input_name = models.CharField(max_length=255, null=True, blank=True)
    can_delete = models.BooleanField(
        default=True
    )  # after initial submit prevent document from being deleted
    can_hide = models.BooleanField(
        default=False
    )  # after initial submit, document cannot be deleted but can be hidden
    hidden = models.BooleanField(
        default=False
    )  # after initial submit prevent document from being deleted

    def delete(self):
        if self.can_delete:
            self._file.delete()
            return super().delete()
        logger.info(
            "Cannot delete existing document object after Proposal has been submitted "
            "(including document submitted before Proposal pushback to status Draft): {}".format(
                self.name
            )
        )

    class Meta:
        app_label = "silrec"


class ProposalType(models.Model):
    # class ProposalType(RevisionedMixin):
    code = models.CharField(max_length=30, blank=True, null=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        # return 'id: {} code: {}'.format(self.id, self.code)
        return self.description

    class Meta:
        app_label = "silrec"


#class ProposalManager(models.Manager):
#    def get_queryset(self):
#        return (
#            super()
#            .get_queryset()
#            .select_related(
#                "proposal_type", "org_applicant", "application_type", "approval"
#            )
#        )

class Proposal(RevisionedMixin, DirtyFieldsMixin):
    #objects = ProposalManager()

    MODEL_PREFIX = "P"

    PROCESSING_STATUS_DRAFT = "draft"
    PROCESSING_STATUS_AMENDMENT_REQUIRED = "amendment_required"
    PROCESSING_STATUS_WITH_ASSESSOR = "with_assessor"
    PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS = "with_assessor_conditions"
    PROCESSING_STATUS_WITH_APPROVER = "with_approver"
    PROCESSING_STATUS_WITH_REFERRAL = "with_referral"
    PROCESSING_STATUS_APPROVED = "approved"
    PROCESSING_STATUS_DECLINED = "declined"
    PROCESSING_STATUS_DISCARDED = "discarded"
    PROCESSING_STATUS_CHOICES = (
        (PROCESSING_STATUS_DRAFT, "Draft"),
        (PROCESSING_STATUS_AMENDMENT_REQUIRED, "Amendment Required"),
        (PROCESSING_STATUS_WITH_ASSESSOR, "With Assessor"),
        (PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS, "With Assessor (Conditions)"),
        (PROCESSING_STATUS_WITH_APPROVER, "With Approver"),
        (PROCESSING_STATUS_WITH_REFERRAL, "With Referral"),
        (PROCESSING_STATUS_APPROVED, "Approved"),
        (PROCESSING_STATUS_DECLINED, "Declined"),
        (PROCESSING_STATUS_DISCARDED, "Discarded"),
    )

    # List of statuses from above that allow a customer to view a proposal (read-only)
#    CUSTOMER_VIEWABLE_STATE = [
#        PROCESSING_STATUS_WITH_ASSESSOR,
#        PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
#        PROCESSING_STATUS_WITH_REFERRAL,
#        PROCESSING_STATUS_WITH_APPROVER,
#        PROCESSING_STATUS_APPROVED_REGISTRATION_OF_INTEREST,
#        PROCESSING_STATUS_APPROVED_COMPETITIVE_PROCESS,
#        PROCESSING_STATUS_APPROVED_EDITING_INVOICING,
#        PROCESSING_STATUS_APPROVED,
#        PROCESSING_STATUS_DECLINED,
#        PROCESSING_STATUS_DISCARDED,
#    ]
#
#    OFFICER_PROCESSABLE_STATE = [
#        PROCESSING_STATUS_WITH_ASSESSOR,
#        PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
#        PROCESSING_STATUS_WITH_REFERRAL,  # <-- Be aware
#        PROCESSING_STATUS_WITH_APPROVER,
#    ]
#
    COMPLIANCE_CHECK_STATUS_CHOICES = (
        ("not_checked", "Not Checked"),
        ("awaiting_returns", "Awaiting Returns"),
        ("completed", "Completed"),
        ("accepted", "Accepted"),
    )

    REVIEW_STATUS_CHOICES = (
        ("not_reviewed", "Not Reviewed"),
        ("awaiting_amendments", "Awaiting Amendments"),
        ("amended", "Amended"),
        ("accepted", "Accepted"),
    )

    proposal_type = models.ForeignKey(
        ProposalType, blank=True, null=True, on_delete=models.SET_NULL
    )
    proposed_issuance_approval = JSONField(blank=True, null=True)
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    lodgement_date = models.DateTimeField(blank=True, null=True)
    submitter = models.IntegerField(null=True)  # EmailUserRO
#    assigned_officer = models.IntegerField(null=True)  # EmailUserRO
#    assigned_approver = models.IntegerField(null=True)  # EmailUserRO
#    approved_by = models.IntegerField(null=True)  # EmailUserRO
    processing_status = models.CharField(
        "Processing Status",
        max_length=35,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_CHOICES[0][0],
    )
    prev_processing_status = models.CharField(max_length=30, blank=True, null=True)
#    review_status = models.CharField(
#        "Review Status",
#        max_length=30,
#        choices=REVIEW_STATUS_CHOICES,
#        default=REVIEW_STATUS_CHOICES[0][0],
#    )
    previous_application = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    #proposed_decline_status = models.BooleanField(default=False)
    # Special Fields
    title = models.CharField(max_length=255, null=True, blank=True)
    application_type = models.ForeignKey(ApplicationType, on_delete=models.PROTECT)
    migrated = models.BooleanField(default=False)

    class Meta:
        app_label = "silrec"
        verbose_name = "Proposal"

    def save(self, *args, **kwargs):
        # Clear out the cached
        #cache.delete(settings.CACHE_KEY_MAP_PROPOSALS)

        # Store the original values of fields we want to keep track of in 
        # django reversion before they are overwritten by super() below
        original_processing_status = self._original_state['processing_status']
        #original_assessor_data = self._original_state['assessor_data']
        #original_comment_data = self._original_state['comment_data']

        super().save(*args, **kwargs)

        if self.lodgement_number == '':
            self.lodgement_number = 'P{0:06d}'.format(self.pk)
            self.save()

        # If the processing_status has changed then add a reversion comment
        # so we have a way of filtering based on the status changing
        if self.processing_status != original_processing_status:
            self.save(version_comment=f'processing_status: {self.processing_status}')


class AmendmentReason(models.Model):
    reason = models.CharField("Reason", max_length=125)

    class Meta:
        app_label = "silrec"
        verbose_name = "Proposal Amendment Reason"  # display name in Admin
        verbose_name_plural = "Proposal Amendment Reasons"

    def __str__(self):
        return self.reason

class ProposalRequest(models.Model):
    proposal = models.ForeignKey(
        Proposal, related_name="proposalrequest_set", on_delete=models.CASCADE
    )
    subject = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)
    # fficer = models.ForeignKey(EmailUser, null=True, on_delete=models.SET_NULL)
    officer = models.IntegerField(null=True)  # EmailUserRO

    def __str__(self):
        return f"{self.subject} - {self.text}"

    class Meta:
        app_label = "silrec"


class AmendmentRequest(ProposalRequest):
    STATUS_CHOICE_REQUESTED = "requested"
    STATUS_CHOICE_AMENDED = "amended"
    STATUS_CHOICES = (
        (STATUS_CHOICE_REQUESTED, "Requested"),
        (STATUS_CHOICE_AMENDED, "Amended"),
    )

    status = models.CharField(
        "Status", max_length=30, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    reason = models.ForeignKey(
        AmendmentReason, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        app_label = "silrec"

#    @transaction.atomic
#    def generate_amendment(self, request):
#        if not self.proposal.can_assess(request.user):
#            raise exceptions.ProposalNotAuthorized()
#
#        if self.status == AmendmentRequest.STATUS_CHOICE_REQUESTED:
#            proposal = self.proposal
#            if proposal.processing_status != Proposal.PROCESSING_STATUS_DRAFT:
#                proposal.processing_status = Proposal.PROCESSING_STATUS_DRAFT
#                proposal.save(
#                    version_comment=f"Proposal amendment requested {request.data.get('reason', '')}"
#                )
#
#                # Mark any related documents that the assessor may have attached to the proposal as not delete-able
#                self.proposal.mark_documents_not_deleteable()
#
#            # Create a log entry for the proposal
#            proposal.log_user_action(
#                ProposalUserAction.ACTION_ID_REQUEST_AMENDMENTS, request
#            )
#
#            # Create a log entry for the applicant
#            proposal.applicant.log_user_action(
#                ProposalUserAction.ACTION_REQUESTED_AMENDMENT.format(proposal.id),
#                request,
#            )
#
#            # send email
#            send_amendment_email_notification(self, request, self.proposal)
#
#        self.save()
#
#    def user_has_object_permission(self, user_id):
#        return self.proposal.user_has_object_permission(user_id)


