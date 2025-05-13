<template>
    <div id="externalOrgInfo" class="container">
        <div class="row">
            <div v-if="org" class="col">
                <div class="row">
                    <FormSection
                        index="organisation-details"
                        label="Organisation Details"
                        :form-collapse="false"
                    >
                        <form
                            id="organisation-details"
                            class="mb-2 needs-validation"
                            novalidate
                            @submit.prevent=""
                        >
                            <div class="row mb-3">
                                <label
                                    for="ledger_organisation_name"
                                    class="col-sm-2 control-label"
                                    >Organisation Name</label
                                >
                                <div class="col-sm-4">
                                    <input
                                        v-model="org.ledger_organisation_name"
                                        type="text"
                                        class="form-control"
                                        name="ledger_organisation_name"
                                        required
                                    />
                                    <div class="invalid-feedback">
                                        Please enter a an organisation name.
                                    </div>
                                </div>
                            </div>

                            <div class="row mb-3">
                                <label
                                    for="ledger_organisation_trading_name"
                                    class="col-sm-2 control-label"
                                    >Trading Name</label
                                >
                                <div class="col-sm-4">
                                    <input
                                        v-model="
                                            org.ledger_organisation_trading_name
                                        "
                                        type="text"
                                        class="form-control"
                                        name="ledger_organisation_trading_name"
                                    />
                                </div>
                            </div>

                            <div class="row mb-3">
                                <label
                                    for="ledger_organisation_abn"
                                    class="col-sm-2 control-label"
                                    >ABN
                                </label>
                                <div class="col-sm-4">
                                    <input
                                        v-model="org.ledger_organisation_abn"
                                        type="text"
                                        class="form-control"
                                        name="ledger_organisation_abn"
                                        disabled
                                    />
                                </div>
                            </div>

                            <div class="row mb-3">
                                <label
                                    for="ledger_organisation_email"
                                    class="col-sm-2 control-label"
                                    >Email
                                </label>
                                <div class="col-sm-4">
                                    <input
                                        v-model="org.ledger_organisation_email"
                                        type="email"
                                        class="form-control"
                                        name="ledger_organisation_email"
                                    />
                                    <div class="invalid-feedback">
                                        Please enter a valid email address.
                                    </div>
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-sm-6">
                                    <BootstrapLoadingButton
                                        text="Update"
                                        :is-loading="updatingDetails"
                                        class="btn btn-primary float-end"
                                        @click="
                                            validateForm('organisation-details')
                                        "
                                    />
                                </div>
                            </div>
                        </form>
                    </FormSection>

                    <FormSection
                        v-if="org"
                        index="address-details"
                        label="Address Details"
                        :form-collapse="false"
                    >
                        <form
                            id="address-details"
                            class="mb-2 needs-validation"
                            novalidate
                            @submit.prevent=""
                        >
                            <fieldset class="mb-3 w-50">
                                <legend>Postal Address</legend>
                                <div class="address-box">
                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="postalAddressLine1"
                                                class="form-label"
                                                >Street</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="postalAddressLine1"
                                                v-model="
                                                    org.address.postal_address
                                                        .line1
                                                "
                                                type="text"
                                                class="form-control"
                                                name="postalAddressLine1"
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="postalLocality"
                                                class="form-label"
                                                >Town/Suburb</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="postalLocality"
                                                v-model="
                                                    org.address.postal_address
                                                        .locality
                                                "
                                                type="text"
                                                class="form-control"
                                                name="postalLocality"
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="postalState"
                                                class="form-label"
                                                >State</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="postalState"
                                                v-model="
                                                    org.address.postal_address
                                                        .state
                                                "
                                                type="text"
                                                class="form-control"
                                                name="postalState"
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="postalPostcode"
                                                class="form-label"
                                                >Postcode</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="postalPostcode"
                                                v-model="
                                                    org.address.postal_address
                                                        .postcode
                                                "
                                                type="text"
                                                class="form-control"
                                                name="postalPostcode"
                                                maxlength="10"
                                                required
                                                @keyup="
                                                    updatePostalAddressFromBillingAddress
                                                "
                                            />
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="postalPostcode"
                                                class="form-label"
                                                >Country</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <select
                                                id="country"
                                                v-model="
                                                    org.address.postal_address
                                                        .country
                                                "
                                                class="form-select"
                                                name="Country"
                                                required
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
                                        <div class="col-md-4">&nbsp;</div>
                                        <div class="col-md-8">
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
                                </div>
                            </fieldset>
                            <fieldset
                                class="mb-3 w-50"
                                :disabled="org.billing_same_as_postal"
                            >
                                <legend>Billing Address</legend>
                                <div class="address-box">
                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="billingAddressLine1"
                                                class="form-label"
                                                >Street</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="billingAddressLine1"
                                                v-model="
                                                    org.address.billing_address
                                                        .line1
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billingAddressLine1"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="billingLocality"
                                                class="form-label"
                                                >Town/Suburb</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="billingLocality"
                                                v-model="
                                                    org.address.billing_address
                                                        .locality
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billingLocality"
                                                required
                                            />
                                        </div>
                                    </div>

                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="billingState"
                                                class="form-label"
                                                >State</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="billingState"
                                                v-model="
                                                    org.address.billing_address
                                                        .state
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billingState"
                                                required
                                            />
                                        </div>
                                    </div>
                                    <div class="row mb-2">
                                        <div class="col-md-4">
                                            <label
                                                for="billingPostcode"
                                                class="form-label"
                                                >Postcode</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <input
                                                id="billingPostcode"
                                                v-model="
                                                    org.address.billing_address
                                                        .postcode
                                                "
                                                type="text"
                                                class="form-control billing-address"
                                                name="billingPostcode"
                                                maxlength="10"
                                                required
                                            />
                                        </div>
                                    </div>
                                    <div class="row mb-4">
                                        <div class="col-md-4">
                                            <label
                                                for="billingPostcode"
                                                class="form-label"
                                                >Country</label
                                            >
                                        </div>
                                        <div class="col-md-8">
                                            <select
                                                id="country"
                                                v-model="
                                                    org.address.billing_address
                                                        .country
                                                "
                                                class="form-select billing-address"
                                                name="Country"
                                                required
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
                                </div>
                            </fieldset>

                            <div class="row">
                                <div class="col-md-6 px-2">
                                    <BootstrapLoadingButton
                                        text="Update"
                                        :is-loading="updatingAddress"
                                        class="btn btn-primary float-end"
                                        @click="validateForm('address-details')"
                                    />
                                </div>
                            </div>
                        </form>
                    </FormSection>

                    <FormSection
                        :form-collapse="false"
                        label="Contact Details"
                        index="contact-details"
                    >
                        <div class="row">
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

                        <datatable
                            id="organisation_contacts_datatable"
                            ref="contacts_datatable"
                            :dt-options="contacts_options"
                            :dt-headers="contacts_headers"
                        />
                    </FormSection>

                    <FormSection
                        :form-collapse="false"
                        label="Account Pins"
                        index="account-pins"
                    >
                        <BootstrapAlert
                            type="warning"
                            icon="exclamation-triangle-fill"
                            class="ms-1"
                        >
                            <ul class="list-group">
                                <li class="list-group-item">
                                    You and your organisation are responsible
                                    for managing the distribution of pin codes.
                                </li>
                                <li class="list-group-item">
                                    If you are not sure which pin code to give
                                    to a staff member please call the Tourism
                                    and Concessions Branch on (08) 9219 9978.
                                </li>
                                <li class="list-group-item">
                                    Never provide these pin codes to people that
                                    are not authorised to
                                    apply/cancel/surrender/pay fees on behalf of
                                    this organisation.
                                </li>
                            </ul>
                        </BootstrapAlert>

                        <h5>Administrator Pins</h5>

                        <BootstrapAlert class="ms-1">
                            <ul class="list-group">
                                <li class="list-group-item">
                                    Provide the new user these pin codes if you
                                    want the them to have administrator
                                    privileges.
                                </li>
                                <li class="list-group-item">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="input-group mb-2 mt-1">
                                                <span
                                                    id="basic-addon1"
                                                    class="input-group-text pin-label"
                                                    >Admin Pin 1</span
                                                >
                                                <input
                                                    ref="admin-pin-1"
                                                    type="text"
                                                    class="form-control"
                                                    :value="org.pins.one"
                                                    aria-label="Username"
                                                    aria-describedby="basic-addon1"
                                                    readonly
                                                />
                                                <button
                                                    class="btn btn-secondary btn-copy input-group-text"
                                                    @click.prevent="
                                                        copyToClipboard(
                                                            'admin-pin-1'
                                                        )
                                                    "
                                                >
                                                    copy
                                                </button>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="input-group mb-2 mt-1">
                                                <span
                                                    id="basic-addon1"
                                                    class="input-group-text pin-label"
                                                    >Admin Pin 2</span
                                                >
                                                <input
                                                    ref="admin-pin-2"
                                                    type="text"
                                                    class="form-control"
                                                    :value="org.pins.two"
                                                    aria-label="Username"
                                                    aria-describedby="basic-addon1"
                                                    readonly
                                                />
                                                <button
                                                    class="btn btn-secondary btn-copy input-group-text"
                                                    @click.prevent="
                                                        copyToClipboard(
                                                            'admin-pin-2'
                                                        )
                                                    "
                                                >
                                                    copy
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </li>
                            </ul>
                        </BootstrapAlert>

                        <h5>User Pins</h5>

                        <BootstrapAlert class="ms-1">
                            <ul class="list-group">
                                <li class="list-group-item">
                                    Provide the new user these pin codes if you
                                    want the new user to be a regular user.
                                </li>
                                <li class="list-group-item">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="input-group mb-2 mt-1">
                                                <span
                                                    id="user-pin-1"
                                                    class="input-group-text pin-label"
                                                    >User Pin 1</span
                                                >
                                                <input
                                                    ref="user-pin-1"
                                                    type="text"
                                                    class="form-control"
                                                    :value="org.pins.three"
                                                    aria-label="Username"
                                                    aria-describedby="user-pin-1"
                                                    readonly
                                                />
                                                <button
                                                    class="btn btn-secondary btn-copy input-group-text"
                                                    @click.prevent="
                                                        copyToClipboard(
                                                            'user-pin-1'
                                                        )
                                                    "
                                                >
                                                    copy
                                                </button>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="input-group mb-2 mt-1">
                                                <span
                                                    id="basic-addon1"
                                                    class="input-group-text pin-label"
                                                    >User Pin 2</span
                                                >
                                                <input
                                                    ref="user-pin-2"
                                                    type="text"
                                                    class="form-control"
                                                    :value="org.pins.four"
                                                    aria-label="Username"
                                                    aria-describedby="basic-addon1"
                                                    readonly
                                                />
                                                <button
                                                    class="btn btn-secondary btn-copy input-group-text"
                                                    @click.prevent="
                                                        copyToClipboard(
                                                            'user-pin-2'
                                                        )
                                                    "
                                                >
                                                    copy
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </li>
                            </ul>
                        </BootstrapAlert>
                    </FormSection>

                    <FormSection
                        :form-collapse="false"
                        label="Linked User Accounts"
                        index="linked-user-accounts"
                    >
                        <BootstrapAlert
                            type="warning"
                            icon="exclamation-triangle-fill"
                            class="ms-1"
                        >
                            The list of users linked to your organisation is
                            controlled by you and your organisation. The
                            Department cannot manage this list.
                        </BootstrapAlert>

                        <div>
                            <datatable
                                id="organisation_contacts_datatable_ref"
                                ref="contacts_datatable_user"
                                :dt-options="contacts_options_ref"
                                :dt-headers="contacts_headers_ref"
                            />
                        </div>
                    </FormSection>
                </div>
                <AddContact ref="add_contact" :org_id="org.id" />
            </div>
            <div v-else>
                <BootstrapSpinner class="text-primary" :is-loading="true" />
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints, constants, helpers, utils } from '@/utils/hooks';
import datatable from '@vue-utils/datatable.vue';
import AddContact from '@common-utils/add_contact.vue';
import BootstrapLoadingButton from '../../../utils/vue/BootstrapLoadingButton.vue';
import swal from 'sweetalert2';

export default {
    name: 'ManageOrganisation',
    components: {
        datatable,
        AddContact,
        BootstrapLoadingButton,
    },
    beforeRouteEnter: function (to, from, next) {
        let initialisers = [
            utils.fetchCountries(),
            utils.fetchOrganisation(to.params.org_id),
            utils.fetchOrganisationPermissions(to.params.org_id),
        ];
        Promise.all(initialisers).then((data) => {
            next((vm) => {
                vm.countries = data[0];
                vm.org = Object.assign({}, data[1]);
                vm.myorgperms = data[2];
            });
        });
    },
    beforeRouteUpdate: function (to, from, next) {
        let initialisers = [
            utils.fetchOrganisation(to.params.org_id),
            utils.fetchOrganisationPermissions(to.params.org_id),
        ];
        Promise.all(initialisers).then((data) => {
            next((vm) => {
                Object.assign(vm.org, data[0]);
                vm.myorgperms = data[1];
            });
        });
    },
    props: {
        isApplication: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        let vm = this;
        return {
            org: null,
            loading: [],
            countries: [],
            contact_user: {
                first_name: null,
                last_name: null,
                email: null,
                mobile_number: null,
                phone_number: null,
            },
            updatingDetails: false,
            updatingAddress: false,
            updatingContact: false,
            logsTable: null,
            myorgperms: null,
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            user_is_self_message: `<i class="ps-2 fa-solid fa-lock text-secondary"></i><span class="text-secondary ps-2">Can't perform actions on self</span>`,
            last_admin_message: `<i class="ps-2 fa-solid fa-lock text-secondary"></i><span class="text-secondary ps-2">Can't remove last active admin user</span>`,
            logsDtOptions: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                order: [[2, 'desc']],
                dom:
                    "<'row'<'col-sm-5'l><'col-sm-6'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-5'i><'col-sm-7'p>>",
                processing: true,
                ajax: {
                    url: helpers.add_endpoint_json(
                        api_endpoints.organisations,
                        vm.$route.params.org_id + '/action_log'
                    ),
                    dataSrc: '',
                },
                columns: [
                    {
                        data: 'who',
                    },
                    {
                        data: 'what',
                    },
                    {
                        data: 'when',
                        mRender: function (data) {
                            return moment(data).format(vm.DATE_TIME_FORMAT);
                        },
                    },
                ],
            },
            commsDtOptions: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                order: [[0, 'desc']],
                processing: true,
                ajax: {
                    url: helpers.add_endpoint_json(
                        api_endpoints.organisations,
                        vm.$route.params.org_id + '/comms_log'
                    ),
                    dataSrc: '',
                },
                columns: [
                    {
                        title: 'Date',
                        data: 'created',
                        render: function (date) {
                            return moment(date).format(vm.DATE_TIME_FORMAT);
                        },
                    },
                    {
                        title: 'Type',
                        data: 'type',
                    },
                    {
                        title: 'Reference',
                        data: 'reference',
                    },
                    {
                        title: 'To',
                        data: 'to',
                        render: vm.commaToNewline,
                    },
                    {
                        title: 'CC',
                        data: 'cc',
                        render: vm.commaToNewline,
                    },
                    {
                        title: 'From',
                        data: 'fromm',
                        render: vm.commaToNewline,
                    },
                    {
                        title: 'Subject/Desc.',
                        data: 'subject',
                    },
                    {
                        title: 'Text',
                        data: 'text',
                        render: function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 100,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-toggle="popover" ' +
                                        'data-trigger="click" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-content="<%= text %>" ' +
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
                        title: 'Documents',
                        data: 'documents',
                        render: function (values) {
                            var result = '';
                            _.forEach(values, function (value) {
                                // We expect an array [docName, url]
                                // if it's a string it is the url
                                var docName = '',
                                    url = '';
                                if (_.isArray(value) && value.length > 1) {
                                    docName = value[0];
                                    url = value[1];
                                }
                                if (typeof s === 'string') {
                                    url = value;
                                    // display the first  chars of the filename
                                    docName = _.last(value.split('/'));
                                    docName = _.truncate(docName, {
                                        length: 18,
                                        omission: '...',
                                        separator: ' ',
                                    });
                                }
                                result +=
                                    '<a href="' +
                                    url +
                                    '" target="_blank"><p>' +
                                    docName +
                                    '</p></a><br>';
                            });
                            return result;
                        },
                    },
                ],
            },
            commsTable: null,

            contacts_headers: [
                'Name',
                'Phone',
                'Mobile',
                'Fax',
                'Email',
                'Action',
            ],
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
                    { data: 'phone_number' },
                    { data: 'mobile_number' },
                    { data: 'fax_number' },
                    { data: 'email' },
                    {
                        data: 'id',
                        mRender: function (data, type, full) {
                            let links = '';
                            let name = full.first_name + ' ' + full.last_name;
                            if (full.user == vm.myorgperms.user_id) {
                                return vm.user_is_self_message;
                            }
                            if (
                                full.admin_user_count == 1 &&
                                full.user_role == 'Organisation Admin'
                            ) {
                                return vm.last_admin_message.replace(
                                    'user',
                                    'contact'
                                );
                            } else {
                                links += `<a data-email='${full.email}' data-name='${name}' data-id='${full.id}' class="remove-contact">Remove</a><br/>`;
                            }
                            return links;
                        },
                    },
                ],
                processing: true,
            },

            contacts_headers_ref: ['Name', 'Role', 'Email', 'Status', 'Action'],
            contacts_options_ref: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    url: helpers.add_endpoint_json(
                        api_endpoints.organisations,
                        vm.$route.params.org_id + '/contacts_exclude'
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
                    { data: 'user_role' },
                    { data: 'email' },
                    { data: 'user_status' },
                    {
                        data: 'id',
                        mRender: function (data, type, full) {
                            let links = '';
                            if (vm.myorgperms.is_admin) {
                                if (full.user == vm.myorgperms.user_id) {
                                    return vm.user_is_self_message;
                                }
                                if (
                                    full.user_role == 'Organisation Admin' &&
                                    full.user_status == 'Active' &&
                                    full.admin_user_count == 1
                                ) {
                                    return vm.last_admin_message;
                                }
                                if (full.user_status == 'Pending') {
                                    links += `<a data-email='${full.email}' data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="accept_contact">Accept</a><br/>`;
                                    links += `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="decline_contact">Decline</a><br/>`;
                                } else if (full.user_status == 'Suspended') {
                                    links += `<a data-email='${full.email}' data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="reinstate_contact">Reinstate</a><br/>`;
                                } else if (full.user_status == 'Active') {
                                    links += `<a data-email='${full.email}' data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="unlink_contact">Unlink</a><br/>`;
                                    links += `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="suspend_contact">Suspend</a><br/>`;
                                    if (full.user_role == 'Organisation User') {
                                        links += `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_organisation_admin">Make Organisation Admin</a><br/>`;
                                    } else {
                                        if (full.admin_user_count > 1) {
                                            links += `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="make_organisation_user">Demote to Organisation User</a><br/>`;
                                        }
                                    }
                                } else if (full.user_status == 'Unlinked') {
                                    links += `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="relink_contact">Relink</a><br/>`;
                                } else if (full.user_status == 'Declined') {
                                    links += `<a data-email='${full.email}'  data-firstname='${full.first_name}' data-lastname='${full.last_name}' data-id='${full.id}' data-mobile='${full.mobile_number}' data-phone='${full.phone_number}' class="accept_declined_contact">Accept (Previously Declined)</a><br/>`;
                                }
                            }
                            return links;
                        },
                    },
                ],
                processing: true,
            },
        };
    },
    computed: {
        classCompute: function () {
            return this.isApplication ? 'row' : 'container';
        },
        isBillingAddressSame: function () {
            return (
                Object.values(this.org.address.postal_address).toString() ==
                Object.values(this.org.address.billing_address).toString()
            );
        },
    },
    created: function () {
        let vm = this;
        this.personal_form = document.forms.personal_form;
        let initialisers = [
            utils.fetchCountries(),
            utils.fetchOrganisation(vm.$route.params.org_id),
            utils.fetchOrganisationPermissions(vm.$route.params.org_id),
        ];
        Promise.all(initialisers).then((data) => {
            vm.countries = data[0];
            vm.org = Object.assign({}, data[1], data[2]);
            vm.myorgperms = data[2];
            vm.org.billing_same_as_postal = vm.isBillingAddressSame || false;
            if (vm.org.billing_same_as_postal) {
                this.copyPostalAddressToBillingAddress();
            }
        });
    },
    mounted: function () {
        this.personal_form = document.forms.personal_form;
    },
    updated: function () {
        $('.panelClicker[data-toggle="collapse"]').on('click', function () {
            var chev = $(this).children()[0];
            window.setTimeout(function () {
                $(chev).toggleClass(
                    'glyphicon-chevron-down glyphicon-chevron-up'
                );
            }, 100);
        });
        this.$nextTick(() => {
            this.eventListeners();
        });
    },
    methods: {
        addContact: function () {
            this.$refs.add_contact.isModalOpen = true;
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
        toggleBillingAddressFieldsDisabled: function () {
            if (!this.org.billing_same_as_postal) {
                $('.billing-address').first().focus();
            } else {
                this.copyPostalAddressToBillingAddress();
            }
        },
        eventListeners: function () {
            let vm = this;
            if (typeof vm.$refs.contacts_datatable !== 'undefined') {
                vm.$refs.contacts_datatable.vmDataTable.on(
                    'click',
                    '.remove-contact',
                    (e) => {
                        e.preventDefault();

                        let name = $(e.target).data('name');
                        let email = $(e.target).data('email');
                        let id = $(e.target).data('id');
                        swal.fire({
                            title: 'Remove Contact',
                            text:
                                'Are you sure you want to remove ' +
                                name +
                                '(' +
                                email +
                                ') as a contact  ?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Remove Contact',
                            reverseButtons: true,
                        })
                            .then(async (result) => {
                                if (result.isConfirmed) {
                                    vm.deleteContact(id);
                                }
                            })
                            .catch((error) => {
                                console.error(error);
                            });
                    }
                );

                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.accept_contact',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Accept Linking Request',
                            text:
                                'Are you sure you want to accept this linking request from ' +
                                name +
                                ' (' +
                                email +
                                ')?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Accept Linking Request',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.isConfirmed) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/accept_user'
                                        ),
                                        {
                                            method: 'POST',
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                        }
                                    )
                                        .then(async (response) => {
                                            const data = await response.json();
                                            if (!response.ok) {
                                                throw new Error(
                                                    JSON.stringify(data)
                                                );
                                            }
                                            swal.fire({
                                                title: 'Linking Request Accepted',
                                                text:
                                                    'You have successfully accepted the linking request from ' +
                                                    name +
                                                    '.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                            });
                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        })
                                        .catch((error) => {
                                            swal.fire(
                                                'Linking Request Failed',
                                                error,
                                                'error'
                                            );
                                            console.error(error);
                                        });
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.accept_declined_contact',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Accept Previously Declined Linking Request',
                            text:
                                'Are you sure you want to accept the previously declined linking request for ' +
                                name +
                                ' (' +
                                email +
                                ')?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText:
                                'Accept Previously Declined Linking Request',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.value) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/accept_declined_user'
                                        ),
                                        {
                                            emulateJSON: true,
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                            method: 'POST',
                                        }
                                    ).then(
                                        async (response) => {
                                            await response.json();
                                            swal.fire({
                                                title: 'Previously Declined Linking Request Accepted',
                                                text:
                                                    'You have successfully accepted the linking request from ' +
                                                    name +
                                                    '.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                            });
                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        },
                                        (error) => {
                                            swal.fire(
                                                'Accepting Previously Declined Linking Request Failed',
                                                'There was an error accepting ' +
                                                    name +
                                                    '.',
                                                'error'
                                            );
                                            console.error(error);
                                        }
                                    );
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.decline_contact',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Decline Linking Request',
                            text:
                                'Are you sure you want to decline the linking request from ' +
                                name +
                                ' (' +
                                email +
                                ')?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Decline Linking Request',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.isConfirmed) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/decline_user'
                                        ),
                                        {
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                            emulateJSON: true,
                                            method: 'POST',
                                        }
                                    )
                                        .then(async (response) => {
                                            await response.json();
                                            if (!response.ok) {
                                                throw new Error(
                                                    response.statusText
                                                );
                                            }
                                            swal.fire({
                                                title: 'Linking Request Declined',
                                                text:
                                                    'You have successfully declined the linking request from ' +
                                                    name +
                                                    '.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                            });
                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        })
                                        .catch((error) => {
                                            swal.fire(
                                                'Contact Decline',
                                                'There was an error declining ' +
                                                    name +
                                                    '.',
                                                'error'
                                            );
                                            console.error(error);
                                        });
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.unlink_contact',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Unlink User',
                            text:
                                'Are you sure you want to unlink ' +
                                name +
                                ' (' +
                                email +
                                ')?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Unlink User',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.isConfirmed) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/unlink_user'
                                        ),
                                        {
                                            emulateJSON: true,
                                            method: 'POST',
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                        }
                                    )
                                        .then(async (response) => {
                                            await response.json();
                                            if (!response.ok) {
                                                throw new Error(
                                                    response.statusText
                                                );
                                            }
                                            swal.fire({
                                                title: 'Unlink Successful',
                                                text:
                                                    'You have successfully unlinked ' +
                                                    name +
                                                    '.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                                reverseButtons: true,
                                            });

                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        })
                                        .catch((error) => {
                                            swal.fire(
                                                'Unlink',
                                                'There was an error unlinking this user ' +
                                                    error,
                                                'error'
                                            );
                                        });
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.make_organisation_admin',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Promote to Organisation Admin',
                            text:
                                'Are you sure you want to promote ' +
                                name +
                                ' (' +
                                email +
                                ') to an organisation admin?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText:
                                'Promote User to Organisation Admin',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.isConfirmed) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/make_admin_user'
                                        ),
                                        {
                                            emulateJSON: true,
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                            method: 'POST',
                                        }
                                    )
                                        .then(async (response) => {
                                            await response.json();
                                            swal.fire({
                                                title: 'Organisation Admin',
                                                text:
                                                    'You have successfully made ' +
                                                    name +
                                                    ' an organisation admin.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                            });
                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        })
                                        .catch((error) => {
                                            swal.fire(
                                                'Organisation Admin',
                                                'There was an error making ' +
                                                    name +
                                                    ' an Organisation Admin.',
                                                'error'
                                            );
                                            console.error(error);
                                        });
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.make_organisation_user',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Demote to Organisation User',
                            text:
                                'Are you sure you want to demote the admin user ' +
                                name +
                                ' (' +
                                email +
                                ') to an organisation user?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText:
                                'Demote User to Organisation User',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.isConfirmed) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/make_user'
                                        ),
                                        {
                                            emulateJSON: true,
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                            method: 'POST',
                                        }
                                    )
                                        .then(async (response) => {
                                            const data = await response.json();
                                            if (!response.ok) {
                                                console.error(
                                                    JSON.stringify(data)
                                                );
                                                swal.fire(
                                                    'Failed to Demote to Organisation User',
                                                    data.errors[0].detail,
                                                    'error'
                                                );
                                                return;
                                            }
                                            swal.fire({
                                                title: 'Organisation User',
                                                text:
                                                    'You have successfully made ' +
                                                    name +
                                                    ' an organisation user.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                            });
                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        })
                                        .catch((error) => {
                                            console.error(error);
                                            swal.fire(
                                                'Failed to Demote to Organisation User',
                                                error,
                                                'error'
                                            );
                                        });
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.suspend_contact',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Suspend User',
                            text:
                                'Are you sure you want to suspend  ' +
                                name +
                                ' (' +
                                email +
                                ')?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Suspend User',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.isConfirmed) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/suspend_user'
                                        ),

                                        {
                                            emulateJSON: true,
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                            method: 'POST',
                                        }
                                    )
                                        .then(async (response) => {
                                            await response.json();
                                            if (!response.ok) {
                                                throw new Error(
                                                    response.statusText
                                                );
                                            }
                                            swal.fire({
                                                title: 'Suspend User',
                                                text:
                                                    'You have successfully suspended ' +
                                                    name +
                                                    ' as a User.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                            });
                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        })
                                        .catch((error) => {
                                            swal.fire(
                                                'Suspend User',
                                                'There was an error suspending ' +
                                                    name +
                                                    ' as a User.',
                                                'error'
                                            );
                                            console.error(error);
                                        });
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.reinstate_contact',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Reinstate User',
                            text:
                                'Are you sure you want to reinstate  ' +
                                name +
                                ' (' +
                                email +
                                ')?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Reinstate User',
                            reverseButtons: true,
                        }).then((result) => {
                            if (result.isConfirmed) {
                                fetch(
                                    helpers.add_endpoint_json(
                                        api_endpoints.organisations,
                                        vm.org.id + '/reinstate_user'
                                    ),
                                    {
                                        emulateJSON: true,
                                        method: 'POST',
                                        body: JSON.stringify(vm.contact_user),
                                    }
                                )
                                    .then(async (response) => {
                                        await response.json();
                                        if (!response.ok) {
                                            throw new Error(
                                                response.statusText
                                            );
                                        }
                                        swal.fire({
                                            title: 'User Successfully Reinstated',
                                            text:
                                                'You have successfully reinstated ' +
                                                name +
                                                '.',
                                            icon: 'success',
                                            confirmButtonText: 'OK',
                                        });

                                        vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                    })
                                    .catch((error) => {
                                        swal.fire(
                                            'Reinstate User',
                                            'There was an error reinstating ' +
                                                name +
                                                '.',
                                            'error'
                                        );
                                        console.error(error);
                                    });
                            }
                        });
                    }
                );
                vm.$refs.contacts_datatable_user.vmDataTable.on(
                    'click',
                    '.relink_contact',
                    (e) => {
                        e.preventDefault();
                        let firstname = $(e.target).data('firstname');
                        let lastname = $(e.target).data('lastname');
                        let name = firstname + ' ' + lastname;
                        let email = $(e.target).data('email');
                        let mobile = $(e.target).data('mobile');
                        let phone = $(e.target).data('phone');
                        vm.contact_user.first_name = firstname;
                        vm.contact_user.last_name = lastname;
                        vm.contact_user.email = email;
                        vm.contact_user.mobile_number = mobile;
                        vm.contact_user.phone_number = phone;
                        swal.fire({
                            title: 'Relink User',
                            text:
                                'Are you sure you want to Relink  ' +
                                name +
                                ' (' +
                                email +
                                ')?',
                            icon: 'question',
                            showCancelButton: true,
                            confirmButtonText: 'Relink User',
                            reverseButtons: true,
                        }).then(
                            (result) => {
                                if (result.isConfirmed) {
                                    fetch(
                                        helpers.add_endpoint_json(
                                            api_endpoints.organisations,
                                            vm.org.id + '/relink_user'
                                        ),
                                        {
                                            emulateJSON: true,
                                            method: 'POST',
                                            body: JSON.stringify(
                                                vm.contact_user
                                            ),
                                        }
                                    )
                                        .then(async (response) => {
                                            await response.json();
                                            if (!response.ok) {
                                                throw new Error(
                                                    response.statusText
                                                );
                                            }
                                            swal.fire({
                                                title: 'Relink User',
                                                text:
                                                    'You have successfully relinked ' +
                                                    name +
                                                    '.',
                                                icon: 'success',
                                                confirmButtonText: 'OK',
                                            });

                                            vm.$refs.contacts_datatable_user.vmDataTable.ajax.reload();
                                        })
                                        .catch((error) => {
                                            swal.fire(
                                                'Relink User',
                                                'There was an error relinking ' +
                                                    name +
                                                    '.',
                                                'error'
                                            );
                                            console.error(error);
                                        });
                                }
                            },
                            (error) => {
                                console.error(error);
                            }
                        );
                    }
                );
            } // endif
        },
        validateForm: function (formId) {
            let vm = this;
            var form = document.getElementById(formId);

            if (form.checkValidity()) {
                if (formId == 'address-details') {
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
                } else if (formId == 'organisation-details') {
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
                    swal.fire(
                        'Success',
                        'Organisation details updated successfully.',
                        'success'
                    );
                })
                .catch((error) => {
                    swal.fire(
                        'Failure updating organisation details.',
                        'Something went wrong! Please try again.',
                        'error'
                    );
                    console.error(error);
                })
                .finally(() => {
                    vm.updatingDetails = false;
                });
        },
        addedContact: function () {
            let vm = this;
            swal.fire(
                'Added',
                'The contact has been successfully added.',
                'success'
            );
            vm.$refs.contacts_datatable.vmDataTable.ajax.reload();
        },
        deleteContact: function (id) {
            let vm = this;

            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.organisation_contacts,
                    id
                ),
                {
                    method: 'DELETE',
                    emulateJSON: true,
                }
            )
                .then(async (response) => {
                    const response_text = await response.text();
                    if (response.ok) {
                        swal.fire(
                            'Contact Removed',
                            'The contact was successfully deleted',
                            'success'
                        );
                        vm.$refs.contacts_datatable.vmDataTable.ajax.reload();
                    } else {
                        throw new Error(response_text);
                    }
                })
                .catch((error) => {
                    console.error(error);
                    swal.fire(
                        'Remove Contact Failed',
                        'The contact could not be deleted because of the following ' +
                            error,
                        'error'
                    );
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
        copyToClipboard: function (refName) {
            var element = this.$refs[refName];
            var title = refName
                .replaceAll('-', ' ')
                .replace(/(?:^|\s|["'([{])+\S/g, (match) =>
                    match.toUpperCase()
                );
            try {
                // Access to navigator.clipboard requires https
                if (window.location.protocol == 'https:') {
                    navigator.clipboard.writeText(element.value);
                } else {
                    const textArea = document.createElement('textarea');
                    textArea.value = element.value;
                    document.body.appendChild(textArea);
                    textArea.focus({ preventScroll: true });
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                }
                swal.fire({
                    title: `${title} copied to clipboard`,
                    icon: 'success',
                    timer: 1500,
                    showConfirmButton: false,
                });
            } catch (err) {
                swal.fire({
                    title: 'Copy Failed',
                    text: `Unable to access the clipboard`,
                    icon: 'error',
                });
                console.error('Unable to copy to clipboard', err);
            }
        },
    },
};
</script>

<style scoped>
.top-buffer-s {
    margin-top: 25px;
}

#organisation_contacts_datatable {
    width: 100% !important;
}

.btn-copy:hover {
    background-color: linear-gradient(rgb(0 0 0/40%) 0 0);
}

.pin-label {
    width: 120px;
}

input[readonly] {
    background-color: white;
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

/* Hide the number input arrows */

/* Chrome, Safari, Edge, Opera */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

/* Firefox */
input[type='number'] {
    -moz-appearance: textfield;
    appearance: textfield;
}
</style>
