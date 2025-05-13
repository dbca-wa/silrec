<template>
    <div :id="'approvalCancellation' + approval_id">
        <modal
            transition="modal fade"
            :title="title"
            large
            @ok="validateForm()"
            @cancel="close()"
        >
            <div class="container-fluid">
                <div class="row">
                    <form
                        id="approvalCancellationForm"
                        class="form-horizontal required-validation"
                        name="approvalCancellationForm"
                        novalidate
                    >
                        <alert v-if="errorString" type="danger"
                            ><strong>{{ errorString }}</strong></alert
                        >
                        <div class="col-sm-12">
                            <div class="row mb-3">
                                <label
                                    class="col-sm-3 col-form-label"
                                    for="cancellation_date"
                                    >Cancellation Date</label
                                >
                                <div class="col-sm-9">
                                    <div
                                        ref="cancellation_date"
                                        class="input-group date"
                                    >
                                        <input
                                            id="cancellation_date"
                                            v-model="
                                                approval_cancellation.cancellation_date
                                            "
                                            type="date"
                                            class="form-control"
                                            placeholder="DD/MM/YYYY"
                                            name="cancellation_date"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please select the cancellation date.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    class="col-sm-3 col-form-label"
                                    for="cancellation_details"
                                    >Cancellation Details</label
                                >
                                <div class="col-sm-9">
                                    <textarea
                                        v-model="
                                            approval_cancellation.cancellation_details
                                        "
                                        name="cancellation_details"
                                        class="cancellation-details form-control"
                                        required
                                    ></textarea>
                                    <div class="invalid-feedback">
                                        Please enter some details about the
                                        cancellation.
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    class="col-sm-3 col-form-label"
                                    for="files"
                                    >Files</label
                                >
                                <div class="col-sm-9">
                                    <FileField
                                        v-if="approval_id"
                                        id="approval_cancellation_documents"
                                        ref="approval_cancellation_documents"
                                        :key="approval_id"
                                        name="approval_cancellation_documents"
                                        :is-repeatable="true"
                                        :document-action-url="
                                            approvalCancellationDocumentsUrl
                                        "
                                        :replace_button_by_text="true"
                                    />
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import FileField from '@/components/forms/filefield_immediate.vue';
import alert from '@vue-utils/alert.vue';
import { helpers, api_endpoints, utils } from '@/utils/hooks.js';
import Swal from 'sweetalert2';

export default {
    name: 'CancelApproval',
    components: {
        modal,
        alert,
        FileField,
    },
    props: {
        approval_id: {
            type: Number,
            default: null,
        },
        approval_lodgement_number: {
            type: String,
            default: null,
        },
    },
    data: function () {
        return {
            isModalOpen: false,
            form: null,
            approval_cancellation: {
                cancellation_date: new Date().toISOString().slice(0, 10),
            },
            state: 'proposed_approval',
            validation_form: null,
            errorString: '',
        };
    },
    computed: {
        title: function () {
            return 'Cancel Approval ' + this.approval_lodgement_number;
        },
        approvalCancellationDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.approvals,
                this.approval_id + '/process_approval_cancellation_document'
            );
        },
    },
    methods: {
        resetForm: function () {
            this.isModalOpen = false;
            this.approval_cancellation = {
                cancellation_date: new Date().toISOString().slice(0, 10),
            };
            this.errorString = '';
        },
        close: function () {
            var form = document.getElementById('approvalCancellationForm');
            form.classList.remove('was-validated');
            this.resetForm();
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById('approvalCancellationForm');

            if (form.checkValidity()) {
                vm.sendData();
            } else {
                form.classList.add('was-validated');
                $('#approvalCancellationForm').find(':invalid').first().focus();
            }

            return false;
        },
        sendData: function () {
            let vm = this;
            let approval_cancellation = Object.assign(
                {},
                vm.approval_cancellation
            );
            approval_cancellation.cancellation_date = helpers.formatDateForAPI(
                vm.approval_cancellation.cancellation_date
            );
            const requestOptions = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(approval_cancellation),
            };
            let url = helpers.add_endpoint_json(
                api_endpoints.approvals,
                vm.approval_id + '/approval_cancellation'
            );

            utils
                .fetchUrl(url, requestOptions)
                .then((data) => {
                    vm.close();
                    Swal.fire({
                        title: 'Cancelled',
                        text: 'An email has been sent to the lease/licence holder regarding the cancellation of this approval',
                        icon: 'success',
                        showCancelButton: false,
                        confirmButtonText: 'Ok',
                        buttonsStyling: false,
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    });
                    vm.$emit('refreshFromResponse', data);
                })
                .catch((error) => {
                    vm.errorString = error;
                });
        },
    },
};
</script>
