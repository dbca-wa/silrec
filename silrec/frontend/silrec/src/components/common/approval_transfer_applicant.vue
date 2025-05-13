<template lang="html">
    <div class="container m-0 p-0">
        <div class="row">
            <div
                v-if="approvalTransferApplicant"
                id="ledgeraccount"
                class="col-md-12"
            >
                <FormSection label="Personal Details" index="personal-details">
                    <form>
                        <alert
                            v-if="showPersonalError"
                            type="danger"
                            style="color: red"
                            ><div v-for="item in errorListPersonal" :key="item">
                                <strong>{{ item }}</strong>
                            </div></alert
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
                                        approvalTransferApplicantComputed.first_name
                                    "
                                    type="text"
                                    class="form-control"
                                    name="firstName"
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
                                    v-model="
                                        approvalTransferApplicantComputed.last_name
                                    "
                                    type="text"
                                    class="form-control"
                                    name="lastName"
                                />
                            </div>
                        </div>
                        <div class="col-sm-12">
                            <button
                                v-if="!updatingPersonal"
                                class="btn btn-primary float-end"
                                @click.prevent="
                                    $emit(
                                        'saveApprovalTransferApplicant',
                                        approvalTransferApplicantComputed
                                    )
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
                <FormSection label="Address Details" index="address-details">
                    <form class="form-horizontal mb-2">
                        <alert
                            v-if="showAddressError"
                            type="danger"
                            style="color: red"
                            ><div v-for="item in errorListAddress" :key="item">
                                <strong>{{ item }}</strong>
                            </div></alert
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
                                            id="line1"
                                            v-model="
                                                approvalTransferApplicantComputed.residential_line1
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialAddressLine1"
                                        />
                                    </div>
                                </div>
                                <div
                                    v-if="
                                        approvalTransferApplicantComputed.residential_line2
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
                                            id="line1"
                                            v-model="
                                                approvalTransferApplicantComputed.residential_line2
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialAddressLine2"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residentialLocality"
                                            class="form-label"
                                            >Town/Suburb</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="locality"
                                            v-model="
                                                approvalTransferApplicantComputed.residential_locality
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialLocality"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residentialState"
                                            class="form-label"
                                            >State</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="state"
                                            v-model="
                                                approvalTransferApplicantComputed.residential_state
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialState"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residentialPostcode"
                                            class="form-label"
                                            >Postcode</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <input
                                            id="postcode"
                                            v-model="
                                                approvalTransferApplicantComputed.residential_postcode
                                            "
                                            type="text"
                                            class="form-control"
                                            name="residentialPostcode"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-2">
                                        <label
                                            for="residentialPostcode"
                                            class="form-label"
                                            >Country</label
                                        >
                                    </div>
                                    <div class="col-md-4">
                                        <select
                                            v-if="countries"
                                            id="country"
                                            v-model="
                                                approvalTransferApplicantComputed.residential_country
                                            "
                                            class="form-select"
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
                                    approvalTransferApplicantComputed.postal_same_as_residential
                                "
                                class="form-check-input"
                                type="checkbox"
                                @change="togglePostal"
                            />
                        </div>
                    </div>

                    <form class="form-horizontal mb-2">
                        <fieldset
                            :disabled="
                                approvalTransferApplicantComputed.postal_same_as_residential
                            "
                        >
                            <legend>Postal Address</legend>
                            <div class="address-box">
                                <div class="row mb-2">
                                    <label for="" class="col-md-2 form-label"
                                        >Street</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_line1"
                                            v-model="
                                                approvalTransferApplicantComputed.postal_line1
                                            "
                                            type="text"
                                            class="form-control postal-address"
                                            name="Street"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label for="" class="col-md-2 form-label"
                                        >Town/Suburb</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_locality"
                                            v-model="
                                                approvalTransferApplicantComputed.postal_locality
                                            "
                                            type="text"
                                            class="form-control postal-address"
                                            name="Town/Suburb"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label for="" class="col-md-2 form-label"
                                        >State</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_state"
                                            v-model="
                                                approvalTransferApplicantComputed.postal_state
                                            "
                                            type="text"
                                            class="form-control postal-address"
                                            name="State"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label for="" class="col-md-2 form-label"
                                        >Postcode</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="postal_postcode"
                                            v-model="
                                                approvalTransferApplicantComputed.postal_postcode
                                            "
                                            type="text"
                                            class="form-control postal-address"
                                            name="Postcode"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label for="" class="col-md-2 form-label"
                                        >Country</label
                                    >
                                    <div class="col-sm-4">
                                        <select
                                            v-if="countries"
                                            id="postal_country"
                                            v-model="
                                                approvalTransferApplicantComputed.postal_country
                                            "
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
                    <div class="col-sm-12">
                        <button
                            v-if="!updatingAddress"
                            class="btn btn-primary float-end"
                            @click.prevent="
                                $emit(
                                    'saveApprovalTransferApplicant',
                                    approvalTransferApplicantComputed
                                )
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
                <FormSection label="Contact Details" index="contact-details">
                    <form>
                        <alert
                            v-if="showContactError"
                            type="danger"
                            style="color: red"
                            ><div v-for="item in errorListContact" :key="item">
                                <strong>{{ item }}</strong>
                            </div></alert
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
                                        approvalTransferApplicantComputed.phone_number
                                    "
                                    type="text"
                                    class="form-control"
                                    name="phone"
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
                                    v-model="
                                        approvalTransferApplicantComputed.mobile_number
                                    "
                                    type="text"
                                    class="form-control"
                                    name="mobile"
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
                                    v-model="
                                        approvalTransferApplicantComputed.email
                                    "
                                    type="text"
                                    class="form-control"
                                    name="email"
                                />
                            </div>
                        </div>
                    </form>
                    <div class="col-sm-12">
                        <button
                            v-if="!updatingContact"
                            class="btn btn-primary float-end"
                            @click.prevent="
                                $emit(
                                    'saveApprovalTransferApplicant',
                                    approvalTransferApplicantComputed
                                )
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
import { utils, api_endpoints, constants } from '@/utils/hooks';
import { v4 as uuid } from 'uuid';
import FormSection from '@/components/forms/section_toggle.vue';
import alert from '@vue-utils/alert.vue';

export default {
    name: 'ApprovalTransferApplicant',
    components: {
        FormSection,
        alert,
    },
    props: {
        approvalTransferApplicant: {
            type: Object,
            required: true,
        },
    },
    emits: ['updateApprovalTransferApplicant', 'saveApprovalTransferApplicant'],
    data: function () {
        return {
            values: null,
            countries: null,
            detailsBody: 'detailsBody' + uuid(),
            addressBody: 'addressBody' + uuid(),
            contactsBody: 'contactsBody' + uuid(),
            panelClickersInitialised: false,
            updatingPersonal: false,
            updatingAddress: false,
            updatingContact: false,
            missing_fields: [],
            errorListPersonal: [],
            showPersonalError: false,
            errorListAddress: [],
            showAddressError: false,
            errorListContact: [],
            showContactError: false,
        };
    },
    computed: {
        approvalTransferApplicantComputed: {
            get() {
                return this.approvalTransferApplicant;
            },
            set(value) {
                this.$emit('updateApprovalTransferApplicant', value);
            },
        },
    },
    mounted: function () {
        this.fetchCountries();
    },
    methods: {
        togglePostal: function () {
            if (!this.approvalTransferApplicant.postal_same_as_residential) {
                $('.postal-address').first().focus();
            } else {
                this.approvalTransferApplicantComputed.postal_line1 =
                    this.approvalTransferApplicantComputed.residential_line1;
                this.approvalTransferApplicantComputed.postal_line2 =
                    this.approvalTransferApplicantComputed.residential_line2;
                this.approvalTransferApplicantComputed.postal_line3 =
                    this.approvalTransferApplicantComputed.residential_line3;
                this.approvalTransferApplicantComputed.postal_locality =
                    this.approvalTransferApplicantComputed.residential_locality;
                this.approvalTransferApplicantComputed.postal_state =
                    this.approvalTransferApplicantComputed.residential_state;
                this.approvalTransferApplicantComputed.postal_country =
                    this.approvalTransferApplicantComputed.residential_country;
                this.approvalTransferApplicantComputed.postal_postcode =
                    this.approvalTransferApplicantComputed.residential_postcode;
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

        updateApprovalTransferApplicant: function () {},
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
