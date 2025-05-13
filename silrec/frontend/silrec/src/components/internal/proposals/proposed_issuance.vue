<template lang="html">
    <div id="proposedIssuanceApproval">
        <modal
            transition="modal fade"
            :title="title"
            large
            :scrollable="true"
            @ok="ok()"
            @cancel="cancel()"
        >
            <ProposedIssuanceForm
                v-if="proposal"
                ref="proposed_approval_form"
                :key="proposedApprovalKey"
                :proposal="proposal"
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
                :applicant_email="applicant_email"
                :proposed-approval-key="proposedApprovalKey"
                :proposed-approval-state="proposedApprovalState"
                :always-show-documents="true"
                :readonly="readonly"
            />
        </modal>
    </div>
</template>

<script>
import { constants } from '@/utils/hooks.js';
import modal from '@vue-utils/bootstrap-modal.vue';
import ProposedIssuanceForm from '@/components/internal/proposals/proposed_issuance_form.vue';
export default {
    name: 'ProposedApproval',
    components: {
        modal,
        ProposedIssuanceForm,
    },
    props: {
        proposal_id: {
            type: Number,
            required: true,
        },
        processing_status: {
            type: String,
            required: true,
        },
        proposal_type: {
            type: String,
            required: true,
        },
        proposedApprovalKey: {
            type: String,
        },
        proposedApprovalState: {
            type: String,
        },
        proposal: {
            type: Object,
            required: true,
        },
    },
    data: function () {
        return {
            isModalOpen: false,
            title: '',
        };
    },
    computed: {
        submitter_email: function () {
            if (this.proposal.submitter) {
                return this.proposal.submitter.email;
            } else {
                return this.proposal.applicant_obj.email;
            }
        },
        applicant_email: function () {
            return this.proposal && this.proposal.applicant.email
                ? this.proposal.applicant.email
                : '';
        },
        readonly: function () {
            let readonly =
                constants.PROPOSAL_STATUS.WITH_APPROVER.ID ==
                this.proposal.processing_status_id
                    ? true
                    : false;
            return readonly;
        },
    },
    watch: {
        // eslint-disable-next-line no-unused-vars
        isModalOpen: function (newVal, oldVal) {
            if (newVal) {
                this.$nextTick(() => {
                    this.$refs.proposed_approval_form.focus();
                    if (
                        this.proposal.proposed_issuance_approval &&
                        this.proposal.proposed_issuance_approval.decision
                    ) {
                        this.$refs.proposed_approval_form.selectedDecision =
                            this.proposal.proposed_issuance_approval.decision;
                        if (
                            this.proposal.proposed_issuance_approval.decision ==
                            constants.APPROVAL_DECISIONS
                                .APPROVE_ADD_TO_EXISTING_COMPETITIVE_PROCESS
                        ) {
                            this.$refs.proposed_approval_form.initialiseExistingCompetitiveProcessSelect2();
                        }
                    }
                });
            }
        },
    },
    mounted: function () {
        this.$nextTick(() => {
            this.title = this.$refs.proposed_approval_form.title;
        });
    },
    methods: {
        ok: async function () {
            await this.$refs.proposed_approval_form.validateForm();
        },
        cancel: function () {
            this.close();
        },
        close: function () {
            this.isModalOpen = false;
            this.approval = {};
            this.$refs.proposed_approval_form.errorString = false;
        },
    },
};
</script>
