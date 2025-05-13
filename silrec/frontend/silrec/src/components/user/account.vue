<template>
    <div v-if="email_user" class="card">
        <div class="card-header fw-bold h4" style="padding: 30px">
            <div class="row">
                <div class="col-6">Organisations</div>
                <div class="col-6 text-end">
                    <i
                        class="bi fw-bold chevron-toggle down-chevron-open"
                        data-bs-target="#organisations-tab-body"
                        onclick=""
                    ></i>
                </div>
            </div>
        </div>
        <div id="organisations-tab-body" class="card-body">
            <FormSection
                index="organisation-details"
                :label="linkOrganisationTitle"
            >
                <BootstrapAlert>
                    To link an organisation to your account, please start by
                    clicking the drop down below and then search for the
                    organisation by name or abn
                </BootstrapAlert>
                <OrganisationSearch
                    v-if="!selectedOrganisation && !newOrganisation"
                    label="Organisations"
                    :lookup-api-endpoint="api_endpoints.organisation_lookup"
                    @selected="organisationSelected"
                    @new-organisation="prepareNewOrganisation"
                />
                <template v-if="selectedOrganisation">
                    <form
                        id="existing-organisation-form"
                        class="needs-validation"
                        novalidate
                        @submit.prevent=""
                    >
                        <div class="row mb-3">
                            <label
                                for="selectedOrganisation"
                                class="col-sm-3 col-form-label"
                                >Selected Organisation</label
                            >

                            <div class="col my-auto">
                                <span class="badge bg-primary fs-6">{{
                                    selectedOrganisation.text
                                }}</span>
                                Wrong Organisation?
                                <a href="#" @click="searchAgain"
                                    >Search Again</a
                                >
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-sm-3"></div>
                            <div class="col-sm-7">
                                <BootstrapAlert>
                                    <ul class="list-group">
                                        <li class="list-group-item">
                                            This organisation has already been
                                            registered with the system.
                                        </li>
                                        <li class="list-group-item">
                                            Please enter the two pin codes
                                            below.
                                        </li>
                                        <li class="list-group-item">
                                            These pin codes can be retrieved
                                            from:
                                        </li>
                                        <li class="list-group-item">
                                            <span
                                                v-for="person in selectedOrganisation.first_five.split(
                                                    ','
                                                )"
                                                :key="person"
                                                class="badge bg-primary bg-first-five me-2"
                                                >{{ person }}</span
                                            >
                                        </li>
                                    </ul>
                                </BootstrapAlert>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="pin1" class="col-sm-3 col-form-label"
                                >Pin 1</label
                            >
                            <div class="col-sm-4">
                                <input
                                    id="pin1"
                                    ref="pin1"
                                    v-model="pins.pin1"
                                    type="text"
                                    class="form-control"
                                    minlength="12"
                                    maxlength="12"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter a 12 digit pin code.
                                </div>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label for="pin2" class="col-sm-3 col-form-label"
                                >Pin 2</label
                            >
                            <div class="col-sm-4">
                                <input
                                    id="pin2"
                                    ref="pin2"
                                    v-model="pins.pin2"
                                    type="text"
                                    class="form-control"
                                    minlength="12"
                                    maxlength="12"
                                    required
                                />
                                <div class="invalid-feedback">
                                    Please enter a 12 digit pin code.
                                </div>
                            </div>
                        </div>
                        <div v-if="validatePinsError" class="row mb-3">
                            <label for="pin2" class="col-sm-3 col-form-label"
                                >&nbsp;</label
                            >
                            <div class="col-sm-4">
                                <BootstrapAlert
                                    type="danger"
                                    icon="exclamation-triangle-fill"
                                    >{{ validatePinsError }}
                                </BootstrapAlert>
                            </div>
                        </div>
                        <div v-if="pinCodesEntered" class="row mb-3">
                            <div for="pin2" class="col-sm-3">&nbsp;</div>
                            <div class="col-sm-4">
                                <BootstrapLoadingButton
                                    text="Submit Request"
                                    :is-loading="validatingPins"
                                    class="btn btn-primary"
                                    @click="validatePinsForm"
                                />
                            </div>
                        </div>
                    </form>
                </template>
                <template v-if="newOrganisation">
                    <form
                        id="new-organisation-form"
                        class="needs-validation"
                        novalidate
                        @submit.prevent=""
                    >
                        <div class="row mb-3">
                            <label for="" class="col-sm-3 col-form-label"
                                >&nbsp;</label
                            >
                            <div class="col-auto">
                                <BootstrapAlert>
                                    <ul class="list-group">
                                        <li class="list-group-item">
                                            The organisation you searched for
                                            has not yet been registered
                                        </li>
                                        <li class="list-group-item">
                                            Please enter the details below
                                        </li>
                                    </ul>
                                </BootstrapAlert>
                            </div>
                            <div class="col">
                                <a href="#" @click="searchAgain"
                                    >Search Again</a
                                >
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label
                                for="newOrganisationName"
                                class="col-sm-3 col-form-label"
                                >Organisation Name</label
                            >
                            <div class="col-sm-6">
                                <input
                                    id="newOrganisationName"
                                    ref="newOrganisationName"
                                    v-model="newOrganisation.name"
                                    type="text"
                                    class="form-control"
                                    required
                                />
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label
                                for="newOrganisationABN"
                                class="col-sm-3 col-form-label"
                                >Organisation ABN or ACN</label
                            >
                            <div class="col-sm-6">
                                <input
                                    id="newOrganisationABN"
                                    ref="newOrganisationABN"
                                    v-model="newOrganisation.abn"
                                    type="text"
                                    class="form-control"
                                    maxlength="50"
                                    required
                                />
                                <div class="invalid-feedback">
                                    This is not a valid ABN or ACN.
                                </div>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <label
                                for="newOrganisationIdentification"
                                class="col-sm-3 col-form-label"
                                >Proof of Employment</label
                            >
                            <div class="col-sm-9">
                                <input
                                    id="newOrganisationIdentification"
                                    ref="newOrganisationIdentification"
                                    type="file"
                                    class="form-control"
                                    required
                                    @change="readFile"
                                />
                                <div id="passwordHelpBlock" class="form-text">
                                    Please upload a letter on your
                                    organisation's official letter head stating
                                    that you are an employee of this
                                    organisation.
                                </div>
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-sm-3"></div>
                            <div class="col-sm-9">
                                <BootstrapLoadingButton
                                    text="Submit Request"
                                    :is-loading="loadingOrganisationRequest"
                                    class="btn btn-primary"
                                    @click="validateOrganisationRequest"
                                />
                            </div>
                        </div>
                    </form>
                </template>
            </FormSection>
            <FormSection
                v-if="organisation_requests && organisation_requests.length"
                index="organisation-requests"
                label="Linked Organisations"
            >
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th scope="col" class="col-1">Organisation</th>
                            <th scope="col" class="col-2">ABN / ACN</th>
                            <th scope="col" class="col-3">Status</th>
                            <th scope="col" class="col-4">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="organisation_request in organisation_requests"
                            :key="organisation_request.id"
                        >
                            <td>
                                <span>{{ organisation_request.name }}</span>
                            </td>
                            <td>
                                <span>{{
                                    helpers.formatABNorACN(
                                        organisation_request.abn
                                    )
                                }}</span>
                            </td>
                            <td>
                                <span
                                    v-if="
                                        'With Assessor' ==
                                        organisation_request.status
                                    "
                                    class="badge bg-secondary p-2"
                                    ><i class="fa fa-clock"></i> Pending</span
                                >
                                <span
                                    v-if="
                                        'Approved' ==
                                        organisation_request.status
                                    "
                                    class="badge bg-success me-1 p-2"
                                    ><i class="fa fa-chain"></i> Linked</span
                                >
                            </td>
                            <td>
                                <template
                                    v-if="
                                        'Approved' ==
                                        organisation_request.status
                                    "
                                >
                                    <div>
                                        <button
                                            class="btn btn-danger btn-sm btn-status"
                                            @click="
                                                unlinkUser(
                                                    organisation_request.organisation,
                                                    organisation_request.name
                                                )
                                            "
                                        >
                                            <i class="fa fa-chain-broken"></i>
                                            unlink
                                        </button>
                                    </div>
                                </template>
                                <span v-else>&nbsp;</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </FormSection>
        </div>
    </div>
    <BootstrapSpinner v-else class="text-primary" />
</template>

<script>
import OrganisationSearch from '@/components/internal/search/OrganisationSearch.vue';
import Swal from 'sweetalert2';
import BootstrapLoadingButton from '../../utils/vue/BootstrapLoadingButton.vue';
import { api_endpoints, constants, helpers, utils } from '@/utils/hooks';

export default {
    name: 'AccountComponent',
    components: {
        BootstrapLoadingButton,
        OrganisationSearch,
    },
    data() {
        return {
            api_endpoints: api_endpoints,
            countries: null,
            email_user: null,
            updatingDetails: false,
            selectedOrganisation: null,
            newOrganisation: null,
            organisation_requests: null,
            term: null,
            role: 'Employee',
            loadingOrganisationRequest: false,
            validatePinsError: null,
            validatingPins: false,
            pins: {
                pin1: '',
                pin2: '',
            },
            loadingOrganisationRequests: false,
            helpers: helpers,
        };
    },
    computed: {
        linkOrganisationTitle: function () {
            if (
                this.organisation_requests &&
                this.organisation_requests.length
            ) {
                return 'Link another Organisation';
            }
            return 'Link an organisation';
        },
    },
    created: function () {
        this.fetchInitialData();
    },
    mounted: function () {},
    methods: {
        numbersOnly: function (event) {
            return (
                event.keyCode === 8 ||
                (event.charCode >= 48 && event.charCode <= 57)
            );
        },
        togglePostalAddressFieldsDisabled: function () {
            $('.postal-address').each(function () {
                if ($(this).attr('disabled')) {
                    $(this).removeAttr('disabled');
                } else {
                    $(this).attr('disabled', 'disabled');
                }
            });
            if (!this.email_user.postal_same_as_residential) {
                $('.postal-address').first().focus();
            }
        },
        pinCodesEntered: function () {
            return (
                this.$refs.pin1.value.length == 12 &&
                this.$refs.pin2.value.length == 12
            );
        },
        fetchInitialData: function () {
            let vm = this;
            let initialisers = [
                utils.fetchCountries(),
                utils.fetchLedgerAccount(),
                utils.fetchRequestUserID(),
                utils.fetchOrganisationRequests(),
            ];
            Promise.all(initialisers).then((data) => {
                vm.countries = data[0];
                vm.email_user = data[1].data;
                vm.email_user.id = data[2].id;
                vm.email_user.is_internal = data[2].is_internal;
                vm.organisation_requests = data[3];
                // Convert date to format that the date picker can use
                //vm.email_user.dob = vm.email_user.dob.split("/").reverse().join("-");
                this.$nextTick(() => {
                    if (vm.email_user.postal_same_as_residential) {
                        vm.togglePostalAddressFieldsDisabled();
                    }
                    if (window.location.hash == '#organisations') {
                        let tab_element = document.querySelector(
                            '#organisations-tab-link'
                        );
                        let tab = new bootstrap.Tab(tab_element);
                        tab.show();
                        this.$nextTick(() => {
                            $('#search-organisations').select2('open');
                        });
                    }
                });
            });
        },
        fetchOrganisationRequests: function () {
            let vm = this;
            vm.loadingOrganisationRequests = true;
            utils.fetchOrganisationRequests().then((data) => {
                vm.organisation_requests = data;
                vm.loadingOrganisationRequests = false;
            });
        },
        validateForm: function (formId) {
            let vm = this;
            var form = document.getElementById(formId);

            if (form.checkValidity()) {
                vm.updateDetails();
            } else {
                form.classList.add('was-validated');
                $(form).find('input:invalid').first().focus();
            }

            return false;
        },
        updateDetails: function () {
            let vm = this;
            vm.updatingDetails = true;
            let email_user = { ...vm.email_user };
            email_user.postal_address = { ...vm.email_user.postal_address };
            email_user.residential_address = {
                ...vm.email_user.residential_address,
            };
            // Convert date back to format that the API expects
            email_user.dob = email_user.dob.split('-').reverse().join('/');
            // Remove the read-only fields from the payload
            delete email_user.first_name;
            delete email_user.last_name;
            this.updateAddressFieldNames(email_user);
            email_user.postal_address.postal_same_as_residential =
                vm.email_user.postal_same_as_residential;
            let payload = JSON.stringify({ payload: email_user });
            fetch(vm.api_endpoints.updateAccountDetails(vm.email_user.id), {
                method: 'POST',
                body: payload,
            })
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        return Promise.reject(error);
                    }
                    Swal.fire(
                        'Success',
                        'Details updated successfully',
                        'success'
                    );
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                })
                .finally(() => {
                    vm.updatingDetails = false;
                });
        },
        updateAddressFieldNames: function (email_user) {
            Object.keys(email_user.postal_address).forEach(function (i) {
                email_user.postal_address['postal_' + i] =
                    email_user.postal_address[i];
                delete email_user.postal_address[i];
            });
            Object.keys(email_user.residential_address).forEach(function (i) {
                email_user.residential_address['residential_' + i] =
                    email_user.residential_address[i];
                delete email_user.residential_address[i];
            });
        },
        organisationSelected: function (organisation) {
            this.selectedOrganisation = organisation;
            this.$nextTick(() => {
                $('#pin1').focus();
            });
        },
        searchAgain: function () {
            this.selectedOrganisation = null;
            this.newOrganisation = null;
            this.$nextTick(() => {
                $('#search-organisations').select2('open');
            });
        },
        prepareNewOrganisation: function (term) {
            this.newOrganisation = {};
            let termAbn = Number(term);
            if (!isNaN(termAbn) && Number.isInteger(termAbn)) {
                this.newOrganisation.abn = term;
                this.$nextTick(() => {
                    $('#newOrganisationABN').focus();
                });
            } else {
                this.newOrganisation.name = term;
                this.$nextTick(() => {
                    $('#newOrganisationName').focus();
                });
            }
        },
        validatePinsForm: function () {
            let vm = this;
            var form = document.getElementById('existing-organisation-form');

            if (form.checkValidity()) {
                vm.validatePins();
            } else {
                form.classList.add('was-validated');
                $('#existing-organisation-form')
                    .find('input:invalid')
                    .first()
                    .focus();
            }

            return false;
        },
        validatePins: function () {
            let vm = this;
            vm.validatingPins = true;
            const requestOptions = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vm.pins),
            };
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.organisations,
                    vm.selectedOrganisation.id + '/validate_pins'
                ),
                requestOptions
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        return Promise.reject(error);
                    }
                    if (data.valid) {
                        Swal.fire(
                            'Success',
                            'The pins you entered have been validated and your request will be processed by an organisation administrator.',
                            'success'
                        );
                        vm.selectedOrganisation = null;
                        vm.fetchOrganisationRequests();
                    } else {
                        Swal.fire(
                            'Error',
                            'The pins you entered are not valid. Please check the pins and try again.',
                            'error'
                        );
                    }
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                })
                .finally(() => {
                    vm.validatingPins = false;
                });
        },
        unlinkUser: function (org_id, org_name) {
            let vm = this;
            swal.fire({
                title: 'Unlink from Organisation',
                text:
                    'Are you sure you want to be unlinked from ' +
                    org_name +
                    ' ?',
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Yes, Please Unlink Me',
                reverseButtons: true,
                confirmButtonColor: '#226fbb',
            }).then(async (result) => {
                if (result.isConfirmed) {
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.organisations,
                            org_id + '/unlink_request_user'
                        ),
                        {
                            emulateJSON: true,
                            method: 'POST',
                        }
                    ).then(
                        async (response) => {
                            const data = await response.text();
                            if (!response.ok) {
                                swal.fire(
                                    'Unlink Failed',
                                    'There was an error unlinking you from ' +
                                        org_name +
                                        '. ' +
                                        data.errors[0].detail,
                                    'error'
                                );
                                return;
                            }
                            swal.fire(
                                'Unlink Successful',
                                'You have been successfully unlinked from ' +
                                    org_name +
                                    '.',
                                'success'
                            );
                            vm.organisation_requests =
                                vm.fetchOrganisationRequests();
                        },
                        (error) => {
                            swal.fire(
                                'Unlink Failed',
                                'There was an error unlinking you from ' +
                                    org_name +
                                    '. ' +
                                    error.body,
                                'error'
                            );
                        }
                    );
                }
            });
        },
        validateOrganisationRequest: function () {
            let vm = this;
            var form = document.getElementById('new-organisation-form');

            if (form.checkValidity()) {
                vm.submitOrganisationRequest();
            } else {
                form.classList.add('was-validated');
                $('#new-organisation-form')
                    .find('input:invalid')
                    .first()
                    .focus();
            }

            return false;
        },
        submitOrganisationRequest: function () {
            let vm = this;
            vm.loadingOrganisationRequest = true;
            let data = new FormData();
            data.append('name', vm.newOrganisation.name);
            data.append('abn', vm.newOrganisation.abn);
            data.append('identification', vm.newOrganisation.identification);
            data.append('role', vm.role);
            const requestOptions = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: data,
            };
            fetch(api_endpoints.organisation_requests, requestOptions)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        return Promise.reject(error);
                    }
                    Swal.fire(
                        'Success',
                        'Your request has been submitted successfully. You will be notified once your request has been processed.',
                        'success'
                    );
                    vm.newOrganisation = null;
                    vm.fetchOrganisationRequests();
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error('There was an error!', error);
                })
                .finally(() => {
                    vm.loadingOrganisationRequest = false;
                });
        },
        readFile: function () {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.newOrganisationIdentification)[0];
            if (input.files && input.files[0]) {
                let reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function (e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.newOrganisation.identification = _file;
        },
    },
};
</script>

<style scoped>
.card-header-tabs .nav-link {
    margin-bottom: -1px;
}

.btn-status {
    height: 28px;
}

.col-1 {
    width: 49%;
}

.col-2 {
    width: 16%;
}

.col-3 {
    width: 15%;
}

.col-4 {
    width: 20%;
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
