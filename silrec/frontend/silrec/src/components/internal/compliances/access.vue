<template>
    <div id="internalCompliance" class="container">
        <div v-if="compliance" class="row">
            <h3>Compliance: {{ compliance.reference }}</h3>
            <div class="col-md-3">
                <CommsLogs
                    class="mb-3"
                    :comms_url="comms_url"
                    :logs_url="logs_url"
                    :comms_add_url="comms_add_url"
                    :disable_add_entry="false"
                />

                <div class="card card-default mb-3">
                    <div class="card-header">Workflow</div>
                    <div class="card-body card-collapse">
                        <div class="mb-1 fw-bold">Status</div>
                        <div>{{ compliance.processing_status_display }}</div>
                    </div>
                    <div class="card-body card-collapse border-top">
                        <div class="mb-1 fw-bold">Currently assigned to</div>
                        <select v-if="isLoading" class="form-select">
                            <option value="">Loading...</option>
                        </select>
                        <select
                            v-else
                            v-model="compliance.assigned_to"
                            :disabled="
                                isFinalised || canViewonly || !check_assessor()
                            "
                            class="form-select mb-2"
                            @change="assignTo"
                        >
                            <option value="null">Unassigned</option>
                            <option
                                v-for="member in compliance.allowed_assessors"
                                :key="member.id"
                                :value="member.id"
                            >
                                {{ member.first_name }} {{ member.last_name }}
                            </option>
                        </select>
                        <a
                            v-if="
                                showAssignToMeButton &&
                                !canViewonly &&
                                check_assessor()
                            "
                            class="float-end mb-2"
                            role="button"
                            @click.prevent="assignMyself()"
                            >Assign to me</a
                        >
                    </div>

                    <div
                        v-if="
                            !isFinalised &&
                            compliance.assigned_to &&
                            compliance.assigned_to == profile.id
                        "
                        class="card-body border-top"
                    >
                        <div class="mb-1 fw-bold">Invite Referee</div>
                        <div class="mb-3">
                            <select ref="referees" class="form-select" />
                            <template v-if="!sendingReferral">
                                <template v-if="selected_referral">
                                    <textarea
                                        ref="assessor_referral_text"
                                        v-model="assessor_referral_text"
                                        class="form-control comments_to_referral my-2"
                                        name="name"
                                        rows="5"
                                        placeholder="Enter any comments for the referee before sending"
                                    />
                                    <div class="text-end">
                                        <a
                                            class="btn btn-primary"
                                            role="button"
                                            @click.prevent="sendReferral()"
                                            >Send</a
                                        >
                                    </div>
                                </template>
                            </template>
                            <template v-else>
                                <span
                                    disabled
                                    class="actionBtn text-primary pull-right"
                                    @click.prevent="sendReferral()"
                                >
                                    Sending Referral&nbsp;
                                    <i
                                        class="fa fa-circle-o-notch fa-spin fa-fw"
                                    />
                                </span>
                            </template>
                        </div>
                    </div>

                    <div
                        v-if="showRecentReferrals"
                        class="card-body border-top"
                    >
                        <div class="col-sm-12">
                            <div class="fw-bold mb-1">
                                Recent Referrals
                                <small class="text-secondary fw-lighter"
                                    >(Showing
                                    {{ compliance.latest_referrals.length }} of
                                    {{ compliance.referrals.length }})</small
                                >
                            </div>
                            <table
                                class="table table-sm table-hover table-referrals"
                            >
                                <thead>
                                    <tr>
                                        <th>Referee</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr
                                        v-for="r in compliance.latest_referrals"
                                        :key="r.id"
                                    >
                                        <td class="truncate-name">
                                            {{ r.referee_obj.first_name }}
                                            {{ r.referee_obj.last_name }}
                                        </td>
                                        <td>
                                            {{ r.processing_status_display }}
                                        </td>
                                        <td class="text-center">
                                            <template
                                                v-if="
                                                    constants.REFERRAL_STATUS
                                                        .PROCESSING_STATUS_WITH_REFERRAL
                                                        .ID ==
                                                    r.processing_status
                                                "
                                            >
                                                <a
                                                    role="button"
                                                    data-bs-toggle="popover"
                                                    data-bs-trigger="hover focus"
                                                    :data-bs-content="
                                                        'Send a reminder to ' +
                                                        r.referee_obj[
                                                            'fullname'
                                                        ]
                                                    "
                                                    data-bs-placement="bottom"
                                                    @click.prevent="
                                                        remindReferral.bind(
                                                            this
                                                        )(
                                                            referrals_api_endpoint,
                                                            r.id,
                                                            r.referee_obj[
                                                                'fullname'
                                                            ]
                                                        )
                                                    "
                                                    ><i
                                                        class="fa fa-bell text-warning"
                                                        aria-hidden="true"
                                                    />
                                                </a>
                                                <a
                                                    role="button"
                                                    data-bs-toggle="popover"
                                                    data-bs-trigger="hover focus"
                                                    :data-bs-content="
                                                        'Recall the referral request sent to ' +
                                                        r.referee_obj[
                                                            'fullname'
                                                        ]
                                                    "
                                                    data-bs-placement="bottom"
                                                    @click.prevent="
                                                        recallReferral.bind(
                                                            this
                                                        )(
                                                            referrals_api_endpoint,
                                                            r.id,
                                                            r.referee_obj[
                                                                'fullname'
                                                            ]
                                                        )
                                                    "
                                                    ><i
                                                        class="fa fa-times-circle text-danger"
                                                        aria-hidden="true"
                                                    />
                                                </a>
                                            </template>
                                            <template v-else-if="!isFinalised">
                                                <small
                                                    ><a
                                                        role="button"
                                                        data-bs-toggle="popover"
                                                        data-bs-trigger="hover focus"
                                                        :data-bs-content="
                                                            'Resend this referral request to ' +
                                                            r.referee_obj[
                                                                'fullname'
                                                            ]
                                                        "
                                                        @click.prevent="
                                                            resendReferral.bind(
                                                                this
                                                            )(
                                                                referrals_api_endpoint,
                                                                r.id,
                                                                r.referee_obj[
                                                                    'fullname'
                                                                ]
                                                            )
                                                        "
                                                        ><i
                                                            class="fa fa-envelope text-primary"
                                                            aria-hidden="true"
                                                        /> </a
                                                ></small>
                                            </template>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                            <MoreReferrals
                                v-if="!isFinalised"
                                ref="more_referrals"
                                :can-action="true"
                                :referral_url="referralListURL"
                                :api_endpoint="referrals_api_endpoint"
                                @switch-status="switchStatus"
                            />
                        </div>
                    </div>
                    <div v-if="canViewActions" class="card-body border-top">
                        <div class="mb-1 fw-bold">Actions</div>
                        <div class="action-buttons">
                            <button
                                v-if="canViewAssessorActions"
                                class="btn btn-primary mb-2"
                                @click.prevent="amendmentRequest()"
                            >
                                Request Amendment
                            </button>
                            <button
                                v-if="canViewAssessorActions"
                                class="btn btn-primary"
                                @click.prevent="acceptCompliance()"
                            >
                                {{ approveButtonText }}
                            </button>
                            <template v-if="compliance.is_referee">
                                <textarea
                                    ref="referral_text"
                                    v-model="referral_text"
                                    class="form-control comments_to_referral my-2"
                                    name="name"
                                    rows="5"
                                    placeholder="Enter any final comments for the assessor before completing the referral"
                                />
                                <button
                                    class="btn btn-primary"
                                    @click.prevent="completeReferral()"
                                >
                                    Complete Referral
                                </button>
                            </template>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-9">
                <div class="row">
                    <div class="col">
                        <ul id="pills-tab" class="nav nav-pills" role="tablist">
                            <li class="nav-item">
                                <a
                                    id="pills-compliance-tab"
                                    class="nav-link active"
                                    data-bs-toggle="pill"
                                    href="#pills-compliance"
                                    role="tab"
                                    aria-controls="pills-compliance"
                                    aria-selected="true"
                                    @click="tabClicked('compliance')"
                                    >Compliance</a
                                >
                            </li>
                            <li v-if="showRelatedItemsTab" class="nav-item">
                                <a
                                    id="pills-related-items-tab"
                                    class="nav-link"
                                    data-bs-toggle="pill"
                                    href="#pills-related-items"
                                    role="tab"
                                    aria-controls="pills-related-items"
                                    aria-selected="true"
                                    @click="tabClicked('related-items')"
                                    >Related Items</a
                                >
                            </li>
                        </ul>

                        <div id="pills-tabContent" class="tab-content">
                            <div
                                id="pills-compliance"
                                class="tab-pane active"
                                role="tabpanel"
                                aria-labelledby="pills-compliance-tab"
                            >
                                <FormSection
                                    :form-collapse="false"
                                    :label="
                                        'Compliance ' + compliance.reference
                                    "
                                    index="compliance_with_requirements"
                                >
                                    <CollapsibleFilters
                                        v-if="compliance.assessment"
                                        ref="collapsible_filters"
                                        :collapsed="collapseAssessmentComments"
                                        component_title="Assessment Comments"
                                        class="mb-3"
                                        @created="collapsible_component_mounted"
                                    >
                                        <div class="container px-3">
                                            <div class="row mb-3 mt-3">
                                                <div class="col">
                                                    <div class="form-floating">
                                                        <textarea
                                                            id="assessor_comment"
                                                            v-model="
                                                                compliance
                                                                    .assessment
                                                                    .assessor_comment
                                                            "
                                                            class="form-control"
                                                            placeholder=""
                                                            :disabled="
                                                                !canEditAssessorComments
                                                            "
                                                            :autofocus="
                                                                canEditAssessorComments
                                                            "
                                                        />
                                                        <label
                                                            for="assessor_comment"
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
                                                            id="deficiency_comment"
                                                            v-model="
                                                                compliance
                                                                    .assessment
                                                                    .deficiency_comment
                                                            "
                                                            class="form-control"
                                                            placeholder=""
                                                            :disabled="
                                                                !canEditAssessorComments
                                                            "
                                                        />
                                                        <label
                                                            for="deficiency_comment"
                                                            >Deficiency
                                                            Comments</label
                                                        >
                                                    </div>
                                                </div>
                                            </div>
                                            <template
                                                v-for="referral in compliance.referrals"
                                            >
                                                <div
                                                    v-if="
                                                        referral.processing_status !=
                                                        constants
                                                            .REFERRAL_STATUS
                                                            .PROCESSING_STATUS_RECALLED
                                                            .ID
                                                    "
                                                    :key="referral.id"
                                                    class="row mb-3 mt-3"
                                                >
                                                    <div class="col">
                                                        <div
                                                            class="form-floating"
                                                        >
                                                            <textarea
                                                                :id="
                                                                    'comment_map_' +
                                                                    referral.id
                                                                "
                                                                v-model="
                                                                    referral.comment
                                                                "
                                                                class="form-control referral-comment"
                                                                :disabled="
                                                                    referral.referral !==
                                                                        profile.id ||
                                                                    referral.processing_status !=
                                                                        constants
                                                                            .REFERRAL_STATUS
                                                                            .PROCESSING_STATUS_WITH_REFERRAL
                                                                            .ID
                                                                "
                                                                :autofocus="
                                                                    referral.referral ==
                                                                    profile.id
                                                                "
                                                            />
                                                            <label
                                                                :for="
                                                                    'comment_map_' +
                                                                    referral.id
                                                                "
                                                                >Referral
                                                                Comment by
                                                                <span
                                                                    class="fw-bold"
                                                                    >{{
                                                                        referral
                                                                            .referee_obj
                                                                            .fullname
                                                                    }}</span
                                                                ></label
                                                            >
                                                        </div>
                                                    </div>
                                                </div>
                                            </template>
                                        </div>
                                    </CollapsibleFilters>
                                    <div
                                        v-if="compliance.approval"
                                        class="row mb-3"
                                    >
                                        <label
                                            for=""
                                            class="col-sm-3 col-form-label"
                                            >Approval</label
                                        >
                                        <div class="col-sm-9">
                                            <router-link
                                                class="form-control-text"
                                                :to="{
                                                    name: 'internal-approval-detail',
                                                    params: {
                                                        approval_id:
                                                            compliance.approval,
                                                    },
                                                }"
                                            >
                                                {{
                                                    compliance.approval_lodgement_number
                                                }}
                                            </router-link>
                                        </div>
                                    </div>
                                    <div
                                        v-if="compliance.holder"
                                        class="row mb-3"
                                    >
                                        <label
                                            for="holder"
                                            class="col-sm-3 col-form-label"
                                            >Holder</label
                                        >
                                        <div class="col-sm-9">
                                            <input
                                                id="holder"
                                                type="text"
                                                class="form-control-plaintext"
                                                name="holder"
                                                readonly
                                                :value="compliance.holder"
                                            />
                                        </div>
                                    </div>
                                    <div
                                        v-if="compliance.due_date"
                                        class="row mb-3"
                                    >
                                        <label
                                            for="holder"
                                            class="col-sm-3 col-form-label"
                                            >Due Date</label
                                        >
                                        <div class="col-sm-9">
                                            <div class="form-control-text">
                                                {{ dueDateFormatted }}
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <label
                                            for="requirement"
                                            class="col-sm-3 col-form-label"
                                            >Requirement</label
                                        >
                                        <div class="col-sm-9">
                                            <input
                                                id="requirement"
                                                type="text"
                                                name="requirement"
                                                readonly
                                                :value="compliance.requirement"
                                                class="form-control"
                                            />
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <label
                                            for="text"
                                            class="col-sm-3 col-form-label"
                                            >Details</label
                                        >
                                        <div class="col-sm-9">
                                            <textarea
                                                id="details"
                                                v-model="compliance.text"
                                                disabled
                                                class="form-control"
                                                name="text"
                                            />
                                        </div>
                                    </div>
                                    <div
                                        v-if="
                                            compliance.gross_turnover_required
                                        "
                                        class="row mb-3"
                                    >
                                        <label
                                            for="gross_turnover"
                                            class="col-sm-3 col-form-label"
                                            >Gross Turnover</label
                                        >
                                        <div class="col-sm-4">
                                            <div class="input-group">
                                                <span class="input-group-text"
                                                    >$</span
                                                >
                                                <input
                                                    id="details"
                                                    v-model="
                                                        compliance.gross_turnover
                                                    "
                                                    type="number"
                                                    disabled
                                                    class="form-control"
                                                    name="gross_turnover"
                                                />
                                                <span class="input-group-text"
                                                    >AUD</span
                                                >
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <label
                                            for=""
                                            class="col-sm-3 col-form-label"
                                            >Attachments</label
                                        >
                                        <div class="col-sm-9">
                                            <template
                                                v-if="
                                                    compliance.documents &&
                                                    compliance.documents.length
                                                "
                                            >
                                                <ul class="list-group">
                                                    <li
                                                        v-for="d in compliance.documents"
                                                        :key="d.id"
                                                        class="list-group-item"
                                                    >
                                                        <i
                                                            class="fa-solid fa-file me-2"
                                                        />
                                                        <a
                                                            :href="d.secure_url"
                                                            target="_blank"
                                                            class="col-form-label"
                                                            >{{ d.name }}</a
                                                        >
                                                    </li>
                                                </ul>
                                            </template>
                                            <template v-else>
                                                <div class="row">
                                                    <div class="col-form-label">
                                                        No attachments
                                                    </div>
                                                </div>
                                            </template>
                                        </div>
                                    </div>
                                </FormSection>
                            </div>
                            <div
                                id="pills-related-items"
                                class="tab-pane"
                                role="tabpanel"
                                aria-labelledby="pills-related-items-tab"
                            >
                                <FormSection
                                    v-if="loadRelatedItems"
                                    :form-collapse="false"
                                    label="Related Items"
                                    index="related-items"
                                >
                                    <ApprovalsTable
                                        ref="approvals_table"
                                        :target-compliance-id="compliance.id"
                                        level="internal"
                                    />
                                </FormSection>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="navbar fixed-bottom bg-navbar me-1">
                <div
                    v-if="compliance && !compliance.readonly"
                    class="container"
                >
                    <div class="col-md-12 text-end">
                        <BootstrapButtonSpinner
                            v-if="saveExitCompliance"
                            class="btn btn-primary me-1"
                            :is-loading="true"
                            :small="true"
                            :center-of-screen="false"
                        />
                        <button
                            v-else
                            class="btn btn-primary me-1"
                            @click.prevent="saveAndExit"
                        >
                            Save and Exit
                        </button>

                        <BootstrapButtonSpinner
                            v-if="savingCompliance"
                            class="btn btn-primary me-1"
                            :is-loading="true"
                            :small="true"
                            :center-of-screen="false"
                        />
                        <button
                            v-else
                            class="btn btn-primary me-1"
                            @click.prevent="save"
                        >
                            Save and Continue
                        </button>
                    </div>
                </div>
                <div v-else class="container">
                    <div class="col-md-12 text-end">
                        <router-link
                            class="btn btn-primary float-end"
                            :to="{ name: 'external-dashboard' }"
                        >
                            Back to Dashboard
                        </router-link>
                    </div>
                </div>
            </div>
            <ComplianceAmendmentRequest
                v-if="compliance.id"
                ref="amendment_request"
                :compliance_id="compliance.id"
                :compliance_lodgement_number="compliance.lodgement_number"
            />
        </div>
        <BootstrapSpinner v-else :loading="true" class="text-primary" />
    </div>
</template>
<script>
import CommsLogs from '@common-utils/comms_logs.vue';
import ComplianceAmendmentRequest from './compliance_amendment_request.vue';
import MoreReferrals from '@common-utils/more_referrals.vue';
import FormSection from '@/components/forms/section_toggle.vue';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import ApprovalsTable from '@/components/common/table_approvals.vue';
import {
    remindReferral,
    recallReferral,
    resendReferral,
} from '@/components/common/workflow_functions.js';

import { api_endpoints, constants, helpers } from '@/utils/hooks';
import Swal from 'sweetalert2';
export default {
    name: 'ComplianceAccess',
    components: {
        ApprovalsTable,
        CommsLogs,
        ComplianceAmendmentRequest,
        FormSection,
        CollapsibleFilters,
        MoreReferrals,
    },
    data() {
        let vm = this;
        return {
            constants: constants,
            referrals_api_endpoint: api_endpoints.compliance_referrals,
            loading: [],
            loadRelatedItems: false,
            profile: {},
            compliance: null,
            DATE_FORMAT: 'DD/MM/YYYY',
            members: [],
            sendingReferral: false,
            selected_referral: null,
            assessor_referral_text: '',
            referral_text: '',
            savingCompliance: false,
            saveExitCompliance: false,
            // Filters
            logs_url: helpers.add_endpoint_json(
                api_endpoints.compliances,
                vm.$route.params.compliance_id + '/action_log'
            ),
            comms_url: helpers.add_endpoint_json(
                api_endpoints.compliances,
                vm.$route.params.compliance_id + '/comms_log'
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.compliances,
                vm.$route.params.compliance_id + '/add_comms_log'
            ),
            remindReferral: remindReferral,
            recallReferral: recallReferral,
            resendReferral: resendReferral,
        };
    },
    computed: {
        isLoading: function () {
            return this.loading.length > 0;
        },
        referralListURL: function () {
            return this.compliance
                ? api_endpoints.compliance_referrals +
                      'datatable_list/?compliance_id=' +
                      this.compliance.id
                : '';
        },
        showRelatedItemsTab: function () {
            if (this.profile) {
                if (this.profile.is_assessor) {
                    return true;
                }
            }
            return false;
        },
        canViewonly: function () {
            return (
                this.compliance.processing_status == 'Due' ||
                this.compliance.processing_status == 'Future' ||
                this.compliance.processing_status == 'Approved'
            );
        },
        showAssignToMeButton: function () {
            return this.compliance.assigned_to != this.profile.id;
        },
        dueDateFormatted: function () {
            return moment(this.compliance.due_date).format(this.DATE_FORMAT);
        },
        collapseAssessmentComments: function () {
            return ![
                constants.COMPLIANCE_PROCESSING_STATUS.WITH_ASSESSOR.ID,
                constants.COMPLIANCE_PROCESSING_STATUS.WITH_REFERRAL.ID,
            ].includes(this.compliance.processing_status);
        },
        showRecentReferrals: function () {
            return (
                this.compliance &&
                this.compliance.assigned_to &&
                this.compliance.latest_referrals &&
                this.compliance.latest_referrals.length > 0 &&
                this.compliance.assigned_to == this.profile.id
            );
        },
        canEditAssessorComments: function () {
            return (
                constants.COMPLIANCE_PROCESSING_STATUS.WITH_ASSESSOR.ID ==
                    this.compliance.processing_status &&
                this.profile.is_assessor &&
                this.profile.id == this.compliance.assigned_to
            );
        },
        isFinalised: function () {
            return (
                this.compliance &&
                [
                    constants.COMPLIANCE_PROCESSING_STATUS.DUE.ID,
                    constants.COMPLIANCE_PROCESSING_STATUS.APPROVED.ID,
                    constants.COMPLIANCE_PROCESSING_STATUS.DISCARDED.ID,
                ].includes(this.compliance.processing_status)
            );
        },
        approveButtonText: function () {
            return this.compliance.gross_turnover_required
                ? 'Approve and Edit Invoicing Details'
                : 'Approve';
        },
        canViewActions: function () {
            return this.compliance.is_referee || this.canViewAssessorActions;
        },
        canViewAssessorActions: function () {
            return (
                this.profile.is_assessor &&
                constants.COMPLIANCE_PROCESSING_STATUS.WITH_ASSESSOR.ID ==
                    this.compliance.processing_status &&
                this.profile.id == this.compliance.assigned_to
            );
        },
    },
    created: function () {
        this.fetchProfile();
        if (!this.compliance) {
            this.fetchCompliance(this.$route.params.compliance_id);
        }
    },
    methods: {
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(
                this.filterApplied
            );
        },
        commaToNewline(s) {
            return s.replace(/[,;]/g, '\n');
        },
        save: async function () {
            if (
                this.profile.is_assessor &&
                this.compliance.assigned_to == this.profile.id
            ) {
                this.assessorSave();
            }
            if (this.profile.is_compliance_referee) {
                this.refereeSave();
            }
        },
        assessorSave: async function () {
            let vm = this;
            vm.savingCompliance = true;
            fetch(
                `${api_endpoints.compliance_assessments}${vm.compliance.assessment.id}/`,
                {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        assessor_comment:
                            vm.compliance.assessment.assessor_comment,
                        deficiency_comment:
                            vm.compliance.assessment.deficiency_comment,
                    }),
                }
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                    }
                    swal.fire({
                        title: 'Success',
                        text: 'Assessment Comments Saved',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false,
                    });
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                })
                .finally(() => {
                    vm.savingCompliance = false;
                });
        },
        refereeSave: function () {
            let vm = this;
            vm.savingCompliance = true;
            const referral = vm.compliance.referrals.filter((obj) => {
                return obj['referral'] == vm.profile.id;
            })[0];

            fetch(`${api_endpoints.compliance_referrals}${referral.id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    comment: referral.comment,
                }),
            })
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                    }
                    swal.fire({
                        title: 'Success',
                        text: 'Referral Comments Saved',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false,
                    });
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                })
                .finally(() => {
                    vm.savingCompliance = false;
                });
        },
        saveAndExit: async function () {
            let vm = this;
            vm.saveExitCompliance = true;
            await this.save();
            vm.$router.push({ name: 'internal-compliances-dash' });
        },
        completeReferral: async function () {
            let vm = this;
            const referral = vm.compliance.referrals.filter((obj) => {
                return obj['referral'] == vm.profile.id;
            })[0];
            fetch(
                `${api_endpoints.compliance_referrals}${referral.id}/complete/`,
                {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        comment: referral.comment,
                        referral_text: vm.referral_text,
                    }),
                }
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error = data || response.statusText;
                        console.error(error);
                        swal.fire({
                            title: 'Error',
                            html: helpers.formatErrorV2(error),
                            icon: 'error',
                        });
                        return;
                    }
                    swal.fire({
                        title: 'Success',
                        text: 'Referral Completed, the assigned assessor will be notified',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false,
                    });
                    vm.$router.push({ name: 'internal-compliances-dash' });
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
        },
        tabClicked: function (param) {
            if (param == 'related-items') {
                this.loadRelatedItems = true;
                this.$nextTick(() => {
                    this.$refs.approvals_table.adjust_table_width();
                });
            }
        },
        assignMyself: async function () {
            let vm = this;
            this.compliance = Object.assign(
                {},
                await helpers.fetchWrapper(
                    helpers.add_endpoint_json(
                        api_endpoints.compliances,
                        vm.compliance.id + '/assign_request_user'
                    )
                )
            );
            Swal.fire({
                title: 'Success',
                text: `Compliance ${this.compliance.reference} has been assigned to you`,
                icon: 'success',
                timer: 2000,
                showConfirmButton: false,
            });
            vm.$nextTick(() => {
                vm.initialiseRefereeSelect();
            });
        },
        assignTo: async function () {
            let vm = this;
            if (vm.compliance.assigned_to != 'null') {
                const url = helpers.add_endpoint_json(
                    api_endpoints.compliances,
                    vm.compliance.id + '/assign_to'
                );
                const data = { user_id: vm.compliance.assigned_to };
                this.compliance = Object.assign(
                    {},
                    await helpers.fetchWrapper(url, 'POST', data)
                );
                let assessor_assigned = this.compliance.allowed_assessors.find(
                    function (assessor) {
                        return assessor.id === vm.compliance.assigned_to;
                    }
                );
                Swal.fire({
                    title: 'Success',
                    text: `Compliance ${this.compliance.reference} has been assigned to ${assessor_assigned.fullname}`,
                    icon: 'success',
                    customClass: 'swal-wide',
                    timer: 2000,
                    showConfirmButton: false,
                });
                if (vm.profile.id == vm.compliance.assigned_to) {
                    vm.$nextTick(() => {
                        vm.initialiseRefereeSelect();
                    });
                }
            } else {
                const url = await helpers.add_endpoint_json(
                    api_endpoints.compliances,
                    vm.compliance.id + '/unassign'
                );
                this.compliance = Object.assign(
                    {},
                    await helpers.fetchWrapper(url)
                );
            }
        },
        sendReferral: async function () {
            let vm = this;
            swal.fire({
                title: 'Send Referral',
                text: 'Are you sure you want to send to referral?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Send Referral',
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    // When Yes
                    await vm.performSendReferral();
                }
            });
        },
        performSendReferral: async function () {
            let vm = this;
            let my_headers = {
                Accept: 'application/json',
                'Content-Type': 'application/json',
            };
            vm.sendingReferral = true;
            await fetch(`/api/compliances/${this.compliance.id}/`, {
                method: 'PUT',
                headers: my_headers,
                body: JSON.stringify(vm.compliance),
            })
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.json().then((json) => {
                            throw new Error(json);
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then(async () => {
                    return fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.compliances,
                            vm.compliance.id + '/assessor_send_referral'
                        ),
                        {
                            method: 'POST',
                            headers: my_headers,
                            body: JSON.stringify({
                                email: vm.selected_referral,
                                text: vm.assessor_referral_text,
                            }),
                        }
                    );
                })
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.json().then((json) => {
                            throw new Error(JSON.stringify(json));
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then(async (response) => {
                    vm.compliance = Object.assign({}, response); // 'with_referral'
                    vm.$nextTick(() => {
                        vm.initialisePopovers();
                    });
                })
                .catch((error) => {
                    let errorText = '';
                    try {
                        error = JSON.parse(error.message);
                        errorText = helpers.formatErrorV2(error);
                    } catch {
                        errorText = error.message;
                    }
                    swal.fire({
                        title: 'Failed to send referral.',
                        html: `${errorText}`,
                        icon: 'warning',
                        customClass: 'swal-wide',
                    });
                })
                .finally(() => {
                    vm.sendingReferral = false;
                    vm.selected_referral = '';
                    vm.assessor_referral_text = '';
                    $(vm.$refs.referees).val(null).trigger('change');
                });
        },
        initialiseRefereeSelect: function (reinit = false) {
            let vm = this;
            if (reinit) {
                $(vm.$refs.referees).data('select2')
                    ? $(vm.$refs.referees).select2('destroy')
                    : '';
            }
            $(vm.$refs.referees)
                .select2({
                    minimumInputLength: 2,
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder: 'Search Referee by Email',
                    ajax: {
                        url: api_endpoints.users + 'get_department_users/',
                        dataType: 'json',
                        data: function (params) {
                            var query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
                        },
                    },
                })
                .on('select2:select', function (e) {
                    let data = e.params.data.id;
                    vm.selected_referral = data;
                    vm.$nextTick(() => {
                        vm.$refs.assessor_referral_text.focus();
                    });
                })
                .on('select2:unselect', function () {
                    vm.selected_referral = null;
                });
        },
        acceptCompliance: async function () {
            let vm = this;
            swal.fire({
                title: `Approve Compliance ${vm.compliance.lodgement_number}`,
                text: 'Are you sure you want to approve this compliance?',
                icon: 'question',
                showCancelButton: true,
                reverseButtons: true,
                confirmButtonText: 'Accept',
                confirmButtonColor: '#226fbb',
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    await helpers
                        .fetchWrapper(
                            helpers.add_endpoint_json(
                                api_endpoints.compliances,
                                vm.compliance.id + '/accept'
                            )
                        )
                        .then(function (response) {
                            vm.compliance = Object.assign({}, response);
                            Swal.fire({
                                title: 'Success',
                                text: `Compliance ${vm.compliance.reference} has been approved.`,
                                icon: 'success',
                                timer: 2000,
                                showConfirmButton: false,
                            });
                            if (vm.compliance.gross_turnover_required) {
                                let requestOptions = {
                                    method: 'PATCH',
                                };
                                fetch(
                                    helpers.add_endpoint_join(
                                        api_endpoints.approvals,
                                        vm.compliance.approval +
                                            '/review_invoice_details/'
                                    ),
                                    requestOptions
                                ).then(
                                    async (response) => {
                                        const data = await response.json();
                                        if (!response.ok) {
                                            const error =
                                                (data && data.message) ||
                                                response.statusText;
                                            console.error(error);
                                            Promise.reject(error);
                                        }
                                        vm.$router.push({
                                            name: 'internal-approval-detail',
                                            hash: '#edit-invoicing',
                                            params: {
                                                approval_id:
                                                    vm.compliance.approval,
                                            },
                                        });
                                    },
                                    (error) => {
                                        console.error(error);
                                    }
                                );
                            } else {
                                vm.$router.push({
                                    name: 'internal-compliances-dash',
                                });
                            }
                        });
                }
            });
        },
        amendmentRequest: function () {
            this.$refs.amendment_request.amendment.compliance =
                this.compliance.id;
            this.$refs.amendment_request.isModalOpen = true;
        },
        fetchProfile: async function () {
            this.profile = Object.assign(
                {},
                await helpers.fetchWrapper(api_endpoints.profile)
            );
        },
        check_assessor: function () {
            let vm = this;
            var assessor = vm.members.filter(function (elem) {
                return elem.id == vm.profile.id;
            });
            if (assessor.length > 0) return true;
            else return false;
        },
        switchStatus: function (new_processing_status) {
            const requestOptions = {
                method: 'POST',
                body: JSON.stringify({ status: new_processing_status }),
            };
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.compliances,
                    this.compliance.id + '/switch_status'
                ),
                requestOptions
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
                    this.compliance = Object.assign({}, data);
                    this.$nextTick(() => {
                        this.initialiseRefereeSelect();
                    });
                })
                .catch((error) => {
                    swal.fire({
                        title: 'Compliance Error',
                        text: error,
                        icon: 'error',
                    });
                });
        },
        fetchCompliance: function (compliance_id) {
            let vm = this;
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.compliances,
                    compliance_id + '/internal_compliance'
                )
            )
                .then(async (response) => {
                    if (!response.ok) {
                        return await response.text().then((text) => {
                            swal.fire({
                                title: 'Compliance Error',
                                text: text,
                                icon: 'error',
                            });
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then(async (data) => {
                    vm.compliance = Object.assign({}, data);
                    vm.members = vm.compliance.allowed_assessors;
                    this.$nextTick(() => {
                        $('textarea').each(function () {
                            if ($(this)[0].scrollHeight > 70) {
                                $(this).height($(this)[0].scrollHeight - 30);
                            }
                        });
                        this.initialiseRefereeSelect();
                        this.initialisePopovers();
                    });
                })
                .catch(() => {
                    swal.fire({
                        title: 'Compliance Error',
                        text: constants.ERRORS.NETWORK_ERROR,
                        icon: 'error',
                    });
                });
        },
        initialisePopovers: function () {
            var popoverTriggerList = [].slice.call(
                document.querySelectorAll('[data-bs-toggle="popover"]')
            );
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        },
    },
    // mounted: function () {
    //     if(constants.COMPLIANCE_PROCESSING_STATUS.WITH_REFERRAL this.compliance){

    //     }
    // },
};
</script>
<style scoped>
.action-buttons {
    box-sizing: border-box;
    width: 100%;
}

.action-buttons button {
    width: 190px;
}

.form-control-text {
    display: block;
    width: fit-content;
    margin: 0px;
    padding: 0.375em 0 0.375em 0;
    line-height: 1.5;
    height: 100%;
}
</style>
