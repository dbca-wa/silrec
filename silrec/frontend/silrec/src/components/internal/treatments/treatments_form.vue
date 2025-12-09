<template>
  <div class="treatment-form">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/treatments/treatments_form.vue</div>
    <form @submit.prevent="saveTreatment">
      <!-- Existing form fields remain the same -->
      <div class="row">
        <div class="col-md-6">
          <div class="form-group">
            <label for="task">Task *</label>
            <select
              id="task"
              v-model="treatmentData.task"
              class="form-select"
              :disabled="readOnly"
              required
            >
              <option value="">Select Task</option>
              <option v-for="task in tasks" :key="task.id" :value="task.task">
                {{ task.task_name }} ({{ task.task }})
              </option>
            </select>
          </div>
        </div>
        <div class="col-md-6">
          <div class="form-group">
            <label for="status">Status</label>
            <select
              id="status"
              v-model="treatmentData.status"
              class="form-select"
              :disabled="readOnly"
            >
              <option value="P">Planned</option>
              <option value="D">Completed</option>
              <option value="C">Cancelled</option>
              <option value="F">Failed</option>
              <option value="W">Written Off</option>
              <option value="X">Not Required</option>
            </select>
          </div>
        </div>
      </div>

      <div class="row mt-3">
        <div class="col-md-4">
          <div class="form-group">
            <label for="planYear">Planned Year</label>
            <input
              id="planYear"
              v-model.number="treatmentData.plan_yr"
              type="number"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="planMonth">Planned Month</label>
            <input
              id="planMonth"
              v-model.number="treatmentData.plan_mth"
              type="number"
              min="1"
              max="12"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="pctArea">Area Percentage</label>
            <input
              id="pctArea"
              v-model.number="treatmentData.pct_area"
              type="number"
              min="0"
              max="100"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
      </div>

      <div class="row mt-3">
        <div class="col-md-6">
          <div class="form-group">
            <label for="completeDate">Complete Date</label>
            <input
              id="completeDate"
              v-model="treatmentData.complete_date"
              type="date"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
        <div class="col-md-6">
          <div class="form-group">
            <label for="organisation">Organisation</label>
            <input
              id="organisation"
              v-model="treatmentData.organisation"
              type="text"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
      </div>

      <div class="row mt-3">
        <div class="col-md-12">
          <div class="form-group">
            <label for="results">Results</label>
            <textarea
              id="results"
              v-model="treatmentData.results"
              class="form-control"
              rows="3"
              :readonly="readOnly"
              placeholder="Describe the treatment results or observations..."
            ></textarea>
          </div>
        </div>
      </div>

      <div class="row mt-3">
        <div class="col-md-12">
          <div class="form-group">
            <label for="reference">Reference</label>
            <input
              id="reference"
              v-model="treatmentData.reference"
              type="text"
              class="form-control"
              :readonly="readOnly"
              placeholder="URL, report title, or other reference"
            />
          </div>
        </div>
      </div>

      <!-- Prescriptions Section - Now Collapsible -->
      <!--
      <div class="mt-4" v-if="treatmentId && !isNew">
        <div class="card">
          <div class="card-header bg-light">
            <h6 class="mb-0">
              <button 
                class="btn btn-link btn-sm text-decoration-none" 
                type="button" 
                @click="togglePrescriptionCollapse"
              >
                <i class="bi" :class="prescriptionCollapsed ? 'bi-chevron-down' : 'bi-chevron-up'"></i>
                Prescription Details
              </button>
            </h6>
          </div>
          
          <div v-if="!prescriptionCollapsed" class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <span class="text-muted">Prescribed tasks and timing for this treatment</span>
              <button 
                v-if="!treatmentData.prescription && !readOnly" 
                type="button"
                class="btn btn-outline-primary btn-sm"
                @click="showNewPrescriptionForm"
              >
                <i class="bi bi-plus"></i> Add New Prescription
              </button>
            </div>
            
            <PrescriptionForm
              v-if="treatmentData.prescription || showPrescriptionForm"
              :prescription-id="treatmentData.prescription"
              :treatment-id="treatmentId"
              :read-only="readOnly"
              @prescription-saved="handlePrescriptionSaved"
              @cancel="handlePrescriptionCancel"
            />
          </div>
        </div>
      </div>
      -->

      <!-- Treatment Extras Section -->
      <div class="mt-4" v-if="treatmentId && !isNew">
        <div class="card">
          <div class="card-header bg-light">
            <h6 class="mb-0">
              <button 
                class="btn btn-link btn-sm text-decoration-none" 
                type="button" 
                @click="toggleExtrasCollapse"
              >
                <i class="bi" :class="extrasCollapsed ? 'bi-chevron-down' : 'bi-chevron-up'"></i>
                Treatment Extra Details
              </button>
            </h6>
          </div>
          
          <div v-if="!extrasCollapsed" class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <span class="text-muted">Additional treatment information and attributes</span>
              <router-link 
                v-if="!readOnly"
                :to="`/internal/treatment/${treatmentId}/extra/new`"
                class="btn btn-outline-primary btn-sm"
              >
                <i class="bi bi-plus"></i> Add Treatment Extra Details
              </router-link>
            </div>
            
            <TreatmentExtrasTable
              :treatment-id="treatmentId"
              :read-only="readOnly"
              @extra-updated="refreshExtras"
            />
          </div>
        </div>
      </div>

    </form>

    <!-- Silviculturist Comments Section -->
    <div class="mt-4" v-if="treatmentId && !isNew">
        <div class="card">
          <div class="card-header bg-light">
            <h6 class="mb-0">
              <button 
                class="btn btn-link btn-sm text-decoration-none" 
                type="button" 
                @click="toggleCommentsCollapse"
              >
                <i class="bi" :class="commentsCollapsed ? 'bi-chevron-down' : 'bi-chevron-up'"></i>
                Silviculturist Comments
              </button>
            </h6>
          </div>
          
          <div v-if="!commentsCollapsed" class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <span class="text-muted">Comments and observations from silviculturists</span>
              <button 
                v-if="!readOnly"
                type="button"
                class="btn btn-outline-primary btn-sm"
                @click="addNewComment"
              >
                <i class="bi bi-plus"></i> Add New Silviculturist Comment
              </button>
            </div>
            
            <SilviculturistComment
              ref="silviculturistComment"
              :treatment-id="treatmentId"
              :read-only="readOnly"
              @comment-updated="refreshComments"
            />
          </div>
        </div>
      </div>

    <!-- Survey/Assessment Section -->
    <div class="mt-4" v-if="treatmentId && !isNew">
      <div class="card">
        <div class="card-header bg-light">
          <h6 class="mb-0">
            <button 
              class="btn btn-link btn-sm text-decoration-none" 
              type="button" 
              @click="toggleSurveyCollapse"
            >
              <i class="bi" :class="surveyCollapsed ? 'bi-chevron-down' : 'bi-chevron-up'"></i>
              Survey/Assessment Documents
            </button>
          </h6>
        </div>
        
        <div v-if="!surveyCollapsed" class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <span class="text-muted">Upload documents, images, or add URLs for surveys and assessments</span>
            <button 
              v-if="!readOnly"
              type="button"
              class="btn btn-outline-primary btn-sm"
              @click="addNewDocument"
            >
              <i class="bi bi-plus"></i> Add Document/URL
            </button>
          </div>
          
          <SurveyAssessment
            ref="surveyAssessment"
            :treatment-id="treatmentId"
            :read-only="readOnly"
            @document-updated="refreshDocuments"
          />
        </div>
      </div>
    </div>

      <!-- Action Buttons -->
      <div v-if="!readOnly" class="mt-4">
        <button type="submit" class="btn btn-primary me-2" :disabled="saving">
          <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
          {{ saving ? 'Saving...' : (treatmentId ? 'Update Treatment' : 'Save Treatment') }}
        </button>
        <button type="button" class="btn btn-secondary" @click="cancel">
          Cancel
        </button>
    </div>
  </div>
</template>

<script>
import TreatmentExtrasTable from './treatments_extras_table.vue';
import PrescriptionForm from './prescription_form.vue';
import SilviculturistComment from './silviculturist_comment.vue';
import SurveyAssessment from './survey_assessment.vue';
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'TreatmentForm',
  components: {
    TreatmentExtrasTable,
    PrescriptionForm,
    SilviculturistComment,
    SurveyAssessment,
  },
  props: {
    treatmentId: {
      type: [Number, String],
      default: null
    },
    cohortId: {
      type: [Number, String],
      required: true
    },
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      treatmentData: {
        task: '',
        status: 'P',
        plan_yr: null,
        plan_mth: null,
        pct_area: null,
        complete_date: null,
        results: '',
        reference: '',
        organisation: '',
        cohort: this.cohortId,
        prescription: null
      },
      tasks: [],
      saving: false,
      showPrescriptionForm: false,
      prescriptionCollapsed: true, // Add this and set to true by default
      extrasCollapsed: true,
      commentsCollapsed: true,
      surveyCollapsed: true,
    };
  },
  computed: {
    isNew() {
      return !this.treatmentId;
    }
  },
  methods: {
    // Add method to toggle prescription collapse
    togglePrescriptionCollapse() {
      this.prescriptionCollapsed = !this.prescriptionCollapsed;
    },
    toggleCommentsCollapse() {
      this.commentsCollapsed = !this.commentsCollapsed;
    },
    addNewComment() {
      if (this.$refs.silviculturistComment) {
        this.$refs.silviculturistComment.addNewComment();
      }
    },
    refreshComments() {
      if (this.$refs.silviculturistComment) {
        this.$refs.silviculturistComment.loadComments();
      }
    },
    toggleExtrasCollapse() {
      this.extrasCollapsed = !this.extrasCollapsed;
    },
    async loadTreatmentData() {
        if (this.treatmentId) {
            try {
                const response = await fetch(`${api_endpoints.treatments}${this.treatmentId}/`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                
                // Format the complete_date for the date input
                if (data.complete_date) {
                    data.complete_date = data.complete_date.split('T')[0];
                }
                
                this.treatmentData = { ...data };
            } catch (error) {
                console.error('Error loading treatment data:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Load Failed',
                    text: 'Failed to load treatment data',
                    confirmButtonText: 'OK'
                });
            }
        }
    },
    showNewPrescriptionForm() {
      this.showPrescriptionForm = true;
      // Auto-expand the prescription section when adding new prescription
      this.prescriptionCollapsed = false;
    },
    handlePrescriptionSaved(prescriptionData) {
      this.treatmentData.prescription = prescriptionData.prescription_id;
      this.showPrescriptionForm = false;
      
      swal.fire({
        icon: 'success',
        title: 'Prescription Added',
        text: 'Prescription has been successfully linked to this treatment',
        timer: 3000,
        showConfirmButton: false
      });
    },
    handlePrescriptionCancel() {
      this.showPrescriptionForm = false;
    },
    async loadTasks() {
        try {
            const response = await fetch(api_endpoints.tasks);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.tasks = data.results || data;
        } catch (error) {
            console.error('Error loading tasks:', error);
            await swal.fire({
                icon: 'error',
                title: 'Load Failed',
                text: 'Failed to load task list',
                confirmButtonText: 'OK'
            });
        }
    },
    async saveTreatment() {
        if (!this.validateForm()) {
            return;
        }

        this.saving = true;
        try {
            let url, method;
            if (this.treatmentId) {
                url = `${api_endpoints.treatments}${this.treatmentId}/`;
                method = 'PUT';
            } else {
                url = api_endpoints.treatments;
                method = 'POST';
            }

            console.log('Saving treatment data:', this.treatmentData);
            console.log('URL:', url, 'Method:', method);

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(this.treatmentData)
            });

            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);

            const responseClone = response.clone();
            
            if (!response.ok) {
                let errorDetail = '';
                try {
                    const errorData = await responseClone.json();
                    errorDetail = JSON.stringify(errorData);
                } catch (e) {
                    try {
                        errorDetail = await responseClone.text();
                    } catch (textError) {
                        errorDetail = 'Could not read error response';
                    }
                }
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorDetail}`);
            }

            const responseData = await response.json();
            console.log('Treatment saved successfully:', responseData);
            
            this.$emit('treatment-saved', responseData);
            
            await swal.fire({
                icon: 'success',
                title: 'Success!',
                text: `Treatment ${this.treatmentId ? 'updated' : 'created'} successfully`,
                timer: 3000,
                showConfirmButton: false
            });
        } catch (error) {
            console.error('Error saving treatment:', error);
            await this.handleSaveError(error);
        } finally {
            this.saving = false;
        }
    },
    validateForm() {
        if (!this.treatmentData.task) {
            swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'Task is required',
                confirmButtonText: 'OK'
            });
            return false;
        }
        
        if (this.treatmentData.plan_mth && (this.treatmentData.plan_mth < 1 || this.treatmentData.plan_mth > 12)) {
            swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'Planned month must be between 1 and 12',
                confirmButtonText: 'OK'
            });
            return false;
        }
        
        if (this.treatmentData.pct_area && (this.treatmentData.pct_area < 0 || this.treatmentData.pct_area > 100)) {
            swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'Area percentage must be between 0 and 100',
                confirmButtonText: 'OK'
            });
            return false;
        }
        
        return true;
    },
    async handleSaveError(error) {
        let errorMessage = 'Failed to save treatment';
        
        if (error.message && error.message.includes('403')) {
            errorMessage = 'You do not have permission to create or update treatments. Please contact an administrator.';
        } else if (error.message && error.message.includes('details:')) {
            try {
                const details = error.message.split('details:')[1];
                try {
                    const errorData = JSON.parse(details);
                    if (typeof errorData === 'object') {
                        if (errorData.error) {
                            errorMessage = errorData.error;
                        } else {
                            errorMessage = Object.values(errorData).flat().join(', ');
                        }
                    } else {
                        errorMessage = details;
                    }
                } catch (e) {
                    errorMessage = details;
                }
            } catch (e) {
                errorMessage = error.message;
            }
        } else {
            errorMessage = error.message || 'Unknown error occurred';
        }
        
        await swal.fire({
            icon: 'error',
            title: 'Save Error',
            text: errorMessage,
            confirmButtonText: 'OK',
            confirmButtonColor: '#d33'
        });
    },
    cancel() {
        this.$emit('cancel');
    },
    refreshExtras() {
        // This will be handled by the TreatmentExtrasTable component itself
    },

    // Add to data() in treatments_form.vue
    //surveyCollapsed: true,

    // Add to methods in treatments_form.vue
    toggleSurveyCollapse() {
      this.surveyCollapsed = !this.surveyCollapsed;
    },
    addNewDocument() {
      if (this.$refs.surveyAssessment) {
        this.$refs.surveyAssessment.addNewDocument();
      }
    },
    refreshDocuments() {
      if (this.$refs.surveyAssessment) {
        this.$refs.surveyAssessment.loadDocuments();
      }
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
    }
  },
  mounted() {
    this.loadTasks();
    if (this.treatmentId) {
      this.loadTreatmentData();
    }
  },
  watch: {
    treatmentId: {
      handler(newVal) {
        if (newVal) {
          this.loadTreatmentData();
        } else {
          this.treatmentData = {
            task: '',
            status: 'P',
            plan_yr: null,
            plan_mth: null,
            pct_area: null,
            complete_date: null,
            results: '',
            reference: '',
            organisation: '',
            cohort: this.cohortId,
            prescription: null
          };
          this.showPrescriptionForm = false;
          this.prescriptionCollapsed = true;
          this.extrasCollapsed = true;
          this.commentsCollapsed = true;
        }
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
.treatment-form {
  max-width: 100%;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.form-control:read-only,
.form-select:disabled {
  background-color: #e9ecef;
  opacity: 1;
}

.btn {
  min-width: 100px;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

/* Styles for collapsible sections */
.card-header {
  padding: 0.5rem 1rem;
}

.btn-link {
  color: #495057;
  font-weight: 500;
}

.btn-link:hover {
  color: #0056b3;
  text-decoration: none;
}
</style>
