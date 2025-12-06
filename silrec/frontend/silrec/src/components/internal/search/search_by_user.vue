<template>
    <div>
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/search/search_by_user.vue</div>
        
        <CollapsibleFilters
            ref="collapsible_filters"
            component_title="Search by User"
            class="mb-2"
            @created="collapsible_component_mounted"
        >
            <div class="row mt-1 p-2">
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="">Select User</label>
                        <Select2Search
                            ref="userSelect"
                            :lookupApiEndpoint="api_endpoints.person_lookup"
                            @selected="onUserSelected"
                            placeholder="Start typing user name..."
                        />
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="form-group">
                        <label for="">Search Field</label>
                        <select
                            v-model="filterField"
                            class="form-select"
                        >
                            <option value="all">All User Fields</option>
                            <option value="created_by">Created By</option>
                            <option value="updated_by">Updated By</option>
                            <option value="uploaded_by">Uploaded By</option>
                            <option value="changed_by">Changed By</option>
                            <option value="submitter">Submitter</option>
                        </select>
                    </div>
                </div>
                
                <div class="col-md-2">
                    <div class="form-group">
                        <label for="">Date From</label>
                        <input
                            v-model="filterDateFrom"
                            type="date"
                            class="form-control"
                        />
                    </div>
                </div>
                
                <div class="col-md-2">
                    <div class="form-group">
                        <label for="">Date To</label>
                        <input
                            v-model="filterDateTo"
                            type="date"
                            class="form-control"
                        />
                    </div>
                </div>
                
                <div class="col-md-12 mt-2">
                    <div class="form-group">
                        <label for="">Models to Search</label>
                        <div class="form-check form-check-inline" v-for="model in availableModels" :key="model.value">
                            <input
                                class="form-check-input"
                                type="checkbox"
                                :id="'model_' + model.value"
                                :value="model.value"
                                v-model="selectedModels"
                            />
                            <label class="form-check-label" :for="'model_' + model.value">
                                {{ model.label }}
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-12 mt-3">
                    <div class="text-end">
                        <button
                            type="button"
                            class="btn btn-primary me-2"
                            @click="searchRecords"
                            :disabled="!selectedUser"
                        >
                            <i class="fa-solid fa-search"></i> Search
                        </button>
                        <button
                            type="button"
                            class="btn btn-secondary"
                            @click="resetSearch"
                        >
                            <i class="fa-solid fa-rotate-left"></i> Reset
                        </button>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div v-if="searchPerformed && !loading" class="row mt-3">
            <div class="col-md-12">
                <div class="alert alert-info">
                    Found {{ totalRecords }} records across {{ searchSummary.models.length }} model(s)
                    <span v-if="searchSummary.models.length > 0">
                        : {{ searchSummary.models.join(', ') }}
                    </span>
                </div>
            </div>
        </div>

        <div class="row" v-if="searchPerformed">
            <div class="col-lg-12">
                <datatable
                    :id="datatable_id"
                    ref="search_datatable"
                    :dt-options="dtOptions"
                    :dt-headers="dtHeaders"
                />
            </div>
        </div>
        
        <div v-if="loading" class="row mt-3">
            <div class="col-md-12 text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Searching records...</p>
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { v4 as uuid } from 'uuid';
import { api_endpoints, constants } from '@/utils/hooks';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
//import Select2Search from '@/components/common/Select2Search.vue';

export default {
    name: 'SearchByUser',
    components: {
        datatable,
        CollapsibleFilters,
        //Select2Search
    },
    data() {
        let vm = this;
        return {
            datatable_id: 'user-search-datatable-' + uuid(),
            
            // Search filters
            selectedUser: null,
            filterField: 'all',
            filterDateFrom: '',
            filterDateTo: '',
            
            // Available models with user references
            availableModels: [
                { value: 'proposal', label: 'Proposals' },
                { value: 'polygon', label: 'Polygons' },
                { value: 'cohort', label: 'Cohorts' },
                { value: 'treatment', label: 'Treatments' },
                { value: 'survey_assessment_document', label: 'Survey Documents' },
                { value: 'silviculturist_comment', label: 'Silviculturist Comments' },
                { value: 'operation', label: 'Operations' }
            ],
            selectedModels: ['proposal', 'polygon', 'cohort', 'treatment', 'survey_assessment_document'],
            
            // Search results
            searchPerformed: false,
            loading: false,
            totalRecords: 0,
            searchSummary: {
                models: []
            }
        };
    },
    computed: {
        dtHeaders: function () {
            return [
                'Model',
                'ID',
                'User Field',
                'User Name',
                'Created On',
                'Updated On',
                'Details',
                'Action'
            ];
        },
        
        column_model: function () {
            return {
                data: 'model_type',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.model_display || full.model_type;
                },
                name: 'model_type',
            };
        },
        
        column_id: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.record_id || full.id;
                },
                name: 'record_id',
            };
        },
        
        column_field: function () {
            return {
                data: 'field',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.field_display || full.field;
                },
                name: 'field',
            };
        },
        
        column_username: function () {
            return {
                data: 'user_name',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.user_name || 'N/A';
                },
                name: 'user_name',
            };
        },
        
        column_created: function () {
            return {
                data: 'created_on',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (full.created_on) {
                        return moment(full.created_on).format('DD/MM/YYYY HH:mm');
                    }
                    return '';
                },
                name: 'created_on',
            };
        },
        
        column_updated: function () {
            return {
                data: 'updated_on',
                orderable: true,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (full.updated_on) {
                        return moment(full.updated_on).format('DD/MM/YYYY HH:mm');
                    }
                    return '';
                },
                name: 'updated_on',
            };
        },
        
        column_details: function () {
            return {
                data: 'details',
                orderable: false,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    let details = [];
                    if (full.name) details.push(`Name: ${full.name}`);
                    if (full.title) details.push(`Title: ${full.title}`);
                    if (full.description) details.push(`Desc: ${full.description.substring(0, 50)}...`);
                    if (full.obj_code) details.push(`Obj: ${full.obj_code}`);
                    if (full.task_name) details.push(`Task: ${full.task_name}`);
                    
                    return details.join('<br/>') || 'No additional details';
                }
            };
        },
        
        column_action: function () {
            let vm = this;
            return {
                data: 'action_url',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (full.action_url) {
                        return `<a href="${full.action_url}" target="_blank">View</a>`;
                    }
                    return '';
                }
            };
        },
        
        dtOptions: function () {
            let vm = this;
            
            return {
                autoWidth: false,
                responsive: true,
                serverSide: true,
                searching: true,
                lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
                pageLength: 25,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                ajax: {
                    url: '/api/search/user_records/', // This endpoint needs to be created
                    dataSrc: 'data',
                    data: function (d) {
                        d.user_id = vm.selectedUser?.id;
                        d.field = vm.filterField;
                        d.date_from = vm.filterDateFrom;
                        d.date_to = vm.filterDateTo;
                        d.models = vm.selectedModels.join(',');
                        d.search_terms = 'model_type,user_name,details';
                    },
                },
                dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
                     "<'row'<'col-sm-12'tr>>" +
                     "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
                order: [[4, 'desc']], // Sort by created date desc by default
                columns: [
                    vm.column_model,
                    vm.column_id,
                    vm.column_field,
                    vm.column_username,
                    vm.column_created,
                    vm.column_updated,
                    vm.column_details,
                    vm.column_action
                ],
                processing: true,
                initComplete: function () {
                    console.log('User search datatable initialized');
                },
            };
        }
    },
    methods: {
        onUserSelected(user) {
            this.selectedUser = user;
        },
        
        searchRecords() {
            if (!this.selectedUser) {
                this.$swal.fire({
                    title: 'Error',
                    text: 'Please select a user to search for',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
                return;
            }
            
            this.loading = true;
            this.searchPerformed = false;
            
            // Simulate API call - in reality, this would call your search endpoint
            setTimeout(() => {
                this.loading = false;
                this.searchPerformed = true;
                this.totalRecords = 125; // Example count
                this.searchSummary.models = ['Proposals', 'Polygons', 'Treatments'];
                
                // Trigger datatable refresh
                if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
                    this.$refs.search_datatable.vmDataTable.ajax.reload();
                }
            }, 1000);
        },
        
        resetSearch() {
            this.selectedUser = null;
            this.filterField = 'all';
            this.filterDateFrom = '';
            this.filterDateTo = '';
            this.selectedModels = ['proposal', 'polygon', 'cohort', 'treatment', 'survey_assessment_document'];
            this.searchPerformed = false;
            this.totalRecords = 0;
            this.searchSummary = { models: [] };
            
            // Clear select2
            if (this.$refs.userSelect && this.$refs.userSelect.$el) {
                $(this.$refs.userSelect.$el).val(null).trigger('change');
            }
        },
        
        collapsible_component_mounted() {
            if (this.$refs.collapsible_filters) {
                this.$refs.collapsible_filters.show_warning_icon(false);
            }
        }
    },
    mounted() {
        console.log('SearchByUser component mounted');
    }
};
</script>

<style scoped>
.form-check-inline {
    margin-right: 15px;
}
</style>
