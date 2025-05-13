<template>
    <div>
        <CollapsibleFilters
            ref="collapsible_filters"
            component_title="Filters"
            class="mb-2"
            @created="collapsible_component_mounted"
        >
            <div class="row mt-1 p-2">
                <div v-if="!approvalId" class="col-md-3">
                    <div class="form-group">
                        <label for="">Organisation</label>
                        <select
                            v-model="filterInvoiceOrganisation"
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
                        <label for="">Payment Status</label>
                        <select
                            v-model="filterInvoiceStatus"
                            class="form-select"
                        >
                            <option value="all">All</option>
                            <option
                                v-for="status in invoice_statuses"
                                :key="status.id"
                                :value="status.id"
                            >
                                {{ status.name }}
                            </option>
                            <option value="overdue">Overdue</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Invoice Due Date From</label>
                        <div
                            ref="invoiceDateFromPicker"
                            class="input-group date"
                        >
                            <input
                                v-model="filterInvoiceDueDateFrom"
                                type="date"
                                class="form-control"
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
                        <label for="">Invoice Due Date To</label>
                        <div ref="invoiceDateToPicker" class="input-group date">
                            <input
                                v-model="filterInvoiceDueDateTo"
                                type="date"
                                class="form-control"
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

        <div v-if="level == 'internal'" class="row mb-2">
            <div class="col">
                <button
                    class="btn btn-primary float-end"
                    @click="generateAdHocInvoiceRecord"
                >
                    Generate Ad Hoc Invoice Record
                </button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="invoices_datatable"
                    :dt-options="invoicesOptions"
                    :dt-headers="invoicesHeaders"
                />
            </div>
        </div>
        <GenerateAdHocInvoiceRecord
            v-if="level == 'internal'"
            ref="invoice_raise_ad_hoc"
            @ad-hoc-invoice-record-generated="adHocInvoiceRecordGenerated"
        >
        </GenerateAdHocInvoiceRecord>
        <InvoiceViewTransactions
            ref="invoice_view_transactions"
            :invoice_id="selectedInvoiceId"
            :invoice_lodgement_number="selectedInvoiceLodgementNumber"
            :invoice_amount="selectedInvoiceAmount"
        >
        </InvoiceViewTransactions>
        <UploadOracleInvoice
            v-if="level == 'internal'"
            ref="invoice_upload_oracle_invoice"
            :invoice-id="selectedInvoiceId"
            :invoice-lodgement-number="selectedInvoiceLodgementNumber"
            :selected-oracle-invoice-number="selectedInvoiceOracleInvoiceNumber"
            :selected-oracle-code="selectedInvoiceOracleCode"
            @oracle-invoice-number-uploaded="oracleInvoiceNumberUploaded"
        >
        </UploadOracleInvoice>
        <InvoiceRecordTransaction
            v-if="level == 'internal'"
            ref="invoice_record_transaction"
            :invoice_id="selectedInvoiceId"
            :invoice_lodgement_number="selectedInvoiceLodgementNumber"
            :balance_remaining="selectedInvoiceBalanceRemaining"
            :force="true"
            @transaction-recorded="transactionRecorded"
        >
        </InvoiceRecordTransaction>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import InvoiceViewTransactions from '../internal/invoices/invoice_view_transactions.vue';
import InvoiceRecordTransaction from '../internal/invoices/invoice_record_transaction.vue';
import UploadOracleInvoice from '../internal/invoices/invoice_upload_oracle_invoice.vue';
import GenerateAdHocInvoiceRecord from '../internal/invoices/invoice_generate_ad_hoc_record.vue';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';

import { v4 as uuid } from 'uuid';
import { api_endpoints, constants } from '@/utils/hooks';

export default {
    name: 'TableInvoices',
    components: {
        CollapsibleFilters,
        datatable,
        InvoiceViewTransactions,
        UploadOracleInvoice,
        GenerateAdHocInvoiceRecord,
        InvoiceRecordTransaction,
    },
    props: {
        level: {
            type: String,
            required: true,
            validator: function (val) {
                let options = ['internal', 'referral', 'external'];
                return options.indexOf(val) != -1 ? true : false;
            },
        },
        approvalId: {
            type: Number,
            required: false,
            default: null,
        },
    },
    data() {
        return {
            datatable_id: 'invoices-datatable-' + uuid(),

            // selected values for filtering
            filterInvoiceOrganisation: sessionStorage.getItem(
                'filterInvoiceOrganisation'
            )
                ? sessionStorage.getItem('filterInvoiceOrganisation')
                : 'all',
            filterInvoiceStatus: sessionStorage.getItem('filterInvoiceStatus')
                ? sessionStorage.getItem('filterInvoiceStatus')
                : 'all',
            filterInvoiceDueDateFrom: sessionStorage.getItem(
                'filterInvoiceDueDateFrom'
            )
                ? sessionStorage.getItem('filterInvoiceDueDateFrom')
                : '',
            filterInvoiceDueDateTo: sessionStorage.getItem(
                'filterInvoiceDueDateTo'
            )
                ? sessionStorage.getItem('filterInvoiceDueDateTo')
                : '',

            // filtering options
            organisations: [],
            invoice_types: [],
            invoice_statuses: [],

            // Filters toggle
            filters_expanded: false,

            selectedInvoiceId: null,
            selectedInvoiceLodgementNumber: null,
            selectedInvoiceAmount: null,
            selectedInvoiceOracleInvoiceNumber: null,
            selectedInvoiceBalanceRemaining: null,
            selectedInvoiceOracleCode: null,
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
        url: function () {
            if (this.approvalId) {
                return (
                    api_endpoints.invoices +
                    `?approval_id=${this.approvalId}&format=datatables`
                );
            }
            return api_endpoints.invoices + '?format=datatables';
        },
        filterApplied: function () {
            if (
                this.filterInvoiceStatus.toLowerCase() === 'all' &&
                this.filterInvoiceOrganisation === 'all' &&
                this.filterInvoiceDueDateFrom.toLowerCase() === '' &&
                this.filterInvoiceDueDateTo.toLowerCase() === ''
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
        invoicesHeaders: function () {
            if (this.is_internal) {
                return [
                    'ID',
                    'Number',
                    'Approval',
                    'Type',
                    'Holder',
                    'Status',
                    'Invoice PDF',
                    'Amount',
                    'GST Free',
                    'Date Due',
                    'Date Issued',
                    'Oracle Invoice Number',
                    'Receivable Activity Code',
                    'Action',
                ];
            }
            return [
                'ID',
                'Number',
                'Approval',
                'Type',
                'Holder',
                'Status',
                'Invoice',
                'Amount',
                'GST Free',
                'Date Due',
                'Date Issued',
                'Action',
            ];
        },
        idColumn: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: false,
                render: function (row, type, full) {
                    return full.id;
                },
            };
        },
        lodgementNumberColumn: function () {
            return {
                data: 'lodgement_number',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.lodgement_number;
                },
            };
        },
        approvalColumn: function () {
            return {
                data: 'approval_lodgement_number',
                orderable: true,
                searchable: true,
                visible: true,
                name: 'approval.lodgement_number',
                render: function (row, type, full) {
                    return full.approval_lodgement_number;
                },
            };
        },
        approvalTypeColumn: function () {
            return {
                data: 'approval_type',
                orderable: true,
                searchable: true,
                visible: true,
                name: 'approval__approval_type__name',
                render: function (row, type, full) {
                    return full.approval_type;
                },
            };
        },
        holderColumn: function () {
            return {
                data: 'holder',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    return full.holder;
                },
            };
        },
        statusColumn: function () {
            return {
                data: 'status_display',
                orderable: true,
                searchable: true,
                visible: true,
                name: 'status',
                render: function (row, type, full) {
                    if ('pending_upload_oracle_invoice' == full.status) {
                        return `<span class="badge bg-secondary">${full.status_display}</span>`;
                    }
                    if ('unpaid' == full.status) {
                        if (
                            full.date_due &&
                            new Date(full.date_due) < new Date()
                        ) {
                            return `<span class="badge bg-danger">${full.status_display} (Overdue)</span>`;
                        }
                        return `<span class="badge bg-warning">${full.status_display}</span>`;
                    }
                    if ('paid' == full.status) {
                        return `<span class="badge bg-success">${full.status_display}</span>`;
                    }
                    if ('void' == full.status) {
                        return `<span class="badge bg-secondary">${full.status_display}</span>`;
                    }
                    return `<span class="badge bg-secondary">${full.status_display}</span>`;
                },
            };
        },
        ledgerInvoicePDFColumn: function () {
            return {
                data: 'ledger_invoice_url',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (!full.ledger_invoice_url) {
                        return 'Not Yet Uploaded';
                    }
                    return `<a href="${full.ledger_invoice_url}" target="_blank">Invoice PDF
                                        <i
                                            class="fa fa-external-link"
                                            aria-hidden="true"
                                        ></i></a>`;
                },
            };
        },
        amountColumn: function () {
            return {
                data: 'amount',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return `$${full.amount}`;
                },
            };
        },
        incGSTColumn: function () {
            return {
                data: 'gst_free',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (full.gst_free) {
                        return '<i class="fa fa-check" aria-hidden="true" style="color:green;"></i>';
                    } else {
                        return '<i class="fa fa-times" aria-hidden="true" style="color:red;"></i>';
                    }
                },
            };
        },
        dateIssuedColumn: function () {
            return {
                data: 'date_issued',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (!full.date_due) {
                        return 'TBC';
                    }
                    return new Date(full.date_issued).toLocaleDateString(
                        'en-AU'
                    );
                },
            };
        },
        dateDueColumn: function () {
            return {
                data: 'date_due',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (!full.date_due) {
                        return 'TBC';
                    }
                    return new Date(full.date_due).toLocaleDateString('en-AU');
                },
            };
        },
        actionColumn: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    let links = '';
                    if (full.status == 'discarded') {
                        return links;
                    }

                    if (full.transaction_count > 0) {
                        links += `<a href="#${full.id}" data-view-transactions="${full.id}" data-invoice-lodgement-number="${full.lodgement_number}" data-invoice-amount="${full.amount}">View Transactions</a><br />`;
                    }
                    if (
                        full.is_customer &&
                        full.balance > 0 &&
                        ![
                            'paid',
                            'void',
                            'pending_upload_oracle_invoice',
                        ].includes(full.status)
                    ) {
                        let end_point =
                            api_endpoints.invoices + full.id + '/pay_invoice/';
                        links += `<a href="${end_point}">Pay Now</a><br />`;
                    }
                    if (full.is_finance_officer) {
                        // Only allow record transaction action if an oracle invoice has been uploaded
                        if ('pending_upload_oracle_invoice' != full.status) {
                            // In the case that an invoice is overpaid we will want to allow recording a transaction to correct the balance
                            if (
                                'unpaid' === full.status ||
                                full.balance != '0.00'
                            ) {
                                links += `<a href="#${full.id}" data-record-transaction="${full.id}" data-invoice-lodgement-number="${full.lodgement_number}" data-balance-remaining="${full.balance}">Record Transaction</a><br />`;
                            }
                        }
                        if (!full.oracle_invoice_number) {
                            links += `<a href="#${full.id}" data-edit-oracle-invoice-number="${full.id}" data-invoice-lodgement-number="${full.lodgement_number}" data-oracle-invoice-number="${full.oracle_invoice_number}" data-oracle-code="${full.oracle_code__id}">Upload Oracle Invoice</a><br />`;
                        }
                    }
                    return links;
                },
            };
        },
        oracleInvoiceNumberColumn: function () {
            return {
                data: 'oracle_invoice_number',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let oracleInvoiceNumber = 'Not Yet Entered';
                    if (full.oracle_invoice_number) {
                        oracleInvoiceNumber = full.oracle_invoice_number;
                    }
                    return oracleInvoiceNumber;
                },
            };
        },
        oracleCodeColumn: function () {
            return {
                data: 'oracle_code__code',
                name: 'oracle_code__code',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let oracleCode = 'Not Yet Selected';
                    if (full.oracle_code__code) {
                        oracleCode = full.oracle_code__code;
                    }
                    return oracleCode;
                },
            };
        },
        applicableColumns: function () {
            let columns = [
                this.idColumn,
                this.lodgementNumberColumn,
                this.approvalColumn,
                this.approvalTypeColumn,
                this.holderColumn,
                this.statusColumn,
                this.ledgerInvoicePDFColumn,
                this.amountColumn,
                this.incGSTColumn,
                this.dateDueColumn,
                this.dateIssuedColumn,
                this.actionColumn,
            ];
            if (this.level === 'internal') {
                columns = [
                    this.idColumn,
                    this.lodgementNumberColumn,
                    this.approvalColumn,
                    this.approvalTypeColumn,
                    this.holderColumn,
                    this.statusColumn,
                    this.ledgerInvoicePDFColumn,
                    this.amountColumn,
                    this.incGSTColumn,
                    this.dateDueColumn,
                    this.dateIssuedColumn,
                    this.oracleInvoiceNumberColumn,
                    this.oracleCodeColumn,
                    this.actionColumn,
                ];
            }
            return columns;
        },
        invoicesOptions: function () {
            let vm = this;
            let buttons = [];
            if (this.level === 'internal') {
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
            }

            return {
                searching: true,
                autoWidth: true,
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
                responsive: true,
                serverSide: true,
                ordering: true,
                ajax: {
                    url: vm.url,
                    dataSrc: 'data',

                    // adding extra GET params for Custom filtering
                    data: function (d) {
                        // Add filters selected
                        d.filter_invoice_organisation =
                            vm.filterInvoiceOrganisation;
                        d.filter_invoice_status = vm.filterInvoiceStatus;
                        d.filter_invoice_due_date_from =
                            vm.filterInvoiceDueDateFrom;
                        d.filter_invoice_due_date_to =
                            vm.filterInvoiceDueDateTo;
                    },
                },
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,
                order: [[1, 'desc']],
                columns: vm.applicableColumns,
                processing: true,
                initComplete: function () {
                    vm.$refs.invoices_datatable.vmDataTable.draw('page');
                },
            };
        },
    },
    watch: {
        filterInvoiceOrganisation: function () {
            this.$refs.invoices_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterInvoiceOrganisation',
                this.filterInvoiceOrganisation
            );
        },
        filterInvoiceStatus: function () {
            this.$refs.invoices_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterInvoiceStatus',
                this.filterInvoiceStatus
            );
        },
        filterInvoiceDueDateFrom: function () {
            this.$refs.invoices_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterInvoiceDueDateFrom',
                this.filterInvoiceDueDateFrom
            );
        },
        filterInvoiceDueDateTo: function () {
            this.$refs.invoices_datatable.vmDataTable.draw();
            sessionStorage.setItem(
                'filterInvoiceDueDateTo',
                this.filterInvoiceDueDateTo
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
        this.$nextTick(() => {
            this.addEventListeners();
        });
    },
    methods: {
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(
                this.filterApplied
            );
        },
        adjust_table_width: function () {
            this.$refs.invoices_datatable.vmDataTable.columns
                .adjust()
                .responsive.recalc();
        },
        expandCollapseFilters: function () {
            this.filters_expanded = !this.filters_expanded;
        },
        fetchFilterLists: async function () {
            let vm = this;

            fetch(api_endpoints.invoices + 'statuses/').then(
                async (response) => {
                    vm.invoice_statuses = await response.json();
                },
                (error) => {
                    console.error(error);
                }
            );

            fetch(api_endpoints.organisations + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        Promise.reject(error);
                    }
                    vm.organisations = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    Promise.reject(error);
                });
        },
        generateAdHocInvoiceRecord: function () {
            let vm = this;
            vm.$refs.invoice_raise_ad_hoc.isModalOpen = true;
        },
        adHocInvoiceRecordGenerated: function () {
            let vm = this;
            vm.$refs.invoice_raise_ad_hoc.isModalOpen = false;
            vm.$refs.invoices_datatable.vmDataTable.draw();
        },
        viewTransactions: function (id, lodgement_number, amount) {
            let vm = this;
            vm.selectedInvoiceId = parseInt(id);
            vm.selectedInvoiceLodgementNumber = lodgement_number;
            vm.selectedInvoiceAmount = Number(amount);
            vm.$refs.invoice_view_transactions.isModalOpen = true;
        },
        editOracleInvoiceNumber: function (
            id,
            lodgement_number,
            oracle_invoice_number,
            oracle_code
        ) {
            let vm = this;
            vm.selectedInvoiceId = parseInt(id);
            vm.selectedInvoiceLodgementNumber = lodgement_number;
            vm.selectedInvoiceOracleInvoiceNumber = oracle_invoice_number;
            vm.selectedInvoiceOracleCode = oracle_code;
            vm.$refs.invoice_upload_oracle_invoice.isModalOpen = true;
        },
        oracleInvoiceNumberUploaded: function () {
            let vm = this;
            vm.$refs.invoice_upload_oracle_invoice.isModalOpen = false;
            vm.$refs.invoices_datatable.vmDataTable.draw();
        },
        recordTransaction: function (id, lodgement_number, balance_remaining) {
            let vm = this;
            vm.selectedInvoiceId = parseInt(id);
            vm.selectedInvoiceLodgementNumber = lodgement_number;
            vm.selectedInvoiceBalanceRemaining = Number(balance_remaining);
            vm.$refs.invoice_record_transaction.isModalOpen = true;
        },
        transactionRecorded: function () {
            let vm = this;
            vm.$refs.invoice_record_transaction.isModalOpen = false;
            vm.$refs.invoices_datatable.vmDataTable.draw();
        },
        addEventListeners: function () {
            let vm = this;

            vm.$refs.invoices_datatable.vmDataTable.on(
                'click',
                'a[data-view-transactions]',
                function (e) {
                    e.preventDefault();
                    let id = $(this).attr('data-view-transactions');
                    let lodgement_number = $(this).attr(
                        'data-invoice-lodgement-number'
                    );
                    let amount = $(this).attr('data-invoice-amount');
                    vm.viewTransactions(id, lodgement_number, amount);
                }
            );

            vm.$refs.invoices_datatable.vmDataTable.on(
                'click',
                'a[data-edit-oracle-invoice-number]',
                function (e) {
                    e.preventDefault();
                    let id = $(this).attr('data-edit-oracle-invoice-number');
                    let lodgement_number = $(this).attr(
                        'data-invoice-lodgement-number'
                    );
                    let oracle_invoice_number = $(this).attr(
                        'data-oracle-invoice-number'
                    );
                    let oracle_code = $(this).attr('data-oracle-code');
                    if (oracle_invoice_number == 'null') {
                        oracle_invoice_number = null;
                    }
                    vm.editOracleInvoiceNumber(
                        id,
                        lodgement_number,
                        oracle_invoice_number,
                        oracle_code
                    );
                }
            );

            vm.$refs.invoices_datatable.vmDataTable.on(
                'click',
                'a[data-record-transaction]',
                function (e) {
                    e.preventDefault();
                    let id = $(this).attr('data-record-transaction');
                    let lodgement_number = $(this).attr(
                        'data-invoice-lodgement-number'
                    );
                    let balance_remaining = $(this).attr(
                        'data-balance-remaining'
                    );
                    vm.recordTransaction(
                        id,
                        lodgement_number,
                        balance_remaining
                    );
                }
            );
        },
    },
};
</script>
