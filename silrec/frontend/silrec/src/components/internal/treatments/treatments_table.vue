<template>
  <div class="treatments-table-container">
    <div class="table-controls mb-3">
      <div class="row align-items-center">
        <div class="col-md-6">
          <h5>Treatments</h5>
        </div>
        <div class="col-md-6 text-end">
          <button 
            class="btn btn-sm btn-outline-primary"
            @click="refreshData"
            title="Refresh data"
          >
            <i class="bi bi-arrow-clockwise"></i>
            Refresh
          </button>
        </div>
      </div>
    </div>

    <div class="filters-wrapper mb-3">
      <CollapsibleFilters
        ref="collapsible_filters"
        component_title="Treatment Filters"
        class="mb-2"
        :filter_warning_icon="filterWarningIcon"
        @created="collapsible_component_mounted"
      >
        <div class="row mt-1 p-2">
          <!-- Task Filter -->
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterTask">Task</label>
              <div class="searchable-select">
                <input
                  id="filterTask"
                  v-model="taskSearch"
                  type="text"
                  class="form-control"
                  placeholder="Type to search tasks..."
                  @focus="showTaskDropdown = true"
                  @blur="onTaskBlur"
                  @input="filterTasks"
                />
                <div v-if="showTaskDropdown" class="dropdown-options">
                  <div 
                    v-for="task in filteredTasks" 
                    :key="task.id"
                    class="dropdown-option"
                    @mousedown="selectTask(task)"
                  >
                    <strong>{{ task.task }}</strong> - {{ task.task_name || 'No description' }}
                  </div>
                  <div v-if="filteredTasks.length === 0" class="dropdown-option no-results">
                    No tasks found
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Status Filter -->
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterStatus">Status</label>
              <div class="searchable-select">
                <input
                  id="filterStatus"
                  v-model="statusSearch"
                  type="text"
                  class="form-control"
                  placeholder="Type to search statuses..."
                  @focus="showStatusDropdown = true"
                  @blur="onStatusBlur"
                  @input="filterStatuses"
                />
                <div v-if="showStatusDropdown" class="dropdown-options">
                  <div class="dropdown-option" @mousedown="selectStatus({ status: 'all', name: 'All Status' })">
                    All Status
                  </div>
                  <div 
                    v-for="status in filteredStatuses" 
                    :key="status.id"
                    class="dropdown-option"
                    @mousedown="selectStatus(status)"
                  >
                    <strong>{{ status.status }}</strong> - {{ status.name || 'No description' }}
                  </div>
                  <div v-if="filteredStatuses.length === 0" class="dropdown-option no-results">
                    No statuses found
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="col-md-3">
            <div class="form-group">
              <label for="filterPlanYear">Planned Year</label>
              <input
                v-model="filterPlanYear"
                type="number"
                class="form-control"
                id="filterPlanYear"
                placeholder="Year..."
                min="2000"
                :max="new Date().getFullYear() + 10"
              />
            </div>
          </div>
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterPlanMonth">Planned Month</label>
              <select
                v-model="filterPlanMonth"
                class="form-select"
                id="filterPlanMonth"
              >
                <option value="all">All Months</option>
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
        <div class="row p-2">
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterCompleteDateFrom">Complete Date From</label>
              <input
                v-model="filterCompleteDateFrom"
                type="date"
                class="form-control"
                id="filterCompleteDateFrom"
              />
            </div>
          </div>
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterCompleteDateTo">Complete Date To</label>
              <input
                v-model="filterCompleteDateTo"
                type="date"
                class="form-control"
                id="filterCompleteDateTo"
              />
            </div>
          </div>

          <!-- Machine Filter -->
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterMachine">Machine</label>
              <div class="searchable-select">
                <input
                  id="filterMachine"
                  v-model="machineSearch"
                  type="text"
                  class="form-control"
                  placeholder="Type to search machines..."
                  @focus="showMachineDropdown = true"
                  @blur="onMachineBlur"
                  @input="filterMachines"
                />
                <div v-if="showMachineDropdown" class="dropdown-options">
                  <div 
                    v-for="machine in filteredMachines" 
                    :key="machine.id"
                    class="dropdown-option"
                    @mousedown="selectMachine(machine)"
                  >
                    <strong>{{ machine.manufacturer }} {{ machine.model }}</strong> - {{ machine.machine_type || 'No type' }}
                  </div>
                  <div v-if="filteredMachines.length === 0" class="dropdown-option no-results">
                    No machines found
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="row p-2">
          <div class="col-md-12 text-end">
            <button 
              class="btn btn-sm btn-outline-secondary me-2"
              @click="clearFilters"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </CollapsibleFilters>
    </div>

    <div class="table-wrapper">
      <datatable
        :id="datatableId"
        ref="treatments_datatable"
        :dt-options="dtOptions"
        :dt-headers="dtHeaders"
      />
    </div>
  </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import { api_endpoints } from '@/utils/hooks';
import { v4 as uuid } from 'uuid';

export default {
  name: 'TreatmentsTable',
  components: {
    datatable,
    CollapsibleFilters,
  },
  props: {
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
      datatableId: 'treatments-table-' + uuid(),
      
      // Original filters
      filterTask: '',
      filterStatus: 'all',
      filterPlanYear: '',
      filterPlanMonth: 'all',
      filterCompleteDateFrom: '',
      filterCompleteDateTo: '',
      filterMachine: '',
      filterOperator: '',

      // Lookup data
      lookups: {
        tasks: [],
        treatment_statuses: [],
        machines: []
      },
      loadingLookups: false,
      lookupError: null,

      // Search and dropdown states for Task
      taskSearch: '',
      showTaskDropdown: false,
      filteredTasks: [],

      // Search and dropdown states for Status
      statusSearch: '',
      showStatusDropdown: false,
      filteredStatuses: [],

      // Search and dropdown states for Machine
      machineSearch: '',
      showMachineDropdown: false,
      filteredMachines: []
    };
  },
  computed: {
    dtHeaders() {
      const headers = [
        'ID',
        'Task',
        'Planned Year',
        'Planned Month',
        'Status',
        'Complete Date',
        'Actions'
      ];
      return headers;
    },
    dtOptions() {
      const vm = this;
      
      return {
        autoWidth: false,
        responsive: true,
        serverSide: true,
        searching: true,
        processing: true,
        ajax: {
          url: api_endpoints.treatments,
          dataSrc: 'data',
          data: function(d) {
            d.cohort_id = vm.cohortId;
            d.filter_task = vm.filterTask;
            d.filter_status = vm.filterStatus;
            d.filter_plan_year = vm.filterPlanYear;
            d.filter_plan_month = vm.filterPlanMonth;
            d.filter_complete_date_from = vm.filterCompleteDateFrom;
            d.filter_complete_date_to = vm.filterCompleteDateTo;
            d.filter_machine = vm.filterMachine;
            d.filter_operator = vm.filterOperator;
          }
        },
        columns: [
          {
            data: 'treatment_id',
            name: 'treatment_id',
            visible: false
          },
          {
            data: 'task',
            name: 'task__name',
            orderable: true,
            render: function(data, type, row) {
              return data?.name || 'N/A';
            }
          },
          {
            data: 'plan_yr',
            name: 'plan_yr',
            orderable: true,
            render: function(data) {
              return data || 'N/A';
            }
          },
          {
            data: 'plan_mth',
            name: 'plan_mth',
            orderable: true,
            render: function(data) {
              if (!data) return 'N/A';
              const months = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
              ];
              return months[data - 1] || data;
            }
          },
          {
            data: 'status',
            name: 'status',
            orderable: true,
            render: function(data) {
              const statusMap = {
                'P': 'Planned',
                'D': 'Completed',
                'C': 'Cancelled',
                'F': 'Failed',
                'W': 'Written Off',
                'X': 'Not Required'
              };
              return statusMap[data] || data;
            }
          },
          {
            data: 'complete_date',
            name: 'complete_date',
            orderable: true,
            render: function(data) {
              return data ? new Date(data).toLocaleDateString() : 'N/A';
            }
          },
          {
            data: 'treatment_id',
            orderable: false,
            searchable: false,
            className: 'action-column',
            render: function(data, type, row) {
              let actions = '';
              if (!vm.readOnly) {
                actions += `<a href="#/internal/treatment/${data}" class="btn btn-sm btn-outline-primary me-1" title="Edit Treatment">
                  <i class="bi bi-pencil"></i>
                </a>`;
                actions += `<button class="btn btn-sm btn-outline-danger delete-treatment-btn" data-treatment-id="${data}" title="Delete Treatment">
                  <i class="bi bi-trash"></i>
                </button>`;
              } else {
                actions += `<a href="#/internal/treatment/${data}" class="btn btn-sm btn-outline-info" title="View Treatment">
                  <i class="bi bi-eye"></i>
                </a>`;
              }
              return actions;
            }
          }
        ],
        dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
        language: {
          processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span>'
        },
        drawCallback: function(settings) {
          vm.attachEventListeners();
        }
      };
    },
    // Check if any filter is active
    areFiltersActive() {
      return this.filterTask !== '' ||
             this.filterStatus !== 'all' ||
             this.filterPlanYear !== '' ||
             this.filterPlanMonth !== 'all' ||
             this.filterCompleteDateFrom !== '' ||
             this.filterCompleteDateTo !== '' ||
             this.filterMachine !== '' ||
             this.filterOperator !== '';
    },
    // Determine filter warning icon state - return class name string
    filterWarningIcon() {
      return this.areFiltersActive ? 'filter-active' : 'filter-clear';
    }
  },
  methods: {
    async loadLookups() {
      this.loadingLookups = true;
      this.lookupError = null;
      
      try {
        const response = await fetch(api_endpoints.combined_lookups);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Extract the lookup data we need
        this.lookups.tasks = data.tasks || [];
        this.lookups.treatment_statuses = data.treatment_statuses || [];
        this.lookups.machines = data.machines || [];
        
        // Initialize filtered lists with all items
        this.filteredTasks = [...this.lookups.tasks];
        this.filteredStatuses = [...this.lookups.treatment_statuses];
        this.filteredMachines = [...this.lookups.machines];
        
        console.log('Lookups loaded successfully:', {
          tasks: this.lookups.tasks.length,
          treatment_statuses: this.lookups.treatment_statuses.length,
          machines: this.lookups.machines.length
        });
        
      } catch (error) {
        console.error('Error loading lookups:', error);
        this.lookupError = error.message;
      } finally {
        this.loadingLookups = false;
      }
    },

    // Task methods
    filterTasks() {
      const searchTerm = this.taskSearch.toLowerCase();
      this.filteredTasks = this.lookups.tasks.filter(task => 
        task.task.toLowerCase().includes(searchTerm) ||
        (task.task_name && task.task_name.toLowerCase().includes(searchTerm))
      );
    },
    
    selectTask(task) {
      this.filterTask = task.task;
      this.taskSearch = `${task.task} - ${task.task_name || ''}`;
      this.showTaskDropdown = false;
      this.refreshData();
    },
    
    onTaskBlur() {
      setTimeout(() => {
        this.showTaskDropdown = false;
      }, 200);
    },

    // Status methods
    filterStatuses() {
      const searchTerm = this.statusSearch.toLowerCase();
      this.filteredStatuses = this.lookups.treatment_statuses.filter(status => 
        status.status.toLowerCase().includes(searchTerm) ||
        (status.name && status.name.toLowerCase().includes(searchTerm))
      );
    },
    
    selectStatus(status) {
      if (status.status === 'all') {
        this.filterStatus = 'all';
        this.statusSearch = 'All Status';
      } else {
        this.filterStatus = status.status;
        this.statusSearch = `${status.status} - ${status.name || ''}`;
      }
      this.showStatusDropdown = false;
      this.refreshData();
    },
    
    onStatusBlur() {
      setTimeout(() => {
        this.showStatusDropdown = false;
      }, 200);
    },

    // Machine methods
    filterMachines() {
      const searchTerm = this.machineSearch.toLowerCase();
      this.filteredMachines = this.lookups.machines.filter(machine => 
        (machine.manufacturer && machine.manufacturer.toLowerCase().includes(searchTerm)) ||
        (machine.model && machine.model.toLowerCase().includes(searchTerm)) ||
        (machine.machine_type && machine.machine_type.toLowerCase().includes(searchTerm))
      );
    },
    
    selectMachine(machine) {
      this.filterMachine = machine.model || machine.manufacturer;
      this.machineSearch = `${machine.manufacturer} ${machine.model}`;
      this.showMachineDropdown = false;
      this.refreshData();
    },
    
    onMachineBlur() {
      setTimeout(() => {
        this.showMachineDropdown = false;
      }, 200);
    },

    refreshData() {
      if (this.$refs.treatments_datatable && this.$refs.treatments_datatable.vmDataTable) {
        this.$refs.treatments_datatable.vmDataTable.ajax.reload();
      }
    },
    clearFilters() {
      // Clear original filter values
      this.filterTask = '';
      this.filterStatus = 'all';
      this.filterPlanYear = '';
      this.filterPlanMonth = 'all';
      this.filterCompleteDateFrom = '';
      this.filterCompleteDateTo = '';
      this.filterMachine = '';
      this.filterOperator = '';

      // Clear search inputs
      this.taskSearch = '';
      this.statusSearch = 'All Status';
      this.machineSearch = '';

      this.refreshData();
    },
    collapsible_component_mounted() {
      // Filter warning icon logic is now handled by computed property
      console.log('Filters mounted, current state:', this.filterWarningIcon);
      
      // Force update the icon color after mount
      this.$nextTick(() => {
        this.updateFilterIconColor();
      });
    },
    updateFilterIconColor() {
      // Directly manipulate the icon element if needed
      const filterIcon = this.$el.querySelector('.filter_warning_icon');
      if (filterIcon) {
        if (this.areFiltersActive) {
          filterIcon.style.color = '#dc3545';
        } else {
          filterIcon.style.color = '#28a745';
        }
      }
    },
    attachEventListeners() {
      const vm = this;
      
      // Remove existing listeners to prevent duplicates
      $(this.$el).off('click', '.delete-treatment-btn');
      
      $(this.$el).on('click', '.delete-treatment-btn', function() {
        const treatmentId = $(this).data('treatment-id');
        vm.deleteTreatment(treatmentId);
      });
    },
    async deleteTreatment(treatmentId) {
      if (confirm('Are you sure you want to delete this treatment?')) {
        try {
          const response = await fetch(`${api_endpoints.treatments}${treatmentId}/`, {
            method: 'DELETE',
            headers: {
              'X-CSRFToken': this.getCSRFToken()
            }
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          this.refreshData();
          this.$emit('treatment-updated');
        } catch (error) {
          console.error('Error deleting treatment:', error);
          alert('Failed to delete treatment');
        }
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
  watch: {
    cohortId: {
      handler(newVal) {
        if (newVal) {
          this.refreshData();
        }
      },
      immediate: true
    },
    // Watch all filters and refresh data when they change
    filterTask() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterStatus() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterPlanYear() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterPlanMonth() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterCompleteDateFrom() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterCompleteDateTo() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterMachine() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterOperator() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    // Debug watch to see when filterWarningIcon changes
    filterWarningIcon: {
      handler(newVal) {
        console.log('Filter warning icon changed to:', newVal);
        this.$nextTick(() => this.updateFilterIconColor());
      }
    }
  },
  mounted() {
    console.log('Treatments table mounted, initial filter state:', this.filterWarningIcon);
    this.loadLookups();
    this.$nextTick(() => this.updateFilterIconColor());
  }
};
</script>

<style scoped>
.treatments-table-container {
  margin-top: 20px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 15px;
  background-color: #fff;
}

.table-wrapper {
  margin-top: 15px;
}

.table-controls {
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.filters-wrapper {
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 10px;
  background-color: #f8f9fa;
}

/* Ensure datatable responsive design */
:deep(.dataTables_wrapper) {
  font-size: 0.875rem;
}

:deep(.table) {
  margin-bottom: 0;
}

:deep(.btn-sm) {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

:deep(.action-column) {
  white-space: nowrap;
  width: 100px;
}

/* Searchable select styles */
.searchable-select {
  position: relative;
}

.dropdown-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: white;
  border: 1px solid #ced4da;
  border-top: none;
  border-radius: 0 0 0.375rem 0.375rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 9999; /* High z-index to dominate other components */
}

.dropdown-option {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f8f9fa;
  transition: background-color 0.15s ease;
}

.dropdown-option:hover {
  background-color: #f8f9fa;
}

.dropdown-option:last-child {
  border-bottom: none;
}

.dropdown-option.no-results {
  color: #6c757d;
  font-style: italic;
  cursor: default;
}

.dropdown-option.no-results:hover {
  background-color: white;
}

.dropdown-option strong {
  color: #495057;
}

/* More specific filter warning icon styles */
:deep(.collapsible-component .filter_warning_icon) {
  transition: color 0.3s ease !important;
}

:deep(.collapsible-component .filter_warning_icon.filter-active) {
  color: #dc3545 !important;
}

:deep(.collapsible-component .filter_warning_icon.filter-clear) {
  color: #28a745 !important;
}

/* Even more specific targeting */
:deep(div.collapsible-component i.filter_warning_icon) {
  transition: color 0.3s ease !important;
}

:deep(div.collapsible-component i.filter_warning_icon.filter-active) {
  color: #dc3545 !important;
}

:deep(div.collapsible-component i.filter_warning_icon.filter-clear) {
  color: #28a745 !important;
}

/* Ensure the searchable select has high z-index when dropdown is open */
.searchable-select:has(.dropdown-options) {
  z-index: 9998; /* High z-index for the container when dropdown is present */
}

/* Additional styling for when dropdown is visible */
.searchable-select .form-control:focus {
  z-index: 9999; /* Ensure the input is above other elements when focused */
  position: relative;
}
</style>

<style>
/* Global styles to ensure dropdown appears above ALL other elements */
.searchable-select .dropdown-options {
  z-index: 10000 !important; /* Very high z-index to dominate everything */
}

/* Ensure dropdowns appear above modals and other high-z-index elements */
.modal .searchable-select .dropdown-options {
  z-index: 10050 !important; /* Even higher than modals */
}

/* Prevent other elements from interfering */
.searchable-select {
  isolation: isolate; /* Creates a new stacking context */
}

/* Global style that will definitely work */
.treatments-table-container .collapsible-component .filter_warning_icon.filter-active {
  color: #dc3545 !important;
}

.treatments-table-container .collapsible-component .filter_warning_icon.filter-clear {
  color: #28a745 !important;
}
</style>
