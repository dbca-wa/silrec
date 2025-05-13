<template lang="html">
    <div id="internal-compliance-amend">
        <modal
            transition="modal fade"
            :title="
                'Amendment Request for Compliance: ' +
                compliance_lodgement_number
            "
            large
            :ok-disabled="loading"
            @ok="validateForm()"
            @cancel="close()"
        >
            <div class="container-fluid">
                <div class="row py-3">
                    <form
                        class="needs-validation"
                        name="complianceAmendmentRequestForm"
                        novalidate
                    >
                        <VueAlert v-model:show="showError" type="danger"
                            ><strong v-html="errorString"></strong
                        ></VueAlert>
                        <div class="col">
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-2"
                                    for="reasons"
                                    >Reason</label
                                >
                                <div class="col-sm-10">
                                    <select
                                        id="reasons"
                                        ref="reasons"
                                        v-model="amendment.reason"
                                        class="form-select"
                                        name="reasons"
                                        required
                                    >
                                        <option
                                            v-for="reason in reason_choices"
                                            :key="reason.key"
                                            :value="reason.key"
                                        >
                                            {{ reason.value }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                            <div class="row">
                                <label
                                    class="col-form-label col-sm-2"
                                    for="text"
                                    >Details</label
                                >
                                <div class="col-sm-10">
                                    <textarea
                                        id="text"
                                        ref="text"
                                        v-model="amendment.text"
                                        class="form-control"
                                        name="text"
                                        required
                                    ></textarea>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <BootstrapSpinner
                v-if="loading"
                class="text-primary"
                :center-of-screen="false"
            />
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import VueAlert from '@vue-utils/alert.vue';
import { helpers } from '@/utils/hooks.js';

export default {
    name: 'ComplianceAmendmentRequest',
    components: {
        modal,
        VueAlert,
    },
    props: {
        compliance_id: {
            type: Number,
            required: true,
        },
        compliance_lodgement_number: {
            type: String,
            required: true,
        },
    },
    data: function () {
        let vm = this;
        return {
            isModalOpen: false,
            form: null,
            amendment: {
                reason: '',
                amendingcompliance: false,
                compliance: vm.compliance_id,
            },
            reason_choices: null,
            loading: false,
            errors: false,
            errorString: '',
            validation_form: null,
        };
    },
    computed: {
        showError: function () {
            var vm = this;
            return vm.errors;
        },
    },
    watch: {
        isModalOpen: function (val) {
            if (val) {
                this.$nextTick(() => {
                    this.$refs.text.focus();
                });
            }
        },
    },
    mounted: function () {
        let vm = this;
        vm.form = document.forms.complianceAmendmentRequestForm;
        vm.fetchAmendmentChoices();
    },
    methods: {
        close: function () {
            this.isModalOpen = false;
        },
        fetchAmendmentChoices: async function () {
            const url = '/api/compliance_amendment_reason_choices.json';
            this.reason_choices = await helpers.fetchWrapper(url);
            this.amendment.reason = this.reason_choices[0].key;
        },
        validateForm: function () {
            let vm = this;
            if ($(vm.form).valid()) {
                vm.sendData();
            }
        },
        sendData: async function () {
            let vm = this;
            vm.amendingcompliance = true;
            vm.loading = true;
            vm.errors = false;
            const amendment = JSON.stringify(vm.amendment);
            const url = '/api/compliance_amendment_request.json';
            const response = await fetch(url, {
                method: 'POST',
                body: amendment,
            });
            if (!response.ok) {
                vm.errors = true;
                this.errorString = await helpers.parseFetchError(response);
                vm.amendingcompliance = false;
            } else {
                this.loading = false;
                new swal(
                    'Sent',
                    `An email has been sent to applicant with the request to amend compliance ${vm.compliance_lodgement_number}.`,
                    'success'
                );
                vm.amendingcompliance = false;
                vm.close();
                vm.$router.push({ name: 'internal-compliances-dash' }); //Navigate to dashboard after creating Amendment request
            }
        },
        eventListerners: function () {
            let vm = this;

            // Intialise select2
            $(vm.$refs.reasons)
                .select2({
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder: 'Select Reason',
                })
                .on('select2:select', function (e) {
                    var selected = $(e.currentTarget);
                    vm.amendment.reason = selected.val();
                })
                .on('select2:unselect', function (e) {
                    var selected = $(e.currentTarget);
                    vm.amendment.reason = selected.val();
                });
        },
    },
};
</script>
