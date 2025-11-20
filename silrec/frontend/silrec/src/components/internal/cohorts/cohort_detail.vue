<template>
  <div class="cohort-detail-container">
    <div v-if="debug">internal/proposals/cohorts/cohort_detail.vue</div>
    <div class="header-actions mb-4">
      <button class="btn btn-secondary" @click="confirmCancel">
        <i class="bi bi-arrow-left"></i> Back to Map
      </button>
      <h2 class="page-title">
        Cohort Details - 
        <span v-if="cohortData.obj_code">Objective: {{ cohortData.obj_code }}</span>
        <span v-else>Cohort {{ $route.params.cohortId }}</span>
      </h2>
      
      <!-- Add Treatment Button -->
      <router-link 
        v-if="canEdit"
        :to="`/internal/cohort/${$route.params.cohortId}/treatment/new`"
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
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">
              Cohort Information
              <button 
                type="button"
                class="btn btn-sm btn-outline-info ms-2"
                @click="showSystemInfo = true"
                title="View System Information"
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
                <i class="bi" :class="showAdditionalFields ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
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
    <div v-if="!loading && !error && cohortData.cohort_id" class="card mb-4">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="card-title mb-0">
          <button 
            type="button"
            class="btn btn-link p-0 border-0 text-decoration-none"
            @click="toggleTreatments"
          >
            <i class="bi" :class="showTreatments ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
            Treatments 
            <span class="badge bg-secondary ms-2">{{ treatmentsCount }}</span>
          </button>
        </h5>
        <div>
          <router-link 
            v-if="canEdit"
            :to="`/internal/cohort/${$route.params.cohortId}/treatment/new`"
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
            <span class="visually-hidden">Loading treatments...</span>
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

    <!-- Sticky Action Buttons -->
    <div v-if="!loading && !error && cohortData.cohort_id && canEdit" class="sticky-action-buttons">
      <div class="action-buttons-container">
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
            <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
            <i class="bi bi-check-circle"></i> {{ saving ? 'Saving...' : 'Save and Continue' }}
          </button>
          <button 
            type="button" 
            class="btn btn-success btn-lg"
            @click="saveAndExit"
            :disabled="saving"
          >
            <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
            <i class="bi bi-check-lg"></i> {{ saving ? 'Saving...' : 'Save' }}
          </button>
        </div>
        <div class="action-buttons-help">
          <small class="text-muted">
            <i class="bi bi-info-circle"></i> 
            Cancel: Discard all changes and return to map | 
            Save and Continue: Save changes and stay on this page | 
            Save: Save changes and return to map
          </small>
        </div>
      </div>
    </div>

    <!-- System Information Modal -->
    <div v-if="showSystemInfo" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">System Information</h5>
            <button type="button" class="btn-close" @click="showSystemInfo = false"></button>
          </div>
          <div class="modal-body">
            <SystemInformation 
              :cohort-data="cohortData"
            />
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showSystemInfo = false">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Cancel Confirmation Modal -->
    <div v-if="showCancelConfirm" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Confirm Cancel</h5>
            <button type="button" class="btn-close" @click="showCancelConfirm = false"></button>
          </div>
          <div class="modal-body">
            <p><i class="bi bi-exclamation-triangle text-warning"></i> All unsaved changes will be lost. Are you sure you want to cancel?</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCancelConfirm = false">
              Continue Editing
            </button>
            <button type="button" class="btn btn-danger" @click="cancelChanges">
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
import { api_endpoints, helpers } from '@/utils/hooks';

export default {
  name: 'CohortDetail',
  components: {
    CohortForm,
    AdditionalCohortFields,
    SystemInformation,
    TreatmentsTable
  },
  props: {
    proposal_id: {
      type: [Number, String],
      default: null
    },
    cohortId: {
      type: [Number, String],
      required: true
    },
    polygonId: {
      type: [Number, String],
      default: null
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      cohortData: {},
      userPermissions: [],
      showAdditionalFields: false,
      showTreatments: false,
      showSystemInfo: false,
      showCancelConfirm: false,
      additionalFieldsKey: 0,
      saving: false,
      readOnly: false,
      hasUnsavedChanges: false,
      treatmentsLoading: false,
      treatmentsCount: 0
    };
  },
  computed: {
    canEdit() {
      return true;
      const editRoles = ['Assessors', 'Reviewers', 'Silrec Admin'];
      return this.userPermissions.some(perm => editRoles.includes(perm));
    },
    debug: function () {
        if (this.$route.query.debug) {
            return this.$route.query.debug === 'true';
        }
        return false;
    },
  },
  methods: {
    async loadCohortData() {
        this.loading = true;
        this.error = null;
        
        try {
          // Use the prop cohortId instead of $route.params.cohortId
          const cohortId = this.cohortId || this.$route.params.cohortId;
          const url = `${api_endpoints.cohorts}${cohortId}/`;
          console.log('Loading cohort data from:', url);
          
          const response = await fetch(url);
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          this.cohortData = data;
          console.log('Cohort data loaded successfully:', this.cohortData);
          
        } catch (error) {
          console.error('Error loading cohort data:', error);
          this.error = 'Failed to load cohort data. Please check if the cohort exists.';
        } finally {
          this.loading = false;
        }
    },

    async toggleTreatments() {
      // Toggle the visibility
      this.showTreatments = !this.showTreatments;
      
      // If we're expanding the treatments section, refresh the data
      if (this.showTreatments) {
        await this.refreshTreatments();
      }
    },

    async refreshTreatments() {
      if (!this.showTreatments) return;
      
      this.treatmentsLoading = true;
      try {
        // Refresh the treatments table
        if (this.$refs.treatmentsTable) {
          this.$refs.treatmentsTable.refreshData();
        }
        
        // Also fetch the treatments count for the badge
        await this.loadTreatmentsCount();
        
      } catch (error) {
        console.error('Error refreshing treatments:', error);
      } finally {
        this.treatmentsLoading = false;
      }
    },

    async loadTreatmentsCount() {
      try {
        const cohortId = this.cohortId || this.$route.params.cohortId;
        const response = await fetch(`${api_endpoints.treatments}?cohort_id=${cohortId}`);
        
        if (response.ok) {
          const data = await response.json();
          // Handle both array and paginated responses
          if (Array.isArray(data)) {
            this.treatmentsCount = data.length;
          } else if (data.results) {
            this.treatmentsCount = data.results.length;
          } else if (data.data) {
            this.treatmentsCount = data.data.length;
          } else {
            this.treatmentsCount = 0;
          }
        }
      } catch (error) {
        console.error('Error loading treatments count:', error);
        this.treatmentsCount = 0;
      }
    },

    async toggleAdditionalFields() {
      console.log('toggleAdd: 1 - Current state:', this.showAdditionalFields);
      
      // If currently showing and about to collapse, check for changes
      if (this.showAdditionalFields && this.$refs.additionalFields) {
        console.log('toggleAdd: 2 - Checking for changes before collapse');
        const hasChanges = this.$refs.additionalFields.checkForChanges();
        console.log('toggleAdd: 3 - Has changes:', hasChanges);
        
        if (hasChanges) {
          console.log('toggleAdd: 4 - Auto-saving changes');
          await this.autoSaveAdditionalFields();
        }
      }
      
      // Toggle the visibility
      this.showAdditionalFields = !this.showAdditionalFields;
      console.log('toggleAdd: 5 - New state:', this.showAdditionalFields);
    },

    async autoSaveAdditionalFields() {
      console.log('autoSaveAdditionalFields: 1 - Starting auto-save');
      try {
        const additionalFormData = this.$refs.additionalFields.getFormDataForAPI();
        const mainFormData = this.$refs.cohortForm ? this.$refs.cohortForm.formData : {};
        
        const combinedData = {
          ...mainFormData,
          ...additionalFormData
        };

        console.log('autoSaveAdditionalFields: 2 - Combined data:', combinedData);

        if (!combinedData.obj_code || !combinedData.regen_method) {
          console.log('autoSaveAdditionalFields: 3 - Missing required fields, skipping save');
          return;
        }

        const url = `${api_endpoints.cohorts}${this.cohortData.cohort_id}/`;
        console.log('autoSaveAdditionalFields: 4 - Making API call to:', url);
        
        const response = await fetch(url, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify(combinedData)
        });

        if (response.ok) {
          const updatedData = await response.json();
          this.cohortData = { ...this.cohortData, ...updatedData };
          this.$refs.additionalFields.resetChangeTracking();
          console.log('autoSaveAdditionalFields: 5 - Auto-save successful');
        } else {
          console.error('autoSaveAdditionalFields: 6 - API error:', response.status);
        }
      } catch (error) {
        console.error('autoSaveAdditionalFields: 7 - Error:', error);
      }
    },

    async saveAllFields() {
      this.saving = true;
      this.error = null;
      
      try {
        // Get data from both form components
        const mainFormData = this.$refs.cohortForm ? this.$refs.cohortForm.formData : {};
        const additionalFormData = this.$refs.additionalFields ? this.$refs.additionalFields.getFormDataForAPI() : {};
        
        // Combine all data
        const combinedData = {
          ...mainFormData,
          ...additionalFormData
        };

        console.log('Saving combined data:', combinedData);

        // Validate required fields
        if (!combinedData.obj_code) {
          throw new Error('Objective Code is required');
        }
        if (!combinedData.regen_method) {
          throw new Error('Regeneration Method is required');
        }

        const url = `${api_endpoints.cohorts}${this.cohortData.cohort_id}/`;
        const response = await fetch(url, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify(combinedData)
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP error! status: ${response.status}, response: ${errorText}`);
        }

        const updatedData = await response.json();
        this.cohortData = { ...this.cohortData, ...updatedData };
        this.hasUnsavedChanges = false;
        
        // Reset change tracking in additional fields
        if (this.$refs.additionalFields) {
          this.$refs.additionalFields.resetChangeTracking();
        }
        
        console.log('All fields saved successfully:', updatedData);
        
        return true;
        
      } catch (error) {
        console.error('Error saving all fields:', error);
        this.error = `Failed to save changes: ${error.message}`;
        return false;
      } finally {
        this.saving = false;
      }
    },

    async saveAndContinue() {
      const success = await this.saveAllFields();
      if (success) {
        this.$emit('success', 'Changes saved successfully');
      }
    },

    async saveAndExit() {
      const success = await this.saveAllFields();
      if (success) {
        this.$router.push('/');
      }
    },

    confirmCancel() {
      this.showCancelConfirm = true;
    },

    cancelChanges() {
      this.showCancelConfirm = false;
      this.$router.push('/');
    },
    
    loadUserPermissions() {
      this.userPermissions = helpers.getUserPermissions();
    },

    getCSRFToken() {
      const name = 'csrftoken';
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    },

    // Detect unsaved changes (you can enhance this with form change detection)
    markUnsavedChanges() {
      this.hasUnsavedChanges = true;
    }
  },
  mounted() {
    this.loadCohortData();
    //this.loadUserPermissions();
    
    // Load treatments count initially
    this.loadTreatmentsCount();
    
    // Add beforeunload handler to warn about unsaved changes
    window.addEventListener('beforeunload', this.beforeUnloadHandler);
  },
  beforeUnmount() {
    // Remove the beforeunload handler
    window.removeEventListener('beforeunload', this.beforeUnloadHandler);
  },
  beforeUnloadHandler(event) {
    if (this.hasUnsavedChanges) {
      event.preventDefault();
      event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
  },
  watch: {
    // Watch both the prop and route param for cohortId changes
    cohortId: {
      handler() {
        this.loadCohortData();
        this.loadTreatmentsCount();
      },
      immediate: true
    },
    '$route.params.cohortId': {
      handler() {
        this.loadCohortData();
        this.loadTreatmentsCount();
      }
    }
  }
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
  min-width: 180px;
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
</style>
