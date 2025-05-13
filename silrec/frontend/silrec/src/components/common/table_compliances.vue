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
                        <label for="">Approval Type</label>
                        <select
                            v-model="filterApprovalType"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="t in approval_types"
                                :key="t.id"
                                :value="t.id"
                            >
                                {{ t.name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Status</label>
                        <select
                            v-model="filterComplianceStatus"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="status in compliance_statuses"
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
                        <label for="">Due Date From</label>
                        <div
                            ref="complianceDateFromPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterComplianceDueDateFrom"
                                type="date"
                                class="form-control"
                                placeholder="DD/MM/YYYY"
                            />
                            <span class="input-group-addon">
                                <span class="glyphicon glyphicon-calendar" />
                            </span>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Due Date To</label>
                        <div
                            ref="complianceDateToPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterComplianceDueDateTo"
                                type="date"
                                class="form-control"
                                placeholder="DD/MM/YYYY"
                            />
                            <span class="input-group-addon">
                                <span class="glyphicon glyphicon-calendar" />
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="compliances_datatable"
                    :dt-options="compliancesOptions"
                    :dt-headers="compliancesHeaders"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { api_endpoints, constants } from '@/utils/hooks';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';

export default {
    name: 'TableCompliances',
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
        targetEmailUserId: {
            type: Number,
            required: false,
            default: 0,
        },
        targetOrganisationId: {
            type: Number,
            required: false,
            default: 0,
        },
        compliancesReferredToMe: {
            type: Boolean,
            default: false,
        },
        filterApprovalTypeCacheName: {
            type: String,
            required: false,
            default: 'filterApprovalType',
        },
        filterComplianceStatusCacheName: {
            type: String,
            required: false,
            default: 'filterComplianceStatus',
        },
        filterComplianceDueDateFromCacheName: {
            type: String,
            required: false,
            default: 'filterComplianceDueDateFrom',
        },
        filterComplianceDueDateToCacheName: {
            type: String,
            required: false,
            default: 'filterComplianceDueDateTo',
        },
    },
    data() {
        let vm = this;
        return {
            datatable_id: 'compliances-datatable-' + vm._.uid,

            // selected values for filtering
            filterApprovalType: sessionStorage.getItem(
                vm.filterApprovalTypeCacheName
            )
                ? sessionStorage.getItem(vm.filterApprovalTypeCacheName)
                : 'all',
            filterComplianceStatus: sessionStorage.getItem(
                vm.filterComplianceStatusCacheName
            )
                ? sessionStorage.getItem(vm.filterComplianceStatusCacheName)
                : 'all',
            filterComplianceDueDateFrom: sessionStorage.getItem(
                vm.filterComplianceDueDateFromCacheName
            )
                ? sessionStorage.getItem(
                      vm.filterComplianceDueDateFromCacheName
                  )
                : '',
            filterComplianceDueDateTo: sessionStorage.getItem(
                vm.filterComplianceDueDateToCacheName
            )
                ? sessionStorage.getItem(vm.filterComplianceDueDateToCacheName)
                : '',

            // filtering options
            approval_types: [],
            compliance_statuses: [],

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
        ajaxUrl: function () {
            let url =
                api_endpoints.compliances_paginated + '?format=datatables';
            if (this.targetEmailUserId) {
                url += '&target_email_user_id=' + this.targetEmailUserId;
            }
            if (this.targetOrganisationId) {
                url += '&target_organisation_id=' + this.targetOrganisationId;
            }
            if (this.compliancesReferredToMe) {
                url +=
                    '&compliances_referred_to_me=' +
                    this.compliancesReferredToMe;
            }
            return url;
        },
        filterApplied: function () {
            if (
                this.filterApprovalType === 'all' &&
                this.filterComplianceStatus.toLowerCase() === 'all' &&
                this.filterComplianceDueDateFrom.toLowerCase() === '' &&
                this.filterComplianceDueDateTo.toLowerCase() === ''
            ) {
                return false;
            } else {
                return true;
            }
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
        compliancesHeaders: function () {
            let headers = [
                'Id',
                'Number',
                'Approval Type',
                'Holder',
                'Approval',
                'Status',
                'Due Date',
                'Action',
            ];
            if (this.is_organisation_view) {
                headers = [
                    'Id',
                    'Number',
                    'Approval Type',
                    'Approval',
                    'Status',
                    'Due Date',
                    'Action',
                ];
            } else if (this.level === 'internal') {
                headers = [
                    'Id',
                    'Number',
                    'Approval Type',
                    'Holder',
                    'Approval',
                    'Status',
                    'Due Date',
                    'Assigned To',
                    'Action',
                ];
            }
            return headers;
        },
        columnId: function () {
            return {
                data: 'id',
                orderable: false,
                searchable: false,
                visible: false,
            };
        },
        holderColumn: function () {
            return {
                data: 'holder',
                orderable: false,
                searchable: true,
                visible: true,
                name: 'approval__current_proposal__ind_applicant__first_name, approval__current_proposal__ind_applicant__last_name, approval__current_proposal__org_applicant__ledger_organisation_name',
                render: function (row, type, full) {
                    //return full.approval_submitter;
                    return full.holder;
                },
            };
        },
        applicationTypeColumn: function () {
            return {
                data: 'approval_type',
                orderable: true,
                searchable: true,
                visible: true,
                name: 'approval__approval_type__name',
                render: function (row, type, full) {
                    return full.approval_type;
                    //return full.id;
                },
            };
        },
        lodgementNumberColumn: function () {
            return {
                // 2. Lodgement Number
                data: 'lodgement_number',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    let lodgement_number = full.lodgement_number;
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
            };
        },
        licenceNumberColumn: function () {
            return {
                // 3. Licence/Permit
                data: 'approval_lodgement_number',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.approval_lodgement_number;
                    //return full.id;
                },
                name: 'approval__lodgement_number',
            };
        },
        dueDateColumn: function () {
            return {
                // 5. Due Date
                data: 'due_date',
                orderable: true,
                searchable: false,
                visible: true,
            };
        },
        processingStatusColumn: function () {
            let vm = this;
            return {
                data: 'processing_status',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return vm.getStatusHtml(
                        full.processing_status_display,
                        full.due_date
                    );
                },
            };
        },
        customerStatusColumn: function () {
            let vm = this;
            return {
                data: 'customer_status',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return vm.getStatusHtml(
                        full.customer_status_display,
                        full.due_date
                    );
                },
            };
        },
        actionColumn: function () {
            let vm = this;
            return {
                // 7. Action
                data: 'id',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let links = '';
                    if (!vm.is_external) {
                        if (full.can_process) {
                            links += `<a href='/internal/compliance/${full.id}'>Process</a><br/>`;
                        } else {
                            if (
                                vm.compliancesReferredToMe &&
                                full.referral_processing_status ==
                                    constants.REFERRAL_STATUS
                                        .PROCESSING_STATUS_WITH_REFERRAL.ID
                            ) {
                                links += `<a href='/internal/compliance/${full.id}'>Process</a><br/>`;
                            } else {
                                links += `<a href='/internal/compliance/${full.id}'>View</a><br/>`;
                            }
                        }
                    } else {
                        if (full.can_user_view) {
                            links += `<a href='/external/compliance/${full.id}'>View</a><br/>`;
                        } else {
                            links += `<a href='/external/compliance/${full.id}'>Submit</a><br/>`;
                        }
                    }
                    return links;
                },
            };
        },
        assignedToNameColumn: function () {
            return {
                // 7. Action
                data: 'assigned_to_name',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.assigned_to_name;
                },
                name: 'assigned_to__first_name, assigned_to__last_name',
            };
        },
        applicableColumns: function () {
            let columns = [
                this.columnId,
                this.lodgementNumberColumn, // Number
                this.applicationTypeColumn, // Type
                this.holderColumn, // Holder
                this.licenceNumberColumn, // Approval
                this.customerStatusColumn, // Status
                this.dueDateColumn, // Due Date
                this.actionColumn, //Action
            ];
            if (this.is_organisation_view) {
                columns = [
                    this.columnId,
                    this.lodgementNumberColumn,
                    this.applicationTypeColumn,
                    this.licenceNumberColumn,
                    this.processingStatusColumn,
                    this.dueDateColumn,
                    this.actionColumn,
                ];
            } else if (this.level === 'internal') {
                columns = [
                    this.columnId,
                    this.lodgementNumberColumn,
                    this.applicationTypeColumn,
                    this.holderColumn,
                    this.licenceNumberColumn,
                    this.processingStatusColumn,
                    this.dueDateColumn,
                    this.assignedToNameColumn,
                    this.actionColumn,
                ];
            }
            return columns;
        },
        compliancesOptions: function () {
            let vm = this;
            let buttons = [];
            buttons = [
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
                ajax: {
                    url: vm.ajaxUrl,
                    dataSrc: 'data',

                    // adding extra GET params for Custom filtering
                    data: function (d) {
                        // Add filters selected
                        d.filter_approval_type = vm.filterApprovalType;
                        d.filter_compliance_status = vm.filterComplianceStatus;
                        d.filter_due_date_from = vm.filterComplianceDueDateFrom;
                        d.filter_due_date_to = vm.filterComplianceDueDateTo;
                    },
                },
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,
                columns: vm.applicableColumns,
                processing: true,
                order: [[0, 'desc']],
            };
        },
    },
    watch: {
        filterApprovalType: function () {
            this.$refs.compliances_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterApprovalTypeCacheName,
                this.filterApprovalType
            );
        },
        filterComplianceStatus: function () {
            this.$refs.compliances_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterComplianceStatusCacheName,
                this.filterComplianceStatus
            );
        },
        filterComplianceDueDateFrom: function () {
            this.$refs.compliances_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterComplianceDueDateFromCacheName,
                this.filterComplianceDueDateFrom
            );
        },
        filterComplianceDueDateTo: function () {
            this.$refs.compliances_datatable.vmDataTable.draw(); // This calls ajax() backend call.  This line is enough to search?  Do we need following lines...?
            sessionStorage.setItem(
                this.filterComplianceDueDateToCacheName,
                this.filterComplianceDueDateTo
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
        $.fn.pulse = function (options_param) {
            var options = $.extend(
                {
                    times: 3,
                    duration: 1000,
                },
                options_param
            );

            var period = function (callback) {
                $(this).animate({ opacity: 0 }, options.duration, function () {
                    $(this).animate({ opacity: 1 }, options.duration, callback);
                });
            };
            return this.each(function () {
                var i = +options.times,
                    self = this,
                    repeat = function () {
                        --i && period.call(self, repeat);
                    };
                period.call(this, repeat);
            });
        };
        $('.pulsate').each(function (element) {
            $(element).pulse({ times: 6, duration: 1000 });
        });
    },
    methods: {
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(
                this.filterApplied
            );
        },
        expandCollapseFilters: function () {
            this.filters_expanded = !this.filters_expanded;
        },
        getStatusHtml: function (status) {
            let class_name = '';
            let icon = '';

            if ('Future' == status) {
                class_name = 'info';
                icon = 'calendar-plus';
            }
            if ('Due' == status) {
                class_name = 'warning';
                icon = 'clock';
            }
            if ('Overdue' == status) {
                class_name = 'danger';
                icon = 'exclamation-circle';
            }
            if ('With Assessor' == status) {
                class_name = 'primary';
                icon = 'clipboard';
            }
            if ('With Referral' == status) {
                class_name = 'secondary';
                icon = 'users';
            }
            if ('Under Review' == status) {
                class_name = 'secondary';
                icon = 'clipboard';
            }
            if ('Approved' == status) {
                class_name = 'success';
                icon = 'check';
            }
            return `<span class="badge bg-${class_name} py-2"><i class="fa fa-${icon}" aria-hidden="true"></i> ${status}</span>`;
        },
        fetchFilterLists: function () {
            let vm = this;

            // Types
            fetch(api_endpoints.approval_types_dict)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.approval_types = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });

            // Statuses
            fetch(api_endpoints.compliance_statuses_dict)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.compliance_statuses = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
        },
    },
};
</script>
