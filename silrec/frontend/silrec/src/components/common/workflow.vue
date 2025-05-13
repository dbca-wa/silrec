<template>
    <div class="" v-bind="$attrs">
        <div class="card card-default mb-2">
            <div class="card-header">Workflow</div>
            <div class="card-body">
                <div class="fw-bold">Status</div>
                {{ proposal.processing_status }}
            </div>
            <div v-if="isAssessorOrApprover" class="card-body border-top">
                <div class="col-sm-12">
                    <div class="fw-bold mb-1">Currently Assigned To</div>
                    <template
                        v-if="proposal.processing_status_id == 'with_approver'"
                    >
                        <select
                            ref="assigned_officer"
                            v-model="assigned_approver"
                            :disabled="!canAction"
                            class="form-select"
                            @change="assignTo()"
                        >
                            <option
                                v-for="member in proposal.allowed_assessors"
                                :key="member.id"
                                :value="member.id"
                            >
                                {{ member.first_name }} {{ member.last_name }}
                            </option>
                        </select>
                        <div class="mt-2">
                            <a
                                v-if="
                                    canAssess &&
                                    proposal.assigned_approver !=
                                        proposal.current_assessor.id
                                "
                                role="button"
                                class="float-end"
                                @click.prevent="assignRequestUser()"
                                >Assign to me
                            </a>
                        </div>
                    </template>
                    <template
                        v-if="
                            proposal.processing_status_id ==
                                constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID ||
                            proposal.processing_status_id ==
                                constants.PROPOSAL_STATUS
                                    .WITH_ASSESSOR_CONDITIONS.ID ||
                            proposal.processing_status_id ==
                                constants.PROPOSAL_STATUS.WITH_REFERRAL.ID
                        "
                    >
                        <select
                            ref="assigned_officer"
                            v-model="assigned_officer"
                            :disabled="!canAction"
                            class="form-select"
                            @change="assignTo()"
                        >
                            <option
                                v-for="member in proposal.allowed_assessors"
                                :key="member.id"
                                :value="member.id"
                            >
                                {{ member.first_name }} {{ member.last_name }}
                            </option>
                        </select>
                        <div class="mt-2">
                            <a
                                v-if="
                                    canAssess &&
                                    proposal.assigned_officer !=
                                        proposal.current_assessor.id
                                "
                                role="button"
                                class="float-end"
                                @click.prevent="assignRequestUser()"
                                >Assign to me
                            </a>
                        </div>
                    </template>
                </div>
            </div>
            <div v-if="show_toggle_proposal" class="card-body border-top">
                <div class="col-sm-12">
                    <div class="fw-bold">Proposal Visibility</div>
                    <a
                        v-if="!showingProposal"
                        class="actionBtn"
                        @click.prevent="toggleProposal()"
                        >Show Proposal</a
                    >
                    <a
                        v-else
                        class="actionBtn"
                        @click.prevent="toggleProposal()"
                        >Hide Proposal</a
                    >
                </div>
            </div>
            <div v-if="show_toggle_requirements" class="card-body border-top">
                <div class="col-sm-12">
                    <div class="fw-bold">Conditions Visibility</div>
                    <a
                        v-if="!showingRequirements"
                        class="actionBtn"
                        @click.prevent="toggleRequirements()"
                        >Show Conditions</a
                    >
                    <a
                        v-else
                        class="actionBtn"
                        @click.prevent="toggleRequirements()"
                        >Hide Conditions</a
                    >
                </div>
            </div>

            <div v-if="showInviteReferee" class="card-body border-top">
                <div class="col-sm-12">
                    <div class="fw-bold mb-1">Invite Referee</div>
                    <div class="mb-3">
                        <select
                            ref="department_users"
                            :disabled="!canAction"
                            class="form-select"
                        ></select>
                        <template v-if="!sendingReferral">
                            <template v-if="selected_referral">
                                <label
                                    class="control-label pull-left"
                                    for="Name"
                                    >Comments</label
                                >
                                <textarea
                                    v-model="assessor_referral_text"
                                    class="form-control"
                                    name="name"
                                ></textarea>
                                <div class="text-end">
                                    <a
                                        v-if="canAction"
                                        class="actionBtn"
                                        @click.prevent="sendReferral()"
                                        >Send</a
                                    >
                                </div>
                            </template>
                        </template>
                        <template v-else>
                            <span
                                v-if="canAction"
                                disabled
                                class="actionBtn text-primary pull-right"
                                @click.prevent="sendReferral()"
                            >
                                Sending Referral&nbsp;
                                <i
                                    class="fa fa-circle-o-notch fa-spin fa-fw"
                                ></i>
                            </span>
                        </template>
                    </div>
                </div>
            </div>

            <div
                v-if="
                    isCurrentAssessor &&
                    proposal.external_referral_invites &&
                    proposal.external_referral_invites.length > 0
                "
                class="card-body border-top"
            >
                <div class="fw-bold mb-1">External Referee Invites</div>
                <table class="table table-sm table-hover table-referrals">
                    <thead>
                        <tr>
                            <th scope="col">Referee</th>
                            <th scope="col">Status</th>
                            <th scope="col">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="external_referee_invite in proposal.external_referral_invites"
                            :key="external_referee_invite.id"
                        >
                            <td class="truncate-name">
                                {{ external_referee_invite.full_name }}
                            </td>
                            <td>Pending</td>
                            <td class="text-center">
                                <a
                                    role="button"
                                    data-bs-toggle="popover"
                                    data-bs-trigger="hover focus"
                                    :data-bs-content="
                                        'Send a reminder to ' +
                                        external_referee_invite.full_name
                                    "
                                    data-bs-placement="bottom"
                                    @click.prevent="
                                        remindExternalReferee(
                                            external_referee_invite
                                        )
                                    "
                                    ><i
                                        class="fa fa-bell text-warning"
                                        aria-hidden="true"
                                    ></i>
                                </a>
                                <a
                                    role="button"
                                    data-bs-toggle="popover"
                                    data-bs-trigger="hover focus"
                                    :data-bs-content="
                                        'Recall the external referee invite sent to ' +
                                        external_referee_invite.full_name
                                    "
                                    data-bs-placement="bottom"
                                    @click.prevent="
                                        retractExternalRefereeInvite(
                                            external_referee_invite
                                        )
                                    "
                                    ><i
                                        class="fa fa-times-circle text-danger"
                                        aria-hidden="true"
                                    ></i>
                                </a>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div
                v-if="
                    isCurrentAssessor &&
                    proposal.latest_referrals &&
                    proposal.latest_referrals.length > 0
                "
                class="card-body border-top"
            >
                <div class="col-sm-12">
                    <div class="fw-bold mb-1">
                        Recent Referrals
                        <small class="text-secondary fw-lighter"
                            >(Showing {{ proposal.latest_referrals.length }} of
                            {{ proposal.referrals.length }})</small
                        >
                    </div>
                    <table class="table table-sm table-hover table-referrals">
                        <thead>
                            <tr>
                                <th>Referee</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                v-for="r in proposal.latest_referrals"
                                :key="r.id"
                            >
                                <td class="truncate-name">
                                    {{ r.referral_obj.first_name }}
                                    {{ r.referral_obj.last_name }}
                                </td>
                                <td>
                                    {{ r.processing_status }}
                                </td>
                                <td class="text-center">
                                    <template
                                        v-if="
                                            constants.REFERRAL_STATUS
                                                .PROCESSING_STATUS_WITH_REFERRAL
                                                .TEXT == r.processing_status
                                        "
                                    >
                                        <a
                                            v-if="canAction"
                                            role="button"
                                            data-bs-toggle="popover"
                                            data-bs-trigger="hover focus"
                                            :data-bs-content="
                                                'Send a reminder to ' +
                                                r.referral_obj['fullname']
                                            "
                                            data-bs-placement="bottom"
                                            @click.prevent="
                                                remindReferral.bind(this)(
                                                    referrals_api_endpoint,
                                                    r.id,
                                                    r.referral_obj['fullname']
                                                )
                                            "
                                            ><i
                                                class="fa fa-bell text-warning"
                                                aria-hidden="true"
                                            ></i>
                                        </a>
                                        <a
                                            role="button"
                                            data-bs-toggle="popover"
                                            data-bs-trigger="hover focus"
                                            :data-bs-content="
                                                'Recall the referral request sent to ' +
                                                r.referral_obj['fullname']
                                            "
                                            data-bs-placement="bottom"
                                            @click.prevent="
                                                recallReferral.bind(this)(
                                                    referrals_api_endpoint,
                                                    r.id,
                                                    r.referral_obj['fullname']
                                                )
                                            "
                                            ><i
                                                class="fa fa-times-circle text-danger"
                                                aria-hidden="true"
                                            ></i>
                                        </a>
                                    </template>
                                    <template v-else>
                                        <small v-if="canAction"
                                            ><a
                                                role="button"
                                                data-bs-toggle="popover"
                                                data-bs-trigger="hover focus"
                                                :data-bs-content="
                                                    'Resend this referral request to ' +
                                                    r.referral_obj['fullname']
                                                "
                                                @click.prevent="
                                                    resendReferral.bind(this)(
                                                        referrals_api_endpoint,
                                                        r.id,
                                                        r.referral_obj[
                                                            'fullname'
                                                        ]
                                                    )
                                                "
                                                ><i
                                                    class="fa fa-envelope text-primary"
                                                    aria-hidden="true"
                                                ></i> </a
                                        ></small>
                                    </template>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <MoreReferrals
                        ref="more_referrals"
                        :can-action="canAction"
                        :is-finalised="isFinalised"
                        :referral_url="referralListURL"
                        :api_endpoint="referrals_api_endpoint"
                        @switch-status="switchStatus"
                    />
                </div>
            </div>

            <div v-if="actionsVisible" class="card-body border-top">
                <div class="row">
                    <div v-if="!isFinalised">
                        <div>
                            <strong>Action</strong>
                        </div>
                        <template
                            v-for="configuration in configurations_for_buttons"
                            :key="configuration.key"
                        >
                            <template
                                v-if="
                                    isReferee &&
                                    configuration.key == 'complete_referral'
                                "
                            >
                                <textarea
                                    v-model="referral_text"
                                    class="form-control my-2"
                                    name="name"
                                    rows="5"
                                    placeholder="Enter any final comments for the assessor here before completing the referral"
                                ></textarea>
                            </template>
                            <button
                                v-if="configuration.function_to_show_hide()"
                                class="btn btn-primary w-75 my-1"
                                :disabled="configuration.function_to_disable()"
                                @click.prevent="
                                    configuration.function_when_clicked
                                "
                            >
                                {{ configuration.button_title }}
                            </button>
                        </template>
                    </div>
                </div>
            </div>
        </div>
        <AddExternalReferral
            ref="AddExternalReferral"
            :proposal-id="proposal.id"
            :email="external_referral_email"
            @external-referee-invite-sent="externalRefereeInviteSent"
        />
    </div>
    <div v-if="isAssessorOrApprover" class="card sticky-top">
        <div class="card-header">Navigation Tools</div>
        <div class="card-body">
            <div class="list-group">
                <li
                    class="list-group-item list-group-item-action"
                    role="button"
                    @click.prevent="toggleFormSections"
                >
                    <a href="#" class="text-primary text-decoration-none"
                        >{{ formSectionsOpen ? 'Collapse' : 'Open' }} Form
                        Sections</a
                    >
                </li>
                <li
                    v-if="formSectionsOpen && formSectionLabels.length > 0"
                    class="list-group-item"
                >
                    <ul class="list-group">
                        <li
                            v-for="(form_section, idx) in formSectionLabels"
                            :key="`form_section_${idx}`"
                            class="list-group-item list-group-item-action"
                            role="button"
                            @click="scrollTo(form_section.id)"
                        >
                            <a class="text-decoration-none">{{
                                form_section.label
                            }}</a>
                        </li>
                    </ul>
                </li>
                <li
                    class="list-group-item list-group-item-action"
                    role="button"
                    @click.prevent="toggleCollapse"
                >
                    <a class="text-primary text-decoration-none"
                        >Toggle Assessment Comments</a
                    >
                </li>
                <li
                    class="list-group-item list-group-item-action"
                    role="button"
                    @click.prevent="scrollTop"
                >
                    <a href="#" class="text-primary text-decoration-none"
                        >Scroll to top</a
                    >
                </li>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints, helpers, constants } from '@/utils/hooks';
import MoreReferrals from '@common-utils/more_referrals.vue';
import AddExternalReferral from '@/components/internal/proposals/proposal_add_external_referral.vue';
import {
    remindReferral,
    recallReferral,
    resendReferral,
} from '@/components/common/workflow_functions.js';
import Swal from 'sweetalert2';

export default {
    name: 'WorkflowComponent',
    components: {
        MoreReferrals,
        AddExternalReferral,
    },
    props: {
        proposal: {
            type: Object,
            default: null,
        },
        onCurrentRevision: {
            type: Boolean,
            default: true,
        },
        isFinalised: {
            type: Boolean,
            default: false,
        },
        canAction: {
            type: Boolean,
            default: false,
        },
        canAssess: {
            type: Boolean,
            default: false,
        },
        isReferee: {
            type: Boolean,
            default: false,
        },
        canUserEdit: {
            type: Boolean,
            default: false,
        },
        profile: {
            type: Object,
            required: true,
        },
    },
    emits: [
        'completeEditing',
        'assignRequestUser',
        'assignTo',
        'toggleProposal',
        'toggleRequirements',
        'switchStatus',
        'amendmentRequest',
        'completeReferral',
        'proposedDecline',
        'proposedApproval',
        'issueApproval',
        'declineProposal',
        'updateProposalData',
        'updateAssignedApprover',
        'updateAssignedOfficer',
        'backToAssessor',
        'enterConditions',
    ],
    data: function () {
        let vm = this;

        let APPLICATION_TYPE = constants.APPLICATION_TYPES;
        let PROPOSAL_STATUS = constants.PROPOSAL_STATUS;
        let ROLES = constants.ROLES;

        return {
            constants: constants,
            referrals_api_endpoint: api_endpoints.referrals,
            showingProposal: false,
            showingRequirements: false,

            loading: [],

            department_users: [],
            selected_referral: '',
            assessor_referral_text: '',
            referral_text: '',
            external_referral_email: '',
            sendingReferral: false,
            formSectionsOpen: true,
            formSectionLabels: [],
            configurations_for_buttons: [
                {
                    key: 'enter_conditions',
                    button_title: 'Enter Conditions',
                    function_when_clicked: vm.enterConditions,
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                // When proposal type is 'lease_licence'
                                // When proposal status is 'with_assessor', 'assessor'/'referral' can see this button
                                [PROPOSAL_STATUS.WITH_ASSESSOR.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                    ROLES.REFERRAL.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display) &&
                            vm.isCurrentAssessor &&
                            !vm.proposal.additional_documents_missing.length >
                                0;

                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'complete_referral',
                    button_title: 'Complete Referral',
                    function_when_clicked: vm.completeReferral,
                    function_to_show_hide: () => {
                        return this.isReferee;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'request_amendment',
                    button_title: 'Request Amendment',
                    function_when_clicked: vm.amendmentRequest,
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.REGISTRATION_OF_INTEREST]: {
                                [PROPOSAL_STATUS.WITH_ASSESSOR.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                            },
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.WITH_ASSESSOR.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display) &&
                            vm.isCurrentAssessor &&
                            !vm.proposal.added_internally;
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'back_to_application',
                    button_title: 'Back to Proposal',
                    function_when_clicked: function () {
                        if (
                            vm.proposal.processing_status_id ===
                            constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS
                                .ID
                        ) {
                            vm.switchStatus(
                                constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID
                            );
                        } else {
                            console.error(
                                `Can not switch back from status ${vm.proposal.processing_status}`
                            );
                        }
                    },
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                // If either the assessor or referrer changes the status to `With Assessor/Referral (Conditions)`
                                // both assessor and referrer should be able to return back to the Proposal
                                [PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                    ROLES.REFERRAL.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display);
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'propose_approve',
                    button_title: 'Propose Approve',
                    function_when_clicked: vm.proposedApproval,
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.REGISTRATION_OF_INTEREST]: {
                                [PROPOSAL_STATUS.WITH_ASSESSOR.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                                [PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                            },
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display) &&
                            vm.isCurrentAssessor &&
                            !vm.proposal.additional_documents_missing.length >
                                0;
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'propose_decline',
                    button_title: 'Propose Decline',
                    function_when_clicked: vm.proposedDecline,
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.REGISTRATION_OF_INTEREST]: {
                                [PROPOSAL_STATUS.WITH_ASSESSOR.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                                [PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                            },
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.WITH_ASSESSOR.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                                [PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display) &&
                            vm.isCurrentAssessor &&
                            !vm.proposal.additional_documents_missing.length >
                                0;
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'back_to_assessor',
                    button_title: 'Back to Assessor',
                    function_when_clicked: function () {
                        vm.backToAssessor();
                    },
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.REGISTRATION_OF_INTEREST]: {
                                [PROPOSAL_STATUS.WITH_APPROVER.ID]: [
                                    ROLES.GROUP_NAME_APPROVER.ID,
                                ],
                            },
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.WITH_APPROVER.ID]: [
                                    ROLES.GROUP_NAME_APPROVER.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display);
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'approve',
                    button_title: 'Approve',
                    function_when_clicked: vm.issueApproval,
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.REGISTRATION_OF_INTEREST]: {
                                [PROPOSAL_STATUS.WITH_APPROVER.ID]: [
                                    ROLES.GROUP_NAME_APPROVER.ID,
                                ],
                            },
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.WITH_APPROVER.ID]: [
                                    ROLES.GROUP_NAME_APPROVER.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display) &&
                            vm.proposal.proposed_issuance_approval &&
                            vm.proposal.assigned_approver == vm.profile.id;
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'decline',
                    button_title: 'Decline',
                    function_when_clicked: vm.declineProposal,
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.REGISTRATION_OF_INTEREST]: {
                                [PROPOSAL_STATUS.WITH_APPROVER.ID]: [
                                    ROLES.GROUP_NAME_APPROVER.ID,
                                ],
                            },
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.WITH_APPROVER.ID]: [
                                    ROLES.GROUP_NAME_APPROVER.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display) &&
                            vm.proposal.proposed_decline_status &&
                            vm.proposal.assigned_approver == vm.profile.id;
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'require_das',
                    button_title: 'Require DAS',
                    function_when_clicked: vm.requireDas,
                    function_to_show_hide: () => {
                        // Pushing back DAS integration until a "Phase 2"
                        return false;

                        // eslint-disable-next-line no-unreachable
                        let condition_to_display = {
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.WITH_ASSESSOR.ID]: [
                                    ROLES.GROUP_NAME_ASSESSOR.ID,
                                ],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display) &&
                            vm.isCurrentAssessor;
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
                {
                    key: 'complete_editing',
                    button_title: 'Complete Editing',
                    function_when_clicked: vm.completeEditing,
                    function_to_show_hide: () => {
                        let condition_to_display = {
                            [APPLICATION_TYPE.LEASE_LICENCE]: {
                                [PROPOSAL_STATUS.APPROVED_EDITING_INVOICING.ID]:
                                    [ROLES.FINANCE.ID],
                            },
                        };
                        let show =
                            vm.check_role_conditions(condition_to_display); // Do we have to restrict this to a specific assigned user as above?
                        return show;
                    },
                    function_to_disable: () => {
                        return false;
                    },
                },
            ],
            remindReferral: remindReferral,
            recallReferral: recallReferral,
            resendReferral: resendReferral,
        };
    },
    computed: {
        assigned_approver: {
            get() {
                return this.proposal.assigned_approver;
            },
            set(value) {
                this.$emit('updateAssignedApprover', value);
            },
        },
        assigned_officer: {
            get() {
                return this.proposal.assigned_officer;
            },
            set(value) {
                this.$emit('updateAssignedOfficer', value);
            },
        },
        actionsVisible: function () {
            if (
                !(
                    this.canAssess ||
                    this.isReferee ||
                    this.proposal.can_edit_invoicing_details
                )
            ) {
                return false;
            }
            for (let i = 0; i < this.configurations_for_buttons.length; i++) {
                if (
                    this.configurations_for_buttons[i].function_to_show_hide()
                ) {
                    return true;
                }
            }
            return false;
        },
        latest_referrals: function () {
            return this.proposal.latest_referrals;
        },
        referralListURL: function () {
            return this.proposal != null
                ? helpers.add_endpoint_json(
                      api_endpoints.referrals,
                      'datatable_list'
                  ) +
                      '?proposal=' +
                      this.proposal.id
                : '';
        },
        isCurrentAssessor: function () {
            return this.proposal.assigned_officer == this.profile.id;
        },
        show_toggle_proposal: function () {
            if (
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID ||
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.WITH_APPROVER.ID ||
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.APPROVED_APPLICATION.ID ||
                this.isFinalised
            ) {
                return true;
            } else {
                return false;
            }
        },
        show_toggle_requirements: function () {
            if (
                this.proposal.processing_status_id ==
                    constants.PROPOSAL_STATUS.WITH_APPROVER.ID ||
                this.isFinalised
            ) {
                return true;
            } else {
                return false;
            }
        },
        showInviteReferee: function () {
            return (
                this.isCurrentAssessor &&
                !this.proposal.additional_documents_missing.length > 0 &&
                [
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID,
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID,
                    constants.PROPOSAL_STATUS.WITH_REFERRAL.ID,
                ].includes(this.proposal.processing_status_id)
            );
        },
        isAssessorOrApprover: function () {
            return (
                !this.isFinalised &&
                this.canAssess &&
                [
                    constants.PROPOSAL_STATUS.WITH_APPROVER.ID,
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR.ID,
                    constants.PROPOSAL_STATUS.WITH_ASSESSOR_CONDITIONS.ID,
                    constants.PROPOSAL_STATUS.WITH_REFERRAL.ID,
                ].includes(this.proposal.processing_status_id)
            );
        },
        debug: function () {
            return this.$route.query.debug && this.$route.query.debug == 'true'
                ? true
                : false;
        },
        display_referrals: function () {
            return true;
        },
        display_actions: function () {
            if (this.debug) return true;

            return !this.isFinalised && this.canAction;
        },
    },
    watch: {
        latest_referrals: function () {
            this.$nextTick(() => {
                this.initialisePopovers();
            });
        },
    },
    mounted: function () {
        let vm = this;
        this.$nextTick(() => {
            vm.initialiseRefereeSelect();
            vm.initialiseAssignedOfficerSelect();
            vm.initialisePopovers();
            this.formSectionLabels = this.getFormSectionLabels();
        });
    },
    methods: {
        toggleCollapse: function () {
            $('.toggle_filters_wrapper > .body').toggleClass('show');
        },
        toggleFormSections: function () {
            if (this.formSectionsOpen) {
                $('.section-toggle:not(:first) .chevron-toggle').removeClass(
                    'down-chevron-open'
                );
                $('.section-toggle:not(:first) .chevron-toggle').addClass(
                    'down-chevron-close'
                );
                $('.section-toggle:not(:first) > .card-body').css(
                    'display',
                    'none'
                );
            } else {
                $('.section-toggle:not(:first) .chevron-toggle').removeClass(
                    'down-chevron-close'
                );
                $('.section-toggle:not(:first) .chevron-toggle').addClass(
                    'down-chevron-open'
                );
                $('.section-toggle:not(:first) > .card-body').css(
                    'display',
                    'block'
                );
            }
            this.formSectionsOpen = !this.formSectionsOpen;

            if (
                $('.section-toggle:not(:first) > .card-body').css('display') ==
                'none'
            ) {
                this.scrollTop();
            }
        },
        getFormSectionLabels: function () {
            return $('#pills-details .section-toggle')
                .map(function () {
                    let obj = {
                        id: $(this).attr('id'),
                        label: $(this).find('.label').text(),
                    };
                    return obj;
                })
                .toArray();
        },
        scrollTop: function () {
            $('html, body').animate(
                {
                    scrollTop: $('.section-toggle:first').offset().top,
                },
                0
            );
        },
        scrollTo: function (id) {
            $('html, body').animate(
                {
                    scrollTop: $('#' + id).offset().top,
                },
                0
            );
        },
        formatDate: function (data) {
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss') : '';
        },
        check_role_conditions: function (condition_to_display) {
            if (this.debug) return true;

            let condition = false;
            if (this.proposal.application_type.name in condition_to_display) {
                if (
                    this.proposal.processing_status_id in
                    condition_to_display[this.proposal.application_type.name]
                ) {
                    let roles =
                        condition_to_display[
                            this.proposal.application_type.name
                        ][this.proposal.processing_status_id];
                    const intersection = roles.filter((role) =>
                        this.proposal.accessing_user_roles.includes(role)
                    );
                    if (intersection.length > 0) condition = true;
                }
            }
            return condition;
        },
        get_allowed_ids: function (ids) {
            let displayable_status_ids = ids.map((a_status) => {
                // if (Object.hasOwn(a_status, 'ID'))
                if (Object.hasOwn(a_status, 'ID')) return a_status.ID;
                else if (Object.hasOwn(a_status, 'id')) return a_status.id;
                else if (Object.hasOwn(a_status, 'Id')) return a_status.Id;
                else return a_status;
            });

            return displayable_status_ids;
        },
        absorb_type_difference: function (processing_status_id) {
            let ret_value = '';

            if (Object.hasOwn(processing_status_id, 'ID'))
                ret_value = processing_status_id.ID;
            else if (Object.hasOwn(processing_status_id, 'id'))
                ret_value = processing_status_id.id;
            else if (Object.hasOwn(processing_status_id, 'Id'))
                ret_value = processing_status_id.Id;
            else ret_value = processing_status_id.toLowerCase();

            return ret_value;
        },
        completeEditing: async function () {
            this.$emit('completeEditing');
        },
        requireDas: function () {},
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
        initialiseRefereeSelect: function (reinit = false) {
            let vm = this;
            if (reinit) {
                $(vm.$refs.department_users).data('select2')
                    ? $(vm.$refs.department_users).select2('destroy')
                    : '';
            }
            $(vm.$refs.department_users)
                .select2({
                    minimumInputLength: 2,
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder: 'Search Referee by Email',
                    ajax: {
                        url: api_endpoints.users + 'get_referees/',
                        dataType: 'json',
                        data: function (params) {
                            var query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
                        },
                        processResults: function (data, params) {
                            if (Object.keys(data.results).length == 0) {
                                Swal.fire({
                                    title: 'No Referee Found',
                                    text: 'Would you like to invite a new external referee to the system?',
                                    icon: 'question',
                                    showCancelButton: true,
                                    reverseButtons: true,
                                    confirmButtonText: 'Yes',
                                    cancelButtonText: 'No',
                                    buttonsStyling: false,
                                    customClass: {
                                        confirmButton: 'btn btn-primary',
                                        cancelButton: 'btn btn-secondary me-2',
                                    },
                                }).then(async (result) => {
                                    if (result.isConfirmed) {
                                        vm.external_referral_email =
                                            params.term;
                                        vm.$refs.AddExternalReferral.isModalOpen = true;
                                        $(vm.$refs.department_users).select2(
                                            'close'
                                        );
                                    }
                                });
                            }
                            return data;
                        },
                    },
                })
                .on('select2:select', function (e) {
                    let data = e.params.data.id;
                    vm.selected_referral = data;
                })
                .on('select2:unselect', function (e) {
                    // eslint-disable-next-line no-unused-vars
                    var selected = $(e.currentTarget);
                    vm.selected_referral = null;
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
                    theme: 'bootstrap-5',
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
                .on('select2:unselect', function (e) {
                    // eslint-disable-next-line no-unused-vars
                    var selected = $(e.currentTarget);
                    if (vm.proposal.processing_status == 'With Approver') {
                        vm.proposal.assigned_approver = null;
                    } else {
                        vm.proposal.assigned_officer = null;
                    }
                    vm.assignTo();
                });
        },
        updateAssignedOfficerSelect: function (selected_user) {
            let vm = this;
            $(vm.$refs.assigned_officer).val(selected_user);
            $(vm.$refs.assigned_officer).trigger('change');
        },
        performSendReferral: async function () {
            let vm = this;
            let my_headers = {
                Accept: 'application/json',
                'Content-Type': 'application/json',
            };

            vm.sendingReferral = true;
            await fetch(
                `/api/proposal/${this.proposal.id}/assessor_save.json`,
                {
                    method: 'POST',
                    headers: my_headers,
                    body: JSON.stringify({ proposal: vm.proposal }),
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
                .then(async () => {
                    return fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposals,
                            vm.proposal.id + '/assessor_send_referral'
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
                            if (Array.isArray(json)) {
                                throw new Error(json);
                            } else {
                                throw new Error(json['non_field_errors']);
                            }
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then(async (response) => {
                    vm.switchStatus(response.processing_status_id); // 'with_referral'
                })
                .catch((error) => {
                    swal.fire({
                        title: `${error}`,
                        text: 'Failed to send referral. Please contact your administrator.',
                        icon: 'warning',
                    });
                })
                .finally(() => {
                    vm.sendingReferral = false;
                    vm.selected_referral = '';
                    vm.assessor_referral_text = '';
                    $(vm.$refs.department_users).val(null).trigger('change');
                });
        },
        sendReferral: async function () {
            let vm = this;
            this.checkAssessorData();
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
        assignRequestUser: async function () {
            this.$emit('assignRequestUser');
        },
        assignTo: function () {
            this.$emit('assignTo');
        },
        toggleProposal: function () {
            this.showingProposal = !this.showingProposal;
            this.$emit('toggleProposal', this.showingProposal);
        },
        toggleRequirements: function () {
            this.showingRequirements = !this.showingRequirements;
            this.$emit('toggleRequirements', this.showingRequirements);
        },
        remindExternalReferee: function (external_referee_invite) {
            fetch(
                helpers.add_endpoint_join(
                    api_endpoints.external_referee_invites,
                    `/${external_referee_invite.id}/remind/`
                ),
                {
                    method: 'POST',
                    headers: {
                        Accept: 'application/json',
                        'Content-Type': 'application/json',
                    },
                }
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        Promise.reject(error);
                    }
                    swal.fire({
                        title: 'Reminder Email Sent',
                        text: `A reminder email was successfully sent to ${external_referee_invite.full_name} (${external_referee_invite.email}).`,
                        icon: 'success',
                    });
                })
                .catch((error) => {
                    console.error(`Error sending reminder. ${error}`);
                    swal.fire({
                        title: 'Reminder Email Failed',
                        text: `${constants.API_ERROR}`,
                        icon: 'warning',
                    });
                });
        },
        retractExternalRefereeInvite: function (external_referee_invite) {
            swal.fire({
                title: 'Retract External Referral Invite',
                text: `Are you sure you want to retract the invite sent to ${external_referee_invite.full_name} (${external_referee_invite.email})?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Retract Email',
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    fetch(
                        helpers.add_endpoint_join(
                            api_endpoints.external_referee_invites,
                            `/${external_referee_invite.id}/retract/`
                        ),
                        {
                            method: 'PATCH',
                            headers: {
                                Accept: 'application/json',
                                'Content-Type': 'application/json',
                            },
                        }
                    )
                        .then(async (response) => {
                            const data = await response.json();
                            if (!response.ok) {
                                const error =
                                    (data && data.message) ||
                                    response.statusText;
                                console.error(error);
                                Promise.reject(error);
                            }
                            this.$emit('updateProposalData', data);
                            swal.fire({
                                title: 'External Referral Invite Retracted',
                                text: `The external referee invite that was sent to ${external_referee_invite.full_name} (${external_referee_invite.email}) has been successfully retracted.`,
                                icon: 'success',
                            });
                        })
                        .catch((error) => {
                            console.error(
                                `Error retracting external referee invite. ${error}`
                            );
                            swal.fire({
                                title: 'Retract External Referee Invite Failed',
                                text: `${constants.API_ERROR}`,
                                icon: 'error',
                            });
                        });
                }
            });
        },
        backToAssessor: function () {
            this.$emit('backToAssessor');
        },
        enterConditions: function () {
            this.$emit('enterConditions');
        },
        switchStatus: function (value) {
            this.$emit('switchStatus', value);
        },
        amendmentRequest: function () {
            this.$emit('amendmentRequest');
        },
        completeReferral: function () {
            this.$emit('completeReferral', this.referral_text);
        },
        proposedDecline: function () {
            this.$emit('proposedDecline');
        },
        proposedApproval: function () {
            this.$emit('proposedApproval');
        },
        issueApproval: function () {
            this.$emit('issueApproval');
        },
        declineProposal: function () {
            this.$emit('declineProposal');
        },
        externalRefereeInviteSent: function (proposal) {
            this.$emit('updateProposalData', proposal);
        },
        initialisePopovers: function () {
            var popoverTriggerList = [].slice.call(
                document.querySelectorAll('[data-bs-toggle="popover"]')
            );
            // eslint-disable-next-line no-unused-vars
            var popoverList = popoverTriggerList.map(
                function (popoverTriggerEl) {
                    return new bootstrap.Popover(popoverTriggerEl);
                }
            );
        },
    },
};
</script>

<style scoped>
.actionBtn {
    cursor: pointer;
}

.sticky-top {
    top: 0.5em;
}
</style>
