<template>
    <div id="organisationRequestsDash" class="container">
        <FormSection
            :form-collapse="false"
            label="Organisation Access Requests"
            index="organisationRequests"
        >
            <OrganisationRequestsTable level="internal" />
        </FormSection>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import OrganisationRequestsTable from '@/components/common/table_organisation_requests.vue';
export default {
    name: 'InternalOrganisationRequestsDashboard',
    components: {
        FormSection,
        OrganisationRequestsTable,
    },
};
</script>
