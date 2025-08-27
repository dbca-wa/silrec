


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

class Proposal(LicensingModelVersioned, DirtyFieldsMixin):
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
    CUSTOMER_VIEWABLE_STATE = [
        PROCESSING_STATUS_WITH_ASSESSOR,
        PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
        PROCESSING_STATUS_WITH_REFERRAL,
        PROCESSING_STATUS_WITH_APPROVER,
        PROCESSING_STATUS_APPROVED_REGISTRATION_OF_INTEREST,
        PROCESSING_STATUS_APPROVED_COMPETITIVE_PROCESS,
        PROCESSING_STATUS_APPROVED_EDITING_INVOICING,
        PROCESSING_STATUS_APPROVED,
        PROCESSING_STATUS_DECLINED,
        PROCESSING_STATUS_DISCARDED,
    ]

    OFFICER_PROCESSABLE_STATE = [
        PROCESSING_STATUS_WITH_ASSESSOR,
        PROCESSING_STATUS_WITH_ASSESSOR_CONDITIONS,
        PROCESSING_STATUS_WITH_REFERRAL,  # <-- Be aware
        PROCESSING_STATUS_WITH_APPROVER,
    ]

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
    #applicant = models.IntegerField(null=True, blank=True)  # EmailUserRO
    #proxy_applicant = models.IntegerField(null=True, blank=True)  # EmailUserRO
    #lodgement_sequence = models.IntegerField(blank=True, default=0)
    lodgement_number = models.CharField(max_length=9, blank=True, default='')
    lodgement_date = models.DateTimeField(blank=True, null=True)
    submitter = models.IntegerField(null=True)  # EmailUserRO
    assigned_officer = models.IntegerField(null=True)  # EmailUserRO
    assigned_approver = models.IntegerField(null=True)  # EmailUserRO
    approved_by = models.IntegerField(null=True)  # EmailUserRO
    processing_status = models.CharField(
        "Processing Status",
        max_length=35,
        choices=PROCESSING_STATUS_CHOICES,
        default=PROCESSING_STATUS_CHOICES[0][0],
    )
    prev_processing_status = models.CharField(max_length=30, blank=True, null=True)
    review_status = models.CharField(
        "Review Status",
        max_length=30,
        choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_STATUS_CHOICES[0][0],
    )
#    approval = models.ForeignKey(
#        "leaseslicensing.Approval",
#        null=True,
#        blank=True,
#        on_delete=models.SET_NULL,
#        related_name="proposals",
#    )
    previous_application = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    #proposed_decline_status = models.BooleanField(default=False)
    # Special Fields
    title = models.CharField(max_length=255, null=True, blank=True)
    application_type = models.ForeignKey(ApplicationType, on_delete=models.PROTECT)
    approval_level = models.CharField(
        "Activity matrix approval level", max_length=255, null=True, blank=True
    )
    approval_level_document = models.ForeignKey(
        ProposalDocument,
        blank=True,
        null=True,
        related_name="approval_level_document",
        on_delete=models.SET_NULL,
    )
    approval_comment = models.TextField(blank=True)
    details_text = models.TextField(blank=True)
    added_internally = models.BooleanField(default=False)
    # If the proposal is created as part of migration of approvals
    migrated = models.BooleanField(default=False)
    original_leaselicence_number = models.CharField(
        max_length=255, blank=True, null=True
    )
    # Registration of Interest generates a Lease Licence
    generated_proposal = models.ForeignKey(
        "self",
        related_name="originating_proposal",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    # Registration of Interest generates a Competitive Process
    generated_competitive_process = models.OneToOneField(
        CompetitiveProcess,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="originating_proposal",
    )
    # Competitive Process generates a Lease Licence
    originating_competitive_process = models.ForeignKey(
        CompetitiveProcess,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_proposal",
    )
    # When adding proposal as a party to an existing competitive process
    competitive_process_to_copy_to = models.ForeignKey(
        CompetitiveProcess,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="proposals_added",
    )
    invoicing_details = models.OneToOneField(
        InvoicingDetails,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="proposal",
    )
    # Registration of Interest additional form fields
    # proposal details
    exclusive_use = models.BooleanField(null=True)
    exclusive_use_text = models.TextField(blank=True)
    long_term_use = models.BooleanField(null=True)
    long_term_use_text = models.TextField(blank=True)
    consistent_purpose = models.BooleanField(null=True)
    consistent_purpose_text = models.TextField(blank=True)
    consistent_plan = models.BooleanField(null=True)
    consistent_plan_text = models.TextField(blank=True)
    # proposal impact
    clearing_vegetation = models.BooleanField(null=True)
    clearing_vegetation_text = models.TextField(blank=True)
    ground_disturbing_works = models.BooleanField(null=True)
    ground_disturbing_works_text = models.TextField(blank=True)
    heritage_site = models.BooleanField(null=True)
    heritage_site_text = models.TextField(blank=True)
    environmentally_sensitive = models.BooleanField(null=True)
    environmentally_sensitive_text = models.TextField(blank=True)
    wetlands_impact = models.BooleanField(null=True)
    wetlands_impact_text = models.TextField(blank=True)
    building_required = models.BooleanField(null=True)
    building_required_text = models.TextField(blank=True)
    significant_change = models.BooleanField(null=True)
    significant_change_text = models.TextField(blank=True)
    aboriginal_site = models.BooleanField(null=True)
    aboriginal_site_text = models.TextField(blank=True)
    native_title_consultation = models.BooleanField(null=True)
    native_title_consultation_text = models.TextField(blank=True)
    mining_tenement = models.BooleanField(null=True)
    mining_tenement_text = models.TextField(blank=True)
    # Lease Licence additional form fields
    # proposal details
    profit_and_loss_text = models.TextField(blank=True)
    cash_flow_text = models.TextField(blank=True)
    capital_investment_text = models.TextField(blank=True)
    financial_capacity_text = models.TextField(blank=True)
    available_activities_text = models.TextField(blank=True)
    market_analysis_text = models.TextField(blank=True)
    staffing_text = models.TextField(blank=True)
    # proposal impact
    key_personnel_text = models.TextField(blank=True)
    key_milestones_text = models.TextField(blank=True)
    risk_factors_text = models.TextField(blank=True)
    legislative_requirements_text = models.TextField(blank=True)
    site_name = models.ForeignKey(
        SiteName, blank=True, null=True, on_delete=models.PROTECT
    )
    proponent_reference_number = models.CharField(null=True, blank=True, max_length=50)
    # datetime_gis_data_first_fetched = models.DateTimeField(blank=True, null=True)
    # datetime_gis_data_last_fetched = models.DateTimeField(blank=True, null=True)

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

        # Append 'P' to Proposal id to generate Lodgement number.
        # Lodgement number and lodgement sequence are used to generate Reference.
        if self.lodgement_number == '':
            self.lodgement_number = 'P{0:06d}'.format(self.pk)
            self.save()

        # If the processing_status has changed then add a reversion comment
        # so we have a way of filtering based on the status changing
        if self.processing_status != original_processing_status:
            self.save(version_comment=f'processing_status: {self.processing_status}')



