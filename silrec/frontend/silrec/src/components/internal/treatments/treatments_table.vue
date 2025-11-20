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
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterTask">Task</label>
              <input
                v-model="filterTask"
                type="text"
                class="form-control"
                id="filterTask"
                placeholder="Filter by task..."
              />
            </div>
          </div>
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterStatus">Status</label>
              <select
                v-model="filterStatus"
                class="form-select"
                id="filterStatus"
              >
                <option value="all">All Status</option>
                <option value="P">Planned</option>
                <option value="D">Completed</option>
                <option value="C">Cancelled</option>
                <option value="F">Failed</option>
                <option value="W">Written Off</option>
                <option value="X">Not Required</option>
              </select>
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
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterMachine">Machine</label>
              <input
                v-model="filterMachine"
                type="text"
                class="form-control"
                id="filterMachine"
                placeholder="Filter by machine..."
              />
            </div>
          </div>
          <div class="col-md-3">
            <div class="form-group">
              <label for="filterOperator">Operator</label>
              <input
                v-model="filterOperator"
                type="text"
                class="form-control"
                id="filterOperator"
                placeholder="Filter by operator..."
              />
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
      
      // Filters
      filterTask: '',
      filterStatus: 'all',
      filterPlanYear: '',
      filterPlanMonth: 'all',
      filterCompleteDateFrom: '',
      filterCompleteDateTo: '',
      filterMachine: '',
      filterOperator: '',
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
    refreshData() {
      if (this.$refs.treatments_datatable && this.$refs.treatments_datatable.vmDataTable) {
        this.$refs.treatments_datatable.vmDataTable.ajax.reload();
      }
    },
    clearFilters() {
      this.filterTask = '';
      this.filterStatus = 'all';
      this.filterPlanYear = '';
      this.filterPlanMonth = 'all';
      this.filterCompleteDateFrom = '';
      this.filterCompleteDateTo = '';
      this.filterMachine = '';
      this.filterOperator = '';
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
</style>

<!-- Add a global style as a last resort -->
<style>
/* Global style that will definitely work */
.treatments-table-container .collapsible-component .filter_warning_icon.filter-active {
  color: #dc3545 !important;
}

.treatments-table-container .collapsible-component .filter_warning_icon.filter-clear {
  color: #28a745 !important;
}
</style>
