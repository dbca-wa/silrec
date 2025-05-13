<template lang="html">
    <div id="internal-proposal-amend">
        <modal
            transition="modal fade"
            title="Amendment Request"
            large
            @ok="ok()"
            @cancel="cancel()"
        >
            <div class="container-fluid">
                <div class="row">
                    <form class="form-horizontal" name="amendForm">
                        <alert v-model:show="showError" type="danger"
                            ><strong>{{ errorString }}</strong></alert
                        >
                        <div class="col-sm-12">
                            <div class="row mb-3">
                                <label
                                    class="col-form-label col-sm-3"
                                    for="reason_select"
                                    >Reason</label
                                >
                                <div class="col-sm-9">
                                    <select
                                        id="reason_select"
                                        ref="reason_choices"
                                        v-model="amendment.reason_id"
                                        class="form-select"
                                        @change="onReasonChange"
                                    >
                                        <option
                                            v-for="r in reason_choices"
                                            :key="r.key"
                                            :value="r.key"
                                        >
                                            {{ r.value }}
                                        </option>
                                    </select>
                                </div>
                            </div>
                            <div class="row">
                                <label
                                    class="col-form-label col-sm-3"
                                    for="amendment_text"
                                    >Details</label
                                >
                                <div class="col-sm-9">
                                    <textarea
                                        id="amendment_text"
                                        ref="amendment_text"
                                        v-model="amendment.text"
                                        class="form-control"
                                        rows="10"
                                    ></textarea>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-offset-2 col-sm-8">
                                    <div
                                        ref="add_attachments"
                                        class="input-group date"
                                        style="width: 70%"
                                    >
                                        <FileField
                                            v-if="false"
                                            ref="filefield"
                                            :uploaded_documents="
                                                amendment.amendment_request_documents
                                            "
                                            :delete_url="delete_url"
                                            :proposal_id="proposal.id"
                                            :is-repeatable="true"
                                            name="amendment_request_file"
                                        />
                                    </div>
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
import { helpers } from '@/utils/hooks.js';

export default {
    name: 'AmendmentRequest',
    components: {
        modal,
        alert,
        FileField,
    },
    props: {
        proposal: {
            type: Object,
            default: null,
        },
    },
    data: function () {
        return {
            isModalOpen: false,
            form: null,
            amendment: {
                reason: '',
                reason_id: null,
                amendingProposal: false,
                proposal_id: this.proposal.id,
                num_files: 0,
                input_name: 'amendment_request_doc',
                requirement_documents: [],
                text: 'test',
            },
            reason_choices: {},
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
        delete_url: function () {
            return this.amendment.id
                ? '/api/amendment_request/' +
                      this.amendment.id +
                      '/delete_document/'
                : '';
        },
        disableOkButton: function () {
            // Disable amendment modal ok-button for as long as no amendment
            // reason has been selected
            return this.amendment.reason_id == null;
        },
    },
    watch: {
        isModalOpen: function (val) {
            if (val) {
                if (this.proposal.additional_documents_missing.length > 0) {
                    this.amendment.text =
                        'The following additional documents are required:';
                    for (
                        let i = 0;
                        i < this.proposal.additional_documents_missing.length;
                        i++
                    ) {
                        this.amendment.text +=
                            '\n\t- ' +
                            this.proposal.additional_documents_missing[i].name;
                    }
                }
                this.$nextTick(() => {
                    this.$refs.amendment_text.focus();
                });
            }
        },
    },
    created: function () {
        this.fetchAmendmentChoices();
    },
    mounted: function () {
        this.form = document.forms.amendForm;
    },
    methods: {
        ok: function () {
            let vm = this;
            if ($(vm.form).valid()) {
                vm.sendData();
            }
        },
        cancel: function () {
            let vm = this;
            vm.close();
        },
        close: function () {
            this.isModalOpen = false;
            this.amendment = {
                reason: '',
                reason_id: this.reason_choices[0].key,
                proposal_id: this.proposal.id,
            };
        },
        onReasonChange: function (e) {
            // Update this proposal's amendment reason on selecting a different reason from the modal
            let vm = this;
            let reason = e.target.innerText;
            let reason_id = e.target.value;
            vm.amendment.reason = reason;
            vm.amendment.reason_id = reason_id;
        },
        fetchAmendmentChoices: async function () {
            try {
                const res = await fetch(
                    '/api/amendment_request_reason_choices.json'
                );
                const resData = await res.json();
                this.reason_choices = Object.assign({}, resData);
                this.amendment.reason_id = this.reason_choices[0].key;
            } catch (error) {
                console.error(error);
            }
        },
        sendData: function () {
            this.errors = false;
            fetch('/api/amendment_request.json', {
                body: JSON.stringify(this.amendment),
                method: 'POST',
            })
                .then(async (response) => {
                    if (!response.ok) {
                        this.errorString = await response.text();
                        this.errors = true;
                        this.amendingProposal = true;
                        return;
                    }
                    await new swal(
                        'Sent',
                        'An email has been sent to the applicant with the request to amend this application',
                        'success'
                    );
                    this.amendingProposal = true;
                    this.close();
                    this.$router.push({ path: '/internal' }); //Navigate to dashboard after creating Amendment request
                })
                .catch((error) => {
                    console.error(error);
                    this.errors = true;
                    this.errorString = helpers.apiVueResourceError(error);
                })
                .finally(() => {
                    this.amendingProposal = true;
                });
        },
    },
};
</script>
