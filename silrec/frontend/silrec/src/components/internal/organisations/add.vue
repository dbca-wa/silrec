<template>
    <div id="internal-add-organisation" class="container">
        <div class="row">
            <div class="col">
                <h3>Add Organisation</h3>
            </div>
        </div>
        <div v-if="errors" class="row">
            <div class="col">
                <BootstrapAlert type="danger" icon="exclamation-triangle-fill">
                    <ErrorRenderer :errors="errors" />
                </BootstrapAlert>
            </div>
        </div>
        <div class="row">
            <div class="col-6">
                <form
                    id="organisation-form"
                    class="needs-validation"
                    novalidate
                >
                    <div class="mb-3">
                        <label
                            for="ledger_organisation_name"
                            class="form-label fw-bold"
                            >Name</label
                        >
                        <input
                            id="ledger_organisation_name"
                            ref="ledger_organisation_name"
                            v-model="organisation.ledger_organisation_name"
                            type="text"
                            class="form-control"
                            required
                            autofocus
                        />
                        <div class="invalid-feedback">Please enter a name.</div>
                    </div>
                    <div class="mb-3">
                        <label
                            for="ledger_organisation_trading_name"
                            class="form-label"
                            >Trading Name</label
                        >
                        <input
                            id="ledger_organisation_trading_name"
                            v-model="
                                organisation.ledger_organisation_trading_name
                            "
                            type="text"
                            class="form-control"
                        />
                    </div>
                    <div class="mb-3">
                        <label
                            for="ledger_organisation_abn"
                            class="form-label fw-bold"
                            >ABN / ACN</label
                        >
                        <input
                            id="ledger_organisation_abn"
                            v-model="organisation.ledger_organisation_abn"
                            type="text"
                            class="form-control"
                            required
                        />
                        <div class="invalid-feedback">
                            Please enter an abn/acn.
                        </div>
                    </div>
                    <div class="mb-3">
                        <label
                            for="ledger_organisation_email"
                            class="form-label fw-bold"
                            >Email</label
                        >
                        <input
                            id="ledger_organisation_email"
                            v-model="organisation.ledger_organisation_email"
                            type="email"
                            class="form-control"
                            required
                        />
                        <div class="invalid-feedback">
                            Please enter a valid email.
                        </div>
                    </div>
                    <button
                        type="submit"
                        class="btn btn-primary me-2"
                        @click.prevent="validateForm(true)"
                    >
                        Add and Exit
                    </button>
                    <button
                        type="submit"
                        class="btn btn-primary"
                        @click.prevent="validateForm(false)"
                    >
                        Add and Continue (Add Another)
                    </button>
                </form>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks.js';

import ErrorRenderer from '@common-utils/ErrorRenderer.vue';

export default {
    name: 'InternalOrganisationAdd',
    components: {
        ErrorRenderer,
    },
    data: function () {
        return {
            organisation: this.emptyOrganisation(),
            errors: null,
        };
    },
    methods: {
        emptyOrganisation: function () {
            return {
                ledger_organisation_name: '',
                ledger_organisation_trading_name: '',
                ledger_organisation_abn: '',
                ledger_organisation_email: '',
            };
        },
        validateForm: function (exit = false) {
            let vm = this;
            var form = document.getElementById('organisation-form');
            vm.errors = null;

            if (form.checkValidity()) {
                vm.addOrganisation(exit);
            } else {
                form.classList.add('was-validated');
                $('#organisation-form').find(':invalid').first().focus();
            }

            return false;
        },
        addOrganisation: async function (exit = false) {
            let vm = this;
            const requestOptions = {
                method: 'POST',
                body: JSON.stringify(vm.organisation),
            };
            await fetch(api_endpoints.organisations, requestOptions).then(
                async (response) => {
                    if (!response.ok) {
                        const data = await response.json();
                        vm.errors = data.errors;
                        return;
                    }
                    swal.fire({
                        title: 'Organisation Added',
                        text: 'The organisation has been added successfully.',
                        icon: 'success',
                        showConfirmButton: false,
                        timer: 1500,
                        didClose: () => {
                            if (exit) {
                                vm.$router.push({
                                    name: 'organisations-dashboard',
                                });
                            } else {
                                vm.organisation = vm.emptyOrganisation();
                                let form =
                                    document.getElementById(
                                        'organisation-form'
                                    );
                                form.classList.remove('was-validated');
                                form.reset();
                                vm.$refs.ledger_organisation_name.focus();
                            }
                        },
                    });
                }
            );
        },
    },
};
</script>
