<template>
    <div class="treatment-extras-table">
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
                            <button
                                class="btn btn-sm btn-outline-primary me-1"
                                @click="editExtra(extra)"
                                title="Edit Details"
                            >
                                <i class="bi bi-pencil"></i>
                            </button>
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
        </div>

        <!-- Edit Treatment Extra Modal -->
        <div
            v-if="showEditModal"
            class="modal fade show d-block"
            tabindex="-1"
            style="background: rgba(0, 0, 0, 0.5)"
        >
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            {{ editingExtra ? 'Edit' : 'Add' }} Treatment
                            Details
                        </h5>
                        <button
                            type="button"
                            class="btn-close"
                            @click="closeEditModal"
                        ></button>
                    </div>
                    <div class="modal-body">
                        <TreatmentExtraForm
                            :treatment-id="treatmentId"
                            :extra-data="editingExtra"
                            @extra-saved="handleExtraSaved"
                            @cancel="closeEditModal"
                        />
                    </div>
                </div>
            </div>
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
        async loadTreatmentExtras() {
            if (!this.treatmentId) {
                this.error = 'No treatment ID provided';
                return;
            }

            this.loading = true;
            this.error = null;

            try {
                const response = await this.$http.get(
                    api_endpoints.treatment_extras,
                    {
                        params: {
                            treatment_id: this.treatmentId,
                        },
                    }
                );
                this.treatmentExtras = response.data;
            } catch (error) {
                console.error('Error loading treatment extras:', error);
                this.error = 'Failed to load treatment details';
            } finally {
                this.loading = false;
            }
        },

        editExtra(extra) {
            this.editingExtra = extra;
            this.showEditModal = true;
        },

        addExtra() {
            this.editingExtra = null;
            this.showEditModal = true;
        },

        async deleteExtra(extraId) {
            if (
                !confirm(
                    'Are you sure you want to delete these treatment details?'
                )
            ) {
                return;
            }

            try {
                await this.$http.delete(
                    `${api_endpoints.treatment_extras}${extraId}/`
                );
                this.$emit('extra-deleted');
                this.loadTreatmentExtras(); // Reload the list
            } catch (error) {
                console.error('Error deleting treatment extra:', error);
                alert('Failed to delete treatment details');
            }
        },

        closeEditModal() {
            this.showEditModal = false;
            this.editingExtra = null;
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
