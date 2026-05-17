<template>
    <div class="container">
        <div class="header-actions mb-4">
            <button class="btn btn-secondary" @click="goBack">
                <i class="bi bi-arrow-left"></i> Back
            </button>
            <h2 class="page-title">Prescription Detail</h2>
        </div>

        <div v-if="loading" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <div v-if="error" class="alert alert-danger">{{ error }}</div>

        <div v-if="!loading && !error && prescription" class="card">
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-3">Prescription ID</dt>
                    <dd class="col-sm-9">{{ prescription.prescription_id }}</dd>

                    <dt class="col-sm-3">Objective Code</dt>
                    <dd class="col-sm-9">{{ prescription.obj_code || 'N/A' }}</dd>

                    <dt class="col-sm-3">Task</dt>
                    <dd class="col-sm-9">{{ prescription.task || 'N/A' }}</dd>

                    <dt class="col-sm-3">Sequence</dt>
                    <dd class="col-sm-9">{{ prescription.sequence }}</dd>

                    <dt class="col-sm-3">Year</dt>
                    <dd class="col-sm-9">{{ prescription.year }}</dd>

                    <dt class="col-sm-3">Mandatory</dt>
                    <dd class="col-sm-9">{{ prescription.mandatory ? 'Yes' : 'No' }}</dd>

                    <dt class="col-sm-3">Comment</dt>
                    <dd class="col-sm-9">{{ prescription.comment || 'N/A' }}</dd>

                    <dt class="col-sm-3">Effective From</dt>
                    <dd class="col-sm-9">{{ prescription.effective_from || 'N/A' }}</dd>

                    <dt class="col-sm-3">Effective To</dt>
                    <dd class="col-sm-9">{{ prescription.effective_to || 'N/A' }}</dd>
                </dl>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'PrescriptionDetail',
    props: {
        prescriptionId: {
            type: [Number, String],
            required: true,
        },
    },
    data() {
        return {
            loading: true,
            error: null,
            prescription: null,
        };
    },
    async mounted() {
        await this.fetchPrescription();
    },
    methods: {
        async fetchPrescription() {
            this.loading = true;
            this.error = null;
            try {
                const response = await fetch(
                    `${api_endpoints.prescriptions}${this.prescriptionId}/`
                );
                if (!response.ok) throw new Error('Failed to load prescription');
                this.prescription = await response.json();
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        goBack() {
            this.$router.go(-1);
        },
    },
};
</script>
