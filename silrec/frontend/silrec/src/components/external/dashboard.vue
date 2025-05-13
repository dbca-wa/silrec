<template>
    <div id="externalDash" class="container">
        <FormSection
            v-if="accessing_user && accessing_user.is_referee"
            :form-collapse="false"
            label="Proposals Referred to Me"
            index="leases_and_licences"
        >
            <ApplicationsReferredToMeTable
                ref="applications_referred_to_me_table"
                level="external"
                :email_user_id_assigned="accessing_user.id"
                filter-application-type-cache-name="filterApplicationTypeForApplicationReferredToMeTable"
                filter-application-status-cache-name="filterApplicationStatusForApplicationReferredToMeTable"
                filter-proposal-lodged-from-cache-name="filterApplicationLodgedFromForApplicationReferredToMeTable"
                filter-proposal-lodged-to-cache-name="filterApplicationLodgedToForApplicationReferredToMeTable"
            />
        </FormSection>

        <FormSection
            :form-collapse="false"
            label="Proposals"
            subtitle="- View existing proposals and lodge new ones"
            index="applications"
        >
            <ApplicationsTable level="external" />
        </FormSection>

        <FormSection
            :form-collapse="false"
            label="Leases and Licences"
            subtitle="- View existing leases / licences and renew them"
            index="licences_and_permits"
        >
            <ApprovalsTable level="external" />
        </FormSection>

        <FormSection
            :form-collapse="false"
            label="Compliances"
            subtitle="- The obligations you must comply by to keep your lease / licence valid"
            index="compliances"
        >
            <CompliancesTable level="external" />
        </FormSection>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import ApplicationsTable from '@/components/common/table_proposals.vue';
import ApplicationsReferredToMeTable from '@/components/common/table_proposals.vue';
import ApprovalsTable from '@/components/common/table_approvals.vue';
import CompliancesTable from '@/components/common/table_compliances.vue';

export default {
    name: 'ExternalDashboard',
    components: {
        FormSection,
        ApplicationsTable,
        ApplicationsReferredToMeTable,
        ApprovalsTable,
        CompliancesTable,
    },
    data: function () {
        return {
            accessing_user: null,
        };
    },
    computed: {
        is_external: function () {
            return this.level == 'external';
        },
        is_internal: function () {
            return this.level == 'internal';
        },
    },
    mounted: async function () {
        const res = await fetch('/api/profile');
        const resData = await res.json();
        this.accessing_user = resData;
        // must be at top level of every page with <FormSection> component
        // eslint-disable-next-line no-undef
        chevron_toggle.init();
    },
};
</script>
