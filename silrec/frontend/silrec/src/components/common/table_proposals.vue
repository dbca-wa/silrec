<template>
    <div>
        <CollapsibleFilters
            ref="collapsible_filters"
            component_title="Filters"
            class="mb-2"
            @created="collapsible_component_mounted"
        >
            <div class="row mt-1 p-2">
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Type</label>
                        <select
                            v-model="filterApplicationType"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="application_type in application_types"
                                :key="application_type.id"
                                :value="application_type.id"
                            >
                                {{ application_type.name_display }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Status</label>
                        <select
                            v-model="filterApplicationStatus"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="status in application_statuses"
                                :key="status.code"
                                :value="status.code"
                            >
                                {{ status.description }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Lodged From</label>
                        <div
                            ref="proposalDateFromPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterProposalLodgedFrom"
                                type="date"
                                class="form-control"
                            />
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Lodged To</label>
                        <div
                            ref="proposalDateToPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterProposalLodgedTo"
                                type="date"
                                class="form-control"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div v-if="!email_user_id_assigned" class="row">
            <div class="col-md-12">
                <div class="text-end">
                    <button
                        type="button"
                        class="btn btn-primary mb-2"
                        @click="new_application_button_clicked"
                    >
                        <i class="fa-solid fa-circle-plus"></i>
                        {{ new_migrate_button_text }}
                    </button>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="application_datatable"
                    :dt-options="dtOptions"
                    :dt-headers="dtHeaders"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { v4 as uuid } from 'uuid';
import { api_endpoints, constants } from '@/utils/hooks';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import { expandToggle } from '@/components/common/table_functions.js';
import { discardProposal } from '@/components/common/workflow_functions.js';

export default {
    name: 'TableApplications',
    components: {
        datatable,
        CollapsibleFilters,
    },
    props: {
        level: {
            type: String,
            required: true,
            validator: function (val) {
                let options = [
                    'internal',
                    'referral',
                    'external',
                    'organisation_view',
                ];
                return options.indexOf(val) != -1 ? true : false;
            },
        },
        email_user_id_assigned: {
            type: Number,
            required: false,
            default: 0,
        },
        targetOrganisationId: {
            type: Number,
            required: false,
            default: 0,
        },
        targetEmailUserId: {
            type: Number,
            required: false,
            default: 0,
        },
        filterApplicationTypeCacheName: {
            type: String,
            required: false,
            default: 'filterApplicationType',
        },
        filterApplicationStatusCacheName: {
            type: String,
            required: false,
            default: 'filterApplicationStatus',
        },
        filterProposalLodgedFromCacheName: {
            type: String,
            required: false,
            default: 'filterApplicationLodgedFrom',
        },
        filterProposalLodgedToCacheName: {
            type: String,
            required: false,
            default: 'filterApplicationLodgedTo',
        },
    },
    emits: ['filter-appied'],
    data() {
        let vm = this;
        return {
            datatable_id: 'applications-datatable-' + uuid(),

            // selected values for filtering
            filterApplicationType: sessionStorage.getItem(
                vm.filterApplicationTypeCacheName
            )
                ? sessionStorage.getItem(vm.filterApplicationTypeCacheName)
                : 'all',
            filterApplicationStatus: sessionStorage.getItem(
                vm.filterApplicationStatusCacheName
            )
                ? sessionStorage.getItem(vm.filterApplicationStatusCacheName)
                : 'all',
            filterProposalLodgedFrom: sessionStorage.getItem(
                vm.filterProposalLodgedFromCacheName
            )
                ? sessionStorage.getItem(vm.filterProposalLodgedFromCacheName)
                : '',
            filterProposalLodgedTo: sessionStorage.getItem(
                vm.filterProposalLodgedToCacheName
            )
                ? sessionStorage.getItem(vm.filterProposalLodgedToCacheName)
                : '',

            // filtering options
            application_types: [],
            application_statuses: [],

            dateFormat: 'DD/MM/YYYY',
            datepickerOptions: {
                format: 'DD/MM/YYYY',
                showClear: true,
                useCurrent: false,
                keepInvalid: true,
                allowInputToggle: true,
            },
        };
    },
    computed: {
        new_migrate_button_text: function () {
            if (this.level == 'internal') {
                return 'Create New or Migrate Existing Lease/Licence';
            }
            return 'New Proposal';
        },
        number_of_columns: function () {
            let num = this.$refs.application_datatable.vmDataTable
                .columns(':visible')
                .nodes().length;
            return num;
        },
        filterApplied: function () {
            let filter_applied = true;
            if (
                this.filterApplicationStatus === 'all' &&
                this.filterApplicationType === 'all' &&
                this.filterProposalLodgedFrom === '' &&
                this.filterProposalLodgedTo === ''
            ) {
                filter_applied = false;
            }
            return filter_applied;
        },
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        is_external: function () {
            return this.level == 'external';
        },
        is_internal: function () {
            return this.level == 'internal';
        },
        is_organisation_view: function () {
            return this.level == 'organisation_view';
        },
        dtHeaders: function () {
            if (this.is_organisation_view) {
                return [
                    'id',
                    'Number',
                    'Type',
                    'Status',
                    'Lodged On',
                    'Action',
                ];
            }
            if (this.is_external) {
                return [
                    'id',
                    'Number',
                    'Type',
                    'Submitter',
                    'Proponent',
                    'Status',
                    'Lodged On',
                    'Action',
                ];
            }
            if (this.is_internal) {
                return [
                    'id',
                    'Number',
                    'Type',
                    'Submitter',
                    'Proponent',
                    'Status',
                    'Lodged On',
                    'Assigned Officer',
                    'Action',
                ];
            }
            // Default
            return [];
        },
        column_id: function () {
            return {
                // 1. ID
                data: 'id',
                orderable: false,
                searchable: false,
                visible: false,
                render: function (row, type, full) {
                    return full.id;
                },
            };
        },
        column_lodgement_number: function () {
            return {
                // 2. Lodgement Number
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    let lodgement_number = full.lodgement_number;
                    if (full.migrated) {
                        lodgement_number += ' (M)';
                    }
                    if (full.referral_processing_status) {
                        if (
                            full.referral_processing_status ==
                            constants.REFERRAL_STATUS
                                .PROCESSING_STATUS_WITH_REFERRAL.ID
                        ) {
                            lodgement_number += `<i class="fa-solid fa-circle-exclamation text-warning ms-1" title="With Referral"></i>`;
                        } else if (
                            full.referral_processing_status ==
                            constants.REFERRAL_STATUS
                                .PROCESSING_STATUS_COMPLETED.ID
                        ) {
                            lodgement_number += `<i class="fa-solid fa-circle-check text-success ms-1" title="Completed"></i>`;
                        }
                        lodgement_number += ``;
                    }
                    return lodgement_number;
                },
                name: 'lodgement_number',
            };
        },
        column_type: function () {
            return {
                // 3. Type (This corresponds to the 'ApplicationType' at the backend)
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    let text = full.application_type.name_display;
                    if (full.proposal_type?.code != 'new') {
                        text += ` (${full.proposal_type?.description})`;
                    }
                    return text;
                },
                name: 'application_type_id__name',
            };
        },
        column_submitter: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (full.submitter) {
                        return full.submitter.fullname;
                    } else {
                        return '';
                    }
                },
                name: 'submitter__first_name, submitter__last_name',
            };
        },
        column_applicant: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (full.applicant_name) {
                        return `${full.applicant_name}`;
                    }
                    return '';
                },
                name: 'proposalapplicant__first_name, proposalapplicant__last_name',
            };
        },
        column_status: function () {
            let vm = this;
            return {
                // 5. Status
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (vm.is_internal) {
                        return full.processing_status;
                    }
                    return full.customer_status;
                },
                name: 'processing_status',
            };
        },
        column_lodged_on: function () {
            return {
                // 6. Lodged
                data: 'id',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (full.lodgement_date) {
                        return moment(full.lodgement_date).format('DD/MM/YYYY');
                    }
                    return '';
                },
                name: 'lodgement_date',
            };
        },
        column_assigned_officer: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (full.assigned_officer) {
                        return full.assigned_officer.fullname;
                    } else {
                        return '';
                    }
                },
                name: 'assigned_officer__first_name, assigned_officer__last_name, assigned_approver__first_name, assigned_approver__last_name',
            };
        },
        column_action: function () {
            let vm = this;
            return {
                // 8. Action
                data: 'id',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let links = '';
                    if (vm.is_internal) {
                        if (full.accessing_user_can_process) {
                            links += `<a href='/internal/proposal/${full.id}'>Process</a><br/>`;
                        } else if (full.can_edit_invoicing_details) {
                            links += `<a href='/internal/proposal/${full.id}'>Edit Invoicing</a><br/>`;
                        } else {
                            links += `<a href='/internal/proposal/${full.id}'>View</a><br/>`;
                        }
                    }
                    if (vm.is_external) {
                        if (full.can_user_edit) {
                            links += `<a href='/external/proposal/${full.id}'>Continue</a><br/>`;
                            links += `<a href='#${full.id}' data-discard-proposal='${full.id}' data-proposal-lodgement-number='${full.lodgement_number}'>Discard</a><br/>`;
                        } else if (full.can_user_view) {
                            if (vm.email_user_id_assigned) {
                                links += `<a href="/external/proposal/${full.id}/referral/">Complete Referral</a><br/>`;
                            } else {
                                links += `<a href='/external/proposal/${full.id}'>View</a><br/>`;
                            }
                        }
                    }
                    return links;
                },
            };
        },
        dtOptions: function () {
            let vm = this;

            let columns = [];
            let search = null;
            let buttons = [
                {
                    extend: 'excel',
                    text: '<i class="fa-solid fa-download"></i> Excel',
                    className: 'btn btn-primary rounded me-2',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    },
                },
                {
                    extend: 'csv',
                    text: '<i class="fa-solid fa-download"></i> CSV',
                    className: 'btn btn-primary rounded',
                    exportOptions: {
                        columns: ':not(.no-export)',
                    },
                },
            ];
            if (this.is_organisation_view) {
                columns = [
                    vm.column_id,
                    vm.column_lodgement_number,
                    vm.column_type,
                    vm.column_status,
                    vm.column_lodged_on,
                    vm.column_action,
                ];
                search = true;
            }

            if (vm.is_external) {
                columns = [
                    vm.column_id,
                    vm.column_lodgement_number,
                    vm.column_type,
                    vm.column_submitter,
                    vm.column_applicant,
                    vm.column_status,
                    vm.column_lodged_on,
                    //vm.column_assigned_officer,
                    vm.column_action,
                ];
                search = false;
            }
            if (vm.is_internal) {
                columns = [
                    vm.column_id,
                    vm.column_lodgement_number,
                    vm.column_type,
                    vm.column_submitter,
                    vm.column_applicant,
                    vm.column_status,
                    vm.column_lodged_on,
                    vm.column_assigned_officer,
                    vm.column_action,
                ];
                // eslint-disable-next-line no-unused-vars
                search = true;
            }

            return {
                autoWidth: false,
                responsive: true,
                serverSide: true,
                searching: true,
                columnDefs: [
                    { responsivePriority: 1, targets: 0 },
                    {
                        responsivePriority: 2,
                        targets: -1,
                        className: 'no-export',
                    },
                ],
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                rowCallback: function (row, proposal) {
                    let row_jq = $(row);
                    row_jq.attr('id', 'proposal_id_' + proposal.id);
                },
                ajax: {
                    url:
                        api_endpoints.proposals_paginated_list +
                        '?format=datatables&email_user_id_assigned=' +
                        vm.email_user_id_assigned +
                        '&target_email_user_id=' +
                        vm.targetEmailUserId +
                        '&target_organisation_id=' +
                        vm.targetOrganisationId,
                    dataSrc: 'data',

                    // adding extra GET params for Custom filtering
                    data: function (d) {
                        d.filter_application_type = vm.filterApplicationType;
                        d.filter_application_status =
                            vm.filterApplicationStatus;
                        d.filter_lodged_from = vm.filterProposalLodgedFrom;
                        d.filter_lodged_to = vm.filterProposalLodgedTo;
                        d.level = vm.level;

                        // Add search terms to be concatenated on the queryset
                        d.search_terms =
                            'proposalapplicant__first_name, proposalapplicant__last_name';
                    },
                },
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,
                order: [[1, 'desc']],
                columns: columns,
                processing: true,
                initComplete: function () {},
            };
        },
    },
    watch: {
        filterApplicationType: function () {
            this.$refs.application_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterApplicationTypeCacheName,
                this.filterApplicationType
            );
            this.$emit('filter-appied');
        },
        filterApplicationStatus: function () {
            this.$refs.application_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterApplicationStatusCacheName,
                this.filterApplicationStatus
            );
            this.$emit('filter-appied');
        },
        filterProposalLodgedFrom: function () {
            this.$refs.application_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterProposalLodgedFromCacheName,
                this.filterProposalLodgedFrom
            );
            this.$emit('filter-appied');
        },
        filterProposalLodgedTo: function () {
            this.$refs.application_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterProposalLodgedToCacheName,
                this.filterProposalLodgedTo
            );
            this.$emit('filter-appied');
        },
        filterApplied: function () {
            if (this.$refs.collapsible_filters) {
                // Collapsible component exists
                this.$refs.collapsible_filters.show_warning_icon(
                    this.filterApplied
                );
            }
        },
    },
    created: function () {
        this.fetchFilterLists();
    },
    mounted: function () {
        let vm = this;
        this.$nextTick(() => {
            vm.addEventListeners();
        });
    },
    methods: {
        updateFilters: function () {
            this.$nextTick(() => {
                this.filterApplicationType = sessionStorage.getItem(
                    this.filterApplicationTypeCacheName
                )
                    ? sessionStorage.getItem(
                          this.filterApplicationTypeCacheName
                      )
                    : 'all';
                this.filterApplicationStatus = sessionStorage.getItem(
                    this.filterApplicationStatusCacheName
                )
                    ? sessionStorage.getItem(
                          this.filterApplicationStatusCacheName
                      )
                    : 'all';
                this.filterProposalLodgedFrom = sessionStorage.getItem(
                    this.filterProposalLodgedFromCacheName
                )
                    ? sessionStorage.getItem(
                          this.filterProposalLodgedFromCacheName
                      )
                    : '';
                this.filterProposalLodgedTo = sessionStorage.getItem(
                    this.filterProposalLodgedToCacheName
                )
                    ? sessionStorage.getItem(
                          this.filterProposalLodgedToCacheName
                      )
                    : '';
                this.$refs.application_datatable.vmDataTable.draw();
            });
        },
        adjust_table_width: function () {
            this.$refs.application_datatable.vmDataTable.columns.adjust();
            this.$refs.application_datatable.vmDataTable.responsive.recalc();
        },
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(
                this.filterApplied
            );
        },
        new_application_button_clicked: async function () {
            var route = 'apply_proposal';
            if (this.level == 'internal') {
                route = 'migrate_proposal';
            }
            await this.$router.push({
                name: route,
            });
        },
        discardProposal: function (proposal_id, lodgement_number) {
            discardProposal(proposal_id, lodgement_number)
                .then(() => {
                    this.$refs.application_datatable.vmDataTable.draw();
                })
                .catch((error) => {
                    console.error(error);
                });
        },
        fetchFilterLists: async function () {
            let vm = this;

            // Application Types
            fetch(api_endpoints.application_types + 'key-value-list/').then(
                async (response) => {
                    const resData = await response.json();
                    vm.application_types = resData;
                },
                () => {}
            );

            // Application Statuses
            const res = await fetch(api_endpoints.application_statuses_dict);
            const data = await res.json();
            if (vm.is_internal) {
                vm.application_statuses = data.internal_statuses;
            } else {
                vm.application_statuses = data.external_statuses;
            }
        },
        addEventListeners: function () {
            let vm = this;
            vm.$refs.application_datatable.vmDataTable.on(
                'click',
                'a[data-discard-proposal]',
                function (e) {
                    e.preventDefault();
                    let id = $(this).attr('data-discard-proposal');
                    let lodgementNumber = $(this).attr(
                        'data-proposal-lodgement-number'
                    );
                    vm.discardProposal(id, lodgementNumber);
                }
            );

            // Listener for thr row
            vm.$refs.application_datatable.vmDataTable.on(
                'click',
                'td',
                function () {
                    expandToggle(vm, this);
                }
            );
        },
    },
};
</script>
