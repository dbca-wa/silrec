<template lang="html">
    <div class="container">
        <div v-if="proposal && !proposal.readonly">
            <div v-if="amendment_request && amendment_request.length > 0">
                <FormSection
                    custom-color="red"
                    label="This Proposal Requires One or More Amendments"
                    index="amendments_requested"
                >
                    <div class="row">
                        <div class="col-12">
                            <ol class="list-group">
                                <li
                                    v-for="a in amendment_request"
                                    :key="a.id"
                                    class="list-group-item d-flex"
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
            </div>
        </div>

        <div v-if="errors">
            <BootstrapAlert
                v-if="errors"
                id="errors"
                ref="errors"
                class="d-flex align-items-center"
                type="danger"
                icon="exclamation-triangle-fill"
            >
                <ErrorRenderer :errors="errors" />
            </BootstrapAlert>
        </div>

        <ApplicationForm
            v-if="proposal"
            ref="application_form"
            :proposal="proposal"
            :is_external="true"
            :readonly="readonly"
            :submitter-id="submitterId"
            :registration-of-interest="registrationOfInterest"
            :lease-licence="leaseLicence"
            :navbar-buttons-disabled="navbarButtonsDisabled"
            :saving-in-progress="savingProposal"
            @update-submit-text="updateSubmitText"
            @refresh-from-response="refreshFromResponse"
            @finished-drawing="onFinishedDrawing"
            @deleted-features="onFinishedDrawing"
        >
            <template #slot_additional_documents_assessment_comments>
                <div class="row">
                    <div
                        v-for="additional_document_type in proposal.additional_document_types"
                        :key="additional_document_type.id"
                        class="col-sm-6"
                    >
                        <div class="card mb-3">
                            <div class="card-body">
                                <h4 class="card-title">
                                    {{ additional_document_type.name }}
                                </h4>
                                <p class="card-text">
                                    <label
                                        :for="additional_document_type.name"
                                        class="form-label"
                                        >Document:
                                    </label>
                                    <FileField
                                        :id="additional_document_type.id"
                                        :ref="additional_document_type.id"
                                        :name="additional_document_type.name"
                                        :is-repeatable="false"
                                        :document-action-url="
                                            additionalDocumentUrl
                                        "
                                        :replace_button_by_text="true"
                                    />
                                    <small
                                        v-if="
                                            additional_document_type.help_text
                                        "
                                        id="helpId"
                                        class="form-text text-muted"
                                        >{{
                                            additional_document_type.help_text
                                        }}</small
                                    >
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </template>
        </ApplicationForm>
        <div v-else>
            <BootstrapSpinner
                :is-loading="true"
                class="text-primary opacity-50"
            />
        </div>

        <div>
            <input
                type="hidden"
                name="csrfmiddlewaretoken"
                :value="csrf_token"
            />
            <input
                type="hidden"
                name="schema"
                :value="JSON.stringify(proposal)"
            />
            <input type="hidden" name="proposal_id" :value="1" />

            <div class="navbar fixed-bottom bg-navbar me-1">
                <div v-if="proposal && !proposal.readonly" class="container">
                    <div class="col-md-12 text-end">
                        <BootstrapButtonSpinner
                            v-if="saveExitProposal"
                            class="btn btn-primary me-1"
                            :is-loading="true"
                            :small="true"
                            :center-of-screen="false"
                        />
                        <button
                            v-else
                            class="btn btn-primary me-1"
                            :disabled="navbarButtonsDisabled"
                            @click.prevent="save_exit"
                        >
                            Save and Exit
                        </button>

                        <BootstrapButtonSpinner
                            v-if="savingProposal"
                            class="btn btn-primary me-1"
                            :is-loading="true"
                            :small="true"
                            :center-of-screen="false"
                        />
                        <button
                            v-else
                            class="btn btn-primary me-1"
                            :disabled="navbarButtonsDisabled"
                            @click.prevent="save"
                        >
                            Save and Continue
                        </button>

                        <BootstrapButtonSpinner
                            v-if="submitting || paySubmitting"
                            class="btn btn-primary me-1"
                            :is-loading="true"
                            :small="true"
                            :center-of-screen="false"
                        />

                        <button
                            v-else
                            id="submitButton"
                            class="btn btn-primary me-1"
                            :disabled="navbarButtonsDisabled"
                            :title="disabledSubmitText"
                            @click.prevent="submit"
                        >
                            {{ submitText }}
                        </button>

                        <input
                            id="save_and_continue_btn"
                            type="hidden"
                            class="btn btn-primary"
                            value="Save Without Confirmation"
                            @click.prevent="save_wo_confirm"
                        />
                    </div>
                </div>
                <div v-else class="container">
                    <div class="col-md-12 text-end">
                        <router-link
                            class="btn btn-primary float-end"
                            :to="{ name: 'external-dashboard' }"
                        >
                            Back to Dashboard
                        </router-link>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import ApplicationForm from '../form.vue';
import FileField from '@/components/forms/filefield_immediate.vue';
import FormSection from '@/components/forms/section_toggle.vue';
import ErrorRenderer from '@common-utils/ErrorRenderer.vue';

import { api_endpoints, helpers } from '@/utils/hooks';

export default {
    name: 'ExternalProposal',
    components: {
        ApplicationForm,
        ErrorRenderer,
        FileField,
        FormSection,
    },
    beforeRouteEnter(to, from, next) {
        next((vm) => {
            if (to.params.proposal_id) {
                vm.fetchProposal(to.params.proposal_id);
            }
        });
    },
    data: function () {
        return {
            proposal: null,
            amendment_request: null,
            loading: [],
            loadingProposal: false,
            proposal_readonly: true,
            hasAmendmentRequest: false,
            submitting: false,
            saveExitProposal: false,
            savingProposal: false,
            paySubmitting: false,
            newText: '',
            pBody: 'pBody',
            errors: null,
            missing_fields: [],
            proposal_parks: null,
            terms_and_conditions_checked: false,
            vesselChanged: false,
            // AUA
            mooringOptionsChanged: false,
            // WLA
            mooringPreferenceChanged: false,
            submitText: 'Submit',
        };
    },
    computed: {
        additionalDocumentUrl: function () {
            return (
                api_endpoints.proposal +
                this.proposal.id +
                '/process_additional_document/'
            );
        },
        navbarButtonsDisabled: function () {
            return this.submitting || this.savingProposal || this.paySubmitting;
        },
        registrationOfInterest: function () {
            let retVal = false;
            if (
                this.proposal &&
                this.proposal.application_type.name ===
                    'registration_of_interest'
            ) {
                retVal = true;
            }
            return retVal;
        },
        leaseLicence: function () {
            let retVal = false;
            if (
                this.proposal &&
                this.proposal.application_type.name === 'lease_licence'
            ) {
                retVal = true;
            }
            return retVal;
        },

        disableSubmit: function () {
            let disable = false;
            if (
                this.proposal.proposal_type &&
                this.proposal.proposal_type.code === 'amendment'
            ) {
                if (
                    ['aaa', 'mla'].includes(
                        this.proposal.application_type_code
                    ) &&
                    !this.vesselChanged
                ) {
                    disable = true;
                } else if (
                    this.proposal.application_type_code === 'wla' &&
                    !this.vesselChanged &&
                    !this.mooringPreferenceChanged
                ) {
                    disable = true;
                } else if (
                    this.proposal.application_type_code === 'aua' &&
                    !this.vesselChanged &&
                    !this.mooringOptionsChanged
                ) {
                    disable = true;
                }
            }
            return disable;
        },
        disabledSubmitText: function () {
            let text = '';
            if (this.disableSubmit) {
                text =
                    'No relevant details have been detected in this amendment application';
            }
            return text;
        },
        autoRenew: function () {
            let renew = false;
            if (
                !this.vesselChanged &&
                !this.mooringOptionsChanged &&
                this.proposal.proposal_type.code === 'renewal' &&
                ['mla', 'aua'].includes(this.proposal.application_type_code)
            ) {
                renew = true;
            }
            return renew;
        },
        submitterId: function () {
            let submitter = null;
            if (
                this.proposal &&
                this.proposal.submitter &&
                this.proposal.submitter.id
            ) {
                submitter = this.proposal.submitter.id;
            }
            return submitter;
        },
        readonly: function () {
            let returnVal = true;
            if (this.proposal.processing_status === 'Draft') {
                returnVal = false;
            }
            return returnVal;
        },
        isLoading: function () {
            return this.loading.length > 0;
        },
        csrf_token: function () {
            return helpers.getCookie('csrftoken');
        },
        proposal_form_url: function () {
            return this.proposal
                ? `/api/proposal/${this.proposal.id}/draft.json`
                : '';
        },
        application_fee_url: function () {
            return this.proposal ? `/application_fee/${this.proposal.id}/` : '';
        },
        proposal_submit_url: function () {
            return this.proposal
                ? `/api/proposal/${this.proposal.id}/submit.json`
                : '';
        },
        applicationTypeCode: function () {
            if (this.proposal) {
                return this.proposal.application_type_code;
            }
            return null;
        },
    },
    methods: {
        proposal_refs: function () {
            if (this.applicationTypeCode == 'wla') {
                return this.$refs.waiting_list_application;
            } else if (this.applicationTypeCode == 'aaa') {
                return this.$refs.annual_admission_application;
            } else if (this.applicationTypeCode == 'aua') {
                return this.$refs.authorised_user_application;
            } else if (this.applicationTypeCode == 'mla') {
                return this.$refs.mooring_licence_application;
            }
        },
        updateSubmitText: function (submitText) {
            this.submitText = submitText;
        },
        save_applicant_data: function () {
            if (this.proposal.applicant_type == 'SUB') {
                this.proposal_refs().$refs.profile.updatePersonal();
                this.proposal_refs().$refs.profile.updateAddress();
                this.proposal_refs().$refs.profile.updateContact();
            }
        },

        save: async function (
            withConfirm = true,
            url = this.proposal_form_url,
            increment_map_key = true
        ) {
            let vm = this;
            vm.savingProposal = true;
            let payload = {
                proposal: {},
            };

            if (this.registrationOfInterest) {
                payload.proposal = {
                    exclusive_use: this.proposal.exclusive_use,
                    long_term_use: this.proposal.long_term_use,
                    consistent_purpose: this.proposal.consistent_purpose,
                    consistent_plan: this.proposal.consistent_plan,
                    clearing_vegetation: this.proposal.clearing_vegetation,
                    ground_disturbing_works:
                        this.proposal.ground_disturbing_works,
                    heritage_site: this.proposal.heritage_site,
                    environmentally_sensitive:
                        this.proposal.environmentally_sensitive,
                    wetlands_impact: this.proposal.wetlands_impact,
                    building_required: this.proposal.building_required,
                    significant_change: this.proposal.significant_change,
                    aboriginal_site: this.proposal.aboriginal_site,
                    native_title_consultation:
                        this.proposal.native_title_consultation,
                    mining_tenement: this.proposal.mining_tenement,
                    groups: this.proposal.groups,
                    details_text: this.proposal.details_text,
                    exclusive_use_text: this.proposal.exclusive_use_text,
                    long_term_use_text: this.proposal.long_term_use_text,
                    consistent_purpose_text:
                        this.proposal.consistent_purpose_text,
                    consistent_plan_text: this.proposal.consistent_plan_text,
                    clearing_vegetation_text:
                        this.proposal.clearing_vegetation_text,
                    ground_disturbing_works_text:
                        this.proposal.ground_disturbing_works_text,
                    heritage_site_text: this.proposal.heritage_site_text,
                    environmentally_sensitive_text:
                        this.proposal.environmentally_sensitive_text,
                    wetlands_impact_text: this.proposal.wetlands_impact_text,
                    building_required_text:
                        this.proposal.building_required_text,
                    significant_change_text:
                        this.proposal.significant_change_text,
                    aboriginal_site_text: this.proposal.aboriginal_site_text,
                    native_title_consultation_text:
                        this.proposal.native_title_consultation_text,
                    mining_tenement_text: this.proposal.mining_tenement_text,
                };
            } else if (this.leaseLicence) {
                if (
                    this.proposal.groups.find(
                        (group) => group.name.trim().toLowerCase() == 'tourism'
                    )
                ) {
                    payload.proposal.profit_and_loss_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.profit_and_loss_text.detailsText;
                    payload.proposal.cash_flow_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.cash_flow_text.detailsText;
                    payload.proposal.capital_investment_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.capital_investment_text.detailsText;
                    payload.proposal.financial_capacity_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.financial_capacity_text.detailsText;
                    payload.proposal.available_activities_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.available_activities_text.detailsText;
                    payload.proposal.market_analysis_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.market_analysis_text.detailsText;
                    payload.proposal.staffing_text =
                        this.$refs.application_form.$refs.lease_licence.$refs.staffing_text.detailsText;
                }

                payload.proposal.key_personnel_text =
                    this.proposal.key_personnel_text;
                payload.proposal.key_milestones_text =
                    this.proposal.key_milestones_text;
                payload.proposal.risk_factors_text =
                    this.proposal.risk_factors_text;
                payload.proposal.legislative_requirements_text =
                    this.proposal.legislative_requirements_text;

                payload.proposal.proponent_reference_number =
                    this.proposal.proponent_reference_number;
                payload.proposal.groups = this.proposal.groups;
            }
            payload.proposalgeometry =
                this.$refs.application_form.$refs.component_map.getJSONFeatures();
            let deleted_features =
                this.$refs.application_form.$refs.component_map.deletedFeaturesProperty();
            // Save right away if there are no deleted features, otherwise ask for confirmation
            let commence_saving = deleted_features.length == 0 ? true : false;

            if (withConfirm) {
                let warning_text = `${deleted_features.length} ${
                    deleted_features.length == 1 ? 'feature' : 'features'
                } will be deleted. Are you sure?`;
                if (deleted_features.length > 0) {
                    await swal
                        .fire({
                            title: 'Save Proposal',
                            text: warning_text,
                            icon: 'question',
                            showCancelButton: true,
                            reverseButtons: true,
                            confirmButtonText: 'Continue',
                        })
                        .then(async (result) => {
                            if (result.isConfirmed) {
                                // When Yes
                                commence_saving = true;
                            }
                        });
                }

                if (!commence_saving) {
                    vm.savingProposal = false;
                    return;
                }
            }

            if (vm.submitting) {
                // Provide an action to have the backend lock the geometry
                payload.action = 'submit';
            }

            const res = await fetch(url, {
                body: JSON.stringify(payload),
                method: 'POST',
            });
            if (res.ok) {
                if (withConfirm) {
                    await swal.fire({
                        title: 'Saved',
                        text: 'Your proposal has been saved',
                        icon: 'success',
                    });
                }
                vm.savingProposal = false;
                const resData = await res.json();
                this.proposal = Object.assign({}, resData);
                this.$nextTick(async () => {
                    if (
                        increment_map_key &&
                        vm.$refs.application_form != undefined
                    ) {
                        vm.$refs.application_form.incrementComponentMapKey();
                    }
                });
                return resData;
            } else {
                const responseJSON = await res.json();
                vm.errors = responseJSON.errors;
                vm.savingProposal = false;

                if (vm.submitting) {
                    throw new Error(responseJSON);
                }
            }
        },
        save_exit: function () {
            let vm = this;
            this.saveExitProposal = true;
            this.save().then(() => {
                this.saveExitProposal = false;
                this.savingProposal = false;
                vm.$router.push({
                    name: 'external-dashboard',
                });
            });
        },
        save_wo_confirm: function () {
            this.save(false);
        },
        setdata: function (readonly) {
            this.proposal_readonly = readonly;
        },
        splitText: function (aText) {
            let newText = '';
            newText = aText.split('\n');
            return newText;
        },
        leaving: function (e) {
            let vm = this;
            var dialogText = 'You have some unsaved changes.';
            if (!vm.proposal_readonly && !vm.submitting) {
                e.returnValue = dialogText;
                return dialogText;
            } else {
                return null;
            }
        },
        highlight_missing_fields: function () {
            let vm = this;
            for (let missing_field of vm.missing_fields) {
                $('#' + missing_field.id).css('color', 'red');
            }
        },
        submit: async function () {
            let vm = this;

            // remove the confirm prompt when navigating away from window (on button 'Submit' click)
            vm.submitting = true;
            vm.paySubmitting = true;

            swal.fire({
                title: vm.submitText + ' Proposal',
                text:
                    'Are you sure you want to ' +
                    vm.submitText.toLowerCase() +
                    ' this application?',
                icon: 'question',
                reverseButtons: true,
                showCancelButton: true,
                confirmButtonText: vm.submitText,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(
                async (result) => {
                    if (!result.isConfirmed) {
                        // Cancel
                        vm.submitting = false;
                        vm.paySubmitting = false;
                        return;
                    } else {
                        // Accept
                        try {
                            await vm.save(false, vm.proposal_submit_url);
                            vm.$nextTick(() => {
                                // const lodgementDate = new Date(vm.proposal.lodgement_date)
                                vm.$router.push({
                                    name: 'submit-proposal',
                                    params: { proposal_id: vm.proposal.id },
                                });
                            });
                        } catch (err) {
                            console.error(err);
                            vm.submitting = false;
                            vm.savingProposal = false;
                            vm.paySubmitting = false;
                            // For some reason the scroll was not working with nexttick so am using a short timeout
                            setTimeout(() => {
                                window.scroll({
                                    top: 0,
                                    left: 0,
                                    behavior: 'smooth',
                                });
                            }, 200);
                        }
                    }
                },
                (error) => {
                    console.error(error);
                }
            );
        },
        fetchProposal: function (id) {
            let vm = this;
            vm.loadingProposal = true;
            fetch(api_endpoints.proposal + id + '.json')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.proposal = data;

                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.proposals,
                            vm.proposal.id + '/amendment_request'
                        )
                    ).then(
                        async (res) => {
                            this.amendment_request = await res.json();
                        },
                        (err) => {
                            console.error(err);
                        }
                    );

                    vm.loadingProposal = false;
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                });
        },
        refreshFromResponse: function (data) {
            this.proposal = Object.assign({}, data);
        },
        onFinishedDrawing: function () {
            if (this.$refs.application_form.$refs.component_map.autoSave) {
                this.saveMapFeatures();
            }
        },
        saveMapFeatures: function () {
            // Save the entire proposal including the map features without reloading the map
            this.save(false, this.proposal_form_url, false);
        },
    },
};
</script>
<style scoped>
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
