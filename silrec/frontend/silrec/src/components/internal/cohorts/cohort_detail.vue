<template>
    <div class="container">
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">
            internal/proposals/cohorts/cohort_detail.vue
        </div>
        <div class="header-actions mb-4">
            <button class="btn btn-secondary" @click="confirmCancel">
                <i class="bi bi-arrow-left"></i> Back to Map
            </button>
            <h2 class="page-title">
                Cohort Details -
                <span v-if="cohortData.obj_code"
                    >Objective: {{ cohortData.obj_code }}</span
                >
                <span v-else>Cohort {{ $route.params.cohortId }}</span>
            </h2>

            <!-- Add Treatment Button -->
            <router-link
                v-if="showFormActions"
                :to="`/internal/cohorts/${$route.params.cohortId}/treatment/new`"
                class="btn btn-primary"
            >
                <i class="bi bi-plus"></i> Add Treatment
            </router-link>
        </div>

        <!-- Loading state -->
        <div v-if="loading" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <!-- Error state -->
        <div v-if="error" class="alert alert-danger">
            {{ error }}
        </div>

        <!-- Combined Cohort Form -->
        <div v-if="!loading && !error && cohortData.cohort_id">
            <form @submit.prevent="saveAndContinue">
                <!-- Cohort Information -->
                <div class="card mb-4">
                    <div
                        class="card-header d-flex justify-content-between align-items-center"
                    >
                        <h5 class="card-title mb-0">
                            Cohort Information
                            <button
                                type="button"
                                class="btn btn-sm btn-outline-info ms-2"
                                @click="showSystemInfo = true"
                                title="View Creation Details"
                            >
                                <i class="bi bi-info-circle"></i>
                            </button>
                        </h5>
                    </div>
                    <div class="card-body">
                        <CohortForm
                            ref="cohortForm"
                            :cohortId="cohortId"
                            :cohort-data="cohortData"
                            :read-only="!canEdit"
                        />
                    </div>
                </div>

                <!-- Additional Cohort Fields (Collapsible) -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">
                            <button
                                type="button"
                                class="btn btn-link p-0 border-0 text-decoration-none"
                                @click="toggleAdditionalFields"
                            >
                                <i
                                    class="bi"
                                    :class="
                                        showAdditionalFields
                                            ? 'bi-chevron-down'
                                            : 'bi-chevron-right'
                                    "
                                ></i>
                                Additional Cohort Fields
                            </button>
                        </h5>
                    </div>
                    <div v-if="showAdditionalFields" class="card-body">
                        <AdditionalCohortFields
                            :key="additionalFieldsKey"
                            ref="additionalFields"
                            :cohort-data="cohortData"
                            :read-only="!canEdit"
                        />
                    </div>
                </div>
            </form>
        </div>

        <!-- Treatments Section (Collapsible) -->
        <div
            v-if="!loading && !error && cohortData.cohort_id"
            class="card mb-4"
        >
            <div
                class="card-header d-flex justify-content-between align-items-center"
            >
                <h5 class="card-title mb-0">
                    <button
                        type="button"
                        class="btn btn-link p-0 border-0 text-decoration-none"
                        @click="toggleTreatments"
                    >
                        <i
                            class="bi"
                            :class="
                                showTreatments
                                    ? 'bi-chevron-down'
                                    : 'bi-chevron-right'
                            "
                        ></i>
                        Treatments
                    </button>
                </h5>
                <div>
                    <router-link
                        v-if="showFormActions"
                        :to="`/internal/cohorts/${$route.params.cohortId}/treatment/new`"
                        class="btn btn-primary btn-sm"
                    >
                        <i class="bi bi-plus"></i> Add Treatment
                    </router-link>
                    <button
                        v-if="showTreatments"
                        type="button"
                        class="btn btn-outline-secondary btn-sm ms-2"
                        @click="refreshTreatments"
                        title="Refresh Treatments"
                    >
                        <i class="bi bi-arrow-clockwise"></i>
                    </button>
                </div>
            </div>
            <div v-if="showTreatments" class="card-body">
                <div v-if="treatmentsLoading" class="text-center">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden"
                            >Loading treatments...</span
                        >
                    </div>
                    <span class="ms-2">Loading treatments...</span>
                </div>
                <div v-else>
                    <TreatmentsTable
                        ref="treatmentsTable"
                        :cohort-id="$route.params.cohortId"
                        :read-only="!canEdit"
                        @treatment-updated="refreshTreatments"
                    />
                </div>
            </div>
        </div>

        <!-- Operations Section (Collapsible) - Modified to use inline form -->
        <div
            v-if="!loading && !error && cohortData.cohort_id"
            class="card mb-4"
        >
            <div
                class="card-header d-flex justify-content-between align-items-center"
            >
                <h5 class="card-title mb-0">
                    <button
                        type="button"
                        class="btn btn-link p-0 border-0 text-decoration-none"
                        @click="toggleOperations"
                    >
                        <i
                            class="bi"
                            :class="
                                showOperations
                                    ? 'bi-chevron-down'
                                    : 'bi-chevron-right'
                            "
                        ></i>
                        Operation Details
                        <span
                            v-if="cohortData.op_id && operationDetails"
                            class="badge bg-success ms-2"
                        >
                            <i class="bi bi-check-circle"></i> Linked
                        </span>
                        <span
                            v-else-if="cohortData.op_id && !operationDetails"
                            class="badge bg-warning ms-2"
                        >
                            <i class="bi bi-exclamation-triangle"></i> Broken
                            Link
                        </span>
                        <span v-else class="badge bg-secondary ms-2">
                            <i class="bi bi-dash-circle"></i> Not Linked
                        </span>
                    </button>
                </h5>
                <div>
                    <button
                        v-if="showOperations"
                        type="button"
                        class="btn btn-outline-secondary btn-sm"
                        @click="refreshOperation"
                        title="Refresh Operation"
                        :disabled="operationLoading"
                    >
                        <i class="bi bi-arrow-clockwise"></i>
                    </button>
                </div>
            </div>
            <div v-if="showOperations" class="card-body">
                <div v-if="operationLoading" class="text-center">
                    <div class="spinner-border spinner-border-sm" role="status">
                        <span class="visually-hidden"
                            >Loading operation...</span
                        >
                    </div>
                    <span class="ms-2">Loading operation...</span>
                </div>
                <div v-else>
                    <!-- Inline Operation Form (read-only or editable) -->
                    <div class="operation-inline-form">
                        <OperationForm
                            :key="operationFormKey"
                            ref="operationForm"
                            :operation-id="cohortData.op_id || null"
                            :cohort-id="cohortData.cohort_id"
                            :fea-id="feaId"
                            :read-only="!canEdit"
                            :show-actions="showFormActions"
                            @operation-saved="handleOperationSaved"
                            @cancel="cancelOperationEdit"
                        />
                    </div>
                </div>
            </div>
        </div>

        <!-- Sticky Action Buttons -->
        <div
            v-if="!loading && !error && cohortData.cohort_id && showFormActions"
            class="navbar fixed-bottom bg-navbar"
        >
            <div class="container">
                <div class="action-buttons">
                    <button
                        type="button"
                        class="btn btn-secondary btn-lg"
                        @click="confirmCancel"
                    >
                        <i class="bi bi-x-circle"></i> Cancel
                    </button>
                    <button
                        type="button"
                        class="btn btn-primary btn-lg"
                        @click="saveAndContinue"
                        :disabled="saving"
                    >
                        <span
                            v-if="saving"
                            class="spinner-border spinner-border-sm me-2"
                        ></span>
                        <i class="bi bi-check-circle"></i>
                        {{ saving ? 'Saving...' : 'Save and Continue' }}
                    </button>
                    <button
                        type="button"
                        class="btn btn-success btn-lg"
                        @click="saveAndExit"
                        :disabled="saving"
                    >
                        <span
                            v-if="saving"
                            class="spinner-border spinner-border-sm me-2"
                        ></span>
                        <i class="bi bi-check-lg"></i>
                        {{ saving ? 'Saving...' : 'Save' }}
                    </button>
                </div>
                <div class="action-buttons-help">
                    <small class="text-muted">
                        <i class="bi bi-info-circle"></i>
                        Cancel: Discard all changes and return to map | Save and
                        Continue: Save changes and stay on this page | Save:
                        Save changes and return to map
                    </small>
                </div>
            </div>
        </div>

        <!-- System Information Modal -->
        <div
            v-if="showSystemInfo"
            class="modal fade show d-block"
            tabindex="-1"
            style="background: rgba(0, 0, 0, 0.5)"
        >
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Created/Updated Details</h5>
                        <button
                            type="button"
                            class="btn-close"
                            @click="showSystemInfo = false"
                        ></button>
                    </div>
                    <div class="modal-body">
                        <SystemInformation :cohort-data="cohortData" />
                    </div>
                    <div class="modal-footer">
                        <button
                            type="button"
                            class="btn btn-secondary"
                            @click="showSystemInfo = false"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Cancel Confirmation Modal -->
        <div
            v-if="showCancelConfirm"
            class="modal fade show d-block"
            tabindex="-1"
            style="background: rgba(0, 0, 0, 0.5)"
        >
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Confirm Cancel</h5>
                        <button
                            type="button"
                            class="btn-close"
                            @click="showCancelConfirm = false"
                        ></button>
                    </div>
                    <div class="modal-body">
                        <p>
                            <i
                                class="bi bi-exclamation-triangle text-warning"
                            ></i>
                            All unsaved changes will be lost. Are you sure you
                            want to cancel?
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button
                            type="button"
                            class="btn btn-secondary"
                            @click="showCancelConfirm = false"
                        >
                            Continue Editing
                        </button>
                        <button
                            type="button"
                            class="btn btn-danger"
                            @click="cancelChanges"
                        >
                            Discard Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import CohortForm from '@/components/internal/cohorts/cohort_form.vue';
import AdditionalCohortFields from '@/components/internal/cohorts/additional_cohort_fields.vue';
import SystemInformation from '@/components/internal/cohorts/system_info_cohort.vue';
import TreatmentsTable from '@/components/internal/treatments/treatments_table.vue';
import OperationForm from '@/components/internal/operations/operations_form.vue';
import { api_endpoints, helpers } from '@/utils/hooks';
import permissionsMixin from '@/mixins/permissions';
import formValidationMixin from '@/mixins/form_validation';

export default {
    name: 'CohortDetail',
    mixins: [permissionsMixin, formValidationMixin],
    components: {
        CohortForm,
        AdditionalCohortFields,
        SystemInformation,
        TreatmentsTable,
        OperationForm,
    },
    props: {
        proposal_id: {
            type: [Number, String],
            default: null,
        },
        cohortId: {
            type: [Number, String],
            required: true,
        },
        polygonId: {
            type: [Number, String],
            default: null,
        },
    },
    data() {
        return {
            loading: false,
            error: null,
            cohortData: {
                cohort_id: null,
                op_id: null,
                obj_code: '',
                // Initialize other fields as needed
            },
            userPermissions: [],
            showAdditionalFields: false,
            showTreatments: false,
            showSystemInfo: false,
            showCancelConfirm: false,
            additionalFieldsKey: 0,
            saving: false,
            hasUnsavedChanges: false,
            treatmentsLoading: false,
            treatmentsCount: 0,
            showOperations: false,
            operationLoading: false,
            operationDetails: null,
            feaId: '',
            operationFormKey: 0,
        };
    },
    computed: {
        canEdit() {
            return !this.isReadOnlyUser;
        },
        showFormActions() {
            return this.canEdit && !this.isOperatorUser;
        },
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        operationExists() {
            return this.cohortData.op_id && this.operationDetails;
        },
    },
    methods: {
        async loadCohortData() {
            this.loading = true;
            this.error = null;

            try {
                const cohortId = this.cohortId || this.$route.params.cohortId;
                const url = `${api_endpoints.cohorts}${cohortId}/`;
                console.log('Loading cohort data from:', url);

                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                this.cohortData = data;
                console.log(
                    'Cohort data loaded successfully:',
                    this.cohortData
                );

                // Load operation data if cohort has op_id
                if (this.cohortData.op_id) {
                    await this.loadOperationData();
                }

                // Get FEA ID from assigned polygons
                await this.loadFEAIdFromPolygons();
            } catch (error) {
                console.error('Error loading cohort data:', error);
                this.error =
                    'Failed to load cohort data. Please check if the cohort exists.';
                await swal.fire({
                    icon: 'error',
                    title: 'Load Failed',
                    text: 'Failed to load cohort data. Please check if the cohort exists.',
                    confirmButtonText: 'OK',
                });
            } finally {
                this.loading = false;
            }
        },

        async loadFEAIdFromPolygons() {
            if (!this.cohortData.cohort_id) return;

            try {
                const response = await fetch(
                    `${api_endpoints.cohorts}${this.cohortData.cohort_id}/`
                );
                if (response.ok) {
                    const cohortDetails = await response.json();
                    if (
                        cohortDetails.assigned_polygons &&
                        cohortDetails.assigned_polygons.length > 0
                    ) {
                        // Get the first polygon's FEA ID
                        const polygonId =
                            cohortDetails.assigned_polygons[0].polygon_id;
                        const polygonResponse = await fetch(
                            `${api_endpoints.polygons}${polygonId}/`
                        );
                        if (polygonResponse.ok) {
                            const polygonData = await polygonResponse.json();
                            this.feaId = polygonData.zfea_id || '';
                        }
                    }
                }
            } catch (error) {
                console.error('Error loading FEA ID from polygons:', error);
            }
        },

        async loadOperationData() {
            if (!this.cohortData.op_id) {
                this.operationDetails = null;
                return;
            }

            this.operationLoading = true;
            try {
                const url = `${api_endpoints.operations}${this.cohortData.op_id}/`;
                console.log('Loading operation data from:', url);
                const response = await fetch(url);

                if (response.ok) {
                    this.operationDetails = await response.json();
                    console.log(
                        'Operation data loaded:',
                        this.operationDetails
                    );
                } else if (response.status === 404) {
                    // Operation doesn't exist (though cohort has op_id)
                    this.operationDetails = null;
                    console.log(
                        'Operation not found for op_id:',
                        this.cohortData.op_id
                    );
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            } catch (error) {
                console.error('Error loading operation data:', error);
                this.operationDetails = null;
            } finally {
                this.operationLoading = false;
            }
        },

        async refreshOperation() {
            this.operationFormKey++; // Force re-render of operation form
            await this.loadOperationData();
            await this.loadFEAIdFromPolygons();
        },

        async handleOperationSaved(operationData) {
            // Update cohort's op_id with the new operation's ID
            if (operationData && operationData.op_id) {
                this.cohortData.op_id = operationData.op_id;
                this.operationDetails = operationData;

                // Force re-render of the operation form by incrementing the key
                this.operationFormKey++;

                // Show success message
                await swal.fire({
                    icon: 'success',
                    title: 'Success!',
                    text: 'Operation saved successfully',
                    timer: 2000,
                    showConfirmButton: false,
                });
            }
        },
        cancelOperationEdit() {
            // Just refresh the operation data to discard changes
            this.refreshOperation();
        },

        formatDate(dateString) {
            if (!dateString) return 'N/A';
            const date = new Date(dateString);
            return date.toLocaleDateString('en-AU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
        },

        async toggleTreatments() {
            this.showTreatments = !this.showTreatments;

            if (this.showTreatments) {
                await this.refreshTreatments();
            }
        },

        async refreshTreatments() {
            if (!this.showTreatments) return;

            this.treatmentsLoading = true;
            try {
                if (this.$refs.treatmentsTable) {
                    this.$refs.treatmentsTable.refreshData();
                }
            } catch (error) {
                console.error('Error refreshing treatments:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Refresh Failed',
                    text: 'Failed to refresh treatments data',
                    confirmButtonText: 'OK',
                });
            } finally {
                this.treatmentsLoading = false;
            }
        },

        async toggleOperations() {
            this.showOperations = !this.showOperations;

            if (this.showOperations) {
                await this.refreshOperation();
            }
        },

        async toggleAdditionalFields() {
            console.log(
                'toggleAdd: 1 - Current state:',
                this.showAdditionalFields
            );

            if (this.showAdditionalFields && this.$refs.additionalFields) {
                console.log(
                    'toggleAdd: 2 - Checking for changes before collapse'
                );
                const hasChanges =
                    this.$refs.additionalFields.checkForChanges();
                console.log('toggleAdd: 3 - Has changes:', hasChanges);

                if (hasChanges) {
                    console.log('toggleAdd: 4 - Auto-saving changes');
                    await this.autoSaveAdditionalFields();
                }
            }

            this.showAdditionalFields = !this.showAdditionalFields;
            console.log('toggleAdd: 5 - New state:', this.showAdditionalFields);
        },

        async autoSaveAdditionalFields() {
            console.log('autoSaveAdditionalFields: 1 - Starting auto-save');
            try {
                const additionalFormData =
                    this.$refs.additionalFields.getFormDataForAPI();
                const mainFormData = this.$refs.cohortForm
                    ? this.$refs.cohortForm.formData
                    : {};

                const combinedData = {
                    ...mainFormData,
                    ...additionalFormData,
                };

                console.log(
                    'autoSaveAdditionalFields: 2 - Combined data:',
                    combinedData
                );

                if (!combinedData.obj_code || !combinedData.regen_method) {
                    console.log(
                        'autoSaveAdditionalFields: 3 - Missing required fields, skipping save'
                    );
                    await swal.fire({
                        icon: 'warning',
                        title: 'Validation Warning',
                        text: 'Objective Code and Regeneration Method are required fields',
                        confirmButtonText: 'OK',
                    });
                    return;
                }

                const url = `${api_endpoints.cohorts}${this.cohortData.cohort_id}/`;
                console.log(
                    'autoSaveAdditionalFields: 4 - Making API call to:',
                    url
                );

                const response = await fetch(url, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify(combinedData),
                });

                if (response.ok) {
                    const updatedData = await response.json();
                    this.cohortData = { ...this.cohortData, ...updatedData };
                    this.$refs.additionalFields.resetChangeTracking();
                    console.log(
                        'autoSaveAdditionalFields: 5 - Auto-save successful'
                    );

                    await swal.fire({
                        icon: 'success',
                        title: 'Auto-saved!',
                        text: 'Additional fields saved automatically',
                        timer: 2000,
                        showConfirmButton: false,
                    });
                } else {
                    console.error(
                        'autoSaveAdditionalFields: 6 - API error:',
                        response.status
                    );
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            } catch (error) {
                console.error('autoSaveAdditionalFields: 7 - Error:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Auto-save Failed',
                    text: 'Failed to auto-save additional fields',
                    confirmButtonText: 'OK',
                });
            }
        },

        async saveAllFields() {
            this.saving = true;
            this.error = null;

            try {
                const mainFormData = this.$refs.cohortForm
                    ? this.$refs.cohortForm.formData
                    : {};
                const additionalFormData = this.$refs.additionalFields
                    ? this.$refs.additionalFields.getFormDataForAPI()
                    : {};

                const combinedData = {
                    ...mainFormData,
                    ...additionalFormData,
                };

                console.log('Saving combined data:', combinedData);

                if (!this.validateFormData(combinedData)) {
                    const messages = this.validationErrors
                        .map((e) => `<li>${e.message}</li>`)
                        .join('');
                    await swal.fire({
                        icon: 'warning',
                        title: 'Validation Error',
                        html: `<div style="text-align: left;">Please fix the following:<ul>${messages}</ul></div>`,
                        confirmButtonText: 'OK',
                    });
                    return false;
                }

                const url = `${api_endpoints.cohorts}${this.cohortData.cohort_id}/`;
                const response = await fetch(url, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify(combinedData),
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(
                        `HTTP error! status: ${response.status}, response: ${errorText}`
                    );
                }

                const updatedData = await response.json();
                this.cohortData = { ...this.cohortData, ...updatedData };
                this.hasUnsavedChanges = false;

                if (this.$refs.additionalFields) {
                    this.$refs.additionalFields.resetChangeTracking();
                }

                console.log('All fields saved successfully:', updatedData);

                return true;
            } catch (error) {
                console.error('Error saving all fields:', error);
                this.error = `Failed to save changes: ${error.message}`;
                await swal.fire({
                    icon: 'error',
                    title: 'Save Failed',
                    text: `Failed to save changes: ${error.message}`,
                    confirmButtonText: 'OK',
                });
                return false;
            } finally {
                this.saving = false;
            }
        },

        async saveAndContinue() {
            const success = await this.saveAllFields();
            if (success) {
                await swal.fire({
                    icon: 'success',
                    title: 'Saved!',
                    text: 'Changes saved successfully',
                    timer: 3000,
                    showConfirmButton: false,
                });
                this.$emit('success', 'Changes saved successfully');
            }
        },

        async saveAndExit() {
            const success = await this.saveAllFields();
            if (success) {
                this.$router.go(-1);
                await swal.fire({
                    icon: 'success',
                    title: 'Saved!',
                    text: 'Changes saved successfully',
                    timer: 2000,
                    showConfirmButton: false,
                });
            }
        },

        confirmCancel() {
            if (this.hasUnsavedChanges) {
                this.showCancelConfirm = true;
            } else {
                this.cancelChanges();
            }
        },

        cancelChanges() {
            this.showCancelConfirm = false;
            this.$router.go(-1);
        },

        loadUserPermissions() {
            this.fetchCurrentUser().then((user) => {
                if (user) {
                    this.userPermissions = user.groups || [];
                }
            });
        },

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

        markUnsavedChanges() {
            this.hasUnsavedChanges = true;
        },
    },
    mounted() {
        this.loadCohortData();
        this.loadUserPermissions();
        this.fetchValidationRules('forest_blocks.Cohort');

        window.addEventListener('beforeunload', this.beforeUnloadHandler);
    },
    beforeUnmount() {
        window.removeEventListener('beforeunload', this.beforeUnloadHandler);
    },
    beforeUnloadHandler(event) {
        if (this.hasUnsavedChanges) {
            event.preventDefault();
            event.returnValue =
                'You have unsaved changes. Are you sure you want to leave?';
        }
    },
    watch: {
        cohortId: {
            handler() {
                this.loadCohortData();
            },
            immediate: true,
        },
        '$route.params.cohortId': {
            handler() {
                this.loadCohortData();
            },
        },
    },
};
</script>

<style scoped>
.header-actions {
    display: flex;
    align-items: center;
    gap: 15px;
    flex-wrap: wrap;
}

.page-title {
    margin: 0;
    flex-grow: 1;
}

.card-header .btn-link {
    color: #333;
    font-weight: 600;
}

.card-header .btn-link:hover {
    color: #0056b3;
    text-decoration: none;
}

.card-header .btn-outline-info {
    border: none;
    font-size: 0.875rem;
    padding: 0.25rem 0.5rem;
}

.card-header .btn-outline-info:hover {
    background-color: #0dcaf0;
    color: white;
}

/* Sticky Action Buttons */
.sticky-action-buttons {
    position: sticky;
    bottom: 0;
    background: white;
    border-top: 1px solid #dee2e6;
    padding: 15px 0;
    margin-top: 20px;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    z-index: 1000;
}

.action-buttons-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 15px;
}

.action-buttons {
    display: flex;
    gap: 15px;
    justify-content: center;
    align-items: center;
    flex-wrap: wrap;
}

.action-buttons .btn-lg {
    min-width: 225px;
    padding: 12px 20px;
    font-size: 1rem;
    font-weight: 500;
}

.action-buttons-help {
    text-align: center;
    margin-top: 8px;
}

/* Badge styling */
.badge {
    font-size: 0.75rem;
}

/* Refresh button styling */
.btn-outline-secondary {
    border-color: #6c757d;
    color: #6c757d;
}

.btn-outline-secondary:hover {
    background-color: #6c757d;
    color: white;
}

/* Operation View Styles */
.operation-view dl {
    margin-bottom: 0;
}

.operation-view dt {
    font-weight: 600;
    color: #495057;
}

.operation-view dd {
    margin-bottom: 0.5rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .action-buttons {
        flex-direction: column;
        gap: 10px;
    }

    .action-buttons .btn-lg {
        min-width: 100%;
        width: 100%;
    }

    .header-actions {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }

    .page-title {
        font-size: 1.25rem;
    }

    .card-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }

    .card-header .btn-sm {
        align-self: flex-end;
    }

    .operation-view .row > div {
        margin-bottom: 1rem;
    }
}

/* Button icons */
.btn i {
    margin-right: 8px;
}

/* Success button specific styling */
.btn-success {
    background-color: #198754;
    border-color: #198754;
}

.btn-success:hover {
    background-color: #157347;
    border-color: #146c43;
}

/* Loading spinner for treatments */
.spinner-border-sm {
    width: 1rem;
    height: 1rem;
}

/* Operation inline form */
.operation-inline-form {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.375rem;
    border: 1px solid #dee2e6;
}

/* Alert styling */
.alert-info,
.alert-warning {
    margin-bottom: 0;
}
</style>
