<template>
    <div id="invoicesDash" class="container">
        <FormSection
            :form-collapse="false"
            label="Invoice Records"
            index="invoices"
        >
            <InvoicesTable :level="level" />
        </FormSection>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import InvoicesTable from '@/components/common/table_invoices.vue';
export default {
    name: 'InternalInvoicesDashboard',
    components: {
        FormSection,
        InvoicesTable,
    },
    data() {
        return {
            level: this.$route.name.includes('external')
                ? 'external'
                : 'internal',
        };
    },
};
</script>
