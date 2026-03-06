<template>
    <div class="container">
        <div class="row">
            <div class="col-sm-12">
                <template v-if="invoice">
                    <h2 class="mb-3">Payment Failure</h2>
                    <p class="lead">
                        Unfortunately there was a problem paying your invoice
                    </p>
                    <p class="lead">
                        Please
                        <a :href="tryAgain">try again</a>
                        and if the problem persists contact us at:
                        <a href="mailto:>{{ supportEmail }}">{{
                            supportEmail
                        }}</a>
                    </p>
                    <table class="table table-sm w-50">
                        <tbody>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold">Invoice</span>
                                </td>
                                <td>{{ invoice.lodgement_number }}</td>
                            </tr>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold">Approval</span>
                                </td>
                                <td>{{ invoice.approval_lodgement_number }}</td>
                            </tr>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold">Holder</span>
                                </td>
                                <td>{{ invoice.holder }}</td>
                            </tr>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold">Approval Type</span>
                                </td>
                                <td>{{ invoice.approval_type }}</td>
                            </tr>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold">Amount</span>
                                </td>
                                <td>${{ invoice.amount }}</td>
                            </tr>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold"
                                        >Balance Remaining</span
                                    >
                                </td>
                                <td>${{ invoice.balance }}</td>
                            </tr>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold">Status</span>
                                </td>
                                <td>
                                    <span class="badge bg-success">{{
                                        invoice.status_display
                                    }}</span>
                                </td>
                            </tr>
                            <tr>
                                <td scope="row">
                                    <span class="fw-bold">Receipt</span>
                                </td>
                                <td>
                                    <a
                                        class="m-0 p-0"
                                        target="_blank"
                                        :href="invoice.ledger_invoice_url"
                                        >Receipt
                                        <i
                                            class="fa fa-external-link"
                                            aria-hidden="true"
                                        ></i>
                                    </a>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </template>
                <BootstrapSpinner v-else :loading="true" class="text-primary" />
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints, constants, utils } from '@/utils/hooks.js';

export default {
    name: 'PaymentSuccess',
    data: function () {
        return {
            invoice: null,
            supportEmail: constants.SUPPORT_EMAIL,
        };
    },
    computed: {
        tryAgain: function () {
            return (
                api_endpoints.invoices +
                this.$route.params.invoice_id +
                '/pay_invoice/'
            );
        },
    },
    created: async function () {
        this.invoice = await utils.fetchUrl(
            api_endpoints.invoices + this.$route.params.invoice_id + '/'
        );
    },
    mounted: function () {},
};
</script>

<style scoped></style>
