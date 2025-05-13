<template id="proposal_approval">
    <div>
        <BootstrapAlert
            v-if="displayApprovedMessage"
            type="success"
            icon="check-circle-fill"
        >
            {{ applicationTypeNameDisplay }} {{ approveDecisionText }} on
            {{ proposalApprovedOn }} by {{ proposalApprovedBy }}.
        </BootstrapAlert>

        <BootstrapAlert
            v-if="displayDeclinedMsg"
            type="warning"
            icon="exclamation-triangle-fill"
        >
            This Proposal was declined. The decision was emailed to
            {{ proposal.submitter.email }}
        </BootstrapAlert>

        <FormSection
            :form-collapse="false"
            :label="decisionLabel"
            index="proposal_decision"
        >
            <ProposedIssuanceForm
                v-if="proposal"
                ref="proposed_approval_form"
                :key="proposedApprovalKey"
                :proposal="proposal"
                :decision-label="decisionLabel"
                :processing_status="proposal.processing_status"
                :proposal_id="proposal.id"
                :proposal_type="
                    proposal.proposal_type ? proposal.proposal_type.code : ''
                "
                :submitter_email="
                    proposal.submitter && proposal.submitter.email
                        ? proposal.submitter.email
                        : ''
                "
                :applicant_email="proposal.applicant_obj.email"
                :proposed-approval-key="proposedApprovalKey"
                :proposed-approval-state="proposedApprovalState"
                :proposal-is-approved="displayApprovedMessage"
                :readonly="true"
            />
        </FormSection>

        <!-- Can only have proposed documents (from the assessor) when applying for a lease/license -->
        <FormSection
            v-if="
                proposal.application_type &&
                proposal.application_type.name == 'lease_licence'
            "
            :form-collapse="false"
            label="Documents"
            index="proposal_documents"
        >
            <ProposedApprovalDocuments
                v-if="proposal"
                ref="proposed_issuance_documents"
                :key="selectedApprovalTypeId"
                :proposal="proposal"
                :proposal-id="proposal.id"
                :processing_status="proposal.processing_status"
                :approval-types="approvalTypes"
                :proposal_id="proposal.id"
                :selected-approval-type-id="selectedApprovalTypeId"
                :readonly="true"
            />
        </FormSection>

        <FormSection
            v-if="show_invoicing_details"
            :form-collapse="false"
            label="Invoicing Details"
            index="proposal_invoicing_details"
        >
            <InvoicingDetails
                v-if="proposal.approval && proposal.invoicing_details"
                ref="invoicing_details"
                context="Proposal"
                :invoicing-details="proposal.invoicing_details"
                :start-date="proposal.approval.start_date"
                :expiry-date="proposal.approval.expiry_date"
                :issue-date="proposal.approval.issue_date"
                :proposal-processing-status-id="proposal.processing_status_id"
                :approval-type="proposal.approval.approval_type"
                :proposal-type-code="proposal.proposal_type.code"
                @update-invoicing-details="
                    $emit('updateInvoicingDetails', $event)
                "
            />
        </FormSection>
    </div>
</template>
<script>
import { api_endpoints, helpers, utils } from '@/utils/hooks';
import { constants } from '@/utils/hooks';
import ProposedIssuanceForm from '@/components/internal/proposals/proposed_issuance_form.vue';
import ProposedApprovalDocuments from '@/components/internal/proposals/proposed_approval_documents.vue';
import FormSection from '@/components/forms/section_toggle.vue';
import InvoicingDetails from '@/components/common/invoicing_details.vue';

export default {
    name: 'InternalProposalApproval',
    components: {
        ProposedIssuanceForm,
        ProposedApprovalDocuments,
        FormSection,
        InvoicingDetails,
    },
    props: {
        proposal: {
            type: Object,
            required: true,
        },
        proposedApprovalState: {
            type: String,
            default: '',
        },
        proposedApprovalKey: {
            type: Object,
            default: null,
        },
        readonly: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['updateInvoicingDetails'],
    data: function () {
        let vm = this;
        return {
            proposedDecision: 'proposal-decision-' + vm._.uid,
            proposedLevel: 'proposal-level-' + vm._.uid,
            uploadedFile: null,
            component_site_selection_key: '',
            approvalTypes: [],
            selectedApprovalTypeId: null,
        };
    },
    computed: {
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
                this.isFinalised;
            return ret_val;
        },
        display_requirements: function () {
            let ret_val =
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID ||
                ((this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.WITH_APPROVER.ID ||
                    this.isFinalised) &&
                    this.showingRequirements);
            return ret_val;
        },
        showElectoralRoll: function () {
            let show = false;
            if (
                this.proposal &&
                ['wla', 'mla'].includes(this.proposal.application_type_code)
            ) {
                show = true;
            }
            return show;
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
                this.proposal.processing_status_id ===
                    constants.PROPOSAL_STATUS.DECLINED.ID ||
                this.proposal.processing_status_id ===
                    constants.PROPOSAL_STATUS.APPROVED.ID
            );
        },
        hasAssessorMode: function () {
            return this.proposal &&
                this.proposal.assessor_mode.has_assessor_mode
                ? true
                : false;
        },
        canSeeSubmission: function () {
            return (
                this.proposal &&
                this.proposal.processing_status !=
                    'With Assessor (Requirements)' &&
                this.proposal.processing_status != 'With Approver' &&
                !this.isFinalised
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
        approvalIssueDate: function () {
            if (this.proposal) {
                return this.proposal.approval_issue_date;
            }
            return '';
        },
        proposalApprovedOn: function () {
            return this.proposal.approved_on;
        },
        proposalApprovedBy: function () {
            return this.proposal.approved_by;
        },
        approveDecisionText: function () {
            /** Returns approval decision text part to be used in the green bar */

            if (
                this.proposal.proposed_issuance_approval.decision ===
                constants.APPROVAL_DECISIONS.APPROVE_LEASE_LICENCE
            ) {
                return 'was approved to proceed to a full application';
            } else if (
                this.proposal.proposed_issuance_approval.decision ===
                constants.APPROVAL_DECISIONS.APPROVE_COMPETITIVE_PROCESS
            ) {
                return 'was approved to proceed to a Competitive Process';
            } else if (
                this.proposal.proposed_issuance_approval.decision ===
                constants.APPROVAL_DECISIONS
                    .APPROVE_ADD_TO_EXISTING_COMPETITIVE_PROCESS
            ) {
                return 'was approved and added to an existing Competitive Process';
            } else {
                return 'was approved';
            }
        },
        show_invoicing_details: function () {
            if (this.debug) return true;

            let display = false;
            if (
                this.proposal &&
                this.proposal.application_type &&
                this.proposal.application_type.name ===
                    constants.APPLICATION_TYPES.LEASE_LICENCE &&
                this.proposal.processing_status_id ===
                    constants.PROPOSAL_STATUS.APPROVED_EDITING_INVOICING.ID &&
                this.proposal.accessing_user_roles.includes(
                    constants.ROLES.FINANCE.ID
                )
            )
                display = true;
            return display;
        },
        applicationTypeNameDisplay: function () {
            /** Returns approval application type text part to be used in the green bar */

            if (this.proposal) {
                if (
                    [
                        constants.APPROVAL_DECISIONS.APPROVE_LEASE_LICENCE,
                        constants.APPROVAL_DECISIONS
                            .APPROVE_COMPETITIVE_PROCESS,
                        constants.APPROVAL_DECISIONS
                            .APPROVE_ADD_TO_EXISTING_COMPETITIVE_PROCESS,
                    ].includes(
                        this.proposal.proposed_issuance_approval.decision
                    )
                ) {
                    return `This ${this.proposal.application_type.name_display}`;
                } else {
                    return `This proposal for a ${this.proposal.application_type.name_display}`;
                }
            }
            return '';
        },
        displayAwaitingPaymentMsg: function () {
            let display = false;
            if (
                this.proposal.processing_status_id ===
                constants.PROPOSAL_STATUS.AWAITING_PAYMENT.ID
            ) {
                display = true;
            }
            return display;
        },
        displayApprovedMessage: function () {
            return [
                constants.PROPOSAL_STATUS.APPROVED.ID,
                constants.PROPOSAL_STATUS.APPROVED_EDITING_INVOICING.ID,
                constants.PROPOSAL_STATUS.APPROVED_APPLICATION.ID,
                constants.PROPOSAL_STATUS.APPROVED_COMPETITIVE_PROCESS.ID,
            ].includes(this.proposal.processing_status_id);
        },
        displayDeclinedMsg: function () {
            let display = false;
            if (
                this.proposal.processing_status_id ===
                constants.PROPOSAL_STATUS.DECLINED.ID
            ) {
                display = true;
            }
            return display;
        },
        approvalExpiryDate: function () {
            let returnDate = null;
            if (this.proposal && this.proposal.end_date) {
                returnDate = moment(
                    this.proposal.end_date,
                    'YYYY-MM-DD'
                ).format('DD/MM/YYYY');
            }
            return returnDate;
        },
        isApprovalLevel: function () {
            return this.proposal.approval_level != null ? true : false;
        },
        decisionLabel: function () {
            let decision_label = 'Decision';
            if (
                this.proposal.processing_status_id ==
                constants.PROPOSAL_STATUS.WITH_APPROVER.ID
            ) {
                decision_label = 'Proposed Decision';
            }
            return decision_label;
        },
    },
    created: function () {
        let vm = this;
        let initialisers = [utils.fetchApprovalTypes()];
        Promise.all(initialisers).then((data) => {
            for (let approvalType of data[0]) {
                vm.approvalTypes.push(approvalType);
            }
            if (vm.proposal.proposed_issuance_approval) {
                vm.selectedApprovalTypeId =
                    vm.proposal.proposed_issuance_approval.approval_type;
            }
        });
    },
    mounted: function () {},
    methods: {
        readFile: function () {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedFile)[0];
            if (input.files && input.files[0]) {
                let reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function (e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.uploadedFile = _file;
            vm.save();
        },
        removeFile: function () {
            let vm = this;
            vm.uploadedFile = null;
            vm.save();
        },
        save: function () {
            let vm = this;
            let data = new FormData(vm.form);
            data.append('approval_level_document', vm.uploadedFile);
            if (vm.proposal.approval_level_document) {
                data.append(
                    'approval_level_document_name',
                    vm.proposal.approval_level_document[0]
                );
            }
            vm.$http
                .post(
                    helpers.add_endpoint_json(
                        api_endpoints.proposals,
                        vm.proposal.id + '/approval_level_document'
                    ),
                    data,
                    {
                        emulateJSON: true,
                    }
                )
                .then(
                    (res) => {
                        vm.proposal = res.body;
                        vm.$emit('refreshFromResponse', res);
                    },
                    (err) => {
                        swal(
                            'Submit Error',
                            helpers.apiVueResourceError(err),
                            'error'
                        );
                    }
                );
        },
        uploadedFileName: function () {
            return this.uploadedFile != null ? this.uploadedFile.name : '';
        },
        addRequirement() {
            this.$refs.requirement_detail.isModalOpen = true;
        },
        removeRequirement(_id) {
            let vm = this;
            swal({
                title: 'Remove Requirement',
                text: 'Are you sure you want to remove this requirement?',
                type: 'warning',
                showCancelButton: true,
                reverseButtons: true,
                confirmButtonText: 'Remove Requirement',
                confirmButtonColor: '#d9534f',
            }).then(
                () => {
                    vm.$http
                        .delete(
                            helpers.add_endpoint_json(
                                api_endpoints.proposal_requirements,
                                _id
                            )
                        )
                        .then(
                            (response) => {
                                if (response.ok) {
                                    vm.$refs.requirements_datatable.vmDataTable.ajax.reload();
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                },
                () => {}
            );
        },
    },
};
</script>
<style scoped></style>
