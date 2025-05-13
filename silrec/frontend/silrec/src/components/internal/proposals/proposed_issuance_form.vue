<template lang="html">
    <div :id="'proposedIssuanceApproval' + uuid" :key="uuid">
        <div class="container-fluid">
            <form
                :id="'proposedIssuanceForm' + uuid"
                class="form-horizontal needs-validation"
                name="proposedIssuanceForm"
                novalidate
            >
                <div class="row pt-2">
                    <VueAlert
                        v-if="errorString && errorString.length > 0"
                        type="danger"
                    >
                        <!-- eslint-disable-next-line vue/no-v-html -->
                        <strong>{{ errorString }}</strong>
                        <!--eslint-enable-->
                    </VueAlert>
                    <div v-if="registrationOfInterest" class="col-sm-12">
                        <div
                            v-if="!proposal.proposed_decline_status"
                            class="row mb-3"
                        >
                            <label class="col-sm-3 col-form-label">{{
                                decisionLabel
                            }}</label>
                            <div class="col-sm-9">
                                <ul class="list-group">
                                    <li
                                        v-for="(
                                            text, key
                                        ) in approvalDecisionText"
                                        :key="key"
                                        class="list-group-item"
                                    >
                                        <input
                                            :id="key"
                                            v-model="selectedDecision"
                                            type="radio"
                                            class="form-check-input me-3"
                                            :name="key"
                                            :value="key"
                                            :disabled="readonly"
                                            @change="selectedDecisionChanged"
                                        />
                                        <label
                                            class="form-check-label"
                                            :for="key"
                                            style="font-weight: normal"
                                            >{{ text }}</label
                                        >
                                    </li>
                                </ul>
                            </div>
                        </div>

                        <div
                            v-if="
                                selectedDecision ==
                                constants.APPROVAL_DECISIONS
                                    .APPROVE_ADD_TO_EXISTING_COMPETITIVE_PROCESS
                            "
                            class="row mb-3 align-items-center"
                        >
                            <label class="col-sm-3 col-form-label"
                                >Competitive Process</label
                            >
                            <div
                                v-if="proposal.competitive_process_to_copy_to"
                                class="col-sm-9"
                            >
                                <span class="badge bg-primary p-2 fs-6">
                                    <router-link
                                        class="text-white"
                                        :to="{
                                            name: 'internal-competitive-process',
                                            params: {
                                                competitive_process_id:
                                                    proposal.competitive_process_to_copy_to,
                                            },
                                        }"
                                        target="_blank"
                                        >{{
                                            competitive_process_lodgement_number
                                        }}</router-link
                                    >
                                </span>
                            </div>
                            <div v-else class="col-sm-9">
                                <select
                                    id="cp"
                                    ref="cp"
                                    class="form-select"
                                    required
                                ></select>
                                <div class="invalid-feedback">
                                    Please search and select a competitive
                                    process.
                                </div>
                            </div>
                        </div>
                        <div
                            v-if="proposal.proposed_decline_status"
                            class="row mb-3 align-items-center"
                        >
                            <label class="col-sm-3 col-form-label">
                                {{ decisionLabel }}
                            </label>
                            <div class="col-sm-9">
                                <span class="badge bg-danger p-2 fs-6">
                                    Decline</span
                                >
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label
                                for="registration_of_interest_details"
                                class="col-sm-3 col-form-label"
                                >Details</label
                            >
                            <div class="col-sm-9">
                                <div class="col-sm-9">
                                    <RichText
                                        id="registration-of-interest-details-approve"
                                        ref="registration_of_interest_details"
                                        :key="uuid"
                                        :proposal-data="proposedDecisionDetails"
                                        placeholder-text="Add some details here"
                                        :readonly="readonly"
                                        @text-changed="
                                            updateProposedDecisionDetails(
                                                $event
                                            )
                                        "
                                    />
                                </div>
                                <div
                                    class="details-invalid-feedback invalid-feedback"
                                >
                                    Please enter some details.
                                </div>
                            </div>
                        </div>
                        <div class="row mb-4">
                            <label
                                for="approval_bcc"
                                class="col-sm-3 col-form-label"
                                >Proposed BCC email</label
                            >
                            <div class="col-sm-9">
                                <input
                                    ref="bcc_email"
                                    v-model="approval.bcc_email"
                                    type="text"
                                    class="form-control"
                                    name="approval_bcc"
                                    :readonly="readonly"
                                />
                            </div>
                        </div>
                        <div
                            v-if="proposal.proposed_issuance_approval"
                            class="row pt-2"
                        >
                            <div class="col-sm-12">
                                <BootstrapAlert
                                    v-if="
                                        submitter_email &&
                                        applicant_email &&
                                        submitter_email != applicant_email
                                    "
                                >
                                    After approving this proposal, the approval
                                    will be emailed to
                                    <span class="fw-bold">{{
                                        submitter_email
                                    }}</span>
                                    and
                                    <span class="fw-bold">{{
                                        applicant_email
                                    }}</span>
                                </BootstrapAlert>
                                <BootstrapAlert v-else>
                                    After approving this proposal, the approval
                                    will be emailed to
                                    <span class="fw-bold">{{
                                        submitter_email
                                    }}</span>
                                </BootstrapAlert>
                            </div>
                        </div>
                        <div
                            v-if="
                                !proposalDeclined &&
                                proposal.proposed_decline_status
                            "
                            class="row pt-2"
                        >
                            <div class="col-sm-12">
                                <BootstrapAlert
                                    v-if="
                                        submitter_email &&
                                        applicant_email &&
                                        submitter_email != applicant_email
                                    "
                                >
                                    After declining this proposal, the
                                    notification will be emailed to
                                    <span class="fw-bold">{{
                                        submitter_email
                                    }}</span>
                                    and
                                    <span class="fw-bold">{{
                                        applicant_email
                                    }}</span>
                                </BootstrapAlert>
                                <BootstrapAlert v-else>
                                    After declining this proposal, the
                                    notification will be emailed to
                                    <span class="fw-bold">{{
                                        submitter_email
                                    }}</span>
                                </BootstrapAlert>
                            </div>
                        </div>
                    </div>
                    <div v-if="leaseLicence" class="col-sm-12">
                        <div class="form-group">
                            <div
                                v-if="proposal.proposed_decline_status"
                                class="row mb-3 align-items-center"
                            >
                                <label class="col-sm-3 col-form-label">
                                    {{ decisionLabel }}
                                </label>
                                <div class="col-sm-9">
                                    <span class="badge bg-danger p-2 fs-6">
                                        Decline</span
                                    >
                                </div>
                            </div>
                            <div v-else class="row mb-3">
                                <label class="col-sm-3 col-form-label">{{
                                    decisionLabel
                                }}</label>
                                <div class="col-sm-9">
                                    <span class="badge bg-success p-2 fs-6">
                                        Approve</span
                                    >
                                </div>
                            </div>
                            <div
                                v-if="!proposal.proposed_decline_status"
                                class="row mb-3"
                            >
                                <label
                                    for="approvalType"
                                    class="col-sm-2 col-form-label text-nowrap"
                                    >Approval Type</label
                                >
                                <div class="col-sm-1 col-form-label">
                                    <i
                                        v-if="
                                            isRenewal &&
                                            !assessedBy &&
                                            !assessedOn
                                        "
                                        class="text-primary fa-solid fa-circle-info"
                                        data-color="info"
                                        data-bs-toggle="tooltip"
                                        data-bs-placement="right"
                                        title="The approval type has been set to the approval type of the current approval."
                                    ></i>
                                </div>
                                <div class="col-sm-9">
                                    <select
                                        ref="select_approvaltype"
                                        v-model="selectedApprovalTypeId"
                                        :disabled="readonly"
                                        class="form-select"
                                        required
                                        @change="
                                            updateApprovalTypeForExisingDocuments
                                        "
                                    >
                                        <option
                                            v-for="atype in approvalTypes"
                                            :key="atype.name"
                                            :value="atype.id"
                                        >
                                            {{ atype.name }}
                                        </option>
                                    </select>
                                    <div class="invalid-feedback">
                                        Please select an Approval Type.
                                    </div>
                                </div>
                            </div>
                            <div
                                v-if="!proposal.proposed_decline_status"
                                class="row mb-3"
                            >
                                <label
                                    for="start_date"
                                    class="col-sm-2 col-form-label text-nowrap"
                                    >Commencement</label
                                >
                                <div class="col-sm-1 col-form-label">
                                    <i
                                        v-if="
                                            isRenewal &&
                                            !assessedBy &&
                                            !assessedOn
                                        "
                                        class="text-primary fa-solid fa-circle-info"
                                        data-bs-toggle="tooltip"
                                        data-bs-placement="right"
                                        title="The commencement date has been set to one day after the expiry date of the current approval."
                                    ></i>
                                </div>
                                <div class="col-sm-9">
                                    <div
                                        ref="start_date"
                                        class="input-group date"
                                    >
                                        <input
                                            v-model="approval.start_date"
                                            :disabled="readonly"
                                            type="date"
                                            class="form-control"
                                            name="start_date"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please select a commencement date.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-show="startDateErrorString" class="row">
                                <VueAlert class="col-sm-12" type="danger"
                                    ><strong>{{ startDateErrorString }}</strong>
                                </VueAlert>
                            </div>
                            <div
                                v-if="!proposal.proposed_decline_status"
                                class="row mb-3"
                            >
                                <label
                                    for="due_date"
                                    class="col-sm-2 col-form-label text-nowrap"
                                    >Expiry</label
                                >
                                <div class="col-sm-1 col-form-label">
                                    <i
                                        v-if="
                                            isRenewal &&
                                            !assessedBy &&
                                            !assessedOn
                                        "
                                        class="text-primary fa-solid fa-circle-info"
                                        data-bs-toggle="tooltip"
                                        data-bs-placement="right"
                                        title="The duration has been set to the same duration as the current approval."
                                    ></i>
                                </div>
                                <div class="col-sm-9">
                                    <div
                                        ref="due_date"
                                        class="input-group date"
                                    >
                                        <input
                                            v-model="approval.expiry_date"
                                            :disabled="readonly"
                                            type="date"
                                            class="form-control"
                                            name="due_date"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please select a expiry date.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-show="toDateErrorString" class="row">
                                <VueAlert class="col-sm-12" type="danger"
                                    ><strong>{{ toDateErrorString }}</strong>
                                </VueAlert>
                            </div>
                            <div class="row mb-3">
                                <label
                                    for="lease_licence_details"
                                    class="col-sm-3 col-form-label text-nowrap"
                                    >Details</label
                                >
                                <div class="col-sm-9">
                                    <RichText
                                        id="lease-licence-details-approve"
                                        ref="lease_licence_details"
                                        :key="uuid"
                                        :proposal-data="proposedDecisionDetails"
                                        :placeholder-text="
                                            selectedApprovalTypeDetailsPlaceholder
                                        "
                                        :readonly="readonly"
                                        @text-changed="
                                            updateProposedDecisionDetails(
                                                $event
                                            )
                                        "
                                    />
                                    <div
                                        class="details-invalid-feedback invalid-feedback"
                                    >
                                        Please enter some details.
                                    </div>
                                </div>
                            </div>
                            <div v-if="selectedApprovalTypeId" class="row mb-3">
                                <label
                                    for="proposed_approval_documents"
                                    class="col-sm-3 col-form-label text-nowrap"
                                    >File</label
                                >
                                <div class="col-sm-9">
                                    <FileField
                                        id="proposal_approve_decline_documents"
                                        ref="proposal_approve_decline_documents"
                                        name="proposal_approve_decline_documents"
                                        :is-repeatable="true"
                                        :document-action-url="fileUrl"
                                        :replace_button_by_text="true"
                                        :readonly="
                                            !selectedApprovalTypeId || readonly
                                        "
                                        :approval_type="selectedApprovalTypeId"
                                    />
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    for="approval_cc"
                                    class="col-sm-2 col-form-label text-nowrap"
                                    >CC Emails</label
                                >
                                <div class="col-sm-1 col-form-label">
                                    <i
                                        v-if="
                                            isRenewal &&
                                            approval.cc_email &&
                                            !assessedBy &&
                                            !assessedOn
                                        "
                                        class="text-primary fa-solid fa-circle-info"
                                        data-bs-toggle="tooltip"
                                        data-bs-placement="right"
                                        title="Emails have been applied from the current approval."
                                    ></i>
                                </div>
                                <div class="col-sm-9">
                                    <input
                                        ref="cc_email"
                                        v-model="cc_email"
                                        type="text"
                                        class="form-control"
                                        name="approval_cc"
                                        :disabled="readonly"
                                    />
                                </div>
                            </div>
                        </div>
                        <div
                            v-if="
                                (leaseLicence &&
                                    !withApprover &&
                                    !proposalIsApproved &&
                                    !proposalDeclined) ||
                                alwaysShowDocuments
                            "
                            class="form-group"
                        >
                            <hr />
                            <ProposedApprovalDocuments
                                v-if="proposal"
                                ref="proposed_issuance_documents"
                                :key="selectedApprovalTypeId"
                                :proposal="proposal"
                                :proposal-id="proposal.id"
                                :processing_status="proposal.processing_status"
                                :approval-types="approvalTypes"
                                :selected-approval-type-id="
                                    selectedApprovalTypeId
                                "
                                :selected-document-types="
                                    approval.selected_document_types
                                "
                                :readonly="withApprover"
                            />
                        </div>
                        <div>
                            <div class="row mb-3">
                                <div class="col-sm-4">
                                    <label
                                        class="col-form-label text-nowrap"
                                        for="recordManagementNumber"
                                        >Record Management Number</label
                                    >
                                </div>
                                <div class="col-sm-1 col-form-label">
                                    <i
                                        v-if="
                                            isRenewal &&
                                            !assessedBy &&
                                            !assessedOn
                                        "
                                        class="text-primary fa-solid fa-circle-info"
                                        data-bs-toggle="tooltip"
                                        data-bs-placement="right"
                                        title="The Record Management Number has been applied from the current approval."
                                    ></i>
                                </div>
                                <div class="col-sm-7">
                                    <input
                                        v-model="
                                            approval.record_management_number
                                        "
                                        class="form-control"
                                        type="text"
                                        required
                                        :readonly="readonly"
                                    />
                                    <div class="invalid-feedback">
                                        Please enter a record management number.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </div>
        <div v-if="issuingApproval" class="container">
            <div class="row">
                <BootstrapSpinner class="text-primary" />
            </div>
        </div>
        <!-- eslint-disable-next-line vue/no-deprecated-slot-attribute -->
        <div slot="footer"></div>
        <!--eslint-enable-->
    </div>
</template>

<script>
import VueAlert from '@vue-utils/alert.vue';
import RichText from '@/components/forms/RichText.vue';
import { v4 as uuid } from 'uuid';

import { api_endpoints, constants, helpers, utils } from '@/utils/hooks';
import FileField from '@/components/forms/filefield_immediate.vue';
import ProposedApprovalDocuments from '@/components/internal/proposals/proposed_approval_documents.vue';
import Swal from 'sweetalert2';
import { initTooltipStyling } from '@/components/common/style_functions.js';

export default {
    name: 'ProposedApprovalForm',
    components: {
        VueAlert,
        RichText,
        FileField,
        ProposedApprovalDocuments,
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
        proposalIsApproved: {
            type: Boolean,
            required: false,
        },
        readonly: {
            type: Boolean,
            default: false,
        },
        submitter_email: {
            type: String,
            required: true,
        },
        applicant_email: {
            type: String,
            default: null,
        },
        proposedApprovalKey: {
            type: String,
            default: '0',
        },
        proposedApprovalState: {
            type: String,
            default: '',
        },
        proposal: {
            type: Object,
            required: true,
        },
        decisionLabel: {
            type: String,
            default: 'Decision',
        },
        alwaysShowDocuments: {
            type: Boolean,
            default: false,
        },
    },
    data: function () {
        return {
            constants: constants,
            uuid: uuid(),
            selectedDecision:
                constants.APPROVAL_DECISIONS.APPROVE_LEASE_LICENCE,
            form: null,
            approval: {},
            approvalTypes: [],
            selectedApprovalType: {},
            selectedApprovalTypeId: null,
            issuingApproval: false,
            approvalDecisionText: {
                [constants.APPROVAL_DECISIONS.APPROVE_LEASE_LICENCE]:
                    'Invite Proponent to Apply for a Lease or Licence',
                [constants.APPROVAL_DECISIONS.APPROVE_COMPETITIVE_PROCESS]:
                    'Start Competitive Process based on this Registration of Interest',
                [constants.APPROVAL_DECISIONS
                    .APPROVE_ADD_TO_EXISTING_COMPETITIVE_PROCESS]:
                    'Add to Existing Competitive Process',
            },
            errorString: '',
            toDateErrorString: '',
            startDateErrorString: '',
            detailsTexts: {},
        };
    },
    computed: {
        proposalDeclined: function () {
            return (
                this.proposal.processing_status_id ===
                constants.PROPOSAL_STATUS.DECLINED.ID
            );
        },
        selectedApprovalTypeExists: function () {
            if (this.selectedApprovalType && this.selectedApprovalType.id) {
                return true;
            }
            return false;
        },
        fileUrl: function () {
            let endPoint = '/process_lease_licence_approval_document/';
            if (this.proposal.proposed_decline_status) {
                endPoint = '/process_proposed_decline_document/';
            }
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + endPoint
            );
        },
        selectedApprovalDocumentTypes: function () {
            if (this.selectedApprovalType) {
                return this.selectedApprovalType.approval_type_document_types;
            }
            return [];
        },
        selectedApprovalTypeName: function () {
            if (this.selectedApprovalType) {
                return this.selectedApprovalType.name;
            }
            return '';
        },
        selectedApprovalTypeDetailsPlaceholder: function () {
            if (this.selectedApprovalType) {
                return this.selectedApprovalType.details_placeholder;
            }
            return '';
        },
        proposedDecisionDetails: function () {
            /** Returns proposed decision details depending on whether the proposed decision
             *  by the assessor is an approval or a decline.
             */

            // This is here to re-evalute the computed property after fetching details texts
            this.uuid;

            if (
                this.proposal.application_type.name ==
                    constants.APPLICATION_TYPES.REGISTRATION_OF_INTEREST &&
                this.approval.decision
            ) {
                return this.approval.details;
            } else if (
                this.proposal.application_type.name ==
                    constants.APPLICATION_TYPES.LEASE_LICENCE &&
                this.approval.details &&
                this.proposal.proposed_decline_status == false
            ) {
                return this.approval.details;
            } else if (this.proposal.proposed_decline_status) {
                return this.proposal.proposaldeclineddetails.reason;
            } else {
                // Use standard text from admin
                let id = Object.hasOwn(
                    this.$refs,
                    'registration_of_interest_details'
                )
                    ? this.$refs.registration_of_interest_details.id
                    : Object.hasOwn(this.$refs, 'lease_licence_details')
                      ? this.$refs.lease_licence_details.id
                      : '';
                return this.detailsTexts[id] || '';
            }
        },
        title: function () {
            return this.processing_status == 'With Approver'
                ? `Issue Approval for ${this.proposal.application_type.name_display}: ${this.proposal.lodgement_number}`
                : this.isRenewal
                  ? `Propose to Approve ${this.proposal.application_type.name_display}: ${this.proposal.lodgement_number} - Renewal`
                  : `Propose to Approve ${this.proposal.application_type.name_display}: ${this.proposal.lodgement_number}`;
        },
        is_amendment: function () {
            return this.proposal_type == 'Amendment' ? true : false;
        },
        csrf_token: function () {
            return helpers.getCookie('csrftoken');
        },
        withApprover: function () {
            return this.proposal.processing_status_id ==
                constants.PROPOSAL_STATUS.WITH_APPROVER.ID
                ? true
                : false;
        },
        registrationOfInterest: function () {
            if (
                this.proposal &&
                this.proposal.application_type.name ===
                    'registration_of_interest'
            ) {
                return true;
            }
            return false;
        },
        leaseLicence: function () {
            if (
                this.proposal &&
                this.proposal.application_type.name === 'lease_licence'
            ) {
                return true;
            }
            return false;
        },
        isRenewal: function () {
            return this.proposal_type == 'renewal' ? true : false;
        },
        assessedBy: function () {
            if (!this.proposal.proposed_issuance_approval) {
                return null;
            }
            return this.proposal.proposed_issuance_approval.assessed_by;
        },
        assessedOn: function () {
            if (!this.proposal.proposed_issuance_approval) {
                return null;
            }
            return this.proposal.proposed_issuance_approval.assessed_on;
        },
        cc_email: {
            get: function () {
                if (this.proposal.proposed_decline_status) {
                    return this.proposal.proposaldeclineddetails.cc_email;
                }
                return this.approval.cc_email;
            },
            set: function (value) {
                this.approval.cc_email = value;
            },
        },
        competitive_process_lodgement_number: function () {
            if (!this.proposal.competitive_process_to_copy_to) {
                return '';
            }
            return `CP${this.proposal.competitive_process_to_copy_to
                .toString()
                .padStart(6, '0')}`;
        },
    },
    created: async function () {
        let vm = this;
        vm.form = document.forms.proposedIssuanceForm;
        this.approval = Object.assign(
            {},
            this.proposal.proposed_issuance_approval
        );

        let initialisers = [
            utils.fetchApprovalTypes(),
            utils.fetchUrl(`${api_endpoints.details_text}key-value-list/`),
        ];
        Promise.all(initialisers).then((data) => {
            for (let approvalType of data[0]) {
                vm.approvalTypes.push(approvalType);
            }

            // Approval Type
            if (vm.approval.approval_type) {
                vm.selectedApprovalTypeId = vm.approval.approval_type;
            }

            for (let detailText of data[1]) {
                vm.detailsTexts[detailText.target] = detailText.body;
            }
            vm.uuid = uuid();
        });

        this.$nextTick(() => {
            if (this.approval.decision) {
                this.selectedDecision = this.approval.decision;
            } else if (this.proposal.proposed_decline_status) {
                this.selectedDecision = 'decline_application';
            }

            this.initSelectApprovalType();
            initTooltipStyling();
        });
    },
    methods: {
        selectedDecisionChanged: function (event) {
            if (
                event.target.value ==
                constants.APPROVAL_DECISIONS
                    .APPROVE_ADD_TO_EXISTING_COMPETITIVE_PROCESS
            ) {
                this.initialiseExistingCompetitiveProcessSelect2();
                this.$nextTick(() => {
                    $('#cp').select2('open');
                });
            }
        },
        initialiseExistingCompetitiveProcessSelect2: function () {
            let vm = this;
            $('#cp')
                .select2({
                    dropdownParent: $(`#proposedIssuanceApproval${vm.uuid}`),
                    minimumInputLength: 2,
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder:
                        'Start typing the competitive process lodgement number',
                    ajax: {
                        url:
                            api_endpoints.competitive_process + 'select2-list/',
                        dataType: 'json',
                        data: function (params) {
                            let query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
                        },
                    },
                })
                .on('select2:open', function () {
                    $(
                        `#proposedIssuanceApproval${vm.uuid} .select2-search__field`
                    ).focus();
                })
                .on('select2:select', function (e) {
                    vm.approval.competitive_process = e.params.data.id;
                    document.activeElement.blur();
                })
                .on('select2:clear', function () {
                    vm.approval.competitive_process = null;
                });
        },
        focus() {
            this.$nextTick(() => {
                if (this.$refs.registration_of_interest_details) {
                    this.$refs.registration_of_interest_details.focus();
                } else {
                    this.$refs.lease_licence_details.focus();
                }
            });
        },
        updateProposedDecisionDetails(detailsText) {
            console.log('detailsText', detailsText);
            this.approval.details = detailsText;
            if (detailsText) {
                $('.details-invalid-feedback').hide();
            }
        },
        handleApprovalTypeChangeEvent(id) {
            this.updateSelectedApprovalType(id);
            this.updateApprovalTypeForExisingDocuments();
            this.initSelectDocument();
        },
        updateSelectedApprovalType(id) {
            // clear existing doc arrays
            if (this.approval) {
                this.approval.selected_document_types = [];
            }
            if (this.proposal.proposed_issuance_approval) {
                this.proposal.proposed_issuance_approval.selected_document_types =
                    [];
            }

            this.selectedApprovalTypeId = id;
        },
        updateApprovalTypeForExisingDocuments: async function () {
            // Convert existing documents to the new approval type in case the user had
            // accidentally selected the wrong approval type. They can easily delete the documents
            // if they want to replace them with different ones.
            this.approval.approval_type = this.selectedApprovalTypeId;
            const response = await fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposals,
                    this.proposal_id +
                        '/update_lease_licence_approval_documents_approval_type'
                ),
                {
                    body: JSON.stringify(this.approval),
                    method: 'POST',
                }
            );
            if (!response.ok) {
                this.issuingApproval = false;
                this.errorString = await helpers.parseFetchError(response);
            }
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById(
                'proposedIssuanceForm' + vm.uuid
            );
            if (vm.registrationOfInterest) {
                if (
                    '' ==
                    this.$refs.registration_of_interest_details.detailsText
                ) {
                    vm.$nextTick(() => {
                        this.$refs.registration_of_interest_details.focus();
                        $('.details-invalid-feedback').show();
                    });
                    return false;
                }
            }
            if (vm.leaseLicence) {
                if ('' == this.$refs.lease_licence_details.detailsText) {
                    vm.$nextTick(() => {
                        this.$refs.lease_licence_details.focus();
                        $('.details-invalid-feedback').show();
                    });
                    return false;
                }
            }
            if (form.checkValidity()) {
                vm.sendData();
            } else {
                form.classList.add('was-validated');
                $('#proposedIssuanceForm' + vm.uuid)
                    .find(':invalid')
                    .first()
                    .focus();
            }

            return false;
        },
        sendData: async function () {
            this.errorString = '';
            this.issuingApproval = true;
            this.approval.assessment = this.assessment;

            this.$nextTick(async () => {
                if (this.registrationOfInterest) {
                    this.approval.decision = this.selectedDecision;
                } else if (this.leaseLicence) {
                    this.approval.approval_type = this.selectedApprovalTypeId;
                    this.approval.selected_document_types =
                        this.$refs.proposed_issuance_documents.selectedDocumentTypes;
                }
                if (this.proposedApprovalState == 'proposed_approval') {
                    const response = await fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposals,
                            this.proposal_id + '/proposed_approval'
                        ),
                        {
                            body: JSON.stringify(this.approval),
                            method: 'POST',
                        }
                    );
                    if (response.ok) {
                        this.issuingApproval = false;
                        Swal.fire({
                            title: `Proposal to Approve: ${this.proposal.lodgement_number}`,
                            text: 'Submitted successfully.',
                            icon: 'success',
                            confirmButtonText: 'OK',
                        });
                        this.$router.push({ path: '/internal' }); //Navigate to dashboard page after Propose issue.
                    } else {
                        this.issuingApproval = false;
                        this.errorString =
                            await helpers.parseFetchError(response);
                    }
                } else if (this.proposedApprovalState == 'final_approval') {
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposals,
                            this.proposal_id + '/final_approval'
                        ),
                        {
                            body: JSON.stringify(this.approval),
                            method: 'POST',
                        }
                    )
                        .then(async (response) => {
                            const data = await response.json();
                            if (!response.ok) {
                                let error =
                                    (data.constructor.name === 'Array' &&
                                        data) ||
                                    (data && data.message) ||
                                    response.statusText;
                                this.issuingApproval = false;
                                console.error(error);
                                this.errorString = error;
                            }
                            this.issuingApproval = false;
                            Swal.fire({
                                title: `Approval Issued: ${this.proposal.lodgement_number}`,
                                text: 'Issued successfully.',
                                icon: 'success',
                                confirmButtonText: 'OK',
                            });
                            this.$router.push({ path: '/internal' }); //Navigate to dashboard page after Propose issue.
                        })
                        .catch((error) => {
                            console.error(
                                `There was an error issuing approval`,
                                error
                            );
                            this.errorString = constants.ERRORS.NETWORK_ERROR;
                        });
                }
            });
        },
        initSelectDocument: function () {
            let vm = this;
            vm.$refs.proposed_issuance_documents.initSelectDocument();
        },
        /**
         * Initialise the select2 control for selecting the approval type of the application
         */
        initSelectApprovalType: function () {
            let vm = this;

            $(vm.$refs.select_approvaltype)
                .select2({
                    dropdownParent: $('#proposedIssuanceApproval .modal'),
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder: 'Select an Approval Type',
                })
                .on('select2:select', function (e) {
                    var selected = $(e.currentTarget);
                    vm.handleApprovalTypeChangeEvent(Number(selected.val()));
                })
                .on('select2:unselecting', function () {
                    var self = $(this);
                    setTimeout(() => {
                        self.select2('close');
                    }, 0);
                })
                .on('select2:unselect', function (e) {
                    // eslint-disable-next-line no-unused-vars
                    let unselected_id = e.params.data.id;
                });
        },
    },
};
</script>
