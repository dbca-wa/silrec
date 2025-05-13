<template id="more-referrals">
    <div class="mt-2">
        <a ref="showRef" role="button" class="float-end" @click.prevent=""
            >Show All Referrals</a
        >
    </div>
</template>

<script>
import { constants } from '@/utils/hooks';
import {
    remindReferral,
    recallReferral,
    resendReferral,
} from '@/components/common/workflow_functions.js';
import { v4 as uuid } from 'uuid';

export default {
    name: 'MoreReferrals',
    props: {
        canAction: {
            type: Boolean,
            required: true,
        },
        referral_url: {
            type: String,
            required: true,
        },
        api_endpoint: {
            type: String,
            required: true,
        },
    },
    emits: ['switchStatus'],
    data() {
        let vm = this;
        return {
            uuid: uuid(),
            table: null,
            dateFormat: 'DD/MM/YYYY HH:mm:ss',
            datatable_url: '',
            datatable_options: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                processing: true,
                ajax: {
                    url: this.referral_url,
                    dataSrc: '',
                },
                dom:
                    "<'row'<'col-sm-4'l><'col-sm-8'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-5'i><'col-sm-7'p>>",
                columns: [
                    {
                        title: 'Sent On',
                        data: 'lodged_on',
                        render: function (date) {
                            return moment(date).format(vm.dateFormat);
                        },
                    },
                    {
                        title: 'Referee',
                        data: 'referral',
                        render: function (data) {
                            return `<span>${data.first_name} ${data.last_name}</span>`;
                        },
                    },
                    {
                        title: 'Status',
                        data: 'referral_status',
                    },
                    {
                        title: 'Action',
                        data: 'id',
                        render: function (data, type, full) {
                            var result = '';
                            if (!vm.canAction) {
                                return result;
                            }
                            let user =
                                full.referral.first_name +
                                ' ' +
                                full.referral.last_name;
                            if (
                                constants.REFERRAL_STATUS
                                    .PROCESSING_STATUS_WITH_REFERRAL.TEXT ==
                                full.referral_status
                            ) {
                                result = `<a data-id="${data}" data-user="${user}" class="remindRef">Remind</a>/<a data-id="${data}" data-user="${user}" class="recallRef">Recall</a>`;
                            } else {
                                result = `<a data-id="${data}" data-user="${user}" class="resendRef">Resend</a>`;
                            }
                            return result;
                        },
                    },
                    {
                        title: 'Assessor Comment',
                        data: 'text',
                        render: function (value) {
                            if (!value) {
                                return '';
                            }

                            let ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 20,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-bs-toggle="popover" ' +
                                        'data-bs-trigger="click" ' +
                                        'data-bs-placement="auto"' +
                                        'data-bs-html="true" ' +
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
                        title: 'Referree Comment',
                        data: 'referral_text',
                        render: function (value) {
                            let ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 20,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-bs-toggle="popover" ' +
                                        'data-bs-trigger="click" ' +
                                        'data-bs-placement="top auto"' +
                                        'data-bs-html="true" ' +
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
                ],
            },
            remindReferral: remindReferral,
            recallReferral: recallReferral,
            resendReferral: resendReferral,
        };
    },
    mounted() {
        this.$nextTick(() => {
            this.initialiseTable();
        });
    },
    methods: {
        initialiseTable: function () {
            // To allow table elements (ref: https://getbootstrap.com/docs/5.1/getting-started/javascript/#sanitizer)
            var myDefaultAllowList = bootstrap.Tooltip.Default.allowList;
            myDefaultAllowList.table = [];
            let vm = this;
            let table_id = 'more-referrals-table' + vm.uuid;
            let popover_name = 'popover-' + vm.uuid;
            let my_content =
                '<table id="' +
                table_id +
                '" class="hover table table-striped table-bordered dt-responsive" cellspacing="0" width="100%"></table>';
            let my_template =
                '<div class="popover ' +
                popover_name +
                '" role="tooltip"><div class="popover-arrow" style="top:110px;"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>';
            let popover_elem = vm.$refs.showRef;

            new bootstrap.Popover(popover_elem, {
                html: true,
                content: my_content,
                template: my_template,
                title: 'Referrals',
                container: 'body',
                placement: 'right',
                trigger: 'click focus',
            });
            popover_elem.addEventListener('inserted.bs.popover', function () {
                vm.table = $('#' + table_id).DataTable(vm.datatable_options);

                // activate popover when table is drawn.
                vm.table
                    .on('draw.dt', function () {
                        vm.initialisePopovers();
                    })
                    .on('click', '.resendRef', function (e) {
                        e.preventDefault();
                        let _id = $(this).data('id');
                        let user = $(this).data('user');
                        vm.resendReferral(vm.api_endpoint, _id, user);
                    })
                    .on('click', '.recallRef', function (e) {
                        e.preventDefault();
                        let _id = $(this).data('id');
                        let user = $(this).data('user');
                        vm.recallReferral(vm.api_endpoint, _id, user);
                    })
                    .on('click', '.remindRef', function (e) {
                        e.preventDefault();
                        let _id = $(this).data('id');
                        let user = $(this).data('user');
                        vm.remindReferral(vm.api_endpoint, _id, user);
                    });
            });
            popover_elem.addEventListener('shown.bs.popover', function () {
                let el = vm.$refs.showRef;
                let popover_bounding_top = parseInt(
                    $('.' + popover_name)[0].getBoundingClientRect().top
                );
                let el_bounding_top = parseInt(
                    $(el)[0].getBoundingClientRect().top
                );
                let diff = el_bounding_top - popover_bounding_top;
                let x = diff + 5;
                $('.' + popover_name)
                    .children('.arrow')
                    .css('top', x + 'px');
            });
        },
        switchStatus: function (value) {
            this.$emit('switchStatus', value);
        },
        initialisePopovers: function () {
            var popoverTriggerList = [].slice.call(
                document.querySelectorAll('[data-bs-toggle="popover"]')
            );
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl, {
                    container: 'body',
                });
            });
            $('[data-bs-toggle="popover"]').on('click', function (e) {
                e.preventDefault();
                return true;
            });
        },
    },
};
</script>
