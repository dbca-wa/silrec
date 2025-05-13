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
                        <label for="">Status</label>
                        <select
                            v-model="filterCompetitiveProcessStatus"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="status in application_statuses"
                                :key="status.id"
                                :value="status.id"
                            >
                                {{ status.text }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Created From</label>
                        <div
                            ref="proposalDateFromPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterCompetitiveProcessCreatedFrom"
                                type="date"
                                class="form-control"
                                placeholder="DD/MM/YYYY"
                            />
                            <span class="input-group-addon">
                                <span
                                    class="glyphicon glyphicon-calendar"
                                ></span>
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Created To</label>
                        <div
                            ref="proposalDateToPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterCompetitiveProcessCreatedTo"
                                type="date"
                                class="form-control"
                                placeholder="DD/MM/YYYY"
                            />
                            <span class="input-group-addon">
                                <span
                                    class="glyphicon glyphicon-calendar"
                                ></span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div class="row">
            <div class="text-end mb-2">
                <button
                    type="button"
                    class="btn btn-primary pull-right"
                    @click="new_competitive_process_clicked"
                >
                    <i class="fa-solid fa-circle-plus"></i> New Competitive
                    Process
                </button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="competitive_process_datatable"
                    :key="datatable_key"
                    :dt-options="datatable_options"
                    :dt-headers="datatable_headers"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { api_endpoints, constants, helpers, utils } from '@/utils/hooks';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import { v4 as uuid } from 'uuid';
import { expandToggleCP } from '@/components/common/table_functions.js';

export default {
    name: 'TableCompetitiveProcesses',
    components: {
        datatable,
        CollapsibleFilters,
    },
    data() {
        return {
            datatable_id: 'competitive-process-datatable-' + uuid(),
            datatable_key: uuid(),

            // selected values for filtering
            filterCompetitiveProcessStatus: sessionStorage.getItem(
                'filterCompetitiveProcessStatus'
            )
                ? sessionStorage.getItem('filterCompetitiveProcessStatus')
                : 'all',
            filterCompetitiveProcessCreatedFrom: sessionStorage.getItem(
                'filterCompetitiveProcessCreatedFrom'
            )
                ? sessionStorage.getItem('filterCompetitiveProcessCreatedFrom')
                : '',
            filterCompetitiveProcessCreatedTo: sessionStorage.getItem(
                'filterCompetitiveProcessCreatedTo'
            )
                ? sessionStorage.getItem('filterCompetitiveProcessCreatedTo')
                : '',

            // filtering options
            application_statuses: [],

            // Filters toggle
            filters_expanded: false,

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
        number_of_columns: function () {
            let num = this.$refs.competitive_process_datatable.vmDataTable
                .columns(':visible')
                .nodes().length;
            return num;
        },
        filterApplied: function () {
            let filter_applied = true;
            if (
                this.filterCompetitiveProcessStatus.toLowerCase() === 'all' &&
                this.filterCompetitiveProcessCreatedFrom.toLowerCase() === '' &&
                this.filterCompetitiveProcessCreatedTo.toLowerCase() === ''
            ) {
                filter_applied = false;
            }
            return filter_applied;
        },
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'Tru3';
            }
            return false;
        },
        datatable_headers: function () {
            return [
                'Id',
                'Lodgement Number',
                'Registration of Interest',
                'Status',
                'Created On',
                'Assigned Officer',
                'Action',
            ];
        },
        column_id: function () {
            return {
                data: 'id',
                // name: 'id',
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
                data: 'lodgement_number',
                name: 'lodgement_number',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (full.migrated) {
                        return full.lodgement_number + ' (M)';
                    } else {
                        return full.lodgement_number;
                    }
                },
            };
        },
        column_registration_of_interest: function () {
            return {
                data: 'registration_of_interest',
                name: 'originating_proposal__lodgement_number',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (full.registration_of_interest) {
                        return `<a href="/internal/proposal/${full.registration_of_interest.id}">${full.registration_of_interest.lodgement_number}</a>`;
                    } else {
                        return '';
                    }
                },
            };
        },
        column_status: function () {
            return {
                data: 'status',
                name: 'status',
                orderable: true,
                searchable: true,
                visible: true,
            };
        },
        column_created_on: function () {
            return {
                data: 'id',
                name: 'created_at',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    return moment(full.created_at).format('DD/MM/YYYY');
                },
            };
        },
        column_assigned_to: function () {
            return {
                data: 'assigned_officer',
                name: 'assigned_officer_id__first_name, assigned_officer_id__last_name', // This functionality works with `LedgerDatatablesFilterBackend` as filter backaned
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
            };
        },
        column_action: function () {
            return {
                // 8. Action
                // data: "action",
                data: null,
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let links = '';
                    if (full.can_accessing_user_process) {
                        links +=
                            '<a href="/internal/competitive_process/' +
                            full.id +
                            '">Process</a>';
                        links +=
                            '<br /><a href="#" data-discard="' +
                            full.id +
                            '" data-lodgement-number="' +
                            full.lodgement_number +
                            '">Discard</a>';
                    } else if (full.can_accessing_user_view) {
                        links +=
                            '<a href="/internal/competitive_process/' +
                            full.id +
                            '">View</a>';
                    }
                    return links;
                },
            };
        },
        datatable_options: function () {
            let vm = this;

            let columns = [
                vm.column_id,
                vm.column_lodgement_number,
                vm.column_registration_of_interest,
                vm.column_status,
                vm.column_created_on,
                vm.column_assigned_to,
                vm.column_action,
            ];
            let search = true;
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

            return {
                autoWidth: false,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                rowCallback: function (row, competitive_process) {
                    let row_jq = $(row);
                    row_jq.attr(
                        'id',
                        'competitive_process_id_' + competitive_process.id
                    );
                },
                responsive: true,
                serverSide: true,
                searching: search,
                columnDefs: [
                    { responsivePriority: 1, targets: 0 },
                    {
                        responsivePriority: 2,
                        targets: -1,
                        className: 'no-export',
                    },
                ],
                ajax: {
                    url:
                        api_endpoints.competitive_process +
                        '?format=datatables',
                    dataSrc: 'data',

                    // adding extra GET params for Custom filtering
                    data: function (d) {
                        d.filter_status = vm.filterCompetitiveProcessStatus;
                        d.filter_competitive_process_created_from =
                            vm.filterCompetitiveProcessCreatedFrom;
                        d.filter_competitive_process_created_to =
                            vm.filterCompetitiveProcessCreatedTo;
                    },
                },
                //dom: 'lBfrtip',
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                //buttons:[ ],
                buttons: buttons,
                order: [[1, 'desc']],
                columns: columns,
                processing: true,
                initComplete: function () {},
            };
        },
    },
    watch: {
        filterCompetitiveProcessStatus: function () {
            this.$refs.competitive_process_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                'filterCompetitiveProcessStatus',
                this.filterCompetitiveProcessStatus
            );
        },
        filterCompetitiveProcessCreatedFrom: function () {
            this.$refs.competitive_process_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                'filterCompetitiveProcessCreatedFrom',
                this.filterCompetitiveProcessCreatedFrom
            );
        },
        filterCompetitiveProcessCreatedTo: function () {
            this.$refs.competitive_process_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                'filterCompetitiveProcessCreatedTo',
                this.filterCompetitiveProcessCreatedTo
            );
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
        createNewCompetitiveProcess: async function () {
            await fetch(api_endpoints.competitive_process, { method: 'POST' })
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
                    const competitive_process = Object.assign({}, data);
                    this.$router.push({
                        name: 'internal-competitive-process',
                        params: {
                            competitive_process_id: competitive_process.id,
                        },
                    });
                })
                .catch((error) => {
                    console.error(
                        `Error fetching external approval data ${error.message}`
                    );
                    throw error;
                });
        },
        discard: async function (
            competitive_process_id,
            competitive_process_lodgement_number
        ) {
            let vm = this;
            await swal
                .fire({
                    title: `Discard Competitive Process ${competitive_process_lodgement_number}`,
                    text: 'Are you sure you want to discard this competitive process?',
                    icon: 'question',
                    showCancelButton: true,
                    reverseButtons: true,
                    confirmButtonText: 'Discard',
                    confirmButtonColor: '#226fbb',
                })
                .then(async (result) => {
                    if (result.isConfirmed) {
                        const requestOptions = {
                            method: 'POST',
                        };
                        let url = helpers.add_endpoint_json(
                            api_endpoints.competitive_process,
                            competitive_process_id + '/discard'
                        );
                        utils
                            .fetchUrl(url, requestOptions)
                            .then(() => {
                                vm.$refs.competitive_process_datatable.vmDataTable.draw();
                            })
                            .catch((error) => {
                                swal.fire({
                                    title: 'Reissue Approval',
                                    text: error,
                                    icon: 'error',
                                });
                            });
                    }
                });
        },
        adjust_table_width: function () {
            this.$refs.competitive_process_datatable.vmDataTable.columns.adjust();
            this.$refs.competitive_process_datatable.vmDataTable.responsive.recalc();
        },
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(
                this.filterApplied
            );
        },
        expandCollapseFilters: function () {
            this.filters_expanded = !this.filters_expanded;
        },
        new_competitive_process_clicked: function () {
            let vm = this;
            swal.fire({
                title: 'Create New Competitive Process',
                text: 'Are you sure you want to create new competitive process?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Create New Competitive Process',
                preConfirm: () => {
                    return true;
                },
                reverseButtons: true,
            })
                .then(async (result) => {
                    if (result.isConfirmed) {
                        // When Yes
                        await vm.createNewCompetitiveProcess();
                        vm.datatable_key = uuid();
                    }
                })
                .catch((error) => {
                    swal.fire({
                        title: 'New Competitive Process',
                        text: error.message,
                        icon: 'error',
                    });
                });
        },
        fetchFilterLists: async function () {
            let vm = this;
            const res = await fetch(
                api_endpoints.competitive_process_statuses_dict
            );
            if (!res.ok) throw new Error(res.statusText); // 400s or 500s error

            let aho = await res.json();
            vm.application_statuses = aho;
        },
        addEventListeners: function () {
            let vm = this;
            // Listener for thr row
            vm.$refs.competitive_process_datatable.vmDataTable.on(
                'click',
                'td',
                function () {
                    expandToggleCP(vm, this);
                }
            );
            vm.$refs.competitive_process_datatable.vmDataTable.on(
                'click',
                'a[data-discard]',
                function (e) {
                    var id = $(this).attr('data-discard');
                    var lodgement_number = $(this).attr(
                        'data-lodgement-number'
                    );
                    e.preventDefault();
                    vm.discard(id, lodgement_number);
                }
            );
        },
    },
};
</script>
<style scoped>
.expand-icon {
    background-color: blue !important;
    color: tomato !important;
}
</style>
