<template>
    <div :id="'invoiceRecordTransaction' + invoice_id">
        <modal
            transition="modal fade"
            :title="title"
            ok-text="Record Transaction"
            cancel-text="Cancel"
            large
            @ok="validateForm"
        >
            <div class="container">
                <div class="row">
                    <div class="col">
                        <form
                            id="invoice-record-transaction-form"
                            class="needs-validation"
                            novalidate
                        >
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>
                                            Debit
                                            <small class="text-muted"
                                                >(Payment - Decreases
                                                Balance)</small
                                            >
                                        </th>
                                        <th>
                                            Credit
                                            <small class="text-muted"
                                                >(Charge - Increases
                                                Balance)</small
                                            >
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>
                                            <input
                                                id="debit"
                                                v-model="transaction.debit"
                                                class="form-control"
                                                type="number"
                                                min="0.00"
                                                step="0.01"
                                                required
                                                @change="
                                                    !transaction.debit
                                                        ? (transaction.debit =
                                                              '0.00')
                                                        : null
                                                "
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a debit or credit
                                                amount.
                                            </div>
                                        </td>
                                        <td>
                                            <input
                                                id="credit"
                                                v-model="transaction.credit"
                                                class="form-control"
                                                type="number"
                                                min="0.00"
                                                step="0.01"
                                                required
                                                @change="
                                                    !transaction.debit
                                                        ? (transaction.debit =
                                                              '0.00')
                                                        : null
                                                "
                                            />
                                            <div class="invalid-feedback">
                                                Please enter a debit or credit
                                                amount.
                                            </div>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </form>
                        <div>
                            <ul class="list-group">
                                <li class="list-group-item">
                                    <span class="footer-heading pe-1"
                                        >Balance Remaining:</span
                                    >
                                    <span
                                        class="fw-bold"
                                        :class="
                                            balance_remaining > 0
                                                ? 'text-danger'
                                                : 'text-success'
                                        "
                                        >{{ balanceRemainingCurrency }}</span
                                    >
                                </li>
                                <li class="list-group-item">
                                    <span class="footer-heading pe-1"
                                        >Projected Balance:</span
                                    >
                                    <span
                                        class="fw-bold"
                                        :class="projectedBalanceClass"
                                        >{{
                                            balanceRemainingAfterTransactionCurrency
                                        }}</span
                                    >
                                </li>
                            </ul>
                            <BootstrapAlert
                                v-if="balance_remaining - transaction.debit < 0"
                                type="warning"
                                icon="exclamation-triangle-fill"
                                class="mt-3"
                            >
                                Transaction is greater than the balance
                                remaining.
                            </BootstrapAlert>
                        </div>
                    </div>
                </div>
            </div>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import { api_endpoints } from '@/utils/hooks.js';
import currency from 'currency.js';
import Swal from 'sweetalert2';

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
        balance_remaining: {
            type: Number,
            default: null,
        },
    },
    emits: ['transactionRecorded'],
    data: function () {
        let vm = this;
        return {
            isModalOpen: false,
            transactions: null,
            transaction: {
                id: vm.invoice_id,
                debit: '0.00',
                credit: '0.00',
            },
        };
    },
    computed: {
        title: function () {
            return (
                'Record Transaction for Invoice: ' +
                this.invoice_lodgement_number
            );
        },

        balanceRemainingCurrency: function () {
            return currency(this.balance_remaining).format();
        },
        balanceRemainingAfterTransaction: function () {
            return (
                this.balance_remaining -
                Number(this.transaction.debit) +
                Number(this.transaction.credit)
            );
        },
        balanceRemainingAfterTransactionCurrency: function () {
            return currency(this.balanceRemainingAfterTransaction).format();
        },
        projectedBalanceClass: function () {
            if (this.balanceRemainingAfterTransaction == 0) {
                return 'text-success';
            }
            if (this.balanceRemainingAfterTransaction < 0) {
                return 'text-warning';
            }
            return '';
        },
    },
    watch: {
        isModalOpen: function (newVal) {
            let vm = this;
            if (newVal) {
                vm.transaction.invoice_id = vm.invoice_id;
                vm.transaction.credit = '0.00';
                vm.$nextTick(function () {
                    $('#debit').focus();
                });
            }
        },
    },
    methods: {
        close: function () {
            this.transaction.credit = '0.00';
            this.transaction.debit = '0.00';
            this.isModalOpen = false;
        },
        validateForm: function () {
            let vm = this;
            var form = document.getElementById(
                'invoice-record-transaction-form'
            );

            if (vm.transaction.debit == 0 && vm.transaction.credit == 0) {
                form.debit.setCustomValidity(
                    'Please enter a debit or credit amount.'
                );
                form.credit.setCustomValidity(
                    'Please enter a debit or credit amount.'
                );
            }

            if (form.checkValidity()) {
                vm.recordTransaction();
            } else {
                form.classList.add('was-validated');
                $('#invoice-record-transaction-form')
                    .find(':invalid')
                    .first()
                    .focus();
            }

            return false;
        },
        recordTransaction: function () {
            let vm = this;
            const requestOptions = {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(vm.transaction),
            };
            fetch(
                api_endpoints.invoices + `${vm.invoice_id}/record_transaction/`,
                requestOptions
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        Promise.reject(error);
                    }
                    Swal.fire({
                        icon: 'success',
                        title: 'Transaction Recorded',
                        text: 'The transaction has been recorded.',
                    });
                    vm.$emit('transactionRecorded');
                })
                .catch((error) => {
                    console.error('There was an error!', error);
                    Promise.reject(error);
                });
        },
    },
};
</script>
