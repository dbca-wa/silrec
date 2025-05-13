<template>
    <div id="compliancesDash" class="container">
        <FormSection
            v-if="show_compliances_form_section"
            :form-collapse="false"
            label="Compliances"
            index="compliances"
        >
            <CompliancesTable level="internal" />
        </FormSection>
        <FormSection
            :form-collapse="false"
            label="Compliances Referred to Me"
            index="compliances-referred-to-me"
        >
            <CompliancesTable
                level="internal"
                :compliances-referred-to-me="true"
                filter-approval-type-cache-name="filterApprovalTypeForCompliancesReferredToMeTable"
                filter-compliance-status-cache-name="filterComplianceStatusForCompliancesReferredToMeTable"
                filter-compliance-due-date-from-cache-name="filterComplianceDueDateFromForCompliancesReferredToMeTable"
                filter-compliance-due-date-to-cache-name="filterComplianceDueDateToForCompliancesReferredToMeTable"
            />
        </FormSection>
    </div>
</template>

<script>
import CompliancesTable from '@/components/common/table_compliances.vue';

export default {
    name: 'InternalCompliancesDashboard',
    components: {
        CompliancesTable,
    },
    data() {
        return {
            accessing_user: null,
        };
    },
    computed: {
        show_compliances_form_section() {
            return (
                this.accessing_user &&
                (this.accessing_user.is_assessor ||
                    this.accessing_user.is_finance_officer)
            );
        },
        show_compliances_referred_to_me_form_section() {
            return (
                this.accessing_user && this.accessing_user.is_compliance_referee
            );
        },
    },
    mounted: async function () {
        const res = await fetch('/api/profile');
        const resData = await res.json();
        this.accessing_user = resData;
    },
};
</script>
