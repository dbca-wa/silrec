<template>
    <div class="container">
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">
            src/components/internal/treatments/treatment_extra_detail.vue
        </div>
        <div class="header-actions mb-4">
            <button class="btn btn-secondary" @click="goBack">
                <i class="bi bi-arrow-left"></i> Back
            </button>
            <h2 class="page-title">
                {{
                    isNew
                        ? 'Add Treatment Extra Details'
                        : 'Edit Treatment Extra Details'
                }}
            </h2>
        </div>

        <div v-if="loading" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <div v-if="error" class="alert alert-danger">
            {{ error }}
        </div>

        <div v-if="!loading && !error" class="card">
            JM2: {{ treatmentId }}<br />
            JM3: {{ treatmentExtraId }}
            <div class="card-body">
                <TreatmentExtraForm
                    :treatment-id="treatmentId"
                    :extra-data="extraData"
                    :read-only="readOnly"
                    @extra-saved="handleExtraSaved"
                    @cancel="goBack"
                    @error="handleError"
                />
            </div>
        </div>
    </div>
</template>

<script>
import TreatmentExtraForm from './treatments_extras_form.vue';
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'TreatmentExtraDetail',
    components: {
        TreatmentExtraForm,
    },
    props: {
        treatmentExtraId: {
            type: [Number, String],
            default: null,
        },
        treatmentId: {
            type: [Number, String],
            required: true,
        },
    },
    data() {
        return {
            loading: false,
            error: null,
            extraData: null,
            readOnly: false,
        };
    },
    computed: {
        isNew() {
            return !this.treatmentExtraId;
        },
    },
    methods: {
        goBack() {
            this.$router.go(-1);
        },
        handleExtraSaved(extraData) {
            this.$emit('extra-saved', extraData);
            this.goBack();
        },
        handleError(errorMessage) {
            this.error = errorMessage;
            swal.fire({
                icon: 'error',
                title: 'Error',
                text: errorMessage,
                confirmButtonText: 'OK',
            });
        },
        async loadExtraData() {
            if (this.isNew) return;

            this.loading = true;
            try {
                const response = await fetch(
                    `${api_endpoints.treatment_extras}${this.treatmentExtraId}/`
                );

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                this.extraData = await response.json();
            } catch (error) {
                console.error('Error loading treatment extra data:', error);
                this.error = 'Failed to load treatment details';
                await swal.fire({
                    icon: 'error',
                    title: 'Load Failed',
                    text: 'Failed to load treatment details',
                    confirmButtonText: 'OK',
                });
            } finally {
                this.loading = false;
            }
        },
    },
    mounted() {
        this.loadExtraData();
    },
};
</script>

<style scoped>
.treatment-extra-detail-container {
    padding: 20px;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 15px;
}

.page-title {
    margin: 0;
    color: #333;
}
</style>
