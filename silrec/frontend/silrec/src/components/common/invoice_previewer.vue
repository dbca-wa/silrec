<template>
    <div class="col m-3 p-3 border rounded">
        <BootstrapAlert
            ><span class="fw-bold">Future Invoice Preview</span>: Based on the
            information entered, the following invoices will be
            generated</BootstrapAlert
        >
        <BootstrapAlert
            v-if="
                chargeMethodKey ==
                constants.CHARGE_METHODS.PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS
                    .ID
            "
            type="warning"
            icon="exclamation-triangle-fill"
            >Additional invoices may be created if there is a discrepency
            between the {{ invoicingRepetitionTypeKey }} and annual
            turnover</BootstrapAlert
        >
        <div v-if="loadingPreviewInvoices" class="text-center">
            <BootstrapSpinner
                class="text-primary invoice-preview-spinner"
                :center-of-screen="false"
            />
        </div>
        <template v-if="previewInvoices && previewInvoices.length">
            <table class="table table-sm table-striped text-left">
                <thead>
                    <tr>
                        <th class="text-left">Number</th>
                        <th class="text-left">Issue Date</th>
                        <th class="text-left">Time Period</th>
                        <th class="text-left">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <template
                        v-if="previewInvoices && previewInvoices.length > 0"
                    >
                        <template
                            v-for="invoice in previewInvoices"
                            :key="invoice.number"
                        >
                            <tr v-if="!invoice.hide">
                                <td>{{ invoice.number }}</td>
                                <td>{{ invoice.issue_date }}</td>
                                <td>{{ invoice.time_period }}</td>
                                <td>
                                    {{ invoice.amount_object.prefix
                                    }}<span
                                        v-if="
                                            invoice.amount_object.amount != null
                                        "
                                        >{{
                                            currency(
                                                invoice.amount_object.amount
                                            )
                                        }}</span
                                    >
                                    {{ invoice.amount_object.suffix }}
                                </td>
                            </tr>
                        </template>
                        <tr v-if="showTotal">
                            <td colspan="3" class="text-end fw-bold pt-2">
                                Total
                                {{
                                    invoicingDetails.invoices_created > 0
                                        ? 'Remaining'
                                        : ''
                                }}
                            </td>
                            <td>
                                {{ totalAmount }}
                            </td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </template>
        <template v-else>
            <div class="alert alert-secondary" role="alert">
                There are no future invoices scheduled for this lease/license
            </div>
        </template>
    </div>
</template>

<script>
import currency from 'currency.js';
import { constants } from '@/utils/hooks';

export default {
    name: 'InvoicePreviewer',
    props: {
        invoicingDetails: {
            type: Object,
            required: true,
        },
        previewInvoices: {
            type: Array,
            required: true,
        },
        chargeMethodKey: {
            type: String,
            required: true,
        },
        loadingPreviewInvoices: {
            type: Boolean,
            required: true,
        },
        invoicingRepetitionTypeKey: {
            type: String,
            required: true,
        },
    },
    emits: ['updateDefaultInvoicingDate'],
    data: function () {
        return {
            constants: constants,
        };
    },
    computed: {
        showTotal: function () {
            return ![
                'percentage_of_gross_turnover',
                'percentage_of_gross_turnover_in_advance',
            ].includes(this.chargeMethodKey);
        },
        pastInvoiceCount: function () {
            return this.previewInvoices.filter(
                (amountObject) => amountObject.hide
            ).length;
        },
        totalAmount: function () {
            if (!this.invoicingDetails.base_fee_amount) {
                return `Enter Base Fee`;
            }
            let totalAmount =
                this.previewInvoices[this.previewInvoices.length - 1]
                    .amount_running_total;

            return `$${currency(totalAmount)}`;
        },
    },
    methods: {
        currency,
    },
};
</script>
