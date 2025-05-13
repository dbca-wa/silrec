<template lang="html">
    <div id="add-contact">
        <modal :title="title()" large @ok="validateForm">
            <form
                id="addContactForm"
                class="needs-validation form-horizontal"
                name="addContactForm"
                novalidate
            >
                <div class="row">
                    <alert
                        v-if="errorString && errorString.length > 0"
                        type="danger"
                        ><strong>{{ errorString }}</strong></alert
                    >
                    <div class="col-lg-12 ps-5 pe-5">
                        <div class="row mb-3 mt-3">
                            <label
                                for="first_name"
                                class="col-sm-3 col-form-label"
                                >Given Name(s):
                            </label>
                            <div class="col-sm-9">
                                <input
                                    id="first_name"
                                    ref="first_name"
                                    v-model="contact.first_name"
                                    type="text"
                                    class="form-control"
                                    name="first_name"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter your given names.
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <label
                                for="last_name"
                                class="col-sm-3 col-form-label"
                                >Last Name</label
                            >
                            <div class="col-sm-9">
                                <input
                                    v-model="contact.last_name"
                                    type="text"
                                    class="form-control"
                                    name="last_name"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter your last name.
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <label for="phone" class="col-sm-3 col-form-label"
                                >Phone
                            </label>
                            <div class="col-sm-9">
                                <input
                                    id="phone_number"
                                    v-model="contact.phone_number"
                                    type="text"
                                    class="form-control"
                                    name="phone"
                                    pattern="\d*"
                                    @keyup="validatePhoneNumbers"
                                />
                                <div class="invalid-feedback">
                                    Please enter a valid phone number or mobile
                                    number.
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <label for="mobile" class="col-sm-3 col-form-label"
                                >Mobile
                            </label>
                            <div class="col-sm-9">
                                <input
                                    id="mobile_number"
                                    v-model="contact.mobile_number"
                                    type="text"
                                    class="form-control"
                                    name="mobile"
                                    pattern="\d*"
                                    @keyup="validatePhoneNumbers"
                                />
                                <div class="invalid-feedback">
                                    Please enter a valid mobile number or phone
                                    number.
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <label for="fax" class="col-sm-3 col-form-label"
                                >Fax
                            </label>
                            <div class="col-sm-9">
                                <input
                                    id="fax_number"
                                    v-model="contact.fax_number"
                                    type="text"
                                    class="form-control"
                                    name="fax"
                                />
                                <div class="invalid-feedback">
                                    Please enter a valid fax number.
                                </div>
                            </div>
                        </div>

                        <div class="row mb-3">
                            <label for="email" class="col-sm-3 col-form-label"
                                >Email
                            </label>
                            <div class="col-sm-9">
                                <input
                                    v-model="contact.email"
                                    type="email"
                                    class="form-control"
                                    name="email"
                                    required
                                    pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$"
                                />
                                <div class="invalid-feedback">
                                    Please enter a valid email address.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import alert from '@vue-utils/alert.vue';
import { helpers, api_endpoints } from '@/utils/hooks.js';
export default {
    name: 'AddOrganisationContact',
    components: {
        modal,
        alert,
    },
    props: {
        org_id: {
            type: Number,
            required: true,
        },
    },
    data: function () {
        return {
            isModalOpen: false,
            form: null,
            contact: {},
            errorString: '',
            successString: '',
            success: false,
        };
    },
    mounted: function () {
        let vm = this;
        vm.form = document.forms.addContactForm;
    },
    methods: {
        title: function () {
            let vm = this;
            if (vm.contact.id) {
                return 'Update Contact';
            }
            return 'Add Contact';
        },
        close: function () {
            this.isModalOpen = false;
            this.contact = {};
            this.errorString = '';
            this.form.reset();
            this.form.classList.remove('was-validated');
        },
        fetchContact: function (id) {
            let vm = this;
            vm.$http.get(api_endpoints.contact(id)).then(
                (response) => {
                    vm.contact = response.body;
                    vm.isModalOpen = true;
                },
                (error) => {
                    console.error(error);
                }
            );
        },
        validatePhoneNumbers: function () {
            let vm = this;
            var form = document.getElementById('addContactForm');
            if (
                (!vm.contact.phone_number && !vm.contact.mobile_number) ||
                (vm.contact.phone_number.trim() == '' &&
                    vm.contact.mobile_number.trim() == '')
            ) {
                form.phone_number.setCustomValidity(
                    'Please enter a valid phone number or mobile number.'
                );
                form.mobile_number.setCustomValidity(
                    'Please enter a valid mobile number or phone number.'
                );
                form.checkValidity();
                form.classList.add('was-validated');
                $('#addContactForm').find(':invalid').first().focus();
                return false;
            }
            form.phone_number.setCustomValidity('');
            form.mobile_number.setCustomValidity('');
            return true;
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById('addContactForm');

            if (!vm.validatePhoneNumbers()) {
                return;
            }

            if (form.checkValidity()) {
                vm.sendData();
            } else {
                form.classList.add('was-validated');
                $('#addContactForm').find(':invalid').first().focus();
            }

            return false;
        },
        sendData: function () {
            let vm = this;
            vm.errorsString = '';
            if (vm.contact.id) {
                const requestOptions = {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(vm.contact),
                };
                fetch(
                    helpers.add_endpoint_json(
                        api_endpoints.organisation_contacts,
                        vm.contact.id
                    ),
                    requestOptions
                ).then(
                    () => {
                        vm.$parent.refreshDatatable();
                        vm.close();
                    },
                    (error) => {
                        console.error(error);
                        vm.errorString = helpers.apiVueResourceError(error);
                    }
                );
            } else {
                vm.contact.organisation = vm.org_id;
                vm.contact.user_status = 'contact_form';
                const requestOptions = {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(vm.contact),
                };
                fetch(api_endpoints.organisation_contacts, requestOptions)
                    .then(async (response) => {
                        if (!response.ok) {
                            const json = await response.json();
                            vm.errorString = json.errors[0].detail;
                            return;
                        }
                        vm.$parent.addedContact();
                        vm.close();
                    })
                    .catch((error) => {
                        console.error(error);
                        vm.errorString = helpers.apiVueResourceError(error);
                    });
            }
        },
    },
};
</script>
