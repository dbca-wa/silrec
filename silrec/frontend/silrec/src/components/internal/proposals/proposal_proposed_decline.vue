<template lang="html">
    <div id="change-contact">
        <modal
            transition="modal fade"
            :title="title"
            large
            @ok="ok()"
            @cancel="cancel()"
        >
            <div class="container-fluid">
                <form class="form-horizontal" name="declineForm">
                    <VueAlert v-if="showError" type="danger"
                        ><strong>{{ errorString }}</strong></VueAlert
                    >
                    <div class="form-group">
                        <div class="row mb-3 align-items-center">
                            <label class="col-sm-3 col-form-label">
                                Proposed Decision
                            </label>
                            <div class="col-sm-9">
                                <span class="badge bg-danger p-2 fs-6">
                                    Decline</span
                                >
                            </div>
                        </div>
                        <div class="row mb-3">
                            <div class="col-sm-3">
                                <label class="control-label" for="Name"
                                    >Details</label
                                >
                            </div>
                            <div class="col-sm-9">
                                <RichText
                                    :id="
                                        proposal.application_type.name ==
                                        'lease_licence'
                                            ? 'lease-licence-details-decline'
                                            : 'registration-of-interest-details-decline'
                                    "
                                    ref="decline_reason"
                                    :key="uuid"
                                    :proposal-data="proposedDecisionDetails"
                                    placeholder-text="Add some details here"
                                    @text-changed="decline.reason = $event"
                                />
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <div
                            class="row question-row"
                            style="margin-bottom: 10px"
                        >
                            <div class="col-sm-3">
                                <label for="proposed_decline_documents"
                                    >File</label
                                >
                            </div>
                            <div class="col-sm-9">
                                <FileField
                                    id="proposed_decline_documents"
                                    ref="proposed_decline_documents"
                                    name="proposed_decline_documents"
                                    :is-repeatable="true"
                                    :document-action-url="
                                        proposedDeclineDocumentsUrl
                                    "
                                    :replace_button_by_text="true"
                                />
                            </div>
                        </div>
                    </div>
                    <div class="form-group">
                        <div class="row mb-3">
                            <div class="col-sm-3">
                                <label class="control-label" for="Name"
                                    >CC email</label
                                >
                            </div>
                            <div class="col-sm-9">
                                <input
                                    v-model="decline.cc_email"
                                    type="text"
                                    style="width: 70%"
                                    class="form-control"
                                    name="cc_email"
                                />
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import VueAlert from '@vue-utils/alert.vue';
import RichText from '@/components/forms/RichText.vue';
import FileField from '@/components/forms/filefield_immediate.vue';
import { helpers, api_endpoints, utils } from '@/utils/hooks.js';
import { v4 as uuid } from 'uuid';
export default {
    name: 'DeclineProposal',
    components: {
        modal,
        VueAlert,
        RichText,
        FileField,
    },
    props: {
        proposal: {
            type: Object,
            default: null,
        },
        processing_status: {
            type: String,
            required: true,
        },
    },
    data: function () {
        return {
            isModalOpen: false,
            form: null,
            decline: {},
            decliningProposal: false,
            errors: false,
            validation_form: null,
            errorString: '',
            successString: '',
            success: false,
            uuid: uuid(),
            detailsTexts: {},
        };
    },
    watch: {
        isModalOpen: function (newVal) {
            if (newVal) {
                this.$nextTick(() => {
                    this.$refs.decline_reason.focus();
                });
            }
        },
    },
    computed: {
        proposedDeclineDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_proposed_decline_document/'
            );
        },
        proposalId: function () {
            if (this.proposal) {
                return this.proposal.id;
            }
            return null;
        },
        showError: function () {
            var vm = this;
            return vm.errors;
        },
        title: function () {
            return this.processing_status == 'With Approver'
                ? 'Decline'
                : 'Propose to Decline';
        },
        callFinalDecline: function () {
            let callFinalDecline = false;
            if (
                this.proposal &&
                this.proposal.processing_status_id === 'with_approver'
            ) {
                callFinalDecline = true;
            }
            return callFinalDecline;
        },
        registrationOfInterest: function () {
            if (
                this.proposal &&
                this.proposal.application_type.name ===
                    'registration_of_interest'
            ) {
                return true;
            }
            return false;
        },
        leaseLicence: function () {
            if (
                this.proposal &&
                this.proposal.application_type.name === 'lease_licence'
            ) {
                return true;
            }
            return false;
        },
        proposedDecisionDetails: function () {
            /** Returns the decline message.
             */

            // This is here to re-evalute the computed property after fetching details texts
            this.uuid;

            if (this.decline.reason) {
                return this.decline.reason;
            } else {
                // Use standard text from admin
                let id = Object.prototype.hasOwnProperty.call(
                    this.$refs,
                    'decline_reason'
                )
                    ? this.$refs.decline_reason.id
                    : '';
                return this.detailsTexts[id] || '';
            }
        },
    },
    created: function () {
        let vm = this;
        vm.form = document.forms.declineForm;
        this.decline = Object.assign({}, this.proposal.proposaldeclineddetails);

        let initialisers = [
            utils.fetchUrl(`${api_endpoints.details_text}key-value-list/`),
        ];
        Promise.all(initialisers).then((data) => {
            for (let detailText of data[0]) {
                vm.detailsTexts[detailText.target] = detailText.body;
            }
        });
    },
    mounted: function () {
        this.$nextTick(() => {
            this.$refs.decline_reason.focus();
        });
    },
    methods: {
        ok: function () {
            let vm = this;
            vm.sendData();
        },
        cancel: function () {
            this.close();
        },
        close: function () {
            this.isModalOpen = false;
            this.decline = {};
            this.errors = false;
        },
        check_status: function () {
            let vm = this;
            if (vm.processing_status == 'With Approver') return true;
            else return false;
        },
        sendData: function () {
            this.errors = false;
            let decline = JSON.parse(JSON.stringify(this.decline));
            this.decliningProposal = true;
            this.$nextTick(async () => {
                if (this.callFinalDecline) {
                    const response = await fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposal,
                            this.proposal.id + '/final_decline'
                        ),
                        {
                            body: JSON.stringify(decline),
                            method: 'POST',
                        }
                    );

                    if (response.ok) {
                        this.decliningProposal = false;
                        this.close();
                        this.$router.push({ path: '/internal' }); //Navigate to dashboard page after Propose issue.
                    } else {
                        this.errors = true;
                        this.decliningProposal = false;
                        this.errorString =
                            await helpers.parseFetchError(response);
                    }
                } else {
                    const response = await fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposal,
                            this.proposal.id + '/proposed_decline'
                        ),
                        {
                            body: JSON.stringify(decline),
                            method: 'POST',
                        }
                    );
                    if (response.ok) {
                        this.decliningProposal = false;
                        this.close();
                        this.$router.push({ path: '/internal' }); //Navigate to dashboard after propose decline.
                    } else {
                        this.errors = true;
                        this.decliningProposal = false;
                        this.errorString =
                            await helpers.parseFetchError(response);
                    }
                }
            });
        },
    },
};
</script>
