<template lang="html">
    <div class="container m-0 p-0">
        <div class="row">
            <div id="ledgeraccount" class="col-md-12">
                <FormSection
                    :form-collapse="collapseFormSections"
                    label="Personal Details"
                    index="personal-details"
                >
                    <form
                        id="personal-details-form"
                        class="needs-validation"
                        novalidate
                    >
                        <div class="row mb-2">
                            <div class="col-md-2">
                                <label for="firstName" class="form-label"
                                    >First Name</label
                                >
                            </div>
                            <div class="col-md-4">
                                <input
                                    id="firstName"
                                    v-model="
                                        proposalApplicantComputed.first_name
                                    "
                                    type="text"
                                    class="form-control"
                                    name="firstName"
                                    :readonly="readonly"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter a first name.
                                </div>
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-2">
                                <label for="lastName" class="form-label"
                                    >Last Name</label
                                >
                            </div>
                            <div class="col-md-4">
                                <input
                                    id="lastName"
                                    v-model="
                                        proposalApplicantComputed.last_name
                                    "
                                    type="text"
                                    class="form-control"
                                    name="lastName"
                                    :readonly="readonly"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter a last name.
                                </div>
                            </div>
                        </div>
                        <div v-if="!readonly" class="col-sm-12">
                            <button
                                v-if="!updatingPersonal"
                                class="btn btn-primary float-end"
                                @click.prevent="
                                    validateForm('personal-details-form')
                                "
                            >
                                Update
                            </button>
                            <button
                                v-else
                                disabled
                                class="btn btn-primary float-end"
                            >
                                <i class="fa fa-spin fa-spinner"></i
                                >&nbsp;Updating
                            </button>
                        </div>
                    </form>
                </FormSection>
                <FormSection
                    :form-collapse="collapseFormSections"
                    label="Address Details"
                    index="address-details"
                >
                    <form
                        id="address-details-form"
                        class="needs-validation"
                        novalidate
                    >
                        <fieldset>
                            <legend>Residential Address</legend>
                            <div class="address-box">
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residentialAddressLine1"
                                            class="form-label"
                                            >Street</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="residential_line1"
                                            v-model="
                                                proposalApplicantComputed.residential_line1
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialAddressLine1"
                                            :readonly="readonly"
                                            @keyup="
                                                updatePostalAddressFromResidentialAddress
                                            "
                                        />
                                        <div class="invalid-feedback">
                                            Please enter a residential street
                                            address.
                                        </div>
                                    </div>
                                </div>
                                <div
                                    v-if="
                                        proposalApplicantComputed.residential_line2
                                    "
                                    class="row mb-2"
                                >
                                    <div class="col-md-2">
                                        <label
                                            for="residentialAddressLine2"
                                            class="form-label"
                                            >Line 2</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="residential_line2"
                                            v-model="
                                                proposalApplicantComputed.residential_line2
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialAddressLine2"
                                            :readonly="readonly"
                                            @keyup="
                                                updatePostalAddressFromResidentialAddress
                                            "
                                        />
                                        <div class="invalid-feedback">
                                            Please enter a residential street
                                            address.
                                        </div>
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residential_locality"
                                            class="form-label"
                                            >Town/Suburb</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="residential_locality"
                                            v-model="
                                                proposalApplicantComputed.residential_locality
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialLocality"
                                            :readonly="readonly"
                                            @keyup="
                                                updatePostalAddressFromResidentialAddress
                                            "
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residential_state"
                                            class="form-label"
                                            >State</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="residential_state"
                                            v-model="
                                                proposalApplicantComputed.residential_state
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialState"
                                            :readonly="readonly"
                                            @keyup="
                                                updatePostalAddressFromResidentialAddress
                                            "
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residential_postcode"
                                            class="form-label"
                                            >Postcode</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="residential_postcode"
                                            v-model="
                                                proposalApplicantComputed.residential_postcode
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialPostcode"
                                            :readonly="readonly"
                                            @keyup="
                                                updatePostalAddressFromResidentialAddress
                                            "
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residential_country"
                                            class="form-label"
                                            >Country</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <select
                                            v-if="countries"
                                            id="residential_country"
                                            v-model="
                                                proposalApplicantComputed.residential_country
                                            "
                                            class="form-select"
                                            name="Country"
                                            :disabled="readonly"
                                            @change="
                                                updatePostalAddressFromResidentialAddress
                                            "
                                        >
                                            <option
                                                v-for="c in countries"
                                                :key="c.code"
                                                :value="c.code"
                                            >
                                                {{ c.name }}
                                            </option>
                                        </select>
                                        <BootstrapSpinner
                                            v-else
                                            class="text-primary"
                                            :is-loading="true"
                                            :center-of-screen="false"
                                            :small="true"
                                        />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </form>
                    <div class="row">
                        <div class="col-md-2">&nbsp;</div>
                        <div class="col-md-6 form-check form-switch">
                            <label
                                for="postal_same_as_residential"
                                class="form-label"
                            >
                                Postal same as residential address</label
                            >
                            <input
                                id="postal_same_as_residential"
                                v-model="
                                    proposalApplicantComputed.postal_same_as_residential
                                "
                                class="form-check-input"
                                type="checkbox"
                                :disabled="readonly"
                                @change="toggleBillingAddressFieldsDisabled"
                            />
                        </div>
                    </div>

                    <form class="form-horizontal mb-2">
                        <fieldset
                            :disabled="
                                proposalApplicantComputed.postal_same_as_residential
                            "
                        >
                            <legend>Postal Address</legend>
                            <div class="address-box">
                                <div class="row mb-2">
                                    <label
                                        for="postal_line1"
                                        class="col-md-2 form-label"
                                        >Street</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_line1"
                                            v-model="
                                                proposalApplicantComputed.postal_line1
                                            "
                                            :readonly="readonly"
                                            type="text"
                                            class="form-control postal-address"
                                            name="Street"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for="postal_locality"
                                        class="col-md-2 form-label"
                                        >Town/Suburb</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_locality"
                                            v-model="
                                                proposalApplicantComputed.postal_locality
                                            "
                                            :readonly="readonly"
                                            type="text"
                                            class="form-control postal-address"
                                            name="Town/Suburb"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for="postal_state"
                                        class="col-md-2 form-label"
                                        >State</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_state"
                                            v-model="
                                                proposalApplicantComputed.postal_state
                                            "
                                            :readonly="readonly"
                                            type="text"
                                            class="form-control postal-address"
                                            name="State"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for="postal_postcode"
                                        class="col-md-2 form-label"
                                        >Postcode</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_postcode"
                                            v-model="
                                                proposalApplicantComputed.postal_postcode
                                            "
                                            :readonly="readonly"
                                            type="text"
                                            class="form-control postal-address"
                                            name="Postcode"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for="postal_country"
                                        class="col-md-2 form-label"
                                        >Country</label
                                    >
                                    <div class="col-sm-4">
                                        <select
                                            v-if="countries"
                                            id="postal_country"
                                            v-model="
                                                proposalApplicantComputed.postal_country
                                            "
                                            :disabled="readonly"
                                            class="form-select postal-address"
                                            name="Country"
                                        >
                                            <option
                                                v-for="c in countries"
                                                :key="c.code"
                                                :value="c.code"
                                            >
                                                {{ c.name }}
                                            </option>
                                        </select>
                                        <BootstrapSpinner
                                            v-else
                                            class="text-primary"
                                            :is-loading="true"
                                            :center-of-screen="false"
                                            :small="true"
                                        />
                                    </div>
                                </div>
                            </div>
                        </fieldset>
                    </form>
                    <div v-if="!readonly" class="col-sm-12">
                        <button
                            v-if="!updatingAddress"
                            class="btn btn-primary float-end"
                            @click.prevent="
                                validateForm('address-details-form')
                            "
                        >
                            Update
                        </button>
                        <button
                            v-else
                            disabled
                            class="btn btn-primary float-end"
                        >
                            <i class="fa fa-spin fa-spinner"></i>&nbsp;Updating
                        </button>
                    </div>
                </FormSection>
                <FormSection
                    :form-collapse="collapseFormSections"
                    label="Contact Details"
                    index="contact-details"
                >
                    <form
                        id="contact-details-form"
                        class="needs-validation"
                        novalidate
                    >
                        <div class="row mb-2">
                            <div class="col-md-2">
                                <label for="phone" class="form-label"
                                    >Phone</label
                                >
                            </div>
                            <div class="col-md-4">
                                <input
                                    id="phone"
                                    v-model="
                                        proposalApplicantComputed.phone_number
                                    "
                                    type="text"
                                    class="form-control"
                                    name="phone"
                                    :readonly="readonly"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter a phone number.
                                </div>
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-2">
                                <label for="mobile" class="form-label"
                                    >Mobile</label
                                >
                            </div>
                            <div class="col-md-4">
                                <input
                                    id="mobile"
                                    v-model="
                                        proposalApplicantComputed.mobile_number
                                    "
                                    type="text"
                                    class="form-control"
                                    name="mobile"
                                    :readonly="readonly"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter a mobile number.
                                </div>
                            </div>
                        </div>
                        <div class="row mb-2">
                            <div class="col-md-2">
                                <label for="email" class="form-label"
                                    >Email</label
                                >
                            </div>
                            <div class="col-md-4">
                                <input
                                    id="email"
                                    v-model="proposalApplicantComputed.email"
                                    type="email"
                                    class="form-control"
                                    name="email"
                                    :readonly="readonly"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter a valid email address.
                                </div>
                            </div>
                        </div>
                    </form>
                    <div v-if="!readonly" class="col-sm-12">
                        <button
                            v-if="!updatingContact"
                            class="btn btn-primary float-end"
                            @click.prevent="
                                validateForm('contact-details-form')
                            "
                        >
                            Update
                        </button>
                        <button
                            v-else
                            disabled
                            class="btn btn-primary float-end"
                        >
                            <i class="fa fa-spin fa-spinner"></i>&nbsp;Updating
                        </button>
                    </div>
                </FormSection>
            </div>
        </div>
    </div>
</template>

<script>
import { helpers, utils, api_endpoints, constants } from '@/utils/hooks';
import FormSection from '@/components/forms/section_toggle.vue';

export default {
    name: 'ApplicantComponent',
    components: {
        FormSection,
    },
    props: {
        proposalId: {
            type: Number,
            required: true,
        },
        customerType: {
            type: String,
            required: false,
            default: 'proponent',
        },
        proposalApplicant: {
            type: Object,
            required: true,
        },
        collapseFormSections: {
            type: Boolean,
            default: true,
        },
        readonly: {
            type: Boolean,
            default: true,
        },
    },
    emits: ['updatePropsalApplicant'],
    data: function () {
        return {
            values: null,
            countries: null,
            panelClickersInitialised: false,
            updatingPersonal: false,
            updatingAddress: false,
            updatingContact: false,
            missing_fields: [],
            showPersonalError: false,
            errorListAddress: [],
            showAddressError: false,
            errorListContact: [],
            showContactError: false,
        };
    },
    computed: {
        proposalApplicantComputed: {
            get() {
                return this.proposalApplicant;
            },
            set(value) {
                console.log(value);
                this.$emit('updatePropsalApplicant', value);
            },
        },
        customerLabel: function () {
            let label = 'Proponent';
            if (this.customerType && this.customerType === 'holder') {
                label = 'Holder';
            }
            return label;
        },
    },
    mounted: function () {
        let vm = this;
        vm.fetchCountries();
        if (!vm.panelClickersInitialised) {
            $('.panelClicker[data-toggle="collapse"]').on('click', function () {
                var chev = $(this).children()[0];
                window.setTimeout(function () {
                    $(chev).toggleClass(
                        'glyphicon-chevron-down glyphicon-chevron-up'
                    );
                }, 100);
            });
            vm.panelClickersInitialised = true;
        }
        if (vm.proposalApplicantComputed.postal_same_as_residential) {
            this.copyResidentialAddressToPostalAddress();
        }
    },
    methods: {
        copyResidentialAddressToPostalAddress: function () {
            this.proposalApplicantComputed.postal_line1 =
                this.proposalApplicantComputed.residential_line1;
            this.proposalApplicantComputed.postal_locality =
                this.proposalApplicantComputed.residential_locality;
            this.proposalApplicantComputed.postal_state =
                this.proposalApplicantComputed.residential_state;
            this.proposalApplicantComputed.postal_postcode =
                this.proposalApplicantComputed.residential_postcode;
            this.proposalApplicantComputed.postal_country =
                this.proposalApplicantComputed.residential_country;
        },
        updatePostalAddressFromResidentialAddress: function () {
            if (this.proposalApplicantComputed.postal_same_as_residential) {
                this.copyResidentialAddressToPostalAddress();
            }
        },
        toggleBillingAddressFieldsDisabled: function () {
            if (!this.proposalApplicantComputed.postal_same_as_residential) {
                $('.postal-address').first().focus();
            } else {
                this.copyResidentialAddressToPostalAddress();
            }
        },
        fetchCountries: function () {
            let vm = this;
            let url = api_endpoints.countries;
            utils
                .fetchUrl(url)
                .then((data) => {
                    vm.countries = Object.assign({}, data);
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error(`Error fetching countries data: ${error}`);
                });
        },
        validateForm: function (formId) {
            let vm = this;
            let form = document.getElementById(formId);
            if (form.checkValidity() === false) {
                form.classList.add('was-validated');
                $(`#${formId}`).find(':invalid').first().focus();
                return;
            }
            form.classList.remove('was-validated');
            if (formId === 'personal-details-form') {
                vm.updatePersonal();
            } else if (formId === 'address-details-form') {
                vm.updateAddress();
            } else if (formId === 'contact-details-form') {
                vm.updateContact();
            }
        },
        updatePersonal: function () {
            let vm = this;
            vm.updatingPersonal = true;
            console.log(vm.proposalApplicantComputed);
            const requestOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(vm.proposalApplicantComputed),
            };
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal,
                    vm.proposalId + '/update_personal'
                ),
                requestOptions
            )
                .then((response) => {
                    response.json().then(() => {
                        swal.fire(
                            'Success',
                            'Personal details updated successfully.',
                            'success'
                        );
                    });
                })
                .catch((error) => {
                    console.error(error);
                })
                .finally(() => {
                    vm.updatingPersonal = false;
                });
        },
        updateContact: function () {
            let vm = this;
            vm.updatingContact = true;
            const requestOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(vm.proposalApplicantComputed),
            };
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal,
                    vm.proposalId + '/update_contact'
                ),
                requestOptions
            )
                .then((response) => {
                    response.json().then(() => {
                        swal.fire(
                            'Success',
                            'Contact details updated successfully.',
                            'success'
                        );
                    });
                })
                .catch((error) => {
                    console.error(error);
                })
                .finally(() => {
                    vm.updatingContact = false;
                });
        },
        updateAddress: async function () {
            let vm = this;
            vm.updatingAddress = true;
            const requestOptions = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(vm.proposalApplicantComputed),
            };
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.proposal,
                    vm.proposalId + '/update_address'
                ),
                requestOptions
            )
                .then((response) => {
                    response.json().then(() => {
                        swal.fire(
                            'Success',
                            'Address details updated successfully.',
                            'success'
                        );
                    });
                })
                .catch((error) => {
                    console.error(error);
                })
                .finally(() => {
                    vm.updatingAddress = false;
                });
        },
    },
};
</script>

<style scoped>
fieldset,
legend {
    all: revert;
}

legend {
    color: grey;
}

fieldset {
    border-color: #efefef;
    border-style: solid;
}
</style>
