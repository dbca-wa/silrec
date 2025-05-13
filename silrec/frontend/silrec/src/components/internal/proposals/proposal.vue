<template lang="html">
    <div v-if="proposal" id="internalProposal" class="container">
        <div v-if="debug">internal/proposals/proposal.vue</div>
        <div class="row">
            <h3>
                {{ proposal.lodgement_number }} -
                {{
                    proposal.application_type
                        ? proposal.application_type.name_display
                        : null
                }}
                -
                {{
                    proposal.proposal_type
                        ? proposal.proposal_type.description
                        : null
                }}
                <small
                    v-if="proposal.original_leaselicence_number"
                    class="text-muted"
                >
                    (Migrating:
                    {{ proposal.original_leaselicence_number }})</small
                >
            </h3>

            <div class="col-md-3">
                <CommsLogs
                    :comms_url="comms_url"
                    :logs_url="logs_url"
                    :comms_add_url="comms_add_url"
                    :disable_add_entry="false"
                />

                <Submission
                    v-if="canSeeSubmission || debug"
                    :can-see-submission="canSeeSubmission"
                    :showing-proposal="showingProposal"
                    :proposal="proposal"
                    :submitter_first_name="submitter_first_name"
                    :submitter_last_name="submitter_last_name"
                    :lodgement_date="proposal.lodgement_date"
                    class="mt-2"
                    @revision-to-display="revisionToDisplay"
                />

                <Workflow
                    ref="workflow"
                    :proposal="proposal"
                    :on-current-revision="onCurrentRevision"
                    :is-finalised="isFinalised"
                    :can-action="canAction"
                    :can-assess="canAssess"
                    :is-referee="isReferee"
                    :can_user_edit="proposal.can_user_edit"
                    :profile="profile"
                    class="mt-2"
                    @toggle-proposal="toggleProposal"
                    @toggle-requirements="toggleRequirements"
                    @back-to-assessor="backToAssessor"
                    @switch-status="switchStatus"
                    @enter-conditions="enterConditions"
                    @complete-referral="completeReferral"
                    @amendment-request="amendmentRequest"
                    @proposed-decline="proposedDecline"
                    @proposed-approval="proposedApproval"
                    @issue-approval="issueApproval"
                    @decline-proposal="declineProposal"
                    @assign-request-user="assignRequestUser"
                    @assign-to="assignTo"
                    @complete-editing="validateInvoicingForm"
                    @update-proposal-data="updateProposalData"
                    @update-assigned-approver="updateAssignedApprover"
                    @update-assigned-officer="updateAssignedOfficer"
                />
            </div>

            <div class="col-md-9">
                <BootstrapAlert v-if="showTransferInformation">
                    Proposal to transfer
                    <span class="fw-bold"
                        >{{ proposal.approval.approval_type_name }}
                        {{ proposal.approval.lodgement_number }}
                    </span>
                    from
                    <span class="fw-bold">{{ proposal.approval.holder }}</span>
                    to
                    <span class="fw-bold">{{ proposal.applicant }}</span>
                </BootstrapAlert>
                <!-- Main contents -->
                <template v-if="display_approval_screen">
                    <ApprovalScreen
                        ref="approval_screen"
                        :proposal="proposal"
                        :readonly="readonly"
                        @update-invoicing-details="updateInvoicingDetails"
                    />
                </template>

                <template v-if="display_requirements">
                    <Requirements
                        :key="requirementsKey"
                        :proposal="proposal"
                        :profile="profile"
                        @refresh-proposal="fetchProposal"
                        @update-requirement="updateRequirement"
                    />
                </template>

                <template
                    v-if="
                        (showingProposal &&
                            [
                                'with_approver',
                                'approved_application',
                                'approved',
                                'declined',
                            ].includes(proposal.processing_status_id)) ||
                        (canSeeSubmission &&
                            ![
                                'with_approver',
                                'approved_application',
                                'approved',
                                'declined',
                            ].includes(proposal.processing_status_id)) ||
                        (!canSeeSubmission && showingProposal)
                    "
                >
                    <FormSection
                        :form-collapse="false"
                        label="Proposal"
                        index="application"
                    >
                        <ApplicationForm
                            v-if="proposal"
                            ref="application_form"
                            :key="computedProposalId"
                            :proposal="proposal"
                            :show_application_title="false"
                            :is_external="false"
                            :is_internal="true"
                            :can_assess="canAssess"
                            :is_referee="isReferee"
                            :readonly="readonly"
                            :submitter-id="submitter_id"
                            :show_related_items_tab="true"
                            :registration-of-interest="isRegistrationOfInterest"
                            :lease-licence="isLeaseLicence"
                            :navbar-buttons-disabled="navbarButtonsDisabled"
                            :saving-in-progress="savingProposal"
                            @refresh-from-response="refreshFromResponse"
                            @form-mounted="applicationFormMounted"
                            @update:gis-data="updateGisData"
                            @finished-drawing="onFinishedDrawing"
                            @deleted-features="onFinishedDrawing"
                        >
                            <!-- Inserted into the slot on the form.vue: Collapsible Assessor Questions -->
                            <template #slot_map_assessment_comments>
                                <AssessmentComments
                                    ref="collapsible_map_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Map Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_map_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_map"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_map
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_map"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="deficiency_comment_map"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_map
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="deficiency_comment_map"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_map_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_map
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_map_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template
                                #slot_proposal_tourism_details_assessment_comments
                            >
                                <AssessmentComments
                                    ref="collapsible_proposal_tourism_details_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Tourism Proposal Details Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_proposal_tourism_details_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_tourism_proposal_details"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_tourism_proposal_details
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_tourism_proposal_details"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="deficiency_comment_tourism_proposal_details"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_tourism_proposal_details
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="deficiency_comment_tourism_proposal_details"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_proposal_details
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                        <textarea
                                                            :id="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_proposal_details
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template
                                #slot_proposal_general_details_assessment_comments
                            >
                                <AssessmentComments
                                    ref="collapsible_proposal_general_details_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="General Proposal Details Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_proposal_general_details_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_general_proposal_details"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_general_proposal_details
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_general_proposal_details"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="deficiency_comment_general_proposal_details"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_general_proposal_details
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="deficiency_comment_general_proposal_details"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_proposal_details
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template
                                #slot_proposal_details_assessment_comments
                            >
                                <AssessmentComments
                                    ref="collapsible_proposal_details_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Proposal Details Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_proposal_details_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_proposal_details"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_proposal_details
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_proposal_details"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="deficiency_comment_proposal_details"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_proposal_details
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="deficiency_comment_proposal_details"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_proposal_details
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_proposal_details_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template #slot_proposal_impact_assessment_comments>
                                <AssessmentComments
                                    ref="collapsible_proposal_impact_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Proposal Impact Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_proposal_impact_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_proposal_impact"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_proposal_impact
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_proposal_impact"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="deficiency_comment_proposal_impact"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_proposal_impact
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="deficiency_comment_proposal_impact"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_proposal_impact_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_proposal_impact
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_proposal_impact_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template #slot_gis_data_assessment_comments>
                                <AssessmentComments
                                    ref="collapsible_gis_data_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Geospatial Data Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_gis_data_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_gis_data"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_gis_data
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_gis_data"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_gis_data"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_gis_data
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_gis_data"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_gis_data_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_gis_data
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_gis_data_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template #slot_categorisation_assessment_comments>
                                <AssessmentComments
                                    ref="collapsible_categorisation_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Categorisation Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_categorisation_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_categorisation"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_categorisation
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_categorisation"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_categorisation"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_categorisation
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_categorisation"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_gis_data_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_categorisation
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_gis_data_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template #slot_deed_poll_assessment_comments>
                                <AssessmentComments
                                    ref="collapsible_deed_poll_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Deed Poll Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_deed_poll_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_deed_poll"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_deed_poll
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_deed_poll"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="deficiency_comment_deed_poll"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_deed_poll
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="deficiency_comment_deed_poll"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.processing_status !=
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_RECALLED
                                                        .TEXT
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_deed_poll_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_deed_poll
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_deed_poll_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>
                            </template>

                            <template
                                #slot_additional_documents_assessment_comments
                            >
                                <AssessmentComments
                                    ref="collapsible_additional_documents_comments"
                                    :collapsed="collapseAssessmentComments"
                                    component_title="Additional Documents Assessment Comments"
                                    class="mb-2"
                                    @created="
                                        collapsible_additional_documents_comments_component_mounted
                                    "
                                >
                                    <div class="container px-3">
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="assessor_comment_additional_documents"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .assessor_comment_additional_documents
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="assessor_comment_additional_documents"
                                                        >Assessor
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3 mt-3">
                                            <div class="col">
                                                <div class="form-floating">
                                                    <textarea
                                                        id="deficiency_comment_additional_documents"
                                                        v-model="
                                                            proposal
                                                                .assessor_assessment
                                                                .deficiency_comment_additional_documents
                                                        "
                                                        class="form-control"
                                                        :disabled="
                                                            !canEditComments
                                                        "
                                                    />
                                                    <label
                                                        for="deficiency_comment_additional_documents"
                                                        >Deficiency
                                                        Comments</label
                                                    >
                                                </div>
                                            </div>
                                        </div>
                                        <template
                                            v-for="referral in proposal.referrals"
                                        >
                                            <div
                                                v-if="
                                                    referral.referral_text ||
                                                    referral.referral ==
                                                        profile.id
                                                "
                                                :key="referral.id"
                                                class="row mb-3 mt-3"
                                            >
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            :id="
                                                                'comment_additional_documents_' +
                                                                referral.id
                                                            "
                                                            v-model="
                                                                referral.comment_additional_documents
                                                            "
                                                            class="form-control referral-comment"
                                                            :disabled="
                                                                referral.referral !==
                                                                profile.id
                                                            "
                                                        />
                                                        <label
                                                            :for="
                                                                'comment_additional_documents_' +
                                                                referral.id
                                                            "
                                                            >Referral Comment by
                                                            <span
                                                                class="fw-bold"
                                                                >{{
                                                                    referral
                                                                        .referral_obj
                                                                        .fullname
                                                                }}</span
                                                            ></label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                        </template>
                                    </div>
                                </AssessmentComments>

                                <strong
                                    >Select one or more documents that need to
                                    be provided by the applicant:</strong
                                >

                                <div
                                    v-show="
                                        select2AppliedToAdditionalDocumentTypes
                                    "
                                    class="mb-3"
                                >
                                    <select
                                        ref="select_additional_document_types"
                                        v-model="
                                            proposal.additional_document_types
                                        "
                                        class="form-select"
                                        :disabled="!canAssess || savingProposal"
                                    ></select>
                                </div>
                                <div class="row">
                                    <div
                                        v-for="additional_document in proposal.additional_documents"
                                        :key="additional_document.id"
                                        class="col-sm-6"
                                    >
                                        <div class="card mb-3">
                                            <div class="card-body">
                                                <h4 class="card-title">
                                                    {{
                                                        additional_document.input_name
                                                    }}
                                                </h4>
                                                <p
                                                    class="card-text d-flex align-items-center"
                                                >
                                                    <label
                                                        for=""
                                                        class="d-inline-block pe-2"
                                                        >Document:
                                                    </label>

                                                    <i
                                                        class="fa fa-file-text pe-2"
                                                        aria-hidden="true"
                                                    ></i>
                                                    <a
                                                        class="d-inline-block text-truncate"
                                                        style="max-width: 250px"
                                                        :href="
                                                            additional_document.secure_url
                                                        "
                                                        target="_blank"
                                                        >{{
                                                            additional_document.name
                                                        }}</a
                                                    >
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </template>

                            <!-- Inserted into the slot on the form.vue: Related Items -->
                            <template #slot_section_related_items>
                                <FormSection
                                    :form-collapse="false"
                                    label="Related Items"
                                    index="related_items"
                                >
                                    <TableRelatedItems
                                        :ajax-url="related_items_ajax_url"
                                    />
                                </FormSection>
                            </template>
                        </ApplicationForm>
                    </FormSection>
                </template>
            </div>
        </div>

        <ProposedApproval
            v-if="showProposedModals"
            ref="proposed_approval"
            :key="proposedApprovalKey"
            :proposal="proposal"
            :processing_status="proposal.processing_status"
            :proposal_id="proposal.id"
            :proposal_type="
                proposal.proposal_type ? proposal.proposal_type.code : ''
            "
            :is-approval-level-document="isApprovalLevelDocument"
            :submitter_email="submitter_email"
            :applicant_email="applicant_email"
            :proposed-approval-key="proposedApprovalKey"
            :proposed-approval-state="proposedApprovalState"
            :assessment="assessment"
        />
        <ProposedDecline
            v-if="showProposedModals"
            ref="proposed_decline"
            :processing_status="proposal.processing_status"
            :proposal="proposal"
            :proposed-approval-key="proposedApprovalKey"
        />
        <AmendmentRequest ref="amendment_request" :proposal="proposal" />

        <div v-if="displaySaveBtns" class="navbar fixed-bottom bg-navbar">
            <div class="container">
                <div class="col-md-12 text-end">
                    <BootstrapButtonSpinner
                        v-if="savingProposal"
                        class="btn btn-primary me-2"
                        :is-loading="true"
                        :small="true"
                        :center-of-screen="false"
                    />
                    <button
                        v-else
                        class="btn btn-primary me-2"
                        :disabled="disableSaveAndExitBtn"
                        @click.prevent="save_and_exit"
                    >
                        Save and Exit
                    </button>

                    <BootstrapButtonSpinner
                        v-if="savingProposal"
                        class="btn btn-primary me-1"
                        :is-loading="true"
                        :small="true"
                        :center-of-screen="false"
                    />
                    <button
                        v-else
                        class="btn btn-primary"
                        :disabled="disableSaveAndContinueBtn"
                        @click.prevent="save_and_continue"
                    >
                        Save and Continue
                    </button>
                </div>
            </div>
        </div>
    </div>
    <div v-if="loading" class="container">
        <div class="row">
            <BootstrapSpinner class="text-primary" />
        </div>
    </div>
</template>

<script>
import ProposedDecline from '@/components/internal/proposals/proposal_proposed_decline.vue';
import AmendmentRequest from '@/components/internal/proposals/amendment_request.vue';
import Requirements from '@/components/internal/proposals/proposal_requirements.vue';
import ProposedApproval from '@/components/internal/proposals/proposed_issuance.vue';
import ApprovalScreen from '@/components/internal/proposals/proposal_approval.vue';
import CommsLogs from '@common-utils/comms_logs.vue';
import Submission from '@common-utils/submission.vue';
import Workflow from '@common-utils/workflow.vue';
import { api_endpoints, helpers, constants } from '@/utils/hooks';
import ApplicationForm from '@/components/form.vue';
import FormSection from '@/components/forms/section_toggle.vue';
import AssessmentComments from '@/components/forms/collapsible_component.vue';
import TableRelatedItems from '@/components/common/table_related_items.vue';
import { declineProposal } from '@/components/common/workflow_functions.js';

export default {
    name: 'InternalProposal',
    components: {
        ProposedDecline,
        AmendmentRequest,
        Requirements,
        ProposedApproval,
        ApprovalScreen,
        CommsLogs,
        Submission,
        Workflow,
        ApplicationForm,
        FormSection,
        AssessmentComments,
        TableRelatedItems,
    },
    data: function () {
        let vm = this;
        return {
            constants: constants,
            profile: null,
            detailsBody: 'detailsBody' + vm._.uid,
            addressBody: 'addressBody' + vm._.uid,
            contactsBody: 'contactsBody' + vm._.uid,
            siteLocations: 'siteLocations' + vm._.uid,
            related_items_datatable_id: 'related_items_datatable' + vm._.uid,
            defaultKey: 'aho',
            proposal: null,
            savingProposal: false,
            latest_revision: {},
            current_revision_id: null,
            assessment: {},
            loading: false,
            approver_comment: '',
            form: null,
            members: [],
            contacts_table_initialised: false,
            initialisedSelects: false,
            showingProposal: false,
            showingRequirements: false,
            hasAmendmentRequest: false,
            state_options: ['requirements', 'processing'],
            contacts_table_id: vm._.uid + 'contacts-table',
            contacts_options: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    url: vm.contactsURL,
                    dataSrc: '',
                },
                columns: [
                    {
                        title: 'Name',
                        mRender: function (data, type, full) {
                            return full.first_name + ' ' + full.last_name;
                        },
                    },
                    {
                        title: 'Phone',
                        data: 'phone_number',
                    },
                    {
                        title: 'Mobile',
                        data: 'mobile_number',
                    },
                    {
                        title: 'Fax',
                        data: 'fax_number',
                    },
                    {
                        title: 'Email',
                        data: 'email',
                    },
                ],
                processing: true,
            },
            contacts_table: null,
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            comms_url: helpers.add_endpoint_json(
                api_endpoints.proposal,
                vm.$route.params.proposal_id + '/comms_log'
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.proposal,
                vm.$route.params.proposal_id + '/add_comms_log'
            ),
            logs_url: helpers.add_endpoint_json(
                api_endpoints.proposal,
                vm.$route.params.proposal_id + '/action_log'
            ),
            panelClickersInitialised: false,
            uuid: 0,
            additionalDocumentTypesSelected: [],
            select2AppliedToAdditionalDocumentTypes: false,
            proposedApprovalState: '',
        };
    },
    computed: {
        withReferral: function () {
            return (
                this.proposal &&
                [constants.PROPOSAL_STATUS.WITH_REFERRAL.ID].includes(
                    this.proposal.processing_status_id
                )
            );
        },
        collapseAssessmentComments: function () {
            return ![
                constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID,
                constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID,
                constants.PROPOSAL_STATUS.WITH_APPROVER.ID,
                constants.PROPOSAL_STATUS.WITH_REFERRAL.ID,
            ].includes(this.proposal.processing_status_id);
        },
        related_items_ajax_url: function () {
            return '/api/proposal/' + this.proposal.id + '/related_items/';
        },
        requirementsKey: function () {
            const req = 'proposal_requirements_' + this.uuid;
            return req;
        },
        canEditComments: function () {
            let canEdit = false;
            if (
                [
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID,
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID,
                ].includes(this.proposal.processing_status_id)
            ) {
                if (
                    this.proposal.accessing_user_roles.includes(
                        constants.ROLES.GROUP_NAME_ASSESSOR.ID
                    )
                ) {
                    canEdit = true;
                }
            }
            return canEdit;
        },
        displaySaveBtns: function () {
            let display = false;

            if (
                [
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID,
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID,
                ].includes(this.proposal.processing_status_id)
            ) {
                if (
                    this.proposal.application_type.name ===
                    constants.APPLICATION_TYPES.LEASE_LICENCE
                ) {
                    if (
                        this.proposal.accessing_user_roles.includes(
                            constants.ROLES.GROUP_NAME_ASSESSOR.ID
                        )
                    ) {
                        display = true;
                    }
                } else if (
                    this.proposal.application_type.name ===
                    constants.APPLICATION_TYPES.REGISTRATION_OF_INTEREST
                ) {
                    if (
                        this.proposal.accessing_user_roles.includes(
                            constants.ROLES.GROUP_NAME_ASSESSOR.ID
                        )
                    ) {
                        display = true;
                    }
                }
            } else if (this.withReferral && this.profile.is_referee) {
                display = true;
            } else if (
                [
                    constants.PROPOSAL_STATUS.APPROVED_EDITING_INVOICING.ID,
                ].includes(this.proposal.processing_status_id)
            ) {
                if (
                    this.proposal.accessing_user_roles.includes(
                        constants.ROLES.FINANCE.ID
                    )
                ) {
                    display = true;
                }
            }

            return display;
        },
        disableSaveAndContinueBtn: function () {
            // Is this needed?
            return !this.displaySaveBtns;
        },
        disableSaveAndExitBtn: function () {
            // Is this needed?
            return !this.displaySaveBtns;
        },
        submitter_first_name: function () {
            if (this.proposal.submitter) {
                return this.proposal.submitter.first_name;
            } else {
                return '';
            }
        },
        submitter_last_name: function () {
            if (this.proposal.submitter) {
                return this.proposal.submitter.last_name;
            } else {
                return '';
            }
        },
        submitter_id: function () {
            if (this.proposal.submitter) {
                return this.proposal.submitter.id;
            } else {
                return this.proposal.applicant_obj.id;
            }
        },
        submitter_email: function () {
            if (this.proposal.submitter) {
                return this.proposal.submitter.email;
            } else {
                return this.proposal.applicant_obj.email;
            }
        },
        proposal_form_url: function () {
            if (
                [
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID,
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID,
                ].includes(this.proposal.processing_status_id)
            ) {
                return `/api/proposal/${this.proposal.id}/assessor_save.json`;
            } else if (
                [constants.PROPOSAL_STATUS.WITH_REFERRAL.ID].includes(
                    this.proposal.processing_status_id
                )
            ) {
                return `/api/proposal/${this.proposal.id}/referral_save.json`;
            } else if (
                [
                    constants.PROPOSAL_STATUS.APPROVED_EDITING_INVOICING.ID,
                ].includes(this.proposal.processing_status_id)
            ) {
                return `/api/proposal/${this.proposal.id}/finance_save.json`;
            } else {
                // Should not reach here
                return '';
            }
        },
        complete_referral_url: function () {
            return `/api/proposal/${this.proposal.id}/complete_referral.json`;
        },
        isRegistrationOfInterest: function () {
            return this.proposal.application_type.name ===
                constants.APPLICATION_TYPES.REGISTRATION_OF_INTEREST
                ? true
                : false;
        },
        isLeaseLicence: function () {
            return this.proposal.application_type.name ===
                constants.APPLICATION_TYPES.LEASE_LICENCE
                ? true
                : false;
        },
        proposedApprovalKey: function () {
            return 'proposed_approval_' + this.uuid;
        },
        computedProposalId: function () {
            if (this.proposal) {
                // Create a new key to make vue reload the component
                return `${this.proposal.id}-${this.uuid}`;
            }
            return '';
        },
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        display_approval_screen: function () {
            if (this.debug) return true;
            let ret_val =
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.WITH_APPROVER.ID ||
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.APPROVED_EDITING_INVOICING.ID ||
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.APPROVED_COMPETITIVE_PROCESS.ID ||
                this.isFinalised;
            return ret_val;
        },
        display_requirements: function () {
            let ret_val =
                (this.profile &&
                    this.proposal.processing_status_id ==
                        constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS
                            .ID) ||
                ((this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.WITH_APPROVER.ID ||
                    this.isFinalised) &&
                    this.showingRequirements);
            return ret_val;
        },
        readonly: function () {
            return !(
                this.proposal.added_internally && this.proposal.assigned_officer
            );
        },
        contactsURL: function () {
            return this.proposal != null
                ? helpers.add_endpoint_json(
                      api_endpoints.organisations,
                      this.proposal.applicant.id + '/contacts'
                  )
                : '';
        },
        isLoading: function () {
            return this.loading.length > 0;
        },
        csrf_token: function () {
            return helpers.getCookie('csrftoken');
        },
        isFinalised: function () {
            return (
                this.proposal.processing_status == 'Declined' ||
                this.proposal.processing_status == 'Approved' ||
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.APPROVED_APPLICATION.ID //approved_application
            );
        },
        canAssess: function () {
            return (
                this.proposal && this.proposal.assessor_mode.assessor_can_assess
            );
        },
        isReferee: function () {
            return this.proposal && this.proposal.assessor_mode.is_referee;
        },
        hasAssessorMode: function () {
            return this.proposal &&
                this.proposal.assessor_mode.has_assessor_mode
                ? true
                : false;
        },
        canAction: function () {
            return this.proposal.assessor_mode.assessor_can_assess;
        },
        canSeeSubmission: function () {
            return (
                this.proposal &&
                ![
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.TEXT,
                ].includes(this.proposal.processing_status)
            );
        },
        onCurrentRevision: function () {
            // Returns whether the currently displayed version is the latest one
            return (
                this.latest_revision.revision_id === this.current_revision_id
            );
        },
        isApprovalLevelDocument: function () {
            return this.proposal &&
                this.proposal.processing_status == 'With Approver' &&
                this.proposal.approval_level != null &&
                this.proposal.approval_level_document == null
                ? true
                : false;
        },
        applicant_email: function () {
            return this.proposal && this.proposal.applicant.email
                ? this.proposal.applicant.email
                : '';
        },
        conditionsMissingDates() {
            return (
                this.proposal &&
                this.proposal.requirements.filter(
                    (condition) =>
                        !condition.standard_requirement
                            ?.gross_turnover_required &&
                        !condition.is_deleted &&
                        !condition.due_date
                )
            );
        },
        showTransferInformation() {
            return (
                this.proposal &&
                this.proposal.proposal_type.code ==
                    constants.PROPOSAL_TYPE.TRANSFER.code &&
                this.proposal.approval &&
                [
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID,
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID,
                    constants.PROPOSAL_STATUS.WITH_APPROVER.ID,
                ].includes(this.proposal.processing_status_id)
            );
        },
        navbarButtonsDisabled: function () {
            return this.savingProposal;
        },
        showProposedModals: function () {
            return (
                this.proposal &&
                this.profile &&
                (this.profile.is_assessor || this.profile.is_approver)
            );
        },
    },
    watch: {},
    updated: function () {
        let vm = this;
        if (!vm.panelClickersInitialised) {
            $('.panelClicker[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass(
                        'glyphicon-chevron-down glyphicon-chevron-up'
                    );
                }, 100);
            });
            vm.panelClickersInitialised = true;
        }
        this.$nextTick(() => {
            vm.initialiseOrgContactTable();
            vm.initialiseSelects();
            vm.form = document.forms.new_proposal;
            if (vm.hasAmendmentRequest) {
                vm.deficientFields();
            }
        });
    },
    created: async function () {
        this.profile = Object.assign(
            {},
            await helpers.fetchWrapper(api_endpoints.profile)
        );
        this.fetchProposal();
    },
    methods: {
        validateInvoicingForm: function () {
            let vm = this;
            var form = document.getElementById('invoicing-form');

            if (form.checkValidity()) {
                if (!this.proposal.invoicing_details.oracle_code) {
                    $('#oracle_code').focus();
                    swal.fire({
                        title: 'Receivable Activity Code Required',
                        text: 'Please select a receivable activity code',
                        icon: 'error',
                        customClass: 'swal-wide',
                    });
                    return;
                }
                vm.completeEditing();
            } else {
                form.classList.add('was-validated');
                $('#invoicing-form').find(':invalid').first().focus();
            }

            return false;
        },
        completeEditing: async function () {
            let vm = this;
            var chargeType = $(
                'input[type=radio][name=charge_method]:checked'
            ).attr('id');
            let cancelled = false;
            if (constants.CHARGE_METHODS.ONCE_OFF_CHARGE.ID == chargeType) {
                await swal
                    .fire({
                        title: 'Confirm Once Off Invoice',
                        text: 'You have selected to invoice as a once off charge, \
                        this will create a new invoice record. An oracle invoice must \
                        be attached to the new invoice record before the system will send a payment request to the lease/licence holder.',
                        icon: 'info',
                        showCancelButton: true,
                        buttonsStyling: false,
                        confirmButtonText: 'Confirm',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                            cancelButton: 'btn btn-secondary me-2',
                        },
                        reverseButtons: true,
                    })
                    .then((result) => {
                        if (result.isDismissed) {
                            cancelled = true;
                        }
                    });
            }
            let previewInvoices =
                this.$refs.approval_screen.$refs.invoicing_details
                    .previewInvoices;
            if (
                [
                    constants.CHARGE_METHODS
                        .BASE_FEE_PLUS_FIXED_ANNUAL_INCREMENT.ID,
                    constants.CHARGE_METHODS
                        .BASE_FEE_PLUS_FIXED_ANNUAL_PERCENTAGE.ID,
                    constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI_CUSTOM.ID,
                    constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI.ID,
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE.ID,
                ].includes(chargeType) &&
                previewInvoices.find(
                    (invoice) =>
                        invoice.start_date_has_passed == true &&
                        invoice.amount_object.amount != null &&
                        invoice.amount_object.amount != 0
                ) &&
                !(
                    this.proposal.proposal_type.code ==
                        constants.PROPOSAL_TYPE.MIGRATION.code ||
                    this.proposal.proposal_type.code ==
                        constants.PROPOSAL_TYPE.TRANSFER.code
                )
            ) {
                let immediateInvoicesHtml =
                    '<p>Based on the information you have entered, the following invoice records will be generated:</p>';
                immediateInvoicesHtml +=
                    '<table class="table table-sm table-striped">';
                immediateInvoicesHtml +=
                    '<thead><tr><th>Number</th><th>Issue Date</th><th>Time Period</th><th>Amount</th></tr></thead><tbody>';

                for (let i = 0; i < previewInvoices.length; i++) {
                    let invoice = previewInvoices[i];
                    if (
                        invoice.start_date_has_passed &&
                        invoice.amount_object.amount != null
                    ) {
                        immediateInvoicesHtml += '<tr>';
                        immediateInvoicesHtml += `<td>${invoice.number}</td>`;
                        immediateInvoicesHtml += `<td>${invoice.issue_date}</td>`;
                        immediateInvoicesHtml += `<td>${invoice.time_period}</td>`;
                        immediateInvoicesHtml += `<td>${invoice.amount_object.prefix}${invoice.amount_object.amount}${invoice.amount_object.suffix}</td>`;
                        immediateInvoicesHtml += '</tr>';
                    }
                }
                immediateInvoicesHtml += '</tbody></table>';
                immediateInvoicesHtml +=
                    '<p class="fs-6 text-muted">* An oracle invoice must be attached to each invoice record before the request for payment will be sent.</p>';
                await swal
                    .fire({
                        title: 'Confirm Immediate Invoice Generation',
                        html: immediateInvoicesHtml,
                        icon: 'info',
                        showCancelButton: true,
                        confirmButtonText: 'Confirm',
                        buttonsStyling: false,
                        customClass: {
                            popup: 'swal-extra-wide',
                            confirmButton: 'btn btn-primary',
                            cancelButton: 'btn btn-secondary me-2',
                        },
                        confirmButtonColor: '#3085d6',
                        reverseButtons: true,
                    })
                    .then((result) => {
                        if (result.isDismissed) {
                            cancelled = true;
                        }
                    });
            }

            if (!cancelled) {
                vm.loading = true;
                const payload = { proposal: this.proposal };
                const res = await fetch(
                    '/api/proposal/' +
                        this.proposal.id +
                        '/finance_complete_editing.json',
                    {
                        body: JSON.stringify(payload),
                        method: 'POST',
                    }
                );

                if (res.ok) {
                    swal.fire({
                        title: 'Saved',
                        text: 'The proposal has been saved',
                        icon: 'success',
                    });
                    let data = await res.json();
                    this.proposal = Object.assign({}, data);
                } else {
                    let errors = [];
                    await res.json().then((json) => {
                        for (let key in json) {
                            errors.push(
                                `${key}: ${
                                    typeof json[key] == 'string'
                                        ? json[key]
                                        : json[key].join(',')
                                }`
                            );
                        }
                        swal.fire({
                            title: 'Please fix following errors before saving',
                            text: errors.join(','),
                            icon: 'error',
                        });
                    });
                }
                vm.loading = false;
            }
        },
        applicationFormMounted: function () {
            this.fetchAdditionalDocumentTypesDict(); // <select> element for the additional document type exists in the ApplicationForm component, which is a child component of this component.
            // Therefore to apply select2 to the element inside child component, we have to make sure the childcomponent has been mounted.  Then select2 can be applied.
        },
        applySelect2ToAdditionalDocumentTypes: function (option_data) {
            let vm = this;

            if (!vm.select2AppliedToAdditionalDocumentTypes) {
                $(vm.$refs.select_additional_document_types)
                    .select2({
                        theme: 'bootstrap-5',
                        allowClear: false,
                        placeholder: 'Select Type',
                        multiple: true,
                        data: option_data,
                    })
                    .on('select2:select', function (e) {
                        vm.proposal.additional_document_types = $(
                            e.currentTarget
                        ).val();
                        vm.proposal.additional_documents_missing.push({
                            name: e.params.data.name,
                        });
                    })
                    .on('select2:unselect', function (e) {
                        vm.proposal.additional_document_types = $(
                            e.currentTarget
                        ).val();
                        vm.proposal.additional_documents_missing =
                            vm.proposal.additional_documents_missing.filter(
                                (item) => item.name != e.params.data.name
                            );
                    })
                    .val(vm.proposal.additional_document_types)
                    .trigger('change');
                vm.select2AppliedToAdditionalDocumentTypes = true;
            }
        },
        collapsible_map_comments_component_mounted: function () {
            this.$refs.collapsible_map_comments.show_warning_icon(false);
        },
        collapsible_proposal_tourism_details_comments_component_mounted:
            function () {
                this.$refs.collapsible_proposal_tourism_details_comments.show_warning_icon(
                    false
                );
            },
        collapsible_proposal_general_details_comments_component_mounted:
            function () {
                this.$refs.collapsible_proposal_general_details_comments.show_warning_icon(
                    false
                );
            },
        collapsible_proposal_details_comments_component_mounted: function () {
            this.$refs.collapsible_proposal_details_comments.show_warning_icon(
                false
            );
        },
        collapsible_proposal_impact_comments_component_mounted: function () {
            this.$refs.collapsible_proposal_impact_comments.show_warning_icon(
                false
            );
        },
        collapsible_gis_data_comments_component_mounted: function () {
            this.$refs.collapsible_gis_data_comments.show_warning_icon(false);
        },
        collapsible_categorisation_comments_component_mounted: function () {
            this.$refs.collapsible_categorisation_comments.show_warning_icon(
                false
            );
        },
        collapsible_deed_poll_comments_component_mounted: function () {
            this.$refs.collapsible_deed_poll_comments.show_warning_icon(false);
        },
        collapsible_additional_documents_comments_component_mounted:
            function () {
                this.$refs.collapsible_additional_documents_comments.show_warning_icon(
                    false
                );
            },
        save_and_continue: async function () {
            await this.save().then(() => {
                this.savingProposal = false;
            });
        },
        save_and_exit: async function () {
            await this.save_and_continue().then(() => {
                this.$router.push({ name: 'internal-dashboard' });
            });
        },
        completeReferral: async function (referral_text) {
            let vm = this;
            vm.checkAssessorData();
            swal.fire({
                title: 'Complete Referral',
                text: 'Are you sure you want to complete this referral?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Submit',
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    container: 'swal2-popover',
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            })
                .then(async (result) => {
                    if (result.isConfirmed) {
                        await fetch(vm.complete_referral_url, {
                            body: JSON.stringify({
                                proposal: this.proposal,
                                referee_id: this.profile.id,
                                referral_text: referral_text,
                            }),
                            method: 'POST',
                            headers: {
                                Accept: 'application/json',
                                'Content-Type': 'application/json',
                            },
                        });
                        if (vm.profile.is_staff) {
                            this.$router.push({ name: 'internal-dashboard' });
                        } else {
                            this.$router.push({ name: 'external-dashboard' });
                        }
                    }
                })
                .catch((err) => {
                    swal.fire({
                        title: 'Referral Error',
                        text: err['message'],
                        icon: 'error',
                        customClass: {
                            container: 'swal2-popover',
                        },
                    });
                });
        },
        save: async function (
            show_confirmation = true,
            increment_map_key = true
        ) {
            let vm = this;
            this.savingProposal = true;
            vm.checkAssessorData();
            try {
                let payload = { proposal: this.proposal };
                // When in Entering Conditions status ApplicationForm might not be there
                if (
                    vm.$refs.application_form &&
                    vm.$refs.application_form.$refs.component_map
                ) {
                    payload.proposalgeometry =
                        vm.$refs.application_form.$refs.component_map.getJSONFeatures();
                }

                if (
                    this.proposal.proposal_type.code ==
                        constants.PROPOSAL_TYPE.MIGRATION.code &&
                    this.proposal.processing_status_id ==
                        constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID
                ) {
                    if (
                        this.proposal.groups.find(
                            (group) =>
                                group.name.trim().toLowerCase() == 'tourism'
                        )
                    ) {
                        payload.proposal.profit_and_loss_text =
                            this.$refs.application_form.$refs.lease_licence.$refs.profit_and_loss_text.detailsText;
                        payload.proposal.cash_flow_text =
                            this.$refs.application_form.$refs.lease_licence.$refs.cash_flow_text.detailsText;
                        payload.proposal.capital_investment_text =
                            this.$refs.application_form.$refs.lease_licence.$refs.capital_investment_text.detailsText;
                        payload.proposal.financial_capacity_text =
                            this.$refs.application_form.$refs.lease_licence.$refs.financial_capacity_text.detailsText;
                        payload.proposal.available_activities_text =
                            this.$refs.application_form.$refs.lease_licence.$refs.available_activities_text.detailsText;
                        payload.proposal.market_analysis_text =
                            this.$refs.application_form.$refs.lease_licence.$refs.market_analysis_text.detailsText;
                        payload.proposal.staffing_text =
                            this.$refs.application_form.$refs.lease_licence.$refs.staffing_text.detailsText;
                    }

                    payload.proposal.key_personnel_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.key_personnel_text.detailsText;
                    payload.proposal.key_milestones_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.key_milestones_text.detailsText;
                    payload.proposal.risk_factors_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.risk_factors_text.detailsText;
                    payload.proposal.legislative_requirements_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.legislative_requirements_text.detailsText;
                    payload.proposal.proponent_reference_number =
                        this.proposal.proponent_reference_number;
                    payload.proposal.groups = this.proposal.groups;
                }

                const res = await fetch(vm.proposal_form_url, {
                    body: JSON.stringify(payload),
                    method: 'POST',
                });

                if (res.ok) {
                    if (show_confirmation) {
                        swal.fire({
                            title: 'Saved',
                            text: 'Your proposal has been saved',
                            icon: 'success',
                        });
                    }
                    let resData = await res.json();
                    vm.proposal = Object.assign({}, resData);
                    vm.$nextTick(async () => {
                        if (
                            increment_map_key &&
                            vm.$refs.application_form != undefined
                        ) {
                            vm.$refs.application_form.incrementComponentMapKey();
                        }
                    });
                } else {
                    let err = await res.json();
                    await swal.fire({
                        title: 'Please fix following errors before saving',
                        text: JSON.stringify(err),
                        icon: 'error',
                    });
                }
            } catch (err) {
                console.error(err);
            }
        },
        checkAssessorData: function () {
            //check assessor boxes and clear value of hidden assessor boxes so it won't get printed on approval pdf.
            //select all fields including hidden fields
            var all_fields = $(
                'input[type=text]:required, textarea:required, input[type=checkbox]:required, input[type=radio]:required, input[type=file]:required, select:required'
            );
            all_fields.each(function () {
                var ele = null;
                //check the fields which has assessor boxes.
                ele = $('[name=' + this.name + '-Assessor]');
                if (ele.length > 0) {
                    let visiblity = $('[name=' + this.name + '-Assessor]').is(
                        ':visible'
                    );
                    if (!visiblity) {
                        if (ele[0].value != '') {
                            ele[0].value = '';
                        }
                    }
                }
            });
        },
        initialiseOrgContactTable: function () {
            let vm = this;
            if (vm.proposal && !vm.contacts_table_initialised) {
                vm.contacts_options.ajax.url = helpers.add_endpoint_json(
                    api_endpoints.organisations,
                    vm.proposal.applicant.id + '/contacts'
                );
                vm.contacts_table = $('#' + vm.contacts_table_id).DataTable(
                    vm.contacts_options
                );
                vm.contacts_table_initialised = true;
            }
        },
        commaToNewline(s) {
            return s.replace(/[,;]/g, '\n');
        },
        proposedDecline: function () {
            this.proposedApprovalState = 'proposed_decline';
            // this.uuid++; Why do we need to reload the whole form when we open a modal!?
            this.$nextTick(() => {
                this.$refs.proposed_decline.isModalOpen = true;
            });
        },
        enterConditions: async function () {
            let vm = this;
            let tab = null;
            if (vm.proposal.groups.length == 0 || !vm.proposal.site_name) {
                // When status is with assessor conditions, the proposal may be hidden
                // Therefore we need to show it before we can validate the groups and site name
                vm.$refs.workflow.showingProposal = true;
                vm.showingProposal = true;
                setTimeout(() => {
                    let someTabTriggerEl =
                        document.querySelector('#pills-details-tab');
                    tab = new bootstrap.Tab(someTabTriggerEl);
                    tab.show();
                }, 200);
            }

            if (vm.proposal.groups.length == 0) {
                swal.fire({
                    title: 'No Group Selected',
                    text: 'You must select one or more groups before entering conditions.',
                    icon: 'warning',
                    didClose: () => {
                        $([document.documentElement, document.body]).animate(
                            {
                                scrollTop: $(
                                    '#section_body_categorisation'
                                ).offset().top,
                            },
                            0,
                            () => {
                                vm.$refs.application_form.$refs.groups.$el.focus();
                            }
                        );
                    },
                });

                return;
            }
            if (!vm.proposal.site_name) {
                swal.fire({
                    title: 'No Site Name Entered',
                    text: 'You must enter a site name before entering conditions.',
                    icon: 'warning',
                    didClose: () => {
                        $([document.documentElement, document.body]).animate(
                            {
                                scrollTop: $(
                                    '#section_body_categorisation'
                                ).offset().top,
                            },
                            0,
                            () => {
                                tab.show();
                                vm.$refs.application_form.$refs.site_name.focus();
                            }
                        );
                    },
                });
                return;
            }

            if (!vm.proposal.proposalgeometry.features.length > 0) {
                swal.fire({
                    title: 'No Land Area Selected',
                    text: 'You must indicate the land area before entering conditions. Please either draw one or more polygons on the map or upload a shapefile and then click the save button. If you have already drawn a polygon, please save the proposal and then try again.',
                    icon: 'warning',
                    didClose: () => {
                        setTimeout(() => {
                            let someTabTriggerEl =
                                document.querySelector('#pills-map-tab');
                            tab = new bootstrap.Tab(someTabTriggerEl);
                            tab.show();
                        }, 200);
                    },
                });
                return;
            }

            // Save the proposal before opening the modal
            this.savingProposal = true;
            await this.save(false).then(() => {
                this.savingProposal = false;
            });

            vm.switchStatus(
                constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID
            );
            vm.showingProposal = false;
        },
        proposedApproval: async function () {
            let vm = this;

            vm.proposedApprovalState = 'proposed_approval';

            if (this.proposal.proposal_type.code == 'transfer') {
                if (!vm.canProposeToApproveTransfer()) {
                    return;
                }
            }

            let tab = null;
            if (vm.proposal.groups.length == 0 || !vm.proposal.site_name) {
                // When status is with assessor conditions, the proposal may be hidden
                // Therefore we need to show it before we can validate the groups and site name
                vm.$refs.workflow.showingProposal = true;
                vm.showingProposal = true;
                setTimeout(() => {
                    let someTabTriggerEl =
                        document.querySelector('#pills-details-tab');
                    tab = new bootstrap.Tab(someTabTriggerEl);
                    tab.show();
                }, 200);
            }

            if (vm.proposal.groups.length == 0) {
                swal.fire({
                    title: 'No Group Selected',
                    text: 'You must select one or more groups before entering conditions.',
                    icon: 'warning',
                    didClose: () => {
                        $([document.documentElement, document.body]).animate(
                            {
                                scrollTop: $(
                                    '#section_body_categorisation'
                                ).offset().top,
                            },
                            0,
                            () => {
                                vm.$refs.application_form.$refs.groups.$el.focus();
                            }
                        );
                    },
                });

                return;
            }
            if (!vm.proposal.site_name) {
                swal.fire({
                    title: 'No Site Name Entered',
                    text: 'You must enter a site name before entering conditions.',
                    icon: 'warning',
                    didClose: () => {
                        $([document.documentElement, document.body]).animate(
                            {
                                scrollTop: $(
                                    '#section_body_categorisation'
                                ).offset().top,
                            },
                            0,
                            () => {
                                tab.show();
                                vm.$refs.application_form.$refs.site_name.focus();
                            }
                        );
                    },
                });
                return;
            }

            if (!vm.proposal.proposalgeometry.features.length > 0) {
                swal.fire({
                    title: 'No Land Area Selected',
                    text: 'You must indicate the land area before entering conditions. Please either draw one or more polygons on the map or upload a shapefile and then click the save button, please save the proposal and then try again.',
                    icon: 'warning',
                    didClose: () => {
                        setTimeout(() => {
                            let someTabTriggerEl =
                                document.querySelector('#pills-map-tab');
                            tab = new bootstrap.Tab(someTabTriggerEl);
                            tab.show();
                        }, 200);
                    },
                });
                return;
            }

            // Save the proposal before opening the modal
            this.savingProposal = true;
            await this.save(false).then(() => {
                this.savingProposal = false;
            });

            if (
                this.conditionsMissingDates &&
                this.conditionsMissingDates.length > 0
            ) {
                swal.fire({
                    title: 'Conditions Missing Dates',
                    text: 'You must enter a due date for each condition before proposing to approve.',
                    icon: 'warning',
                });
                return;
            }

            // this.uuid++; Why do we need to reload the whole form when we open a modal!?
            this.$nextTick(() => {
                vm.$refs.proposed_approval.isModalOpen = true;
            });
        },
        canProposeToApproveTransfer() {
            if (
                this.proposal.approval.has_outstanding_compliances ||
                this.proposal.approval.has_outstanding_invoices
            ) {
                swal.fire({
                    title: `Unable to Transfer Lease/License`,
                    text: `Lease/License ${this.proposal.approval.lodgement_number} can not be transferred as it has outstanding compliances or invoices. \
                    The current holder must submit any due compliances and pay any due invoices before it can be approved \
                    (Note: Invoices records for the lease/licence that don't yet have a due date because a finance officer hasn't uploaded the oracle invoice yet
                    must also be processed by a finance officer before a transfer can occur).`,
                    icon: 'warning',
                    showCancelButton: true,
                    showConfirmButton: false,
                    cancelButtonText: 'Dismiss',
                });
                return false;
            }
            if (this.proposal.approval.has_missing_gross_turnover_entries) {
                swal.fire({
                    title: `Unable to Transfer Lease/License`,
                    text: `Lease/License ${this.proposal.approval.lodgement_number} can not be transferred \
                    as it is missing actual gross turnover entries for one or more financial years. \
                    A finance officer must enter actual gross turnover entries for all elapsed financial years.`,
                    icon: 'warning',
                    showCancelButton: true,
                    showConfirmButton: false,
                    cancelButtonText: 'Dismiss',
                });
                return false;
            }
            return true;
        },
        issueApproval: function () {
            //save approval level comment before opening 'issue approval' modal
            if (
                this.proposal &&
                this.proposal.processing_status == 'With Approver' &&
                this.proposal.approval_level != null &&
                this.proposal.approval_level_document == null
            ) {
                if (this.proposal.approval_level_comment != '') {
                    let vm = this;
                    let data = new FormData();
                    data.append(
                        'approval_level_comment',
                        vm.proposal.approval_level_comment
                    );
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposal,
                            vm.proposal.id + '/approval_level_comment'
                        ),
                        { body: JSON.stringify(data), method: 'POST' }
                    ).then(
                        (res) => {
                            vm.proposal = res.body;
                        },
                        (err) => {
                            console.error(err);
                        }
                    );
                }
            }
            if (
                this.isApprovalLevelDocument &&
                this.proposal.approval_level_comment == ''
            ) {
                swal(
                    'Error',
                    'Please add Approval document or comments before final approval',
                    'error'
                );
            } else {
                this.proposedApprovalState = 'final_approval';

                if (this.proposal.proposal_type.code == 'transfer') {
                    if (!this.canProposeToApproveTransfer()) {
                        console.warn('cannot approve transfer');
                        return;
                    }
                }

                // this.uuid++; Why do we need to reload the whole form when we open a modal!?
                this.$nextTick(() => {
                    this.$refs.proposed_approval.isModalOpen = true;
                });
            }
        },
        declineProposal: async function () {
            let vm = this;
            await declineProposal(this.proposal)
                .then((data) => {
                    if (data != null) {
                        // Only update the proposal if the discard was successful
                        vm.proposal = Object.assign({}, data);
                        vm.uuid++;
                        swal.fire({
                            title: `Proposal ${this.proposal.lodgement_number} Declined`,
                            text: 'The proposal has been declined and the proponent has been notified by email.',
                            icon: 'success',
                        });
                    }
                })
                .catch((error) => {
                    swal.fire({
                        title: 'The proposal could not be declined',
                        text: error,
                        icon: 'error',
                    });
                });
        },
        updateProposalData: function (proposal) {
            this.proposal = proposal;
        },
        amendmentRequest: async function () {
            this.loading = true;
            let values = '';
            $('.deficiency').each((i, d) => {
                values +=
                    $(d).val() != ''
                        ? `Question - ${$(d).data(
                              'question'
                          )}\nDeficiency - ${$(d).val()}\n\n`
                        : '';
            });
            await this.save(false);
            this.$refs.amendment_request.amendment.text = values;
            this.$refs.amendment_request.isModalOpen = true;
            this.loading = false;
        },
        highlight_deficient_fields: function (deficient_fields) {
            for (let deficient_field of deficient_fields) {
                $('#' + 'id_' + deficient_field).css('color', 'red');
            }
        },
        deficientFields() {
            let vm = this;
            let deficient_fields = [];
            $('.deficiency').each((i, d) => {
                if ($(d).val() != '') {
                    let name = $(d)[0].name;
                    let tmp = name.replace('-comment-field', '');
                    deficient_fields.push(tmp);
                }
            });
            vm.highlight_deficient_fields(deficient_fields);
        },
        toggleProposal: function (value) {
            this.showingProposal = value;
        },
        toggleRequirements: function (value) {
            this.showingRequirements = value;
        },
        updateAssignedApprover: function (value) {
            let vm = this;
            vm.proposal.assigned_approver = value;
        },
        updateAssignedOfficer: function (value) {
            let vm = this;
            vm.proposal.assigned_officer = value;
        },
        updateAssignedOfficerSelect: function () {
            let vm = this;
            if (vm.proposal.processing_status == 'With Approver') {
                vm.$refs.workflow.updateAssignedOfficerSelect(
                    vm.proposal.assigned_approver
                );
            } else {
                vm.$refs.workflow.updateAssignedOfficerSelect(
                    vm.proposal.assigned_officer
                );
            }
        },
        assignRequestUser: async function () {
            let vm = this;

            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal,
                    vm.proposal.id + '/assign_request_user'
                )
            )
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.json().then((json) => {
                            throw new Error(json);
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then((data) => {
                    vm.proposal = Object.assign({}, data);
                    vm.updateAssignedOfficerSelect();
                    vm.$nextTick(() => {
                        vm.$refs.workflow.initialiseRefereeSelect();
                    });
                })
                .catch((error) => {
                    this.updateAssignedOfficerSelect();
                    console.error(error);
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                    });
                });
        },
        assignTo: async function () {
            let vm = this;
            let unassign = true;
            let data = {};
            if (this.processing_status == 'With Approver') {
                unassign =
                    this.proposal.assigned_approver != null &&
                    this.proposal.assigned_approver != 'undefined'
                        ? false
                        : true;
                data = { assessor_id: this.proposal.assigned_approver };
            } else {
                unassign =
                    this.proposal.assigned_officer != null &&
                    this.proposal.assigned_officer != 'undefined'
                        ? false
                        : true;
                data = { assessor_id: this.proposal.assigned_officer };
            }

            let endpoint = 'unassign';
            let payload = {};
            if (!unassign) {
                endpoint = 'assign_to';
                payload = {
                    body: JSON.stringify(data),
                    method: 'POST',
                };
            }

            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal,
                    `${vm.proposal.id}/${endpoint}`
                ),
                payload
            )
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.json().then((json) => {
                            throw new Error(json);
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then((data) => {
                    vm.proposal = Object.assign({}, data);
                    vm.updateAssignedOfficerSelect();
                })
                .catch((error) => {
                    this.updateAssignedOfficerSelect();
                    console.error(error);
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                    });
                });
        },
        backToAssessor: async function () {
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal,
                    this.proposal.id + '/back_to_assessor'
                ),
                {
                    method: 'PATCH',
                }
            )
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.json().then((json) => {
                            throw new Error(json);
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then((data) => {
                    this.proposedApprovalState = '';
                    this.proposal = Object.assign({}, data);
                    this.uuid++;
                })
                .catch((error) => {
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                    });
                });
        },
        switchStatus: async function (new_status) {
            let data = {
                status: new_status,
                approver_comment: this.approver_comment,
            };

            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal,
                    this.proposal.id + '/switch_status'
                ),
                {
                    body: JSON.stringify(data),
                    method: 'POST',
                }
            )
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.json().then((json) => {
                            throw new Error(json);
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then((data) => {
                    this.proposal = Object.assign({}, data);
                    this.approver_comment = '';
                    this.$nextTick(() => {
                        this.initialiseAssignedOfficerSelect(true);
                        this.updateAssignedOfficerSelect();
                    });
                    //if approver is pushing back proposal to Assessor then navigate the approver back to dashboard page
                    if (
                        this.proposal.processing_status_id ==
                            constants.PROPOSAL_STATUS.WITH_APPROVER.ID &&
                        (new_status ==
                            constants.PROPOSAL_STATUS
                                .WITH_ASSESSOR_CONDITIONS ||
                            new_status ==
                                constants.PROPOSAL_STATUS.WITH_ASSESSOR)
                    ) {
                        this.$router.push({ path: '/internal' });
                    }
                })
                .catch((error) => {
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                    });
                });
        },
        initialiseAssignedOfficerSelect: function (reinit = false) {
            let vm = this;
            if (reinit) {
                $(vm.$refs.assigned_officer).data('select2')
                    ? $(vm.$refs.assigned_officer).select2('destroy')
                    : '';
            }
            // Assigned officer select
            $(vm.$refs.assigned_officer)
                .select2({
                    theme: 'bootstrap',
                    allowClear: true,
                    placeholder: 'Select Officer',
                })
                .on('select2:select', function (e) {
                    var selected = $(e.currentTarget);
                    if (vm.proposal.processing_status == 'With Approver') {
                        vm.proposal.assigned_approver = selected.val();
                    } else {
                        vm.proposal.assigned_officer = selected.val();
                    }
                    vm.assignTo();
                })
                .on('select2:unselecting', function () {
                    var self = $(this);
                    setTimeout(() => {
                        self.select2('close');
                    }, 0);
                })
                .on('select2:unselect', function () {
                    if (vm.proposal.processing_status == 'With Approver') {
                        vm.proposal.assigned_approver = null;
                    } else {
                        vm.proposal.assigned_officer = null;
                    }
                    vm.assignTo();
                });
        },
        initialiseSelects: function () {
            let vm = this;
            if (!vm.initialisedSelects) {
                vm.initialiseAssignedOfficerSelect();
                vm.initialisedSelects = true;
            }
        },
        fetchAdditionalDocumentTypesDict: async function () {
            const response = await fetch('/api/additional_document_types_dict');
            const resData = await response.json();
            this.applySelect2ToAdditionalDocumentTypes(resData);
        },
        revisionToDisplay: async function (revision) {
            let payload = {
                revision_id: revision.revision_id,
                debug: this.debug,
            };

            await fetch(
                `/api/proposal/${
                    this.$route.params.proposal_id
                }/revision_version?${new URLSearchParams(payload)}`
            )
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.json().then((json) => {
                            throw new Error(json);
                        });
                    } else {
                        return response.json();
                    }
                })
                .then((response) => {
                    this.proposal = Object.assign({}, response);
                    this.current_revision_id = revision.revision_id;
                    this.uuid++;
                })
                .catch((error) => {
                    console.error(error);
                });
        },
        fetchProposal: async function () {
            let vm = this;
            vm.loading = true;
            let payload = {
                debug: this.debug,
            };
            fetch(
                `/api/proposal/${
                    this.$route.params.proposal_id
                }?${new URLSearchParams(payload)}`
            )
                .then(async (response) => {
                    if (!response.ok) {
                        const text = await response.json();
                        throw new Error(text);
                    } else {
                        return await response.json();
                    }
                })
                .then((data) => {
                    vm.proposal = Object.assign({}, data);
                    // Dict of the latest revision's parameters
                    vm.latest_revision = Object.assign(
                        {},
                        data.lodgement_versions[0]
                    );
                    // Set current reivsion id to the latest one on creation
                    vm.current_revision_id = vm.latest_revision.revision_id;
                    vm.hasAmendmentRequest = this.proposal.hasAmendmentRequest;
                    if (vm.debug == true) {
                        this.showingProposal = true;
                    }
                    if (
                        [constants.PROPOSAL_STATUS.WITH_REFERRAL.TEXT].includes(
                            vm.proposal.processing_status
                        )
                    ) {
                        $(
                            'textarea.referral-comment:enabled:visible:not([readonly="readonly"]):first'
                        ).focus();
                    }
                    this.$nextTick(() => {
                        $('textarea').each(function () {
                            if ($(this)[0].scrollHeight > 70) {
                                $(this).height($(this)[0].scrollHeight - 30);
                            }
                        });
                        if (
                            constants.PROPOSAL_STATUS.APPROVED_EDITING_INVOICING
                                .ID == vm.proposal.processing_status_id &&
                            vm.profile.is_finance_officer &&
                            $('#invoicing-form').length
                        ) {
                            $(document).scrollTop(
                                $('#invoicing-form').offset()?.top - 300
                            );
                        }
                    });
                })
                .catch((error) => {
                    console.error(error);
                })
                .finally(() => {
                    vm.loading = false;
                });
        },
        updateRequirement: function (newRequirement) {
            var oldRequirement = this.proposal.requirements.find(
                (requirement) => requirement.id == newRequirement.id
            );
            if (
                typeof oldRequirement === 'object' &&
                !Array.isArray(oldRequirement) &&
                oldRequirement !== null
            ) {
                Object.assign(oldRequirement, newRequirement);
            }
        },
        updateInvoicingDetails: function (value) {
            Object.assign(this.proposal.invoicing_details, value);
        },
        updateGisData: function (property, value) {
            if (!Object.hasOwn(this.proposal, property)) {
                console.warn(`Property ${property} does not exist on proposal`);
                return;
            }

            this.proposal[property];

            if (this.proposal[property].find((item) => item.id == value.id)) {
                this.proposal[property] = this.proposal[property].filter(
                    (item) => item.id != value.id
                );
            } else {
                this.proposal[property].push({
                    id: value.id,
                    name: value.name,
                });
            }
        },
        onFinishedDrawing: function () {
            if (this.$refs.application_form.$refs.component_map.autoSave) {
                this.saveMapFeatures();
            }
        },
        saveMapFeatures: async function () {
            // Save the entire proposal including the map features without reloading the map
            await this.save(false, false).then(() => {
                this.savingProposal = false;
            });
        },
        refreshFromResponse: function (data) {
            this.proposal = Object.assign({}, data);
        },
    },
};
</script>
