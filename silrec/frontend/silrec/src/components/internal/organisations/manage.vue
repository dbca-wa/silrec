<template>
    <div id="internalOrgInfo" class="container">
        <div v-if="org" class="row">
            <h3>{{ organisation_name }} [ABN: {{ formattedABN }}]</h3>
            <div class="col-md-3">
                <CommsLogs
                    :comms_url="comms_url"
                    :logs_url="logs_url"
                    :comms_add_url="comms_add_url"
                    :disable_add_entry="false"
                />
            </div>
            <div class="col-md-9">
                <ul id="pills-tab" class="nav nav-pills" role="tablist">
                    <li class="nav-item">
                        <a
                            id="pills-details-tab"
                            class="nav-link active"
                            data-bs-toggle="pill"
                            href="#pills-details"
                            role="tab"
                            aria-controls="pills-details"
                            aria-selected="true"
                            >Details</a
                        >
                    </li>
                    <li class="nav-item">
                        <a
                            id="pills-other-tab"
                            class="nav-link"
                            data-bs-toggle="pill"
                            href="#pills-other"
                            role="tab"
                            aria-controls="pills-other"
                            aria-selected="false"
                            >Other</a
                        >
                    </li>
                </ul>
                <div class="tab-content">
                    <div
                        id="pills-details"
                        class="tab-pane active"
                        role="tabpanel"
                        aria-labelledby="pills-applications-tab"
                    >
                        <FormSection
                            :form-collapse="false"
                            label="Organisation Details"
                            index="details"
                        >
                            <form
                                id="organisation-details-form"
                                class="needs-validation"
                                novalidate
                                @submit.prevent="
                                    validateForm('organisation-details-form')
                                "
                            >
                                <div class="row mb-2">
                                    <label
                                        for="ledger_organisation_name"
                                        class="col-sm-3 control-label"
                                        >Name</label
                                    >
                                    <div class="col-sm-9">
                                        <input
                                            id="ledger_organisation_name"
                                            v-model="
                                                org.ledger_organisation_name
                                            "
                                            type="text"
                                            class="form-control"
                                            name="ledger_organisation_name"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please enter an organisation name
                                        </div>
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for="ledger_organisation_trading_name"
                                        class="col-sm-3 control-label"
                                        >Trading Name</label
                                    >
                                    <div class="col-sm-9">
                                        <input
                                            id="ledger_organisation_trading_name"
                                            v-model="
                                                org.ledger_organisation_trading_name
                                            "
                                            type="text"
                                            class="form-control"
                                            name="ledger_organisation_trading_name"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for="ledger_organisation_abn"
                                        class="col-md-3 control-label"
                                        >ABN</label
                                    >
                                    <div class="col-md-4">
                                        <input
                                            id="ledger_organisation_abn"
                                            v-model="
                                                org.ledger_organisation_abn
                                            "
                                            type="text"
                                            class="form-control"
                                            name="ledger_organisation_abn"
                                            placeholder=""
                                        />
                                        <div class="invalid-feedback">
                                            Please enter an organisation ABN,
                                            ACN (Or other identifier for
                                            international organisations)
                                        </div>
                                    </div>
                                </div>
                                <div class="row mb-4">
                                    <label
                                        for="ledger_organisation_email"
                                        class="col-sm-3 control-label"
                                        >Email</label
                                    >
                                    <div class="col-sm-6">
                                        <input
                                            id="ledger_organisation_email"
                                            v-model="
                                                org.ledger_organisation_email
                                            "
                                            type="email"
                                            class="form-control"
                                            name="ledger_organisation_email"
                                            placeholder=""
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please enter a valid email address
                                        </div>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col">
                                        <button
                                            class="btn btn-primary float-end"
                                        >
                                            Update
                                        </button>
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
                            <form
                                id="organisation-address-form"
                                class="needs-validation"
                                novalidate
                                @submit.prevent="
                                    validateForm('organisation-address-form')
                                "
                            >
                                <fieldset class="mb-3">
                                    <legend>Postal Address</legend>

                                    <div class="row mb-2">
                                        <label
                                            for="street"
                                            class="col-sm-3 control-label"
                                            >Street</label
                                        >
                                        <div class="col-sm-6">
                                            <input
                                                id="street"
                                                v-model="
                                                    org.address.postal_address
                                                        .line1
                                                "
                                                type="text"
                                                class="form-control"
                                                name="street"
                                                placeholder=""
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a street address
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <label
                                            for="suburb"
                                            class="col-sm-3 control-label"
                                            >Town/Suburb</label
                                        >
                                        <div class="col-sm-6">
                                            <input
                                                id="suburb"
                                                v-model="
                                                    org.address.postal_address
                                                        .locality
                                                "
                                                type="text"
                                                class="form-control"
                                                name="suburb"
                                                placeholder=""
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a town or suburb
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <label
                                            for="state"
                                            class="col-sm-3 control-label"
                                            >State</label
                                        >
                                        <div class="col-sm-2">
                                            <input
                                                id="state"
                                                v-model="
                                                    org.address.postal_address
                                                        .state
                                                "
                                                type="text"
                                                class="form-control"
                                                name="state"
                                                placeholder=""
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a state
                                            </div>
                                        </div>
                                        <label
                                            for="postcode"
                                            class="col-sm-2 control-label"
                                            >Postcode</label
                                        >
                                        <div class="col-sm-2">
                                            <input
                                                id="postcode"
                                                v-model="
                                                    org.address.postal_address
                                                        .postcode
                                                "
                                                type="text"
                                                class="form-control"
                                                name="postcode"
                                                placeholder=""
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a postcode
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <label
                                            for="country"
                                            class="col-sm-3 control-label"
                                            >Country</label
                                        >
                                        <div class="col-sm-4">
                                            <select
                                                id="country"
                                                v-model="
                                                    org.address.postal_address
                                                        .country
                                                "
                                                class="form-select"
                                                name="country"
                                                @change="
                                                    updatePostalAddressFromBillingAddress
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
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <div class="col-sm-3">&nbsp;</div>
                                        <div class="col-sm-6">
                                            <div class="form-check form-switch">
                                                <label
                                                    for="billingPostcodeSame"
                                                    class="form-label"
                                                >
                                                    Billing Address same as
                                                    Postal Address</label
                                                >
                                                <input
                                                    id="toggleBillingAddressFieldsDisabled"
                                                    v-model="
                                                        org.billing_same_as_postal
                                                    "
                                                    class="form-check-input"
                                                    type="checkbox"
                                                    @change="
                                                        toggleBillingAddressFieldsDisabled
                                                    "
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </fieldset>
                                <fieldset
                                    class="mb-3"
                                    :disabled="org.billing_same_as_postal"
                                >
                                    <legend>Billing Address</legend>

                                    <div class="row mb-2">
                                        <label
                                            for="billing-street"
                                            class="col-sm-3 control-label"
                                            >Street</label
                                        >
                                        <div class="col-sm-6">
                                            <input
                                                id="billing-street"
                                                v-model="
                                                    org.address.billing_address
                                                        .line1
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billing-street"
                                                placeholder=""
                                                required
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a street address
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <label
                                            for="billing-suburb"
                                            class="col-sm-3 control-label"
                                            >Town/Suburb</label
                                        >
                                        <div class="col-sm-6">
                                            <input
                                                id="billing-suburb"
                                                v-model="
                                                    org.address.billing_address
                                                        .locality
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billing-suburb"
                                                placeholder=""
                                                required
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a town or suburb
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <label
                                            for="billing-state"
                                            class="col-sm-3 control-label"
                                            >State</label
                                        >
                                        <div class="col-sm-2">
                                            <input
                                                id="billing-state"
                                                v-model="
                                                    org.address.billing_address
                                                        .state
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billing-state"
                                                placeholder=""
                                                required
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a state
                                            </div>
                                        </div>
                                        <label
                                            for="billing-postcode"
                                            class="col-sm-2 control-label"
                                            >Postcode</label
                                        >
                                        <div class="col-sm-2">
                                            <input
                                                id="billing-postcode"
                                                v-model="
                                                    org.address.billing_address
                                                        .postcode
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billing-postcode"
                                                placeholder=""
                                                required
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a postcode
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <label
                                            for="billing-country"
                                            class="col-sm-3 control-label"
                                            >Country</label
                                        >
                                        <div class="col-sm-4">
                                            <select
                                                id="billing-country"
                                                v-model="
                                                    org.address.billing_address
                                                        .country
                                                "
                                                class="form-select billing-address"
                                                name="billing-country"
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
                                <div class="row">
                                    <div class="col">
                                        <button
                                            class="btn btn-primary float-end"
                                        >
                                            Update
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </FormSection>

                        <FormSection
                            :form-collapse="false"
                            label="Contacts"
                            index="contacts"
                        >
                            <TableOrganisationContacts
                                ref="organisation_contacts_datatable"
                                :organisation-id="org.id"
                                level="internal"
                            />
                        </FormSection>
                        <FormSection
                            :form-collapse="false"
                            label="Linked User Accounts"
                            index="linkeduseraccounts"
                        >
                            <form class="form-horizontal">
                                <div class="col-sm-12">
                                    <div class="row">
                                        <div class="col-sm-12">
                                            <p class="fs-6">
                                                Users linked to this
                                                organisation:
                                            </p>
                                        </div>
                                        <div class="mb-3">
                                            <ul
                                                v-if="
                                                    org.delegates &&
                                                    org.delegates.length
                                                "
                                                class="ms-0 ps-0"
                                            >
                                                <span
                                                    v-for="d in org.delegates"
                                                    :key="d.user"
                                                    :class="
                                                        'organisation_admin' ==
                                                        d.user_role
                                                            ? 'bg-primary'
                                                            : 'bg-secondary'
                                                    "
                                                    class="badge me-1 fs-6"
                                                    data-bs-toggle="tooltip"
                                                    data-bs-html="true"
                                                    data-bs-title="<em>Tooltip</em> <u>with</u> <b>HTML</b>"
                                                    @click="
                                                        personRedirect(d.user)
                                                    "
                                                >
                                                    {{ d.full_name }}
                                                    <span
                                                        v-if="
                                                            'organisation_admin' ==
                                                            d.user_role
                                                        "
                                                    >
                                                        (Admin)</span
                                                    >
                                                </span>
                                            </ul>
                                            <div v-else class="col">
                                                <span
                                                    class="badge bg-secondary fs-6"
                                                    >This organisation currently
                                                    has no linked users.</span
                                                >
                                            </div>
                                        </div>
                                        <div class="row">
                                            <BootstrapAlert class="ms-2">
                                                Persons linked to the
                                                organisation are controlled by
                                                the organisation. <br />
                                                The Department cannot manage
                                                this list of people.
                                            </BootstrapAlert>
                                        </div>
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for=""
                                        class="col-sm-3 control-label fw-bold"
                                    >
                                        User Pin Code 1:</label
                                    >
                                    <span class="col-sm-3 fw-light">
                                        {{ org.pins.three }}
                                    </span>
                                    <label
                                        for=""
                                        class="col-sm-3 control-label fw-bold"
                                    >
                                        User Pin Code 2:</label
                                    >
                                    <div class="col-sm-3 fw-light">
                                        {{ org.pins.four }}
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <label
                                        for=""
                                        class="col-sm-3 control-label fw-bold"
                                    >
                                        Admin Pin Code 1:</label
                                    >
                                    <span class="col-sm-3 fw-light">
                                        {{ org.pins.one }}
                                    </span>
                                    <label
                                        for=""
                                        class="col-sm-3 control-label fw-bold"
                                    >
                                        Admin Pin Code 2:</label
                                    >
                                    <div class="col-sm-3 fw-light">
                                        {{ org.pins.two }}
                                    </div>
                                </div>
                            </form>
                        </FormSection>
                    </div>

                    <div
                        id="pills-other"
                        class="tab-pane"
                        role="tabpanel"
                        aria-labelledby="pills-other-tab"
                    >
                        <FormSection label="Applications" index="applications">
                            <ApplicationsTable
                                ref="proposals_table"
                                level="organisation_view"
                                :target-organisation-id="org.id"
                                :url="proposals_url"
                            />
                        </FormSection>

                        <FormSection label="Approvals" index="approvals">
                            <ApprovalsTable
                                ref="approvals_table"
                                level="organisation_view"
                                :target-organisation-id="org.id"
                                :url="approvals_url"
                            />
                        </FormSection>

                        <FormSection label="Compliances" index="compliances">
                            <CompliancesTable
                                ref="compliances_table"
                                level="organisation_view"
                                :target-organisation-id="org.id"
                                :url="compliances_url"
                            />
                        </FormSection>
                    </div>
                </div>
            </div>
            <AddContact ref="add_contact" :org_id="org.id" />
        </div>
        <div v-else>
            <BootstrapSpinner class="text-primary" :is-loading="true" />
        </div>
    </div>
</template>

<script>
import { api_endpoints, constants, helpers } from '@/utils/hooks.js';
import ApplicationsTable from '@/components/common/table_proposals.vue';
import ApprovalsTable from '@/components/common/table_approvals.vue';
import CompliancesTable from '@/components/common/table_compliances.vue';
import TableOrganisationContacts from '@/components/common/table_organisation_contacts.vue';
import CommsLogs from '@common-utils/comms_logs.vue';
import AddContact from '@common-utils/add_contact.vue';
import utils from '../utils.js';
import FormSection from '@/components/forms/section_toggle.vue';

export default {
    name: 'ManageOrganisation',
    components: {
        CommsLogs,
        ApplicationsTable,
        ApprovalsTable,
        CompliancesTable,
        AddContact,
        TableOrganisationContacts,
        FormSection,
    },
    data() {
        let vm = this;
        return {
            organisation_name: '',
            organisation_abn: '',
            org: null,
            countries: [],
            updatingDetails: false,
            updatingAddress: false,
            updatingContact: false,
            activate_tables: false,
            comms_url: helpers.add_endpoint_json(
                api_endpoints.organisations,
                vm.$route.params.org_id + '/comms_log'
            ),
            logs_url: helpers.add_endpoint_json(
                api_endpoints.organisations,
                vm.$route.params.org_id + '/action_log'
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.organisations,
                vm.$route.params.org_id + '/add_comms_log'
            ),

            contacts_headers: [
                'Name',
                'Phone',
                'Mobile',
                'Fax',
                'Email',
                'Action',
            ],

            proposals_url:
                api_endpoints.proposals_paginated_external +
                '&org_id=' +
                vm.$route.params.org_id,
            approvals_url:
                api_endpoints.approvals_paginated_external +
                '&org_id=' +
                vm.$route.params.org_id,
            compliances_url:
                api_endpoints.compliances_paginated +
                '&org_id=' +
                vm.$route.params.org_id,

            contacts_options: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    url: helpers.add_endpoint_json(
                        api_endpoints.organisations,
                        vm.$route.params.org_id + '/contacts'
                    ),
                    dataSrc: '',
                },
                columns: [
                    {
                        data: 'id',
                        mRender: function (data, type, full) {
                            return full.first_name + ' ' + full.last_name;
                        },
                    },
                    { data: 'phone_number', defaultContent: '' },
                    { data: 'mobile_number', defaultContent: '' },
                    { data: 'fax_number', defaultContent: '' },
                    { data: 'email', defaultContent: '' },
                    {
                        data: 'id',
                        mRender: function (data, type, full) {
                            if (
                                'Organisation Admin' == full.user_role &&
                                1 == full.admin_user_count
                            ) {
                                return '';
                            }
                            let links = '';
                            let name = full.first_name + ' ' + full.last_name;
                            links += `<a data-email='${full.email}' data-name='${name}' data-id='${full.id}' class="remove-contact">Remove</a><br/>`;
                            return links;
                        },
                    },
                ],
                processing: true,
            },
        };
    },
    computed: {
        formattedABN: function () {
            if (this.organisation_abn == null || this.organisation_abn == '') {
                return '';
            }
            if (this.organisation_abn.length == 9) {
                return helpers.formatACN(this.organisation_abn);
            } else if (this.organisation_abn.length == 11) {
                return helpers.formatABN(this.organisation_abn);
            }
            return this.organisation_abn;
        },
        orgHasAddress: function () {
            return (
                this.org &&
                this.org.address &&
                Object.keys(this.org.address).length !== 0
            );
        },
    },
    created: function () {
        let vm = this;
        let initialisers = [
            utils.fetchCountries(),
            utils.fetchOrganisation(vm.$route.params.org_id),
        ];
        Promise.all(initialisers).then((data) => {
            vm.countries = data[0];
            vm.org = data[1];
            this.assignNameAndABN();
            vm.org.address = vm.org.address != null ? vm.org.address : {};
            vm.org.pins = vm.org.pins != null ? vm.org.pins : {};
        });
    },
    methods: {
        assignNameAndABN: function () {
            // Prevent the page heading being reactive when the user is editing name and abn
            this.organisation_name = Object.assign(
                {},
                this.org
            ).ledger_organisation_name;
            this.organisation_abn = Object.assign(
                {},
                this.org
            ).ledger_organisation_abn;
        },
        toggleBillingAddressFieldsDisabled: function () {
            if (!this.org.billing_same_as_postal) {
                $('.billing-address').first().focus();
            } else {
                this.copyPostalAddressToBillingAddress();
            }
        },
        copyPostalAddressToBillingAddress: function () {
            this.org.address.billing_address.line1 =
                this.org.address.postal_address.line1;
            this.org.address.billing_address.locality =
                this.org.address.postal_address.locality;
            this.org.address.billing_address.state =
                this.org.address.postal_address.state;
            this.org.address.billing_address.postcode =
                this.org.address.postal_address.postcode;
            this.org.address.billing_address.country =
                this.org.address.postal_address.country;
        },
        updatePostalAddressFromBillingAddress: function () {
            if (this.org.billing_same_as_postal) {
                this.copyPostalAddressToBillingAddress();
            }
        },
        personRedirect: function (id) {
            window.location.href = '/internal/person/details/' + id;
        },
        validateForm: function (formId) {
            let vm = this;
            var form = document.getElementById(formId);

            if (form.checkValidity()) {
                if (formId == 'organisation-address-form') {
                    const code1 = vm.org.address.postal_address.postcode;
                    const code2 = vm.org.address.billing_address.postcode;
                    if (
                        isNaN(Number.parseInt(code1)) ||
                        isNaN(Number.parseInt(code2))
                    ) {
                        swal.fire(
                            'Failure updating organisation details.',
                            'Postcode should only contain numeric value.',
                            'error'
                        );
                    } else {
                        vm.updateAddress();
                    }
                } else if (formId == 'organisation-details-form') {
                    vm.updateDetails();
                }
            } else {
                form.classList.add('was-validated');
                $(form).find('input:invalid').first().focus();
            }
            return false;
        },
        updateDetails: function () {
            let vm = this;
            vm.updatingDetails = true;
            let payload = JSON.stringify({
                organisation_id: vm.org.ledger_organisation_id,
                organisation_name: vm.org.ledger_organisation_name
                    ? vm.org.ledger_organisation_name
                    : null,
                organisation_abn: vm.org.ledger_organisation_abn
                    ? vm.org.ledger_organisation_abn
                    : null,
                organisation_email: vm.org.ledger_organisation_email
                    ? vm.org.ledger_organisation_email
                    : null,
                organisation_trading_name: vm.org
                    .ledger_organisation_trading_name
                    ? vm.org.ledger_organisation_trading_name
                    : null,
            });
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.organisations,
                    vm.org.id + '/update_details'
                ),
                {
                    method: 'PUT',
                    body: payload,
                }
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        return Promise.reject(error);
                    }
                    this.assignNameAndABN();
                    swal.fire(
                        'Success',
                        'Organisation details updated successfully.',
                        'success'
                    );
                })
                .catch((error) => {
                    swal.fire(
                        'Failure updating organisation details.',
                        error,
                        'error'
                    );
                    console.error(error);
                })
                .finally(() => {
                    vm.updatingDetails = false;
                });
        },
        updateAddress: function () {
            let vm = this;
            vm.updatingAddress = true;
            let payload = JSON.stringify({
                organisation_id: vm.org.ledger_organisation_id,
                postal_address: {
                    postal_line1: vm.org.address.postal_address.line1,
                    postal_locality: vm.org.address.postal_address.locality,
                    postal_state: vm.org.address.postal_address.state,
                    postal_postcode: vm.org.address.postal_address.postcode,
                    postal_country: vm.org.address.postal_address.country,
                },
                billing_address: {
                    billing_line1: vm.org.address.billing_address.line1,
                    billing_locality: vm.org.address.billing_address.locality,
                    billing_state: vm.org.address.billing_address.state,
                    billing_postcode: vm.org.address.billing_address.postcode,
                    billing_country: vm.org.address.billing_address.country,
                },
            });

            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.organisations,
                    vm.org.id + '/update_address'
                ),
                {
                    method: 'POST',
                    body: payload,
                }
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.org.billing_same_as_postal =
                        vm.isBillingAddressSame != null
                            ? vm.isBillingAddressSame
                            : false;
                    swal.fire(
                        'Success',
                        'Organisation address updated successfully',
                        'success'
                    );
                })
                .catch((error) => {
                    swal.fire(
                        'Failure updating organisation address.',
                        'Something went wrong! Please try again.',
                        'error'
                    );
                    console.error(error);
                })
                .finally(() => {
                    vm.updatingAddress = false;
                });
        },
    },
};
</script>

<style>
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
