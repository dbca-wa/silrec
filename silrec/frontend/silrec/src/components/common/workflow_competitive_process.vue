<template>
    <div class="card card-default">
        <div class="card-header">Workflow</div>
        <template v-if="competitiveProcess">
            <div class="card-body">
                <div class="fw-bold">Status</div>
                {{ competitiveProcess.status }}
            </div>
            <div v-if="showCurrentlyAssignedTo" class="card-body border-top">
                <div class="fw-bold">Currently Assigned To</div>
                <div class="form-group">
                    <select
                        ref="assigned_officer"
                        v-model="assigned_officer_id"
                        :disabled="
                            elementDisabled ||
                            !competitiveProcess.accessing_user_is_competitive_process_editor
                        "
                        class="form-control"
                        @change="assignTo()"
                    >
                        <option
                            v-for="member in competitiveProcess.allowed_editors"
                            :key="member.id"
                            :value="member.id"
                        >
                            {{ member.first_name }} {{ member.last_name }}
                        </option>
                    </select>
                    <div
                        v-if="
                            competitiveProcess.accessing_user_is_competitive_process_editor
                        "
                        class="text-end"
                    >
                        <a
                            v-if="showAssignToMe"
                            class="actionBtn pull-right"
                            style="cursor: pointer"
                            @click.prevent="assignRequestUser()"
                            >Assign to me</a
                        >
                    </div>
                </div>
            </div>
            <div v-if="display_actions" class="card-body border-top">
                <div class="fw-bold">Action</div>
                <template
                    v-for="configuration in configurations_for_buttons"
                    :key="configuration.key"
                >
                    <button
                        v-if="configuration.function_to_show_hide()"
                        class="btn btn-primary w-75 my-1"
                        :disabled="configuration.function_to_disable()"
                        @click.prevent="configuration.function_when_clicked"
                    >
                        {{ configuration.button_title }}
                    </button>
                </template>
            </div>
        </template>
    </div>
</template>

<script>
import { helpers, constants } from '@/utils/hooks';

export default {
    name: 'WorkflowCompetitiveProcess',
    components: {},
    filters: {
        formatDate: function (data) {
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss') : '';
        },
    },
    props: {
        competitiveProcess: {
            type: Object,
            default: null,
        },
        processing: {
            type: Boolean,
            default: false,
        },
        discarded: {
            type: Boolean,
            default: false,
        },
        declined: {
            type: Boolean,
            default: false,
        },
        finalised: {
            type: Boolean,
            default: false,
        },
        canAction: {
            type: Boolean,
            default: false,
        },
        canUnlock: {
            type: Boolean,
            default: false,
        },
        canAssess: {
            type: Boolean,
            default: false,
        },
    },
    emits: [
        'assignRequestUser',
        'assignTo',
        'issueComplete',
        'issueDiscard',
        'issueUnlock',
    ],
    data: function () {
        let vm = this;

        return {
            constants: constants,
            showingProposal: false,
            showingRequirements: false,

            loading: [],

            department_users: [],
            configurations_for_buttons: [
                {
                    key: 'complete',
                    button_title: 'Complete',
                    function_when_clicked: vm.issueComplete,
                    function_to_show_hide: () => {
                        return vm.user_is_eligible(
                            this.action_roles('complete')
                        );
                    },
                    function_to_disable: () => {
                        return this.elementDisabled;
                    },
                },
                {
                    key: 'discard',
                    button_title: 'Discard',
                    function_when_clicked: vm.issueDiscard,
                    function_to_show_hide: () => {
                        return vm.user_is_eligible(
                            this.action_roles('discard')
                        );
                    },
                    function_to_disable: () => {
                        return this.elementDisabled;
                    },
                },
                {
                    key: 'unlock',
                    button_title: 'Unlock',
                    function_when_clicked: vm.issueUnlock,
                    function_to_show_hide: () => {
                        return vm.user_is_eligible(this.action_roles('unlock'));
                    },
                    function_to_disable: () => {
                        // Disable Unlock button only on processing or discarded,
                        // but not on completed|declined
                        return this.processing || this.discarded;
                    },
                },
            ],
        };
    },
    computed: {
        showCurrentlyAssignedTo: function () {
            return (
                !this.finalised &&
                [
                    constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS.ID,
                    constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS_UNLOCKED
                        .ID,
                ].includes(this.competitiveProcess.status_id)
            );
        },
        debug: function () {
            return this.$route.query.debug && this.$route.query.debug == 'true'
                ? true
                : false;
        },
        display_actions: function () {
            if (this.debug) return true;

            return this.canAction || this.canUnlock;
        },
        assigned_officer_id: function () {
            if (this.competitiveProcess.assigned_officer) {
                return this.competitiveProcess.assigned_officer.id;
            } else {
                return null;
            }
        },
        currentUserIsAssignedUser: function () {
            return (
                this.competitiveProcess.assigned_officer &&
                this.competitiveProcess.assigned_officer.id ==
                    this.competitiveProcess.accessing_user.id
            );
        },
        showAssignToMe: function () {
            return (
                this.canAssess &&
                !this.elementDisabled &&
                !this.currentUserIsAssignedUser
            );
        },
        elementDisabled: function () {
            /** Returns whether an element is disabled
             * True while processing (saving), when discarded, when finalized, or when declined
             * */

            return (
                this.processing ||
                this.discarded ||
                this.finalised ||
                this.declined
            );
        },
    },
    mounted: function () {
        let vm = this;
        this.$nextTick(() => {
            vm.initialiseAssignedOfficerSelect();
        });
    },
    methods: {
        user_is_eligible: function (status_roles) {
            /** Checks whether the user's roles allow for making certain
             *  actions (e.g. complete, discard) on this competitive process
             *  given the competitive process' current workflow status.
             */

            let status_id = this.competitiveProcess.status_id;

            if (status_id in status_roles) {
                let eligible_roles = status_roles[status_id];
                // Return true if the accessing user's roles are in the eligible roles
                if (
                    eligible_roles.filter((role) =>
                        this.competitiveProcess.accessing_user_roles.includes(
                            role
                        )
                    ).length > 0
                ) {
                    return true;
                }
            }
            return false;
        },
        action_roles: function (action) {
            /** Returns a dictionary of workflow status and user roles to define
             *  when workflow action items (e.g. complete, discard) are usable
             */

            if (['complete', 'discard'].includes(action)) {
                // A competitive process editor can complete or discard a competitive process in progress
                return {
                    [constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS.ID]: [
                        constants.ROLES.COMPETITIVE_PROCESS_EDITOR.ID,
                    ],
                    [constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS_UNLOCKED
                        .ID]: [constants.ROLES.COMPETITIVE_PROCESS_EDITOR.ID],
                };
            } else if (action == 'unlock') {
                // A competitive process editor can unlock a completed or declined competitive process
                return {
                    [constants.COMPETITIVE_PROCESS_STATUS.COMPLETED_APPLICATION
                        .ID]: [constants.ROLES.COMPETITIVE_PROCESS_EDITOR.ID],
                    [constants.COMPETITIVE_PROCESS_STATUS.COMPLETED_DECLINED
                        .ID]: [constants.ROLES.COMPETITIVE_PROCESS_EDITOR.ID],
                };
            } else {
                console.warn(`action_roles: action ${action} not recognised`);
                return {};
            }
        },
        get_allowed_ids: function (ids) {
            let displayable_status_ids = ids.map((a_status) => {
                if (Object.prototype.hasOwnProperty.call(a_status, 'ID'))
                    return a_status.ID;
                else if (Object.prototype.hasOwnProperty.call(a_status, 'id'))
                    return a_status.id;
                else if (Object.prototype.hasOwnProperty.call(a_status, 'Id'))
                    return a_status.Id;
                else return a_status;
            });

            return displayable_status_ids;
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
                    // Competitve process only has one relevant status, so we can just set the assigned officer
                    if (
                        [
                            constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS.ID,
                            constants.COMPETITIVE_PROCESS_STATUS
                                .IN_PROGRESS_UNLOCKED.ID,
                        ].includes(vm.competitiveProcess.status_id)
                    ) {
                        vm.competitiveProcess.assigned_officer = selected.val();
                    } else {
                        console.warn(
                            `Can not change assignment while in status {vm.competitiveProcess.status}`
                        );
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
                    // Competitve process only has one relevant status, so we can just unset the assigned officer
                    if (
                        [
                            constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS.ID,
                            constants.COMPETITIVE_PROCESS_STATUS
                                .IN_PROGRESS_UNLOCKED.ID,
                        ].includes(vm.competitiveProcess.status_id)
                    ) {
                        vm.competitiveProcess.assigned_officer = null;
                    } else {
                        console.warn(
                            `Can not change assignment while in status {vm.competitiveProcess.status}`
                        );
                    }
                    vm.assignTo();
                });
        },
        updateAssignedOfficerSelect: function (selected_user) {
            let vm = this;

            $(vm.$refs.assigned_officer).val(selected_user);
            $(vm.$refs.assigned_officer).trigger('change');
        },
        refreshFromResponse: function (response) {
            let vm = this;
            vm.competitiveProcess = helpers.copyObject(response.body);
            vm.competitiveProcess.applicant.address =
                vm.competitiveProcess.applicant.address != null
                    ? vm.competitiveProcess.applicant.address
                    : {};
            vm.$nextTick(() => {
                vm.initialiseAssignedOfficerSelect(true);
                vm.updateAssignedOfficerSelect();
            });
        },
        assignRequestUser: function () {
            this.$emit('assignRequestUser');
        },
        assignTo: function () {
            this.$emit('assignTo');
        },
        issueComplete: function () {
            this.$emit('issueComplete');
        },
        issueDiscard: function () {
            this.$emit('issueDiscard');
        },
        issueUnlock: function () {
            this.$emit('issueUnlock');
        },
    },
};
</script>
