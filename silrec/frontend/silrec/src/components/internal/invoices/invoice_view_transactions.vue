<template>
    <div :id="'invoiceTransactions' + invoice_id">
        <modal
            transition="modal fade"
            :title="title"
            okText=""
            cancelText="Dismiss"
            large
        >
            <div class="container">
                <div class="row">
                    <div v-if="readyToRender" class="col">
                        <table
                            :key="invoice_id"
                            class="table table-sm table-striped"
                        >
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Time</th>
                                    <th>Debit</th>
                                    <th>Credit</th>
                                    <th>Balance</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr
                                    v-for="transaction in transactions"
                                    :key="transaction.id"
                                >
                                    <td>
                                        {{
                                            new Date(
                                                transaction.datetime_created
                                            ).toLocaleDateString()
                                        }}
                                    </td>
                                    <td>
                                        {{
                                            new Date(
                                                transaction.datetime_created
                                            ).toLocaleTimeString()
                                        }}
                                    </td>
                                    <td>${{ transaction.debit }}</td>
                                    <td>${{ transaction.credit }}</td>
                                    <td>
                                        ${{
                                            cumulativeBalance(
                                                transaction.cumulative_balance
                                            )
                                        }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div>
                            <ul class="list-group mb-3">
                                <li class="list-group-item">
                                    <span class="footer-heading"
                                        >Invoice Amount:</span
                                    >
                                    <span class="fw-bold"
                                        >${{ invoiceAmount }}</span
                                    >
                                </li>
                                <li class="list-group-item">
                                    <span class="footer-heading"
                                        >Total Payments:</span
                                    >
                                    <span
                                        class="fw-bold"
                                        :class="
                                            invoice_amount - balanceRemaining >
                                            0
                                                ? 'text-success'
                                                : ''
                                        "
                                        >${{ paymentsMade }}</span
                                    >
                                </li>
                            </ul>
                            <ul class="list-group">
                                <li class="list-group-item">
                                    <span class="footer-heading"
                                        >Balance Remaining:</span
                                    >
                                    <span
                                        class="fw-bold"
                                        :class="
                                            balanceRemaining > 0
                                                ? 'text-danger'
                                                : 'text-success'
                                        "
                                        >${{ balanceRemaining }}</span
                                    >
                                </li>
                            </ul>
                        </div>
                    </div>
                    <BootstrapSpinner
                        v-else
                        class="text-primary"
                        :isLoading="true"
                        :centerOfScreen="false"
                        :small="true"
                    />
                </div>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import { utils } from '@/utils/hooks.js';
import currency from 'currency.js';

export default {
    name: 'InvoiceTransactions',
    components: {
        modal,
    },
    props: {
        invoice_id: {
            type: Number,
            default: null,
        },
        invoice_lodgement_number: {
            type: String,
            default: null,
        },
        invoice_amount: {
            type: Number,
            default: null,
        },
    },
    data: function () {
        return {
            isModalOpen: false,
            transactions: null,
        };
    },
    watch: {
        isModalOpen: async function (newVal) {
            if (newVal) {
                this.transactions = await utils.fetchInvoiceTransactions(
                    this.invoice_id
                );
            }
        },
    },
    computed: {
        title: function () {
            return (
                'Transaction History for Invoice: ' +
                this.invoice_lodgement_number
            );
        },
        readyToRender: function () {
            return (
                this.transactions &&
                this.transactions.length > 0 &&
                this.balanceRemaining !== null &&
                this.paymentsMade !== null
            );
        },
        balanceRemaining: function () {
            if (!this.transactions) {
                return null;
            }
            return currency(
                this.invoice_amount -
                    this.transactions[this.transactions.length - 1]
                        .cumulative_balance
            );
        },
        paymentsMade: function () {
            if (!this.transactions) {
                return null;
            }
            return currency(this.invoice_amount - this.balanceRemaining);
        },
        invoiceAmount: function () {
            return currency(this.invoice_amount);
        },
    },
    methods: {
        close: function () {
            this.transactions = null;
            this.isModalOpen = false;
        },
        cumulativeBalance: function (cumulative_balance) {
            return currency(this.invoice_amount - cumulative_balance);
        },
    },
};
</script>

<style scoped>
.footer-heading {
    display: inline-block;
    width: 160px;
}
</style>
