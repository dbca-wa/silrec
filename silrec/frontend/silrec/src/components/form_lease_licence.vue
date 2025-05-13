<template lang="html">
    <div>
        <div v-if="debug">components/form_lease_licence.vue</div>
        <FormSection
            v-if="show_supporting_documents"
            :form-collapse="false"
            label="Supporting Documents for Transfer"
            index="supporting_documents_for_transfer"
        >
            <FileField
                v-if="
                    proposal.approval.active_transfer.has_supporting_documents
                "
                id="supporting_documents"
                ref="supporting_documents"
                name="supporting_documents"
                :is-repeatable="true"
                :document-action-url="supportingDocumentsForTransferUrl"
                :replace_button_by_text="true"
                :readonly="true"
            />
            <div v-else>
                No supporting documents were provided for this transfer.
            </div>
        </FormSection>
        <FormSection
            v-if="proposal && show_tourism_proposal_details"
            :form-collapse="false"
            label="Tourism Proposal Details"
            index="tourism_proposal_details"
        >
            <slot
                name="slot_proposal_tourism_details_assessment_comments"
            ></slot>

            <div class="row mb-2">
                <div class="fw-bold">Profit and Loss</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="profit_and_loss_text" class="form-label"
                        >Provide five-year integrated profit and loss, balance
                        sheet and cash flow projections (preferably by month).
                        State clearly the underlying assumptions made in respect
                        to design, construction, rental, operations and target
                        markets</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="profit_and_loss_text"
                        ref="profit_and_loss_text"
                        :key="proposal.id"
                        :proposal-data="proposal.profit_and_loss_text"
                        :readonly="readonly"
                        required
                        @text-changed="proposal.profit_and_loss_text = $event"
                    />
                </div>
            </div>
            <div class="row pb-3">
                <label
                    for="profit_and_loss_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-8">
                    <FileField
                        id="profit_and_loss_documents"
                        ref="profit_and_loss_documents"
                        :readonly="readonly"
                        name="profit_and_loss_documents"
                        :is-repeatable="true"
                        :document-action-url="profitAndLossDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Cashflow</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="cash_flow_text" class="form-label"
                        >Provide cash flow projections to demonstrate time to
                        amortize the capital investment</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="cash_flow_text"
                        ref="cash_flow_text"
                        :key="proposal.id"
                        :proposal-data="proposal.cash_flow_text"
                        :readonly="readonly"
                        required
                        @text-changed="proposal.cash_flow_text = $event"
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label for="cash_flow_documents" class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="cash_flow_documents"
                        ref="cash_flow_documents"
                        :readonly="readonly"
                        name="cash_flow_documents"
                        :is-repeatable="true"
                        :document-action-url="cashFlowDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Capital Investment</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="capital_investment_text" class="form-label"
                        >Include proposed capital investment showing costing
                        against each component of the built development and
                        start-up costs</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="capital_investment_text"
                        ref="capital_investment_text"
                        :key="proposal.id"
                        :proposal-data="proposal.capital_investment_text"
                        :readonly="readonly"
                        required
                        @text-changed="
                            proposal.capital_investment_text = $event
                        "
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="capital_investment_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-8">
                    <FileField
                        id="capital_investment_documents"
                        ref="capital_investment_documents"
                        :readonly="readonly"
                        name="capital_investment_documents"
                        :is-repeatable="true"
                        :document-action-url="capitalInvestmentDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Financial Capacity</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="financial_capacity_text" class="form-label"
                        >Demonstrate that you and/or the nominated operator have
                        the financial capacity to build and operate the
                        proposal. Information/evidence from
                        banks/financiers/accountants would assist in
                        demonstrating this, for example, audited financial
                        statements for the last 3 years or letter from a
                        financier confirming access to the required
                        finance</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="financial_capacity_text"
                        ref="financial_capacity_text"
                        :key="proposal.id"
                        :proposal-data="proposal.financial_capacity_text"
                        :readonly="readonly"
                        required
                        @text-changed="
                            proposal.financial_capacity_text = $event
                        "
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="financial_capacity_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-8">
                    <FileField
                        id="financial_capacity_documents"
                        ref="financial_capacity_documents"
                        :readonly="readonly"
                        name="financial_capacity_documents"
                        :is-repeatable="true"
                        :document-action-url="financialCapacityDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Available Activities</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="available_activities_text" class="form-label"
                        >Specify the full range of recreational, educational,
                        cultural and other activities that will be available to
                        visitors through your proposal and what will be
                        required/developed to undertake them. Articulate the
                        timeline for the introduction of each activity over a
                        five-year period</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="available_activities_text"
                        ref="available_activities_text"
                        :key="proposal.id"
                        :proposal-data="proposal.available_activities_text"
                        :readonly="readonly"
                        required
                        @text-changed="
                            proposal.available_activities_text = $event
                        "
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="available_activities_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="available_activities_documents"
                        ref="available_activities_documents"
                        :readonly="readonly"
                        name="available_activities_documents"
                        :is-repeatable="true"
                        :document-action-url="availableActivitiesDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Market Analysis</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="market_analysis_text" class="form-label"
                        >Outline a market analysis that identifies the target
                        markets for the operation and how these will be
                        accommodated as well as a competitor analysis. (Note the
                        market analysis should inform the integrated profit and
                        loss and cash flow projections with realistic
                        assumptions and estimations)</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="market_analysis_text"
                        ref="market_analysis_text"
                        :key="proposal.id"
                        :proposal-data="proposal.market_analysis_text"
                        :readonly="readonly"
                        required
                        @text-changed="proposal.market_analysis_text = $event"
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="market_analysis_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="market_analysis_documents"
                        ref="market_analysis_documents"
                        :readonly="readonly"
                        name="market_analysis_documents"
                        :is-repeatable="true"
                        :document-action-url="marketAnalysisDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Staffing</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="staffing_text" class="form-label"
                        >Provide details of staffing, workforce management.
                        (Note the market analysis should inform the integrated
                        profit and loss and cash flow projections with realistic
                        assumptions and estimations)</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="staffing_text"
                        ref="staffing_text"
                        :key="proposal.id"
                        :proposal-data="proposal.staffing_text"
                        :readonly="readonly"
                        required
                        @text-changed="proposal.staffing_text = $event"
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label for="staffing_documents" class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="staffing_documents"
                        ref="staffing_documents"
                        :readonly="readonly"
                        name="staffing_documents"
                        :is-repeatable="true"
                        :document-action-url="staffingDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </FormSection>

        <FormSection
            v-if="proposal"
            :form-collapse="false"
            label="General Proposal Details"
            index="general_proposal_details"
        >
            <slot
                name="slot_proposal_general_details_assessment_comments"
            ></slot>
            <div class="row mb-2">
                <div class="fw-bold">Key Personnel</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="key_personnel_text" class="form-label">
                        Provide details of the key personnel and their
                        qualifications and experience that is appropriate to
                        developing and operating the venture under the proposed
                        tourism lease. Include bios of the proposed board and
                        management team demonstrating capability in delivering
                        and maintaining the proposal</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="key_personnel_text"
                        ref="key_personnel_text"
                        :key="proposal.id"
                        :proposal-data="proposal.key_personnel_text"
                        :readonly="readonly"
                        @text-changed="proposal.key_personnel_text = $event"
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="key_personnel_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="key_personnel_documents"
                        ref="key_personnel_documents"
                        :readonly="readonly"
                        name="key_personnel_documents"
                        :is-repeatable="true"
                        :document-action-url="keyPersonnelDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Key Milestones</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="key_milestones_text" class="form-label"
                        >Provide details regarding key milestones</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="key_milestones_text"
                        ref="key_milestones_text"
                        :key="proposal.id"
                        :proposal-data="proposal.key_milestones_text"
                        :readonly="readonly"
                        @text-changed="proposal.key_milestones_text = $event"
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="key_milestones_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="key_milestones_documents"
                        ref="key_milestones_documents"
                        :readonly="readonly"
                        name="key_milestones_documents"
                        :is-repeatable="true"
                        :document-action-url="keyMilestonesDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Risk Factors</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label for="risk_factors_text" class="form-label"
                        >Identify specific risk factors and likely impacts to
                        allow consideration of options. Include how key risks
                        will be avoided, reduced, managed or mitigated. (Note
                        the management of risk should inform the integrated
                        profit and loss and cash flow projections).</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="risk_factors_text"
                        ref="risk_factors_text"
                        :key="proposal.id"
                        :proposal-data="proposal.risk_factors_text"
                        :readonly="readonly"
                        @text-changed="proposal.risk_factors_text = $event"
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="risk_factors_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="risk_factors_documents"
                        ref="risk_factors_documents"
                        :readonly="readonly"
                        name="risk_factors_documents"
                        :is-repeatable="true"
                        :document-action-url="riskFactorsDocumentsUrl"
                        :replace_button_by_text="true"
                    />
                </div>
            </div>

            <div class="row mb-2 pt-3 border-top">
                <div class="fw-bold">Legislative Requirements</div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <label
                        for="legislative_requirements_text"
                        class="form-label"
                        >If legislative or regulatory requirements apply to the
                        proposal, please provide details and upload any
                        approvals already received</label
                    >
                </div>
            </div>
            <div class="row mb-3">
                <div class="col">
                    <RichText
                        id="legislative_requirements_text"
                        ref="legislative_requirements_text"
                        :key="proposal.id"
                        :proposal-data="proposal.legislative_requirements_text"
                        :readonly="readonly"
                        @text-changed="
                            proposal.legislative_requirements_text = $event
                        "
                    />
                </div>
            </div>
            <div class="row mb-3">
                <label
                    for="legislative_requirements_documents"
                    class="col-form-label col-sm-4"
                    >Attach any supporting documents</label
                >
                <div class="col-sm-9">
                    <FileField
                        id="legislative_requirements_documents"
                        ref="legislative_requirements_documents"
                        :readonly="readonly"
                        name="legislative_requirements_documents"
                        :is-repeatable="true"
                        :document-action-url="
                            legislativeRequirementsDocumentsUrl
                        "
                        :replace_button_by_text="true"
                    />
                </div>
            </div>
        </FormSection>

        <FormSection
            v-if="proposal"
            :form-collapse="false"
            label="Proponent Reference Number"
            index="proponent_reference_number"
        >
            <BootstrapAlert v-if="!is_internal">
                <ul class="list-group">
                    <li class="list-group-item">
                        You may use this field to identify the application
                        within your organisation (or for your own records).
                    </li>
                    <!-- Note: Add this back in when we have a way to add the proponent reference number to the invoice programatically
                    <li class="list-group-item">
                        If entered, it will be displayed on any invoices
                        generated by our system.
                    </li>
                --></ul>
            </BootstrapAlert>
            <div class="row mb-3">
                <div class="col-sm-4">
                    <label class="" for="proponent_reference"
                        >Proponent Reference Number</label
                    >
                </div>
                <div class="col-sm-8">
                    <input
                        id="proponent_reference"
                        v-model="proposal.proponent_reference_number"
                        type="text"
                        class="form-control"
                        name="proponent_reference"
                        :readonly="is_internal || readonly"
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
import { api_endpoints, constants, helpers } from '@/utils/hooks';

export default {
    name: 'LeaseLicenceForm',
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
        is_internal: {
            type: Boolean,
            required: true,
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
        supportingDocumentsForTransferUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.approval_transfers,
                this.proposal.approval.active_transfer.id +
                    '/process_supporting_document/'
            );
        },
        show_supporting_documents: function () {
            return (
                this.proposal &&
                this.proposal.approval &&
                this.proposal.proposal_type.code ==
                    constants.PROPOSAL_TYPE.TRANSFER.code &&
                this.proposal.approval.active_transfer
            );
        },
        show_tourism_proposal_details: function () {
            return (
                this.proposal &&
                this.proposal.groups.find(
                    (group) => group.name.trim().toLowerCase() == 'tourism'
                )
            );
        },
        profitAndLossDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_profit_and_loss_document/'
            );
        },
        cashFlowDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_cash_flow_document/'
            );
        },
        capitalInvestmentDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_capital_investment_document/'
            );
        },
        financialCapacityDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_financial_capacity_document/'
            );
        },
        availableActivitiesDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_available_activities_document/'
            );
        },
        marketAnalysisDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_market_analysis_document/'
            );
        },
        staffingDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_staffing_document/'
            );
        },
        keyPersonnelDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_key_personnel_document/'
            );
        },
        keyMilestonesDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_key_milestones_document/'
            );
        },
        riskFactorsDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_risk_factors_document/'
            );
        },
        legislativeRequirementsDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_legislative_requirements_document/'
            );
        },
    },
};
</script>

<style lang="css" scoped>
.inline-details-text {
    margin-bottom: 20px;
}

.question-row {
    margin-bottom: 10px;
    padding-left: 15px;
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
