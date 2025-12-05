<template>
  <div class="report-generator">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/reports/report_generator.vue</div>
    
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Report Generator</h5>
      </div>
      
      <div class="card-body">
        <!-- Step 1: Select Report -->
        <div class="mb-4">
          <h6>Step 1: Select Report</h6>
          <div class="row">
            <div class="col-md-6">
              <div class="form-group">
                <label for="reportSelect" class="form-label">Report Type *</label>
                <select 
                  id="reportSelect"
                  v-model="selectedReportId"
                  class="form-select"
                  @change="onReportChange"
                  :disabled="loading"
                >
                  <option value="">-- Select a report --</option>
                  <option 
                    v-for="report in availableReports" 
                    :key="report.id"
                    :value="report.id"
                  >
                    {{ report.name }}
                  </option>
                </select>
                <div class="form-text text-muted">
                  {{ selectedReport?.description || 'Select a report to generate' }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 2: Set Parameters -->
        <div v-if="selectedReport" class="mb-4">
          <h6>Step 2: Set Parameters</h6>
          <div class="row">
            <div 
              v-for="param in selectedReport.parameters" 
              :key="param.name"
              class="col-md-6 mb-3"
            >
              <div class="form-group">
                <label :for="param.name" class="form-label">
                  {{ param.label }}
                  <span v-if="param.required" class="text-danger">*</span>
                </label>
                
                <!-- Select Input -->
                <select 
                  v-if="param.field_type === 'select' || param.field_type === 'multiselect'"
                  :id="param.name"
                  v-model="parameters[param.name]"
                  :multiple="param.field_type === 'multiselect'"
                  class="form-select"
                  :required="param.required"
                >
                  <option value="">-- Select --</option>
                  <option 
                    v-for="option in param.options" 
                    :key="option"
                    :value="option"
                  >
                    {{ option }}
                  </option>
                </select>
                
                <!-- Text Input -->
                <input 
                  v-else-if="param.field_type === 'text'"
                  :id="param.name"
                  v-model="parameters[param.name]"
                  type="text"
                  class="form-control"
                  :required="param.required"
                  :placeholder="`Enter ${param.label.toLowerCase()}`"
                />
                
                <!-- Number Input -->
                <input 
                  v-else-if="param.field_type === 'number'"
                  :id="param.name"
                  v-model="parameters[param.name]"
                  type="number"
                  class="form-control"
                  :required="param.required"
                  :placeholder="`Enter ${param.label.toLowerCase()}`"
                />
                
                <!-- Date Input -->
                <input 
                  v-else-if="param.field_type === 'date'"
                  :id="param.name"
                  v-model="parameters[param.name]"
                  type="date"
                  class="form-control"
                  :required="param.required"
                />
                
                <!-- Year Input -->
                <input 
                  v-else-if="param.field_type === 'year'"
                  :id="param.name"
                  v-model="parameters[param.name]"
                  type="number"
                  min="2000"
                  :max="new Date().getFullYear()"
                  class="form-control"
                  :required="param.required"
                  placeholder="YYYY"
                />
                
                <!-- Month Input -->
                <select 
                  v-else-if="param.field_type === 'month'"
                  :id="param.name"
                  v-model="parameters[param.name]"
                  class="form-select"
                  :required="param.required"
                >
                  <option value="">-- Select Month --</option>
                  <option value="1">January</option>
                  <option value="2">February</option>
                  <option value="3">March</option>
                  <option value="4">April</option>
                  <option value="5">May</option>
                  <option value="6">June</option>
                  <option value="7">July</option>
                  <option value="8">August</option>
                  <option value="9">September</option>
                  <option value="10">October</option>
                  <option value="11">November</option>
                  <option value="12">December</option>
                </select>
              </div>
            </div>
          </div>
          
          <!-- Add Custom WHERE Clause Button -->
          <div class="mb-3">
            <button 
              type="button" 
              class="btn btn-outline-secondary btn-sm"
              @click="addCustomClause"
              v-if="selectedReport?.report_type === 'custom'"
            >
              <i class="bi bi-plus-circle me-1"></i> Add Custom Filter
            </button>
          </div>
          
          <!-- Custom WHERE Clauses -->
          <div v-for="(clause, index) in customClauses" :key="index" class="row mb-3 border p-3 rounded">
            <div class="col-md-3">
              <label class="form-label">Field</label>
              <input 
                v-model="clause.field"
                type="text"
                class="form-control"
                placeholder="e.g., cmpt.region"
              />
            </div>
            <div class="col-md-2">
              <label class="form-label">Operator</label>
              <select v-model="clause.operator" class="form-select">
                <option value="=">=</option>
                <option value="!=">!=</option>
                <option value=">">></option>
                <option value="<"><</option>
                <option value="LIKE">LIKE</option>
                <option value="IN">IN</option>
              </select>
            </div>
            <div class="col-md-4">
              <label class="form-label">Value</label>
              <input 
                v-model="clause.value"
                type="text"
                class="form-control"
                placeholder="Enter value"
              />
            </div>
            <div class="col-md-2">
              <label class="form-label">Condition</label>
              <select v-model="clause.condition" class="form-select">
                <option value="AND">AND</option>
                <option value="OR">OR</option>
              </select>
            </div>
            <div class="col-md-1 d-flex align-items-end">
              <button 
                type="button" 
                class="btn btn-danger btn-sm"
                @click="removeCustomClause(index)"
              >
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>

        <!-- Step 3: Select Export Format -->
        <div v-if="selectedReport" class="mb-4">
          <h6>Step 3: Select Export Format</h6>
          <div class="row">
            <div class="col-md-6">
              <div class="form-group">
                <label for="exportFormat" class="form-label">Export Format *</label>
                <select 
                  id="exportFormat"
                  v-model="exportFormat"
                  class="form-select"
                  :disabled="loading"
                >
                  <option value="">-- Select format --</option>
                  <option 
                    v-for="format in selectedReport.export_formats" 
                    :key="format"
                    :value="format"
                  >
                    {{ format === 'excel' ? 'Excel (.xlsx)' : 
                       format === 'csv' ? 'CSV (.csv)' : 
                       format === 'shapefile' ? 'Shapefile (.shp)' : 
                       'PDF (.pdf)' }}
                  </option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="d-flex gap-2">
          <button 
            type="button" 
            class="btn btn-primary"
            @click="generateReport"
            :disabled="!canGenerate || generating"
          >
            <span v-if="generating" class="spinner-border spinner-border-sm me-1"></span>
            {{ generating ? 'Generating...' : 'Generate Report' }}
          </button>
          
          <button 
            type="button" 
            class="btn btn-outline-secondary"
            @click="previewReport"
            :disabled="!canPreview || previewing"
          >
            <span v-if="previewing" class="spinner-border spinner-border-sm me-1"></span>
            {{ previewing ? 'Previewing...' : 'Preview Data' }}
          </button>
          
          <button 
            type="button" 
            class="btn btn-outline-danger"
            @click="resetForm"
          >
            Reset
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <div v-if="previewData" class="modal fade show d-block" tabindex="-1" style="background-color: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Preview: {{ selectedReport?.name }}</h5>
            <button type="button" class="btn-close" @click="closePreview"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-info">
              <strong>SQL Executed:</strong>
              <pre class="mt-2 mb-2" style="font-size: 0.85em">{{ previewData.sql }}</pre>
              <div>Showing first {{ previewData.row_count }} rows</div>
            </div>
            
            <div class="table-responsive">
              <table class="table table-sm table-striped table-bordered">
                <thead>
                  <tr>
                    <th v-for="col in previewData.columns" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, index) in previewData.data" :key="index">
                    <td v-for="col in previewData.columns" :key="col">
                      {{ row[col] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div v-if="previewData.data.length === 0" class="text-center text-muted py-4">
              No data found for the selected parameters
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closePreview">Close</button>
            <button type="button" class="btn btn-primary" @click="generateReport">
              Generate Full Report
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'ReportGenerator',
  data() {
    return {
      // Available reports from API
      availableReports: [],
      loading: false,
      
      // Selected report
      selectedReportId: null,
      selectedReport: null,
      
      // Parameters for WHERE clauses
      parameters: {},
      
      // Custom WHERE clauses
      customClauses: [],
      
      // Export format
      exportFormat: 'excel',
      
      // Loading states
      generating: false,
      previewing: false,
      
      // Preview data
      previewData: null
    };
  },
  computed: {
    canGenerate() {
      if (!this.selectedReport || !this.exportFormat) return false;
      
      // Check required parameters
      if (this.selectedReport.parameters) {
        for (const param of this.selectedReport.parameters) {
          if (param.required && !this.parameters[param.name]) {
            return false;
          }
        }
      }
      
      return true;
    },
    
    canPreview() {
      if (!this.selectedReport) return false;
      
      // For preview, all required parameters must be filled
      if (this.selectedReport.parameters) {
        for (const param of this.selectedReport.parameters) {
          if (param.required && !this.parameters[param.name]) {
            return false;
          }
        }
      }
      
      return true;
    }
  },
  methods: {
    async loadAvailableReports() {
      this.loading = true;
      try {
        const response = await fetch(`${api_endpoints.reports}list_reports/`);
        if (response.ok) {
          this.availableReports = await response.json();
        } else {
          throw new Error('Failed to load reports');
        }
      } catch (error) {
        console.error('Error loading reports:', error);
        await swal.fire({
          icon: 'error',
          title: 'Load Failed',
          text: 'Failed to load available reports',
          confirmButtonText: 'OK'
        });
      } finally {
        this.loading = false;
      }
    },
    
    onReportChange() {
      this.selectedReport = this.availableReports.find(
        r => r.id === this.selectedReportId
      );
      
      // Reset parameters
      this.parameters = {};
      this.customClauses = [];
      
      // Set default values
      if (this.selectedReport?.parameters) {
        this.selectedReport.parameters.forEach(param => {
          if (param.default_value) {
            this.parameters[param.name] = param.default_value;
          }
        });
      }
      
      // Set default export format
      if (this.selectedReport?.export_formats?.length > 0) {
        this.exportFormat = this.selectedReport.export_formats[0];
      }
    },
    
    addCustomClause() {
      this.customClauses.push({
        field: '',
        operator: '=',
        value: '',
        condition: 'AND'
      });
    },
    
    removeCustomClause(index) {
      this.customClauses.splice(index, 1);
    },
    
    async generateReport() {
        if (!this.canGenerate) return;
        
        this.generating = true;
        
        try {
            // Prepare request data
            const requestData = {
                parameters: this.parameters,
                export_format: this.exportFormat
            };
            
            // Add custom clauses if any (filter out empty ones)
            const validCustomClauses = this.customClauses.filter(clause => 
                clause.field && clause.field.trim() && 
                clause.value && clause.value.toString().trim()
            );
            
            if (validCustomClauses.length > 0) {
                requestData.custom_clauses = validCustomClauses;
            }
            
            console.log('Sending request data:', requestData);
            
            const response = await fetch(
                `${api_endpoints.reports}${this.selectedReportId}/execute/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify(requestData)
                }
            );
            
            if (response.ok) {
                // Handle file download
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Create filename with timestamp
                const timestamp = new Date().toISOString().slice(0,10).replace(/-/g, '');
                const extension = this.exportFormat === 'excel' ? 'xlsx' : 
                                this.exportFormat === 'csv' ? 'csv' : 'pdf';
                a.download = `${this.selectedReport.name}_${timestamp}.${extension}`;
                
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                await swal.fire({
                    icon: 'success',
                    title: 'Report Generated',
                    text: `Report has been exported as ${this.exportFormat.toUpperCase()}`,
                    confirmButtonText: 'OK'
                });
            } else {
                const errorText = await response.text();
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch (e) {
                    errorData = { error: errorText };
                }
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error('Error generating report:', error);
            await swal.fire({
                icon: 'error',
                title: 'Generation Failed',
                text: error.message || 'Failed to generate report',
                confirmButtonText: 'OK'
            });
        } finally {
            this.generating = false;
        }
    },    
    async previewReport() {
        if (!this.canPreview) return;
        
        this.previewing = true;
        
        try {
            // Build query parameters for preview
            const params = new URLSearchParams();
            Object.entries(this.parameters).forEach(([key, value]) => {
                if (value !== null && value !== undefined && value !== '') {
                    if (Array.isArray(value)) {
                        value.forEach(v => params.append(`param_${key}`, v));
                    } else {
                        params.append(`param_${key}`, value);
                    }
                }
            });
            
            // Add custom clauses if any
            const validCustomClauses = this.customClauses.filter(clause => 
                clause.field && clause.field.trim() && 
                clause.value && clause.value.toString().trim()
            );
            
            if (validCustomClauses.length > 0) {
                params.append('custom_clauses', JSON.stringify(validCustomClauses));
            }
            
            console.log('Preview params:', params.toString());
            
            const response = await fetch(
                `${api_endpoints.reports}${this.selectedReportId}/preview/?${params}`
            );
            
            if (response.ok) {
                this.previewData = await response.json();
            } else {
                const errorText = await response.text();
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch (e) {
                    errorData = { error: errorText };
                }
                throw new Error(errorData.error || 'Failed to preview report');
            }
        } catch (error) {
            console.error('Error previewing report:', error);
            await swal.fire({
                icon: 'error',
                title: 'Preview Failed',
                text: error.message || 'Failed to preview report',
                confirmButtonText: 'OK'
            });
        } finally {
            this.previewing = false;
        }
    },
    closePreview() {
      this.previewData = null;
    },
    
    resetForm() {
      this.selectedReportId = null;
      this.selectedReport = null;
      this.parameters = {};
      this.customClauses = [];
      this.exportFormat = 'excel';
      this.previewData = null;
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
    this.loadAvailableReports();
  }
};
</script>

<style scoped>
.report-generator {
  max-width: 1200px;
  margin: 0 auto;
}

.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

.modal.show {
  display: block;
}

pre {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.table-responsive {
  max-height: 400px;
  overflow-y: auto;
}
</style>
