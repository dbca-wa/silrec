<template>
    <div :id="'approvalSurrender' + approval_id">
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
                        id="approvalSurrenderForm"
                        class="form-horizontal required-validation"
                        name="approvalSurrenderForm"
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
                                    >Surrender Date</label
                                >
                                <div class="col-sm-9">
                                    <div
                                        ref="surrender_date"
                                        class="input-group date"
                                    >
                                        <input
                                            v-model="
                                                approval_surrender.surrender_date
                                            "
                                            type="date"
                                            class="form-control"
                                            name="surrender_date"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please select the surrender date.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-sm-3">
                                    <label class="col-form-label" for="Name"
                                        >Surrender Details</label
                                    >
                                </div>
                                <div class="col-sm-9">
                                    <textarea
                                        v-model="
                                            approval_surrender.surrender_details
                                        "
                                        name="surrender_details"
                                        class="form-control surrender-details"
                                        required
                                    ></textarea>
                                    <div class="invalid-feedback">
                                        Please enter some details about the
                                        surrender.
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
                                        id="approval_surrender_documents"
                                        ref="approval_surrender_documents"
                                        :key="approval_id"
                                        name="approval_surrender_documents"
                                        :is-repeatable="true"
                                        :document-action-url="
                                            approvalSurrenderDocumentsUrl
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
import Swal from 'sweetalert2';

import { helpers, api_endpoints, utils } from '@/utils/hooks.js';

export default {
    name: 'SurrenderApproval',
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
            type: [String, null],
            required: true,
            validator: (p) => {
                // Seems hacky but lets me have a required prop that can be null
                let valid = ['string'].indexOf(typeof p) !== -1;
                if (p === null) {
                    console.warn(
                        `Received approval_lodgement_number is null, this is probably an error.`
                    );
                    valid = true;
                }
                return valid;
            },
        },
    },
    data: function () {
        return {
            isModalOpen: false,
            approval_surrender: {
                surrender_date: new Date().toISOString().slice(0, 10),
            },
            errorString: '',
        };
    },
    computed: {
        title: function () {
            return 'Surrender Approval ' + this.approval_lodgement_number;
        },
        approvalSurrenderDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.approvals,
                this.approval_id + '/process_approval_surrender_document'
            );
        },
    },
    methods: {
        close: function () {
            var form = document.getElementById('approvalSurrenderForm');
            form.classList.remove('was-validated');
            this.resetForm();
        },
        resetForm: function () {
            this.isModalOpen = false;
            this.approval_surrender = {
                surrender_date: new Date().toISOString().slice(0, 10),
            };
            this.errorString = '';
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById('approvalSurrenderForm');

            if (form.checkValidity()) {
                vm.sendData();
            } else {
                form.classList.add('was-validated');
                $('#approvalSurrenderForm').find(':invalid').first().focus();
            }

            return false;
        },
        sendData: function () {
            let vm = this;
            let approval_surrender = Object.assign({}, vm.approval_surrender);
            approval_surrender.surrender_date = helpers.formatDateForAPI(
                vm.approval_surrender.surrender_date
            );
            let url = helpers.add_endpoint_json(
                api_endpoints.approvals,
                vm.approval_id + '/approval_surrender'
            );
            const requestOptions = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(approval_surrender),
            };

            utils
                .fetchUrl(url, requestOptions)
                .then((data) => {
                    vm.close();
                    Swal.fire(
                        'Surrender',
                        'An email has been sent to the lease/licence holder about surrender of this approval',
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
