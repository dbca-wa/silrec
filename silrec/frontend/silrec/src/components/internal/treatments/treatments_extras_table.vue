<template>
    <div class="treatment-extras-table">
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">
            src/components/internal/treatments/treatments_extras_table.vue
        </div>
        JM4 {{ treatmentId }}
        <div v-if="loading" class="text-center p-3">
            <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span class="ms-2">Loading treatment details...</span>
        </div>

        <div v-else-if="error" class="alert alert-warning">
            <i class="bi bi-exclamation-triangle"></i> {{ error }}
        </div>

        <div
            v-else-if="treatmentExtras.length === 0"
            class="text-muted text-center p-3"
        >
            <i class="bi bi-info-circle"></i> No additional treatment details
            found.
        </div>

        <div v-else class="table-responsive">
            <table class="table table-sm table-striped">
                <thead>
                    <tr>
                        <th>Reschedule Reason</th>
                        <th>Success Rate</th>
                        <th>Stocking Rate</th>
                        <th>Species Assessed</th>
                        <th>Assessment Type</th>
                        <th v-if="!readOnly">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="extra in treatmentExtras"
                        :key="extra.treatment_xtra_id"
                    >
                        <td>
                            <span
                                v-if="extra.rescheduled_reason"
                                class="badge bg-secondary"
                            >
                                {{ extra.rescheduled_reason }}
                            </span>
                            <span v-else class="text-muted">-</span>
                        </td>
                        <td>
                            <span v-if="extra.success_rate_pct !== null">
                                {{ extra.success_rate_pct }}%
                            </span>
                            <span v-else class="text-muted">-</span>
                        </td>
                        <td>
                            <span v-if="extra.stocking_rate_spha !== null">
                                {{ extra.stocking_rate_spha }} sph
                            </span>
                            <span v-else class="text-muted">-</span>
                        </td>
                        <td>
                            <span v-if="extra.api_species_assessed_display">
                                {{ extra.api_species_assessed_display }}
                            </span>
                            <span v-else class="text-muted">-</span>
                        </td>
                        <td>
                            <span v-if="extra.zassessment_type">
                                {{ extra.zassessment_type }}
                            </span>
                            <span v-else class="text-muted">-</span>
                        </td>
                        <td v-if="!readOnly" class="action-column">
                            <router-link
                                :to="`/internal/treatment/${treatment_id}/treatment-extra/${extra.treatment_xtra_id}`"
                                class="btn btn-sm btn-outline-primary me-1"
                                title="Edit Details"
                            >
                                <i class="bi bi-pencil"></i>
                            </router-link>
                            <button
                                class="btn btn-sm btn-outline-danger"
                                @click="deleteExtra(extra.treatment_xtra_id)"
                                title="Delete Details"
                            >
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>

            <!-- Add Extra Button -->
            <!--
      <div v-if="!readOnly && treatmentId" class="mt-3">
        <router-link 
          :to="`/internal/treatment/${treatmentId}/extra/new`"
          class="btn btn-outline-primary btn-sm"
        >
          <i class="bi bi-plus"></i> Add Treatment Details
        </router-link>
      </div>
      -->
        </div>
    </div>
</template>

<script>
import TreatmentExtraForm from './treatments_extras_form.vue';
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'TreatmentExtrasTable',
    components: {
        TreatmentExtraForm,
    },
    props: {
        treatmentId: {
            type: [Number, String],
            required: true,
        },
        readOnly: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            loading: false,
            error: null,
            treatmentExtras: [],
            showEditModal: false,
            editingExtra: null,
        };
    },
    computed: {
        hasExtras() {
            return this.treatmentExtras.length > 0;
        },
    },
    methods: {
        getCSRFToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === name + '=') {
                        cookieValue = decodeURIComponent(
                            cookie.substring(name.length + 1)
                        );
                        break;
                    }
                }
            }
            return cookieValue;
        },
        async loadTreatmentExtras() {
            this.loading = true;
            this.error = null;

            try {
                const response = await fetch(
                    `${api_endpoints.treatment_extras}?treatment_id=${this.treatmentId}`
                );

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                // Handle both array and paginated response formats
                if (Array.isArray(data)) {
                    this.treatmentExtras = data;
                } else if (data.results && Array.isArray(data.results)) {
                    this.treatmentExtras = data.results;
                } else {
                    this.treatmentExtras = [];
                }
            } catch (error) {
                console.error('Error loading treatment extras:', error);
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

        async deleteExtra(treatmentExtraId) {
            const result = await swal.fire({
                icon: 'warning',
                title: 'Are you sure?',
                text: 'Are you sure you want to delete these treatment details?',
                showCancelButton: true,
                confirmButtonText: 'Yes, delete it!',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#d33',
            });

            if (!result.isConfirmed) {
                return;
            }

            try {
                const response = await fetch(
                    `${api_endpoints.treatment_extras}${treatmentExtraId}/`,
                    {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': this.getCSRFToken(),
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                // Remove from local array
                this.treatmentExtras = this.treatmentExtras.filter(
                    (extra) => extra.treatment_xtra_id !== treatmentExtraId
                );

                this.$emit('extra-updated');

                await swal.fire({
                    icon: 'success',
                    title: 'Deleted!',
                    text: 'Treatment details deleted successfully',
                    timer: 3000,
                    showConfirmButton: false,
                });
            } catch (error) {
                console.error('Error deleting treatment extra:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Delete Failed',
                    text: 'Failed to delete treatment details',
                    confirmButtonText: 'OK',
                });
            }
        },

        handleExtraSaved() {
            this.closeEditModal();
            this.loadTreatmentExtras();
            this.$emit('extra-updated');
        },

        refreshData() {
            this.loadTreatmentExtras();
        },
    },
    mounted() {
        this.loadTreatmentExtras();
    },
    watch: {
        treatmentId: {
            handler(newVal) {
                if (newVal) {
                    this.loadTreatmentExtras();
                }
            },
            immediate: true,
        },
    },
};
</script>

<style scoped>
.treatment-extras-table {
    margin-top: 10px;
}

.action-column {
    white-space: nowrap;
    width: 100px;
}

.table {
    font-size: 0.875rem;
}

.badge {
    font-size: 0.75rem;
}
</style>
