<template>
  <div class="treatment-extra-form">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/treatments/treatments_extras_form.vue</div>
    <form @submit.prevent="saveExtra">
      <div class="row">
        <div class="col-md-6">
          <div class="form-group mb-3">
            <label for="rescheduledReason" class="form-label">Reschedule Reason</label>
            <select
              id="rescheduledReason"
              v-model="formData.rescheduled_reason"
              class="form-select"
              :disabled="readOnly"
            >
              <option value="">Select Reason</option>
              <option value="weather">Weather Conditions</option>
              <option value="resource">Resource Availability</option>
              <option value="operational">Operational Issues</option>
              <option value="biological">Biological Factors</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        
        <div class="col-md-6">
          <div class="form-group mb-3">
            <label for="successRate" class="form-label">Success Rate (%)</label>
            <input
              id="successRate"
              v-model.number="formData.success_rate_pct"
              type="number"
              min="0"
              max="100"
              step="1"
              class="form-control"
              :readonly="readOnly"
            />
            <div class="form-text">Percentage of successful outcomes (0-100)</div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-md-6">
          <div class="form-group mb-3">
            <label for="stockingRate" class="form-label">Stocking Rate (sph)</label>
            <input
              id="stockingRate"
              v-model.number="formData.stocking_rate_spha"
              type="number"
              min="0"
              step="1"
              class="form-control"
              :readonly="readOnly"
            />
            <div class="form-text">Stems per hectare</div>
          </div>
        </div>
        
        <div class="col-md-6">
          <div class="form-group mb-3">
            <label for="speciesAssessed" class="form-label">Species Assessed</label>
            <input
              id="speciesAssessed"
              v-model="formData.api_species_assessed"
              type="text"
              class="form-control"
              :readonly="readOnly"
              placeholder="e.g., JAR, KAR, MAR"
            />
            <div class="form-text">API species code</div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-md-6">
          <div class="form-group mb-3">
            <label for="assessmentType" class="form-label">Assessment Type</label>
            <input
              id="assessmentType"
              v-model="formData.zassessment_type"
              type="text"
              class="form-control"
              :readonly="readOnly"
              placeholder="e.g., Regeneration, Survival"
            />
          </div>
        </div>
        
        <div class="col-md-6">
          <div class="form-group mb-3">
            <label for="resultStandard" class="form-label">Result Standard</label>
            <input
              id="resultStandard"
              v-model="formData.zresult_standard"
              type="text"
              class="form-control"
              :readonly="readOnly"
              placeholder="e.g., Adequate, Optimal"
            />
          </div>
        </div>
      </div>

      <!-- Planting Information -->
      <div class="card mt-3">
        <div class="card-header">
          <h6 class="card-title mb-0">Planting Information</h6>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <div class="form-group mb-3">
                <label for="species1Planted" class="form-label">Primary Species</label>
                <input
                  id="species1Planted"
                  v-model.number="formData.zspecies1_planted"
                  type="number"
                  class="form-control"
                  :readonly="readOnly"
                  placeholder="Species code"
                />
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group mb-3">
                <label for="plantingRate1" class="form-label">Primary Planting Rate (sph)</label>
                <input
                  id="plantingRate1"
                  v-model.number="formData.zplanting_rate1_spha"
                  type="number"
                  min="0"
                  step="1"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
          </div>
          
          <div class="row">
            <div class="col-md-6">
              <div class="form-group mb-3">
                <label for="species2Planted" class="form-label">Secondary Species</label>
                <input
                  id="species2Planted"
                  v-model.number="formData.zspecies2_planted"
                  type="number"
                  class="form-control"
                  :readonly="readOnly"
                  placeholder="Species code"
                />
              </div>
            </div>
            <div class="col-md-6">
              <div class="form-group mb-3">
                <label for="plantingRate2" class="form-label">Secondary Planting Rate (sph)</label>
                <input
                  id="plantingRate2"
                  v-model.number="formData.zplanting_rate2_spha"
                  type="number"
                  min="0"
                  step="1"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
          </div>
          
          <div class="row">
            <div class="col-md-12">
              <div class="form-group mb-3">
                <label for="seedSource" class="form-label">Seed Source</label>
                <input
                  id="seedSource"
                  v-model="formData.zseed_source"
                  type="text"
                  class="form-control"
                  :readonly="readOnly"
                  placeholder="e.g., Zone or Forest Block"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Additional Quantities -->
      <div class="card mt-3">
        <div class="card-header">
          <h6 class="card-title mb-0">Additional Measurements</h6>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-3">
              <div class="form-group mb-3">
                <label for="qty1" class="form-label">Quantity 1</label>
                <input
                  id="qty1"
                  v-model.number="formData.qty1"
                  type="number"
                  step="0.1"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group mb-3">
                <label for="qty2" class="form-label">Quantity 2</label>
                <input
                  id="qty2"
                  v-model.number="formData.qty2"
                  type="number"
                  step="0.1"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group mb-3">
                <label for="qty3" class="form-label">Quantity 3</label>
                <input
                  id="qty3"
                  v-model.number="formData.qty3"
                  type="number"
                  step="0.1"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-group mb-3">
                <label for="qty4" class="form-label">Quantity 4</label>
                <input
                  id="qty4"
                  v-model.number="formData.qty4"
                  type="number"
                  step="0.1"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Legacy Fields -->
      <div class="card mt-3">
        <div class="card-header">
          <h6 class="card-title mb-0">Legacy Information</h6>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-4">
              <div class="form-group mb-3">
                <label for="machineId" class="form-label">Machine ID</label>
                <input
                  id="machineId"
                  v-model.number="formData.zmachine_id"
                  type="number"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group mb-3">
                <label for="patch" class="form-label">Patch</label>
                <input
                  id="patch"
                  v-model="formData.zpatch"
                  type="text"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group mb-3">
                <label for="silvic" class="form-label">Silvic Code</label>
                <input
                  id="silvic"
                  v-model="formData.zsilvic"
                  type="text"
                  class="form-control"
                  :readonly="readOnly"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div v-if="!readOnly" class="mt-4">
        <button 
          type="submit" 
          class="btn btn-primary me-2" 
          :disabled="saving"
        >
          <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
          {{ saving ? 'Saving...' : (formData.treatment_xtra_id ? 'Update' : 'Save') }}
        </button>
        <button 
          type="button" 
          class="btn btn-secondary" 
          @click="$emit('cancel')"
          :disabled="saving"
        >
          Cancel
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'TreatmentExtraForm',
  props: {
    treatmentId: {
      type: [Number, String],
      required: true
    },
    extraData: {
      type: Object,
      default: null
    },
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      saving: false,
      formData: {
        treatment_xtra_id: null,
        rescheduled_reason: '',
        success_rate_pct: null,
        stocking_rate_spha: null,
        api_species_assessed: '',
        zassessment_type: '',
        zresult_standard: '',
        zspecies1_planted: null,
        zplanting_rate1_spha: null,
        zspecies2_planted: null,
        zplanting_rate2_spha: null,
        zseed_source: '',
        qty1: null,
        qty2: null,
        qty3: null,
        qty4: null,
        zmachine_id: null,
        zpatch: '',
        zsilvic: '',
        ztaskid: '',
        ztreatno: null
      }
    };
  },
  computed: {
    isEditing() {
      return !!this.formData.treatment_xtra_id;
    }
  },
  methods: {
    initializeForm() {
        if (this.extraData) {
            // Editing existing extra
            this.formData = { ...this.extraData };
        } else {
            // Creating new extra - reset form
            this.formData = {
                treatment_xtra_id: null,
                rescheduled_reason: '',
                success_rate_pct: null,
                stocking_rate_spha: null,
                api_species_assessed: '',
                zassessment_type: '',
                zresult_standard: '',
                zspecies1_planted: null,
                zplanting_rate1_spha: null,
                zspecies2_planted: null,
                zplanting_rate2_spha: null,
                zseed_source: '',
                qty1: null,
                qty2: null,
                qty3: null,
                qty4: null,
                zmachine_id: null,
                zpatch: '',
                zsilvic: '',
                ztaskid: '',
                ztreatno: null
            };
        }
    },
    
    async saveExtra() {
        if (!this.validateForm()) {
            return;
        }

        this.saving = true;
        
        try {
            let url, method, dataToSave;
            
            if (this.isEditing) {
                // Update existing
                url = `${api_endpoints.treatment_extras}${this.formData.treatment_xtra_id}/`;
                method = 'PUT';
                dataToSave = this.formData;
            } else {
                // Create new
                url = api_endpoints.treatment_extras;
                method = 'POST';
                dataToSave = {
                    ...this.formData,
                    treatment: this.treatmentId
                };
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(dataToSave)
            });

            if (!response.ok) {
                let errorDetail = '';
                try {
                    const errorData = await response.json();
                    errorDetail = JSON.stringify(errorData);
                } catch (e) {
                    try {
                        errorDetail = await response.text();
                    } catch (textError) {
                        errorDetail = 'Could not read error response';
                    }
                }
                throw new Error(`HTTP error! status: ${response.status}, details: ${errorDetail}`);
            }

            const responseData = await response.json();
            
            this.$emit('extra-saved', responseData);
            
            await swal.fire({
                icon: 'success',
                title: 'Success!',
                text: `Treatment details ${this.isEditing ? 'updated' : 'added'} successfully`,
                timer: 3000,
                showConfirmButton: false
            });
            
        } catch (error) {
            console.error('Error saving treatment extra:', error);
            
            let errorMessage = 'Failed to save treatment details';
            if (error.message && error.message.includes('details:')) {
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
                confirmButtonText: 'OK'
            });
            
        } finally {
            this.saving = false;
        }
    },
    
    validateForm() {
        // Basic validation - you can expand this as needed
        if (this.formData.success_rate_pct !== null && 
            (this.formData.success_rate_pct < 0 || this.formData.success_rate_pct > 100)) {
            swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'Success rate must be between 0 and 100',
                confirmButtonText: 'OK'
            });
            return false;
        }
        
        if (this.formData.stocking_rate_spha !== null && this.formData.stocking_rate_spha < 0) {
            swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'Stocking rate cannot be negative',
                confirmButtonText: 'OK'
            });
            return false;
        }
        
        return true;
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
    this.initializeForm();
  },
  watch: {
    extraData: {
      handler(newVal) {
        this.initializeForm();
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
/*
.treatment-extra-form {
  max-height: 70vh;
  overflow-y: auto;
}
*/

.card {
  border: 1px solid #dee2e6;
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.form-text {
  font-size: 0.75rem;
  color: #6c757d;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.25rem;
}
</style>
