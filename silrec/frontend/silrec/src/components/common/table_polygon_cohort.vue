<template>
    <div class="polygon-cohort-table-container" data-table="polygon-cohort">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/common/table_polygon_cohort.vue</div>
        <div class="table-controls mb-3">
            <div class="row align-items-center">
                <div class="col-md-6">
                    <h5 v-if="showTitle">Polygon & Cohort Data</h5>
                </div>
                <div class="col-md-6 text-end">
                    <button 
                        class="btn btn-sm btn-outline-secondary me-2"
                        @click="toggleTable"
                        :title="tableVisible ? 'Hide table' : 'Show table'"
                    >
                        <i class="bi" :class="tableVisible ? 'bi-eye-slash' : 'bi-eye'"></i>
                        {{ tableVisible ? 'Hide Table' : 'Show Table' }}
                    </button>
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

        <div v-if="tableVisible" class="table-wrapper">
            <CollapsibleFilters
                ref="collapsible_filters"
                component_title="Table Filters"
                class="mb-2"
                @created="collapsible_component_mounted"
            >
                <div class="row mt-1 p-2">
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="filterPolygonName">Polygon Name</label>
                            <input
                                v-model="filterPolygonName"
                                type="text"
                                class="form-control"
                                id="filterPolygonName"
                                placeholder="Filter by name..."
                            />
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="filterCohortStatus">Cohort Status</label>
                            <select
                                v-model="filterCohortStatus"
                                class="form-select"
                                id="filterCohortStatus"
                            >
                                <option value="all">All Status</option>
                                <option value="active">Active</option>
                                <option value="closed">Closed</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="filterSpecies">Species</label>
                            <input
                                v-model="filterSpecies"
                                type="text"
                                class="form-control"
                                id="filterSpecies"
                                placeholder="Filter by species..."
                            />
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="form-group">
                            <label for="filterArea">Min Area (ha)</label>
                            <input
                                v-model="filterMinArea"
                                type="number"
                                class="form-control"
                                id="filterArea"
                                placeholder="Min area..."
                                min="0"
                                step="0.1"
                            />
                        </div>
                    </div>
                </div>
            </CollapsibleFilters>

            <div class="row">
                <div class="col-lg-12">
                    <datatable
                        :id="datatable_id"
                        ref="polygon_cohort_datatable"
                        :dt-options="dtOptions"
                        :dt-headers="dtHeaders"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import { v4 as uuid } from 'uuid';
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'PolygonCohortTable',
    components: {
        datatable,
        CollapsibleFilters,
    },
    props: {
        proposalId: {
            type: Number,
            required: true
        },
        showTitle: {
            type: Boolean,
            default: true
        },
        initialVisible: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            datatable_id: 'polygon-cohort-table-' + uuid(),
            tableVisible: this.initialVisible,
            
            // Filters
            filterPolygonName: '',
            filterCohortStatus: 'all',
            filterSpecies: '',
            filterMinArea: '',
        };
    },
    computed: {
        dtHeaders() {
            return [
                'ID',
                'Polygon Name',
                'FEA ID',
                'Area (ha)',
                'Cohort ID',
                'Objective',
                'Target BA (m²/ha)',
                'Residual BA (m²/ha)',
                'Species',
                'Status',
                'Actions'
            ];
        },
        dtOptions() {
            let vm = this;
            
            return {
                autoWidth: false,
                responsive: true,
                serverSide: true,
                searching: true,
                processing: true,
                ajax: {
                    url: api_endpoints.polygon_cohort_table,
                    dataSrc: 'data',
                    data: function(d) {
                        d.proposal_id = vm.proposalId;
                        d.filter_polygon_name = vm.filterPolygonName;
                        d.filter_cohort_status = vm.filterCohortStatus;
                        d.filter_species = vm.filterSpecies;
                        d.filter_min_area = vm.filterMinArea;
                    }
                },
                columns: [
                    // Polygon ID
                    {
                        data: 'polygon_id',
                        name: 'polygon_id',
                        visible: false,
                        orderable: true
                    },
                    // Polygon Name
                    {
                        data: 'name',
                        name: 'name',
                        orderable: true,
                        render: function(data, type, row) {
                            return data || 'N/A';
                        }
                    },
                    // FEA ID
                    {
                        data: 'zfea_id',
                        name: 'zfea_id',
                        orderable: true,
                        render: function(data, type, row) {
                            return data || 'N/A';
                        }
                    },
                    // Area
                    {
                        data: 'area_ha',
                        name: 'area_ha',
                        orderable: true,
                        render: function(data, type, row) {
                            return data ? data.toFixed(2) : 'N/A';
                        }
                    },
                    // Cohort ID
                    {
                        data: 'assigned_cohorts',
                        name: 'assigned_cohorts',
                        orderable: false,
                        render: function(data, type, row) {
                            if (data && data.length > 0) {
                                return data.map(cht => cht.cohort).join(', ');
                            }
                            return 'No cohorts';
                        }
                    },
                    // Objective Code
                    {
                        data: 'assigned_cohorts',
                        name: 'assigned_cohorts',
                        orderable: false,
                        render: function(data, type, row) {
                            if (data && data.length > 0) {
                                return data.map(cht => 
                                    cht.cohort_details?.obj_code || 'N/A'
                                ).join(', ');
                            }
                            return 'N/A';
                        }
                    },
                    // Target BA
                    {
                        data: 'assigned_cohorts',
                        name: 'assigned_cohorts',
                        orderable: false,
                        render: function(data, type, row) {
                            if (data && data.length > 0) {
                                return data.map(cht => 
                                    cht.cohort_details?.target_ba_m2ha ? 
                                    cht.cohort_details.target_ba_m2ha.toFixed(2) : 'N/A'
                                ).join(', ');
                            }
                            return 'N/A';
                        }
                    },
                    // Residual BA
                    {
                        data: 'assigned_cohorts',
                        name: 'assigned_cohorts',
                        orderable: false,
                        render: function(data, type, row) {
                            if (data && data.length > 0) {
                                return data.map(cht => 
                                    cht.cohort_details?.resid_ba_m2ha ? 
                                    cht.cohort_details.resid_ba_m2ha.toFixed(2) : 'N/A'
                                ).join(', ');
                            }
                            return 'N/A';
                        }
                    },
                    // Species
                    {
                        data: 'assigned_cohorts',
                        name: 'assigned_cohorts',
                        orderable: false,
                        render: function(data, type, row) {
                            if (data && data.length > 0) {
                                return data.map(cht => 
                                    cht.cohort_details?.species || 'N/A'
                                ).join(', ');
                            }
                            return 'N/A';
                        }
                    },
                    // Status
                    {
                        data: 'assigned_cohorts',
                        name: 'assigned_cohorts',
                        orderable: false,
                        render: function(data, type, row) {
                            if (data && data.length > 0) {
                                const statuses = data.map(cht => 
                                    cht.status_current ? 'Active' : 'Closed'
                                );
                                return [...new Set(statuses)].join(', '); // Remove duplicates
                            }
                            return 'N/A';
                        }
                    },
                    // Actions
                    {
                        data: 'polygon_id',
                        orderable: false,
                        searchable: false,
                        className: 'action-column',
                        render: function(data, type, row) {
                            let actions = '';
                            // Get the first cohort ID for navigation
                            const cohortId = row.assigned_cohorts && row.assigned_cohorts.length > 0 ? row.assigned_cohorts[0].cohort : null;
                            console.log('JM 8: ' + JSON.stringify(row.proposal_id))

                            if (cohortId) {
                                actions += `<a href="${row.proposal_id}/cohorts/${cohortId}/polygon/${data}" class="btn btn-sm btn-outline-primary me-1" title="Edit Cohort">
                                <i class="bi bi-pencil"></i> Edit 1</a>`;
                            } else {
                                actions += `<button class="btn btn-sm btn-outline-secondary me-1" disabled title="No Cohort Assigned">
                                <i class="bi bi-pencil"></i> Edit</button>`;
                            }

                            actions += `<button class="btn btn-sm btn-outline-primary me-1 view-polygon-btn" data-polygon-id="${data}" title="View Details">
                                <i class="bi bi-eye"></i>
                            </button>`;
                            actions += `<button class="btn btn-sm btn-outline-info zoom-polygon-btn" data-polygon-id="${data}" title="Zoom to Polygon">
                                <i class="bi bi-zoom-in"></i>
                            </button>`;
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
                    // Re-attach event listeners after table redraw
                    vm.attachEventListeners();
                }
            };
        }
    },
    methods: {
        toggleTable() {
            this.tableVisible = !this.tableVisible;
            if (this.tableVisible) {
                this.$nextTick(() => {
                    this.refreshData();
                });
            }
        },
        async __refreshData() {
            try {
                if (this.$refs.polygon_cohort_datatable && this.$refs.polygon_cohort_datatable.vmDataTable) {
                    await this.$refs.polygon_cohort_datatable.vmDataTable.ajax.reload();
                }
            } catch (error) {
                console.error('Error refreshing data:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Refresh Failed',
                    text: 'Failed to refresh table data. Please try again.',
                    confirmButtonText: 'OK'
                });
            }
        },

        refreshData: async function() {
            try {
                if (this.$refs.polygon_cohort_datatable && this.$refs.polygon_cohort_datatable.vmDataTable) {
                    await this.$refs.polygon_cohort_datatable.vmDataTable.ajax.reload();
                    console.log('Datatable refreshed successfully');
                } else {
                    console.warn('Datatable ref not found for refresh');
                }
            } catch (error) {
                console.error('Error refreshing data:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Refresh Failed',
                    text: 'Failed to refresh table data. Please try again.',
                    confirmButtonText: 'OK'
                });
            }
        },

        collapsible_component_mounted() {
            // Filter warning icon logic if needed
        },
        // Method to handle polygon selection from table
        handlePolygonSelection(polygonId) {
            this.$emit('polygon-selected', polygonId);
        },
        // Method to handle zoom to polygon
        handleZoomToPolygon(polygonId) {
            this.$emit('zoom-to-polygon', polygonId);
        },
        // Attach event listeners to action buttons
        attachEventListeners() {
            const vm = this;
            
            // Remove existing listeners to prevent duplicates
            $(this.$el).off('click', '.view-polygon-btn');
            $(this.$el).off('click', '.zoom-polygon-btn');
            
            // Attach new listeners
            $(this.$el).on('click', '.view-polygon-btn', function() {
                const polygonId = $(this).data('polygon-id');
                vm.handlePolygonSelection(polygonId);
            });
            
            $(this.$el).on('click', '.zoom-polygon-btn', function() {
                const polygonId = $(this).data('polygon-id');
                vm.handleZoomToPolygon(polygonId);
            });
        }
    },
    mounted() {
        // Load data if table is initially visible
        if (this.tableVisible) {
            this.$nextTick(() => {
                this.refreshData();
            });
        }
    },
    watch: {
        proposalId: {
            handler(newVal) {
                if (newVal && this.tableVisible) {
                    this.refreshData();
                }
            },
            immediate: true
        },
        // Watch filters and refresh data when they change
        filterPolygonName() {
            this.refreshData();
        },
        filterCohortStatus() {
            this.refreshData();
        },
        filterSpecies() {
            this.refreshData();
        },
        filterMinArea() {
            this.refreshData();
        }
    }
};
</script>

<style scoped>
.polygon-cohort-table-container {
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
</style>
