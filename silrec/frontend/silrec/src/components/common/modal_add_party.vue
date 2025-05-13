<template lang="html">
    <div id="modal_add_party">
        <Modal
            ref="modal_add_party"
            transition="modal fade"
            title="Add Party"
            ok-text="Add"
            large
            :ok-disabled="disableOkButton"
            @ok="okClicked"
            @cancel="cancel"
        >
            <div class="container-fluid">
                <div class="row mb-3">
                    <div class="col-sm-3">
                        <label class="form-label">Add party</label>
                    </div>
                    <div class="col-sm-9">
                        <div class="form-check form-check-inline">
                            <input
                                id="inlineRadio2"
                                v-model="type_to_add"
                                class="form-check-input"
                                type="radio"
                                name="inlineRadioOptions"
                                value="organisation"
                                checked
                            />
                            <label class="form-check-label" for="inlineRadio2"
                                >Organisation</label
                            >
                        </div>
                        <div class="form-check form-check-inline">
                            <input
                                id="inlineRadio1"
                                v-model="type_to_add"
                                class="form-check-input"
                                type="radio"
                                name="inlineRadioOptions"
                                value="person"
                            />
                            <label class="form-check-label" for="inlineRadio1"
                                >Person</label
                            >
                        </div>
                    </div>
                </div>
                <div v-show="type_to_add == 'person'" class="row mb-3">
                    <div class="col-sm-3">
                        <label class="form-label">Person</label>
                    </div>
                    <div class="col-sm-7">
                        <select
                            id="select_email_users"
                            ref="email_users"
                            class="form-select"
                            aria-label="Select person to add"
                            :disabled="false"
                        >
                            <option value="null"></option>
                            <option
                                v-for="user in email_users"
                                :key="user.id"
                                :value="user.email"
                            >
                                {{ user.name }}
                            </option>
                        </select>
                    </div>
                </div>
                <div v-show="type_to_add == 'organisation'" class="row mb-3">
                    <div class="col-sm-3">
                        <label class="form-label">Organisation</label>
                    </div>
                    <div class="col-sm-7">
                        <select
                            id="select_organisations"
                            ref="organisations"
                            class="form-select"
                            aria-label="Select organisation to add"
                            :disabled="false"
                        >
                            <option value="null"></option>
                            <option
                                v-for="organisation in organisations"
                                :key="organisation.id"
                                :value="organisation.email"
                            >
                                {{ organisation.name }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>
        </Modal>
    </div>
</template>

<script>
import Modal from '@vue-utils/bootstrap-modal.vue';
import { api_endpoints } from '@/utils/hooks.js';

export default {
    name: 'AddParty',
    components: {
        Modal,
    },
    props: {},
    emits: ['partyToAdd', 'closeModal'],
    data: function () {
        return {
            isModalOpen: false,
            errorString: '',
            successString: '',
            success: false,
            saving: false,

            type_to_add: 'organisation',
            // Person
            email_users: [],
            selected_email_user: null,

            // Organisation
            organisations: [],
            selected_organisation: null,
        };
    },
    computed: {
        disableOkButton: function () {
            let disabled = true;
            if (this.selected_email_user || this.selected_organisation) {
                disabled = false;
            }
            return disabled;
        },
    },
    watch: {
        isModalOpen: function (newVal) {
            if (newVal) {
                this.$nextTick(() => {
                    $(this.$refs.organisations).select2('open');
                });
            }
        },
        type_to_add: function (newVal) {
            if (newVal == 'person') {
                this.$nextTick(() => {
                    $(this.$refs.email_users).select2('open');
                });
            } else {
                this.$nextTick(() => {
                    $(this.$refs.organisations).select2('open');
                });
            }
        },
    },
    mounted: function async() {
        let vm = this;
        vm.$nextTick(async () => {
            vm.initialiseSelectPerson();
            vm.initialiseSelectOrganisation();
        });
    },
    methods: {
        initialiseSelectPerson: function () {
            let vm = this;
            $(vm.$refs.email_users)
                .select2({
                    dropdownParent: $('#modal_add_party .modal'),
                    minimumInputLength: 2,
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder: 'Start typing to find a Person (Esc to close)',
                    ajax: {
                        url: api_endpoints.person_lookup,
                        dataType: 'json',
                        data: function (params) {
                            var query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
                        },
                        processResults: function (data) {
                            return data;
                        },
                    },
                })
                .on('select2:select', function (e) {
                    vm.selected_email_user = e.params.data;
                })
                .on('select2:unselect', function () {
                    vm.selected_email_user = null;
                })
                .empty()
                .trigger('change');
        },
        initialiseSelectOrganisation: function () {
            let vm = this;
            $(vm.$refs.organisations)
                .select2({
                    dropdownParent: $('#modal_add_party .modal'),
                    minimumInputLength: 2,
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder:
                        'Start typing to find an Organisation (Esc to close)',
                    ajax: {
                        url: api_endpoints.organisation_lookup,
                        dataType: 'json',
                        data: function (params) {
                            var query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
                        },
                        processResults: function (data) {
                            return data;
                        },
                    },
                })
                .on('select2:select', function (e) {
                    let data = e.params.data;
                    vm.selected_organisation = data;
                })
                .on('select2:unselect', function () {
                    vm.selected_organisation = null;
                })
                .empty()
                .trigger('change');
        },
        okClicked: function () {
            let party_to_add = null;
            if (this.type_to_add === 'person') {
                party_to_add = this.selected_email_user;
            } else if (this.type_to_add === 'organisation') {
                party_to_add = this.selected_organisation;
            }
            if (party_to_add) {
                this.$emit('partyToAdd', {
                    // Issue an event with type and person/organisation
                    type: this.type_to_add,
                    party_to_add: party_to_add,
                });
            }
            this.close();
        },
        cancel: function () {
            this.close();
        },
        close: function () {
            this.selected_email_user = null;
            this.selected_organisation = null;
            $(this.$refs.email_users).empty();
            $(this.$refs.organisations).empty();
            this.type_to_add = 'organisation';
            this.isModalOpen = false;
            $('.has-error').removeClass('has-error');
            this.$emit('closeModal');
        },
    },
};
</script>
