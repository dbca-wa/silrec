<template lang="html">
    <div>
        <div v-if="debug">components/form_registration_of_interest.vue</div>
        <FormSection
            v-if="proposal"
            :form-collapse="false"
            label="Proposal Details"
            index="application_details"
        >
            <slot name="slot_proposal_details_assessment_comments"></slot>

            <div class="row mb-3">
                <div class="col-12">
                    <label for="details_text" class="form-label"
                        >Provide a description of your proposal</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="details_text"
                        ref="details_text"
                        :key="proposal.id"
                        :proposal-data="proposal.details_text"
                        label="Rich text in here"
                        :readonly="readonly"
                        @text-changed="proposal.details_text = $event"
                    />
                </div>
            </div>

            <div class="row pb-3">
                <div class="col-sm-4">
                    <label for="supporting_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-8">
                    <FileField
                        id="supporting_documents"
                        ref="supporting_documents"
                        :readonly="readonly"
                        name="supporting_documents"
                        :is-repeatable="true"
                        :document-action-url="supportingDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal require exclusive use of or
                        non-exclusive access to a site?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="exclusive_use_yes"
                            v-model="proposal.exclusive_use"
                            class="form-check-input"
                            type="radio"
                            name="exclusive_use_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="exclusive_use_yes" class="form-check-label"
                            >Yes</label
                        >
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="exclusive_use_no"
                            v-model="proposal.exclusive_use"
                            class="form-check-input"
                            type="radio"
                            name="exclusive_use_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                            :checked="null == proposal.exclusive_use"
                        />
                        <label for="exclusive_use_no">No</label>
                    </div>
                </div>
            </div>

            <div v-show="proposal.exclusive_use" class="row mb-3">
                <div class="col-12">
                    <label class="form-label">Provide details</label>
                </div>
                <div class="col-12">
                    <RichText
                        id="exclusive_use_text"
                        ref="exclusive_use_text"
                        :key="proposal.id"
                        :proposal-data="proposal.exclusive_use_text"
                        :readonly="readonly"
                        @text-changed="proposal.exclusive_use_text = $event"
                    />
                </div>
            </div>
            <div v-show="proposal.exclusive_use" class="row pb-3 mb-3">
                <div class="col-sm-4">
                    <label for="exclusive_use_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-8">
                    <FileField
                        id="exclusive_use_documents"
                        ref="exclusive_use_documents"
                        :readonly="readonly"
                        name="exclusive_use_documents"
                        :is-repeatable="true"
                        :document-action-url="exclusiveUseDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal require long-term use of or access to
                        a site?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="long_term_use_yes"
                            v-model="proposal.long_term_use"
                            class="form-check-input"
                            type="radio"
                            name="long_term_use_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="long_term_use_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="long_term_use_no"
                            v-model="proposal.long_term_use"
                            class="form-check-input"
                            type="radio"
                            name="long_term_use_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                            :checked="null == proposal.long_term_use"
                        />
                        <label for="long_term_use_no">No</label>
                    </div>
                </div>
            </div>

            <div v-show="proposal.long_term_use" class="row mb-3">
                <div class="col-12">
                    <label for="long_term_use_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="long_term_use_text"
                        ref="long_term_use_text"
                        :key="proposal.id"
                        :proposal-data="proposal.long_term_use_text"
                        :readonly="readonly"
                        @text-changed="proposal.long_term_use_text = $event"
                    />
                </div>
            </div>

            <div v-show="proposal.long_term_use" class="row mb-3">
                <div class="col-sm-4">
                    <label for="long_term_use_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-8">
                    <FileField
                        id="long_term_use_documents"
                        ref="long_term_use_documents"
                        :readonly="readonly"
                        name="long_term_use_documents"
                        :is-repeatable="true"
                        :document-action-url="longTermUseDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Is the proposal consistent with the purpose of the park
                        or reserve?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="consistent_purpose_yes"
                            v-model="proposal.consistent_purpose"
                            class="form-check-input"
                            type="radio"
                            name="consistent_purpose_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="consistent_purpose_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="consistent_purpose_no"
                            v-model="proposal.consistent_purpose"
                            class="form-check-input"
                            type="radio"
                            name="consistent_purpose_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="consistent_purpose_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="consistent_purpose_null"
                            v-model="proposal.consistent_purpose"
                            class="form-check-input"
                            type="radio"
                            name="consistent_purpose_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="consistent_purpose_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.consistent_purpose" class="row mb-3">
                <div class="col-12">
                    <label for="consistent_purpose_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="consistent_purpose_text"
                        ref="consistent_purpose_text"
                        :key="proposal.id"
                        :proposal-data="proposal.consistent_purpose_text"
                        :readonly="readonly"
                        @text-changed="
                            proposal.consistent_purpose_text = $event
                        "
                    />
                </div>
            </div>
            <div v-show="proposal.consistent_purpose" class="row mb-3">
                <div class="col-sm-4">
                    <label for="consistent_purpose_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-8">
                    <FileField
                        id="consistent_purpose_documents"
                        ref="consistent_purpose_documents"
                        :readonly="readonly"
                        name="consistent_purpose_documents"
                        :is-repeatable="true"
                        :document-action-url="consistentPurposeDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-1 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Is the proposal consistent with the park or reserve
                        management plan?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="consistent_plan_yes"
                            v-model="proposal.consistent_plan"
                            class="form-check-input"
                            type="radio"
                            name="consistent_plan_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="consistent_plan_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="consistent_plan_no"
                            v-model="proposal.consistent_plan"
                            class="form-check-input"
                            type="radio"
                            name="consistent_plan_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="consistent_plan_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="consistent_plan_null"
                            v-model="proposal.consistent_plan"
                            class="form-check-input"
                            type="radio"
                            name="consistent_plan_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="consistent_plan_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.consistent_plan" class="row mb-3">
                <div class="col-12">
                    <label for="consistent_plan_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="consistent_plan_text"
                        ref="consistent_plan_text"
                        :key="proposal.id"
                        :proposal-data="proposal.consistent_plan_text"
                        :readonly="readonly"
                        @text-changed="proposal.consistent_plan_text = $event"
                    />
                </div>
            </div>
            <div v-show="proposal.consistent_plan" class="row mb-3">
                <div class="col-sm-6">
                    <label for="consistent_plan_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-6">
                    <FileField
                        id="consistent_plan_documents"
                        ref="consistent_plan_documents"
                        :readonly="readonly"
                        name="consistent_plan_documents"
                        :is-repeatable="true"
                        :document-action-url="consistentPlanDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </FormSection>

        <FormSection
            v-if="proposal"
            :form-collapse="false"
            label="Proposal Impact"
            index="proposal_impact"
        >
            <slot name="slot_proposal_impact_assessment_comments"></slot>
            <div class="row mb-3">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal involve clearing of native
                        vegetation?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="clearing_vegetation_yes"
                            v-model="proposal.clearing_vegetation"
                            class="form-check-input"
                            type="radio"
                            name="clearing_vegetation_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="clearing_vegetation_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="clearing_vegetation_no"
                            v-model="proposal.clearing_vegetation"
                            class="form-check-input"
                            type="radio"
                            name="clearing_vegetation_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="clearing_vegetation_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="clearing_vegetation_null"
                            v-model="proposal.clearing_vegetation"
                            class="form-check-input"
                            type="radio"
                            name="clearing_vegetation_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="clearing_vegetation_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.clearing_vegetation" class="row mb-3">
                <div class="col-12">
                    <label for="clearing_vegetation_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="clearing_vegetation_text"
                        ref="clearing_vegetation_text"
                        :key="proposal.id"
                        :proposal-data="proposal.clearing_vegetation_text"
                        :readonly="readonly"
                        @text-changed="
                            proposal.clearing_vegetation_text = $event
                        "
                    />
                </div>
            </div>
            <div v-show="proposal.clearing_vegetation" class="row mb-3">
                <div class="col-sm-3">
                    <label for="clearing_vegetation_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="clearing_vegetation_documents"
                        ref="clearing_vegetation_documents"
                        :readonly="readonly"
                        name="clearing_vegetation_documents"
                        :is-repeatable="true"
                        :document-action-url="clearingVegetationDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal involve ground-disturbing
                        works?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="ground_disturbing_works_yes"
                            v-model="proposal.ground_disturbing_works"
                            class="form-check-input"
                            type="radio"
                            name="ground_disturbing_works_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="ground_disturbing_works_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="ground_disturbing_works_no"
                            v-model="proposal.ground_disturbing_works"
                            class="form-check-input"
                            type="radio"
                            name="ground_disturbing_works_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="ground_disturbing_works_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="ground_disturbing_works_null"
                            v-model="proposal.ground_disturbing_works"
                            class="form-check-input"
                            type="radio"
                            name="ground_disturbing_works_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="ground_disturbing_works_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.ground_disturbing_works" class="row mb-3">
                <div class="col-12">
                    <label for="ground_disturbing_works_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="ground_disturbing_works_text"
                        ref="ground_disturbing_works_text"
                        :key="proposal.id"
                        :proposal-data="proposal.ground_disturbing_works_text"
                        :readonly="readonly"
                        @text-changed="
                            proposal.ground_disturbing_works_text = $event
                        "
                    />
                </div>
            </div>
            <div v-show="proposal.ground_disturbing_works" class="row mb-3">
                <div class="col-sm-3">
                    <label for="ground_disturbing_works_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="ground_disturbing_works_documents"
                        ref="ground_disturbing_works_documents"
                        :readonly="readonly"
                        name="ground_disturbing_works_documents"
                        :is-repeatable="true"
                        :document-action-url="groundDisturbingWorksDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal impact on a World or National
                        Heritage area?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="heritage_site_yes"
                            v-model="proposal.heritage_site"
                            class="form-check-input"
                            type="radio"
                            name="heritage_site_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="heritage_site_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="heritage_site_no"
                            v-model="proposal.heritage_site"
                            class="form-check-input"
                            type="radio"
                            name="heritage_site_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="heritage_site_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="heritage_site_null"
                            v-model="proposal.heritage_site"
                            class="form-check-input"
                            type="radio"
                            name="heritage_site_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="heritage_site_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.heritage_site" class="row mb-3">
                <div class="col-12">
                    <label for="heritage_site_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="heritage_site_text"
                        ref="heritage_site_text"
                        :key="proposal.id"
                        :proposal-data="proposal.heritage_site_text"
                        :readonly="readonly"
                        @text-changed="proposal.heritage_site_text = $event"
                    />
                </div>
            </div>
            <div v-show="proposal.heritage_site" class="row mb-3">
                <div class="col-sm-3">
                    <label for="heritage_site_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="heritage_site_documents"
                        ref="heritage_site_documents"
                        :readonly="readonly"
                        name="heritage_site_documents"
                        :is-repeatable="true"
                        :document-action-url="heritageSiteDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Is the proposal located in a environmentally sensitive
                        area or habitat for significant flora and fauna?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="environmentally_sensitive_yes"
                            v-model="proposal.environmentally_sensitive"
                            class="form-check-input"
                            type="radio"
                            name="environmentally_sensitive_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="environmentally_sensitive_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="environmentally_sensitive_no"
                            v-model="proposal.environmentally_sensitive"
                            class="form-check-input"
                            type="radio"
                            name="environmentally_sensitive_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="environmentally_sensitive_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="environmentally_sensitive_null"
                            v-model="proposal.environmentally_sensitive"
                            class="form-check-input"
                            type="radio"
                            name="environmentally_sensitive_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="environmentally_sensitive_null"
                            >Unsure</label
                        >
                    </div>
                </div>
            </div>
            <div v-show="proposal.environmentally_sensitive" class="row mb-3">
                <div class="col-12">
                    <label
                        for="environmentally_sensitive_text"
                        class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="environmentally_sensitive_text"
                        ref="environmentally_sensitive_text"
                        :key="proposal.id"
                        :proposal-data="proposal.environmentally_sensitive_text"
                        :readonly="readonly"
                        @text-changed="
                            proposal.environmentally_sensitive_text = $event
                        "
                    />
                </div>
            </div>
            <div v-show="proposal.environmentally_sensitive" class="row mb-3">
                <div class="col-sm-3">
                    <label for="environmentally_sensitive_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="environmentally_sensitive_documents"
                        ref="environmentally_sensitive_documents"
                        :readonly="readonly"
                        name="environmentally_sensitive_documents"
                        :is-repeatable="true"
                        :document-action-url="
                            environmentallySensitiveDocumentsUrl
                        "
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal impact on wetlands or water
                        courses?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="wetlands_impact_yes"
                            v-model="proposal.wetlands_impact"
                            class="form-check-input"
                            type="radio"
                            name="wetlands_impact_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="wetlands_impact_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="wetlands_impact_no"
                            v-model="proposal.wetlands_impact"
                            class="form-check-input"
                            type="radio"
                            name="wetlands_impact_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="wetlands_impact_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="wetlands_impact_null"
                            v-model="proposal.wetlands_impact"
                            class="form-check-input"
                            type="radio"
                            name="wetlands_impact_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="wetlands_impact_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.wetlands_impact" class="row mb-3">
                <div class="col-12">
                    <label for="wetlands_impact_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="wetlands_impact_text"
                        ref="wetlands_impact_text"
                        :key="proposal.id"
                        :proposal-data="proposal.wetlands_impact_text"
                        :readonly="readonly"
                        @text-changed="proposal.wetlands_impact_text = $event"
                    />
                </div>
            </div>
            <div v-show="proposal.wetlands_impact" class="row mb-3">
                <div class="col-sm-3">
                    <label for="wetlands_impact_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="wetlands_impact_documents"
                        ref="wetlands_impact_documents"
                        :readonly="readonly"
                        name="wetlands_impact_documents"
                        :is-repeatable="true"
                        :document-action-url="wetlandsImpactDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal involve building a structure or
                        building?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="building_required_yes"
                            v-model="proposal.building_required"
                            class="form-check-input"
                            type="radio"
                            name="building_required_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="building_required_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="building_required_no"
                            v-model="proposal.building_required"
                            class="form-check-input"
                            type="radio"
                            name="building_required_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="building_required_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="building_required_null"
                            v-model="proposal.building_required"
                            class="form-check-input"
                            type="radio"
                            name="building_required_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="building_required_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.building_required" class="row mb-3">
                <div class="col-12">
                    <label for="building_required_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="building_required_text"
                        ref="building_required_text"
                        :key="proposal.id"
                        :proposal-data="proposal.building_required_text"
                        :readonly="readonly"
                        @text-changed="proposal.building_required_text = $event"
                    />
                </div>
            </div>
            <div v-show="proposal.building_required" class="row mb-3">
                <div class="col-sm-3">
                    <label for="building_required_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="building_required_documents"
                        ref="building_required_documents"
                        :readonly="readonly"
                        name="building_required_documents"
                        :is-repeatable="true"
                        :document-action-url="buildingRequiredDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal create a significant change to or
                        visual impact on the proposed site?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="significant_change_yes"
                            v-model="proposal.significant_change"
                            class="form-check-input"
                            type="radio"
                            name="significant_change_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="significant_change_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="significant_change_no"
                            v-model="proposal.significant_change"
                            class="form-check-input"
                            type="radio"
                            name="significant_change_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="significant_change_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="significant_change_null"
                            v-model="proposal.significant_change"
                            class="form-check-input"
                            type="radio"
                            name="significant_change_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="significant_change_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.significant_change" class="row mb-3">
                <div class="col-12">
                    <label for="significant_change_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="significant_change_text"
                        ref="significant_change_text"
                        :key="proposal.id"
                        :proposal-data="proposal.significant_change_text"
                        :readonly="readonly"
                        @text-changed="
                            proposal.significant_change_text = $event
                        "
                    />
                </div>
            </div>
            <div v-show="proposal.significant_change" class="row mb-3">
                <div class="col-sm-3">
                    <label for="significant_change_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="significant_change_documents"
                        ref="significant_change_documents"
                        :readonly="readonly"
                        name="significant_change_documents"
                        :is-repeatable="true"
                        :document-action-url="significantChangeDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal impact on a
                        <a target="_blank" href="http://www.google.com"
                            >registered Aboriginal site</a
                        >?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="aboriginal_site_yes"
                            v-model="proposal.aboriginal_site"
                            class="form-check-input"
                            type="radio"
                            name="aboriginal_site_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="aboriginal_site_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="aboriginal_site_no"
                            v-model="proposal.aboriginal_site"
                            class="form-check-input"
                            type="radio"
                            name="aboriginal_site_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="aboriginal_site_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="aboriginal_site_null"
                            v-model="proposal.aboriginal_site"
                            class="form-check-input"
                            type="radio"
                            name="aboriginal_site_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="aboriginal_site_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.aboriginal_site" class="row mb-3">
                <div class="col-12">
                    <label for="aboriginal_site_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="aboriginal_site_text"
                        ref="aboriginal_site_text"
                        :key="proposal.id"
                        :proposal-data="proposal.aboriginal_site_text"
                        :readonly="readonly"
                        @text-changed="proposal.aboriginal_site_text = $event"
                    />
                </div>
            </div>
            <div v-show="proposal.aboriginal_site" class="row mb-3">
                <div class="col-sm-3">
                    <label for="aboriginal_site_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="aboriginal_site_documents"
                        ref="aboriginal_site_documents"
                        :readonly="readonly"
                        name="aboriginal_site_documents"
                        :is-repeatable="true"
                        :document-action-url="aboriginalSiteDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Has any consultation occurred with the relevant
                        Aboriginal native title party?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="native_title_consultation_yes"
                            v-model="proposal.native_title_consultation"
                            class="form-check-input"
                            type="radio"
                            name="native_title_consultation_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="native_title_consultation_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="native_title_consultation_no"
                            v-model="proposal.native_title_consultation"
                            class="form-check-input"
                            type="radio"
                            name="native_title_consultation_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="native_title_consultation_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="native_title_consultation_null"
                            v-model="proposal.native_title_consultation"
                            class="form-check-input"
                            type="radio"
                            name="native_title_consultation_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="native_title_consultation_null"
                            >Unsure</label
                        >
                    </div>
                </div>
            </div>
            <div v-show="proposal.native_title_consultation" class="row mb-3">
                <div class="col-12">
                    <label
                        for="native_title_consultation_text"
                        class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="native_title_consultation_text"
                        ref="native_title_consultation_text"
                        :key="proposal.id"
                        :proposal-data="proposal.native_title_consultation_text"
                        :readonly="readonly"
                        @text-changed="
                            proposal.native_title_consultation_text = $event
                        "
                    />
                </div>
            </div>
            <div v-show="proposal.native_title_consultation" class="row mb-3">
                <div class="col-sm-3">
                    <label for="native_title_consultation_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="native_title_consultation_documents"
                        ref="native_title_consultation_documents"
                        :readonly="readonly"
                        name="native_title_consultation_documents"
                        :is-repeatable="true"
                        :document-action-url="
                            nativeTitleConsultationDocumentsUrl
                        "
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-3 pt-3 border-top">
                <div class="col-sm-8">
                    <label class="col-form-label"
                        >Will the proposal impact on a
                        <a target="_blank" href="http://google.com"
                            >mining tenement</a
                        >?</label
                    >
                </div>
                <div class="col-sm-4">
                    <div class="form-check form-check-inline pt-2">
                        <input
                            id="mining_tenement_yes"
                            v-model="proposal.mining_tenement"
                            class="form-check-input"
                            type="radio"
                            name="mining_tenement_yes"
                            :value="true"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="mining_tenement_yes">Yes</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="mining_tenement_no"
                            v-model="proposal.mining_tenement"
                            class="form-check-input"
                            type="radio"
                            name="mining_tenement_no"
                            :value="false"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="mining_tenement_no">No</label>
                    </div>
                    <div class="form-check form-check-inline">
                        <input
                            id="mining_tenement_null"
                            v-model="proposal.mining_tenement"
                            class="form-check-input"
                            type="radio"
                            name="mining_tenement_null"
                            :value="null"
                            data-parsley-required
                            :disabled="readonly"
                        />
                        <label for="mining_tenement_null">Unsure</label>
                    </div>
                </div>
            </div>
            <div v-show="proposal.mining_tenement" class="row mb-3">
                <div class="col-12">
                    <label for="mining_tenement_text" class="form-label"
                        >Provide details</label
                    >
                </div>
                <div class="col-12">
                    <RichText
                        id="mining_tenement_text"
                        ref="mining_tenement_text"
                        :key="proposal.id"
                        :proposal-data="proposal.mining_tenement_text"
                        :readonly="readonly"
                        @text-changed="proposal.mining_tenement_text = $event"
                    />
                </div>
            </div>
            <div v-show="proposal.mining_tenement" class="row mb-3">
                <div class="col-sm-3">
                    <label for="mining_tenement_documents"
                        >Attach any supporting documents</label
                    >
                </div>
                <div class="col-sm-9">
                    <FileField
                        id="mining_tenement_documents"
                        ref="mining_tenement_documents"
                        :readonly="readonly"
                        name="mining_tenement_documents"
                        :is-repeatable="true"
                        :document-action-url="miningTenementDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </FormSection>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import RichText from '@/components/forms/RichText.vue';
import FileField from '@/components/forms/filefield_immediate.vue';
import { api_endpoints, helpers } from '@/utils/hooks';

export default {
    name: 'RegistrationOfInterestForm',
    components: {
        FormSection,
        RichText,
        FileField,
    },
    props: {
        proposal: {
            type: Object,
            required: true,
        },
        readonly: {
            type: Boolean,
            default: true,
        },
    },
    data: function () {
        return {};
    },
    computed: {
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        proposalId: function () {
            return this.proposal ? this.proposal.id : null;
        },
        deedPollDocumentUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_deed_poll_document/'
            );
        },
        supportingDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_supporting_document/'
            );
        },
        exclusiveUseDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_exclusive_use_document/'
            );
        },
        longTermUseDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_long_term_use_document/'
            );
        },
        consistentPurposeDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_consistent_purpose_document/'
            );
        },
        consistentPlanDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_consistent_plan_document/'
            );
        },
        clearingVegetationDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_clearing_vegetation_document/'
            );
        },
        groundDisturbingWorksDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_ground_disturbing_works_document/'
            );
        },
        heritageSiteDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_heritage_site_document/'
            );
        },
        environmentallySensitiveDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id +
                    '/process_environmentally_sensitive_document/'
            );
        },
        wetlandsImpactDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_wetlands_impact_document/'
            );
        },
        buildingRequiredDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_building_required_document/'
            );
        },
        significantChangeDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_significant_change_document/'
            );
        },
        aboriginalSiteDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_aboriginal_site_document/'
            );
        },
        nativeTitleConsultationDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id +
                    '/process_native_title_consultation_document/'
            );
        },
        miningTenementDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_mining_tenement_document/'
            );
        },
    },
    mounted: function () {},
    methods: {},
};
</script>

<style lang="css" scoped>
.inline-details-text {
    margin-bottom: 20px;
}

.details-text {
    padding-left: 15px;
}

.section-style {
    padding-left: 15px;
    margin-bottom: 20px;
}

.list-inline-item {
    padding-right: 15px;
}

.section {
    text-transform: capitalize;
}

.list-group {
    margin-bottom: 0;
}

.fixed-top {
    position: fixed;
    top: 56px;
}

.nav-item {
    margin-bottom: 2px;
}

.nav-item > li > a {
    background-color: yellow !important;
    color: #fff;
}

.nav-item > li.active > a,
.nav-item > li.active > a:hover,
.nav-item > li.active > a:focus {
    color: white;
    background-color: blue;
    border: 1px solid #888888;
}

.admin > div {
    display: inline-block;
    vertical-align: top;
    margin-right: 1em;
}
</style>
