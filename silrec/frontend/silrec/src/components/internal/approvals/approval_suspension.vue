<template lang="html">
    <div :id="'approvalSuspension' + approval_id">
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
                        id="approvalSuspensionForm"
                        class="form-horizontal required-validation"
                        name="approvalSuspensionForm"
                        novalidate
                    >
                        <alert v-if="errorString" type="danger"
                            ><strong>{{ errorString }}</strong></alert
                        >
                        <div class="col-sm-12">
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-3"
                                    for="Name"
                                    >From Date</label
                                >
                                <div class="col-sm-9">
                                    <div
                                        ref="from_date"
                                        class="input-group date"
                                    >
                                        <input
                                            v-model="
                                                approval_suspension.from_date
                                            "
                                            type="date"
                                            class="form-control"
                                            name="from_date"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please select the date the
                                            suspension starts.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-3"
                                    for="Name"
                                    >To Date</label
                                >
                                <div class="col-sm-9">
                                    <div ref="to_date" class="input-group date">
                                        <input
                                            id="to_date"
                                            v-model="
                                                approval_suspension.to_date
                                            "
                                            type="date"
                                            class="form-control"
                                            name="to_date"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please select the date the
                                            suspension ends.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-3"
                                    for="Name"
                                    >Suspension Details</label
                                >
                                <div class="col-sm-9">
                                    <textarea
                                        v-model="
                                            approval_suspension.suspension_details
                                        "
                                        name="suspension_details"
                                        class="form-control"
                                        required
                                    ></textarea>
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
                                        id="approval_suspension_documents"
                                        ref="approval_suspension_documents"
                                        :key="approval_id"
                                        name="approval_suspension_documents"
                                        :is-repeatable="true"
                                        :document-action-url="
                                            approvalSuspensionDocumentsUrl
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
import alert from '@vue-utils/alert.vue';
import FileField from '@/components/forms/filefield_immediate.vue';

import Swal from 'sweetalert2';

import { helpers, api_endpoints, utils } from '@/utils/hooks.js';
export default {
    name: 'SuspendApproval',
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
            approval_suspension: {
                from_date: new Date().toISOString().slice(0, 10),
            },
            state: 'proposed_approval',
            issuingApproval: false,
            validation_form: null,
            errorString: '',
        };
    },
    computed: {
        showError: function () {
            var vm = this;
            return vm.errors;
        },
        title: function () {
            return 'Suspend Approval';
        },
        approvalSuspensionDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.approvals,
                this.approval_id + '/process_approval_suspension_document'
            );
        },
    },
    methods: {
        close: function () {
            var form = document.getElementById('approvalSuspensionForm');
            form.classList.remove('was-validated');
            this.resetForm();
        },
        resetForm: function () {
            this.isModalOpen = false;
            this.approval_suspension = {
                from_date: new Date().toISOString().slice(0, 10),
            };
            this.errors = false;
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById('approvalSuspensionForm');

            if (form.checkValidity()) {
                vm.sendData();
            } else {
                form.classList.add('was-validated');
                $('#approvalSuspensionForm').find(':invalid').first().focus();
            }

            return false;
        },
        sendData: function () {
            let vm = this;
            let approval_suspension = Object.assign({}, vm.approval_suspension);
            approval_suspension.from_date = helpers.formatDateForAPI(
                vm.approval_suspension.from_date
            );
            approval_suspension.to_date = helpers.formatDateForAPI(
                vm.approval_suspension.to_date
            );
            const requestOptions = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(approval_suspension),
            };
            let url = helpers.add_endpoint_json(
                api_endpoints.approvals,
                vm.approval_id + '/approval_suspension'
            );

            utils
                .fetchUrl(url, requestOptions)
                .then((data) => {
                    vm.close();
                    Swal.fire(
                        'Suspend',
                        'An email has been sent to the lease/licence holder about suspension of this approval',
                        'success'
                    );
                    vm.$emit('refreshFromResponse', data);
                })
                .catch((error) => {
                    vm.errorString = error;
                });
        },
    },
};
</script>
