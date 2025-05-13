<template>
    <div class="row mb-3">
        <div class="col">
            <div v-if="editingFromProposalPage">
                <BootstrapAlert>
                    Enter the percentage of gross turnover to charge for each
                    financial year
                </BootstrapAlert>
            </div>
            <template
                v-for="year in grossTurnoverPercentagesComputed"
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
                                        :disabled="
                                            year.gross_turnover ||
                                            hasGrossTurnoverEntries(year) ||
                                            year.locked
                                        "
                                        @change="$emit('onChangePercentage')"
                                        @keyup="$emit('onChangePercentage')"
                                    />
                                    <span class="input-group-text">%</span>
                                </div>
                            </label>
                            <div v-if="!editingFromProposalPage" class="pe-3">
                                Gross Turnover
                            </div>
                            <div
                                v-if="!editingFromProposalPage"
                                class="col-sm-4"
                            >
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input
                                        v-model="year.gross_turnover"
                                        type="number"
                                        class="form-control"
                                        max="1000000000000"
                                        :disabled="
                                            year.locked ||
                                            !financialYearHasPassed(
                                                year.financial_year
                                            ) ||
                                            (!yearIsBeforeIssueDate(year) &&
                                                !allQuartersLocked(year))
                                        "
                                        :placeholder="
                                            !yearIsBeforeIssueDate(year) &&
                                            !allQuartersLocked(year)
                                                ? 'Enter ' +
                                                  repetitionTypePlural
                                                : ''
                                        "
                                        @change="
                                            grossAnnualTurnoverChanged(
                                                $event,
                                                year
                                            )
                                        "
                                        @keyup="
                                            grossAnnualTurnoverChanged(
                                                $event,
                                                year
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
                            (!editingFromProposalPage ||
                                !financialYearHasPassed(year.financial_year)) &&
                            !year.locked &&
                            year.gross_turnover &&
                            year.discrepency &&
                            year.discrepency != 0 &&
                            year.discrepency_invoice_amount != 0
                        "
                        class="card-body"
                    >
                        <BootstrapAlert>
                            <template
                                v-if="year.discrepency_invoice_amount > 0"
                            >
                                <div v-if="!yearIsBeforeIssueDate(year)">
                                    The gross annual turnover entered is greater
                                    than the sum of the four quarters.
                                </div>
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
                                <div v-if="!yearIsBeforeIssueDate(year)">
                                    The gross annual turnover entered is less
                                    than the sum of the four quarters.
                                </div>
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
                    <div
                        v-if="
                            !editingFromProposalPage &&
                            invoicingReptitionQuarterly &&
                            year.quarters.length > 0
                        "
                        class="card-body py-3"
                    >
                        <div
                            v-for="quarter in year.quarters"
                            :key="year.year + quarter.quarter"
                            class="div d-flex align-items-center pb-1"
                        >
                            <div class="col-sm-5">&nbsp;</div>
                            <div class="pe-3 quarter">
                                <div class="input-group">
                                    <input
                                        type="text"
                                        readonly
                                        class="form-control form-control-quarter"
                                        :value="`Q${
                                            quarter.quarter
                                        } ${getFinancialQuarterLabel(
                                            quarter.quarter
                                        )}`"
                                    />
                                </div>
                            </div>
                            <div class="pe-3">Gross Turnover</div>
                            <div class="col-sm-3">
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input
                                        v-model="quarter.gross_turnover"
                                        type="number"
                                        class="form-control"
                                        :readonly="
                                            grossQuarterlyTurnoverReadonly(
                                                year.financial_year,
                                                quarter.quarter
                                            ) || quarter.locked
                                        "
                                        @change="
                                            grossQuarterlyTurnoverChanged(
                                                $event,
                                                quarter
                                            )
                                        "
                                        @keyup="
                                            grossQuarterlyTurnoverChanged(
                                                $event,
                                                quarter
                                            )
                                        "
                                    />
                                    <span class="input-group-text">AUD</span>
                                </div>
                            </div>
                        </div>
                        <div
                            v-if="quartersTotal(year) > 0"
                            class="div d-flex align-items-center pb-1 pt-2"
                        >
                            <div class="col-sm-4 pe-3">&nbsp;</div>
                            <div class="pe-3 quarter">
                                <div class="input-group"></div>
                            </div>
                            <div class="pe-3">Quarters Total&nbsp;&nbsp;</div>
                            <div class="col-sm-3">
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input
                                        type="text"
                                        readonly
                                        class="form-control"
                                        :value="quartersTotal(year)"
                                    />
                                    <span class="input-group-text">AUD</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div
                        v-if="
                            !editingFromProposalPage &&
                            !invoicingReptitionQuarterly &&
                            year.months.length > 0
                        "
                        class="card-body py-3"
                    >
                        <div
                            v-for="month in year.months"
                            :key="month.year + month.month"
                            class="div d-flex align-items-center pb-1"
                        >
                            <div class="col-sm-5">&nbsp;</div>
                            <div class="pe-3 quarter">
                                <div class="input-group">
                                    <input
                                        type="text"
                                        readonly
                                        class="form-control form-control-quarter"
                                        :value="`${month.label}`"
                                    />
                                </div>
                            </div>
                            <div class="pe-3">Gross Turnover</div>
                            <div class="col-sm-3">
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input
                                        v-model="month.gross_turnover"
                                        type="number"
                                        class="form-control"
                                        :readonly="
                                            grossMonthlyTurnoverReadonly(
                                                month.year,
                                                month.month
                                            ) || month.locked
                                        "
                                        @change="
                                            grossMonthlyTurnoverChanged(
                                                $event,
                                                month
                                            )
                                        "
                                        @keyup="
                                            grossMonthlyTurnoverChanged(
                                                $event,
                                                month
                                            )
                                        "
                                    />
                                    <span class="input-group-text">AUD</span>
                                </div>
                            </div>
                        </div>
                        <div
                            v-if="monthsTotal(year) > 0"
                            class="div d-flex align-items-center pb-1 pt-2"
                        >
                            <div class="col-sm-4 pe-3">&nbsp;</div>
                            <div class="pe-3 quarter">
                                <div class="input-group"></div>
                            </div>
                            <div class="pe-3">Months Total&nbsp;&nbsp;</div>
                            <div class="col-sm-3">
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input
                                        type="text"
                                        readonly
                                        class="form-control"
                                        :value="monthsTotal(year)"
                                    />
                                    <span class="input-group-text">AUD</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </template>
        </div>
    </div>
    <div class="row mb-3 pb-3 border-bottom">
        <div class="col">
            <BootstrapAlert v-if="editingFromProposalPage" class="py-2 mb-0">
                The system will generate compliances to ask for an audited
                financial statement for each
                {{
                    invoicingRepetitionTypeKey ==
                    constants.INVOICING_REPETITON_TYPES.QUARTERLY.ID
                        ? 'quarter'
                        : 'month'
                }}
                and financial year
            </BootstrapAlert>
        </div>
    </div>
</template>

<script>
import currency from 'currency.js';
import { constants, helpers } from '@/utils/hooks';

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
        issueDate: {
            type: String,
            required: true,
        },
        grossTurnoverPercentages: {
            type: Array,
            required: true,
        },
        invoicingRepetitionType: {
            type: Number,
            required: true,
        },
        invoicingRepetitionTypeKey: {
            type: String,
            required: false,
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
        'onChangeAnnualGrossTurnover',
        'onChangeQuarterlyGrossTurnover',
        'onChangeMonthlyGrossTurnover',
    ],
    data: function () {
        return {
            originalAnnualTurnover: null,
            financialYearHasPassed: helpers.financialYearHasPassed,
            getFinancialQuarterLabel: helpers.getFinancialQuarterLabel,
            helpers: helpers,
            currency: currency,
            constants: constants,
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
        invoicingReptitionQuarterly: function () {
            return (
                this.invoicingRepetitionTypeKey ==
                constants.INVOICING_REPETITON_TYPES.QUARTERLY.ID
            );
        },
        editingFromProposalPage: function () {
            return this.context == 'Proposal';
        },
        repetitionTypePlural: function () {
            return this.invoicingRepetitionTypeKey ==
                constants.INVOICING_REPETITON_TYPES.QUARTERLY.ID
                ? 'quarters'
                : 'months';
        },
    },
    watch: {
        invoicingRepetitionType: function (newVal) {
            if (newVal) {
                this.populateFinancialYearsArray(
                    helpers.financialYearsIncluded(
                        this.startDate,
                        this.expiryDate
                    )
                );
            }
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
            return (
                !this.financialYearHasPassed(
                    grossTurnoverPercentage.financial_year
                ) ||
                (!this.editingFromProposalPage &&
                    !this.allQuartersEntered(grossTurnoverPercentage))
            );
        },
        grossQuarterlyTurnoverReadonly: function (
            financialYear,
            financialQuarter
        ) {
            // Gross turnover is readonly if the financial quarter hasn't passed
            return !this.helpers.financialQuarterHasPassed(
                financialYear,
                financialQuarter
            );
        },
        grossMonthlyTurnoverReadonly: function (year, month) {
            // Gross turnover is readonly if the month hasn't passed
            return !this.helpers.monthHasPassed(year, month);
        },
        allQuartersEntered: function (grossTurnoverPercentage) {
            // Returns true if all the quarterly figures have been entered

            for (let i = 0; i < grossTurnoverPercentage.quarters.length; i++) {
                if (
                    grossTurnoverPercentage.quarters[i].gross_turnover ==
                        null ||
                    grossTurnoverPercentage.quarters[i].gross_turnover == ''
                ) {
                    return false;
                }
            }
            return true;
        },
        allQuartersLocked: function (grossTurnoverPercentage) {
            // Returns true if all the quarterly figures have been locked

            for (let i = 0; i < grossTurnoverPercentage.quarters.length; i++) {
                if (grossTurnoverPercentage.quarters[i].locked == false) {
                    return false;
                }
            }
            return true;
        },
        quartersTotal: function (grossTurnoverPercentage) {
            return grossTurnoverPercentage.quarters.reduce(
                (total, quarter) =>
                    total + parseFloat(quarter.gross_turnover || 0),
                0
            );
        },
        monthsTotal: function (grossTurnoverPercentage) {
            return grossTurnoverPercentage.months.reduce(
                (total, month) => total + parseFloat(month.gross_turnover || 0),
                0
            );
        },
        grossAnnualTurnoverChanged: function (event, year) {
            if (!event.target.value) {
                year.gross_turnover = null;
                year.discrepency = null;
                year.discrepency_invoice_amount = null;
                this.$emit('onChangeAnnualGrossTurnover');
                return;
            }
            let total_of_quarters = year.quarters.reduce(
                (total, quarter) =>
                    total + parseFloat(quarter.gross_turnover || 0),
                0
            );
            if (event.target.value != total_of_quarters) {
                year.discrepency = currency(
                    event.target.value - total_of_quarters
                );
                year.discrepency_invoice_amount = currency(
                    (event.target.value * year.percentage) / 100 -
                        (total_of_quarters * year.percentage) / 100
                );
            } else {
                year.discrepency = 0;
                year.discrepency_invoice_amount = 0;
            }
            this.$emit('onChangeAnnualGrossTurnover');
        },
        grossQuarterlyTurnoverChanged: function (event, quarter) {
            if (!event.target.value) {
                quarter.gross_turnover = null;
            }
            this.$emit('onChangeQuarterlyGrossTurnover');
        },
        grossMonthlyTurnoverChanged: function (event, month) {
            if (!event.target.value) {
                month.gross_turnover = null;
            }
            this.$emit('onChangeMonthlyGrossTurnover');
        },
        getPeriods: function (year) {
            if (this.invoicingReptitionQuarterly) {
                return year.quarters;
            }
            return year.months;
        },
        hasGrossTurnoverEntries: function (year) {
            var periods = this.getPeriods(year);
            for (let i = 0; i < periods.length; i++) {
                if (
                    periods[i].gross_turnover != null &&
                    periods[i].gross_turnover != ''
                ) {
                    return true;
                }
            }
            return false;
        },
        hasAllGrossTurnoverEntries: function (year) {
            var periods = this.getPeriods(year);
            for (let i = 0; i < periods.length; i++) {
                if (
                    periods[i].gross_turnover == null ||
                    periods[i].gross_turnover == ''
                ) {
                    return false;
                }
            }
            return true;
        },
        yearIsBeforeIssueDate: function (year) {
            return (
                new Date(year.financial_year.split('-')[1], 5, 30) <
                new Date(this.issueDate)
            );
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
                    };
                    financialYears.push(financialYear);
                }
                if (this.invoicingReptitionQuarterly) {
                    let grossTurnoverPercentage = this
                        .grossTurnoverPercentagesComputed[i]
                        ? this.grossTurnoverPercentagesComputed[i]
                        : financialYear;
                    if (!grossTurnoverPercentage.quarters) {
                        grossTurnoverPercentage.quarters = [];
                    }
                    grossTurnoverPercentage.months = [];
                    for (let j = 0; j < 4; j++) {
                        if (
                            !helpers.financialQuarterIncluded(
                                this.startDate,
                                this.expiryDate,
                                grossTurnoverPercentage.financial_year,
                                j + 1
                            )
                        ) {
                            continue;
                        }
                        if (!grossTurnoverPercentage.quarters[j]) {
                            if (
                                !grossTurnoverPercentage.quarters.find(
                                    (x) => x.quarter == j + 1
                                )
                            ) {
                                grossTurnoverPercentage.quarters.push({
                                    quarter: j + 1,
                                    gross_turnover: null,
                                });
                            }
                        }
                    }
                } else {
                    let financialMonths = helpers.getFinancialMonths(
                        financialYearsIncluded[i]
                    );
                    let grossTurnoverPercentage = this
                        .grossTurnoverPercentagesComputed[i]
                        ? this.grossTurnoverPercentagesComputed[i]
                        : financialYear;
                    if (!grossTurnoverPercentage.months) {
                        grossTurnoverPercentage.months = [];
                    }
                    grossTurnoverPercentage.quarters = [];
                    for (let j = 0; j < financialMonths.length; j++) {
                        let year = financialMonths[j].year;
                        let month = financialMonths[j].month;
                        let monthStart = moment(
                            `${year}-${month}-01`,
                            'YYYY-MM-DD'
                        );
                        let monthEnd = moment(monthStart).endOf('month');
                        if (
                            !helpers.datesOverlap(
                                this.startDate,
                                this.expiryDate,
                                monthStart,
                                monthEnd
                            )
                        ) {
                            continue;
                        }
                        if (
                            !grossTurnoverPercentage.months.find(
                                (x) => x.month == month && x.year == year
                            )
                        ) {
                            grossTurnoverPercentage.months.push({
                                year: year,
                                month: month,
                                label: financialMonths[j].label,
                                gross_turnover: null,
                            });
                        }
                    }
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

<style scoped>
.quarter {
    width: 142px;
}
.form-control-quarter {
    width: 50px;
}
</style>
