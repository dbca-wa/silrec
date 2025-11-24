<template>
  <div class="prescription-form">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/treatments/prescription_form.vue</div>
    
    <div class="card">
      <div class="card-header bg-light">
        <h6 class="mb-0">
          <button 
            class="btn btn-link btn-sm text-decoration-none" 
            type="button" 
            @click="toggleCollapse"
          >
            <i class="bi" :class="isCollapsed ? 'bi-chevron-down' : 'bi-chevron-up'"></i>
            {{ isNew ? 'Add New Prescription' : 'Edit Prescription' }}
          </button>
        </h6>
      </div>
      
      <div v-if="!isCollapsed" class="card-body">
        <form @submit.prevent="savePrescription">
          <div class="row">
            <div class="col-md-6">
              <div class="form-group">
                <label for="objCode">Objective Code *</label>
                <select
                  id="objCode"
                  v-model="prescriptionData.obj_code"
                  class="form-select"
                  :disabled="readOnly"
                  required
                >
                  <option value="">Select Objective</option>
                  <option v-for="objective in objectives" :key="objective.obj_code" :value="objective.obj_code">
                    {{ objective.description }} ({{ objective.obj_code }})
                  </option>
                </select>
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group">
                <label for="sequence">Sequence *</label>
                <input
                  id="sequence"
                  v-model.number="prescriptionData.sequence"
                  type="number"
                  min="1"
                  class="form-control"
                  :readonly="readOnly"
                  required
                />
              </div>
            </div>
          </div>

          <div class="row mt-3">
            <div class="col-md-6">
              <div class="form-group">
                <label for="prescriptionTask">Task *</label>
                <select
                  id="prescriptionTask"
                  v-model="prescriptionData.task"
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
                <label for="year">Years From Operation</label>
                <input
                  id="year"
                  v-model.number="prescriptionData.year"
                  type="number"
                  min="0"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
          </div>

          <div class="row mt-3">
            <div class="col-md-4">
              <div class="form-group">
                <label for="responsibility">Responsibility</label>
                <select
                  id="responsibility"
                  v-model="prescriptionData.responsibility"
                  class="form-select"
                  :disabled="readOnly"
                >
                  <option value="">Select Organisation</option>
                  <option v-for="org in organisations" :key="org.id" :value="org.id">
                    {{ org.description }}
                  </option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="areaPct">Area Percentage</label>
                <input
                  id="areaPct"
                  v-model.number="prescriptionData.area_pct"
                  type="number"
                  min="0"
                  max="100"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="mandatory">Mandatory</label>
                <select
                  id="mandatory"
                  v-model="prescriptionData.mandatory"
                  class="form-select"
                  :disabled="readOnly"
                >
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
              </div>
            </div>
          </div>

          <div class="row mt-3">
            <div class="col-md-6">
              <div class="form-group">
                <label for="canReschedule">Can Reschedule</label>
                <select
                  id="canReschedule"
                  v-model="prescriptionData.can_reschedule"
                  class="form-select"
                  :disabled="readOnly"
                >
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group">
                <label for="done">Already Done</label>
                <select
                  id="done"
                  v-model="prescriptionData.done"
                  class="form-select"
                  :disabled="readOnly"
                >
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
              </div>
            </div>
          </div>

          <div class="row mt-3">
            <div class="col-md-12">
              <div class="form-group">
                <label for="prescriptionComment">Comment</label>
                <textarea
                  id="prescriptionComment"
                  v-model="prescriptionData.comment"
                  class="form-control"
                  rows="2"
                  :readonly="readOnly"
                  placeholder="Comments about this prescription..."
                ></textarea>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div v-if="!readOnly" class="mt-4">
            <button type="submit" class="btn btn-primary me-2" :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
              {{ saving ? 'Saving...' : (prescriptionId ? 'Update Prescription' : 'Save Prescription') }}
            </button>
            <button type="button" class="btn btn-secondary" @click="cancel">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'PrescriptionForm',
  props: {
    prescriptionId: {
      type: [Number, String],
      default: null
    },
    treatmentId: {
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
      prescriptionData: {
        obj_code: '',
        sequence: 1,
        task: '',
        year: null,
        responsibility: '',
        area_pct: 100,
        can_reschedule: true,
        mandatory: true,
        done: false,
        comment: ''
      },
      objectives: [],
      tasks: [],
      organisations: [],
      saving: false,
      isCollapsed: false
    };
  },
  computed: {
    isNew() {
      return !this.prescriptionId;
    }
  },
  methods: {
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed;
    },
    async loadPrescriptionData() {
      if (this.prescriptionId) {
        try {
          const response = await fetch(`${api_endpoints.prescriptions}${this.prescriptionId}/`);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          this.prescriptionData = { ...data };
        } catch (error) {
          console.error('Error loading prescription data:', error);
          await swal.fire({
            icon: 'error',
            title: 'Load Failed',
            text: 'Failed to load prescription data',
            confirmButtonText: 'OK'
          });
        }
      }
    },
    async loadObjectives() {
      try {
        const response = await fetch(api_endpoints.objectives);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        this.objectives = data.results || data;
      } catch (error) {
        console.error('Error loading objectives:', error);
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
      }
    },
    async loadOrganisations() {
      try {
        const response = await fetch(api_endpoints.organisations);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        this.organisations = data.results || data;
      } catch (error) {
        console.error('Error loading organisations:', error);
      }
    },
    async savePrescription() {
      if (!this.validateForm()) {
        return;
      }

      this.saving = true;
      try {
        let url, method;
        if (this.prescriptionId) {
          url = `${api_endpoints.prescriptions}${this.prescriptionId}/`;
          method = 'PUT';
        } else {
          url = api_endpoints.prescriptions;
          method = 'POST';
        }

        const response = await fetch(url, {
          method: method,
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify(this.prescriptionData)
        });

        if (!response.ok) {
          let errorDetail = '';
          try {
            const errorData = await response.clone().json();
            errorDetail = JSON.stringify(errorData);
          } catch (e) {
            try {
              errorDetail = await response.clone().text();
            } catch (textError) {
              errorDetail = 'Could not read error response';
            }
          }
          throw new Error(`HTTP error! status: ${response.status}, details: ${errorDetail}`);
        }

        const responseData = await response.json();
        
        // If this is a new prescription, update the treatment with the new prescription ID
        if (this.isNew && this.treatmentId) {
          await this.updateTreatmentWithPrescription(responseData.prescription_id);
        }

        this.$emit('prescription-saved', responseData);
        
        await swal.fire({
          icon: 'success',
          title: 'Success!',
          text: `Prescription ${this.prescriptionId ? 'updated' : 'created'} successfully`,
          timer: 3000,
          showConfirmButton: false
        });

        this.isCollapsed = true;

      } catch (error) {
        console.error('Error saving prescription:', error);
        await this.handleSaveError(error);
      } finally {
        this.saving = false;
      }
    },
    async updateTreatmentWithPrescription(prescriptionId) {
      try {
        const response = await fetch(`${api_endpoints.treatments}${this.treatmentId}/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.getCSRFToken()
          },
          body: JSON.stringify({
            prescription: prescriptionId
          })
        });

        if (!response.ok) {
          throw new Error(`Failed to update treatment with prescription: ${response.status}`);
        }

        console.log('Treatment updated with prescription ID:', prescriptionId);
      } catch (error) {
        console.error('Error updating treatment with prescription:', error);
        // Don't throw error here - prescription was created successfully
      }
    },
    validateForm() {
      if (!this.prescriptionData.obj_code) {
        swal.fire({
          icon: 'error',
          title: 'Validation Error',
          text: 'Objective code is required',
          confirmButtonText: 'OK'
        });
        return false;
      }
      
      if (!this.prescriptionData.sequence || this.prescriptionData.sequence < 1) {
        swal.fire({
          icon: 'error',
          title: 'Validation Error',
          text: 'Sequence must be at least 1',
          confirmButtonText: 'OK'
        });
        return false;
      }
      
      if (!this.prescriptionData.task) {
        swal.fire({
          icon: 'error',
          title: 'Validation Error',
          text: 'Task is required',
          confirmButtonText: 'OK'
        });
        return false;
      }
      
      if (this.prescriptionData.area_pct && (this.prescriptionData.area_pct < 0 || this.prescriptionData.area_pct > 100)) {
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
      let errorMessage = 'Failed to save prescription';
      
      if (error.message && error.message.includes('403')) {
        errorMessage = 'You do not have permission to create or update prescriptions. Please contact an administrator.';
      } else if (error.message && error.message.includes('details:')) {
        try {
          const details = error.message.split('details:')[1];
          try {
            const errorData = JSON.parse(details);
            if (typeof errorData === 'object') {
              errorMessage = errorData.error || Object.values(errorData).flat().join(', ');
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
      this.isCollapsed = true;
      this.$emit('cancel');
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
    this.loadObjectives();
    this.loadTasks();
    this.loadOrganisations();
    if (this.prescriptionId) {
      this.loadPrescriptionData();
    }
  },
  watch: {
    prescriptionId: {
      handler(newVal) {
        if (newVal) {
          this.loadPrescriptionData();
          this.isCollapsed = false;
        } else {
          this.prescriptionData = {
            obj_code: '',
            sequence: 1,
            task: '',
            year: null,
            responsibility: '',
            area_pct: 100,
            can_reschedule: true,
            mandatory: true,
            done: false,
            comment: ''
          };
        }
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
.prescription-form {
  margin-bottom: 1rem;
}

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

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}
</style>
