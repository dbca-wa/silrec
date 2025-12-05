<template>
  <div class="report-generator">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/reports/report_generator.vue</div>
    
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">Dynamic SQL Report Generator</h5>
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
          <!--
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
          -->
          
          <!-- Custom WHERE Clauses -->
          <div v-for="(clause, index) in customClauses" :key="index" class="row mb-3 border p-3 rounded">
            <div class="col-md-4">
              <label class="form-label">Field *</label>
              <select 
                v-model="clause.field"
                class="form-select"
                :required="true"
                @change="onFieldChange(index)"
              >
                <option value="">-- Select Field --</option>
                <optgroup label="From Report SQL">
                  <option 
                    v-for="field in availableFields.filter(f => f.type === 'select_field')" 
                    :key="field.value"
                    :value="field.value"
                  >
                    {{ field.label }}
                  </option>
                </optgroup>
                <!--
                <optgroup label="Common Fields">
                  <option 
                    v-for="field in availableFields.filter(f => f.type === 'common')" 
                    :key="field.value"
                    :value="field.value"
                  >
                    {{ field.label }}
                  </option>
                </optgroup>
                -->
              </select>
              <div v-if="clause.field" class="form-text small">
                <code>{{ clause.field }}</code>
              </div>
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Operator *</label>
              <select 
                v-model="clause.operator" 
                class="form-select"
                :required="true"
              >
                <option value="=">=</option>
                <option value="!=">!=</option>
                <option value=">">></option>
                <option value="<">&lt;</option>
                <option value=">=">>=</option>
                <option value="<=">&lt;=</option>
                <option value="LIKE">LIKE (Contains)</option>
                <option value="NOT LIKE">NOT LIKE (Does Not Contain)</option>
                <option value="IN">IN (In List)</option>
                <option value="NOT IN">NOT IN (Not In List)</option>
                <option value="IS NULL">IS NULL</option>
                <option value="IS NOT NULL">IS NOT NULL</option>
                <option value="BETWEEN">BETWEEN (Range)</option>
              </select>
            </div>
            
            <div class="col-md-3">
              <label class="form-label">Value *</label>
              <input 
                v-if="!['IS NULL', 'IS NOT NULL'].includes(clause.operator)"
                v-model="clause.value"
                type="text"
                class="form-control"
                :required="true"
                :placeholder="getValuePlaceholder(clause)"
              />
              <div v-else class="form-control-plaintext">
                <em>No value required</em>
              </div>
              <div v-if="clause.operator === 'BETWEEN'" class="form-text small">
                Enter two values separated by comma: start,end
              </div>
              <div v-if="clause.operator === 'IN' || clause.operator === 'NOT IN'" class="form-text small">
                Enter multiple values separated by commas
              </div>
            </div>
            
            <div class="col-md-1">
              <label class="form-label">Logic</label>
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
                title="Remove Filter"
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
              <!-- Collapsible SQL Section -->
              <div class="accordion mb-3" id="previewAccordion">
                <div class="accordion-item">
                  <h2 class="accordion-header" id="sqlHeading">
                    <button 
                      class="accordion-button collapsed" 
                      type="button" 
                      data-bs-toggle="collapse" 
                      data-bs-target="#sqlCollapse" 
                      aria-expanded="false" 
                      aria-controls="sqlCollapse"
                    >
                      <i class="bi bi-code-slash me-2"></i>
                      SQL Query (Click to expand/collapse)
                    </button>
                  </h2>
                  <div 
                    id="sqlCollapse" 
                    class="accordion-collapse collapse" 
                    aria-labelledby="sqlHeading" 
                    data-bs-parent="#previewAccordion"
                  >
                    <div class="accordion-body bg-light">
                      <div class="alert alert-info">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                          <strong>Executed SQL:</strong>
                          <button 
                            type="button" 
                            class="btn btn-sm btn-outline-secondary"
                            @click="copySqlToClipboard"
                            title="Copy SQL to clipboard"
                          >
                            <i class="bi bi-clipboard"></i> Copy
                          </button>
                        </div>
                        <pre class="mb-0" style="font-size: 0.8em; max-height: 300px; overflow-y: auto;">{{ previewData.sql }}</pre>
                      </div>
                      
                      <!-- Parameters Summary -->
                      <div v-if="previewData.parameters && Object.keys(previewData.parameters).length > 0" class="mt-3">
                        <h6 class="mb-2">Parameters:</h6>
                        <div class="row">
                          <div 
                            v-for="(value, key) in previewData.parameters" 
                            :key="key"
                            class="col-md-6 mb-1"
                          >
                            <small>
                              <strong>{{ key }}:</strong> {{ Array.isArray(value) ? value.join(', ') : value }}
                            </small>
                          </div>
                        </div>
                      </div>
                      
                      <!-- Custom Clauses Summary -->
                      <div v-if="previewData.custom_clauses && previewData.custom_clauses.length > 0" class="mt-3">
                        <h6 class="mb-2">Custom Filters:</h6>
                        <div class="row">
                          <div 
                            v-for="(clause, index) in previewData.custom_clauses" 
                            :key="index"
                            class="col-12 mb-1"
                          >
                            <small>
                              <strong>{{ index + 1 }}.</strong> 
                              {{ clause.field }} {{ clause.operator }} 
                              <span v-if="clause.value">{{ clause.value }}</span>
                              <span v-else>{{ clause.operator }}</span>
                            </small>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Results Section (always visible) -->
                <div class="accordion-item">
                  <h2 class="accordion-header" id="resultsHeading">
                    <button 
                      class="accordion-button" 
                      type="button" 
                      data-bs-toggle="collapse" 
                      data-bs-target="#resultsCollapse" 
                      aria-expanded="true" 
                      aria-controls="resultsCollapse"
                    >
                      <i class="bi bi-table me-2"></i>
                      Results ({{ previewData.row_count }} rows)
                      <span class="badge bg-secondary ms-2">Showing first {{ Math.min(previewData.row_count, 10) }}</span>
                    </button>
                  </h2>
                  <div 
                    id="resultsCollapse" 
                    class="accordion-collapse collapse show" 
                    aria-labelledby="resultsHeading" 
                    data-bs-parent="#previewAccordion"
                  >
                    <div class="accordion-body p-0">
                      <div class="table-responsive">
                        <table class="table table-sm table-striped table-bordered mb-0">
                          <thead>
                            <tr>
                              <th v-for="col in previewData.columns" :key="col">
                                {{ col }}
                                <span v-if="previewData.data[0] && previewData.data[0][col] !== null" 
                                      class="badge bg-light text-dark ms-1" style="font-size: 0.6em; font-weight: normal;">
                                  {{ typeof previewData.data[0][col] }}
                                </span>
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(row, index) in previewData.data" :key="index">
                              <td v-for="col in previewData.columns" :key="col">
                                <template v-if="row[col] === null || row[col] === undefined">
                                  <span class="text-muted fst-italic">null</span>
                                </template>
                                <template v-else-if="typeof row[col] === 'boolean'">
                                  <span :class="row[col] ? 'text-success' : 'text-danger'">
                                    {{ row[col] ? '✓' : '✗' }}
                                  </span>
                                </template>
                                <template v-else-if="Array.isArray(row[col])">
                                  {{ row[col].join(', ') }}
                                </template>
                                <template v-else>
                                  {{ row[col] }}
                                </template>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      
                      <div v-if="previewData.data.length === 0" class="text-center text-muted py-4">
                        <i class="bi bi-inbox display-6"></i>
                        <p class="mt-2">No data found for the selected parameters</p>
                      </div>
                    </div>
                  </div>
                </div>
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
      
      // Available fields for custom clauses
      availableFields: [],
      loadingFields: false,
      
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
      
      // Check custom clauses have all required fields
      for (const clause of this.customClauses) {
        if (!clause.field || (!clause.value && !['IS NULL', 'IS NOT NULL'].includes(clause.operator))) {
          return false;
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
      
      // Check custom clauses for preview
      for (const clause of this.customClauses) {
        if (!clause.field || (!clause.value && !['IS NULL', 'IS NOT NULL'].includes(clause.operator))) {
          return false;
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
    
    async fetchAvailableFields(reportId) {
      this.loadingFields = true;
      try {
        const response = await fetch(`${api_endpoints.reports}${reportId}/available_fields/`);
        if (response.ok) {
          this.availableFields = await response.json();
        } else {
          this.availableFields = [];
          console.warn('Could not load available fields, using empty list');
        }
      } catch (error) {
        console.error('Error fetching available fields:', error);
        this.availableFields = [];
      } finally {
        this.loadingFields = false;
      }
    },
    
    onReportChange() {
      this.selectedReport = this.availableReports.find(
        r => r.id === this.selectedReportId
      );
      
      // Reset parameters
      this.parameters = {};
      this.customClauses = [];
      this.availableFields = [];
      
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
      
      // Fetch available fields for this report
      if (this.selectedReportId) {
        this.fetchAvailableFields(this.selectedReportId);
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
    
    onFieldChange(index) {
      // Optional: Auto-set operator based on field type
      const clause = this.customClauses[index];
      if (clause.field) {
        // You could add logic here to suggest operators based on field name
        // For example, date fields might default to '=', numeric fields to '=', etc.
        if (clause.field.includes('date') || clause.field.includes('year')) {
          clause.operator = '=';
        } else if (clause.field.includes('area') || clause.field.includes('rate')) {
          clause.operator = '>=';
        }
      }
    },
    
    getValuePlaceholder(clause) {
      if (clause.operator === 'LIKE' || clause.operator === 'NOT LIKE') {
        return 'Enter search text (use % as wildcard)';
      } else if (clause.operator === 'IN' || clause.operator === 'NOT IN') {
        return 'value1, value2, value3';
      } else if (clause.operator === 'BETWEEN') {
        return 'start, end';
      } else {
        return 'Enter value';
      }
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
        const validCustomClauses = this.customClauses.filter(clause => {
          // Check if field is selected
          if (!clause.field || !clause.field.trim()) {
            return false;
          }
          
          // Check if value is required and provided
          if (!['IS NULL', 'IS NOT NULL'].includes(clause.operator)) {
            if (!clause.value || !clause.value.toString().trim()) {
              return false;
            }
          }
          
          return true;
        });
        
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
        const validCustomClauses = this.customClauses.filter(clause => {
          if (!clause.field || !clause.field.trim()) {
            return false;
          }
          
          if (!['IS NULL', 'IS NOT NULL'].includes(clause.operator)) {
            if (!clause.value || !clause.value.toString().trim()) {
              return false;
            }
          }
          
          return true;
        });
        
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
      this.availableFields = [];
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
    },
    copySqlToClipboard() {
        if (this.previewData && this.previewData.sql) {
          navigator.clipboard.writeText(this.previewData.sql)
            .then(() => {
              // Show a temporary success message
              const copyButton = document.querySelector('[title="Copy SQL to clipboard"]');
              const originalHtml = copyButton.innerHTML;
              copyButton.innerHTML = '<i class="bi bi-check"></i> Copied!';
              copyButton.classList.remove('btn-outline-secondary');
              copyButton.classList.add('btn-success');
              
              setTimeout(() => {
                copyButton.innerHTML = originalHtml;
                copyButton.classList.remove('btn-success');
                copyButton.classList.add('btn-outline-secondary');
              }, 2000);
            })
            .catch(err => {
              console.error('Failed to copy SQL: ', err);
            });
        }
    },

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

.form-text code {
  background-color: #f1f1f1;
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.85em;
}

optgroup {
  font-weight: normal;
  font-style: normal;
}

optgroup label {
  font-weight: bold;
  color: #495057;
}
</style>
