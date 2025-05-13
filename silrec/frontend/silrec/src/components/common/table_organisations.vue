<template>
    <div>
        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="organisations_datatable"
                    :dt-options="invoicesOptions"
                    :dt-headers="invoicesHeaders"
                />
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { v4 as uuid } from 'uuid';
import { api_endpoints, constants } from '@/utils/hooks';

export default {
    name: 'TableOrganisations',
    components: {
        datatable,
    },
    data() {
        return {
            datatable_id: 'organisations-datatable-' + uuid(),
        };
    },
    computed: {
        url: function () {
            return api_endpoints.organisations + `?format=datatables`;
        },
        invoicesHeaders: function () {
            return [
                'ID',
                'Ledger ID',
                'Name',
                'Trading Name',
                'ABN',
                'Email',
                'Actions',
            ];
        },
        idColumn: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: false,
            };
        },
        ledgerOrganisationIDColumn: function () {
            return {
                data: 'ledger_organisation_id',
                orderable: true,
                searchable: true,
                visible: true,
            };
        },
        ledgerOrganisationNameColumn: function () {
            return {
                data: 'ledger_organisation_name',
                orderable: true,
                searchable: true,
                visible: true,
            };
        },
        ledgerOrganisationTradingNameColumn: function () {
            return {
                data: 'ledger_organisation_trading_name',
                orderable: true,
                searchable: true,
                visible: true,
            };
        },
        ledgerOrganisationABNColumn: function () {
            return {
                data: 'ledger_organisation_abn',
                orderable: true,
                searchable: true,
                visible: true,
            };
        },
        ledgerOrganisationEmailColumn: function () {
            return {
                data: 'ledger_organisation_email',
                orderable: true,
                searchable: true,
                visible: true,
            };
        },
        actionColumn: function () {
            return {
                data: 'id',
                visible: true,
                render: function (row, type, full) {
                    return `<a href="/internal/organisations/${full.id}"">Manage</a>`;
                },
            };
        },
        applicableColumns: function () {
            return [
                this.idColumn,
                this.ledgerOrganisationIDColumn,
                this.ledgerOrganisationNameColumn,
                this.ledgerOrganisationTradingNameColumn,
                this.ledgerOrganisationABNColumn,
                this.ledgerOrganisationEmailColumn,
                this.actionColumn,
            ];
        },
        invoicesOptions: function () {
            let vm = this;
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
                    vm.$refs.organisations_datatable.vmDataTable.draw('page');
                },
            };
        },
    },
};
</script>
