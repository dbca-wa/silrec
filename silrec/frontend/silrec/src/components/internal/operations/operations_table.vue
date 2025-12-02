<template>
  <div class="operations-table-container">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/operations/operations_table.vue</div>
    <div class="table-controls mb-3">
      <div class="row align-items-center">
        <div class="col-md-6">
          <h5>Operations</h5>
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

    <div class="table-wrapper">
      <datatable
        :id="datatableId"
        ref="operations_datatable"
        :dt-options="dtOptions"
        :dt-headers="dtHeaders"
      />
    </div>
  </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { api_endpoints } from '@/utils/hooks';
import { v4 as uuid } from 'uuid';

export default {
  name: 'OperationsTable',
  components: {
    datatable,
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
      datatableId: 'operations-table-' + uuid(),
    };
  },
  computed: {
    dtHeaders() {
      const headers = [
        'Operation ID',
        'FEA ID',
        'DAS ID',
        'Plan Release',
        'Silvic Plan Map',
        'Silvic Plan Doc',
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
          url: api_endpoints.operations,
          type: 'GET',
          data: function(d) {
            d.cohort_id = vm.cohortId;
          },
          dataSrc: function (json) {
            return json.data;
          }
        },
        
        columns: [
          {
            data: 'op_id',
            name: 'op_id',
            visible: true,
            orderable: true
          },
          {
            data: 'fea_id',
            name: 'fea_id',
            orderable: true,
            render: function(data) {
              return data || 'N/A';
            }
          },
          {
            data: 'das_id',
            name: 'das_id',
            orderable: true,
            render: function(data) {
              return data || 'N/A';
            }
          },
          {
            data: 'plan_release',
            name: 'plan_release',
            orderable: true,
            render: function(data) {
              return data || 'N/A';
            }
          },
          {
            data: 'silvic_plan_map',
            name: 'silvic_plan_map',
            orderable: false,
            render: function(data, type, row) {
              if (data) {
                return `<a href="${data}" target="_blank" class="btn btn-sm btn-outline-info" title="View Silvic Plan Map">
                  <i class="bi bi-file-earmark-image"></i> View Map
                </a>`;
              }
              return 'No map';
            }
          },
          {
            data: 'silvic_plan_doc',
            name: 'silvic_plan_doc',
            orderable: false,
            render: function(data, type, row) {
              if (data) {
                return `<a href="${data}" target="_blank" class="btn btn-sm btn-outline-info" title="View Silvic Plan Document">
                  <i class="bi bi-file-earmark-text"></i> View Doc
                </a>`;
              }
              return 'No document';
            }
          },
          {
            data: 'op_id',
            orderable: false,
            searchable: false,
            className: 'action-column',
            render: function(data, type, row) {
              let actions = '';
              if (!vm.readOnly) {
                actions += `<a href="/internal/operation/${data}/edit" class="btn btn-sm btn-outline-primary me-1" title="Edit Operation">
                  <i class="bi bi-pencil"></i>
                </a>`;
                actions += `<button class="btn btn-sm btn-outline-danger delete-operation-btn" data-operation-id="${data}" title="Delete Operation">
                  <i class="bi bi-trash"></i>
                </button>`;
              } else {
                actions += `<a href="#/internal/operation/${data}" class="btn btn-sm btn-outline-info" title="View Operation">
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
          emptyTable: 'No operations found',
          info: 'Showing _START_ to _END_ of _TOTAL_ operations',
          infoEmpty: 'Showing 0 to 0 of 0 operations',
          infoFiltered: '(filtered from _MAX_ total operations)',
          lengthMenu: 'Show _MENU_ operations',
          loadingRecords: 'Loading...',
          search: 'Search:',
          zeroRecords: 'No matching operations found'
        },
        
        drawCallback: function(settings) {
          vm.attachEventListeners();
        }
      };
    }
  },
  methods: {
    refreshData() {
      if (this.$refs.operations_datatable && this.$refs.operations_datatable.vmDataTable) {
        this.$refs.operations_datatable.vmDataTable.ajax.reload(null, false);
      }
    },
    
    attachEventListeners() {
      const vm = this;

      $(this.$el).off('click', '.delete-operation-btn');

      $(this.$el).on('click', '.delete-operation-btn', function() {
        const operationId = $(this).data('operation-id');
        vm.deleteOperation(operationId);
      });
    },
    
    async deleteOperation(operationId) {
        const result = await swal.fire({
            icon: 'warning',
            title: 'Are you sure?',
            text: 'Are you sure you want to delete this operation? This will also unlink it from any cohorts.',
            showCancelButton: true,
            confirmButtonText: 'Yes, delete it!',
            cancelButtonText: 'Cancel',
            confirmButtonColor: '#d33'
        });

        if (!result.isConfirmed) {
            return;
        }

        try {
            const response = await fetch(`${api_endpoints.operations}${operationId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.refreshData();
            this.$emit('operation-updated');

            await swal.fire({
                icon: 'success',
                title: 'Deleted!',
                text: 'Operation deleted successfully',
                timer: 3000,
                showConfirmButton: false
            });
        } catch (error) {
            console.error('Error deleting operation:', error);
            await swal.fire({
                icon: 'error',
                title: 'Delete Failed',
                text: 'Failed to delete operation',
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
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.refreshData();
    });
  }
};
</script>

<style scoped>
.operations-table-container {
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
</style>
