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
            <div class="col-md-6">
                <div class="form-group">
                  <label for="post_2024_only" class="form-check-label">
                    <br>
                    <div>
                      <input
                        id="post_2024_only"
                        v-model="filterPost2024Only"
                        type="checkbox"
                        class="form-check-input me-2"
                        checked
                      />
                      Post 2024 only
                    </div>
                  </label>
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
                    <span v-if="param.field_type === 'multiselect'" class="badge bg-info ms-1">
                        <i class="bi bi-list-check"></i> Multi-select
                    </span>
                    <span v-if="param.field_type === 'year_enhanced'" class="badge bg-secondary ms-1">
                        <i class="bi bi-calendar-range"></i> Supports: 2024, 2024,2023,2022, 2020-2024
                    </span>
                    </label>

                    <!-- Single Select -->
                    <select 
                    v-if="param.field_type === 'select'"
                    :id="param.name"
                    v-model="parameters[param.name]"
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
                    
                    <!-- Multi-select with Select2 (Tag mode) -->
                    <select 
                    v-else-if="param.field_type === 'multiselect'"
                    :id="'multiselect-' + param.name"
                    :ref="'multiselect-' + param.name"
                    class="form-select select2-multiple-tags"
                    :multiple="true"
                    :required="param.required"
                    style="width: 100%;"
                    >
                    <option 
                        v-for="option in param.options" 
                        :key="option"
                        :value="option"
                        :selected="isOptionSelected(param.name, option)"
                    >
                        {{ option }}
                    </option>
                    </select>
                    
                    <!-- Year Enhanced Input -->
                    <input 
                    v-else-if="param.field_type === 'year_enhanced'"
                    :id="param.name"
                    v-model="parameters[param.name]"
                    type="text"
                    class="form-control"
                    :required="param.required"
                    :placeholder="'Examples: 2024 | 2024,2023,2022 | 2020-2024'"
                    />
                    
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
                    
                    <!-- Year Input (legacy) -->
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
                    
                    <!-- Range Input (Two values) -->
                    <div v-else-if="param.field_type === 'range'" class="row g-2">
                    <div class="col">
                        <label class="form-label small">From</label>
                        <input 
                        :id="param.name + '_from'"
                        v-model="parameters[param.name][0]"
                        type="number"
                        class="form-control"
                        :required="param.required"
                        placeholder="Min"
                        />
                    </div>
                    <div class="col">
                        <label class="form-label small">To</label>
                        <input 
                        :id="param.name + '_to'"
                        v-model="parameters[param.name][1]"
                        type="number"
                        class="form-control"
                        :required="param.required"
                        placeholder="Max"
                        />
                    </div>
                    </div>
                    
                    <!-- Fallback for unknown field types -->
                    <input 
                    v-else
                    :id="param.name"
                    v-model="parameters[param.name]"
                    type="text"
                    class="form-control"
                    :required="param.required"
                    :placeholder="`Enter ${param.label.toLowerCase()}`"
                    />
                    
                    <div v-if="param.field_type === 'year_enhanced'" class="form-text text-muted">
                    Enter a single year, comma-separated years, or a year range (e.g., 2020-2024). You can also combine formats like: 2024,2022-2023
                    </div>
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
import $ from 'jquery';
import 'select2/dist/css/select2.min.css';
import 'select2/dist/js/select2.min.js';

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
      previewData: null,
      
      // Select2 instances
      select2Instances: {},
      filterPost2024Only: true,
    };
  },
  computed: {
    canGenerate() {
      if (!this.selectedReport || !this.exportFormat) return false;
      
      // Check required parameters
      if (this.selectedReport.parameters) {
        for (const param of this.selectedReport.parameters) {
          if (param.required) {
            const value = this.parameters[param.name];
            
            if (param.field_type === 'multiselect') {
              if (!value || !Array.isArray(value) || value.length === 0) {
                return false;
              }
            } else if (param.field_type === 'range') {
              if (!value || !Array.isArray(value) || value.length < 2 || 
                  !value[0] || !value[1]) {
                return false;
              }
            } else if (param.field_type === 'year_enhanced') {
                // Validate enhanced year format
                if (!this.validateEnhancedYear(value)) {
                return false;
                }
            } else {
              if (!value && value !== 0) { // Allow 0 as valid number
                return false;
              }
            }
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
          if (param.required) {
            const value = this.parameters[param.name];
            
            if (param.field_type === 'multiselect') {
              if (!value || !Array.isArray(value) || value.length === 0) {
                return false;
              }
            } else if (param.field_type === 'range') {
              if (!value || !Array.isArray(value) || value.length < 2 || 
                  !value[0] || !value[1]) {
                return false;
              }
            } else {
              if (!value && value !== 0) {
                return false;
              }
            }
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

    validateEnhancedYear(value) {
        if (!value) return false;
        
        const valueStr = String(value).trim();
        if (valueStr === '') return false;
        
        // Split by comma to handle multiple inputs
        const parts = valueStr.split(',').map(p => p.trim());
        
        for (const part of parts) {
        // Check if it's a range (contains '-')
        if (part.includes('-')) {
            const rangeParts = part.split('-');
            if (rangeParts.length !== 2) return false;
            
            const start = rangeParts[0].trim();
            const end = rangeParts[1].trim();
            
            // Both must be non-empty
            if (!start || !end) return false;
            
            // Both should be valid years
            if (!this.isValidYear(start) || !this.isValidYear(end)) return false;
            
            // Start should be <= end
            if (parseInt(start) > parseInt(end)) return false;
        } else {
            // Single year
            if (!this.isValidYear(part)) return false;
        }
        }
        
        return true;
    },
    
    isValidYear(value) {
        if (!value) return false;
        const year = parseInt(value);
        if (isNaN(year)) return false;
        const currentYear = new Date().getFullYear();
        return year >= 1900 && year <= currentYear + 10; // Allow up to 10 years in future
    },

    isOptionSelected(paramName, option) {
      return this.parameters[paramName] && this.parameters[paramName].includes(option);
    },
    
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
    
    async onReportChange() {
      this.selectedReport = this.availableReports.find(
        r => r.id === this.selectedReportId
      );
      
      // Reset parameters
      this.parameters = {};
      this.customClauses = [];
      this.availableFields = [];
      
      // Initialize parameters based on field_type
      if (this.selectedReport?.parameters) {
        this.selectedReport.parameters.forEach(param => {
          if (param.field_type === 'multiselect') {
            // Initialize as empty array for multiselect
            this.parameters[param.name] = [];
          } else if (param.field_type === 'range') {
            this.parameters[param.name] = ['', ''];
          } else if (param.default_value) {
            this.parameters[param.name] = param.default_value;
          } else {
            // Initialize with empty string for other types
            this.parameters[param.name] = '';
          }
        });
      }
      
      // Set default export format
      if (this.selectedReport?.export_formats?.length > 0) {
        this.exportFormat = this.selectedReport.export_formats[0];
      }
      
      // Fetch available fields for this report
      if (this.selectedReportId) {
        await this.fetchAvailableFields(this.selectedReportId);
      }
      
      // Re-initialize Select2 after Vue has updated the DOM
      this.$nextTick(() => {
        // Destroy existing Select2 instances
        this.destroySelect2Instances();
        
        // Wait for DOM to fully update
        setTimeout(() => {
          this.initializeSelect2();
        }, 200);
      });
    },
    
    initializeSelect2() {
      // Initialize multi-selects with Select2 (tag mode)
      $('.select2-multiple-tags').each((index, element) => {
        const $element = $(element);
        const paramName = element.id.replace('multiselect-', '');
        
        // Destroy existing Select2 instance if any
        if ($element.data('select2')) {
          $element.select2('destroy');
        }
        
        // Store reference
        this.select2Instances[paramName] = $element;
        
        // Initialize Select2 with simpler configuration
        $element.select2({
          theme: 'bootstrap-5',
          placeholder: 'Select options...',
          allowClear: true,
          width: '100%',
          closeOnSelect: false,
          multiple: true,
          tags: false
        }).on('change', (e) => {
          const paramName = e.target.id.replace('multiselect-', '');
          const values = Array.from($(e.target).val() || []);
          this.parameters[paramName] = values;
        });
        
        // Set initial value if any
        const currentValues = this.parameters[paramName] || [];
        if (currentValues && currentValues.length > 0) {
          $element.val(currentValues).trigger('change');
        }
      });
    },

    destroySelect2Instances() {
      // Destroy all Select2 instances
      Object.values(this.select2Instances).forEach($element => {
        if ($element.data('select2')) {
          $element.select2('destroy');
        }
      });
      this.select2Instances = {};
      
      // Also destroy any other Select2 instances that might have been created
      $('.form-select').each((index, element) => {
        const $element = $(element);
        if ($element.data('select2')) {
          $element.select2('destroy');
        }
      });
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
    
    async generateReport() {
      if (!this.canGenerate) return;
      
      this.generating = true;
      
      try {
        // Prepare request data
        const requestData = {
          parameters: {},
          export_format: this.exportFormat
        };
        
        // Process parameters for backend
        Object.keys(this.parameters).forEach(key => {
          const value = this.parameters[key];
          if (Array.isArray(value)) {
            // For multiselect, send array
            // For range, we need to check if it's a range field
            const paramConfig = this.selectedReport.parameters.find(p => p.name === key);
            if (paramConfig && paramConfig.field_type === 'range') {
              // Range should be sent as [min, max]
              requestData.parameters[key] = value;
            } else {
              // Multiselect - filter out empty strings
              requestData.parameters[key] = value.filter(v => v !== '' && v != null);
            }
          } else {
            requestData.parameters[key] = value;
          }
        });
        
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
                          this.exportFormat === 'csv' ? 'csv' : 
                          this.exportFormat === 'shapefile' ? 'shz' : 'pdf';
          a.download = `${this.selectedReport.name.replace(/\s+/g, '_')}_${timestamp}.${extension}`;
          
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
              // For arrays, send each value as separate param
              const filteredValues = value.filter(v => v !== '' && v != null);
              filteredValues.forEach(v => params.append(`param_${key}`, v));
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
      
      this.destroySelect2Instances();
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
  },
  
  // Clean up Select2 when component is destroyed
  beforeUnmount() {
    this.destroySelect2Instances();
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

/* Accordion customizations */
.accordion-button:not(.collapsed) {
  background-color: #f8f9fa;
  color: #0d6efd;
}

.accordion-button:focus {
  box-shadow: none;
  border-color: rgba(0, 0, 0, 0.125);
}

pre {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 5px;
  border: 1px solid #404040;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  tab-size: 2;
}

/* Range input styling */
.form-label.small {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6c757d;
}

/* Custom styles for Select2 integration */
.select2-container--bootstrap-5 .select2-selection--multiple {
  min-height: 42px;
  padding: 0.375rem 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 0.375rem;
}

.select2-container--bootstrap-5 .select2-selection--multiple .select2-selection__rendered {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
  min-height: 24px;
}

.select2-container--bootstrap-5 .select2-selection--multiple .select2-selection__choice {
  background-color: #0d6efd;
  color: white;
  border: none;
  border-radius: 0.25rem;
  padding: 0.25rem 0.5rem;
  margin: 2px;
  display: flex;
  align-items: center;
  font-size: 0.875rem;
}

.select2-container--bootstrap-5 .select2-selection--multiple .select2-selection__choice__remove {
  color: white;
  margin-left: 0.5rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0;
}

.select2-container--bootstrap-5 .select2-selection--multiple .select2-selection__choice__remove:hover {
  color: #ffcccb;
}

.select2-container--bootstrap-5 .select2-selection--multiple .select2-search--inline {
  flex: 1;
  min-width: 60px;
}

.select2-container--bootstrap-5 .select2-selection--multiple .select2-search__field {
  margin-top: 0;
  height: 24px;
}

/* Ensure the dropdown appears correctly */
.select2-container--bootstrap-5.select2-container--open .select2-dropdown {
  z-index: 1060;
  border: 1px solid #ced4da;
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.select2-container--bootstrap-5 .select2-dropdown .select2-results__option {
  padding: 0.5rem 1rem;
}

.select2-container--bootstrap-5 .select2-dropdown .select2-results__option--selected {
  background-color: #e7f1ff;
  color: #0d6efd;
}

.select2-container--bootstrap-5 .select2-dropdown .select2-results__option--highlighted {
  background-color: #0d6efd;
  color: white;
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

/* Fix for Select2 dropdown positioning */
.select2-container {
  z-index: 1055 !important;
}

.select2-dropdown {
  z-index: 1060 !important;
}

/* Make Select2 look consistent with Bootstrap form controls */
.select2-container--bootstrap-5 .select2-selection {
  min-height: calc(1.5em + 0.75rem + 2px);
  padding: 0.375rem 0.75rem;
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.5;
  color: #212529;
  background-color: #fff;
  background-clip: padding-box;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.select2-container--bootstrap-5 .select2-selection:focus {
  border-color: #86b7fe;
  outline: 0;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

/* Make the multi-select look like a single select when empty */
.select2-container--bootstrap-5 .select2-selection--multiple:not(.select2-selection--multiple-selected) .select2-selection__rendered::before {
  content: "Select options";
  color: #6c757d;
  font-style: italic;
}

/* Style for when items are selected */
.select2-container--bootstrap-5 .select2-selection--multiple.select2-selection--multiple-selected .select2-selection__rendered::before {
  display: none;
}

/* Better visual feedback for selected tags */
.select2-selection__choice {
  position: relative;
  padding-right: 1.5rem !important;
}

.select2-selection__choice__remove {
  position: absolute;
  right: 0.25rem;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0.7;
}

.select2-selection__choice__remove:hover {
  opacity: 1;
}

/* Hide the original select arrow for Select2 elements */
.select2-multiple-tags {
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%23343a40' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 16px 12px;
}

/* Ensure proper spacing in form */
.form-group .select2-container {
  margin-bottom: 0;
}
</style>
