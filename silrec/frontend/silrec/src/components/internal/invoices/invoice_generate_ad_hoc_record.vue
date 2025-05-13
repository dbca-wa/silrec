<template>
    <div id="raiseAdHocInvoice">
        <modal
            transition="modal fade"
            title="Generate Ad Hoc Invoice Record"
            ok-text="Generate Invoice Record"
            :ok-disabled="generatingAdHocInvoiceRecord"
            cancel-text="Cancel"
            large
            @ok="validateForm"
        >
            <div class="container">
                <div class="row">
                    <div class="col">
                        <form
                            id="generate-ad-hoc-invoice-record-form"
                            class="needs-validation"
                            novalidate
                        >
                            <BootstrapAlert
                                v-if="errors"
                                class="alert alert-danger mb-0"
                                role="alert"
                                icon="exclamation-triangle-fill"
                            >
                                <ErrorRenderer :errors="errors" />
                            </BootstrapAlert>
                            <div class="row mt-3 mb-3">
                                <label
                                    for="approval"
                                    class="col-sm-4 col-form-label"
                                    >Approval</label
                                >
                                <div class="col-sm-8">
                                    <Multiselect
                                        v-if="approvals"
                                        ref="approval"
                                        v-model="invoice.approval"
                                        :custom-label="
                                            (opt) =>
                                                approvals.find(
                                                    (x) => x.id == opt
                                                ).lodgement_number
                                        "
                                        placeholder="Select Approval"
                                        :min-chars="2"
                                        :options="
                                            approvals.map(
                                                (approval) => approval.id
                                            )
                                        "
                                        :allow-empty="false"
                                        :hide-selected="true"
                                        :multiple="false"
                                        :searchable="true"
                                        :loading="loadingApprovals"
                                        @select="
                                            populateOracleCodeFromApproval()
                                        "
                                    />
                                </div>
                            </div>
                            <div class="row mt-3 mb-3">
                                <label
                                    for="amount"
                                    class="col-sm-4 col-form-label"
                                    >Amount</label
                                >
                                <div class="col-sm-8">
                                    <input
                                        id="amount"
                                        v-model="invoice.amount"
                                        type="number"
                                        class="form-control"
                                        step="0.01"
                                        required
                                    />
                                    <div class="invalid-feedback">
                                        Please enter the amount.
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3 mb-3">
                                <label
                                    for="description"
                                    class="col-sm-4 col-form-label"
                                    >Description</label
                                >
                                <div class="col-sm-8">
                                    <textarea
                                        id="description"
                                        v-model="invoice.description"
                                        class="form-control"
                                        required
                                    ></textarea>
                                    <div class="invalid-feedback">
                                        Please enter the description.
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3 mb-3">
                                <label
                                    for="issue-date"
                                    class="col-sm-4 col-form-label"
                                    >Issue Date</label
                                >
                                <div class="col-sm-8">
                                    <input
                                        id="issue-date"
                                        v-model="invoice.date_issued"
                                        class="form-control"
                                        type="date"
                                        required
                                        @change="updateDueDate"
                                    />
                                    <div class="invalid-feedback">
                                        Please enter an issue date.
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3 mb-3">
                                <label
                                    for="due-date"
                                    class="col-sm-4 col-form-label"
                                    >Due Date</label
                                >
                                <div class="col-sm-8">
                                    <input
                                        id="due-date"
                                        v-model="invoice.date_due"
                                        class="form-control"
                                        type="date"
                                        required
                                    />
                                    <div class="invalid-feedback">
                                        Please enter an issue date.
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-3 mb-3">
                                <label
                                    for="oracle-invoice-number"
                                    class="col-sm-4 col-form-label"
                                    >Oracle Invoice Number</label
                                >
                                <div class="col-sm-8">
                                    <input
                                        id="oracle-invoice-number"
                                        v-model="invoice.oracle_invoice_number"
                                        type="text"
                                        class="form-control"
                                        required
                                        maxlength="50"
                                    />
                                    <div class="invalid-feedback">
                                        Please enter the oracle invoice number.
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    for="formFile"
                                    class="col-form-label col-sm-4"
                                    >Oracle Invoice</label
                                >
                                <div class="col-sm-8">
                                    <input
                                        id="oracle-invoice"
                                        class="form-control"
                                        type="file"
                                        data-filetype="application/pdf"
                                        accepts=".pdf"
                                        required
                                    />
                                    <div class="invalid-feedback">
                                        Please select the oracle invoice file
                                        (.pdf)
                                    </div>
                                </div>
                            </div>
                            <div v-if="oracleCodePrepopulated" class="row">
                                <BootstrapAlert
                                    icon="exclamation-triangle-fill"
                                    type="warning"
                                >
                                    <div class="mb-2">
                                        This
                                        <strong
                                            >Receivable Activity Code</strong
                                        >
                                        was prepopulated from the
                                        {{
                                            selectedApproval.approval_type__type
                                        }}.
                                    </div>
                                    <div>
                                        Only change it if you want the funds
                                        allocated to a different code.
                                    </div>
                                </BootstrapAlert>
                            </div>
                            <div class="row mb-3">
                                <label
                                    for="oracle_code"
                                    class="col-form-label col-sm-4"
                                    >Receivable Activity Code</label
                                >
                                <div class="col-sm-8 mb-3">
                                    <Multiselect
                                        v-if="oracle_codes"
                                        id="oracle_code"
                                        ref="oracle_code"
                                        v-model="oracleCode"
                                        :custom-label="
                                            (opt) =>
                                                oracle_codes.find(
                                                    (x) => x.id == opt
                                                )?.code
                                        "
                                        placeholder="Start Typing to Search for a Code"
                                        :options="
                                            oracle_codes.map(
                                                (oracle_code) => oracle_code.id
                                            )
                                        "
                                        :allow-empty="false"
                                        :hide-selected="true"
                                        :multiple="false"
                                        :searchable="true"
                                        :loading="loadingOracleCodes"
                                        :disabled="false"
                                    />
                                </div>
                            </div>

                            <div
                                v-if="generatingAdHocInvoiceRecord"
                                class="col-sm-8"
                            >
                                <BootstrapSpinner
                                    class="text-primary"
                                    :center-of-screen="false"
                                />
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import { api_endpoints } from '@/utils/hooks.js';
import Swal from 'sweetalert2';
import Multiselect from 'vue-multiselect';
import ErrorRenderer from '@common-utils/ErrorRenderer.vue';

export default {
    name: 'InvoiceRaiseAdHoc',
    components: {
        ErrorRenderer,
        modal,
        Multiselect,
    },
    emits: ['adHocInvoiceRecordGenerated'],
    data: function () {
        return {
            isModalOpen: false,
            invoice: {},
            loadingApprovals: false,
            generatingAdHocInvoiceRecord: false,
            approvals: [],
            selectedApproval: null,
            loadingOracleCodes: false,
            oracle_codes: [],
            oracleCode: null,
            errors: null,
        };
    },
    computed: {
        oracleCodePrepopulated: function () {
            return (
                this.selectedApproval &&
                this.selectedApproval.invoicing_details &&
                this.selectedApproval.invoicing_details.oracle_code &&
                this.selectedApproval.invoicing_details.oracle_code ==
                    this.oracleCode
            );
        },
    },
    watch: {
        isModalOpen: function (val) {
            if (val) {
                this.$nextTick(() => {
                    this.focusFirstField();
                });
            }
        },
    },
    created: async function () {
        this.fetchApprovals();
        this.fetchOracleCodes();
    },
    methods: {
        focusFirstField: function () {
            $('#generate-ad-hoc-invoice-record-form')
                .find('input')
                .first()
                .focus();
        },
        updateDueDate: function () {
            if (this.invoice.date_due) {
                return;
            }
            let date_issued = new Date(this.invoice.date_issued);
            let date_due = date_issued.setDate(date_issued.getDate() + 30);
            this.invoice.date_due = new Date(date_due)
                .toISOString()
                .split('T')[0];
        },
        resetInvoice: function () {
            this.invoice = {
                approval: null,
                amount: null,
                description: null,
                date_issued: null,
                date_due: null,
                oracle_invoice_number: null,
            };
            // Clear the file field
            $('#oracle-invoice').val('');
            this.oracleCode = null;
        },
        close: function () {
            var form = document.getElementById(
                'generate-ad-hoc-invoice-record-form'
            );
            form.classList.remove('was-validated');
            this.errors = null;
            this.resetInvoice();
            this.isModalOpen = false;
        },
        confirmUpload: function () {
            Swal.fire({
                title: 'Confirm Ad Hoc Invoice Record Generation',
                text: `You are about to generate an invoice record with the details entered. A payment request will be sent to the lease/licence holder immediately.`,
                icon: 'warning',
                showCancelButton: true,
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((result) => {
                if (result.isConfirmed) {
                    return this.validateForm();
                }
            });
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById(
                'generate-ad-hoc-invoice-record-form'
            );

            if (!this.invoice.approval) {
                this.focusFirstField();
                return;
            }

            let oracleInvoice = document.getElementById('oracle-invoice');
            if (
                !oracleInvoice.files[0] ||
                oracleInvoice.files[0].name.split('.').pop() != 'pdf'
            ) {
                oracleInvoice.setCustomValidity(
                    'The oracle invoice file must be a pdf file.'
                );
            } else {
                oracleInvoice.setCustomValidity('');
            }

            if (form.checkValidity()) {
                if (!vm.oracleCode || vm.oracleCode == 'null') {
                    $('#oracle_code').focus();
                    return;
                }
                vm.generateAdHocInvoiceRecord();
            } else {
                form.classList.add('was-validated');
                $('#oracle-invoice-number-form')
                    .find(':invalid')
                    .first()
                    .focus();
            }

            return false;
        },
        generateAdHocInvoiceRecord: function () {
            let vm = this;
            let oracleInvoice = $('#oracle-invoice').prop('files')[0];
            const formData = new FormData();
            for (let key in this.invoice) {
                formData.append(key, this.invoice[key]);
            }
            formData.append('invoice_pdf', oracleInvoice);
            formData.append('oracle_code', vm.oracleCode);
            const requestOptions = {
                method: 'POST',
                body: formData,
            };
            vm.generatingAdHocInvoiceRecord = true;
            fetch(
                api_endpoints.invoices + 'generate_ad_hoc_invoice/',
                requestOptions
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        vm.errors = data;
                        return;
                    }
                    vm.$emit('adHocInvoiceRecordGenerated', data);
                    vm.resetInvoice();
                    Swal.fire({
                        title: 'Ad Hoc Invoice Record Generated',
                        text: `The ad hoc invoice record has been generated.`,
                        icon: 'success',
                        showConfirmButton: false,
                        timer: 2000,
                    });
                    vm.close();
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    Promise.reject(error);
                })
                .finally(() => {
                    vm.generatingAdHocInvoiceRecord = false;
                });
        },
        fetchApprovals: async function () {
            let vm = this;
            vm.loadingApprovals = true;

            fetch(api_endpoints.approvals + 'key-value-list/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                    }
                    vm.approvals = data;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                })
                .finally(() => {
                    vm.loadingApprovals = false;
                });
        },
        populateOracleCodeFromApproval: async function () {
            let vm = this;
            vm.loadingApprovals = true;

            fetch(api_endpoints.approvals + vm.invoice.approval + '/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                    }
                    vm.selectedApproval = data;
                    if (
                        vm.selectedApproval &&
                        vm.selectedApproval.invoicing_details &&
                        vm.selectedApproval.invoicing_details.oracle_code
                    ) {
                        vm.oracleCode =
                            vm.selectedApproval.invoicing_details.oracle_code;
                    }
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                })
                .finally(() => {
                    vm.loadingApprovals = false;
                });
        },
        fetchOracleCodes: async function () {
            let vm = this;
            try {
                vm.loadingOracleCodes = true;
                const res = await fetch(
                    api_endpoints.oracle_codes + 'key-value-list/'
                );
                if (!res.ok) throw new Error(res.statusText); // 400s or 500s error
                vm.oracle_codes = await res.json();
                vm.loadingOracleCodes = false;
            } catch (err) {
                console.error({ err });
            }
        },
    },
};
</script>
