<template>
    <div class="container">
        <div class="header-actions mb-4">
            <button class="btn btn-secondary" @click="goBack">
                <i class="bi bi-arrow-left"></i> Back
            </button>
            <h2 class="page-title">Polygon Detail</h2>
        </div>

        <div v-if="loading" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <div v-if="error" class="alert alert-danger">{{ error }}</div>

        <div v-if="!loading && !error && polygon" class="card">
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-3">Polygon ID</dt>
                    <dd class="col-sm-9">{{ polygon.polygon_id }}</dd>

                    <dt class="col-sm-3">Name</dt>
                    <dd class="col-sm-9">{{ polygon.name || 'N/A' }}</dd>

                    <dt class="col-sm-3">Area (ha)</dt>
                    <dd class="col-sm-9">{{ polygon.area_ha }}</dd>

                    <dt class="col-sm-3">Compartment</dt>
                    <dd class="col-sm-9">{{ polygon.compartment || 'N/A' }}</dd>

                    <dt class="col-sm-3">FEA ID</dt>
                    <dd class="col-sm-9">{{ polygon.zfea_id || 'N/A' }}</dd>

                    <dt class="col-sm-3">Spatial Precision</dt>
                    <dd class="col-sm-9">{{ polygon.sp_code || 'N/A' }}</dd>

                    <dt class="col-sm-3">Created On</dt>
                    <dd class="col-sm-9">{{ polygon.created_on || 'N/A' }}</dd>

                    <dt class="col-sm-3">Created By</dt>
                    <dd class="col-sm-9">{{ polygon.created_by || 'N/A' }}</dd>

                    <dt class="col-sm-3">Updated On</dt>
                    <dd class="col-sm-9">{{ polygon.updated_on || 'N/A' }}</dd>

                    <dt class="col-sm-3">Updated By</dt>
                    <dd class="col-sm-9">{{ polygon.updated_by || 'N/A' }}</dd>
                </dl>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'PolygonDetail',
    props: {
        polygonId: {
            type: [Number, String],
            required: true,
        },
    },
    data() {
        return {
            loading: true,
            error: null,
            polygon: null,
        };
    },
    async mounted() {
        await this.fetchPolygon();
    },
    methods: {
        async fetchPolygon() {
            this.loading = true;
            this.error = null;
            try {
                const response = await fetch(
                    `${api_endpoints.polygons}${this.polygonId}/`
                );
                if (!response.ok) throw new Error('Failed to load polygon');
                this.polygon = await response.json();
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
