<template>
  <div class="treatment-form">
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
              <option v-for="task in tasks" :key="task.id" :value="task.id">
                {{ task.name }}
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
          <h6>Additional Treatment Details</h6>
          <router-link 
            v-if="!readOnly"
            :to="`/internal/treatment/${treatmentId}/extra/new`"
            class="btn btn-outline-primary btn-sm"
          >
            <i class="bi bi-plus"></i> Add Details
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
          const response = await this.$http.get(`${api_endpoints.treatments}${this.treatmentId}/`);
          this.treatmentData = { ...response.data };
        } catch (error) {
          console.error('Error loading treatment data:', error);
          this.$emit('error', 'Failed to load treatment data');
        }
      }
    },
    async loadTasks() {
      try {
        const response = await this.$http.get(api_endpoints.tasks);
        this.tasks = response.data;
      } catch (error) {
        console.error('Error loading tasks:', error);
        this.$emit('error', 'Failed to load task list');
      }
    },
    async saveTreatment() {
      if (!this.validateForm()) {
        return;
      }

      this.saving = true;
      try {
        let response;
        if (this.treatmentId) {
          response = await this.$http.put(
            `${api_endpoints.treatments}${this.treatmentId}/`,
            this.treatmentData
          );
        } else {
          response = await this.$http.post(api_endpoints.treatments, this.treatmentData);
        }
        this.$emit('treatment-saved', response.data);
        this.$emit('success', `Treatment ${this.treatmentId ? 'updated' : 'created'} successfully`);
      } catch (error) {
        console.error('Error saving treatment:', error);
        this.handleSaveError(error);
      } finally {
        this.saving = false;
      }
    },
    validateForm() {
      if (!this.treatmentData.task) {
        this.$emit('error', 'Task is required');
        return false;
      }
      
      if (this.treatmentData.plan_mth && (this.treatmentData.plan_mth < 1 || this.treatmentData.plan_mth > 12)) {
        this.$emit('error', 'Planned month must be between 1 and 12');
        return false;
      }
      
      if (this.treatmentData.pct_area && (this.treatmentData.pct_area < 0 || this.treatmentData.pct_area > 100)) {
        this.$emit('error', 'Area percentage must be between 0 and 100');
        return false;
      }
      
      return true;
    },
    handleSaveError(error) {
      let errorMessage = 'Failed to save treatment';
      if (error.response && error.response.data) {
        const errors = error.response.data;
        if (typeof errors === 'object') {
          errorMessage = Object.values(errors).flat().join(', ');
        } else {
          errorMessage = errors;
        }
      }
      this.$emit('error', errorMessage);
    },
    cancel() {
      this.$emit('cancel');
    },
    refreshExtras() {
      // This will be handled by the TreatmentExtrasTable component itself
      // through its internal data loading
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
