<template>
    <div>
        <div v-if="level === 'internal'" class="row">
            <div class="col">
                <button
                    style="margin-bottom: 10px"
                    class="btn btn-primary float-end"
                    @click.prevent="addContact()"
                >
                    Add Contact
                </button>
            </div>
        </div>
        <CollapsibleFilters
            ref="collapsible_filters"
            component_title="Filters"
            class="mb-2"
            @created="collapsible_component_mounted"
        >
            <div class="row mt-1 p-2">
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Role</label>
                        <select v-model="filterRole" class="form-select">
                            <option value="">All</option>
                            <option value="consultant">Consultant</option>
                            <option value="organisation_user">Employee</option>
                            <option value="organisation_admin">Admin</option>
                        </select>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="organisation_contacts_datatable"
                    :dt-options="dtOptions"
                    :dt-headers="dtHeaders"
                    @vue:mounted="addOrgContactEventListeners"
                />
            </div>
            <AddContact ref="add_contact" :org_id="organisationId" />
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import datatable from '@/utils/vue/datatable.vue';
import AddContact from '@common-utils/add_contact.vue';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import { api_endpoints, helpers, constants } from '@/utils/hooks';

export default {
    name: 'TableOrganisationContacts',
    components: {
        datatable,
        AddContact,
        CollapsibleFilters,
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
        /**
         * The organisation for which to display contacts
         */
        organisationId: {
            type: [Number, null],
            required: true,
            validator: (p) => {
                // Seems hacky but lets me have a required prop that can be null
                let valid = p === null || ['number'].indexOf(typeof p) !== -1;
                return valid;
            },
        },
    },
    data() {
        return {
            datatable_id: 'organisation-contacts-datatable-' + uuid(),
            // selected values for filtering
            filterRole: sessionStorage.getItem('filterRole')
                ? sessionStorage.getItem('filterRole')
                : '',
            // Filters toggle
            filters_expanded: false,
        };
    },
    computed: {
        ajaxUrl: function () {
            var url =
                api_endpoints.organisation_contacts_paginated +
                '?format=datatables';
            if (this.organisationId) {
                url += '&organisation_id=' + this.organisationId;
            }
            return url;
        },
        filterApplied: function () {
            if (this.filterRole.toLowerCase() === '') {
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
        dtHeaders: function () {
            return [
                'Number',
                'Name',
                'Role',
                'Phone',
                'Mobile',
                'Fax',
                'Email',
                'Action',
            ];
        },
        idColumn: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: false,
                visible: false,
                render: function (row, type, full) {
                    return full.id;
                },
            };
        },
        nameColumn: function () {
            return {
                data: 'full_name',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    return full.full_name;
                },
                name: 'first_name, last_name',
            };
        },
        roleColumn: function () {
            return {
                data: 'user_role',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.user_role;
                },
                name: 'user_role',
            };
        },
        phoneColumn: function () {
            return {
                data: 'phone_number',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    return full.phone_number;
                },
            };
        },
        mobileColumn: function () {
            return {
                data: 'mobile_number',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    return full.mobile_number;
                },
            };
        },
        faxColumn: function () {
            return {
                data: 'fax_number',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    return full.fax_number;
                },
            };
        },
        emailColumn: function () {
            return {
                data: 'email',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    return full.email;
                },
            };
        },
        actionsColumn: function () {
            return {
                data: 'id',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (
                        'Organisation Admin' == full.user_role &&
                        1 == full.admin_user_count
                    ) {
                        return '';
                    }
                    return `<button class="btn btn-sm btn-danger remove-contact" data-email='${full.email}' data-id='${full.id}' data-name='${full.full_name}'><i class="fa-solid fa-trash pe-1"></i> Remove</button>`;
                },
            };
        },
        applicableColumns: function () {
            return [
                this.idColumn,
                this.nameColumn,
                this.roleColumn,
                this.phoneColumn,
                this.mobileColumn,
                this.faxColumn,
                this.emailColumn,
                this.actionsColumn,
            ];
        },
        dtOptions: function () {
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
                autoWidth: false,
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
                ajax: {
                    url: vm.ajaxUrl,
                    dataSrc: 'data',

                    // adding extra GET params for Custom filtering
                    data: function (d) {
                        // Add filters selected
                        d.filter_role = vm.filterRole;
                        // Add search terms to be concatenated on the queryset
                        d.search_terms = 'first_name, last_name, email';
                    },
                },
                order: [[0, 'desc']],
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons: buttons,
                columns: vm.applicableColumns,
                processing: true,
            };
        },
    },
    watch: {
        filterRole: function () {
            this.$refs.organisation_contacts_datatable.vmDataTable.draw();
            sessionStorage.setItem('filterRole', this.filterRole);
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
    created: function () {},
    methods: {
        collapsible_component_mounted: function () {
            this.$refs.collapsible_filters.show_warning_icon(
                this.filterApplied
            );
        },
        expandCollapseFilters: function () {
            this.filters_expanded = !this.filters_expanded;
        },
        addContact: function () {
            this.$refs.add_contact.isModalOpen = true;
            this.$nextTick(() => {
                this.$refs.add_contact.$refs.first_name.focus();
            });
        },
        addedContact: function () {
            let vm = this;
            swal.fire({
                title: 'Added',
                text: 'The contact has been successfully added.',
                icon: 'success',
            });
            vm.$refs.organisation_contacts_datatable.vmDataTable.ajax.reload();
        },
        deleteContact: function (id) {
            let vm = this;
            const requestOptions = {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
            };
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.organisation_contacts,
                    id
                ),
                requestOptions
            )
                .then(async (response) => {
                    if (204 === response.status) {
                        swal.fire({
                            title: 'Contact Deleted',
                            text: 'The contact was successfully deleted',
                            icon: 'success',
                        });
                        vm.$refs.contacts_datatable.vmDataTable.ajax.reload();
                    }
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        if (400 == response.status) {
                            const errorString =
                                helpers.getErrorStringFromResponseData(data);
                            swal.fire({
                                title: 'Unable to Delete Contact',
                                html: `${errorString}`,
                                icon: 'error',
                            });
                        }
                        return Promise.reject(error);
                    }
                    swal.fire({
                        title: 'Contact Deleted',
                        text: 'The contact was successfully deleted',
                        icon: 'success',
                    });
                    vm.$refs.organisation_contacts_datatable.vmDataTable.ajax.reload();
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
        },
        personRedirect: function (id) {
            window.location.href = '/internal/person/details/' + id;
        },
        addOrgContactEventListeners: function () {
            let vm = this;

            vm.$refs.organisation_contacts_datatable.vmDataTable.on(
                'click',
                '.remove-contact',
                (e) => {
                    e.preventDefault();

                    let name = $(e.target).data('name');
                    let email = $(e.target).data('email');
                    let id = $(e.target).data('id');
                    swal.fire({
                        title: 'Delete Contact',
                        text: `Are you sure you want to remove ${name} (${email}) as a contact  ?`,
                        icon: 'question',
                        showCancelButton: true,
                        confirmButtonText: 'Accept',
                        reverseButtons: true,
                    }).then(
                        (result) => {
                            if (result.isConfirmed) {
                                vm.deleteContact(id);
                            }
                        },
                        (error) => {
                            console.error(error);
                        }
                    );
                }
            );
        },
    },
};
</script>
