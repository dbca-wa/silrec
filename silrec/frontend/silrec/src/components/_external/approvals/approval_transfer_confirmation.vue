<template lang="html">
    <div class="container">
        <div class="row d-flex justify-content-center">
            <div
                v-if="approval && approval.active_transfer"
                class="col-sm-7 border rounded p-4"
            >
                <div class="form-para">
                    <h3>
                        {{ approval.approval_type__type }} Transfer Initiated
                    </h3>
                </div>
                <div class="mb-3">Your application to transfer:</div>
                <div class="mb-3">
                    <span class="badge bg-primary me-2 fs-6">
                        {{ approval.lodgement_number }} -
                        {{ approval.approval_type }}</span
                    >
                    to
                    <i
                        class="fa fa-long-arrow-right text-success"
                        aria-hidden="true"
                    ></i>
                    <span class="badge bg-primary ms-1 me-2 fs-6">{{
                        approval.active_transfer.transferee_name
                    }}</span>
                </div>
                <div class="mb-3">has been initiated successfully.</div>
                <div class="mb-3">
                    You will be notified when the transfer proposal has been
                    approved.
                </div>

                <table class="table table-sm mb-3">
                    <tbody>
                        <tr>
                            <th scope="row" class="w-25">Reference number:</th>
                            <td>
                                {{ approval.active_transfer.lodgement_number }}
                            </td>
                        </tr>
                        <tr>
                            <th scope="row">Date / Time:</th>
                            <td>
                                {{
                                    formatDate(
                                        approval.active_transfer
                                            .datetime_initiated
                                    )
                                }}
                            </td>
                        </tr>
                    </tbody>
                </table>
                <BootstrapAlert type="warning" icon="exclamation-triangle-fill">
                    <div class="mb-3">
                        If any compliances become due during the transfer
                        process, they must be submitted before the transfer can
                        be completed.
                    </div>
                    <div class="mb-3">
                        If any invoices become due during the transfer process,
                        they must be paid before the transfer can be completed.
                    </div>
                </BootstrapAlert>
                <a
                    href="/external/"
                    class="router-link-active btn btn-primary float-end"
                    >Back to Dashboard</a
                >
            </div>
            <div v-else class="col-sm-6 borderDecoration">
                No transfer application found.
            </div>
            <BootstrapSpinner v-if="loading" />
        </div>
    </div>
</template>
<script>
export default {
    name: 'ApprovalTransferConfirmation',
    data: function () {
        return {
            approval: null,
            loading: false,
        };
    },
    created: function () {
        this.fetchApproval();
    },
    methods: {
        fetchApproval: function () {
            this.loading = true;
            fetch(`/api/approvals/${this.$route.params.approval_id}/`)
                .then((response) => {
                    response.json().then((data) => {
                        this.approval = data;
                    });
                })
                .catch((error) => {
                    console.error(error);
                })
                .finally(() => {
                    this.loading = false;
                });
        },
        formatDate: function (data) {
            return data ? moment(data).format('DD/MM/YYYY HH:mm:ss') : '';
        },
    },
};
</script>
