<template lang="html">
    <div class="container">
        <div class="row">
            <div class="col-9">
                <div
                    v-if="compliance && compliance.id"
                    class="col border rounded p-3"
                >
                    <h2>Compliance Submitted Successfully</h2>
                    <table class="table py-2 w-50">
                        <tbody>
                            <tr>
                                <td><strong>Compliance:</strong></td>
                                <td>
                                    <strong>{{
                                        compliance.lodgement_number
                                    }}</strong>
                                </td>
                            </tr>
                            <tr>
                                <td><strong>Date/Time:</strong></td>
                                <td>
                                    <strong>{{
                                        compliance.lodgement_date_display
                                    }}</strong>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="my-4">
                        <p>Thank you for your submission.</p>
                        <p>
                            The compliance will be provided to an officer to
                            assess.
                        </p>
                        <p>
                            You will be notified by email once your submission
                            has been reviewed or if further action is required
                        </p>
                    </div>
                    <a class="btn btn-secondary" href="/external/"
                        >Back to dashboard</a
                    >
                </div>
                <BootstrapSpinner v-else :loading="true" class="text-primary" />
            </div>
        </div>
    </div>
</template>
<script>
import { api_endpoints, helpers } from '@/utils/hooks';

export default {
    name: 'ExternalComplianceSubmit',
    beforeRouteEnter: function (to, from, next) {
        next(async (vm) => {
            vm.fetchCompliance(to.params.compliance_id);
        });
    },
    data: function () {
        return {
            compliance: {},
        };
    },
    computed: {
        formattedDate: function () {
            return this.compliance.lodgement_date
                ? moment(this.compliance.lodgement_date).format(
                      'DD/MM/YYYY HH:mm:ss'
                  )
                : '';
        },
    },
    created: function () {
        if (!this.compliance) {
            this.fetchCompliance(this.$route.params.compliance_id);
        }
    },
    mounted: function () {
        let vm = this;
        vm.form = document.forms.new_compliance;
    },
    methods: {
        fetchCompliance: async function (compliance_id) {
            let vm = this;
            const response = await fetch(
                helpers.add_endpoint_json(
                    api_endpoints.compliances,
                    compliance_id
                )
            );
            const resData = await response.json();
            vm.compliance = Object.assign({}, resData);
        },
    },
};
</script>

<style lang="css" scoped>
.borderDecoration {
    border: 1px solid;
    border-radius: 5px;
    padding: 50px;
    margin-top: 70px;
}
</style>
