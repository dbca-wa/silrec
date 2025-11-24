<template>
  <div class="treatment-form">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/treatments/treatments_form.vue</div>
    <form @submit.prevent="saveTreatment">
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

      <!-- Treatment Extras Section -->
      <div class="mt-4" v-if="treatmentId && !isNew">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h6>Treatment Extra Details</h6>
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
    </form>
  </div>
</template>

<script>
import TreatmentExtrasTable from './treatments_extras_table.vue';
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'TreatmentForm',
  components: {
    TreatmentExtrasTable
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
        cohort: this.cohortId
      },
      tasks: [],
      saving: false
    };
  },
  computed: {
    isNew() {
      return !this.treatmentId;
    }
  },
  methods: {
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
                    data.complete_date = data.complete_date.split('T')[0]; // Extract just the date part
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

            // Clone the response before reading it to avoid "body stream already read" error
            const responseClone = response.clone();
            
            if (!response.ok) {
                let errorDetail = '';
                try {
                    // Try to parse as JSON first
                    const errorData = await responseClone.json();
                    errorDetail = JSON.stringify(errorData);
                } catch (e) {
                    // If JSON parsing fails, try as text
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
            
            // Show success message
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
        
        // Check if it's a permission error
        if (error.message && error.message.includes('403')) {
            errorMessage = 'You do not have permission to create or update treatments. Please contact an administrator.';
        } 
        // Check if it's a validation error from the server
        else if (error.message && error.message.includes('details:')) {
            try {
                const details = error.message.split('details:')[1];
                // Try to parse the details as JSON for structured errors
                try {
                    const errorData = JSON.parse(details);
                    if (typeof errorData === 'object') {
                        // Handle Django REST framework validation errors
                        if (errorData.error) {
                            errorMessage = errorData.error;
                        } else {
                            errorMessage = Object.values(errorData).flat().join(', ');
                        }
                    } else {
                        errorMessage = details;
                    }
                } catch (e) {
                    // If not JSON, use the raw details
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
          // Reset form for new treatment
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
            cohort: this.cohortId
          };
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
</style>
