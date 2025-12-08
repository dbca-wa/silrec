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
                            placeholder="Enter text to search for (min. 2 chars) ..."
                        />
                            <!--@keyup.enter="searchRecords"-->
                        <small class="form-text text-muted">
                            Enter text to search across all configured text fields
                        </small>
                    </div>
                </div>
                                
                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Records to Search</label>
                        <select
                            ref="recordsToSearchSelect"
                            class="form-select select2-single"
                            style="width: 100%;"
                        >
                            <option v-for="model in availableModels" 
                                    :key="model.key"
                                    :value="model.key">
                                {{ model.display_name }} 
                                <span v-if="model.search_fields_count > 0">
                                    ({{ model.search_fields_count }} field{{ model.search_fields_count !== 1 ? 's' : '' }})
                                </span>
                            </option>
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
                        <small class="form-text text-muted">Optional</small>
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
                        <small class="form-text text-muted">Optional</small>
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

                <div class="col-md-12 mt-2 p-2" v-if="availableFields.length > 0">
                    <div class="form-group">
                        <div class="row mb-2">
                            <div class="col-12">
                                <label for="" class="form-label">
                                    Text Fields to Search 
                                    <span class="badge bg-primary ms-1">{{ availableFields.length }}</span>
                                </label>
                            </div>
                            <div class="col-12">
                                <div class="form-check form-check-inline">
                                    <input
                                        class="form-check-input"
                                        type="checkbox"
                                        id="selectAllFields"
                                        :checked="allFieldsSelected"
                                        @change="toggleAllFields"
                                    />
                                    <label class="form-check-label fw-bold" for="selectAllFields">
                                        Select/Deselect All
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-12">
                                <div class="form-check form-check-inline mb-2" 
                                     v-for="field in availableFields" 
                                     :key="field.id"
                                     style="min-width: 200px;">
                                    <input
                                        class="form-check-input"
                                        type="checkbox"
                                        :id="'field_' + field.id"
                                        :value="field.field_name"
                                        v-model="selectedFields"
                                    />
                                    <label class="form-check-label" :for="'field_' + field.id"
                                          :title="field.description || field.display_name">
                                        {{ field.display_name }}
                                        <span v-if="field.description" 
                                              class="text-muted small d-block" 
                                              style="font-size: 0.8em; line-height: 1.2;">
                                            {{ field.description }}
                                        </span>
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-12">
                                <small class="text-muted">
                                    Selected {{ selectedFields.length }} of {{ availableFields.length }} field(s)
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-12" v-else-if="fieldsLoaded">
                    <div class="alert alert-warning">
                        <i class="fa-solid fa-triangle-exclamation me-2"></i>
                        No search fields configured for <strong>{{ selectedModelDisplay }}</strong>.
                        <router-link to="/admin/proposals/textsearchfielddisplay/" 
                                     target="_blank"
                                     class="alert-link ms-2">
                            Configure fields in Admin
                        </router-link>
                    </div>
                </div>
                
                <div class="col-md-12 mt-4">
                    <div class="text-end">
                        <button
                            type="button"
                            class="btn btn-primary me-2"
                            @click="searchRecords"
                            :disabled="!searchText || searchText.length < 2 || selectedFields.length === 0"
                            :title="getSearchButtonTitle"
                        >
                            <i class="fa-solid fa-search"></i> 
                            <span v-if="!loading">Search</span>
                            <span v-else>Searching...</span>
                        </button>
                        <button
                            type="button"
                            class="btn btn-secondary me-2"
                            @click="resetSearch"
                            :disabled="loading"
                        >
                            <i class="fa-solid fa-rotate-left"></i> Reset
                        </button>
                        <button
                            type="button"
                            class="btn btn-outline-info"
                            @click="loadDefaultFields"
                            title="Reload default field configuration"
                        >
                            <i class="fa-solid fa-arrows-rotate"></i> Reload Fields
                        </button>
                    </div>
                </div>
            </div>
        </CollapsibleFilters>

        <div v-if="searchPerformed && !loading" class="row mt-3">
            <div class="col-md-12">
                <div class="alert" :class="totalRecords > 0 ? 'alert-success' : 'alert-warning'">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fa-solid" :class="totalRecords > 0 ? 'fa-circle-check' : 'fa-circle-exclamation'"></i>
                            <strong class="ms-2">
                                {{ totalRecords }} record{{ totalRecords !== 1 ? 's' : '' }} found
                            </strong>
                            <span v-if="selectedModel !== 'all'" class="ms-2">
                                in <strong>{{ selectedModelDisplay }}</strong> model
                            </span>
                            for text: "<strong>{{ searchText }}</strong>"
                        </div>
                        <div>
                            <button
                                v-if="totalRecords > 0"
                                type="button"
                                class="btn btn-sm btn-outline-primary"
                                @click="exportResults"
                            >
                                <i class="fa-solid fa-download"></i> Export
                            </button>
                        </div>
                    </div>
                    <div v-if="selectedFields.length > 0" class="mt-2 small">
                        <span class="text-muted">Searching in {{ selectedFields.length }} field(s): </span>
                        <span class="fst-italic">{{ selectedFields.join(', ') }}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="row" v-show="searchPerformed">
            <div class="col-lg-12">
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Search Text Results</h5>
                    </div>
                    <div class="card-body p-0">
                        <datatable
                            :id="datatable_id"
                            ref="search_datatable"
                            :dt-options="dtOptions"
                            :dt-headers="dtHeaders"
                        />
                    </div>
                </div>
            </div>
        </div>

<!--
        <div class="row" v-if="searchPerformed">
            <div class="col-lg-12">
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Search Results</h5>
                    </div>
                    <div class="card-body p-0">
                        <datatable
                            v-show="!loading && totalRecords > 0"
                            :id="datatable_id"
                            ref="search_datatable"
                            :dt-options="dtOptions"
                            :dt-headers="dtHeaders"
                        />
                        <div v-if="loading" class="text-center p-5">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2">Loading search results...</p>
                        </div>
                        <div v-else-if="totalRecords === 0" class="text-center p-5">
                            <i class="fa-solid fa-magnifying-glass fa-3x text-muted mb-3"></i>
                            <h4 class="text-muted">No results found</h4>
                            <p class="text-muted">
                                No records matching "<strong>{{ searchText }}</strong>" were found.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
-->
       
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
import moment from 'moment';

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
            //filterField: 'all',
            matchType: 'contains',
            filterDateFrom: '',
            filterDateTo: '',
            caseSensitive: false,
            selectedModel: 'all',
            selectedModelDisplay: 'All Records',
            
            // Dynamic fields from database
            availableModels: [],
            availableFields: [],
            selectedFields: [],
            
            // Loading states
            fieldsLoaded: false,
            loadingFields: false,
            loading: false,
            
            // Search results
            searchPerformed: false,
            totalRecords: 0,
            
            // Select2 instances
            select2RecordsToSearch: null,
            
            // Error handling
            errorMessage: ''
        };
    },
    computed: {
        allFieldsSelected() {
            return this.availableFields.length > 0 && 
                   this.selectedFields.length === this.availableFields.length;
        },
        
        getSearchButtonTitle() {
            if (!this.searchText || this.searchText.length < 2) {
                return 'Please enter at least 2 characters to search';
            }
            if (this.selectedFields.length === 0) {
                return 'Please select at least one field to search';
            }
            return 'Search records';
        },
        
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
                className: 'text-nowrap'
            };
        },
        
        column_id: function () {
            return {
                data: 'record_id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.record_id || full.id;
                },
                name: 'record_id',
                className: 'text-nowrap'
            };
        },
        
        column_field: function () {
            return {
                data: 'field_found',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    // Try to get display name from field_display first
                    if (full.field_display) {
                        return full.field_display;
                    }
                    // Fallback to field_found
                    return full.field_found;
                },
                name: 'field_found',
            };
        },
        
        column_preview: function () {
            let vm = this;
            return {
                data: 'text_preview',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    let text = full.text_preview || full.matching_text || '';
                    let searchText = vm.searchText;
                    
                    // Highlight the search term in the preview
                    if (text && searchText) {
                        try {
                            const escapedSearchText = searchText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                            const regex = new RegExp(`(${escapedSearchText})`, 'gi');
                            text = text.replace(regex, '<mark>$1</mark>');
                        } catch (e) {
                            console.warn('Error highlighting search text:', e);
                        }
                    }
                    
                    // Limit length for display
                    if (text.length > 150) {
                        text = text.substring(0, 150) + '...';
                    }
                    
                    return text;
                }
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
                        try {
                            // Handle different date formats
                            let dateStr = full.created_on;
                            if (typeof dateStr === 'string') {
                                // Try parsing as ISO date
                                const date = moment(dateStr);
                                if (date.isValid()) {
                                    return date.format('DD/MM/YYYY HH:mm');
                                }
                            } else if (dateStr instanceof Date) {
                                return moment(dateStr).format('DD/MM/YYYY HH:mm');
                            }
                        } catch (e) {
                            console.warn('Error formatting date:', e);
                        }
                    }
                    return 'N/A';
                },
                name: 'created_on',
                className: 'text-nowrap'
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
                    
                    // Use detail fields from the result
                    if (full.obj_code) details.push(`<strong>Objective:</strong> ${full.obj_code}`);
                    if (full.task_name) details.push(`<strong>Task:</strong> ${full.task_name}`);
                    if (full.polygon_name) details.push(`<strong>Polygon:</strong> ${full.polygon_name}`);
                    if (full.compartment) details.push(`<strong>Compartment:</strong> ${full.compartment}`);
                    
                    // If we have a details field from the API, use it
                    if (full.details && full.details !== 'No additional details') {
                        return full.details;
                    }
                    
                    return details.length > 0 ? details.join('<br/>') : '<em>No additional details</em>';
                },
                className: 'small'
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
                        // Check if URL is absolute or relative
                        let url = full.action_url;
                        if (!url.startsWith('http') && !url.startsWith('/')) {
                            url = '/' + url;
                        }
                        
                        return `<a href="${url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                  <i class="fa-solid fa-external-link-alt"></i> View
                               </a>`;
                    }
                    return '';
                },
                className: 'text-center'
            };
        },
        
        dtOptions: function () {
            let vm = this;
            
            return {
                autoWidth: true,
                responsive: true,
                serverSide: true,
                searching: true,
                processing: true,
                lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
                pageLength: 10,
                deferLoading: 0, // Don't load until we trigger it
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                    emptyTable: 'No matching records found',
                    info: 'Showing _START_ to _END_ of _TOTAL_ records',
                    infoEmpty: 'Showing 0 to 0 of 0 records',
                    infoFiltered: '(filtered from _MAX_ total records)',
                    lengthMenu: 'Show _MENU_ records',
                    loadingRecords: 'Loading...',
                    search: 'Search within results:',
                    zeroRecords: 'No matching records found'
                },
                ajax: {
                    url: api_endpoints.search_by_text,
                    type: 'GET',
                    dataSrc: 'data',
                    data: function (d) {
                        // Build parameters for the search
                        if (!vm.searchText || vm.searchText.length < 2) {
                            return {};
                        }

                        const params = {
                            search_text: vm.searchText,
                            model: vm.selectedModel,
                            match_type: vm.matchType,
                            date_from: vm.filterDateFrom,
                            date_to: vm.filterDateTo,
                            case_sensitive: vm.caseSensitive,
                            fields: vm.selectedFields, // This will be serialized as array
                            draw: d.draw,
                            start: d.start,
                            length: d.length,
                            order: JSON.stringify(d.order || []),
                            search: JSON.stringify(d.search || {})
                        };
                        
                        return params;
                    },
                    error: function (xhr, error, thrown) {
                        console.error('Datatable AJAX error:', error, thrown);
                        vm.loading = false;
                        swal.fire({
                            title: 'Error',
                            text: 'Failed to load search results. Please try again.',
                            icon: 'error',
                            confirmButtonText: 'OK'
                        });
                    }
                },
                dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
                     "<'row'<'col-sm-12'tr>>" +
                     "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
                order: [[4, 'desc']], // Default order by created date descending
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
                drawCallback: function (settings) {
                    // Update totalRecords on every draw
                    const json = settings.json;
                    if (json) {
                        vm.totalRecords = json.recordsFiltered || json.recordsTotal || 0;
                    }
                    vm.loading = false;
                },
                initComplete: function () {
                    console.log('Text search datatable initialized');
                    
                    // Add custom search delay
                    const api = this.api();
                    const searchInput = $('.dataTables_filter input');
                    searchInput.unbind();
                    searchInput.bind('input', function() {
                        const value = this.value;
                        clearTimeout(this.delay);
                        this.delay = setTimeout(function() {
                            api.search(value).draw();
                        }, 500);
                    });
                },
            };
        }
    },
    methods: {
        async loadAvailableModels() {
            try {
                // Use fetch instead of this.$http
                const response = await fetch(api_endpoints.text_search_available_models);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                this.availableModels = data;
            } catch (error) {
                console.warn('Could not load models from API, using fallback:', error);
                
                // Fallback to default models
                this.availableModels = [
                    { key: 'all', display_name: 'All Records', search_fields_count: 12 },
                    { key: 'proposal', display_name: 'Proposals', search_fields_count: 3 },
                    { key: 'polygon', display_name: 'Polygons', search_fields_count: 2 },
                    { key: 'cohort', display_name: 'Cohorts', search_fields_count: 3 },
                    { key: 'treatment', display_name: 'Treatments', search_fields_count: 2 },
                    { key: 'treatment_xtra', display_name: 'Treatment Extras', search_fields_count: 1 },
                    { key: 'survey_assessment_document', display_name: 'Survey Documents', search_fields_count: 2 },
                    { key: 'silviculturist_comment', display_name: 'Silviculturist Comments', search_fields_count: 1 },
                    { key: 'prescription', display_name: 'Prescriptions', search_fields_count: 1 }
                ];
            }
        },
        
        async loadFieldsForModel(modelKey) {
            this.loadingFields = true;
            this.availableFields = [];
            this.selectedFields = [];
            this.fieldsLoaded = false;
            this.errorMessage = '';
            
            try {
                // Use fetch instead of this.$http
                console.log('URL: ' + api_endpoints.text_search_fields_by_model)
                //const url = `${api_endpoints.text_search_fields_by_model}`;
                const baseUrl = api_endpoints.text_search_fields_by_model;
                const url = `${baseUrl}?model=${encodeURIComponent(modelKey)}`;

                //const url = new URL(api_endpoints.text_search_fields_by_model);
                //url.searchParams.append('model', modelKey);
                
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.fields && Array.isArray(data.fields)) {
                    this.availableFields = data.fields;
                    
                    // Auto-select all fields by default (except for 'all' model where we might want a subset)
                    if (modelKey === 'all') {
                        // For 'all' model, select common fields by default
                        const commonFields = ['comments', 'description', 'title', 'name', 'results'];
                        this.selectedFields = this.availableFields
                            .filter(field => commonFields.includes(field.field_name))
                            .map(field => field.field_name);
                    } else {
                        // For specific model, select all fields
                        this.selectedFields = this.availableFields.map(field => field.field_name);
                    }
                    
                    // Update model display name
                    if (modelKey === 'all') {
                        this.selectedModelDisplay = 'All Records';
                    } else if (data.model && data.model.display_name) {
                        this.selectedModelDisplay = data.model.display_name;
                    } else {
                        // Find in availableModels
                        const model = this.availableModels.find(m => m.key === modelKey);
                        this.selectedModelDisplay = model ? model.display_name : this.$options.filters.formatModelName(modelKey);
                    }
                    
                    console.log(`Loaded ${this.availableFields.length} fields for model: ${modelKey}`);
                } else {
                    this.availableFields = [];
                    this.selectedFields = [];
                    console.warn('No fields returned for model:', modelKey);
                }
                
                this.fieldsLoaded = true;
                
            } catch (error) {
                console.error('Error loading fields for model:', error);
                this.errorMessage = `Failed to load fields: ${error.message}`;
                this.fieldsLoaded = true;
                
                // Fallback to default fields based on model
                this.loadDefaultFieldsForModel(modelKey);
                
                swal.fire({
                    title: 'Warning',
                    text: 'Using default field configuration. Some fields may not be available.',
                    icon: 'warning',
                    confirmButtonText: 'OK'
                });
            } finally {
                this.loadingFields = false;
            }
        },
        
        loadDefaultFieldsForModel(modelKey) {
            // Default field configurations as fallback
            const defaultFields = {
                'all': [
                    { id: 1, field_name: 'comments', display_name: 'Comments', description: 'General comments field' },
                    { id: 2, field_name: 'description', display_name: 'Description', description: 'Description field' },
                    { id: 3, field_name: 'title', display_name: 'Title', description: 'Title field' },
                    { id: 4, field_name: 'name', display_name: 'Name', description: 'Name field' },
                    { id: 5, field_name: 'results', display_name: 'Results', description: 'Results field' }
                ],
                'proposal': [
                    { id: 11, field_name: 'processing_status', display_name: 'Processing Status', description: 'Proposal status' },
                    { id: 12, field_name: 'title', display_name: 'Title', description: 'Proposal title' }
                ],
                'polygon': [
                    { id: 21, field_name: 'name', display_name: 'Name', description: 'Polygon name' }
                ],
                'cohort': [
                    { id: 31, field_name: 'comments', display_name: 'Comments', description: 'Cohort comments' },
                    { id: 32, field_name: 'obj_code', display_name: 'Objective Code', description: 'Objective code' },
                    { id: 33, field_name: 'species', display_name: 'Species', description: 'Species information' }
                ],
                'treatment': [
                    { id: 41, field_name: 'results', display_name: 'Results', description: 'Treatment results' },
                    { id: 42, field_name: 'reference', display_name: 'Reference', description: 'Treatment reference' }
                ]
            };
            
            this.availableFields = defaultFields[modelKey] || defaultFields['all'];
            this.selectedFields = this.availableFields.map(field => field.field_name);
            
            const model = this.availableModels.find(m => m.key === modelKey);
            this.selectedModelDisplay = model ? model.display_name : this.$options.filters.formatModelName(modelKey);
            
            this.fieldsLoaded = true;
        },
        
        async loadDefaultFields() {
            await this.loadFieldsForModel(this.selectedModel);
            swal.fire({
                title: 'Success',
                text: 'Fields reloaded successfully',
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
        },
        
        initializeSelect2() {
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
                    dropdownParent: $(this.$refs.recordsToSearchSelect).parent(),
                    templateResult: this.formatModelOption,
                    templateSelection: this.formatModelSelection
                });
                
                // Set initial value
                this.select2RecordsToSearch.val(this.selectedModel).trigger('change');
                
                // Bind change event
                this.select2RecordsToSearch.on('change', async (event) => {
                    const newModel = $(event.target).val();
                    if (newModel !== this.selectedModel) {
                        this.selectedModel = newModel;
                        await this.loadFieldsForModel(newModel);
                    }
                });
            }
        },
        
        formatModelOption(model) {
            if (!model.id) {
                return model.text;
            }
            
            const $option = $('<span></span>');
            const modelData = this.availableModels.find(m => m.key === model.id);
            
            if (modelData) {
                $option.text(modelData.display_name);
                if (modelData.search_fields_count > 0) {
                    $option.append(` <span class="badge bg-secondary float-end">${modelData.search_fields_count}</span>`);
                }
            } else {
                $option.text(model.text);
            }
            
            return $option;
        },
        
        formatModelSelection(model) {
            if (!model.id) {
                return model.text;
            }
            
            const modelData = this.availableModels.find(m => m.key === model.id);
            return modelData ? modelData.display_name : model.text;
        },
        
        toggleAllFields(event) {
            if (event.target.checked) {
                // Select all fields
                this.selectedFields = this.availableFields.map(field => field.field_name);
            } else {
                // Deselect all fields
                this.selectedFields = [];
            }
        },
        searchRecords() {
            if (!this.searchText || this.searchText.length < 2) {
                swal.fire({
                    title: 'Error',
                    text: 'Please enter at least 2 characters to search',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
                return;
            }

            if (this.selectedFields.length === 0) {
                swal.fire({
                    title: 'Error',
                    text: 'Please select at least one field to search',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
                return;
            }

            this.loading = true;
            this.searchPerformed = true;
            
            // Use a flag to track if this is the first search
            const isFirstSearch = !this.$refs.search_datatable || !this.$refs.search_datatable.vmDataTable;
            
            if (!isFirstSearch) {
                // For subsequent searches, just reload the existing datatable
                const table = this.$refs.search_datatable.vmDataTable;
                
                // Clear and reload with new parameters
                table.clear();
                table.ajax.reload(null, false, (json) => {
                    this.loading = false;
                    this.totalRecords = json.recordsFiltered || json.recordsTotal || 0;
                    
                    if (this.totalRecords === 0) {
                        swal.fire({
                            title: 'No Results',
                            text: 'No records found matching your search criteria.',
                            icon: 'info',
                            confirmButtonText: 'OK'
                        });
                    }
                });
            } else {
                // For first search, wait for datatable to initialize
                this.$nextTick(() => {
                    if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
                        const table = this.$refs.search_datatable.vmDataTable;
                        
                        // Set up a one-time listener for the draw event
                        const onFirstDraw = () => {
                            this.loading = false;
                            this.totalRecords = table.page.info().recordsDisplay;
                            table.off('draw.dt', onFirstDraw);
                            
                            if (this.totalRecords === 0) {
                                swal.fire({
                                    title: 'No Results',
                                    text: 'No records found matching your search criteria.',
                                    icon: 'info',
                                    confirmButtonText: 'OK'
                                });
                            }
                        };
                        
                        table.on('draw.dt', onFirstDraw);
                        
                        // Also set up error handling
                        const onError = () => {
                            this.loading = false;
                        };
                        
                        // Add error event listener (remove it after first error)
                        $(table.table().node()).on('error.dt', onError);
                        
                        // Remove error listener after first draw
                        table.one('draw.dt', () => {
                            $(table.table().node()).off('error.dt', onError);
                        });
                        
                        // Trigger the initial AJAX call
                        table.ajax.reload();
                    } else {
                        // Fallback if datatable still not initialized
                        this.loading = false;
                        this.searchPerformed = true;
                        
                        swal.fire({
                            title: 'Error',
                            text: 'Could not initialize search results table. Please try again.',
                            icon: 'error',
                            confirmButtonText: 'OK'
                        });
                    }
                });
            }
        },
        resetSearch() {
            this.searchText = '';
            //this.filterField = 'all';
            this.matchType = 'contains';
            this.filterDateFrom = '';
            this.filterDateTo = '';
            this.caseSensitive = false;
            this.selectedModel = 'all';
            this.selectedFields = ['comment', 'description', 'title', 'name', 'results'];
            this.searchPerformed = false;
            this.totalRecords = 0;
            this.errorMessage = '';
            
            // Reset Select2
            if (this.select2RecordsToSearch) {
                this.select2RecordsToSearch.val('all').trigger('change');
            }
            
            // Reload fields for 'all' model
            this.loadFieldsForModel('all');
            
            // Clear datatable if it exists
            if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
                this.$refs.search_datatable.vmDataTable.clear();
                this.$refs.search_datatable.vmDataTable.draw();
            }
        },
        
        exportResults() {
            // Export functionality would go here
            swal.fire({
                title: 'Export Results',
                text: 'Export functionality will be implemented soon.',
                icon: 'info',
                confirmButtonText: 'OK'
            });
        },
        
        destroySelect2() {
            // Destroy Records to Search Select2
            if (this.select2RecordsToSearch && this.select2RecordsToSearch.select2) {
                this.select2RecordsToSearch.off('change');
                this.select2RecordsToSearch.select2('destroy');
                this.select2RecordsToSearch = null;
            }
        },
        
        collapsible_component_mounted() {
            if (this.$refs.collapsible_filters) {
                this.$refs.collapsible_filters.show_warning_icon(false);
            }
        }
    },
    async mounted() {
        console.log('SearchByText component mounted');
        
        // Load available models
        await this.loadAvailableModels();
        
        // Load fields for default model
        await this.loadFieldsForModel('all');
        
        // Initialize Select2 after component is mounted
        this.$nextTick(() => {
            setTimeout(() => {
                this.initializeSelect2();
            }, 300);
        });
    },
    beforeDestroy() {
        // Clean up the datatable to prevent memory leaks
        if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
            this.$refs.search_datatable.vmDataTable.destroy(true);
        }
        this.destroySelect2();
    },
    beforeUnmount() {
        // Clean up Select2 instances
        this.destroySelect2();
    },
    
    watch: {
        selectedFields(newVal, oldVal) {
            // If all fields were selected and one gets deselected, update the "Select All" checkbox
            if (oldVal && oldVal.length === this.availableFields.length && newVal.length < oldVal.length) {
                // The "Select All" checkbox will automatically update due to computed property
            }
        }
    }
};
</script>

<style scoped>
.form-check-inline {
    margin-right: 20px;
    margin-bottom: 10px;
    min-width: 200px;
}

.form-check-label {
    cursor: pointer;
    user-select: none;
}

.form-check-input {
    cursor: pointer;
}

mark {
    background-color: #fff3cd;
    padding: 0 2px;
    border-radius: 2px;
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

/* Datatable styling */
:deep(.dataTables_wrapper) {
    padding: 0;
}

:deep(.dataTables_filter) {
    margin-bottom: 1rem;
}

:deep(.dataTables_length) {
    margin-bottom: 1rem;
}

:deep(.table) {
    margin-bottom: 0;
}

:deep(.table th) {
    background-color: #f8f9fa;
    border-bottom: 2px solid #dee2e6;
}

:deep(.table-striped tbody tr:nth-of-type(odd)) {
    background-color: rgba(0, 0, 0, 0.02);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .form-check-inline {
        min-width: 100%;
        margin-right: 0;
    }
    
    .select2-container--bootstrap-5 {
        width: 100% !important;
    }
}

/* Loading animation */
.spinner-border {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

/* Card styling */
.card {
    border: 1px solid rgba(0, 0, 0, 0.125);
    border-radius: 0.375rem;
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card-header {
    border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

/* Alert styling */
.alert {
    border-radius: 0.375rem;
    border: 1px solid transparent;
}

.alert-warning {
    background-color: #fff3cd;
    border-color: #ffeaa7;
    color: #856404;
}

.alert-success {
    background-color: #d4edda;
    border-color: #c3e6cb;
    color: #155724;
}

.alert-info {
    background-color: #d1ecf1;
    border-color: #bee5eb;
    color: #0c5460;
}

/* Badge styling */
.badge {
    font-size: 0.75em;
    padding: 0.25em 0.5em;
}

/* Button styling */
.btn {
    border-radius: 0.375rem;
    font-weight: 500;
}

.btn-primary {
    background-color: #0d6efd;
    border-color: #0d6efd;
}

.btn-primary:hover {
    background-color: #0b5ed7;
    border-color: #0a58ca;
}

.btn-primary:disabled {
    background-color: #6c757d;
    border-color: #6c757d;
    opacity: 0.65;
}

.btn-outline-primary {
    color: #0d6efd;
    border-color: #0d6efd;
}

.btn-outline-primary:hover {
    background-color: #0d6efd;
    border-color: #0d6efd;
    color: white;
}

/* Tooltip-like for field descriptions */
[title]:hover:after {
    content: attr(title);
    position: absolute;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 0.85em;
    z-index: 1000;
    white-space: pre-wrap;
    max-width: 300px;
}

/* Make select2 badges look better in dropdown */
.select2-container--bootstrap-5 .select2-results__option .badge {
    float: right;
    margin-top: 2px;
}
</style>
