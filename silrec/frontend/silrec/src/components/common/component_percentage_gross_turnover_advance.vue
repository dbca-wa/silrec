<template>
    <!-- <pre>{{ $filters.pretty(grossTurnoverPercentagesComputed) }}</pre> -->
    <div class="row mb-3 pb-3 border-bottom">
        <div class="col">
            <BootstrapAlert v-if="editingFromProposalPage()" class="py-2 mb-0">
                Gross turnover estimates for future years do not have to be
                entered now however they must be entered by the first issue date
                that relates to that financial year.
            </BootstrapAlert>
        </div>
    </div>
    <div class="row mb-3">
        <div class="col">
            <template
                v-for="(year, index) in grossTurnoverPercentagesComputed"
                :key="year.year"
            >
                <div class="card mb-2">
                    <div class="card-body py-3 border-bottom">
                        <div class="div d-flex align-items-center">
                            <div class="col-sm-4 pe-3">
                                <div class="input-group">
                                    <span class="input-group-text"
                                        >Financial Year</span
                                    >
                                    <input
                                        v-model="year.financial_year"
                                        type="text"
                                        readonly
                                        class="form-control form-control-year"
                                    />
                                </div>
                            </div>
                            <label class="col-sm-2 pe-3">
                                <div class="input-group">
                                    <input
                                        v-model="year.percentage"
                                        step="0.1"
                                        min="0"
                                        max="100"
                                        type="number"
                                        class="form-control"
                                        :readonly="
                                            !editingFromProposalPage() &&
                                            (year.estimated_gross_turnover ||
                                                year.gross_turnover ||
                                                year.estimate_locked ||
                                                year.locked)
                                        "
                                        required
                                        @change="$emit('onChangePercentage')"
                                        @keyup="$emit('onChangePercentage')"
                                    />
                                    <span class="input-group-text">%</span>
                                </div>
                            </label>
                        </div>
                    </div>
                    <div class="card-body py-3">
                        <div class="div d-flex align-items-center">
                            <div class="pe-3">Gross Turnover Estimate</div>
                            <div class="col-sm-4 pe-3">
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input
                                        v-model="year.estimated_gross_turnover"
                                        type="number"
                                        class="form-control"
                                        max="1000000000000"
                                        :readonly="year.estimate_locked"
                                        :required="
                                            (editingFromProposalPage() &&
                                                financialYearHasPassed(
                                                    year.financial_year
                                                )) ||
                                            financialYearHasStarted(
                                                year.financial_year
                                            )
                                        "
                                        @change="
                                            grossAnnualTurnoverEstimateChanged(
                                                $event,
                                                year,
                                                index
                                            )
                                        "
                                        @keyup="
                                            grossAnnualTurnoverEstimateChanged(
                                                $event,
                                                year,
                                                index
                                            )
                                        "
                                    />
                                    <span class="input-group-text">AUD</span>
                                </div>
                            </div>
                            <div v-if="context == 'Approval'" class="pe-4">
                                Gross Turnover Actual
                            </div>
                            <div v-if="context == 'Approval'" class="col-sm-4">
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input
                                        v-model="year.gross_turnover"
                                        type="number"
                                        class="form-control"
                                        max="1000000000000"
                                        :readonly="
                                            !financialYearHasPassed(
                                                year.financial_year
                                            ) || year.locked
                                        "
                                        @change="
                                            grossAnnualTurnoverChanged(
                                                $event,
                                                year,
                                                index
                                            )
                                        "
                                        @keyup="
                                            grossAnnualTurnoverChanged(
                                                $event,
                                                year,
                                                index
                                            )
                                        "
                                    />
                                    <span class="input-group-text">AUD</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div
                        v-if="
                            !year.locked &&
                            year.estimated_gross_turnover &&
                            year.gross_turnover &&
                            year.discrepency &&
                            year.discrepency != 0
                        "
                        class="card-body"
                    >
                        <BootstrapAlert>
                            <template
                                v-if="year.discrepency_invoice_amount > 0"
                            >
                                The actual gross annual turnover entered is
                                greater than the estimate for this financial
                                year.<br />
                                When you complete editing, the system will
                                generate a charge invoice record for
                                <strong
                                    >${{
                                        currency(
                                            year.discrepency_invoice_amount
                                        )
                                    }}</strong
                                >
                            </template>
                            <template
                                v-else-if="year.discrepency_invoice_amount < 0"
                            >
                                The actual gross annual turnover entered is less
                                than the estimate for this financial year.<br />
                                When you complete editing, the system will
                                generate a refund invoice record for
                                <strong
                                    >${{
                                        currency(
                                            Math.abs(
                                                year.discrepency_invoice_amount
                                            )
                                        )
                                    }}</strong
                                >
                            </template>
                        </BootstrapAlert>
                    </div>
                </div>
            </template>
        </div>
    </div>
    <div class="row mb-3 pb-3 border-bottom">
        <div class="col">
            <BootstrapAlert v-if="context == 'Proposal'" class="py-2 mb-0">
                The system will generate compliances to ask for an audited
                financial statement for each financial year
            </BootstrapAlert>
        </div>
    </div>
</template>

<script>
import currency from 'currency.js';
import { helpers } from '@/utils/hooks';

export default {
    name: 'PercentageTurnover',
    props: {
        startDate: {
            type: String,
            required: true,
        },
        expiryDate: {
            type: String,
            required: true,
        },
        grossTurnoverPercentages: {
            type: Array,
            required: true,
        },
        proposalProcessingStatusId: {
            type: String,
            required: true,
        },
        context: {
            type: String,
            required: true,
        },
    },
    emits: [
        'updateGrossTurnoverPercentages',
        'onChangePercentage',
        'onChangeGrossTurnoverEstimate',
        'onChangeGrossTurnoverActual',
    ],
    data: function () {
        return {
            originalAnnualTurnover: null,
            financialYearHasPassed: helpers.financialYearHasPassed,
            financialYearHasStarted: helpers.financialYearHasStarted,
            getFinancialQuarterLabel: helpers.getFinancialQuarterLabel,
            helpers: helpers,
            currency: currency,
        };
    },
    computed: {
        grossTurnoverPercentagesComputed: {
            get: function () {
                return this.grossTurnoverPercentages;
            },
            set: function (value) {
                this.$emit('updateGrossTurnoverPercentages', value);
            },
        },
    },
    created: function () {
        const financialYearsIncluded = helpers.financialYearsIncluded(
            this.startDate,
            this.expiryDate
        );
        this.populateFinancialYearsArray(financialYearsIncluded);
    },
    methods: {
        grossAnnualTurnoverReadonly: function (grossTurnoverPercentage) {
            // Gross turnover is readonly if the financial year hasn't passed
            // or if the proposal is being edited from the proposal details page
            return !this.financialYearHasPassed(
                grossTurnoverPercentage.financial_year
            );
        },
        editingFromProposalPage: function () {
            return this.context == 'Proposal';
        },
        hasGrossTurnoverEntry: function (year) {
            return year.gross_turnover != null && year.gross_turnover != '';
        },
        grossAnnualTurnoverEstimateChanged: function (event, year) {
            if (!event.target.value) {
                year.estimated_gross_turnover = null;
            }
            this.$emit(
                'onChangeGrossTurnoverEstimate',
                year.estimated_gross_turnover
            );
        },
        grossAnnualTurnoverChanged: function (event, year, index) {
            if (!event.target.value) {
                year.gross_turnover = null;
                year.discrepency = null;
                year.discrepency_invoice_amount = null;
                this.$emit('onChangeGrossTurnoverActual', year.gross_turnover);
                return;
            }
            if (
                this.grossTurnoverPercentagesComputed[index + 1] &&
                !this.financialYearHasPassed(
                    this.grossTurnoverPercentagesComputed[index + 1]
                        .financial_year
                )
            ) {
                this.grossTurnoverPercentagesComputed[
                    index + 1
                ].estimated_gross_turnover = year.gross_turnover;
            }
            const estimated_gross_turnover =
                this.grossTurnoverPercentagesComputed[index]
                    .estimated_gross_turnover;
            if (event.target.value != estimated_gross_turnover) {
                year.discrepency =
                    event.target.value - estimated_gross_turnover;
                year.discrepency_invoice_amount = currency(
                    (event.target.value * year.percentage) / 100 -
                        (estimated_gross_turnover * year.percentage) / 100
                );
            } else {
                year.discrepency = 0;
                year.discrepency_invoice_amount = 0;
            }
            this.$emit('onChangeGrossTurnoverActual', year.gross_turnover);
        },
        populateFinancialYearsArray: function (financialYearsIncluded) {
            var financialYear = null;
            var financialYears = [];

            for (let i = 0; i < financialYearsIncluded.length; i++) {
                let year = financialYearsIncluded[i].split('-')[1];
                if (
                    this.grossTurnoverPercentagesComputed.filter(
                        (x) => x.year == year
                    ).length == 0
                ) {
                    financialYear = {
                        year: year,
                        financial_year: financialYearsIncluded[i],
                        percentage: 0.0,
                        gross_turnover: null,
                        quarters: [],
                        months: [],
                    };
                    financialYears.push(financialYear);
                }
            }
            financialYears = this.grossTurnoverPercentagesComputed.concat(
                ...financialYears
            );
            financialYears.sort((a, b) => a.year - b.year);
            this.grossTurnoverPercentagesComputed = financialYears;
        },
    },
};
</script>
