<template>
    <div>
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/search/search_by_text.vue</div>
        
        <CollapsibleFilters
            ref="collapsible_filters"
            component_title="Search by Text String"
            class="mb-2"
            @created="collapsible_component_mounted"
            :collapsed="false"
        >
            <div class="row mt-1 p-2">
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="">Search Text</label>
                        <input
                            v-model="searchText"
                            type="text"
                            class="form-control"
                            placeholder="Enter text to search for..."
                        />
                        <small class="form-text text-muted">
                            Search in: comments, descriptions, titles, names, results, etc.
                        </small>
                    </div>
                </div>
                
                <!--
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Search Field</label>
                        <select
                            ref="searchFieldSelect"
                            class="form-select select2-single"
                            style="width: 100%;"
                        >
                            <option value="all">All Text Fields</option>
                            <option value="comments">Comments</option>
                            <option value="description">Description</option>
                            <option value="title">Title</option>
                            <option value="name">Name</option>
                            <option value="results">Results</option>
                            <option value="reference">Reference</option>
                            <option value="extra_info">Extra Info</option>
                        </select>
                    </div>
                </div>
                -->
                                
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Records to Search</label>
                        <select
                            ref="recordsToSearchSelect"
                            class="form-select select2-single"
                            style="width: 100%;"
                        >
                            <option value="all">All Records</option>
                            <option value="proposal">Proposals</option>
                            <option value="polygon">Polygons</option>
                            <option value="cohort">Cohorts</option>
                            <option value="treatment">Treatments</option>
                            <option value="treatment_xtra">Treatment Extras</option>
                            <option value="survey_assessment_document">Survey Documents</option>
                            <option value="silviculturist_comment">Silviculturist Comments</option>
                            <option value="prescription">Prescriptions</option>
                        </select>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Match Type</label>
                        <select
                            v-model="matchType"
                            class="form-select"
                        >
                            <option value="contains">Contains</option>
                            <option value="exact">Exact Match</option>
                            <option value="starts_with">Starts With</option>
                            <option value="ends_with">Ends With</option>
                        </select>
                    </div>
                </div>
            </div>
                
            <div class="row p-2">
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Date From</label>
                        <input
                            v-model="filterDateFrom"
                            type="date"
                            class="form-control"
                        />
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Date To</label>
                        <input
                            v-model="filterDateTo"
                            type="date"
                            class="form-control"
                        />
                    </div>
                </div>
                
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Case Sensitive</label>
                        <div class="form-check form-switch mt-2">
                            <input
                                class="form-check-input"
                                type="checkbox"
                                id="caseSensitiveSwitch"
                                v-model="caseSensitive"
                            />
                            <label class="form-check-label" for="caseSensitiveSwitch">
                                {{ caseSensitive ? 'Yes' : 'No' }}
                            </label>
                        </div>
                    </div>
                </div>

                <div class="col-md-12 mt-2 p-2">
                    <div class="form-group">
                        <div class="row p-2">
                            <label for="">Text Fields to Search</label>
                        </div>
                        <div>
                          <div class="form-check form-check-inline" v-for="field in availableFields" :key="field.value">
                            <input
                                class="form-check-input"
                                type="checkbox"
                                :id="'field_' + field.value"
                                :value="field.value"
                                v-model="selectedFields"
                            />
                            <label class="form-check-label" :for="'field_' + field.value">
                                {{ field.label }}
                            </label>
                          </div>
                        </div>
                    </div>
                </div>
                <!--
                -->
                
                <div class="col-md-12 mt-3">
                    <div class="text-end">
                        <button
                            type="button"
                            class="btn btn-primary me-2"
                            @click="searchRecords"
                            :disabled="!searchText || searchText.length < 2"
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
                    Found {{ totalRecords }} records
                    <span v-if="selectedModel !== 'all'">
                        in {{ selectedModel | formatModelName }} model
                    </span>
                    for text: "<strong>{{ searchText }}</strong>"
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
                <p class="mt-2">Searching text in records...</p>
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue';
import { v4 as uuid } from 'uuid';
import { api_endpoints, constants } from '@/utils/hooks';
import CollapsibleFilters from '@/components/forms/collapsible_component.vue';
import $ from 'jquery';
import 'select2/dist/css/select2.min.css';
import 'select2/dist/js/select2.min.js';

export default {
    name: 'SearchByText',
    components: {
        datatable,
        CollapsibleFilters
    },
    filters: {
        formatModelName(value) {
            const modelNames = {
                'proposal': 'Proposals',
                'polygon': 'Polygons', 
                'cohort': 'Cohorts',
                'treatment': 'Treatments',
                'treatment_xtra': 'Treatment Extras',
                'survey_assessment_document': 'Survey Documents',
                'silviculturist_comment': 'Silviculturist Comments',
                'prescription': 'Prescriptions'
            };
            return modelNames[value] || value;
        }
    },
    data() {
        let vm = this;
        return {
            datatable_id: 'text-search-datatable-' + uuid(),
            
            // Search filters
            searchText: '',
            filterField: 'all',
            matchType: 'contains',
            filterDateFrom: '',
            filterDateTo: '',
            caseSensitive: false,
            selectedModel: 'all',
            
            // Available text fields to search
            availableFields: [
                { value: 'comments', label: 'Comments' },
                { value: 'description', label: 'Description' },
                { value: 'title', label: 'Title' },
                { value: 'name', label: 'Name' },
                { value: 'results', label: 'Results' },
                { value: 'reference', label: 'Reference' },
                { value: 'extra_info', label: 'Extra Info' },
                { value: 'herbicide_app_spec', label: 'Herbicide Spec' },
                { value: 'task_description', label: 'Task Description' }
            ],
            selectedFields: ['comments', 'description', 'title', 'name', 'results'],
            
            // Search results
            searchPerformed: false,
            loading: false,
            totalRecords: 0,
            
            // Select2 instances
            select2SearchField: null,
            select2RecordsToSearch: null
        };
    },
    computed: {
        dtHeaders: function () {
            return [
                'Model',
                'ID',
                'Field Found',
                'Text Preview',
                'Created On',
                'Created By',
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
                data: 'field_found',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.field_display || full.field_found;
                },
                name: 'field_found',
            };
        },
        
        column_preview: function () {
            return {
                data: 'text_preview',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let text = full.text_preview || full.matching_text || '';
                    let searchText = this.searchText;
                    
                    // Highlight the search term in the preview
                    if (text && searchText) {
                        const regex = new RegExp(`(${searchText})`, 'gi');
                        text = text.replace(regex, '<mark>$1</mark>');
                    }
                    
                    return text.length > 100 ? text.substring(0, 100) + '...' : text;
                }.bind(this)
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
                        return moment(full.created_on).format('DD/MM/YYYY');
                    }
                    return '';
                },
                name: 'created_on',
            };
        },
        
        column_created_by: function () {
            return {
                data: 'created_by',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.created_by || 'N/A';
                },
                name: 'created_by',
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
                    if (full.obj_code) details.push(`Objective: ${full.obj_code}`);
                    if (full.task_name) details.push(`Task: ${full.task_name}`);
                    if (full.polygon_name) details.push(`Polygon: ${full.polygon_name}`);
                    if (full.compartment) details.push(`Compartment: ${full.compartment}`);
                    
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
                    url: api_endpoints.search_by_text,
                    dataSrc: 'data',
                    data: function (d) {
                        d.search_text = vm.searchText;
                        d.field = vm.filterField;
                        d.match_type = vm.matchType;
                        d.date_from = vm.filterDateFrom;
                        d.date_to = vm.filterDateTo;
                        d.case_sensitive = vm.caseSensitive;
                        d.model = vm.selectedModel;
                        d.fields = vm.selectedFields.join(',');
                        d.search_terms = 'model_type,text_preview,created_by,details';
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
                    vm.column_preview,
                    vm.column_created,
                    vm.column_created_by,
                    vm.column_details,
                    vm.column_action
                ],
                processing: true,
                initComplete: function () {
                    console.log('Text search datatable initialized');
                },
            };
        }
    },
    methods: {
        initializeSelect2() {
            // Initialize Search Field Select2
            if (this.$refs.searchFieldSelect) {
                // Destroy existing instance if any
                if (this.select2SearchField && this.select2SearchField.select2) {
                    this.select2SearchField.select2('destroy');
                }
                
                // Initialize Select2
                this.select2SearchField = $(this.$refs.searchFieldSelect).select2({
                    theme: 'bootstrap-5',
                    placeholder: 'Select search field',
                    allowClear: false,
                    width: '100%',
                    dropdownParent: $(this.$refs.searchFieldSelect).parent()
                });
                
                // Set initial value
                this.select2SearchField.val(this.filterField).trigger('change');
                
                // Bind change event
                this.select2SearchField.on('change', (event) => {
                    this.filterField = $(event.target).val();
                });
            }
            
            // Initialize Records to Search Select2
            if (this.$refs.recordsToSearchSelect) {
                // Destroy existing instance if any
                if (this.select2RecordsToSearch && this.select2RecordsToSearch.select2) {
                    this.select2RecordsToSearch.select2('destroy');
                }
                
                // Initialize Select2
                this.select2RecordsToSearch = $(this.$refs.recordsToSearchSelect).select2({
                    theme: 'bootstrap-5',
                    placeholder: 'Select records to search',
                    allowClear: false,
                    width: '100%',
                    dropdownParent: $(this.$refs.recordsToSearchSelect).parent()
                });
                
                // Set initial value
                this.select2RecordsToSearch.val(this.selectedModel).trigger('change');
                
                // Bind change event
                this.select2RecordsToSearch.on('change', (event) => {
                    this.selectedModel = $(event.target).val();
                });
            }
        },
        
        destroySelect2() {
            // Destroy Search Field Select2
            if (this.select2SearchField && this.select2SearchField.select2) {
                this.select2SearchField.off('change');
                this.select2SearchField.select2('destroy');
                this.select2SearchField = null;
            }
            
            // Destroy Records to Search Select2
            if (this.select2RecordsToSearch && this.select2RecordsToSearch.select2) {
                this.select2RecordsToSearch.off('change');
                this.select2RecordsToSearch.select2('destroy');
                this.select2RecordsToSearch = null;
            }
        },
        
        searchRecords() {
            if (!this.searchText || this.searchText.length < 2) {
                this.$swal.fire({
                    title: 'Error',
                    text: 'Please enter at least 2 characters to search',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
                return;
            }
            
            this.loading = true;
            this.searchPerformed = false;
            
            // Simulate API call
            setTimeout(() => {
                this.loading = false;
                this.searchPerformed = true;
                this.totalRecords = 88; // Example count
                
                // Trigger datatable refresh
                if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
                    this.$refs.search_datatable.vmDataTable.ajax.reload();
                }
            }, 1000);
        },
        
        resetSearch() {
            this.searchText = '';
            this.filterField = 'all';
            this.matchType = 'contains';
            this.filterDateFrom = '';
            this.filterDateTo = '';
            this.caseSensitive = false;
            this.selectedModel = 'all';
            this.selectedFields = ['comments', 'description', 'title', 'name', 'results'];
            this.searchPerformed = false;
            this.totalRecords = 0;
            
            // Reset Select2 values
            if (this.select2SearchField) {
                this.select2SearchField.val('all').trigger('change');
            }
            
            if (this.select2RecordsToSearch) {
                this.select2RecordsToSearch.val('all').trigger('change');
            }
        },
        
        collapsible_component_mounted() {
            if (this.$refs.collapsible_filters) {
                this.$refs.collapsible_filters.show_warning_icon(false);
            }
        }
    },
    mounted() {
        console.log('SearchByText component mounted');
        
        // Initialize Select2 after component is mounted
        this.$nextTick(() => {
            setTimeout(() => {
                this.initializeSelect2();
            }, 200);
        });
    },
    
    beforeUnmount() {
        // Clean up Select2 instances
        this.destroySelect2();
    }
};
</script>

<style scoped>
.form-check-inline {
    margin-right: 15px;
    margin-bottom: 5px;
}

mark {
    background-color: yellow;
    padding: 0 2px;
}

/* Select2 customizations */
.select2-single {
    min-height: 38px;
}

.select2-container--bootstrap-5 .select2-selection {
    min-height: 38px;
    padding: 0.375rem 0.75rem;
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    color: #212529;
    background-color: #fff;
    background-clip: padding-box;
    border: 1px solid #ced4da;
    border-radius: 0.375rem;
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.select2-container--bootstrap-5 .select2-selection:focus {
    border-color: #86b7fe;
    outline: 0;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.select2-container--bootstrap-5 .select2-dropdown {
    border: 1px solid #ced4da;
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    z-index: 1060 !important;
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

/* Ensure proper z-index for dropdown */
.select2-container {
    z-index: 1055 !important;
}

.select2-dropdown {
    z-index: 1060 !important;
}

/* Fix for original select arrow visibility */
.select2-single {
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%23343a40' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3e%3c/svg%3e");
    background-repeat: no-repeat;
    background-position: right 0.75rem center;
    background-size: 16px 12px;
}
</style>
