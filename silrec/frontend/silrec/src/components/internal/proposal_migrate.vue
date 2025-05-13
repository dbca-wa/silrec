<template lang="html">
    <div class="container">
        <div class="row">
            <div class="col-sm-12">
                <FormSection label="New or Existing?" index="propsal_migrate">
                    <div class="col">
                        <div class="row mb-3 align-items-center">
                            <label
                                for="profit_and_loss_documents"
                                class="col-form-label"
                            ></label>
                            <div class="col-6 col-form-label">
                                Are you creating a new lease/license or
                                migrating an existing one?
                            </div>
                            <div class="col">
                                <div class="form-check mb-2">
                                    <input
                                        id="flexRadioDefault1"
                                        v-model="migrated"
                                        class="form-check-input"
                                        type="radio"
                                        name="flexRadioDefault"
                                        :value="false"
                                    />
                                    <label
                                        class="form-check-label"
                                        for="flexRadioDefault1"
                                    >
                                        Create New
                                    </label>
                                </div>
                                <div class="form-check form-check-inline">
                                    <input
                                        id="flexRadioDefault2"
                                        v-model="migrated"
                                        class="form-check-input"
                                        type="radio"
                                        name="flexRadioDefault"
                                        :value="true"
                                    />
                                    <label
                                        class="form-check-label"
                                        for="flexRadioDefault2"
                                    >
                                        Migrate Existing
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div
                            v-if="migrated"
                            class="row mb-3 align-items-center"
                        >
                            <div class="col-3 col-form-label">
                                Original Lease/License Number
                            </div>
                            <div class="col-5">
                                <input
                                    ref="original-lease-license-number"
                                    v-model="original_leaselicence_number"
                                    type="text"
                                    class="form-control"
                                    placeholder="Enter the original lease/license number"
                                    autofocus
                                />
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col">
                                <BootstrapAlert v-if="migrated">
                                    Backdated invoices and an invoice for the
                                    current billing period
                                    <strong><u>will not be</u></strong>
                                    generated for a lease or license that is
                                    being migrated. <br />Only invoices for
                                    future billing periods will be generated.
                                </BootstrapAlert>
                                <BootstrapAlert v-else>
                                    Backdated invoices and an invoice for the
                                    current billing period
                                    <strong><u>will be</u></strong> generated
                                    for a new lease or license when the
                                    commencement date is in the past.
                                </BootstrapAlert>
                            </div>
                        </div>
                    </div>
                </FormSection>
                <FormSection
                    label="Select Proponent"
                    index="proposal_apply_on_behalf_of"
                >
                    <div
                        v-if="!addingNewUser && !addingNewOrganisation"
                        class="container"
                    >
                        <form>
                            <div class="mb-3 row">
                                <label
                                    for="inputName"
                                    class="col-3 col-form-label"
                                    >Select Proponent Type:</label
                                >
                                <div class="col-5">
                                    <ul class="list-group">
                                        <li class="list-group-item">
                                            <div class="form-check">
                                                <input
                                                    id=""
                                                    v-model="applicantType"
                                                    class="form-check-input"
                                                    type="radio"
                                                    name="transferee_type"
                                                    value="organisation"
                                                    @change="
                                                        transfereeTypeChanged
                                                    "
                                                />
                                                <label
                                                    class="form-check-label"
                                                    for=""
                                                >
                                                    Organisation
                                                </label>
                                            </div>
                                        </li>
                                        <li class="list-group-item">
                                            <div class="form-check">
                                                <input
                                                    id=""
                                                    v-model="applicantType"
                                                    class="form-check-input"
                                                    type="radio"
                                                    name="transferee_type"
                                                    value="individual"
                                                    @change="
                                                        transfereeTypeChanged
                                                    "
                                                />
                                                <label
                                                    class="form-check-label"
                                                    for=""
                                                >
                                                    Individual
                                                </label>
                                            </div>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            <div
                                v-if="applicantType == 'organisation'"
                                class="row mb-3"
                            >
                                <div class="col-3">Select Organisation</div>
                                <div class="col-5">
                                    <select
                                        id="search"
                                        ref="search"
                                        class="form-select"
                                        placeholder="Start typing the Organisation's Name or ABN"
                                    />
                                </div>
                            </div>
                            <div
                                v-if="applicantType == 'individual'"
                                class="row mb-3"
                            >
                                <div class="col-3">Select Individual</div>
                                <div class="col-5">
                                    <select
                                        id="search"
                                        ref="search"
                                        class="form-select"
                                        placeholder="Start typing the individual's name or email"
                                    />
                                </div>
                            </div>
                        </form>
                    </div>
                    <div v-else class="container">
                        <div class="row">
                            <div class="col-8">
                                <form
                                    id="newForm"
                                    name="newForm"
                                    class="needs-validation"
                                    novalidate
                                    @submit.prevent="validateForm"
                                >
                                    <fieldset
                                        v-if="addingNewUser"
                                        class="rounded-3 border p-3"
                                    >
                                        <legend class="float-none w-auto px-3">
                                            Add New Email User
                                        </legend>
                                        <div class="row mb-3">
                                            <label
                                                for="email"
                                                class="col-sm-3 col-form-label"
                                                >Email</label
                                            >
                                            <div class="col-sm-9">
                                                <input
                                                    id="email"
                                                    ref="email"
                                                    v-model="newUser.email"
                                                    type="email"
                                                    class="form-control"
                                                />
                                                <div class="invalid-feedback">
                                                    Please enter a valid email
                                                    address
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            type="submit"
                                            class="btn btn-primary float-end"
                                        >
                                            Add and Select New Email User
                                        </button>
                                        <button
                                            class="btn btn-secondary float-end me-2"
                                            @click.prevent="cancelAddNew"
                                        >
                                            Cancel
                                        </button>
                                    </fieldset>
                                    <fieldset
                                        v-if="
                                            addingNewOrganisation &&
                                            !addingNewUser
                                        "
                                        class="rounded-3 border p-3"
                                    >
                                        <legend class="float-none w-auto px-3">
                                            Add New Organisation
                                        </legend>
                                        <div class="row mb-3">
                                            <label
                                                for="organisation-name"
                                                class="col-sm-3 col-form-label"
                                                >Organisation Name</label
                                            >
                                            <div class="col-sm-9">
                                                <input
                                                    id="organisation-name"
                                                    ref="organisation-name"
                                                    v-model="
                                                        newOrganisation.ledger_organisation_name
                                                    "
                                                    type="text"
                                                    class="form-control"
                                                    maxlength="255"
                                                    required
                                                />
                                                <div class="invalid-feedback">
                                                    Please enter the
                                                    organisation name
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3">
                                            <label
                                                for="trading-name"
                                                class="col-sm-3 col-form-label"
                                                >Trading Name</label
                                            >
                                            <div class="col-sm-9">
                                                <input
                                                    id="trading-name"
                                                    v-model="
                                                        newOrganisation.ledger_organisation_trading_name
                                                    "
                                                    type="text"
                                                    maxlength="255"
                                                    class="form-control"
                                                />
                                            </div>
                                        </div>
                                        <div class="row mb-3">
                                            <label
                                                for="abn"
                                                class="col-sm-3 col-form-label"
                                                ><span
                                                    v-if="
                                                        newOrganisation
                                                            .ledger_organisation_abn
                                                            .length == 9
                                                    "
                                                    >ABN</span
                                                >
                                                <span
                                                    v-else-if="
                                                        newOrganisation
                                                            .ledger_organisation_abn
                                                            .length == 11
                                                    "
                                                    >ACN</span
                                                >
                                                <span v-else> ABN / ACN </span>
                                            </label>
                                            <div class="col-sm-9">
                                                <input
                                                    id="abn"
                                                    v-model="
                                                        newOrganisation.ledger_organisation_abn
                                                    "
                                                    type="text"
                                                    class="form-control"
                                                    pattern="\d*"
                                                    required
                                                    maxlength="11"
                                                    @change="validateABNACN"
                                                />
                                                <div class="invalid-feedback">
                                                    Please enter a valid abn or
                                                    ACN
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3">
                                            <label
                                                for="email"
                                                class="col-sm-3 col-form-label"
                                                >Email</label
                                            >
                                            <div class="col-sm-9">
                                                <input
                                                    id="email"
                                                    ref="email"
                                                    v-model="
                                                        newOrganisation.ledger_organisation_email
                                                    "
                                                    type="email"
                                                    class="form-control"
                                                    required
                                                />
                                                <div class="invalid-feedback">
                                                    Please enter a valid email
                                                    address
                                                </div>
                                            </div>
                                        </div>
                                        <div class="row mb-3">
                                            <BootstrapAlert>
                                                The organisation must have an
                                                admin user who will have access
                                                to the organisation's pin codes
                                                and be able to approve linking
                                                requests from new users.
                                            </BootstrapAlert>
                                        </div>
                                        <div class="row mb-3">
                                            <label
                                                for="email"
                                                class="col-sm-3 col-form-label"
                                                >Admin User</label
                                            >
                                            <div class="col-sm-9">
                                                <select
                                                    id="search"
                                                    ref="search"
                                                    v-model="
                                                        newOrganisation.admin_user_id
                                                    "
                                                    class="form-select"
                                                    placeholder="Start typing the individual's name or email"
                                                    required
                                                />
                                                <div class="invalid-feedback">
                                                    Please select an admin user
                                                    for the new organisation
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            type="submit"
                                            class="btn btn-primary float-end"
                                        >
                                            Add and Select New Organisation
                                        </button>
                                        <button
                                            class="btn btn-secondary float-end me-2"
                                            @click.prevent="cancelAddNew"
                                        >
                                            Cancel
                                        </button>
                                    </fieldset>
                                </form>
                            </div>
                        </div>
                    </div>
                </FormSection>
                <div class="col-sm-12">
                    <button
                        v-if="!creatingProposal"
                        :disabled="continueDisabed"
                        class="btn btn-primary float-end continue"
                        @click.prevent="submit()"
                    >
                        Continue
                    </button>
                    <BootstrapButtonSpinner
                        v-else
                        class="btn btn-primary float-end continue"
                        :is-loading="true"
                        :center-of-screen="false"
                        :small="true"
                    />
                </div>
            </div>
            <BootstrapSpinner
                v-if="loading"
                class="text-primary"
                :is-loading="true"
            />
        </div>
    </div>
</template>
<script>
import FormSection from '@/components/forms/section_toggle.vue';
import { api_endpoints } from '@/utils/hooks';
export default {
    name: 'ProposalMigrate',
    components: {
        FormSection,
    },
    data: function () {
        return {
            loading: false,
            selectedApplication: null,
            searchApiEndpoint: api_endpoints.organisation_lookup,
            searchPlaceholder: 'Start typing the Organisation Name or ABN',
            applicantType: 'organisation',
            // The user can add a new user in the process of adding a new organisation
            // so we need seperate variables to keep track of the applicant type in gnenral vs the appcliant type for the select2
            select2applicantType: 'organisation',
            applicant: null,
            applicantName: null,
            creatingProposal: false,
            addingNewUser: false,
            addingNewOrganisation: false,
            newUser: null,
            newOrganisation: null,
            migrated: false,
            original_leaselicence_number: null,
        };
    },
    computed: {
        createMigrateLabel: function () {
            let label = 'Create a new';
            if (this.migrated) {
                label = 'Migrate an existing';
            }
            return label;
        },
        abnAcnLabel: function () {
            let label = 'ABN / ACN';
            if (
                this.newOrganisation &&
                this.newOrganisation.ledger_organisation_abn.length == 11
            ) {
                label = 'ACN';
            }
            if (
                this.newOrganisation &&
                this.newOrganisation.ledger_organisation_abn.length == 9
            ) {
                label = 'ABN';
            }
            return label;
        },
        alertText: function () {
            let text = '';
            if (
                this.selectedApplication &&
                this.selectedApplication.description
            ) {
                text = this.selectedApplication.description;
            }
            text = 'a ' + text;
            return text;
        },
        continueDisabed: function () {
            if (this.migrated && !this.original_leaselicence_number) {
                return true;
            }
            if (this.addingNewOrganisation) {
                return true;
            }
            return !this.applicant;
        },
    },
    watch: {
        migrated: function () {
            if (this.migrated) {
                this.$nextTick(() => {
                    this.$refs['original-lease-license-number'].focus();
                });
            } else {
                this.original_leaselicence_number = null;
            }
        },
    },
    created: function () {
        this.initNewUser();
        this.initNewOrganisation();
    },
    mounted: function () {
        this.setPlaceholderAndApiEndpoint();
    },
    methods: {
        initNewUser: function () {
            this.newUser = { email: '' };
        },
        initNewOrganisation: function () {
            this.newOrganisation = {
                ledger_organisation_name: '',
                ledger_organisation_trading_name: '',
                ledger_organisation_abn: '',
                ledger_organisation_email: '',
                admin_user_id: null,
            };
        },
        validateABNACN: function (event) {
            var abnAcn = event.target;
            if (abnAcn.value.length != 9 && abnAcn.value.length != 11) {
                abnAcn.setCustomValidity(
                    'Please enter a valid ABN or ACN (9 or 11 digits)'
                );
            } else {
                abnAcn.setCustomValidity('');
            }
        },
        addNewLedgerEmailuser: async function () {
            this.loading = true;
            let res = await fetch(
                api_endpoints.proposal + 'add_new_ledger_emailuser/',
                {
                    body: JSON.stringify(this.newUser),
                    method: 'POST',
                }
            );
            const data = await res.json();
            this.loading = false;
            if (!res.status == 200) {
                console.error(data.message);
                swal.fire({
                    title: 'Add New Email User Failed',
                    text: 'There was an error attempting to add the new email user. Please try again later.',
                    icon: 'error',
                });
                return;
            }
            this.addingNewUser = false;
            this.$nextTick(() => {
                this.initialiseSearch();
            });
            this.$nextTick(() => {
                let newOption = new Option(
                    data.data.email,
                    data.data.emailuser_id,
                    true,
                    true
                );
                $('#search').append(newOption);
                $('#search').trigger('change');
                if (this.addingNewOrganisation) {
                    this.newOrganisation.admin_user_id = data.data.emailuser_id;
                    this.applicantType = 'organisation';
                } else {
                    this.applicant = data.data.emailuser_id;
                    this.applicantName = data.data.email;
                }

                swal.fire({
                    title: 'New User Created Successfully',
                    text: 'The new email user has been created and selected.',
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false,
                });
            });
        },
        addNewOrganisation: async function () {
            this.loading = true;
            let res = await fetch(api_endpoints.create_organisation, {
                body: JSON.stringify(this.newOrganisation),
                method: 'POST',
            });
            const data = await res.json();
            const status = await res.status;
            this.loading = false;
            if (status != 200) {
                console.error(data.errors[0].detail);
                swal.fire({
                    title: 'Add New Organisation Failed',
                    text: data.errors[0].detail,
                    icon: 'error',
                });
                return;
            }
            this.addingNewOrganisation = false;
            this.applicantType = 'organisation';
            this.$nextTick(() => {
                this.initialiseSearch();
            });
            this.$nextTick(() => {
                let newOption = new Option(
                    data.ledger_organisation_name,
                    data.id,
                    true,
                    true
                );
                $('#search').append(newOption);
                $('#search').trigger('change');
                this.applicant = data.id;
                this.applicantName = data.ledger_organisation_name;
                swal.fire({
                    title: 'New Organisation Created Successfully',
                    text: 'The new organisation has been created and selected.',
                    icon: 'success',
                    timer: 2000,
                    showConfirmButton: false,
                });
            });
        },
        cancelAddNew: function () {
            this.addingNewUser = false;
            this.addingNewOrganisation = false;
            this.applicantType = 'organisation';
            this.select2ApplicantType = 'organisation';
            this.initNewUser();
            this.initNewOrganisation();
            this.$nextTick(() => {
                this.initialiseSearch();
                this.$nextTick(() => {
                    $('#search').select2('open');
                });
            });
        },
        submit: function () {
            let vm = this;
            swal.fire({
                title: `${vm.createMigrateLabel} Lease License`,
                text: `Are you sure you want to ${vm.createMigrateLabel.toLowerCase()} lease/license for ${
                    vm.applicantName
                }?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Proceed',
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(
                (result) => {
                    if (result.isConfirmed) {
                        this.migrateProposal();
                    }
                },
                (error) => {
                    console.error(error);
                }
            );
        },
        setPlaceholderAndApiEndpoint: function () {
            if (this.select2applicantType == 'individual') {
                this.searchPlaceholder =
                    "Start typing the Individual's Name or Email";
                this.searchApiEndpoint = api_endpoints.person_lookup;
                this.initialiseSearch();
            } else {
                this.searchPlaceholder =
                    'Start typing the Organisation Name or ABN';
                this.searchApiEndpoint = api_endpoints.organisation_lookup;
                this.initialiseSearch();
            }
        },
        transfereeTypeChanged: function () {
            if (this.applicantType == 'individual') {
                this.select2applicantType = 'individual';
            } else {
                this.select2applicantType = 'organisation';
            }
            this.setPlaceholderAndApiEndpoint();
            setTimeout(() => {
                this.initialiseSearch();
                $('#search').select2('open');
                this.resetApplicant();
            }, 200);
        },
        initialiseSearch: function () {
            let vm = this;
            $('#search')
                .select2({
                    minimumInputLength: 2,
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder: vm.searchPlaceholder,
                    ajax: {
                        url: vm.searchApiEndpoint,
                        dataType: 'json',
                        data: function (params) {
                            let query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
                        },
                        processResults: function (data, params) {
                            if (data.results.length == 0) {
                                swal.fire({
                                    title: 'No Results Found',
                                    html: `<p>No results found for the search term '${params.term}'.</p><p> Would you like to add a new ${vm.select2applicantType} to the ledger database?</p>`,
                                    icon: 'question',
                                    confirmButtonText: 'Yes please',
                                    cancelButtonText: 'Search Again',
                                    showCancelButton: true,
                                    reverseButtons: true,
                                    buttonsStyling: false,
                                    customClass: {
                                        confirmButton: 'btn btn-primary',
                                        cancelButton: 'btn btn-secondary me-2',
                                    },
                                }).then(async (result) => {
                                    if (result.isConfirmed) {
                                        $('#search').select2('destroy');
                                        if (
                                            vm.select2applicantType ==
                                            'individual'
                                        ) {
                                            vm.addingNewUser = true;
                                        } else {
                                            vm.addingNewOrganisation = true;
                                        }
                                        vm.$nextTick(() => {
                                            if (
                                                vm.select2applicantType ==
                                                'individual'
                                            ) {
                                                vm.newUser.email = params.term;
                                                vm.$refs.email.focus();
                                            } else {
                                                if (
                                                    /^\d+$/.test(
                                                        params.term.replace(
                                                            /\s/g,
                                                            ''
                                                        )
                                                    )
                                                ) {
                                                    vm.newOrganisation.ledger_organisation_abn =
                                                        params.term;
                                                } else {
                                                    vm.newOrganisation.ledger_organisation_name =
                                                        params.term;
                                                }
                                                vm.$refs[
                                                    'organisation-name'
                                                ].focus();
                                                // Get the select2 ready to select the admin user for the new organisation
                                                vm.select2applicantType =
                                                    'individual';
                                                vm.setPlaceholderAndApiEndpoint();
                                                vm.initialiseSearch();
                                            }
                                        });
                                    } else {
                                        $('#search').select2('open');
                                    }
                                });
                            }
                            return {
                                results: data.results,
                            };
                        },
                    },
                })
                .on('select2:open', function () {
                    const searchField = $(
                        `[aria-controls='select2-search-results']`
                    );
                    searchField[0].focus();
                })
                .on('select2:select', function (e) {
                    vm.applicant = e.params.data.id;
                    vm.applicantName = e.params.data.text;
                    if (vm.addingNewOrganisation) {
                        vm.newOrganisation.admin_user_id = vm.applicant;
                    }
                    document.activeElement.blur();
                })
                .on('select2:clear', function () {
                    vm.resetApplicant();
                });
        },
        resetApplicant: function () {
            this.applicant = null;
            if (this.addingNewOrganisation) {
                this.newOrganisation.admin_user_id = null;
            }
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById('newForm');

            if (form.checkValidity()) {
                if (vm.applicantType == 'organisation' && !vm.addingNewUser) {
                    vm.addNewOrganisation();
                } else {
                    vm.addNewLedgerEmailuser();
                }
            } else {
                form.classList.add('was-validated');
                $('#newForm').find('input:invalid').first().focus();
            }

            return false;
        },
        migrateProposal: async function () {
            this.$nextTick(async () => {
                let res = null;
                try {
                    this.creatingProposal = true;
                    let payload = {
                        ind_applicant: null,
                        org_applicant: null,
                        migrated: this.migrated,
                        original_leaselicence_number:
                            this.original_leaselicence_number,
                    };

                    if (this.applicantType == 'individual') {
                        payload.ind_applicant = this.applicant;
                    } else {
                        payload.org_applicant = this.applicant;
                    }
                    res = await fetch(api_endpoints.proposal + 'migrate/', {
                        body: JSON.stringify(payload),
                        method: 'POST',
                    });
                    const resData = await res.json();
                    const proposal = Object.assign({}, resData);
                    this.$router.push({
                        name: 'internal-proposal',
                        params: { proposal_id: proposal.id },
                    });
                } catch (error) {
                    console.error(error);
                    await swal.fire({
                        title: 'Create Proposal',
                        icon: 'error',
                        text: 'There was an error attempting to create the proposal application. Please try again later.',
                    });
                    this.$router.go();
                }
            });
        },
    },
};
</script>

<style scoped lang="css">
button.continue {
    width: 150px;
}
</style>
