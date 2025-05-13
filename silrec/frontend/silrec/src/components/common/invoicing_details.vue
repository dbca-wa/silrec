<template>
    <form id="invoicing-form" novalidate class="needs-validation">
        <div class="row mb-4">
            <label class="col-form-label col-sm-4"
                >Lease or Licence Charge Method</label
            >
            <div class="col-sm-8">
                <ul class="list-group">
                    <li
                        v-for="(charge_method, index) in charge_methods"
                        :key="charge_method.key"
                        class="list-group-item"
                    >
                        <input
                            v-if="invoicingDetailsComputed"
                            :id="charge_method.key"
                            v-model="invoicingDetailsComputed.charge_method"
                            type="radio"
                            class="form-check-input me-2"
                            name="charge_method"
                            :value="charge_method.id"
                            required
                            :disabled="
                                context == 'Approval' &&
                                charge_method.id !=
                                    invoicingDetailsComputed.charge_method
                            "
                            @change="onChargeMethodChange(charge_method)"
                        />
                        <label
                            :for="charge_method.key"
                            class="form-check-label"
                            >{{ charge_method.display_name }}</label
                        >
                        <div
                            v-if="index == charge_methods.length - 1"
                            class="invalid-tooltip mt-2 invalid-charge-method"
                        >
                            You must select a charge method.
                        </div>
                    </li>
                </ul>
            </div>
        </div>
        <div
            v-if="show_oracle_code"
            class="row mb-3 pt-3 border-top border-bottom"
        >
            <div>
                <BootstrapAlert>
                    <div class="mb-2">
                        The <strong>Receivable Activity Code</strong> determines
                        where the revenue from this {{ approvalType }} will be
                        allocated
                    </div>
                    <div>
                        To add a new code please visit:
                        <a
                            href="/admin/silrec/oraclecode/"
                            target="_blank"
                            >Oracle Codes Admin</a
                        >
                    </div>
                </BootstrapAlert>
            </div>

            <label for="oracle_code" class="col-form-label col-sm-4"
                >Receivable Activity Code</label
            >
            <div class="col-sm-8 mb-3">
                <Multiselect
                    id="oracle_code"
                    ref="oracle_code"
                    v-model="invoicingDetailsComputed.oracle_code"
                    :custom-label="
                        (opt) => oracle_codes.find((x) => x.id == opt)?.code
                    "
                    placeholder="Start Typing to Search for a Code"
                    :options="oracle_codes.map((oracle_code) => oracle_code.id)"
                    :allow-empty="false"
                    :hide-selected="true"
                    :multiple="false"
                    :searchable="true"
                    :loading="loadingOracleCodes"
                    :disabled="false"
                    @select="updatePreviewInvoices"
                    @change="updatePreviewInvoices"
                />
            </div>
        </div>
        <div v-if="show_once_off_charge_amount" class="row mb-3">
            <div class="col-sm-4">
                <label for="once_off_charge_amount" class="control-label"
                    >Once-off Charge ($AUD)</label
                >
            </div>
            <div class="col-sm-8">
                <input
                    v-if="invoicingDetailsComputed"
                    id="once_off_charge_amount"
                    v-model="invoicingDetailsComputed.once_off_charge_amount"
                    type="number"
                    min="1"
                    class="form-control"
                    :readonly="context != 'Proposal'"
                    required
                />
            </div>
        </div>
        <div v-if="show_base_fee" class="row mb-3 pb-3 border-bottom">
            <label for="base_fee_amount" class="col-form-label col-sm-4"
                >Base Fee ($AUD)</label
            >
            <div class="col-sm-8">
                <input
                    v-if="invoicingDetailsComputed"
                    id="base_fee_amount"
                    v-model="invoicingDetailsComputed.base_fee_amount"
                    type="number"
                    min="0"
                    step="1"
                    class="form-control"
                    required
                    @keyup="updatePreviewInvoices"
                />
            </div>
        </div>

        <div
            v-if="show_crown_land_rent_review_interval"
            class="row mb-3 pb-3 border-bottom"
        >
            <label class="col-form-label col-sm-4"
                >Crown Land Rent Review</label
            >
            <div class="col-sm-8">
                <div class="d-flex align-items-center">
                    <div class="pe-3">Once every</div>
                    <div class="pe-3">
                        <input
                            v-if="invoicingDetailsComputed"
                            id="review_once_every"
                            v-model="invoicingDetailsComputed.review_once_every"
                            type="number"
                            min="1"
                            max="20"
                            step="1"
                            class="form-control"
                            :readonly="crown_land_rent_review_readonly"
                            required
                            @change="saveInvoicingDetails"
                        />
                    </div>
                    <div class="">
                        <select
                            v-model="
                                invoicingDetailsComputed.review_repetition_type
                            "
                            class="form-select"
                            aria-label="Repetition Type"
                            required
                            disabled
                        >
                            <option
                                v-for="repetition_type in repetition_types"
                                :key="repetition_type.key"
                                :value="repetition_type.id"
                            >
                                {{ repetition_type.display_name }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="show_custom_cpi_years" class="row mb-3 pb-3 border-bottom">
            <template
                v-for="custom_cpi_year in invoicingDetailsComputed.custom_cpi_years"
                :key="custom_cpi_year.year"
            >
                <div class="div d-flex align-items-center mb-3">
                    <div class="col-sm-2 pe-3">
                        <div class="input-group">
                            <span class="input-group-text">Year</span>
                            <input
                                v-model="custom_cpi_year.year"
                                type="text"
                                readonly
                                class="form-control form-control-year text-center"
                            />
                        </div>
                    </div>
                    <div class="pe-3">Label</div>
                    <div class="col-sm-6 pe-3">
                        <div class="input-group">
                            <input
                                v-model="custom_cpi_year.label"
                                type="text"
                                class="form-control"
                                :readonly="
                                    customCPIYearReadonly(custom_cpi_year)
                                "
                                :required="
                                    !isMigrationProposal &&
                                    custom_cpi_year.has_passed
                                "
                            />
                        </div>
                    </div>
                    <label class="col-sm-3">
                        <div class="input-group">
                            <span class="input-group-text">CPI</span>
                            <input
                                v-model="custom_cpi_year.percentage"
                                step="0.1"
                                min="-100"
                                max="100"
                                type="number"
                                class="form-control"
                                :readonly="
                                    customCPIYearReadonly(custom_cpi_year)
                                "
                                :required="
                                    !isMigrationProposal &&
                                    custom_cpi_year.has_passed
                                "
                                @change="updatePreviewInvoices"
                                @keyup="updatePreviewInvoices"
                            />
                            <span class="input-group-text">%</span>
                        </div>
                    </label>
                </div>
            </template>
            <div class="row">
                <div class="col">
                    <BootstrapAlert
                        >You will be sent reminders to enter the custom cpi 60
                        days and 45 days prior to the next invoicing
                        period</BootstrapAlert
                    >
                </div>
            </div>
        </div>
        <div v-if="show_cpi_method">
            <div class="row mb-3">
                <div class="col-sm-4 col-form-label">
                    CPI Calculation Method
                </div>
                <div class="col-sm-8">
                    <select
                        v-model="
                            invoicingDetailsComputed.cpi_calculation_method
                        "
                        class="form-select"
                        aria-label="CPI Calculation Method"
                        required
                        :disabled="cpi_calculation_method_disabled"
                        @change="updatePreviewInvoices"
                    >
                        <option
                            v-for="cpi_calculation_method in cpi_calculation_methods"
                            :key="cpi_calculation_method.id"
                            :value="cpi_calculation_method.id"
                        >
                            {{ cpi_calculation_method.display_name }}
                        </option>
                    </select>
                </div>
            </div>
            <div class="row mb-3 border-bottom">
                <div class="col">
                    <BootstrapAlert class="py-2">
                        The CPI percentage for the selected quarter will be
                        fetched from the ABS when an invoice is generated
                    </BootstrapAlert>
                </div>
            </div>
        </div>
        <div
            v-if="show_invoicing_frequency"
            class="row mb-3 pb-3 border-bottom"
        >
            <label for="invoicing_frequency" class="col-form-label col-sm-4"
                >Invoicing Frequency</label
            >
            <div class="col-sm-8">
                <div class="d-flex align-items-center">
                    <div class="pe-3">Once every</div>
                    <div class="pe-3">
                        <input
                            v-if="invoicingDetailsComputed"
                            id="invoicing_once_every"
                            v-model="
                                invoicingDetailsComputed.invoicing_once_every
                            "
                            type="number"
                            min="1"
                            max="6"
                            step="1"
                            class="form-control"
                            :data-previous-value="
                                invoicing_once_every_previous_value
                            "
                            :readonly="invoicing_once_every_readonly"
                            required
                            @change="updateInvoicingOnceEvery"
                        />
                    </div>
                    <div class="">
                        <select
                            v-model="
                                invoicingDetailsComputed.invoicing_repetition_type
                            "
                            class="form-select"
                            aria-label="Repetition Type"
                            :disabled="invoicing_repetition_type_disabled"
                            required
                            @change="onInvoicingRepetitionTypeChange"
                        >
                            <option
                                v-for="repetition_type in filtered_repetition_types"
                                :key="repetition_type.key"
                                :value="repetition_type.id"
                            >
                                {{ repetition_type.display_name }}
                            </option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="show_invoicing_quarters" class="row mb-3 pb-3 border-bottom">
            <label for="invoicing_frequency" class="col-form-label col-sm-4"
                >Invoicing Quarters</label
            >
            <div class="col-sm-8">
                <div class="d-flex align-items-center">
                    <div class="pe-3">
                        <select
                            v-model="
                                invoicingDetailsComputed.invoicing_quarters_start_month
                            "
                            :disabled="invoicing_quarters_start_month_disabled"
                            class="form-select"
                            @change="updatePreviewInvoices"
                        >
                            <option
                                :value="1"
                                :selected="
                                    invoicingDetailsComputed.invoicing_quarters_start_month ==
                                    1
                                "
                            >
                                NOV-JAN, FEB-APR, MAY-JUL, AUG-OCT
                            </option>
                            <option
                                :value="2"
                                :selected="
                                    invoicingDetailsComputed.invoicing_quarters_start_month ==
                                    2
                                "
                            >
                                DEC-FEB, MAR-MAY, JUN-AUG, SEP-NOV
                            </option>
                            <option
                                :value="3"
                                :selected="
                                    invoicingDetailsComputed.invoicing_quarters_start_month ==
                                    3
                                "
                            >
                                JAN-MAR, APR-JUN, JUL-SEP, OCT-DEC
                            </option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="show_percentage_of_gross_turnover_arrears">
            <PercentageTurnoverArrears
                v-if="invoicingDetailsComputed"
                :start-date="startDate"
                :expiry-date="expiryDate"
                :issue-date="issueDate"
                :gross-turnover-percentages="
                    invoicingDetailsComputed.gross_turnover_percentages
                "
                :invoicing-repetition-type="
                    invoicingDetailsComputed.invoicing_repetition_type
                "
                :invoicing-repetition-type-key="
                    invoicingDetailsComputed.invoicing_repetition_type_key
                "
                :proposal-processing-status-id="proposalProcessingStatusId"
                :context="context"
                @update-gross-turnover-percentages="
                    updateGrossTurnoverPercentages
                "
                @on-change-percentage="updatePreviewInvoices"
                @on-change-annual-gross-turnover="updatePreviewInvoices"
                @on-change-quarterly-gross-turnover="updatePreviewInvoices"
                @on-change-monthly-gross-turnover="updatePreviewInvoices"
            />
        </div>
        <div v-if="show_percentage_of_gross_turnover_advance">
            <PercentageTurnoverAdvance
                v-if="invoicingDetailsComputed"
                :start-date="startDate"
                :expiry-date="expiryDate"
                :gross-turnover-percentages="
                    invoicingDetailsComputed.gross_turnover_percentages
                "
                :proposal-processing-status-id="proposalProcessingStatusId"
                :context="context"
                @update-gross-turnover-percentages="
                    updateGrossTurnoverPercentages
                "
                @on-change-percentage="updatePreviewInvoices"
                @on-change-gross-turnover-estimate="updatePreviewInvoices"
                @on-change-gross-turnover-actual="updatePreviewInvoices"
            />
        </div>

        <div v-if="show_fixed_annual_increment">
            <AnnualIncrement
                v-if="invoicingDetailsComputed"
                increment-type="annual_increment_amount"
                :years-array="invoicingDetailsComputed.annual_increment_amounts"
                :approval-duration-years="approvalDurationYears"
                :start-date="startDate"
                :context="context"
                @update-years-array="updateYearsArray"
                @on-change-increment="updatePreviewInvoices"
            />
        </div>
        <div v-if="show_fixed_annual_percentage">
            <AnnualIncrement
                v-if="invoicingDetailsComputed"
                increment-type="annual_increment_percentage"
                :years-array="
                    invoicingDetailsComputed.annual_increment_percentages
                "
                :start-date="startDate"
                :context="context"
                :approval-duration-years="approvalDurationYears"
                @update-years-array="updateYearsArray"
                @on-change-increment="updatePreviewInvoices"
            />
        </div>
        <div
            v-if="show_invoice_previewer"
            class="row mb-3 border-bottom justify-content-center"
        >
            <InvoicePreviewer
                v-if="
                    previewInvoices &&
                    invoicingDetailsComputed &&
                    invoicingDetailsComputed.invoicing_repetition_type
                "
                :preview-invoices="previewInvoices"
                :invoicing-details="invoicingDetailsComputed"
                :start-date="startDate"
                :expiry-date="expiryDate"
                :charge-method-key="invoicingDetailsComputed.charge_method_key"
                :invoicing-repetition-type-key="
                    invoicingDetailsComputed.invoicing_repetition_type_key
                "
                :show-past-invoices="context == 'Proposal'"
                :loading-preview-invoices="loadingPreviewInvoices"
                :context="context"
                @update-default-invoicing-date="updateDefaultInvoicingDate"
            />
        </div>
    </form>
</template>

<script>
import AnnualIncrement from '@/components/common/component_fixed_annual_amount.vue';
import PercentageTurnoverAdvance from '@/components/common/component_percentage_gross_turnover_advance.vue';
import PercentageTurnoverArrears from '@/components/common/component_percentage_gross_turnover_arrears.vue';
import InvoicePreviewer from '@/components/common//invoice_previewer.vue';
import Multiselect from 'vue-multiselect';

import { api_endpoints, constants, helpers, utils } from '@/utils/hooks';

export default {
    name: 'InvoicingDetails',
    components: {
        AnnualIncrement,
        PercentageTurnoverAdvance,
        PercentageTurnoverArrears,
        InvoicePreviewer,
        Multiselect,
    },
    props: {
        context: {
            type: String,
            required: true,
        },
        invoicingDetails: {
            type: Object,
            required: true,
        },
        startDate: {
            type: String,
            required: true,
        },
        expiryDate: {
            type: String,
            required: true,
        },
        issueDate: {
            type: String,
            required: true,
        },
        proposalProcessingStatusId: {
            type: String,
            required: true,
        },
        proposalTypeCode: {
            type: String,
            required: true,
        },
        approvalType: {
            type: String,
            required: true,
        },
    },
    emits: ['updateInvoicingDetails'],
    data: function () {
        return {
            sequentialYearHasPassed: helpers.sequentialYearHasPassed,
            yearsElapsedSinceStartDate: helpers.yearsElapsedSinceStartDate,
            approvalDurationYears: helpers.yearsInDateRange(
                this.startDate,
                this.expiryDate
            ),
            financialYearsIncluded: helpers.financialYearsIncluded(
                this.startDate,
                this.expiryDate
            ),
            charge_methods: [],
            repetition_types: [],
            cpi_calculation_methods: [],
            oracle_codes: [],
            previewInvoices: null,
            loadingPreviewInvoices: false,
            loadingOracleCodes: false,
            invoicing_once_every_previous_value: 1,
        };
    },
    computed: {
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        editingFromProposalPage: function () {
            return this.context === 'Proposal';
        },
        invoicingDetailsComputed: {
            get() {
                return this.invoicingDetails;
            },
            set(value) {
                this.$emit('updateInvoicingDetails', value);
            },
        },
        isMigrationProposal: function () {
            return (
                this.proposalTypeCode == constants.PROPOSAL_TYPE.MIGRATION.code
            );
        },
        show_oracle_code: function () {
            if (
                this.invoicingDetails &&
                this.invoicingDetails.charge_method_key
            )
                if (
                    this.invoicingDetails.charge_method_key !=
                    constants.CHARGE_METHODS.NO_RENT_OR_LICENCE_CHARGE.ID
                )
                    return true;
            return false;
        },
        show_once_off_charge_amount: function () {
            if (
                this.invoicingDetails &&
                this.invoicingDetails.charge_method_key
            )
                if (
                    this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS.ONCE_OFF_CHARGE.ID
                )
                    return true;
            return false;
        },
        show_fixed_annual_increment: function () {
            if (
                this.invoicingDetails &&
                this.invoicingDetails.charge_method_key
            )
                if (
                    this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS
                        .BASE_FEE_PLUS_FIXED_ANNUAL_INCREMENT.ID
                )
                    return true;
            return false;
        },
        show_fixed_annual_percentage: function () {
            if (
                this.invoicingDetails &&
                this.invoicingDetails.charge_method_key
            )
                if (
                    this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS
                        .BASE_FEE_PLUS_FIXED_ANNUAL_PERCENTAGE.ID
                )
                    return true;
            return false;
        },
        show_base_fee: function () {
            if (
                this.show_fixed_annual_increment ||
                this.show_fixed_annual_percentage ||
                (this.invoicingDetails &&
                    this.invoicingDetails.charge_method_key ===
                        constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI.ID) ||
                this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI_CUSTOM.ID
            )
                return true;
            return false;
        },
        show_crown_land_rent_review_interval: function () {
            return this.show_base_fee;
        },
        show_cpi_method: function () {
            if (this.invoicingDetails && this.invoicingDetails.charge_method)
                if (
                    this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI.ID
                )
                    return true;
            return false;
        },
        show_custom_cpi_years: function () {
            if (
                this.invoicingDetails &&
                this.invoicingDetails.charge_method_key
            )
                if (
                    this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI_CUSTOM.ID
                )
                    return true;
            return false;
        },
        show_percentage_of_gross_turnover_advance: function () {
            if (this.invoicingDetails && this.invoicingDetails.charge_method)
                if (
                    this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE.ID
                )
                    return true;
            return false;
        },
        show_percentage_of_gross_turnover_arrears: function () {
            if (this.invoicingDetails && this.invoicingDetails.charge_method)
                if (
                    this.invoicingDetails.charge_method_key ===
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS.ID
                )
                    return true;
            return false;
        },
        show_crown_land_rent_review_date: function () {
            return this.show_base_fee;
        },
        crown_land_rent_review_readonly: function () {
            return this.context != 'Proposal';
        },
        invoicing_once_every_readonly: function () {
            return (
                [1, 2].includes(
                    this.invoicingDetailsComputed.invoicing_repetition_type
                ) ||
                [
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS.ID,
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE.ID,
                ].includes(this.invoicingDetailsComputed.charge_method_key) ||
                this.context != 'Proposal'
            );
        },
        cpi_calculation_method_disabled: function () {
            return this.context != 'Proposal';
        },
        invoicing_repetition_type_disabled: function () {
            return this.context != 'Proposal';
        },
        invoicing_quarters_start_month_disabled: function () {
            return this.context != 'Proposal';
        },
        invoicing_schedule_disabled: function () {
            return this.context != 'Proposal';
        },
        show_invoicing_frequency: function () {
            if (this.invoicingDetails) {
                if (
                    [
                        constants.CHARGE_METHODS
                            .BASE_FEE_PLUS_FIXED_ANNUAL_INCREMENT.ID,
                        constants.CHARGE_METHODS
                            .BASE_FEE_PLUS_FIXED_ANNUAL_PERCENTAGE.ID,
                        constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI.ID,
                        constants.CHARGE_METHODS.BASE_FEE_PLUS_ANNUAL_CPI_CUSTOM
                            .ID,
                        constants.CHARGE_METHODS
                            .PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS.ID,
                        constants.CHARGE_METHODS
                            .PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE.ID,
                    ].includes(this.invoicingDetails.charge_method_key)
                )
                    return true;
                return false;
            }
            return false;
        },
        show_invoice_previewer: function () {
            return this.show_invoicing_frequency;
        },
        show_invoicing_quarters: function () {
            return (
                (this.invoicingDetails.charge_method_key ==
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS.ID ||
                    this.invoicingDetails.charge_method_key ==
                        constants.CHARGE_METHODS
                            .PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE.ID) &&
                this.show_invoicing_frequency &&
                this.invoicingDetailsComputed.invoicing_repetition_type_key ==
                    constants.INVOICING_REPETITON_TYPES.QUARTERLY.ID
            );
        },
        show_month_of_year_to_invoice: function () {
            return (
                1 == this.invoicingDetailsComputed.invoicing_repetition_type &&
                this.show_invoicing_frequency
            );
        },
        filtered_repetition_types: function () {
            // Don't show annual invoicing option for gross turnover charge method
            if (this.invoicingDetails) {
                if (
                    this.invoicingDetails.charge_method_key ==
                        constants.CHARGE_METHODS
                            .PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS.ID ||
                    this.invoicingDetails.charge_method_key ==
                        constants.CHARGE_METHODS
                            .PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE.ID
                ) {
                    return this.repetition_types.filter(
                        (repetition_type) =>
                            repetition_type.key !=
                            constants.INVOICING_REPETITON_TYPES.ANNUALLY.ID
                    );
                }
            }
            return this.repetition_types;
        },
    },
    created: async function () {
        await this.fetchChargeMethods();
        this.fetchRepetitionTypes();
        this.fetchCPICalculationMethods();
        this.fetchOracleCodes();
        if (!this.invoicingDetailsComputed.invoicing_quarters_start_month) {
            // 1 = January [JAN, APR, JUL, OCT], 2 = February [FEB, MAY, AUG, NOV], 3 = March [MAR, JUN, SEP, DEC]
            this.invoicingDetailsComputed.invoicing_quarters_start_month = 3;
        }
        this.invoicing_once_every_previous_value =
            this.invoicingDetailsComputed.invoicing_once_every;
        this.invoicingDetailsComputed.context = this.context;
    },
    mounted: function () {
        this.$nextTick(function () {
            this.invoicingDetailsComputed = {
                ...this.invoicingDetailsComputed,
                custom_cpi_years: this.getCustomCPIYears(),
            };
        });
    },
    methods: {
        getCustomCPIYears: function () {
            const rows = [];
            let periodStartDate = moment(this.startDate);
            for (let i = 0; i < this.approvalDurationYears; i++) {
                let hasPassed = periodStartDate.isSameOrBefore(moment());
                if (!this.invoicingDetailsComputed.custom_cpi_years[i]) {
                    rows.push({
                        year: i + 1,
                        label: '',
                        percentage: null,
                        has_passed: hasPassed,
                    });
                } else {
                    rows.push(
                        this.invoicingDetailsComputed.custom_cpi_years[i]
                    );
                }
                periodStartDate = periodStartDate.add(1, 'year');
            }
            return rows;
        },
        customCPIYearReadonly: function (year) {
            return (
                // No need for back dated custom cpi year information for migrations
                // as invoices are not generated for backdated periods
                (this.isMigrationProposal && year.has_passed) ||
                // When editing from the approval page and not a migration proposal and the year has passed
                // In this case the custom cpi should have already been entered from the proposal page or
                // by the finanace officer aftering getting reminders that an issue date was approaching
                (!this.editingFromProposalPage &&
                    !this.isMigrationProposal &&
                    year.has_passed)
            );
        },
        onChargeMethodChange: function (charge_method) {
            this.invoicingDetailsComputed.charge_method_key = charge_method.key;
            if (
                [
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS.ID,
                    constants.CHARGE_METHODS
                        .PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE.ID,
                ].includes(this.invoicingDetailsComputed.charge_method_key)
            ) {
                this.invoicingDetailsComputed.invoicing_repetition_type = 2;
            } else {
                this.invoicingDetailsComputed.invoicing_repetition_type = 1;
            }
            this.updatePreviewInvoices();
        },
        onInvoicingRepetitionTypeChange: function (event) {
            if (['1', '2'].includes(event.target.value)) {
                this.invoicingDetailsComputed.invoicing_once_every = 1;
            }
            this.updatePreviewInvoices();
        },
        updateInvoicingRepetitionTypeKey: function (invoicing_repetition_type) {
            this.invoicingDetailsComputed = {
                ...this.invoicingDetailsComputed,
                invoicing_repetition_type_key: this.repetition_types.find(
                    (x) => x.id == invoicing_repetition_type
                ).key,
            };
        },
        updateYearsArray: function (incrementType, years_array) {
            if ('annual_increment_amount' == incrementType) {
                this.invoicingDetailsComputed = {
                    ...this.invoicingDetailsComputed,
                    annual_increment_amounts: years_array,
                };
            } else {
                this.invoicingDetailsComputed = {
                    ...this.invoicingDetailsComputed,
                    annual_increment_percentages: years_array,
                };
            }
        },
        updateGrossTurnoverPercentages: function (gross_turnover_percentages) {
            this.invoicingDetailsComputed = {
                ...this.invoicingDetailsComputed,
                gross_turnover_percentages: gross_turnover_percentages,
            };
        },
        updateDefaultInvoicingDate: function (firstIssueDate) {
            if (!this.invoicingDetailsComputed.invoicing_day_of_month) {
                let invoicing_day_of_month = firstIssueDate.date();
                this.invoicingDetailsComputed = {
                    ...this.invoicingDetailsComputed,
                    invoicing_day_of_month: invoicing_day_of_month,
                };
            }
            if (
                this.invoicingDetailsComputed.invoicing_repetition_type == 1 &&
                !this.invoicingDetailsComputed.invoicing_month_of_year
            ) {
                let invoicing_month_of_year = firstIssueDate.month() + 1;
                this.invoicingDetailsComputed = {
                    ...this.invoicingDetailsComputed,
                    invoicing_month_of_year: invoicing_month_of_year,
                };
            }
        },
        chargeMethodDisabled: function (charge_method) {
            return (
                (this.context == 'Approval' &&
                    !(
                        charge_method.id ==
                        this.invoicingDetailsComputed.charge_method
                    )) ||
                ([
                    constants.CHARGE_METHODS
                        .BASE_FEE_PLUS_FIXED_ANNUAL_INCREMENT.ID,
                    constants.CHARGE_METHODS
                        .BASE_FEE_PLUS_FIXED_ANNUAL_PERCENTAGE.ID,
                ].includes(charge_method.key) &&
                    // The approval runs for less than a full year
                    this.approvalDurationYears - 1 == 0)
            );
        },
        fetchChargeMethods: async function () {
            let vm = this;
            try {
                const res = await fetch(api_endpoints.charge_methods);
                if (!res.ok) throw new Error(res.statusText); // 400s or 500s error
                let charge_methods = await res.json();
                vm.charge_methods = charge_methods;
                // This has to happen here as the show_invoice_previewer computed method depends on the charge_method key
                this.fetchPreviewInvoices();
            } catch (err) {
                console.error({ err });
            }
        },
        fetchRepetitionTypes: async function () {
            let vm = this;
            try {
                const res = await fetch(api_endpoints.repetition_types);
                if (!res.ok) throw new Error(res.statusText); // 400s or 500s error
                let repetition_types = await res.json();
                vm.repetition_types = repetition_types;
                vm.$nextTick(function () {
                    if (!vm.invoicingDetailsComputed.review_once_every) {
                        vm.invoicingDetailsComputed.review_once_every = 5;
                    }
                    if (!vm.invoicingDetailsComputed.invoicing_once_every) {
                        vm.invoicingDetailsComputed.invoicing_once_every = 1;
                    }
                    if (!vm.invoicingDetailsComputed.review_repetition_type) {
                        vm.invoicingDetailsComputed.review_repetition_type = 1;
                    }
                    if (
                        constants.CHARGE_METHODS
                            .PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS.ID !=
                            this.invoicingDetailsComputed.charge_method_key &&
                        !vm.invoicingDetailsComputed.invoicing_repetition_type
                    ) {
                        vm.invoicingDetailsComputed.invoicing_repetition_type = 1;
                    }
                });
            } catch (err) {
                console.error({ err });
            }
        },
        fetchCPICalculationMethods: async function () {
            let vm = this;
            try {
                const res = await fetch(
                    api_endpoints.cpi_calculation_methods + 'no-pagination/'
                );
                if (!res.ok) throw new Error(res.statusText); // 400s or 500s error
                let cpi_calculation_methods = await res.json();
                vm.cpi_calculation_methods = cpi_calculation_methods;
                if (
                    vm.invoicingDetailsComputed.cpi_calculation_method == null
                ) {
                    vm.invoicingDetailsComputed.cpi_calculation_method =
                        cpi_calculation_methods.find(
                            (x) => x.name == 'latest_sep_qtr'
                        ).id;
                }
            } catch (err) {
                console.error({ err });
            }
        },
        fetchPreviewInvoices: async function () {
            if (!this.show_invoice_previewer) {
                return;
            }
            this.previewInvoices = await utils.fetchUrl(
                api_endpoints.invoicing_details +
                    `${this.invoicingDetails.id}/preview_invoices/`
            );
        },
        saveInvoicingDetails: async function () {
            const requestOptions = {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.invoicingDetailsComputed),
            };
            await utils.fetchUrl(
                api_endpoints.invoicing_details +
                    `${this.invoicingDetails.id}/`,
                requestOptions
            );
        },
        updateInvoicingOnceEvery: function () {
            var changing_to;

            if (this.invoicingDetailsComputed.invoicing_once_every == 5) {
                if (this.invoicing_once_every_previous_value > 5) {
                    this.invoicingDetailsComputed.invoicing_once_every = 4;
                    changing_to = 4;
                } else {
                    this.invoicingDetailsComputed.invoicing_once_every = 6;
                    changing_to = 6;
                }
                this.invoicing_once_every_previous_value =
                    this.invoicingDetailsComputed.invoicing_once_every;
                swal.fire({
                    title: `The system does not support invoicing every 5 months. Changing value to ${changing_to} months.`,
                    icon: 'info',
                });
            }
            this.updatePreviewInvoices();
        },
        updatePreviewInvoices: async function () {
            this.updateInvoicingRepetitionTypeKey(
                this.invoicingDetailsComputed.invoicing_repetition_type
            );
            const requestOptions = {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.invoicingDetailsComputed),
            };
            this.loadingPreviewInvoices = true;
            this.previewInvoices = await utils.fetchUrl(
                api_endpoints.invoicing_details +
                    `${this.invoicingDetails.id}/update_and_preview_invoices/`,
                requestOptions
            );
            this.loadingPreviewInvoices = false;
        },
        fetchOracleCodes: async function () {
            let vm = this;
            try {
                vm.loadingOracleCodes = true;
                const res = await fetch(
                    api_endpoints.oracle_codes + 'key-value-list/'
                );
                if (!res.ok) throw new Error(res.statusText); // 400s or 500s error
                let oracle_codes = await res.json();
                vm.oracle_codes = oracle_codes;
                vm.loadingOracleCodes = false;
            } catch (err) {
                console.error({ err });
            }
        },
    },
};
</script>
<style scoped>
.invalid-charge-method {
    margin-left: -17px;
}
</style>
