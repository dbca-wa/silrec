<template>
  <div class="treatments-table">
    <datatable
      :id="datatableId"
      ref="treatments_datatable"
      :dt-options="dtOptions"
      :dt-headers="dtHeaders"
    />
  </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { api_endpoints } from '@/utils/hooks';
import { v4 as uuid } from 'uuid';

export default {
  name: 'TreatmentsTable',
  components: {
    datatable
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
      datatableId: 'treatments-table-' + uuid()
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
          }
        },
        columns: [
          {
            data: 'treatment_id',
            name: 'treatment_id',
            visible: false
          },
          {
            data: 'task_name',
            name: 'task__name',
            orderable: true
          },
          {
            data: 'plan_yr',
            name: 'plan_yr',
            orderable: true
          },
          {
            data: 'plan_mth',
            name: 'plan_mth',
            orderable: true
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
        drawCallback: function(settings) {
          vm.attachEventListeners();
        }
      };
    }
  },
  methods: {
    refreshData() {
      if (this.$refs.treatments_datatable && this.$refs.treatments_datatable.vmDataTable) {
        this.$refs.treatments_datatable.vmDataTable.ajax.reload();
      }
    },
    attachEventListeners() {
      const vm = this;
      
      // Only need to handle delete buttons now
      $(this.$el).off('click', '.delete-treatment-btn');
      
      $(this.$el).on('click', '.delete-treatment-btn', function() {
        const treatmentId = $(this).data('treatment-id');
        vm.deleteTreatment(treatmentId);
      });
    },
    async deleteTreatment(treatmentId) {
      if (confirm('Are you sure you want to delete this treatment?')) {
        try {
          await this.$http.delete(`${api_endpoints.treatments}${treatmentId}/`);
          this.refreshData();
          this.$emit('treatment-updated');
        } catch (error) {
          console.error('Error deleting treatment:', error);
          alert('Failed to delete treatment');
        }
      }
    }
  }
};
</script>
