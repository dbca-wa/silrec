<template>
    <div class="row mb-3 border-bottom">
        <div class="col">
            <template v-for="item in yearsArrayComputed" :key="item.key">
                <div class="card mb-2">
                    <div class="card-body py-1">
                        <div class="div d-flex align-items-center">
                            <label class="col-sm-4 col-form-label"
                                >Increment
                            </label>
                            <div class="pe-3">
                                After
                                <div
                                    class="badge bg-primary rounded-pill year-and-ordinal text-center mx-1"
                                >
                                    {{ ordinalSuffixOf(item.year) }} Year
                                </div>
                                increase by
                            </div>
                            <div class="pe-3">
                                <div
                                    v-if="
                                        incrementType ===
                                        'annual_increment_amount'
                                    "
                                    class="input-group"
                                >
                                    <span class="input-group-text">$</span>
                                    <input
                                        v-model="item.increment_amount"
                                        type="number"
                                        :min="0"
                                        :max="100000000"
                                        :step="100"
                                        class="form-control form-control-sm"
                                        :readonly="
                                            !editingFromProposalPage &&
                                            yearHasPassed(item.year)
                                        "
                                        required
                                        @change="$emit('onChangeIncrement')"
                                        @onkeyup="$emit('onChangeIncrement')"
                                    />
                                    <span class="input-group-text">AUD</span>
                                </div>
                                <div
                                    v-else-if="
                                        incrementType ===
                                        'annual_increment_percentage'
                                    "
                                    class="input-group"
                                >
                                    <input
                                        v-model="item.increment_percentage"
                                        type="number"
                                        :min="0"
                                        :max="100"
                                        :step="0.1"
                                        class="form-control form-control-sm"
                                        required
                                        :readonly="
                                            !editingFromProposalPage &&
                                            yearHasPassed(item.year)
                                        "
                                        @change="$emit('onChangeIncrement')"
                                        @onkeyup="$emit('onChangeIncrement')"
                                    />
                                    <span class="input-group-text">%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </template>
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import { helpers } from '@/utils/hooks';

export default {
    name: 'AnnualAmount',
    props: {
        incrementType: {
            type: String,
            required: true,
        },
        yearsArray: {
            type: Array,
            required: true,
        },
        stepYear: {
            type: Number,
            default: 1,
        },
        minIncrement: {
            type: Number,
            default: 1,
        },
        approvalDurationYears: {
            type: Number,
            required: true,
        },
        startDate: {
            type: String,
            required: true,
        },
        context: {
            type: String,
            required: true,
        },
    },
    emits: ['updateYearsArray', 'onChangeIncrement'],
    data: function () {
        return {
            yearsElapsedSinceStartDate: helpers.yearsElapsedSinceStartDate,
            ordinalSuffixOf: helpers.ordinalSuffixOf,
        };
    },
    computed: {
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        yearsArrayComputed: {
            get() {
                return this.yearsArray;
            },
            set(value) {
                this.$emit('updateYearsArray', this.incrementType, value);
            },
        },
        valueTitle: function () {
            if (this.incrementType === 'annual_increment_amount')
                return 'Amount ($AUD)';

            return 'Percentage (%)';
        },
        stepIncrement: function () {
            if (this.incrementType === 'annual_increment_amount') return 100;
            return 0.1;
        },
        editingFromProposalPage: function () {
            return this.context === 'Proposal';
        },
    },
    mounted: function () {
        for (
            let i = this.yearsArrayComputed.length;
            i < this.approvalDurationYears - 1;
            i++
        ) {
            if (!this.yearsArrayComputed[i]) {
                this.yearsArrayComputed.push({
                    key: uuid(),
                    year: i + 1,
                    [this.getKeyName()]: 0.0,
                });
            }
        }
    },
    methods: {
        getKeyName: function () {
            if (this.incrementType === 'annual_increment_amount')
                return 'increment_amount';
            return 'increment_percentage';
        },
        yearHasPassed: function (yearIndex) {
            var startDate = new Date(this.startDate);
            var yearStartDate = new Date(
                startDate.setFullYear(startDate.getFullYear() + yearIndex)
            );
            if (yearStartDate < new Date()) {
                return true;
            }
            return false;
        },
    },
};
</script>
<style scoped>
.year-and-ordinal {
    display: inline-block;
    width: 90px;
    font-size: 0.9em;
}
</style>
