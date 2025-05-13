<template lang="html">
    <div class="container m-0 p-0">
        <div class="row">
            <div id="ledgeraccount" class="col-md-12">
                <FormSection
                    :form-collapse="collapseFormSections"
                    label="Personal Details"
                    index="personal-details"
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
                                :value="emailUser.first_name"
                                type="text"
                                class="form-control"
                                name="firstName"
                                :readonly="true"
                                required
                            />
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
                                :value="emailUser.last_name"
                                type="text"
                                class="form-control"
                                name="lastName"
                                :readonly="true"
                                required
                            />
                        </div>
                    </div>
                </FormSection>
                <FormSection
                    :form-collapse="collapseFormSections"
                    label="Address Details"
                    index="address-details"
                >
                    <form
                        v-if="emailUser.residential_address"
                        id="address-details-form"
                        class="mb-2"
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
                                            :value="
                                                emailUser.residential_address
                                                    .line1
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialAddressLine1"
                                            :readonly="true"
                                        />
                                    </div>
                                </div>
                                <div
                                    v-if="emailUser.residential_address.line2"
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
                                            :value="
                                                emailUser.residential_address
                                                    .line2
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialAddressLine2"
                                            :readonly="true"
                                        />
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
                                            :value="
                                                emailUser.residential_address
                                                    .locality
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialLocality"
                                            :readonly="true"
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
                                            :value="
                                                emailUser.residential_address
                                                    .state
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialState"
                                            :readonly="true"
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
                                            :value="
                                                emailUser.residential_address
                                                    .postcode
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialPostcode"
                                            :readonly="true"
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
                                            :value="
                                                emailUser.residential_address
                                                    .country
                                            "
                                            class="form-select"
                                            name="Country"
                                            :disabled="true"
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

                    <form
                        v-if="emailUser.postal_address"
                        class="form-horizontal mb-2"
                    >
                        <fieldset>
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
                                            :value="
                                                emailUser.postal_address.line1
                                            "
                                            :readonly="true"
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
                                            :value="
                                                emailUser.postal_address
                                                    .locality
                                            "
                                            :readonly="true"
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
                                            :value="
                                                emailUser.postal_address.state
                                            "
                                            :readonly="true"
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
                                            :value="
                                                emailUser.postal_address
                                                    .postcode
                                            "
                                            :readonly="true"
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
                                            :value="
                                                emailUser.postal_address.country
                                            "
                                            :disabled="true"
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
                </FormSection>
                <FormSection
                    :form-collapse="collapseFormSections"
                    label="Contact Details"
                    index="contact-details"
                >
                    <form id="contact-details-form">
                        <div class="row mb-2">
                            <div class="col-md-2">
                                <label for="phone" class="form-label"
                                    >Phone</label
                                >
                            </div>
                            <div class="col-md-4">
                                <input
                                    id="phone"
                                    :value="emailUser.phone_number"
                                    type="text"
                                    class="form-control"
                                    name="phone"
                                    :readonly="true"
                                    required
                                />
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
                                    :value="emailUser.mobile_number"
                                    type="text"
                                    class="form-control"
                                    name="mobile"
                                    :readonly="true"
                                    required
                                />
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
                                    :value="emailUser.email"
                                    type="email"
                                    class="form-control"
                                    name="email"
                                    :readonly="true"
                                    required
                                />
                            </div>
                        </div>
                    </form>
                </FormSection>
            </div>
        </div>
    </div>
</template>

<script>
import { utils, api_endpoints, constants } from '@/utils/hooks';
import FormSection from '@/components/forms/section_toggle.vue';

export default {
    name: 'ApplicantComponent',
    components: {
        FormSection,
    },
    props: {
        emailUser: {
            type: Object,
            required: true,
        },
        collapseFormSections: {
            type: Boolean,
            default: true,
        },
    },
    data: function () {
        return {
            countries: null,
            panelClickersInitialised: false,
        };
    },
    computed: {
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
    },
    methods: {
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
