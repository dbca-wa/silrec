<template>
    <div id="organisations-dashboard" class="container">
        <div class="row">
            <div class="col">
                <FormSection label="Organisations" index="organisations">
                    <div class="d-flex flex-row-reverse mb-2">
                        <a
                            class="btn btn-primary"
                            href="/internal/organisations/add"
                        >
                            <i class="fa-solid fa-circle-plus"></i> Add
                            Organisation
                        </a>
                    </div>
                    <OrganisationsTable />
                </FormSection>
            </div>
        </div>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import OrganisationsTable from '@/components/common/table_organisations.vue';
export default {
    name: 'InternalOrganisationRequestsDashboard',
    components: {
        FormSection,
        OrganisationsTable,
    },
};
</script>
