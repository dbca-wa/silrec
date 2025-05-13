<template id="comms_logs">
    <div class="">
        <div class="card mb-3">
            <div class="card-header">Logs</div>
            <div class="card-body border-bottom">
                <label for="assigned-to" class="form-label"
                    >Communication Logs</label
                >
                <div class="rounded border py-2">
                    <span class="ps-3 pe-2"
                        ><i class="bi bi-card-list"></i>
                    </span>
                    <a ref="showCommsBtn" href="#" class="pe-5" @click.prevent
                        >View</a
                    >
                    <template v-if="!disable_add_entry">
                        <span class="pe-2">
                            <i class="bi bi-plus-circle"></i>
                        </span>
                        <a ref="addCommsBtn" href="#" @click.prevent="addComm()"
                            >Add Entry</a
                        >
                    </template>
                </div>
            </div>
            <div class="card-body">
                <label for="assigned-to" class="form-label">Action Logs</label>
                <div class="rounded border py-2">
                    <span class="ps-3 pe-2"
                        ><i class="bi bi-card-list"></i>
                    </span>
                    <a ref="showActionBtn" href="#" @click.prevent>View</a>
                </div>
            </div>
        </div>
        <AddCommLog ref="add_comm" :url="comms_add_url" />
    </div>
</template>

<script>
import AddCommLog from './add_comm_log.vue';
import { constants } from '@/utils/hooks';
import { v4 as uuid } from 'uuid';

export default {
    name: 'CommsLogSection',
    components: {
        AddCommLog,
    },
    props: {
        comms_url: {
            type: String,
            required: true,
        },
        logs_url: {
            type: String,
            required: true,
        },
        comms_add_url: {
            type: String,
            required: true,
        },
        disable_add_entry: {
            type: Boolean,
            default: true,
        },
    },
    data() {
        let vm = this;
        return {
            uuid: uuid(),
            dateFormat: 'DD/MM/YYYY HH:mm:ss',
            actionsTable: null,
            popoversInitialised: false,
            actionsDtOptions: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                order: [[3, 'desc']], // order the non-formatted date as a hidden column
                dom:
                    "<'row'<'col-sm-4'l><'col-sm-8'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-5'i><'col-sm-7'p>>",
                processing: true,
                ajax: {
                    url: vm.logs_url,
                    dataSrc: '',
                },
                columns: [
                    {
                        title: 'Who',
                        data: 'who',
                        orderable: false,
                    },
                    {
                        title: 'What',
                        data: 'what',
                        orderable: false,
                    },
                    {
                        title: 'When',
                        data: 'when',
                        orderable: false,
                        mRender: function (data) {
                            return moment(data).format(vm.dateFormat);
                        },
                    },
                    {
                        title: 'Created',
                        data: 'when',
                        visible: false,
                    },
                ],
            },
            commsDtOptions: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                order: [[8, 'desc']], // order the non-formatted date as a hidden column
                processing: true,
                dom:
                    "<'row'<'col-sm-4'l><'col-sm-8'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-5'i><'col-sm-7'p>>",
                ajax: {
                    url: vm.comms_url,
                    dataSrc: '',
                },
                columns: [
                    {
                        title: 'Date',
                        data: 'created',
                        render: function (date) {
                            return moment(date).format(vm.dateFormat);
                        },
                    },
                    {
                        title: 'Type',
                        data: 'type',
                    },
                    {
                        title: 'To',
                        data: 'to',
                        render: function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 25,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-bs-toggle="popover" ' +
                                        'data-trigger="click" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-bs-content="<%= text %>" ' +
                                        '>more</a>'
                                );
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value,
                                });
                            }

                            return result;
                        },
                    },
                    {
                        title: 'CC',
                        data: 'cc',
                        render: function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 25,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-bs-toggle="popover" ' +
                                        'data-trigger="click" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-bs-content="<%= text %>" ' +
                                        '>more</a>'
                                );
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value,
                                });
                            }

                            return result;
                        },
                    },
                    {
                        title: 'From',
                        data: 'fromm',
                        render: function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 25,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-bs-toggle="popover" ' +
                                        'data-trigger="click" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-bs-content="<%= text %>" ' +
                                        '>more</a>'
                                );
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value,
                                });
                            }

                            return result;
                        },
                    },
                    {
                        title: 'Subject/Desc.',
                        data: 'subject',
                        render: function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 25,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-bs-toggle="popover" ' +
                                        'data-trigger="click" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-bs-content="<%= text %>" ' +
                                        '>more</a>'
                                );
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value,
                                });
                            }

                            return result;
                        },
                    },
                    {
                        title: 'Text',
                        data: 'text',
                        render: function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 25,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-bs-toggle="popover" ' +
                                        'data-trigger="click" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-bs-content="<%= text %>" ' +
                                        '>more</a>'
                                );
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value,
                                });
                            }

                            return result;
                        },
                    },
                    {
                        title: 'Documents',
                        data: 'documents',
                        render: function (row, type, full) {
                            if (!full.documents || !full.documents.length) {
                                return 'No documents';
                            }
                            let result =
                                '<ul class="list-group list-group-numbered">';

                            for (let i = 0; i < full.documents.length; i++) {
                                result +=
                                    '<li class="list-group-item"><a href="' +
                                    full.document_urls[i] +
                                    '" target="_blank"> ' +
                                    full.documents[i][0] +
                                    '</a></li>';
                            }
                            result += '</ul>';
                            return result;
                        },
                    },
                    {
                        title: 'Created',
                        data: 'created',
                        visible: false,
                    },
                ],
            },
            commsTable: null,
        };
    },
    mounted: function () {
        let vm = this;
        this.$nextTick(() => {
            vm.initialisePopovers();
        });
    },
    methods: {
        initialiseCommLogs: function () {
            var myDefaultAllowList = bootstrap.Tooltip.Default.allowList;

            // To allow table elements (ref: https://getbootstrap.com/docs/5.0/getting-started/javascript/#sanitizer)
            myDefaultAllowList.table = ['class', 'cellspacing', 'width'];

            let vm = this;
            let commsLogId = 'comms-log-table' + vm.uuid;
            let popover_name = 'popover-' + vm.uuid + '-comms';
            let popover_elem = $(vm.$refs.showCommsBtn)[0];
            let my_content =
                '<table id="' +
                commsLogId +
                '" class="hover table table-striped table-bordered dt-responsive" cellspacing="0" width="100%"></table>';
            let my_template =
                '<div class="popover ' +
                popover_name +
                '" role="tooltip"><div class="popover-arrow" style="top:110px;"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>';

            new bootstrap.Popover(popover_elem, {
                html: true,
                content: my_content,
                template: my_template,
                title: 'Communication logs',
                container: 'body',
                placement: 'right',
                trigger: 'click',
            });
            popover_elem.addEventListener('inserted.bs.popover', () => {
                // when the popover template has been added to the DOM
                vm.commsTable = $('#' + commsLogId).DataTable(
                    vm.commsDtOptions
                );
                vm.commsTable.on('draw', function () {
                    // Draw event - fired once the table has completed a draw.
                    var popoverTriggerList = [].slice.call(
                        document.querySelectorAll(
                            '#' + commsLogId + ' [data-bs-toggle="popover"]'
                        )
                    );
                    popoverTriggerList.map(function (popoverTriggerEl) {
                        return new bootstrap.Popover(popoverTriggerEl, {
                            container: '#' + commsLogId,
                        });
                    });
                });
            });
            popover_elem.addEventListener('shown.bs.popover', () => {
                // when the popover has been made visible to the user
                let el = vm.$refs.showCommsBtn;
                var popover_bounding_top = parseInt(
                    $('.' + popover_name)[0].getBoundingClientRect().top
                );
                var el_bounding_top = parseInt(
                    $(el)[0].getBoundingClientRect().top
                );
                var diff = el_bounding_top - popover_bounding_top;
                var x = diff + 5;
                $('.' + popover_name)
                    .children('.arrow')
                    .css('top', x + 'px');
            });
        },
        initialiseActionLogs: function () {
            var myDefaultAllowList = bootstrap.Tooltip.Default.allowList;

            // To allow table elements (ref: https://getbootstrap.com/docs/5.0/getting-started/javascript/#sanitizer)
            myDefaultAllowList.table = ['class', 'cellspacing', 'width'];

            let vm = this;
            let actionLogId = 'actions-log-table' + vm.uuid;
            let popover_name = 'popover-' + vm.uuid + '-logs';
            let popover_elem = $(vm.$refs.showActionBtn)[0];
            let my_content =
                '<table id="' +
                actionLogId +
                '" class="hover table table-striped table-bordered dt-responsive" cellspacing="0" width="100%"></table>';
            let my_template =
                '<div class="popover ' +
                popover_name +
                '" role="tooltip"><div class="popover-arrow" style="top:110px;"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>';

            new bootstrap.Popover(popover_elem, {
                html: true,
                content: my_content,
                template: my_template,
                title: 'Action logs',
                container: 'body',
                placement: 'right',
                trigger: 'click',
            });
            popover_elem.addEventListener('inserted.bs.popover', () => {
                vm.actionsTable = $('#' + actionLogId).DataTable(
                    this.actionsDtOptions
                );
                vm.actionsTable.on('draw', function () {
                    var popoverTriggerList = [].slice.call(
                        document.querySelectorAll(
                            '#' + actionLogId + ' [data-bs-toggle="popover"]'
                        )
                    );
                    popoverTriggerList.map(function (popoverTriggerEl) {
                        return new bootstrap.Popover(popoverTriggerEl);
                    });
                });
            });
            popover_elem.addEventListener('shown.bs.popover', () => {
                // when the popover has been made visible to the user
                let el = vm.$refs.showActionBtn;
                var popover_bounding_top = parseInt(
                    $('.' + popover_name)[0].getBoundingClientRect().top
                );
                var el_bounding_top = parseInt(
                    $(el)[0].getBoundingClientRect().top
                );
                var diff = el_bounding_top - popover_bounding_top;
                var x = diff + 5;
                $('.' + popover_name)
                    .children('.arrow')
                    .css('top', x + 'px');
            });
        },
        initialisePopovers: function () {
            if (!this.popoversInitialised) {
                this.initialiseActionLogs();
                this.initialiseCommLogs();
                this.popoversInitialised = true;
            }
        },
        addComm() {
            this.$refs.add_comm.isModalOpen = true;
            this.$nextTick(() => {
                $('input#to').focus();
            });
        },
    },
};
</script>
