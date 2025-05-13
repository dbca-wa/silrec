<template lang="html">
    <datatable
        :id="datatable_id"
        ref="related_items_datatable"
        :dt-options="datatable_options"
        :dt-headers="datatable_headers"
    />
</template>

<script>
import { v4 as uuid } from 'uuid';
import { constants } from '@/utils/hooks';
import datatable from '@/utils/vue/datatable.vue';

export default {
    name: 'TableRelatedItems',
    components: {
        datatable,
    },
    props: {
        ajaxUrl: {
            type: String,
            required: true,
        },
    },
    data() {
        return {
            datatable_id: uuid(),
        };
    },
    computed: {
        column_lodgement_number: function () {
            return {
                data: 'lodgement_number',
                orderable: false,
                searchable: false,
                visible: true,
            };
        },
        column_type: function () {
            return {
                data: 'item_type',
                orderable: false,
                searchable: false,
                visible: true,
            };
        },
        column_description: function () {
            return {
                data: 'description',
                orderable: false,
                searchable: false,
                visible: true,
            };
        },
        column_action: function () {
            return {
                data: 'detail_url',
                orderable: false,
                searchable: false,
                visible: true,
                // eslint-disable-next-line no-unused-vars
                render: function (data, type, row) {
                    return `<a href="${data}" target="_blank">View</a>`;
                },
            };
        },
        datatable_options: function () {
            let vm = this;
            let columns = [
                vm.column_lodgement_number,
                vm.column_type,
                vm.column_description,
                vm.column_action,
            ];
            return {
                autoWidth: false,
                columnDefs: [
                    { responsivePriority: 1, targets: 0 },
                    {
                        responsivePriority: 2,
                        targets: -1,
                    },
                ],
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                serverSide: true,
                searching: true,
                ordering: true,
                order: [[0, 'desc']],
                ajax: {
                    url: vm.ajaxUrl,
                    dataSrc: 'data',
                    data: function () {},
                    error: function (response, textStatus, errorThrown) {
                        let error = response.responseJSON
                            ? response.responseJSON.data
                            : response.responseText;
                        console.error(
                            `${textStatus}: ${errorThrown}: ${JSON.stringify(
                                error
                            )}`
                        );
                    },
                },
                dom: 'lBfrtip',
                buttons: [],
                columns: columns,
                processing: true,
            };
        },
        datatable_headers: function () {
            return ['Number', 'Type', 'Description', 'Action'];
        },
    },
};
</script>
