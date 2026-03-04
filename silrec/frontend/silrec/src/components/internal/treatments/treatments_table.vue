<template>
  <div class="treatments-table-container">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/treatments/treatments_table.vue</div>
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
        :collapsed="false"
        :filter_warning_icon="filterWarningIcon"
        @created="collapsible_component_mounted"
      >
        <div class="row mt-1 p-2">
          <!-- Task Classification Filter (Parent) -->
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterTaskClassification">Task Classification</label>
              <select
                v-model="filterTaskClassificationId"
                class="form-select"
                id="filterTaskClassification"
                @change="onTaskClassificationChange"
              >
                <option value="all">All Classifications</option>
                <option 
                  v-for="classification in taskClassifications" 
                  :key="classification.id"
                  :value="classification.id"
                >
                  {{ classification.task_class }} - {{ classification.description }}
                </option>
              </select>
            </div>
          </div>
          
          <!-- Task Filter (Child - dependent on classification) -->
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterTask">Task</label>
              <div class="searchable-select">
                <input
                  id="filterTask"
                  v-model="taskSearch"
                  type="text"
                  class="form-control"
                  :placeholder="taskPlaceholder"
                  :disabled="isTaskDisabled"
                  @focus="onTaskFocus"
                  @blur="onTaskBlur"
                  @input="filterTasks"
                />
                <div v-if="showTaskDropdown" class="dropdown-options">
                  <div 
                    class="dropdown-option all-tasks-option"
                    @mousedown="selectAllTasks"
                  >
                    <strong>All Tasks</strong>
                  </div>
                  <div 
                    v-for="task in filteredTasks" 
                    :key="task.id"
                    class="dropdown-option"
                    @mousedown="selectTask(task)"
                  >
                    <strong>{{ task.task }}</strong> - {{ task.task_name || 'No description' }}
                  </div>
                  <div v-if="filteredTasks.length === 0 && taskSearch !== '' && taskSearch !== 'All Tasks'" class="dropdown-option no-results">
                    No tasks found
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="row mt-1 p-2">
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
                  :placeholder="statusPlaceholder"
                  @focus="onStatusFocus"
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
          <div class="col-md-3">
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
      required: false
    },
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      datatableId: 'treatments-table-' + uuid(),
      
      filterTask: '',
      filterTaskClassificationId: 'all',
      filterStatus: 'all',
      filterPlanYear: '',
      filterPlanMonth: 'all',
      filterCompleteDateFrom: '',
      filterCompleteDateTo: '',
      filterMachine: '',
      filterOperator: '',
      filterPost2024Only: true,

      lookups: {
        tasksWithClassification: null,
        treatment_statuses: [],
        machines: []
      },
      loadingLookups: false,
      lookupError: null,

      taskSearch: '',
      showTaskDropdown: false,
      filteredTasks: [],
      taskInputFocused: false,

      statusSearch: '',
      showStatusDropdown: false,
      filteredStatuses: [],
      statusInputFocused: false,

      machineSearch: '',
      showMachineDropdown: false,
      filteredMachines: []
    };
  },
  computed: {
    taskClassifications() {
      return this.lookups.tasksWithClassification?.classifications || [];
    },
    
    allTasks() {
      return this.lookups.tasksWithClassification?.tasks || [];
    },
    
    isTaskDisabled() {
      return !this.lookups.tasksWithClassification?.classification_table_exists || 
             (this.filterTaskClassificationId !== 'all' && this.taskClassifications.length === 0);
    },
    
    dtHeaders() {
      const headers = [
        'Treatment ID',
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
        ordering: true,
        paging: true,
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        
        ajax: {
          url: api_endpoints.treatments,
          type: 'GET',
          data: function(d) {
            d.cohort_id = vm.cohortId;
            d.filter_task = vm.filterTask;
            d.filter_task_classification_id = vm.filterTaskClassificationId;
            d.filter_status = vm.filterStatus;
            d.filter_plan_year = vm.filterPlanYear;
            d.filter_plan_month = vm.filterPlanMonth;
            d.filter_complete_date_from = vm.filterCompleteDateFrom;
            d.filter_complete_date_to = vm.filterCompleteDateTo;
            d.filter_machine = vm.filterMachine;
            d.filter_operator = vm.filterOperator;
            d.filter_post_2024_only = vm.filterPost2024Only;
          },
          dataSrc: function (json) {
            return json.data;
          }
        },
        
        columns: [
          {
            data: 'treatment_id',
            name: 'treatment_id',
            visible: true,
            orderable: true
          },
          {
            data: 'task',
            name: 'task__name',
            orderable: true,
            render: function(data, type, row) {
              return row?.task || 'N/A';
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
                actions += `<a href="/internal/treatment/${data}" class="btn btn-sm btn-outline-primary me-1" title="Edit Treatment">
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
          processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span>',
          emptyTable: 'No treatments found',
          info: 'Showing _START_ to _END_ of _TOTAL_ treatments',
          infoEmpty: 'Showing 0 to 0 of 0 treatments',
          infoFiltered: '(filtered from _MAX_ total treatments)',
          lengthMenu: 'Show _MENU_ treatments',
          loadingRecords: 'Loading...',
          search: 'Search:',
          zeroRecords: 'No matching treatments found'
        },
        
        drawCallback: function(settings) {
          vm.attachEventListeners();
        }
      };
    },
    areFiltersActive() {
      return this.filterTask !== '' ||
             this.filterTaskClassificationId !== 'all' ||
             this.filterStatus !== 'all' ||
             this.filterPlanYear !== '' ||
             this.filterPlanMonth !== 'all' ||
             this.filterCompleteDateFrom !== '' ||
             this.filterCompleteDateTo !== '' ||
             this.filterMachine !== '' ||
             this.filterOperator !== '' ||
             this.filterPost2024Only !== true;
    },
    filterWarningIcon() {
      return this.areFiltersActive ? 'filter-active' : 'filter-clear';
    },
    taskPlaceholder() {
      if (this.isTaskDisabled) {
        return 'Select classification first';
      }
      return (this.taskSearch === '' || this.taskInputFocused) ? 'Type to search tasks...' : '';
    },
    statusPlaceholder() {
      return (this.statusSearch === '' || this.statusInputFocused) ? 'Type to search statuses...' : '';
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

            this.lookups.tasksWithClassification = data.tasks_with_classification;
            this.lookups.treatment_statuses = data.treatment_statuses || [];
            this.lookups.machines = data.machines || [];

            // Initialize filtered lists
            this.updateFilteredTasks();
            this.filteredStatuses = [...this.lookups.treatment_statuses];
            this.filteredMachines = [...this.lookups.machines];

        } catch (error) {
            console.error('Error loading lookups:', error);
            this.lookupError = error.message;
            await swal.fire({
                icon: 'error',
                title: 'Load Failed',
                text: 'Failed to load lookup data',
                confirmButtonText: 'OK'
            });
        } finally {
            this.loadingLookups = false;
        }
    },

    onTaskClassificationChange() {
      // Clear selected task when classification changes
      this.filterTask = '';
      this.taskSearch = '';
      this.showTaskDropdown = false;
      
      // Update filtered tasks based on new classification
      this.updateFilteredTasks();
      
      // Refresh the data table
      this.refreshData();
    },

    updateFilteredTasks() {
      if (!this.allTasks.length) {
        this.filteredTasks = [];
        return;
      }

      if (this.filterTaskClassificationId === 'all') {
        // Show all tasks
        this.filteredTasks = [...this.allTasks];
      } else {
        // Filter tasks by selected classification
        this.filteredTasks = this.allTasks.filter(task => 
          task.classification && task.classification.id === parseInt(this.filterTaskClassificationId)
        );
      }
    },

    filterTasks() {
      const searchTerm = this.taskSearch.toLowerCase();
      let tasksToFilter = this.filteredTasks; // Start with already filtered by classification
      
      if (searchTerm !== '' && searchTerm !== 'all tasks') {
        tasksToFilter = tasksToFilter.filter(task => 
          task.task.toLowerCase().includes(searchTerm) ||
          (task.task_name && task.task_name.toLowerCase().includes(searchTerm))
        );
      }
      
      this.filteredTasks = tasksToFilter;
    },
    
    onTaskFocus() {
      if (this.isTaskDisabled) return;
      
      this.taskInputFocused = true;
      this.showTaskDropdown = true;
      if (this.taskSearch === 'All Tasks') {
        this.taskSearch = '';
      }
    },
    
    selectAllTasks() {
      this.filterTask = '';
      this.taskSearch = 'All Tasks';
      this.taskInputFocused = false;
      this.showTaskDropdown = false;
      this.refreshData();
    },
    
    selectTask(task) {
      this.filterTask = task.task;
      this.taskSearch = `${task.task} - ${task.task_name || ''}`;
      this.taskInputFocused = false;
      this.showTaskDropdown = false;
      this.refreshData();
    },
    
    onTaskBlur() {
      this.taskInputFocused = false;
      setTimeout(() => {
        this.showTaskDropdown = false;
        if (this.taskSearch === '' && !this.isTaskDisabled) {
          this.taskSearch = 'All Tasks';
        }
      }, 200);
    },

    filterStatuses() {
      const searchTerm = this.statusSearch.toLowerCase();
      this.filteredStatuses = this.lookups.treatment_statuses.filter(status => 
        status.status.toLowerCase().includes(searchTerm) ||
        (status.name && status.name.toLowerCase().includes(searchTerm))
      );
    },
    
    onStatusFocus() {
      this.statusInputFocused = true;
      this.showStatusDropdown = true;
      if (this.statusSearch === 'All Status') {
        this.statusSearch = '';
      }
    },
    
    selectStatus(status) {
      if (status.status === 'all') {
        this.filterStatus = 'all';
        this.statusSearch = 'All Status';
        this.filteredStatuses = [...this.lookups.treatment_statuses];
      } else {
        this.filterStatus = status.status;
        this.statusSearch = `${status.status} - ${status.name || ''}`;
      }
      this.statusInputFocused = false;
      this.showStatusDropdown = false;
      this.refreshData();
    },
    
    onStatusBlur() {
      this.statusInputFocused = false;
      setTimeout(() => {
        this.showStatusDropdown = false;
        if (this.statusSearch === '') {
          this.statusSearch = 'All Status';
        }
      }, 200);
    },

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
        this.$refs.treatments_datatable.vmDataTable.ajax.reload(null, false);
      }
    },

    clearFilters() {
      this.filterTask = '';
      this.filterTaskClassificationId = 'all';
      this.filterStatus = 'all';
      this.filterPlanYear = '';
      this.filterPlanMonth = 'all';
      this.filterCompleteDateFrom = '';
      this.filterCompleteDateTo = '';
      this.filterMachine = '';
      this.filterOperator = '';
      this.filterPost2024Only = true;

      this.taskSearch = '';
      this.statusSearch = '';
      this.machineSearch = '';

      this.taskInputFocused = false;
      this.statusInputFocused = false;

      this.updateFilteredTasks();
      this.filteredStatuses = [...this.lookups.treatment_statuses];
      this.filteredMachines = [...this.lookups.machines];

      this.refreshData();
    },
    collapsible_component_mounted() {
      this.$nextTick(() => {
        this.updateFilterIconColor();
      });
    },
    updateFilterIconColor() {
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

      $(this.$el).off('click', '.delete-treatment-btn');

      $(this.$el).on('click', '.delete-treatment-btn', function() {
        const treatmentId = $(this).data('treatment-id');
        vm.deleteTreatment(treatmentId);
      });
    },
    async deleteTreatment(treatmentId) {
        const result = await swal.fire({
            icon: 'warning',
            title: 'Are you sure?',
            text: 'Are you sure you want to delete this treatment?',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it!',
            cancelButtonText: 'Cancel',
            confirmButtonColor: '#d33'
        });

        if (!result.isConfirmed) {
            return;
        }

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

            await swal.fire({
                icon: 'success',
                title: 'Deleted!',
                text: 'Treatment deleted successfully',
                timer: 3000,
                showConfirmButton: false
            });
        } catch (error) {
            console.error('Error deleting treatment:', error);
            await swal.fire({
                icon: 'error',
                title: 'Delete Failed',
                text: 'Failed to delete treatment',
                confirmButtonText: 'OK'
            });
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
    filterTaskClassificationId: {
      handler() {
        this.updateFilteredTasks();
      }
    },
    filterTask() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterTaskClassificationId() {
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
    filterPost2024Only() {
      this.refreshData();
      this.$nextTick(() => this.updateFilterIconColor());
    },
    filterWarningIcon: {
      handler(newVal) {
        this.$nextTick(() => this.updateFilterIconColor());
      }
    }
  },
  mounted() {
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
  z-index: 9999;
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

:deep(.collapsible-component .filter_warning_icon) {
  transition: color 0.3s ease !important;
}

:deep(.collapsible-component .filter_warning_icon.filter-active) {
  color: #dc3545 !important;
}

:deep(.collapsible-component .filter_warning_icon.filter-clear) {
  color: #28a745 !important;
}

:deep(div.collapsible-component i.filter_warning_icon) {
  transition: color 0.3s ease !important;
}

:deep(div.collapsible-component i.filter_warning_icon.filter-active) {
  color: #dc3545 !important;
}

:deep(div.collapsible-component i.filter_warning_icon.filter-clear) {
  color: #28a745 !important;
}

.searchable-select:has(.dropdown-options) {
  z-index: 9998;
}

.searchable-select .form-control:focus {
  z-index: 9999;
  position: relative;
}

.form-control::placeholder {
  color: #6c757d;
  opacity: 0.8;
}

.form-control:focus::placeholder {
  opacity: 0.6;
}
</style>

<style>
.searchable-select .dropdown-options {
  z-index: 10000 !important;
}

.modal .searchable-select .dropdown-options {
  z-index: 10050 !important;
}

.searchable-select {
  isolation: isolate;
}

.treatments-table-container .collapsible-component .filter_warning_icon.filter-active {
  color: #dc3545 !important;
}

.treatments-table-container .collapsible-component .filter_warning_icon.filter-clear {
  color: #28a745 !important;
}
</style>
