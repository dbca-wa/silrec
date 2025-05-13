<template>
    <FormSection :form-collapse="false" label="Details" index="details">
        <form>
            <div class="row mb-2">
                <label
                    for="ledger_organisation_name"
                    class="col-md-2 col-form-label"
                    >Organisation Name</label
                >
                <div class="col-md-6">
                    <input
                        id="ledger_organisation_name"
                        v-model="org.ledger_organisation_name"
                        type="text"
                        class="form-control"
                        :readonly="readonly"
                    />
                </div>
            </div>
            <div
                v-if="
                    org.ledger_organisation_trading_name &&
                    org.ledger_organisation_trading_name !=
                        org.ledger_organisation_name
                "
                class="row mb-2"
            >
                <label
                    for="ledger_organisation_trading_name"
                    class="col-md-2 col-form-label"
                    >Trading Name</label
                >
                <div class="col-md-6">
                    <input
                        id="ledger_organisation_trading_name"
                        v-model="org.ledger_organisation_trading_name"
                        type="text"
                        class="form-control"
                        :readonly="readonly"
                    />
                </div>
            </div>
            <div class="row mb-2">
                <label
                    for="ledger_organisation_abn"
                    class="col-md-2 col-form-label"
                    >ABN</label
                >
                <div class="col-md-6">
                    <input
                        id="ledger_organisation_abn"
                        v-model="org.ledger_organisation_abn"
                        type="text"
                        class="form-control"
                        :readonly="readonly"
                    />
                </div>
            </div>
            <div class="row mb-2">
                <label
                    for="ledger_organisation_email"
                    class="col-md-2 col-form-label"
                    >Email</label
                >
                <div class="col-md-6">
                    <input
                        id="ledger_organisation_email"
                        v-model="org.ledger_organisation_email"
                        type="text"
                        class="form-control"
                        :readonly="readonly"
                    />
                </div>
            </div>
            <div v-if="!isInternal" class="row mb2">
                <div class="col">
                    <a
                        role="button"
                        target="_blank"
                        :href="'/external/organisations/manage/' + org.id"
                        class="btn btn-primary float-end"
                        ><i class="fa fa-external-link" aria-hidden="true"></i>
                        Update Organisation Details</a
                    >
                </div>
            </div>
        </form>
    </FormSection>
    <FormSection
        v-if="orgHasAddress"
        :form-collapse="false"
        label="Address Details"
        index="addressdetails"
    >
        <form v-if="org.address.postal_address">
            <fieldset>
                <legend>Postal Address</legend>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label">Street</label>
                    <div class="col-sm-6">
                        <input
                            v-model="org.address.postal_address.line1"
                            type="text"
                            class="form-control"
                            name="street"
                            :readonly="readonly"
                        />
                    </div>
                </div>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label"
                        >Town/Suburb</label
                    >
                    <div class="col-sm-6">
                        <input
                            v-model="org.address.postal_address.locality"
                            type="text"
                            class="form-control"
                            name="surburb"
                            :readonly="readonly"
                        />
                    </div>
                </div>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label">State</label>
                    <div class="col-sm-2">
                        <input
                            v-model="org.address.postal_address.state"
                            type="text"
                            class="form-control"
                            name="country"
                            :readonly="readonly"
                        />
                    </div>
                    <label for="" class="col-sm-2 col-form-label"
                        >Postcode</label
                    >
                    <div class="col-sm-2">
                        <input
                            v-model="org.address.postal_address.postcode"
                            type="text"
                            class="form-control"
                            name="postcode"
                            :readonly="readonly"
                        />
                    </div>
                </div>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label"
                        >Country</label
                    >
                    <div class="col-sm-4">
                        <select
                            v-model="org.address.postal_address.country"
                            class="form-control"
                            name="country"
                            :disabled="readonly"
                        >
                            <option
                                v-for="c in countries"
                                :key="c.code"
                                :value="c.code"
                            >
                                {{ c.name }}
                            </option>
                        </select>
                    </div>
                </div>
            </fieldset>
        </form>

        <form v-if="org.address.billing_address">
            <fieldset>
                <legend>Billing Address</legend>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label">Street</label>
                    <div class="col-sm-6">
                        <input
                            v-model="org.address.billing_address.line1"
                            type="text"
                            class="form-control"
                            name="street"
                            :readonly="readonly"
                        />
                    </div>
                </div>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label"
                        >Town/Suburb</label
                    >
                    <div class="col-sm-6">
                        <input
                            v-model="org.address.billing_address.locality"
                            type="text"
                            class="form-control"
                            name="surburb"
                            :readonly="readonly"
                        />
                    </div>
                </div>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label">State</label>
                    <div class="col-sm-2">
                        <input
                            v-model="org.address.billing_address.state"
                            type="text"
                            class="form-control"
                            name="country"
                            :readonly="readonly"
                        />
                    </div>
                    <label for="" class="col-sm-2 col-form-label"
                        >Postcode</label
                    >
                    <div class="col-sm-2">
                        <input
                            v-model="org.address.billing_address.postcode"
                            type="text"
                            class="form-control"
                            name="postcode"
                            :readonly="readonly"
                        />
                    </div>
                </div>
                <div class="row mb-2">
                    <label for="" class="col-sm-2 col-form-label"
                        >Country</label
                    >
                    <div class="col-sm-4">
                        <select
                            v-model="org.address.billing_address.country"
                            class="form-control"
                            name="country"
                            :disabled="readonly"
                        >
                            <option
                                v-for="c in countries"
                                :key="c.code"
                                :value="c.code"
                            >
                                {{ c.name }}
                            </option>
                        </select>
                    </div>
                </div>
            </fieldset>
        </form>
    </FormSection>

    <FormSection :form-collapse="false" label="Contacts" index="contacts">
        <TableOrganisationContacts
            ref="organisation_contacts"
            :organisation-id="org.id ? org.id : null"
            :level="isInternal ? 'internal' : 'external'"
        />
    </FormSection>
</template>

<script>
import { helpers, utils, api_endpoints } from '@/utils/hooks';
import FormSection from '@/components/forms/section_toggle.vue';
import TableOrganisationContacts from '@/components/common/table_organisation_contacts.vue';

export default {
    name: 'OrganisationApplicant',
    components: {
        TableOrganisationContacts,
        FormSection,
    },
    props: {
        org: {
            type: Object,
            default: null,
        },
        readonly: {
            type: Boolean,
            default: true,
        },
        isInternal: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            loading: [],
            countries: [],
        };
    },
    computed: {
        isLoading: function () {
            return this.loading.length == 0;
        },
        formattedABN: function () {
            if (
                this.org.ledger_organisation_abn == null ||
                this.org.ledger_organisation_abn == ''
            ) {
                return '';
            }
            return helpers.formatABN(this.org.ledger_organisation_abn);
        },
        orgHasAddress: function () {
            return (
                this.org &&
                this.org.address &&
                (Object.keys(this.org.address['postal_address']).length !== 0 ||
                    Object.keys(this.org.address['billing_address']).length !==
                        0)
            );
        },
    },
    created: function () {},
    mounted: function () {
        let vm = this;
        vm.fetchCountries();
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
                    console.error(`Error fetching countries data ${error}`);
                });
        },
    },
};
</script>

<style scoped>
.top-buffer-s {
    margin-top: 10px;
}

.actionBtn {
    cursor: pointer;
}

.hidePopover {
    display: none;
}

.discount {
    width: 100px;
}

.row-waiver {
    height: 32px;
}

.badge {
    cursor: pointer;
}
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
