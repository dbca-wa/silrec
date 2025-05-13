<template>
    <div>
        <div v-if="is_internal" class="row">
            <div class="text-end mb-2">
                <button
                    type="button"
                    class="btn btn-primary pull-right"
                    :disabled="elementDisabled"
                    @click="add_party_clicked"
                >
                    <i class="fa-solid fa-circle-plus"></i> Add Party
                </button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="parties_datatable"
                    :key="datatable_key"
                    :dt-headers="datatable_headers"
                    :dt-options="datatable_options"
                />
            </div>
        </div>
        <AddPartyModal
            ref="add_party"
            @close-modal="closeModal"
            @party-to-add="addParty"
        />
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import datatable from '@/utils/vue/datatable.vue';
import AddPartyModal from '@/components/common/modal_add_party.vue';
import { expandToggleParties } from '@/components/common/table_functions.js';
import { api_endpoints, constants } from '@/utils/hooks.js';

export default {
    name: 'TableParties',
    components: {
        datatable,
        AddPartyModal,
    },
    props: {
        level: {
            type: String,
            default: 'internal',
        },
        competitiveProcessParties: {
            type: Array,
            default: function () {
                return [];
            },
        },
        competitiveProcessId: {
            type: Number,
            default: null,
        },
        accessingUser: {
            type: Object,
            default: function () {
                return null;
            },
        },
        processing: {
            type: Boolean,
            default: false,
        },
        discarded: {
            type: Boolean,
            default: false,
        },
        declined: {
            type: Boolean,
            default: false,
        },
        completed: {
            type: Boolean,
            default: false,
        },
        finalised: {
            type: Boolean,
            default: false,
        },
        readonly: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['add-party'],
    data() {
        return {
            datatable_id: uuid(),
            datatable_key: uuid(),
            new_party_id: -1, // This is used to identify new parties in the datatable

            // For expander
            td_expand_class_name: 'expand-icon',
            td_collapse_class_name: 'collapse-icon',
            expandable_row_class_name: 'expandable_row',
            custom_row_apps: {},
        };
    },
    computed: {
        column_id: () => {
            return {
                data: 'id',
                name: 'id',
                orderable: false,
                searchable: false,
                visible: false,
                render: function (row, type, full) {
                    return full.id;
                },
            };
        },
        column_name: function () {
            return {
                data: null,
                className: 'text-truncate',
                render: function (row, type, full) {
                    if (full.is_person) {
                        return 'fullname' in full.person
                            ? full.person.fullname
                            : 'full_name' in full.person
                              ? full.person.full_name
                              : '(name)';
                    } else {
                        return '';
                    }
                },
            };
        },
        column_organisation: () => {
            return {
                data: null,
                className: 'text-truncate',
                render: function (row, type, full) {
                    if (full.is_organisation)
                        return `<span class="d-inline-block text-truncate" style="max-width:180px;">${full.organisation.ledger_organisation_name}</span>`;
                    return '';
                },
            };
        },
        column_phone: () => {
            return {
                data: null,
                render: function (row, type, full) {
                    if (full.is_person && full.person) {
                        return full.person.phone_number
                            ? full.person.phone_number
                            : '';
                    } else if (full.is_organisation && full.organisation) {
                        // Return the phone number of the first org contact in the list
                        if (
                            full.organisation.contacts &&
                            full.organisation.contacts.length > 0
                        ) {
                            return full.organisation.contacts[0].phone_number;
                        }
                        return '';
                    } else {
                        return '(phone)';
                    }
                },
            };
        },
        column_mobile: () => {
            return {
                data: null,
                render: function (row, type, full) {
                    if (full.is_person && full.person) {
                        return full.person.mobile_number
                            ? full.person.mobile_number
                            : '';
                    } else if (full.is_organisation && full.organisation) {
                        // Return the mobile number of the first org contact in the list
                        if (
                            full.organisation.contacts &&
                            full.organisation.contacts.length > 0
                        ) {
                            return full.organisation.contacts[0].mobile_number;
                        }
                        return '';
                    } else {
                        return '(mobile)';
                    }
                },
            };
        },
        column_email: () => {
            return {
                data: null,
                render: function (row, type, full) {
                    if (full.is_person && full.person) {
                        return full.person.email ? full.person.email : '';
                    } else if (full.is_organisation) {
                        return full.organisation.ledger_organisation_email;
                    } else {
                        return '(email)';
                    }
                },
            };
        },
        column_actions: () => {
            return {
                data: 'id',
                orderable: false,
                render: function (row, type, full) {
                    return `<button id="button-${full.id}" class="btn btn-sm btn-primary">Show Details</button>`;
                },
            };
        },
        is_external: function () {
            return this.level == 'external';
        },
        is_internal: function () {
            return this.level == 'internal';
        },
        datatable_headers: function () {
            if (this.is_internal) {
                return [
                    'id',
                    'Name',
                    'Organisation',
                    'Phone',
                    'Mobile',
                    'Actions',
                    'Email',
                ];
            }
            return [];
        },
        datatable_options: function () {
            let vm = this;

            let columns = [];
            columns = [
                vm.column_id,
                vm.column_name,
                vm.column_organisation,
                vm.column_phone,
                vm.column_mobile,
                vm.column_email,
                vm.column_actions,
            ];

            return {
                autoWidth: false,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                columnDefs: [
                    { responsivePriority: 1, targets: 1 },
                    {
                        responsivePriority: 2,
                        targets: -1,
                    },
                ],
                createdRow: function (row, full_data) {
                    full_data.expanded = false;
                },
                rowCallback: function () {},
                responsive: true,
                serverSide: false,
                data: vm.competitiveProcessParties,
                searching: true,
                dom:
                    "<'d-flex align-items-center'<'me-auto'l>f>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>>",
                columns: columns,
                processing: true,
            };
        },
        elementDisabled: function () {
            // Returns whether an element is disabled
            // True while processing (saving), when discarded, finalized, declined, or completed
            return (
                this.readonly ||
                this.processing ||
                this.discarded ||
                this.finalised ||
                this.declined ||
                this.completed
            );
        },
    },
    created: function () {},
    mounted: function () {
        let vm = this;
        vm.$nextTick(() => {
            vm.addEventListeners();
        });
    },
    methods: {
        addParty: async function (params) {
            let url;
            let is_person = params.type === 'person';
            let is_organisation = params.type === 'organisation';

            if (is_person) {
                for (let party of this.competitiveProcessParties) {
                    if (
                        party.is_person &&
                        party.person_id === params.party_to_add.id
                    )
                        // Person has been already added
                        return;
                }
                url = `${api_endpoints.users}${params.party_to_add.id}`;
            } else if (is_organisation) {
                for (let party of this.competitiveProcessParties) {
                    if (
                        party.is_organisation &&
                        party.organisation === params.party_to_add.id
                    )
                        // Organisation has already been added
                        return;
                }
                url = `${api_endpoints.organisations}${params.party_to_add.id}`;
            }

            await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
                .then(async (response) => {
                    if (response.ok) {
                        return await response.json();
                    } else {
                        return response.text().then((text) => {
                            throw new Error(text);
                        });
                    }
                })
                .then((data) => {
                    let new_data = {
                        id: 0, // This is competitive_process_party id.  Empty string because this is not saved yet.
                        is_person: is_person, //true,
                        is_organisation: is_organisation, // false,
                        person: is_person ? data : null, // Either a person or an organisation
                        person_id: is_person ? data.id : null,
                        organisation: is_organisation ? data : null,
                        organisation_id: is_organisation ? data.id : null,
                        invited_at: null,
                        removed_at: null,
                        party_details: [],
                        expanded: false,
                    };
                    this.$emit('add-party', new_data);
                    this.$refs.parties_datatable.vmDataTable.row
                        .add(new_data)
                        .draw();
                })
                .catch((error) => {
                    console.error(error.message);
                });

            for (let party of this.competitiveProcessParties) {
                // Somehow all the expander collapsed when adding a new row.  Accordingly set the expanded attribute to false
                party.expanded = false;
            }
        },
        openAddPartyModal: function () {
            this.$nextTick(() => {
                this.$refs.add_party.isModalOpen = true;
            });
        },
        closeModal: function () {
            this.uuid++;
        },
        number_of_columns: function () {
            // Return the number of visible columns
            let num = this.$refs.parties_datatable.vmDataTable
                .columns(':visible')
                .nodes().length;
            return num;
        },
        updateCustomRowColSpan: function () {
            // Set colspan to the manually added table row
            $('tr.' + this.expandable_row_class_name + ' td').attr(
                'colspan',
                this.number_of_columns()
            );
            // The tr padding was breaking the bounds of the containing element
            $('tr.' + this.expandable_row_class_name + ' td').addClass('p-0');
        },
        add_party_clicked: function () {
            this.openAddPartyModal();
        },
        addClickEventHandler: function () {
            let vm = this;

            vm.$refs.parties_datatable.vmDataTable.on(
                'click',
                'tr button',
                function () {
                    expandToggleParties(vm, this);
                }
            );
        },
        addResponsiveResizeHandler: function () {
            // When columns are shown/hidden, expand/collapse the child row according to the current expand-collapse status of each row
            let vm = this;
            vm.$refs.parties_datatable.vmDataTable.on(
                'responsive-resize',
                function () {
                    // This event can be used to inform external libraries and controls that Responsive has changed the visibility of columns in the table in response to a resize or recalculation event.
                    vm.updateCustomRowColSpan();
                }
            );
        },
        addEventListeners: function () {
            this.addClickEventHandler();
            this.addResponsiveResizeHandler();
        },
    },
};
</script>
