<template>
    <div id="externalCompliance" class="container">
        <div v-if="compliance">
            <BootstrapAlert
                v-if="isDiscarded"
                type="danger"
                icon="exclamation-triangle-fill"
            >
                <h3>
                    You cannot access this Compliance as it has been discarded.
                </h3>
            </BootstrapAlert>
            <div v-else class="">
                <FormSection
                    v-if="!isFinalised && hasAmendmentRequest"
                    custom-color="red"
                    label="This Compliance Requires One or More Amendments"
                    index="amendment_compliance_with_requirements"
                >
                    <div class="row mb-3">
                        <div class="col">
                            <ol class="list-group">
                                <li
                                    v-for="a in amendment_request"
                                    :key="a.id"
                                    class="list-group-item d-flex justify-content-between align-items-start"
                                >
                                    <div class="ms-2 me-auto">
                                        <div class="mt-3">
                                            <BootstrapAlert
                                                class="alert-sm d-inline-flex"
                                                type="danger"
                                                icon="exclamation-triangle-fill"
                                            >
                                                {{ a.reason }}
                                            </BootstrapAlert>
                                        </div>
                                        <div class="amendment-text py-3">
                                            <pre>{{ a.text }}</pre>
                                        </div>
                                    </div>
                                </li>
                            </ol>
                        </div>
                    </div>
                </FormSection>
                <div class="col-md-12">
                    <FormSection
                        :label="title"
                        index="compliance_with_requirements"
                    >
                        <form
                            id="complianceForm"
                            class="needs-validation"
                            name="complianceForm"
                            novalidate
                        >
                            <alert v-model:show="showError" type="danger">
                                <strong>{{ errorString }}</strong>
                            </alert>
                            <div
                                v-if="
                                    constants.COMPLIANCE_CUSTOMER_STATUS
                                        .WITH_ASSESSOR.ID ==
                                    compliance.customer_status
                                "
                                class="row mb-3"
                            >
                                <label class="col-form-label col-sm-2" for=""
                                    >Status:</label
                                >
                                <div class="col-sm-6">
                                    <span class="badge bg-secondary py-2 mt-1"
                                        ><i class="fa fa-clock"></i>
                                        {{
                                            compliance.customer_status_display
                                        }}</span
                                    >
                                </div>
                            </div>
                            <div
                                v-if="
                                    constants.COMPLIANCE_CUSTOMER_STATUS
                                        .APPROVED.ID ==
                                    compliance.customer_status
                                "
                                class="row mb-3"
                            >
                                <label class="col-form-label col-sm-2" for=""
                                    >Status:</label
                                >
                                <div class="col-sm-6">
                                    <span class="badge bg-success py-2 mt-1"
                                        ><i class="fa fa-check"></i>
                                        {{
                                            compliance.customer_status_display
                                        }}</span
                                    >
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-2"
                                    for="due_date"
                                    >Due Date:</label
                                >
                                <div class="col-sm-6">
                                    <input
                                        id="due_date"
                                        type="text"
                                        readonly
                                        class="form-control-plaintext"
                                        name="due_date"
                                        :value="compliance.due_date"
                                    />
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-2"
                                    for="requirement"
                                    >Requirement:</label
                                >
                                <div class="col-sm-6">
                                    <input
                                        id="requirement"
                                        type="text"
                                        readonly
                                        class="form-control-plaintext"
                                        name="requirement"
                                        :value="compliance.requirement"
                                        required
                                    />
                                </div>
                            </div>
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-2"
                                    for="detail"
                                    >Details:</label
                                >
                                <div class="col-sm-9">
                                    <textarea
                                        id="detail"
                                        v-model="compliance.text"
                                        :disabled="isFinalised"
                                        class="form-control"
                                        name="detail"
                                        rows="8"
                                        autofocus
                                        required
                                    ></textarea>
                                    <div class="invalid-feedback">
                                        Please provide some details regarding
                                        the fulfillment of the above
                                        requirement.
                                    </div>
                                </div>
                            </div>
                            <div
                                v-if="compliance.gross_turnover_required"
                                class="row mb-3"
                            >
                                <label
                                    for="gross_turnover"
                                    class="col-sm-2 col-form-label"
                                    >Gross Turnover</label
                                >
                                <div class="col-sm-4">
                                    <div class="input-group">
                                        <span class="input-group-text">$</span>
                                        <input
                                            id="details"
                                            v-model="compliance.gross_turnover"
                                            type="number"
                                            class="form-control"
                                            name="gross_turnover"
                                            :disabled="isFinalised"
                                            required
                                        />
                                        <div class="invalid-feedback">
                                            Please provide the gross turnover
                                            for the period.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div v-if="hasDocuments" class="row mb-3">
                                <label class="col-form-label col-sm-2"
                                    >Documents:</label
                                >
                                <div class="col-sm-9">
                                    <template
                                        v-if="
                                            compliance.documents &&
                                            compliance.documents.length
                                        "
                                    >
                                        <ul class="list-group">
                                            <li
                                                v-for="d in compliance.documents"
                                                :key="d.id"
                                                class="list-group-item rounded"
                                            >
                                                <a
                                                    :href="d.secure_url"
                                                    target="_blank"
                                                    class="me-1"
                                                    >{{ d.name }}</a
                                                >
                                                <span
                                                    v-if="
                                                        !isFinalised &&
                                                        d.can_delete
                                                    "
                                                >
                                                    <a
                                                        class="fa fa-trash-o control-label"
                                                        title="Remove file"
                                                        style="
                                                            cursor: pointer;
                                                            color: red;
                                                        "
                                                        @click="
                                                            delete_document(d)
                                                        "
                                                    ></a>
                                                </span>
                                                <span v-else>
                                                    <i
                                                        class="fa fa-info-circle"
                                                        aria-hidden="true"
                                                        title="Previously submitted documents cannot be deleted"
                                                        style="cursor: pointer"
                                                    ></i>
                                                </span>
                                            </li>
                                        </ul>
                                    </template>
                                </div>
                            </div>
                            <div v-if="!isFinalised" class="row mb-3">
                                <label class="col-form-label col-sm-2"
                                    >Attachments:</label
                                >
                                <div class="col-sm-9">
                                    <template v-if="files && files.length">
                                        <ul class="list-group">
                                            <li
                                                v-for="(f, i) in files"
                                                :key="f"
                                                class="list-group-item rounded"
                                            >
                                                <div class="row">
                                                    <div class="col">
                                                        <span
                                                            v-if="
                                                                f.file == null
                                                            "
                                                            class="btn btn-primary btn-sm btn-file float-start"
                                                            ><i
                                                                class="fa fa-upload"
                                                                aria-hidden="true"
                                                            ></i>
                                                            Attach File
                                                            <input
                                                                type="file"
                                                                :name="
                                                                    'file-upload-' +
                                                                    i
                                                                "
                                                                :class="
                                                                    'file-upload-' +
                                                                    i
                                                                "
                                                                @change="
                                                                    uploadFile(
                                                                        'file-upload-' +
                                                                            i,
                                                                        f
                                                                    )
                                                                "
                                                            />
                                                        </span>
                                                        <span
                                                            v-else
                                                            class="btn btn-secondary btn-sm btn-file float-start"
                                                            ><i
                                                                class="fa fa-edit"
                                                            ></i>
                                                            Update File
                                                            <input
                                                                type="file"
                                                                :name="
                                                                    'file-upload-' +
                                                                    i
                                                                "
                                                                :class="
                                                                    'file-upload-' +
                                                                    i
                                                                "
                                                                @change="
                                                                    uploadFile(
                                                                        'file-upload-' +
                                                                            i,
                                                                        f
                                                                    )
                                                                "
                                                            />
                                                        </span>
                                                    </div>
                                                    <div class="col-sm-7">
                                                        <span>{{
                                                            f.name
                                                        }}</span>
                                                    </div>
                                                    <div class="col-sm-1">
                                                        <button
                                                            v-if="
                                                                f.file || i > 0
                                                            "
                                                            class="btn btn-danger btn-sm"
                                                            @click.prevent="
                                                                removeFile(i)
                                                            "
                                                        >
                                                            <i
                                                                class="fa fa-trash"
                                                                aria-hidden="true"
                                                            ></i>
                                                        </button>
                                                    </div>
                                                </div>
                                            </li>
                                        </ul>
                                    </template>
                                    <div class="border-top mt-3 p-2">
                                        <button
                                            class="btn btn-sm btn-primary"
                                            @click.prevent="attachAnother"
                                        >
                                            <i class="fa fa-add"></i> Add
                                            Another File
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </FormSection>
                </div>
            </div>
            <div class="navbar fixed-bottom bg-navbar border-top">
                <div class="container">
                    <div class="col-md-12 text-end">
                        <button
                            v-if="!isFinalised"
                            class="btn btn-primary me-2"
                            @click.prevent="
                                validateForm(
                                    (method = 'PATCH'),
                                    (custom_action = 'save'),
                                    (exit_after = true)
                                )
                            "
                        >
                            Save and Exit
                        </button>
                        <button
                            v-if="!isFinalised"
                            class="btn btn-primary me-2"
                            @click.prevent="
                                validateForm(
                                    (method = 'PATCH'),
                                    (custom_action = 'save'),
                                    (exit_after = false)
                                )
                            "
                        >
                            Save and Continue
                        </button>
                        <button
                            v-if="!isFinalised"
                            class="btn btn-primary"
                            @click.prevent="validateForm()"
                        >
                            Submit
                        </button>
                    </div>
                </div>
            </div>
        </div>
        <BootstrapSpinner v-else :is-loading="true" class="text-primary" />
    </div>
</template>
<script>
import FormSection from '@/components/forms/section_toggle.vue';
import { v4 as uuid } from 'uuid';
import { api_endpoints, constants, helpers } from '@/utils/hooks';
import alert from '@vue-utils/alert.vue';

export default {
    name: 'ExternalComplianceAccess',
    components: {
        FormSection,
        alert,
    },
    beforeRouteEnter: function (to, from, next) {
        next(async (vm) => {
            if (to.params.compliance_id) {
                vm.fetchCompliance(to.params.compliance_id);
            }
        });
    },
    data() {
        return {
            title: '',
            form: null,
            loading: [],
            compliance: null,
            original_compliance: {},
            amendment_request: [],
            hasAmendmentRequest: false,
            errors: false,
            errorString: '',
            pdBody: 'pdBody' + uuid(),
            oBody: 'oBody' + uuid(),
            validation_form: null,
            files: [
                {
                    file: null,
                    name: '',
                },
            ],
            constants: constants,
        };
    },
    computed: {
        showError: function () {
            var vm = this;
            return vm.errors;
        },
        isLoading: function () {
            return this.loading.length > 0;
        },
        isDiscarded: function () {
            return (
                this.compliance &&
                this.compliance.customer_status ==
                    constants.COMPLIANCE_PROCESSING_STATUS.DISCARDED.ID
            );
        },
        hasAttachments: function () {
            if (this.files.length == 0) {
                return false;
            }
            for (let i = 0; i < this.files.length; i++) {
                if (this.files[i].file && this.files[i].name) {
                    return true;
                }
            }
            return false;
        },
        hasDocuments: function () {
            return (
                this.compliance.documents &&
                this.compliance.documents.length > 0
            );
        },
        isFinalised: function () {
            return (
                this.compliance &&
                (this.compliance.customer_status ==
                    constants.COMPLIANCE_PROCESSING_STATUS.WITH_ASSESSOR.ID ||
                    this.compliance.customer_status ==
                        constants.COMPLIANCE_PROCESSING_STATUS.APPROVED.ID)
            );
        },
    },
    created: function () {
        this.fetchCompliance(this.$route.params.compliance_id);
    },
    mounted: function () {
        this.form = document.forms.complianceForm;
    },
    methods: {
        uploadFile(target, file_obj) {
            let _file = null;
            var input = $('.' + target)[0];
            if (input.files && input.files[0]) {
                let reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function (e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            file_obj.file = _file;
            file_obj.name = _file.name;
        },
        removeFile(index) {
            let length = this.files.length;
            $('.file-row-' + index).remove();
            this.files.splice(index, 1);
            this.$nextTick(() => {
                length == 1 ? this.attachAnother() : '';
            });
        },
        attachAnother() {
            this.files.push({
                file: null,
                name: '',
            });
        },
        close: function () {
            this.$router.push({ name: 'external-dashboard' });
        },
        setAmendmentData: function (amendment_request) {
            this.amendment_request = amendment_request;

            if (amendment_request.length > 0) this.hasAmendmentRequest = true;
        },
        delete_document: function (doc) {
            let vm = this;
            let data = { document: doc };
            if (doc) {
                fetch(
                    helpers.add_endpoint_json(
                        api_endpoints.compliances,
                        vm.compliance.id + '/delete_document'
                    ),
                    {
                        method: 'POST',
                        body: JSON.stringify(data),
                    }
                ).then(
                    async (response) => {
                        vm.refreshFromResponse(response);
                        vm.compliance = await Object.assign(
                            {},
                            response.json()
                        );
                    },
                    (error) => {
                        vm.errors = true;
                        vm.errorString = error.message;
                    }
                );
            }
        },
        validateForm: function (
            method = 'POST',
            custom_action = 'submit',
            exit_after = false
        ) {
            let vm = this;
            var form = document.getElementById('complianceForm');

            if (
                vm.compliance.gross_turnover_required &&
                !vm.hasDocuments &&
                !vm.hasAttachments
            ) {
                swal.fire({
                    title: 'Audited Financial Statement Required',
                    text: 'Please attach an audited finanacial statement for the period',
                    icon: 'error',
                });
                return false;
            }

            if (form.checkValidity()) {
                vm.sendData(method, custom_action, exit_after);
            } else {
                form.classList.add('was-validated');
                $('#complianceForm').find(':invalid').first().focus();
            }

            return false;
        },
        sendData: function (
            method = 'POST',
            custom_action = 'submit',
            exit_after = false
        ) {
            this.$nextTick(() => {
                this.errors = false;
                let formData = new FormData();
                formData.append('detail', this.compliance.text);
                formData.append(
                    'gross_turnover',
                    this.compliance.gross_turnover
                );
                let numFiles = 0;
                for (let i = 0; i < this.files.length; i++) {
                    if (this.files[i].file && this.files[i].name) {
                        formData.append('file' + i, this.files[i].file);
                        formData.append('name' + i, this.files[i].name);
                        numFiles++;
                    }
                }
                formData.append('num_files', numFiles);

                fetch(
                    helpers.add_endpoint_json(
                        api_endpoints.compliances,
                        this.compliance.id + '/' + custom_action
                    ),
                    {
                        method: method,
                        body: formData,
                    }
                )
                    .then(async (response) => {
                        if (!response.ok) {
                            return await response.json().then((json) => {
                                throw new Error(json);
                            });
                        } else {
                            return await response.json();
                        }
                    })
                    .then((data) => {
                        this.addingCompliance = false;
                        this.refreshFromResponse(data);
                        this.compliance = Object.assign({}, data);

                        if ('submit' == custom_action) {
                            this.$router.push({
                                name: 'submit_compliance',
                                params: { compliance_id: this.compliance.id },
                            });
                        } else {
                            swal.fire({
                                title: `Compliance ${this.compliance.lodgement_number} Saved`,
                                text: 'Compliance has been saved successfully',
                                icon: 'success',
                            });
                            if (exit_after) {
                                this.close();
                            } else {
                                this.files = [];
                            }
                        }
                    })
                    .catch((error) => {
                        this.errors = true;
                        this.addingCompliance = false;
                        this.errorString = error.message;
                        swal.fire({
                            title: 'Compliance Error',
                            text: error.message,
                            icon: 'error',
                        });
                    });
            });
        },
        fetchCompliance: async function (compliance_id) {
            let vm = this;
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.compliances,
                    compliance_id
                )
            ).then(
                async (response) => {
                    const resData = await response.json();
                    vm.compliance = Object.assign({}, resData);
                    if (
                        vm.compliance.customer_status ==
                            constants.COMPLIANCE_CUSTOMER_STATUS.WITH_ASSESSOR
                                .ID ||
                        vm.compliance.customer_status ==
                            constants.COMPLIANCE_CUSTOMER_STATUS.APPROVED.ID
                    ) {
                        vm.isFinalised = true;
                    }
                    vm.status = vm.compliance.customer_status;

                    if (
                        vm.compliance.customer_status ==
                        constants.COMPLIANCE_CUSTOMER_STATUS.WITH_ASSESSOR.ID
                    ) {
                        vm.title =
                            'View Compliance - ' +
                            this.compliance.lodgement_number;
                    } else if (
                        vm.compliance.customer_status ==
                        constants.COMPLIANCE_CUSTOMER_STATUS.APPROVED.ID
                    ) {
                        vm.title =
                            'View Compliance - ' +
                            this.compliance.lodgement_number;
                    } else {
                        vm.title =
                            'Submit Compliance - ' +
                            this.compliance.lodgement_number;
                    }

                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.compliances,
                            compliance_id + '/amendment_request'
                        )
                    ).then(
                        async (res) => {
                            vm.setAmendmentData(await res.json());
                        },
                        (err) => {
                            console.error(err);
                        }
                    );
                },
                (error) => {
                    console.error(error);
                }
            );
        },
        refreshFromResponse: async function (resData) {
            this.original_compliance = helpers.copyObject(resData);
            this.compliance = helpers.copyObject(resData);
            if (
                this.compliance.customer_status ==
                    constants.COMPLIANCE_CUSTOMER_STATUS.WITH_ASSESSOR.ID ||
                this.compliance.customer_status ==
                    constants.COMPLIANCE_CUSTOMER_STATUS.APPROVED.ID
            ) {
                this.isFinalised = true;
            }
        },
    },
};
</script>

<style scoped>
.btn-file {
    position: relative;
    overflow: hidden;
}

.btn-file input[type='file'] {
    position: absolute;
    top: 0;
    right: 0;
    min-width: 100%;
    min-height: 100%;
    font-size: 100px;
    text-align: right;
    filter: alpha(opacity=0);
    opacity: 0;
    outline: none;
    background: white;
    cursor: inherit;
    display: block;
}

.alert-sm {
    padding: 0.25rem 0.5rem;
    font-size: 0.875rem;
    margin-bottom: 0;
    border-radius: 0.2rem;
}

.amendment-text {
    white-space: pre-wrap;
}
</style>
