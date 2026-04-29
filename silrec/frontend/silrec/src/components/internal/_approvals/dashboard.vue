<template>
    <div id="TreatmentsDash" class="container">
        <TreatmentsTable
            ref="treatmentsTable"
            :read-only="isReadOnlyUser"
            @treatment-updated="refreshTreatments"
        />
    </div>
</template>

<script>
import TreatmentsTable from '@/components/internal/treatments/treatments_table.vue';
import permissionsMixin from '@/mixins/permissions';

export default {
    name: 'InternalTreatmentsDashboard',
    mixins: [permissionsMixin],
    components: {
        TreatmentsTable,
    },
    data() {
        return {
            // You can add any dashboard-level data here if needed
        };
    },
    methods: {
        async refreshTreatments() {
            // Refresh the treatments table data
            if (
                this.$refs.treatmentsTable &&
                this.$refs.treatmentsTable.refresh
            ) {
                await this.$refs.treatmentsTable.refresh();
            }
        },
    },
    mounted() {
        this.fetchCurrentUser();
        // You can add any initialization logic here
        console.log('Treatments dashboard mounted');
    },
};
</script>

<style scoped>
#TreatmentsDash {
    padding: 20px;
}
.container {
    width: 100%;
    height: 100%;
}
</style>
