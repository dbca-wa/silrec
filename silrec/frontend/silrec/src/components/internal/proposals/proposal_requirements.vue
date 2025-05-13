<template id="proposal_requirements">
    <div>
        <FormSection
            :form-collapse="false"
            label="Conditions"
            index="conditions"
        >
            <BootstrapAlert
                v-if="
                    conditionsMissingDates && conditionsMissingDates.length > 0
                "
                icon="exclamation-triangle-fill"
                type="warning"
            >
                A due date is required for every condition
            </BootstrapAlert>
            <form class="form-horizontal" action="index.html" method="post">
                <div class="row">
                    <div class="col-sm-12">
                        <button
                            v-if="hasAssessorMode || isReferrerCanEdit"
                            style="margin-bottom: 10px"
                            class="btn btn-primary float-end"
                            @click.prevent="addRequirement()"
                        >
                            Add Condition
                        </button>
                    </div>
                </div>
                <div class="row">
                    <div class="col-sm-12">
                        <datatable
                            :id="datatableId"
                            ref="requirements_datatable"
                            :dt-options="requirement_options"
                            :dt-headers="requirement_headers"
                        />
                    </div>
                </div>
            </form>

            <RequirementDetail
                v-if="proposal && requirements"
                ref="requirement_detail"
                :key="uuid"
                :proposal_id="proposal.id"
                :requirements="requirements"
                :selected-requirement="selectedRequirement"
                @update-requirement="updateRequirement"
            />
        </FormSection>
    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import { api_endpoints, constants, helpers } from '@/utils/hooks';
import datatable from '@vue-utils/datatable.vue';
import RequirementDetail from '@/components/internal/proposals/proposal_add_requirement.vue';
import FormSection from '@/components/forms/section_toggle.vue';

export default {
    name: 'InternalProposalRequirements',
    components: {
        datatable,
        RequirementDetail,
        FormSection,
    },
    props: {
        proposal: { type: Object, default: null },
        profile: { type: Object, default: null },
    },
    emits: ['updateRequirement', 'refreshProposal'],
    data: function () {
        let vm = this;
        return {
            uuid: 0,
            panelBody: 'proposal-requirements-' + uuid(),
            selectedRequirement: {},
            requirements: null,
            requirement_headers: [
                'Condition',
                'Due Date',
                'Repeats',
                'Source',
                'Action',
                'Order',
            ],
            requirement_options: {
                autoWidth: false,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    url: helpers.add_endpoint_json(
                        api_endpoints.proposal,
                        vm.proposal.id + '/requirements'
                    ),
                    dataSrc: '',
                },
                order: [],
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: [
                    {
                        extend: 'excel',
                        text: '<i class="fa-solid fa-download"></i> Excel',
                        className: 'btn btn-primary rounded me-2',
                        exportOptions: {
                            columns: ':visible',
                        },
                    },
                    {
                        extend: 'csv',
                        text: '<i class="fa-solid fa-download"></i> CSV',
                        className: 'btn btn-primary rounded',
                        exportOptions: {
                            columns: ':visible',
                        },
                    },
                ],
                columns: [
                    {
                        data: 'requirement',
                        // eslint-disable-next-line no-unused-vars
                        mRender: function (data, type, full) {
                            let result = `<span data-bs-toggle="tooltip" data-bs-placement="top" style="max-width:220px" class="d-inline-block text-truncate" title="${data}">${data}</span>`;
                            return result;
                        },
                    },
                    {
                        data: 'due_date',
                        // eslint-disable-next-line no-unused-vars
                        mRender: function (data, type, full) {
                            return data != '' && data != null
                                ? moment(data).format('DD/MM/YYYY')
                                : '';
                        },
                        orderable: false,
                    },
                    {
                        data: 'recurrence',
                        mRender: function (data, type, full) {
                            if (full.recurrence) {
                                let recurrence_interval = '';
                                switch (full.recurrence_pattern) {
                                    case 1:
                                        recurrence_interval = 'week';
                                        break;
                                    case 2:
                                        recurrence_interval = 'month';
                                        break;
                                    case 3:
                                        recurrence_interval = 'year';
                                        break;
                                }
                                let plural = '';
                                if (full.recurrence_schedule > 1) {
                                    plural = 's';
                                }
                                return `Once every ${full.recurrence_schedule} ${recurrence_interval}${plural}`;
                            }
                            return 'N/A';
                        },
                        orderable: false,
                    },
                    {
                        data: 'source',
                        mRender: function (data, type, full) {
                            if (full.source) {
                                return full.source.fullname;
                            } else {
                                return '';
                            }
                        },
                        orderable: false,
                    },
                    {
                        data: 'id',
                        mRender: function (data, type, full) {
                            let links = '';
                            if (vm.hasAssessorMode || vm.isReferrer) {
                                // Whether the current user can edit/delete a referral
                                let show_action_btns =
                                    vm.hasAssessorMode ||
                                    (vm.isReferrerCanEdit &&
                                        full.can_referral_edit);
                                // Whether a referral has been completed, but can still be viewed
                                let referral_completed =
                                    vm.isReferrer &&
                                    !vm.isReferrerCanEdit &&
                                    full.can_referral_edit;
                                // Assessors can edit and/or delete all proposed requirements
                                // Referral parties can only edit or delete their own requirements
                                if (show_action_btns) {
                                    links += `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                    links += `<a href='#' class="deleteRequirement" data-id="${full.id}">Delete</a><br/>`;
                                } else if (referral_completed) {
                                    links += 'Referral completed<br/>';
                                }
                            }
                            return links;
                        },
                        orderable: false,
                    },
                    {
                        data: 'id',
                        mRender: function (data, type, full) {
                            let links = '';
                            if (vm.proposal.assessor_mode.has_assessor_mode) {
                                links += `<a class="dtMoveUp" data-id="${full.id}" href='#'><i class="fa fa-angle-up fa-2x"></i></a><br/>`;
                                links += `<a class="dtMoveDown" data-id="${full.id}" href='#'><i class="fa fa-angle-down fa-2x"></i></a><br/>`;
                            }
                            return links;
                        },
                        orderable: false,
                    },
                ],
                processing: true,
                initComplete: function () {
                    helpers.enablePopovers();
                    vm.addTableListeners();
                },
            },
        };
    },
    computed: {
        datatableId: function () {
            return 'requirements-datatable';
        },
        hasAssessorMode() {
            return this.proposal.assessor_mode.has_assessor_mode;
        },
        isReferrer() {
            return this.proposal.assessor_mode.is_referee;
        },
        isReferrerCanEdit() {
            return this.proposal.assessor_mode.referee_can_edit;
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
    },
    watch: {
        hasAssessorMode() {
            // reload the table
            this.$refs.requirements_datatable.vmDataTable.ajax.reload();
        },
    },
    mounted: async function () {
        if (this.profile.is_assessor) {
            await this.fetchRequirements();
        }
        this.$nextTick(() => {
            this.eventListeners();
            let tooltipTriggerList = [].slice.call(
                document.querySelectorAll('[data-bs-toggle="tooltip"]')
            );
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        });
    },
    methods: {
        addRequirement() {
            this.uuid++;
            this.selectedRequirement = null;
            this.$nextTick(() => {
                this.$refs.requirement_detail.isModalOpen = true;
            });
        },
        removeRequirement: async function (_id) {
            swal.fire({
                title: 'Remove Requirement',
                text: 'Are you sure you want to remove this requirement?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Yes',
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    const response = await fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposal_requirements,
                            _id + '/discard'
                        )
                    );
                    if (response.ok) {
                        this.selectedRequirement = {}; // Unselect, so it can be re-added without error
                        this.$emit('refreshProposal');
                        this.$refs.requirements_datatable.vmDataTable.ajax.reload();
                    } else {
                        console.error('error');
                    }
                }
            });
        },
        fetchRequirements: async function () {
            const url = api_endpoints.proposal_standard_requirements;
            const response = await fetch(url, {
                body: JSON.stringify({
                    application_type_id: this.proposal.application_type.id,
                }),
                method: 'POST',
            });
            if (response.ok) {
                this.requirements = await response.json();
            } else {
                console.error('error');
            }
        },
        editRequirement: async function (_id) {
            const response = await fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal_requirements,
                    _id
                )
            );
            if (response.ok) {
                const resData = await response.json();
                this.selectedRequirement = Object.assign({}, resData);
                this.uuid++;
                this.$nextTick(() => {
                    this.$refs.requirement_detail.isModalOpen = true;
                });
            } else {
                console.error('error');
            }
        },
        updateRequirement(requirement) {
            this.$emit('updateRequirement', requirement);
            this.$emit('refreshProposal');
            this.$refs.requirements_datatable.vmDataTable.ajax.reload();
        },
        eventListeners() {
            let vm = this;
            if (!vm.$refs.requirements_datatable) {
                // Prevent uncaught error when clicking show/hide too fast (why would anyone even do this?)
                return;
            }
            vm.$refs.requirements_datatable.vmDataTable.on(
                'click',
                '.deleteRequirement',
                function (e) {
                    var id = $(this).attr('data-id');
                    e.preventDefault();
                    vm.removeRequirement(id);
                }
            );
            vm.$refs.requirements_datatable.vmDataTable.on(
                'click',
                '.editRequirement',
                function (e) {
                    var id = $(this).attr('data-id');
                    e.preventDefault();
                    vm.editRequirement(id);
                }
            );
        },
        addTableListeners: function () {
            let vm = this;
            if (!vm.$refs.requirements_datatable) {
                // Prevent uncaught error when clicking show/hide too fast (why would anyone even do this?)
                return;
            }
            $(vm.$refs.requirements_datatable.table)
                .find('tr:last .dtMoveDown')
                .remove();
            $(vm.$refs.requirements_datatable.table)
                .children('tbody')
                .find('tr:first .dtMoveUp')
                .remove();
            // Remove previous binding before adding it
            $('.dtMoveUp').off('click');
            $('.dtMoveDown').off('click');

            // Bind clicks to functions
            vm.$refs.requirements_datatable.vmDataTable.on(
                'click',
                '.dtMoveUp',
                function (e) {
                    var id = $(this).attr('data-id');
                    e.preventDefault();
                    vm.moveUp(id);
                }
            );
            vm.$refs.requirements_datatable.vmDataTable.on(
                'click',
                '.dtMoveDown',
                function (e) {
                    var id = $(this).attr('data-id');
                    e.preventDefault();
                    vm.moveDown(id);
                }
            );
        },
        async sendDirection(req, direction) {
            let movement = direction == 'down' ? 'move_down' : 'move_up';
            try {
                await fetch(
                    helpers.add_endpoint_json(
                        api_endpoints.proposal_requirements,
                        req + '/' + movement
                    )
                );
                this.$parent.uuid++;
            } catch (error) {
                console.error(error);
            }
        },
        moveUp(id) {
            this.sendDirection(id, 'up');
        },
        moveDown(id) {
            this.sendDirection(id, 'down');
        },
    },
};
</script>
