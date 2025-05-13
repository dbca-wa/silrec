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
                            v-model="filterApprovalType"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="ap in approvalTypes"
                                :key="ap.id"
                                :value="ap.id"
                            >
                                {{ ap.name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Status</label>
                        <select
                            v-model="filterApprovalStatus"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="status in approval_statuses"
                                :key="status.id"
                                :value="status.code"
                            >
                                {{ status.description }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Expiry Date From</label>
                        <div
                            ref="approvalDateFromPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterApprovalExpiryDateFrom"
                                type="date"
                                class="form-control"
                            />
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Expiry Date To</label>
                        <div
                            ref="approvalDateToPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterApprovalExpiryDateTo"
                                type="date"
                                class="form-control"
                            />
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mb-2 p-2">
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="filter-region">Organisation</label>
                        <select
                            id="filter-region"
                            v-model="filterApprovalOrganisation"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="organisation in organisations"
                                :key="organisation.id"
                                :value="organisation.id"
                            >
                                {{ organisation.ledger_organisation_name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="filter-region">Region</label>
                        <select
                            id="filter-region"
                            v-model="filterApprovalRegion"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="region in regions"
                                :key="region.id"
                                :value="region.id"
                            >
                                {{ region.name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="filter-district">District</label>
                        <select
                            id=" filter-district"
                            v-model="filterApprovalDistrict"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="district in districts"
                                :key="district.id"
                                :value="district.id"
                            >
                                {{ district.name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="filter-group">Group</label>
                        <select
                            id="filter-group"
                            v-model="filterApprovalGroup"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="group in groups"
                                :key="group.id"
                                :value="group.id"
                            >
                                {{ group.name }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="approvals_datatable"
                    :dt-options="datatable_options"
                    :dt-headers="datatable_headers"
                />
            </div>
        </div>
        <ApprovalCancellation
            ref="approval_cancellation"
            :approval_id="selectedApprovalId"
            :approval_lodgement_number="selectedApprovalLodgementNumber"
            @refresh-from-response="refreshFromResponseApprovalModify"
        >
        </ApprovalCancellation>
        <ApprovalSurrender
            ref="approval_surrender"
            :approval_id="selectedApprovalId"
            :approval_lodgement_number="selectedApprovalLodgementNumber"
            @refresh-from-response="refreshFromResponseApprovalModify"
        >
        </ApprovalSurrender>
        <ApprovalSuspension
            ref="approval_suspension"
            :approval_id="selectedApprovalId"
            :approval_lodgement_number="selectedApprovalLodgementNumber"
            @refresh-from-response="refreshFromResponseApprovalModify"
        >
        </ApprovalSuspension>
        <div v-if="approvalHistoryId">
            <ApprovalHistory
                ref="approval_history"
                :key="approvalHistoryId"
                :approval-id="approvalHistoryId"
                :approval-lodgement-number="selectedApprovalLodgementNumber"
            />
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import ApprovalCancellation from '../internal/approvals/approval_cancellation.vue';
import ApprovalSuspension from '../internal/approvals/approval_suspension.vue';
import ApprovalSurrender from '../internal/approvals/approval_surrender.vue';
import ApprovalHistory from '../internal/approvals/approval_history.vue';
import { api_endpoints, constants, helpers, utils } from '@/utils/hooks';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import { v4 as uuid } from 'uuid';
import Swal from 'sweetalert2';

export default {
    name: 'TableApprovals',
    components: {
        datatable,
        ApprovalCancellation,
        ApprovalSuspension,
        ApprovalSurrender,
        ApprovalHistory,
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
        targetComplianceId: {
            type: Number,
            required: false,
            default: 0,
        },
    },
    data() {
        return {
            datatable_id: 'approvals-datatable-' + uuid(),
            selectedWaitingListAllocationId: null,
            approvalHistoryId: null,
            uuid: 0,
            mooringBayId: null,
            statusValues: [],
            approvalTypes: [],
            holderList: [],
            organisations: [],
            regions: [],
            districts: [],
            groups: [],
            profile: {},
            selectedApprovalId: null,
            selectedApprovalLodgementNumber: null,

            // selected values for filtering
            filterApprovalType: sessionStorage.getItem('filterApprovalType')
                ? sessionStorage.getItem('filterApprovalType')
                : 'all',
            filterApprovalStatus: sessionStorage.getItem('filterApprovalStatus')
                ? sessionStorage.getItem('filterApprovalStatus')
                : 'all',
            filterApprovalExpiryDateFrom: sessionStorage.getItem(
                'filterApprovalExpiryDateFrom'
            )
                ? sessionStorage.getItem('filterApprovalExpiryDateFrom')
                : '',
            filterApprovalExpiryDateTo: sessionStorage.getItem(
                'filterApprovalExpiryDateTo'
            )
                ? sessionStorage.getItem('filterApprovalExpiryDateTo')
                : '',

            filterApprovalOrganisation: sessionStorage.getItem(
                'filterApprovalOrganisation'
            )
                ? sessionStorage.getItem('filterApprovalOrganisation')
                : 'all',
            filterApprovalRegion: sessionStorage.getItem('filterApprovalRegion')
                ? sessionStorage.getItem('filterApprovalRegion')
                : 'all',
            filterApprovalDistrict: sessionStorage.getItem(
                'filterApprovalDistrict'
            )
                ? sessionStorage.getItem('filterApprovalDistrict')
                : 'all',
            filterApprovalGroup: sessionStorage.getItem('filterApprovalGroup')
                ? sessionStorage.getItem('filterApprovalGroup')
                : 'all',

            // filtering options
            approval_types: [],
            approval_statuses: [],

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
        filterApplied: function () {
            let filter_applied = true;
            if (
                this.filterApprovalType === 'all' &&
                this.filterApprovalStatus.toLowerCase() === 'all' &&
                this.filterApprovalExpiryDateFrom.toLowerCase() === '' &&
                this.filterApprovalExpiryDateTo.toLowerCase() === '' &&
                this.filterApprovalOrganisation === 'all' &&
                this.filterApprovalRegion === 'all' &&
                this.filterApprovalDistrict === 'all' &&
                this.filterApprovalGroup === 'all'
            ) {
                filter_applied = false;
            }
            return filter_applied;
        },
        csrf_token: function () {
            return helpers.getCookie('csrftoken');
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
        // Datatable settings
        datatable_headers: function () {
            if (this.is_organisation_view) {
                return [
                    'Id',
                    'Number',
                    'Type',
                    'Status',
                    'Document',
                    'Expiry Date',
                    'Action',
                ];
            } else if (this.is_external) {
                return [
                    'Id',
                    'Number',
                    'Type',
                    'Site',
                    'Holder',
                    'Status',
                    'Expiry Date',
                    'Document',
                    'Original Lease/License Number',
                    'Site Name',
                    'Groups',
                    'Categories',
                    'Action',
                ];
            } else if (this.is_internal) {
                return [
                    'Id',
                    'Number',
                    'Type',
                    'Holder',
                    'Proposal',
                    'Status',
                    'Expiry Date',
                    'Document',
                    'Original Lease/License Number',
                    'Site Name',
                    'Groups',
                    'Categories',
                    'Action',
                ];
            } else {
                console.error('Unknown datatable level: ' + this.level);
                return [];
            }
        },
        columnId: function () {
            return {
                data: 'id',
                orderable: false,
                searchable: false,
                visible: false,
                render: function (row, type, full) {
                    return full.id;
                },
            };
        },
        columnLodgementNumber: function () {
            return {
                data: 'lodgement_number',
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
        columnType: function () {
            return {
                data: 'approval_type',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.approval_type;
                },
                name: 'approval_type__name',
            };
        },
        columnSite: function () {
            return {
                data: 'site_name',
                orderable: true,
                searchable: true,
                visible: true,
                name: 'current_proposal__site_name__name',
                render: function (row, type, full) {
                    return full.site_name;
                },
            };
        },
        columnGroups: function () {
            return {
                data: 'groups_names_list',
                orderable: true,
                searchable: true,
                visible: true,
                name: 'current_proposal__groups__group__name',
                render: function (row, type, full) {
                    let html = '';
                    if (full.groups_names_list) {
                        for (
                            let i = 0;
                            i < full.groups_names_list.length;
                            i++
                        ) {
                            html += `<span class="badge bg-primary">${full.groups_names_list[i]}</span>&nbsp;`;
                        }
                    }
                    return html;
                },
            };
        },
        columnCategories: function () {
            return {
                data: 'categories_list',
                orderable: true,
                searchable: true,
                visible: true,
                name: 'current_proposal__categories__category__name',
                render: function (row, type, full) {
                    let html = '';
                    if (full.categories_list) {
                        for (let i = 0; i < full.categories_list.length; i++) {
                            html += `<span class="badge bg-primary">${full.categories_list[i]}</span>&nbsp;`;
                        }
                    }
                    return html;
                },
            };
        },
        columnHolder: function () {
            return {
                data: 'holder',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.holder;
                },
                name: 'current_proposal__proposalapplicant__first_name, current_proposal__proposalapplicant__last_name, current_proposal__org_applicant__ledger_organisation_name',
            };
        },
        columnLinkedApplications: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    var text = full.linked_applications.join(', ');
                    var ellipsis = '...',
                        truncated = _.truncate(text, {
                            length: 25,
                            omission: ellipsis,
                            separator: ' ',
                        }),
                        isTruncated = _.endsWith(truncated, ellipsis),
                        result =
                            '<span>' +
                            (isTruncated
                                ? truncated.slice(0, -ellipsis.length)
                                : truncated) +
                            '</span>',
                        popTemplate = _.template(
                            '<a tabindex="0" ' +
                                'data-bs-title="Applications for ' +
                                full.lodgement_number +
                                '" ' +
                                'data-bs-template=\'<div class="popover" role="tooltip"><div class="arrow"></div>' +
                                '<div class="row ps-0">' +
                                '<div class="col-md-12 text-nowrap">' +
                                '<h3 class="popover-header"></h3>' +
                                '</div>' +
                                '</div>' +
                                '<div type="button" id="close" class="popover-close">' +
                                '<i class="fa fa-window-close" aria-hidden="true"></i>' +
                                '</div>' +
                                '<div class="popover-body"></div>\' ' +
                                'role="button" ' +
                                'data-bs-toggle="popover" ' +
                                'data-bs-trigger="hover click" ' +
                                'data-bs-placement="top" ' +
                                'data-bs-content="<%= text %>" ' +
                                `><b>${ellipsis}</b></a>`
                        );
                    if (isTruncated) {
                        result += popTemplate({
                            text: text,
                        });
                    }

                    return result;
                },
            };
        },
        columnStatus: function () {
            return {
                data: 'status',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.status;
                },
            };
        },
        columnExpiryDate: function () {
            return {
                data: 'expiry_date',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (full.expiry_date) {
                        return moment(full.expiry_date).format('DD/MM/YYYY');
                    }
                    return '';
                },
            };
        },
        columnDocument: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    let _file_name = 'Approval.PDF';
                    if (full.licence_document) {
                        return `<a href="${full.licence_document}" target="_blank">
                            <i class="fa fa-file-pdf" style='color: red'></i>
                            ${_file_name}</a>`;
                    } else {
                        // Should not happen that there is no license document, but better not show one being
                        // there when that is not the case
                        console.warn(
                            `No license document for license ${full.lodgement_number}`
                        );
                        return '';
                    }
                },
            };
        },
        columnOriginalLeaseLicenseNumber: function () {
            return {
                data: 'original_leaselicence_number',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (full.original_leaselicence_number) {
                        return full.original_leaselicence_number;
                    }
                    return 'N/A';
                },
            };
        },
        columnAction: function () {
            let vm = this;
            return {
                // 10. Action
                data: 'id',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let links = '';

                    if (vm.is_external) {
                        if (full.can_reissue) {
                            links += `<a href='/external/approval/${full.id}'>View</a><br/>`;
                            if (full.can_action || vm.debug) {
                                if (full.can_amend || vm.debug) {
                                    links += `<a href='#${full.id}' data-amend-approval='${full.current_proposal.id}'>Amend</a><br/>`;
                                } else if (
                                    full.has_draft_amendment &&
                                    full.active_amendment.processing_status ==
                                        constants.PROPOSAL_STATUS.DRAFT.ID
                                ) {
                                    links += `<a href='/external/proposal/${full.active_amendment.id}'>Continue Amendment Application</a><br/>`;
                                } else if (full.has_pending_renewal) {
                                    if (!full.has_draft_renewal) {
                                        links += `<a href='#${full.id}' data-renew-approval='${full.current_proposal.id}'>Renew</a><br/>`;
                                    } else if (
                                        full.active_amendment
                                            .processing_status ==
                                        constants.PROPOSAL_STATUS.DRAFT.ID
                                    ) {
                                        links += `<a href='/external/proposal/${full.active_renewal.id}'>Continue Renewal Application</a><br/>`;
                                    }
                                }
                                links += `<a href='#${full.id}' data-surrender-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}">Surrender</a><br/>`;
                            }
                        }
                        if (!full.has_pending_transfer) {
                            let transfer_text = 'Transfer';
                            if (full.has_draft_transfer) {
                                transfer_text = 'Continue Transfer Application';
                            }
                            links += `<a href='#${full.id}' data-transfer-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}" data-can-initiate-transfer="${full.can_initiate_transfer}" data-has-active-transfer="${full.has_draft_transfer}">${transfer_text}</a><br/>`;
                        }
                    } else if (!vm.is_external) {
                        links += `<a href='/internal/approval/${full.id}'>View</a><br/>`;
                        links += `<a href='#${full.id}' data-history-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}">History</a><br/>`;
                        if (
                            full.is_approver &&
                            full.can_reissue &&
                            full.current_proposal
                        ) {
                            links += `<a href='#${full.id}' data-reissue-approval='${full.current_proposal.id}'>Reissue</a><br/>`;
                        }
                        if (full.is_assessor) {
                            if (full.can_reissue && full.can_action) {
                                links += `<a href='#${full.id}' data-cancel-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}">Cancel</a><br/>`;
                                links += `<a href='#${full.id}' data-surrender-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}">Surrender</a><br/>`;
                            }
                            if (full.status == 'Current' && full.can_action) {
                                links += `<a href='#${full.id}' data-suspend-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}">Suspend</a><br/>`;
                            }
                            if (full.can_reinstate) {
                                links += `<a href='#${full.id}' data-reinstate-approval='${full.id}'>Reinstate</a><br/>`;
                            }
                            if (
                                constants.APPROVAL_STATUS
                                    .CURRENT_PENDING_RENEWAL_REVIEW.TEXT ==
                                full.status
                            ) {
                                links += `<a href='#${full.id}' data-review-renewal-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}">Review Renewal</a><br/>`;
                            }
                        }
                        if (full.is_finance_officer) {
                            if (
                                [
                                    constants.APPROVAL_STATUS.CURRENT.TEXT,
                                    constants.APPROVAL_STATUS
                                        .CURRENT_PENDING_RENEWAL.TEXT,
                                    constants.APPROVAL_STATUS
                                        .CURRENT_PENDING_RENEWAL_REVIEW.TEXT,
                                ].includes(full.status) &&
                                constants.PROPOSAL_STATUS.APPROVED.ID ==
                                    full.current_proposal_processing_status
                            ) {
                                links += `<a href='#${full.id}' data-review-invoice-detail-approval='${full.id}' data-approval-lodgement-number="${full.lodgement_number}">Review Invoicing Details</a><br/>`;
                            }
                            if (
                                full.status ==
                                constants.APPROVAL_STATUS
                                    .CURRENT_EDITING_INVOICING.TEXT
                            ) {
                                links += `<a href='/internal/approval/${full.id}#edit-invoicing'>Continue Editing Invoicing</a><br/>`;
                            }
                        }
                        if (
                            full.renewal_document &&
                            full.renewal_notification_sent_to_holder
                        ) {
                            links += `<a href='${full.renewal_document}' target='_blank'>Renewal Notice</a><br/>`;
                        }
                    }

                    return links;
                },
            };
        },
        datatable_options: function () {
            let vm = this;
            let selectedColumns = [];
            if (this.is_organisation_view) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    vm.columnType,
                    vm.columnStatus,
                    vm.columnDocument,
                    vm.columnExpiryDate,
                    vm.columnAction,
                ];
            } else if (this.is_external) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    vm.columnType,
                    vm.columnSite,
                    vm.columnHolder,
                    vm.columnStatus,
                    vm.columnExpiryDate,
                    vm.columnDocument,
                    vm.columnOriginalLeaseLicenseNumber,
                    vm.columnSite,
                    vm.columnGroups,
                    vm.columnCategories,
                    vm.columnAction,
                ];
            } else if (vm.is_internal) {
                selectedColumns = [
                    vm.columnId,
                    vm.columnLodgementNumber,
                    vm.columnType,
                    vm.columnHolder,
                    vm.columnLinkedApplications,
                    vm.columnStatus,
                    vm.columnExpiryDate,
                    vm.columnDocument,
                    vm.columnOriginalLeaseLicenseNumber,
                    vm.columnSite,
                    vm.columnGroups,
                    vm.columnCategories,
                    vm.columnAction,
                ];
            }
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
                rowCallback: function (row, proposal) {
                    let row_jq = $(row);
                    row_jq.attr('id', 'proposal_id_' + proposal.id);
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
                    url:
                        api_endpoints.approvals_paginated_list +
                        '?format=datatables&target_email_user_id=' +
                        vm.targetEmailUserId +
                        '&target_organisation_id=' +
                        vm.targetOrganisationId +
                        '&target_compliance_id=' +
                        vm.targetComplianceId,
                    //"url": api_endpoints.approvals,
                    dataSrc: 'data',

                    // adding extra GET params for Custom filtering
                    data: function (d) {
                        d.filter_approval_type = vm.filterApprovalType;
                        d.filter_approval_status = vm.filterApprovalStatus;
                        d.filter_approval_expiry_date_from =
                            vm.filterApprovalExpiryDateFrom;
                        d.filter_approval_expiry_date_to =
                            vm.filterApprovalExpiryDateTo;

                        d.filter_approval_organisation =
                            vm.filterApprovalOrganisation;
                        d.filter_approval_region = vm.filterApprovalRegion;
                        d.filter_approval_district = vm.filterApprovalDistrict;
                        d.filter_approval_group = vm.filterApprovalGroup;

                        d.level = vm.level;

                        // Add search terms to be concatenated on the queryset
                        d.search_terms =
                            'current_proposal__proposalapplicant__first_name, current_proposal__proposalapplicant__last_name';
                    },
                },
                //dom: 'frt', //'lBfrtip',
                //dom: 'lBfrtip',
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,
                columns: selectedColumns,
                processing: true,
                order: [[1, 'desc']],
            };
        },
    },
    watch: {
        filterApprovalType: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalType',
                this.filterApprovalType
            );
        },
        filterApprovalStatus: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalStatus',
                this.filterApprovalStatus
            );
        },
        filterApprovalExpiryDateFrom: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalExpiryDateFrom',
                this.filterApprovalExpiryDateFrom
            );
        },
        filterApprovalExpiryDateTo: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalExpiryDateTo',
                this.filterApprovalExpiryDateTo
            );
        },
        filterApprovalOrganisation: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalOrganisation',
                this.filterApprovalOrganisation
            );
        },
        filterApprovalRegion: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalRegion',
                this.filterApprovalRegion
            );
        },
        filterApprovalDistrict: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalDistrict',
                this.filterApprovalDistrict
            );
        },
        filterApprovalGroup: function () {
            this.$refs.approvals_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterApprovalGroup',
                this.filterApprovalGroup
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
    created: async function () {
        await this.fetchFilterLists();
        await this.fetchProfile();
    },
    mounted: function () {
        this.$nextTick(() => {
            this.addEventListeners();
        });
    },
    methods: {
        number_of_columns: function () {
            let num_cols = this.$refs.approvals_datatable.vmDataTable
                .columns(':visible')
                .nodes().length;
            return num_cols;
        },
        adjust_table_width: function () {
            this.$refs.approvals_datatable.vmDataTable.columns.adjust();
            this.$refs.approvals_datatable.vmDataTable.responsive.recalc();
        },
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(
                this.filterApplied
            );
        },
        fetchProfile: function () {
            let vm = this;
            fetch(api_endpoints.profile).then(
                (response) => {
                    vm.profile = response.body;
                },
                (error) => {
                    console.error(error);
                }
            );
        },
        refreshFromResponseApprovalModify: function () {
            this.$refs.approvals_datatable.vmDataTable.ajax.reload();
        },
        addEventListeners: function () {
            let vm = this;

            //Internal Action shortcut listeners
            let table = vm.$refs.approvals_datatable.vmDataTable;
            table.on('processing.dt', function () {});
            table
                .on('click', 'a[data-offer]', async function (e) {
                    var id = $(this).attr('data-offer');
                    e.preventDefault();
                    vm.mooringBayId = parseInt(
                        $(this).attr('data-mooring-bay')
                    );
                    await vm.offerMooringLicence(id);
                })
                .on('responsive-display.dt', function () {
                    var tablePopover = $(this).find('[data-toggle="popover"]');
                    if (tablePopover.length > 0) {
                        tablePopover.popover();
                        // the next line prevents from scrolling up to the top after clicking on the popover.
                        $(tablePopover).on('click', function (e) {
                            e.preventDefault();
                            return true;
                        });
                    }
                })
                .on('draw.dt', function () {
                    var popoverTriggerList = [].slice.call(
                        document.querySelectorAll('a[data-bs-toggle="popover"]')
                    );
                    popoverTriggerList.map(function (popoverTriggerEl) {
                        let popover = new bootstrap.Popover(popoverTriggerEl);
                        // Listeners to hide popovers on 'x'-click
                        vm.$refs.approvals_datatable.vmDataTable.on(
                            'click',
                            'a[data-bs-toggle="popover"]',
                            function (e) {
                                e.preventDefault();
                                let attributes = e.currentTarget.attributes;
                                let popoverId;
                                if (attributes && attributes.length > 0) {
                                    popoverId = attributes['10'].value;
                                }

                                if (
                                    popover.tip &&
                                    popover.tip.id == popoverId
                                ) {
                                    // Ideally the listener would only be shown on popover show, but that does work okay for now
                                    $(`#${popoverId}`)
                                        .find('.popover-close')
                                        .off('click')
                                        .on('click', () => popover.hide());
                                }
                            }
                        );

                        return popover;
                    });
                });
            // Internal Reissue listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-reissue-approval]',
                function (e) {
                    var id = $(this).attr('data-reissue-approval');
                    e.preventDefault();
                    vm.reissueApproval(id);
                }
            );

            //Internal Cancel listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-cancel-approval]',
                function (e) {
                    var id = $(this).attr('data-cancel-approval');
                    var lodgement_number = $(this).attr(
                        'data-approval-lodgement-number'
                    );
                    e.preventDefault();
                    vm.cancelApproval(id, lodgement_number);
                }
            );

            //Internal Suspend listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-suspend-approval]',
                function (e) {
                    var id = $(this).attr('data-suspend-approval');
                    var lodgement_number = $(this).attr(
                        'data-approval-lodgement-number'
                    );
                    e.preventDefault();
                    vm.suspendApproval(id, lodgement_number);
                }
            );

            // Internal Reinstate listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-reinstate-approval]',
                function (e) {
                    var id = $(this).attr('data-reinstate-approval');
                    e.preventDefault();
                    vm.reinstateApproval(id);
                }
            );

            //Internal/ External Surrender listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-surrender-approval]',
                function (e) {
                    var id = $(this).attr('data-surrender-approval');
                    var lodgement_number = $(this).attr(
                        'data-approval-lodgement-number'
                    );
                    e.preventDefault();
                    vm.surrenderApproval(id, lodgement_number);
                }
            );

            // External renewal listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-renew-approval]',
                function (e) {
                    var id = $(this).attr('data-renew-approval');
                    e.preventDefault();
                    vm.renewApproval(id);
                }
            );

            // External amend listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-amend-approval]',
                function (e) {
                    var id = $(this).attr('data-amend-approval');
                    e.preventDefault();
                    vm.amendApproval(id);
                }
            );

            // External transfer listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-transfer-approval]',
                function (e) {
                    var id = $(this).attr('data-transfer-approval');
                    var lodgement_number = $(this).attr(
                        'data-approval-lodgement-number'
                    );
                    var can_initiate_transfer = $(this).attr(
                        'data-can-initiate-transfer'
                    );
                    var has_draft_transfer = $(this).attr(
                        'data-has-active-transfer'
                    );
                    if (has_draft_transfer == 'true') {
                        vm.$router.push({
                            name: 'external-approval-transfer',
                            params: { approval_id: id },
                        });
                        return;
                    }
                    e.preventDefault();
                    if (can_initiate_transfer != 'true') {
                        swal.fire({
                            title: `Unable to Transfer Lease/License`,
                            text: `Lease/License ${lodgement_number} can not be transferred as it has outstanding compliances or invoices. \
                    You must submit any due compliances and pay any due invoices before applying to transfer.`,
                            icon: 'warning',
                            showCancelButton: true,
                            showConfirmButton: false,
                            cancelButtonText: 'Dismiss',
                        });
                        return;
                    }
                    vm.transferApproval(id, lodgement_number);
                }
            );
            // Internal history listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-history-approval]',
                function (e) {
                    var id = $(this).attr('data-history-approval');
                    var lodgement_number = $(this).attr(
                        'data-approval-lodgement-number'
                    );
                    e.preventDefault();
                    vm.approvalHistory(id, lodgement_number);
                }
            );

            // Internal review invoice details listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-review-invoice-detail-approval]',
                function (e) {
                    var id = $(this).attr(
                        'data-review-invoice-detail-approval'
                    );
                    var lodgement_number = $(this).attr(
                        'data-approval-lodgement-number'
                    );
                    e.preventDefault();
                    vm.approvalReviewInvoiceDetails(id, lodgement_number);
                }
            );

            // Internal review renewal listener
            vm.$refs.approvals_datatable.vmDataTable.on(
                'click',
                'a[data-review-renewal-approval]',
                function (e) {
                    var id = $(this).attr('data-review-renewal-approval');
                    var lodgement_number = $(this).attr(
                        'data-approval-lodgement-number'
                    );
                    e.preventDefault();
                    vm.approvalReviewRenewal(id, lodgement_number);
                }
            );
        },
        fetchFilterLists: async function () {
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
                    vm.approvalTypes = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
            // Statuses
            fetch(api_endpoints.approval_statuses_dict)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.approval_statuses = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
            // Organisations
            fetch(api_endpoints.organisations + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.organisations = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
            // Regions
            fetch(api_endpoints.regions + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.regions = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
            // Districts
            fetch(api_endpoints.districts + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.districts = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
            // Category
            fetch(api_endpoints.groups + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.groups = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
        },
        reissueApproval: async function (proposal_id) {
            let vm = this;
            await swal
                .fire({
                    title: 'Reissue Approval',
                    text: 'Are you sure you want to reissue this approval?',
                    icon: 'question',
                    showCancelButton: true,
                    reverseButtons: true,
                    confirmButtonText: 'Reissue Approval',
                    confirmButtonColor: '#226fbb',
                })
                .then(async (result) => {
                    if (result.isConfirmed) {
                        const requestOptions = {
                            method: 'POST',
                        };
                        let url = helpers.add_endpoint_json(
                            api_endpoints.proposal,
                            proposal_id + '/reissue_approval'
                        );
                        utils
                            .fetchUrl(url, requestOptions)
                            .then((data) => {
                                vm.$router.push({
                                    name: 'internal-proposal',
                                    params: { proposal_id: data.id },
                                });
                            })
                            .catch((error) => {
                                Swal.fire({
                                    title: 'Reissue Approval',
                                    text: error,
                                    icon: 'error',
                                });
                            });
                    }
                });
        },

        reinstateApproval: async function (approval_id) {
            let vm = this;
            // eslint-disable-next-line no-unused-vars
            let status = 'with_approver';
            Swal.fire({
                title: 'Reinstate Approval',
                text: 'Are you sure you want to reinstate this approval?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Reinstate approval',
                reverseButtons: true,
            }).then(async (result) => {
                if (result.isConfirmed) {
                    let url = helpers.add_endpoint_json(
                        api_endpoints.approvals,
                        approval_id + '/approval_reinstate'
                    );
                    let requestOptions = {
                        method: 'POST',
                    };
                    utils
                        .fetchUrl(url, requestOptions)
                        .then(() => {
                            Swal.fire(
                                'Reinstate',
                                'Your approval has been reinstated',
                                'success'
                            );
                            vm.$refs.approvals_datatable.vmDataTable.ajax.reload();
                        })
                        .catch((error) => {
                            Swal.fire('Reinstate Approval', error, 'error');
                        });
                }
            });
        },
        cancelApproval: function (approval_id, approval_lodgement_number) {
            this.selectedApprovalId = parseInt(approval_id);
            this.selectedApprovalLodgementNumber = approval_lodgement_number;
            this.$refs.approval_cancellation.isModalOpen = true;
            this.$nextTick(() => {
                $(
                    `#approvalCancellation${approval_id} textarea.cancellation-details`
                ).focus();
            });
        },
        suspendApproval: function (approval_id, approval_lodgement_number) {
            this.selectedApprovalId = parseInt(approval_id);
            this.selectedApprovalLodgementNumber = approval_lodgement_number;
            this.$refs.approval_suspension.isModalOpen = true;
            this.$nextTick(() => {
                $(`#approvalSuspension${approval_id} input#to_date`).focus();
            });
        },
        surrenderApproval: function (approval_id, approval_lodgement_number) {
            this.selectedApprovalId = parseInt(approval_id);
            this.selectedApprovalLodgementNumber = approval_lodgement_number;
            this.$refs.approval_surrender.isModalOpen = true;
            this.$nextTick(() => {
                $(
                    `#approvalSurrender${approval_id} textarea.surrender-details`
                ).focus();
            });
        },
        approvalHistory: function (id, approvalLodgementNumber) {
            this.approvalHistoryId = parseInt(id);
            this.selectedApprovalLodgementNumber = approvalLodgementNumber;
            this.uuid++;
            this.$nextTick(() => {
                this.$refs.approval_history.isModalOpen = true;
            });
        },
        approvalReviewInvoiceDetails: function (
            approval_id,
            // eslint-disable-next-line no-unused-vars
            approval_lodgement_number
        ) {
            let vm = this;
            Swal.fire({
                title: 'Approval Review Invoice Details',
                text: 'Are you sure you want to review the invoice details for this approval?',
                icon: 'question',
                showCancelButton: true,
                reverseButtons: true,
                confirmButtonText: 'Review Invoice Details',
                confirmButtonColor: '#226fbb',
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    let requestOptions = {
                        method: 'PATCH',
                    };
                    fetch(
                        helpers.add_endpoint_join(
                            api_endpoints.approvals,
                            approval_id + '/review_invoice_details/'
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
                                params: { approval_id: approval_id },
                            });
                        },
                        (error) => {
                            console.error(error);
                        }
                    );
                }
            });
        },
        approvalReviewRenewal: function (approval_id) {
            this.$router.push({
                name: 'internal-approval-detail',
                params: { approval_id: approval_id },
            });
        },
        renewApproval: async function (proposal_id) {
            let vm = this;
            // eslint-disable-next-line no-unused-vars
            let status = 'with_approver';
            Swal.fire({
                title: 'Renew Approval',
                text: 'Are you sure you want to renew this approval?',
                icon: 'question',
                showCancelButton: true,
                reverseButtons: true,
                confirmButtonText: 'Renew approval',
                confirmButtonColor: '#226fbb',
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    const requestOptions = {
                        method: 'POST',
                    };
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposal,
                            proposal_id + '/renew_approval'
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
                                return Promise.reject(error);
                            }
                            vm.$router.push({
                                name: 'draft_proposal',
                                params: { proposal_id: data.id },
                            });
                        },
                        (error) => {
                            console.error(error);
                            Swal.fire({
                                title: 'Renew Approval',
                                text: error.body,
                                icon: 'error',
                            });
                        }
                    );
                }
            });
        },
        amendApproval: async function (proposal_id) {
            let vm = this;
            // eslint-disable-next-line no-unused-vars
            let status = 'with_approver';
            Swal.fire({
                title: 'Amend Approval',
                text: 'Are you sure you want to amend this approval?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Amend approval',
                reverseButtons: true,
            }).then(async (result) => {
                if (result.isConfirmed) {
                    let url =
                        helpers.add_endpoint_json(
                            api_endpoints.proposal,
                            proposal_id + '/amend_approval'
                        ) +
                        '?debug=' +
                        vm.debug +
                        '&type=amend';
                    let requestOptions = {
                        method: 'GET',
                    };
                    utils
                        .fetchUrl(url, requestOptions)
                        .then((response) => {
                            vm.$router.push({
                                name: 'draft_proposal',
                                params: { proposal_id: response.id },
                            });
                        })
                        .catch((error) => {
                            Swal.fire({
                                title: 'Amend Approval',
                                text: error,
                                icon: 'error',
                            });
                        });
                }
            });
        },
        transferApproval: async function (approval_id, lodgement_number) {
            swal.fire({
                title: `Transfer Lease/License`,
                text: `Are you sure you want to transfer Lease/License ${lodgement_number}?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Apply to Transfer',
                reverseButtons: true,
            }).then(async (result) => {
                if (result.isConfirmed) {
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.approvals,
                            approval_id + '/transfer'
                        ),
                        {
                            method: 'POST',
                        }
                    ).then(
                        (response) => {
                            if (response.ok) {
                                this.$router.push({
                                    name: 'external-approval-transfer',
                                    params: { approval_id: approval_id },
                                });
                            }
                        },
                        (error) => {
                            console.error(error);
                        }
                    );
                }
            });
        },
    },
};
</script>

<style>
.popover-close {
    position: absolute;
    top: -0.6rem;
    right: 0.25rem;
    font-size: 2.5em;
}
</style>
