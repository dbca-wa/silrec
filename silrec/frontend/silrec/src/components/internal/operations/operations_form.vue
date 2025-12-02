<template>
  <div class="operation-form">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/operations/operations_form.vue</div>
    <form @submit.prevent="saveOperation">
      <div class="row">
        <div class="col-md-4">
          <div class="form-group mb-3">
            <label for="feaId" class="form-label">FEA ID *</label>
            <input
              id="feaId"
              v-model="operationData.fea_id"
              type="text"
              class="form-control"
              :readonly="readOnly || !isNew"
              required
              maxlength="20"
              placeholder="Enter FEA ID (from polygon zfea_id)"
            />
            <div class="form-text">FEA ID from polygon's zfea_id field</div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group mb-3">
            <label for="dasId" class="form-label">DAS ID</label>
            <input
              id="dasId"
              v-model.number="operationData.das_id"
              type="number"
              class="form-control"
              :readonly="readOnly"
              placeholder="Disturbance Approval System ID"
            />
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group mb-3">
            <label for="planRelease" class="form-label">Plan Release</label>
            <input
              id="planRelease"
              v-model="operationData.plan_release"
              type="text"
              class="form-control"
              :readonly="readOnly"
              maxlength="50"
              placeholder="Release package identifier"
            />
          </div>
        </div>
      </div>

      <!-- File Upload Section -->
      <div class="row mt-3">
        <div class="col-md-6">
          <div class="card">
            <div class="card-header bg-light">
              <h6 class="mb-0">Silvicultural Plan Map</h6>
            </div>
            <div class="card-body">
              <div v-if="operationData.silvic_plan_map && !showMapUpload" class="mb-2">
                <div class="d-flex justify-content-between align-items-center">
                  <span class="text-muted">
                    <i class="bi bi-file-earmark-image me-1"></i>
                    Map file attached
                  </span>
                  <div>
                    <a :href="operationData.silvic_plan_map" 
                       target="_blank" 
                       class="btn btn-sm btn-outline-info me-1"
                       title="View Map">
                      <i class="bi bi-eye"></i> View
                    </a>
                    <button v-if="!readOnly" 
                            type="button"
                            class="btn btn-sm btn-outline-warning"
                            @click="showMapUpload = true"
                            title="Replace Map">
                      <i class="bi bi-arrow-repeat"></i> Replace
                    </button>
                  </div>
                </div>
              </div>
              
              <div v-if="showMapUpload || (!operationData.silvic_plan_map && !readOnly)">
                <div class="form-group mb-3">
                  <label for="silvicPlanMap" class="form-label">Upload Silvicultural Plan Map</label>
                  <input
                    id="silvicPlanMap"
                    ref="mapFileInput"
                    type="file"
                    class="form-control"
                    :disabled="readOnly"
                    accept=".pdf,.jpg,.jpeg,.png,.gif,.tif,.tiff"
                    @change="handleMapFileUpload"
                  />
                  <div class="form-text">PDF, JPG, PNG, GIF, or TIFF files</div>
                </div>
                
                <div v-if="mapFilePreview" class="mt-2">
                  <div class="d-flex align-items-center">
                    <i class="bi bi-file-earmark-image me-2"></i>
                    <span class="small">{{ mapFilePreview.name }}</span>
                    <button v-if="!readOnly"
                            type="button"
                            class="btn btn-sm btn-outline-danger ms-2"
                            @click="clearMapFile">
                      <i class="bi bi-x"></i>
                    </button>
                  </div>
                </div>
                
                <div v-if="operationData.silvic_plan_map && showMapUpload" class="mt-2">
                  <button v-if="!readOnly"
                          type="button"
                          class="btn btn-sm btn-outline-secondary"
                          @click="cancelMapUpload">
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="col-md-6">
          <div class="card">
            <div class="card-header bg-light">
              <h6 class="mb-0">Silvicultural Plan Document</h6>
            </div>
            <div class="card-body">
              <div v-if="operationData.silvic_plan_doc && !showDocUpload" class="mb-2">
                <div class="d-flex justify-content-between align-items-center">
                  <span class="text-muted">
                    <i class="bi bi-file-earmark-text me-1"></i>
                    Document file attached
                  </span>
                  <div>
                    <a :href="operationData.silvic_plan_doc" 
                       target="_blank" 
                       class="btn btn-sm btn-outline-info me-1"
                       title="View Document">
                      <i class="bi bi-eye"></i> View
                    </a>
                    <button v-if="!readOnly" 
                            type="button"
                            class="btn btn-sm btn-outline-warning"
                            @click="showDocUpload = true"
                            title="Replace Document">
                      <i class="bi bi-arrow-repeat"></i> Replace
                    </button>
                  </div>
                </div>
              </div>
              
              <div v-if="showDocUpload || (!operationData.silvic_plan_doc && !readOnly)">
                <div class="form-group mb-3">
                  <label for="silvicPlanDoc" class="form-label">Upload Silvicultural Plan Document</label>
                  <input
                    id="silvicPlanDoc"
                    ref="docFileInput"
                    type="file"
                    class="form-control"
                    :disabled="readOnly"
                    accept=".pdf,.doc,.docx,.xls,.xlsx"
                    @change="handleDocFileUpload"
                  />
                  <div class="form-text">PDF, Word, or Excel files</div>
                </div>
                
                <div v-if="docFilePreview" class="mt-2">
                  <div class="d-flex align-items-center">
                    <i class="bi bi-file-earmark-text me-2"></i>
                    <span class="small">{{ docFilePreview.name }}</span>
                    <button v-if="!readOnly"
                            type="button"
                            class="btn btn-sm btn-outline-danger ms-2"
                            @click="clearDocFile">
                      <i class="bi bi-x"></i>
                    </button>
                  </div>
                </div>
                
                <div v-if="operationData.silvic_plan_doc && showDocUpload" class="mt-2">
                  <button v-if="!readOnly"
                          type="button"
                          class="btn btn-sm btn-outline-secondary"
                          @click="cancelDocUpload">
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div v-if="!readOnly" class="mt-4">
        <button type="submit" class="btn btn-primary me-2" :disabled="saving">
          <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
          {{ saving ? 'Saving...' : (operationId ? 'Update Operation' : 'Save Operation') }}
        </button>
        <button type="button" class="btn btn-secondary" @click="cancel">
          Cancel
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'OperationForm',
  props: {
    operationId: {
      type: [Number, String],
      default: null
    },
    cohortId: {
      type: [Number, String],
      required: false
    },
    feaId: {
      type: String,
      default: ''
    },
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      operationData: {
        fea_id: '',
        das_id: null,
        plan_release: '',
        silvic_plan_map: null,
        silvic_plan_doc: null,
        silvic_plan_map_file: null,
        silvic_plan_doc_file: null
      },
      saving: false,
      mapFilePreview: null,
      docFilePreview: null,
      showMapUpload: false,
      showDocUpload: false
    };
  },
  computed: {
    isNew() {
      return !this.operationId;
    }
  },
  methods: {
    async loadOperationData() {
        if (this.operationId) {
            try {
                const response = await fetch(`${api_endpoints.operations}${this.operationId}/`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                this.operationData = { ...data };
            } catch (error) {
                console.error('Error loading operation data:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Load Failed',
                    text: 'Failed to load operation data',
                    confirmButtonText: 'OK'
                });
            }
        } else {
            // For new operation, use provided FEA ID
            this.operationData.fea_id = this.feaId || '';
        }
    },
    
    async loadCohortPolygonFEA() {
        if (this.cohortId && !this.feaId) {
            try {
                console.log("URL1: " + `${api_endpoints.cohorts}${this.cohortId}/`);
                const response = await fetch(`${api_endpoints.cohorts}${this.cohortId}/`);
                if (response.ok) {
                    const cohortData = await response.json();
                    // Try to get FEA ID from assigned polygons
                    if (cohortData.assigned_polygons && cohortData.assigned_polygons.length > 0) {
                        // Get the first polygon's FEA ID
                        const polygonId = cohortData.assigned_polygons[0].polygon_id;
                        console.log("URL2: " + `${api_endpoints.polygons}${polygonId}/`);
                        const polygonResponse = await fetch(`${api_endpoints.polygons}${polygonId}/`);
                        if (polygonResponse.ok) {
                            const polygonData = await polygonResponse.json();
                            this.operationData.fea_id = polygonData.zfea_id || '';
                        }
                    }
                }
            } catch (error) {
                console.error('Error loading polygon FEA ID:', error);
            }
            console.log("URL3: " + this.operationData.fea_id);
        }
    },
    
    handleMapFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.mapFilePreview = file;
        this.operationData.silvic_plan_map_file = file;
      }
    },
    
    handleDocFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        this.docFilePreview = file;
        this.operationData.silvic_plan_doc_file = file;
      }
    },
    
    clearMapFile() {
      this.mapFilePreview = null;
      this.operationData.silvic_plan_map_file = null;
      if (this.$refs.mapFileInput) {
        this.$refs.mapFileInput.value = '';
      }
    },
    
    clearDocFile() {
      this.docFilePreview = null;
      this.operationData.silvic_plan_doc_file = null;
      if (this.$refs.docFileInput) {
        this.$refs.docFileInput.value = '';
      }
    },
    
    cancelMapUpload() {
      this.showMapUpload = false;
      this.clearMapFile();
    },
    
    cancelDocUpload() {
      this.showDocUpload = false;
      this.clearDocFile();
    },
    
    async saveOperation() {
        if (!this.validateForm()) {
            return;
        }

        this.saving = true;
        console.log('Starting save operation...');
        console.log('Operation Data:', JSON.stringify(this.operationData, null, 2));
        
        try {
            const formData = new FormData();
            
            // Add regular fields
            Object.keys(this.operationData).forEach(key => {
                if (key !== 'silvic_plan_map_file' && key !== 'silvic_plan_doc_file') {
                    const value = this.operationData[key];
                    console.log(`Adding field ${key}:`, value);
                    
                    if (value !== null && value !== undefined) {
                        formData.append(key, value);
                    }
                }
            });
            
            // Log all form data entries
            for (let [key, value] of formData.entries()) {
                console.log(`FormData: ${key} = ${value}`);
            }
            
            // Add cohort_id if provided
            if (this.cohortId) {
                formData.append('cohort_id', this.cohortId);
                console.log('Added cohort_id:', this.cohortId);
            }
            
            // Add files if provided
            if (this.operationData.silvic_plan_map_file) {
                formData.append('silvic_plan_map_file', this.operationData.silvic_plan_map_file);
                console.log('Added silvic_plan_map_file:', this.operationData.silvic_plan_map_file.name);
            }
            
            if (this.operationData.silvic_plan_doc_file) {
                formData.append('silvic_plan_doc_file', this.operationData.silvic_plan_doc_file);
                console.log('Added silvic_plan_doc_file:', this.operationData.silvic_plan_doc_file.name);
            }

            let url, method;
            if (this.operationId) {
                url = `${api_endpoints.operations}${this.operationId}/`;
                method = 'PUT';
                console.log('Updating existing operation:', this.operationId);
            } else {
                url = api_endpoints.operations;
                method = 'POST';
                console.log('Creating new operation');
            }

            console.log('Sending request to:', url);
            console.log('Method:', method);
            
            const csrfToken = this.getCSRFToken();
            console.log('CSRF Token exists:', !!csrfToken);

            const response = await fetch(url, {
                method: method,
                headers: {
                    'X-CSRFToken': csrfToken
                    // Note: DON'T set Content-Type for FormData - let browser set it with boundary
                },
                body: formData
            });

            console.log('Response status:', response.status);
            console.log('Response status text:', response.statusText);
            
            // First, try to get the response as text
            const responseText = await response.text();
            console.log('Raw response text:', responseText);
            
            if (!response.ok) {
                // Try to parse as JSON
                let errorData;
                try {
                    errorData = JSON.parse(responseText);
                } catch (e) {
                    errorData = { detail: responseText };
                }
                
                console.log('Error data:', errorData);
                throw new Error(`HTTP error! status: ${response.status}, details: ${JSON.stringify(errorData)}`);
            }

            // Parse successful response
            let responseData;
            try {
                responseData = JSON.parse(responseText);
            } catch (e) {
                responseData = { success: true, message: 'Operation saved successfully' };
            }
            
            console.log('Operation saved successfully:', responseData);
            
            this.$emit('operation-saved', responseData);
            
            await swal.fire({
                icon: 'success',
                title: 'Success!',
                text: `Operation ${this.operationId ? 'updated' : 'created'} successfully`,
                timer: 3000,
                showConfirmButton: false
            });
        } catch (error) {
            console.error('Error saving operation:', error);
            await this.handleSaveError(error);
        } finally {
            this.saving = false;
        }
    },
    
    validateForm() {
        if (!this.operationData.fea_id) {
            swal.fire({
                icon: 'error',
                title: 'Validation Error',
                text: 'FEA ID is required',
                confirmButtonText: 'OK'
            });
            return false;
        }
        
        return true;
    },
    
    async handleSaveError(error) {
        let errorMessage = 'Failed to save operation';
        let errorDetails = '';
        
        console.error('Full error object:', error);
        console.error('Error message:', error.message);
        
        if (error.message && error.message.includes('403')) {
            errorMessage = 'You do not have permission to create or update operations. Please contact an administrator.';
        } else if (error.message && error.message.includes('details:')) {
            try {
                const details = error.message.split('details:')[1];
                console.log('Raw error details:', details);
                
                // Try to parse JSON first
                try {
                    const errorData = JSON.parse(details);
                    console.log('Parsed error data:', errorData);
                    
                    if (typeof errorData === 'object') {
                        if (errorData.error) {
                            errorMessage = errorData.error;
                        } else if (errorData.detail) {
                            errorMessage = errorData.detail;
                        } else if (Array.isArray(errorData)) {
                            errorMessage = errorData.join(', ');
                        } else {
                            // Extract all error messages from the object
                            const errorMessages = [];
                            for (const [key, value] of Object.entries(errorData)) {
                                if (Array.isArray(value)) {
                                    errorMessages.push(`${key}: ${value.join(', ')}`);
                                } else {
                                    errorMessages.push(`${key}: ${value}`);
                                }
                            }
                            errorMessage = errorMessages.join('; ');
                        }
                    } else {
                        errorMessage = details;
                    }
                } catch (e) {
                    // If not JSON, use as plain text
                    console.log('Error details not JSON:', details);
                    errorMessage = details;
                }
            } catch (e) {
                errorMessage = error.message;
            }
        } else {
            errorMessage = error.message || 'Unknown error occurred';
        }
        
        console.log('Final error message to show:', errorMessage);
        
        await swal.fire({
            icon: 'error',
            title: 'Save Error',
            html: `<p>${errorMessage}</p>${errorDetails ? `<p><small>Details: ${errorDetails}</small></p>` : ''}`,
            confirmButtonText: 'OK',
            confirmButtonColor: '#d33'
        });
    },
    
    cancel() {
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
    this.loadOperationData();
    this.loadCohortPolygonFEA();
  },
  watch: {
    operationId: {
      handler(newVal) {
        if (newVal) {
          this.loadOperationData();
        } else {
          this.operationData = {
            fea_id: this.feaId || '',
            das_id: null,
            plan_release: '',
            silvic_plan_map: null,
            silvic_plan_doc: null,
            silvic_plan_map_file: null,
            silvic_plan_doc_file: null
          };
          this.mapFilePreview = null;
          this.docFilePreview = null;
          this.showMapUpload = false;
          this.showDocUpload = false;
        }
      },
      immediate: true
    },
    feaId: {
      handler(newVal) {
        if (newVal && !this.operationId) {
          this.operationData.fea_id = newVal;
        }
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
.operation-form {
  max-width: 100%;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.form-control:read-only {
  background-color: #e9ecef;
  opacity: 1;
}

.form-text {
  font-size: 0.75rem;
  color: #6c757d;
}

.btn {
  min-width: 100px;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
}

.card-header {
  padding: 0.5rem 1rem;
}

.card-body {
  padding: 1rem;
}
</style>
