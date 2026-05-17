<template>
    <div class="container">
        <div class="header-actions mb-4">
            <button class="btn btn-secondary" @click="goBack">
                <i class="bi bi-arrow-left"></i> Back
            </button>
            <h2 class="page-title">Treatment Extra Detail</h2>
        </div>

        <div v-if="loading" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <div v-if="error" class="alert alert-danger">{{ error }}</div>

        <div v-if="!loading && !error && extra" class="card">
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-3">Treatment Extra ID</dt>
                    <dd class="col-sm-9">{{ extra.treatment_xtra_id }}</dd>

                    <dt class="col-sm-3">Treatment</dt>
                    <dd class="col-sm-9">{{ extra.treatment_info || extra.treatment || 'N/A' }}</dd>

                    <dt class="col-sm-3">Machine ID</dt>
                    <dd class="col-sm-9">{{ extra.zmachine_id || 'N/A' }}</dd>

                    <dt class="col-sm-3">Success Rate (%)</dt>
                    <dd class="col-sm-9">{{ extra.success_rate_pct != null ? extra.success_rate_pct + '%' : 'N/A' }}</dd>

                    <dt class="col-sm-3">Stocking Rate (spha)</dt>
                    <dd class="col-sm-9">{{ extra.stocking_rate_spha != null ? extra.stocking_rate_spha : 'N/A' }}</dd>

                    <dt class="col-sm-3">Reschedule Reason</dt>
                    <dd class="col-sm-9">{{ extra.rescheduled_reason || 'N/A' }}</dd>

                    <dt class="col-sm-3">Z Result Standard</dt>
                    <dd class="col-sm-9">{{ extra.zresult_standard || 'N/A' }}</dd>

                    <dt class="col-sm-3">Seed Source</dt>
                    <dd class="col-sm-9">{{ extra.zseed_source || 'N/A' }}</dd>

                    <dt class="col-sm-3">Assessment Type</dt>
                    <dd class="col-sm-9">{{ extra.zassessment_type || 'N/A' }}</dd>
                </dl>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'TreatmentExtraDetailPage',
    props: {
        treatmentExtraId: {
            type: [Number, String],
            required: true,
        },
    },
    data() {
        return {
            loading: true,
            error: null,
            extra: null,
        };
    },
    async mounted() {
        await this.fetchExtra();
    },
    methods: {
        async fetchExtra() {
            this.loading = true;
            this.error = null;
            try {
                const response = await fetch(
                    `${api_endpoints.treatment_extras}${this.treatmentExtraId}/`
                );
                if (!response.ok) throw new Error('Failed to load treatment extra');
                this.extra = await response.json();
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
