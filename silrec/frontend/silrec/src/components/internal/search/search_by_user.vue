<template>
    <div>
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/search/search_by_user.vue</div>
        
        <CollapsibleFilters
            ref="collapsible_filters"
            component_title="Search by Editor"
            class="mb-2"
            @created="collapsible_component_mounted"
            :collapsed="false"
        >
            <div class="row mt-1 p-2">
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="">Select Editor</label>
                        <select
                            ref="userSelect"
                            class="form-select select2-single"
                            style="width: 100%;"
                        >
                            <option value="">Select an editor...</option>
                            <option v-for="user in userOptions" 
                                    :key="user.id"
                                    :value="user.id">
                                {{ user.full_name }} ({{ user.email }})
                            </option>
                        </select>
                        <small class="form-text text-muted">
                            Select an editor to find all records associated with them
                        </small>
                    </div>
                </div>
                
                <div class="col-md-2">
                    <div class="form-group">
                        <label for="">Search Mode</label>
                        <select
                            v-model="searchMode"
                            class="form-select"
                        >
                            <option value="created_by">Created By</option>
                            <option value="updated_by">Updated By</option>
                            <option value="submitted_by">Submitted By</option>
                            <!-- 
                            <option value="assigned_to">Assigned To</option>
                            <option value="referral">Referral</option>
                            -->
                            <option value="all">All Editor Fields</option>
                        </select>
                    </div>
                </div>

                <div class="col-md-2">
                    <div class="form-group">
                        <label for="">Record Type</label>
                        <select
                            v-model="modelType"
                            class="form-select"
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
                <div class="col-md-2">
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
                <!--
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
                        <label for="">Include Inactive</label>
                        <div class="form-check form-switch mt-2">
                            <input
                                class="form-check-input"
                                type="checkbox"
                                id="includeInactiveSwitch"
                                v-model="includeInactive"
                            />
                            <label class="form-check-label" for="includeInactiveSwitch">
                                {{ includeInactive ? 'Yes' : 'No' }}
                            </label>
                        </div>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="form-group">
                        <label for="">Results per page</label>
                        <select
                            v-model="pageSize"
                            class="form-select"
                        >
                            <option value="10">10</option>
                            <option value="25">25</option>
                            <option value="50">50</option>
                            <option value="100">100</option>
                        </select>
                    </div>
                </div>
                -->
                
                <div class="col-md-12 mt-4">
                    <div class="text-end">
                        <button
                            type="button"
                            class="btn btn-primary me-2"
                            @click="searchRecords"
                            :disabled="!selectedUser"
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
                            @click="refreshUserList"
                            title="Refresh user list"
                        >
                            <i class="fa-solid fa-users"></i> Refresh Users
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
                            <span class="ms-2">
                                for user: <strong>{{ selectedUserName }}</strong>
                            </span>
                            <span v-if="searchMode !== 'all'" class="ms-2">
                                ({{ searchModeDisplay }})
                            </span>
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
                    <div v-if="selectedModelDisplay !== 'All Records'" class="mt-2 small">
                        <span class="text-muted">Searching in: </span>
                        <span class="fst-italic">{{ selectedModelDisplay }}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="row" v-show="searchPerformed">
            <div class="col-lg-12">
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Search Editor Results</h5>
                        <div class="small text-muted mt-1">
                            Showing records for: <strong>{{ selectedUserName }}</strong>
                        </div>
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
    name: 'SearchByUser',
    components: {
        datatable,
        CollapsibleFilters
    },
    data() {
        let vm = this;
        return {
            datatable_id: 'user-search-datatable-' + uuid(),
            
            // Search filters
            selectedUser: null,
            selectedUserName: '',
            searchMode: 'all',
            modelType: 'all',
            filterDateFrom: '',
            filterDateTo: '',
            includeInactive: false,
            pageSize: 25,
            
            // User list
            userOptions: [],
            loadingUsers: false,
            
            // Loading states
            loading: false,
            
            // Search results
            searchPerformed: false,
            totalRecords: 0,
            
            // Select2 instance
            select2UserSelect: null,
            
            // Error handling
            errorMessage: ''
        };
    },
    computed: {
        searchModeDisplay() {
            const modes = {
                'created_by': 'Created By',
                'updated_by': 'Updated By',
                'submitted_by': 'Submitted By',
                //'assigned_to': 'Assigned To',
                //'referral': 'Referral',
                'all': 'All User Fields'
            };
            return modes[this.searchMode] || this.searchMode;
        },
        
        selectedModelDisplay() {
            const models = {
                'all': 'All Records',
                'proposal': 'Proposals',
                'polygon': 'Polygons',
                'cohort': 'Cohorts',
                'treatment': 'Treatments',
                'treatment_xtra': 'Treatment Extras',
                'survey_assessment_document': 'Survey Documents',
                'silviculturist_comment': 'Silviculturist Comments',
                'prescription': 'Prescriptions'
            };
            return models[this.modelType] || this.modelType;
        },
        
        getSearchButtonTitle() {
            if (!this.selectedUser) {
                return 'Please select a user to search';
            }
            return `Search records for ${this.selectedUserName}`;
        },
        
        dtHeaders: function () {
            return [
                'Model',
                'Record ID',
                'User Role',
                'Title/Name',
                'Status',
                'Created On',
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
                    const modelNames = {
                        'proposal': 'Proposal',
                        'polygon': 'Polygon',
                        'cohort': 'Cohort',
                        'treatment': 'Treatment',
                        'treatment_xtra': 'Treatment Extra',
                        'survey_assessment_document': 'Survey Document',
                        'silviculturist_comment': 'Silviculturist Comment',
                        'prescription': 'Prescription'
                    };
                    return modelNames[full.model_type] || full.model_type;
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
        
        column_user_role: function () {
            let vm = this;
            return {
                data: 'user_role',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.user_role_display || full.user_role || 'Unknown';
                },
                name: 'user_role',
            };
        },
        
        column_title: function () {
            return {
                data: 'title',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    let title = full.title || full.name || full.description || 'N/A';
                    // Limit length for display
                    if (title.length > 50) {
                        title = title.substring(0, 50) + '...';
                    }
                    return title;
                }
            };
        },
        
        column_status: function () {
            return {
                data: 'status',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (!full.status) return 'N/A';
                    
                    let statusClass = 'secondary';
                    const statusText = full.status_display || full.status;
                    
                    // Add color coding based on status
                    if (statusText.toLowerCase().includes('approved') || 
                        statusText.toLowerCase().includes('complete') ||
                        statusText.toLowerCase().includes('active')) {
                        statusClass = 'success';
                    } else if (statusText.toLowerCase().includes('pending') || 
                               statusText.toLowerCase().includes('in progress') ||
                               statusText.toLowerCase().includes('draft')) {
                        statusClass = 'warning';
                    } else if (statusText.toLowerCase().includes('rejected') || 
                               statusText.toLowerCase().includes('cancelled') ||
                               statusText.toLowerCase().includes('inactive')) {
                        statusClass = 'danger';
                    }
                    
                    return `<span class="badge bg-${statusClass}">${statusText}</span>`;
                },
                name: 'status',
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
                            let dateStr = full.created_on;
                            if (typeof dateStr === 'string') {
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
        
        column_action: function () {
            let vm = this;
            return {
                data: 'action_url',
                orderable: false,
                searchable: false,
                visible: true,
                render: function (row, type, full) {
                    if (full.action_url) {
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
                autoWidth: false,
                responsive: true,
                serverSide: true,
                searching: true,
                processing: true,
                lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
                pageLength: vm.pageSize,
                deferLoading: 0,
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
                    url: vm.getSearchEndpoint(),
                    type: 'GET',
                    dataSrc: 'data',
                    data: function (d) {
                        if (!vm.selectedUser) {
                            return {};
                        }

                        const params = {
                            user_id: vm.selectedUser,
                            search_mode: vm.searchMode,
                            model_type: vm.modelType,
                            date_from: vm.filterDateFrom,
                            date_to: vm.filterDateTo,
                            include_inactive: vm.includeInactive,
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
                        vm.showError('Failed to load search results. Please try again.');
                    }
                },
                dom: "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
                     "<'row'<'col-sm-12'tr>>" +
                     "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
                order: [[5, 'desc']], // Default order by created date descending
                columns: [
                    vm.column_model,
                    vm.column_id,
                    vm.column_user_role,
                    vm.column_title,
                    vm.column_status,
                    vm.column_created,
                    vm.column_action
                ],
                drawCallback: function (settings) {
                    const json = settings.json;
                    if (json) {
                        vm.totalRecords = json.recordsFiltered || json.recordsTotal || 0;
                    }
                    vm.loading = false;
                },
                initComplete: function () {
                    console.log('User search datatable initialized');
                    
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
        getSearchEndpoint() {
            // This should point to your backend API endpoint for user search
            // For now, we'll use the same endpoint structure as text search
            return '/api/search_by_user/';
        },
        
        async loadUsers() {
            this.loadingUsers = true;
            try {
                // Use the users endpoint from your API
                const response = await fetch(api_endpoints.users);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                
                // Transform data to match our format
                this.userOptions = data.map(user => ({
                    id: user.id,
                    full_name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email,
                    email: user.email,
                    first_name: user.first_name,
                    last_name: user.last_name
                }));
                
                // Sort by full name
                this.userOptions.sort((a, b) => {
                    const nameA = a.full_name.toLowerCase();
                    const nameB = b.full_name.toLowerCase();
                    if (nameA < nameB) return -1;
                    if (nameA > nameB) return 1;
                    return 0;
                });
                
            } catch (error) {
                console.error('Error loading users:', error);
                this.showError('Failed to load user list. Please try again.');
                
                // Fallback with sample data
                this.userOptions = [
                    { id: 1, full_name: 'Admin User', email: 'admin@example.com' },
                    { id: 2, full_name: 'Test User', email: 'test@example.com' }
                ];
            } finally {
                this.loadingUsers = false;
            }
        },
        
        async refreshUserList() {
            await this.loadUsers();
            this.initializeSelect2();
            this.showSuccess('User list refreshed successfully');
        },
        
        initializeSelect2() {
            // Initialize User Select2
            if (this.$refs.userSelect) {
                // Destroy existing instance if any
                if (this.select2UserSelect && this.select2UserSelect.select2) {
                    this.select2UserSelect.select2('destroy');
                }
                
                // Initialize Select2
                this.select2UserSelect = $(this.$refs.userSelect).select2({
                    theme: 'bootstrap-5',
                    placeholder: 'Select an editor...',
                    allowClear: true,
                    width: '100%',
                    dropdownParent: $(this.$refs.userSelect).parent(),
                    templateResult: this.formatUserOption,
                    templateSelection: this.formatUserSelection
                });
                
                // Bind change event
                this.select2UserSelect.on('change', (event) => {
                    const userId = $(event.target).val();
                    this.selectedUser = userId ? parseInt(userId) : null;
                    
                    // Update selected user name
                    if (this.selectedUser) {
                        const user = this.userOptions.find(u => u.id === this.selectedUser);
                        this.selectedUserName = user ? `${user.full_name} (${user.email})` : '';
                    } else {
                        this.selectedUserName = '';
                    }
                });
            }
        },
        
        formatUserOption(user) {
            if (!user.id) {
                return user.text;
            }
            
            const $option = $('<span></span>');
            const userData = this.userOptions.find(u => u.id === user.id);
            
            if (userData) {
                $option.text(`${userData.full_name} (${userData.email})`);
            } else {
                $option.text(user.text);
            }
            
            return $option;
        },
        
        formatUserSelection(user) {
            if (!user.id) {
                return user.text;
            }
            
            const userData = this.userOptions.find(u => u.id === user.id);
            return userData ? `${userData.full_name} (${userData.email})` : user.text;
        },
        
        searchRecords() {
            if (!this.selectedUser) {
                this.showError('Please select a user to search');
                return;
            }

            this.loading = true;
            this.searchPerformed = true;
            
            const isFirstSearch = !this.$refs.search_datatable || !this.$refs.search_datatable.vmDataTable;
            
            if (!isFirstSearch) {
                const table = this.$refs.search_datatable.vmDataTable;
                
                table.clear();
                table.ajax.reload(null, false, (json) => {
                    this.loading = false;
                    this.totalRecords = json.recordsFiltered || json.recordsTotal || 0;
                    
                    if (this.totalRecords === 0) {
                        this.showInfo('No records found for the selected user and criteria.');
                    }
                });
            } else {
                this.$nextTick(() => {
                    if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
                        const table = this.$refs.search_datatable.vmDataTable;
                        
                        const onFirstDraw = () => {
                            this.loading = false;
                            this.totalRecords = table.page.info().recordsDisplay;
                            table.off('draw.dt', onFirstDraw);
                            
                            if (this.totalRecords === 0) {
                                this.showInfo('No records found for the selected user and criteria.');
                            }
                        };
                        
                        table.on('draw.dt', onFirstDraw);
                        
                        const onError = () => {
                            this.loading = false;
                        };
                        
                        $(table.table().node()).on('error.dt', onError);
                        
                        table.one('draw.dt', () => {
                            $(table.table().node()).off('error.dt', onError);
                        });
                        
                        table.ajax.reload();
                    } else {
                        this.loading = false;
                        this.searchPerformed = true;
                        this.showError('Could not initialize search results table. Please try again.');
                    }
                });
            }
        },
        
        resetSearch() {
            this.selectedUser = null;
            this.selectedUserName = '';
            this.searchMode = 'all';
            this.modelType = 'all';
            this.filterDateFrom = '';
            this.filterDateTo = '';
            this.includeInactive = false;
            this.pageSize = 25;
            this.searchPerformed = false;
            this.totalRecords = 0;
            this.errorMessage = '';
            
            // Reset Select2
            if (this.select2UserSelect) {
                this.select2UserSelect.val('').trigger('change');
            }
            
            // Clear datatable if it exists
            if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
                this.$refs.search_datatable.vmDataTable.clear();
                this.$refs.search_datatable.vmDataTable.draw();
            }
        },
        
        exportResults() {
            if (!this.selectedUser) {
                this.showError('Please select a user first');
                return;
            }
            
            // Build export URL
            const params = new URLSearchParams({
                user_id: this.selectedUser,
                search_mode: this.searchMode,
                model_type: this.modelType,
                date_from: this.filterDateFrom,
                date_to: this.filterDateTo,
                include_inactive: this.includeInactive,
                export: 'csv'
            });
            
            const exportUrl = `${this.getSearchEndpoint()}?${params.toString()}`;
            
            // Create temporary link to trigger download
            const link = document.createElement('a');
            link.href = exportUrl;
            link.download = `user_search_${this.selectedUser}_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },
        
        showError(message) {
            swal.fire({
                title: 'Error',
                text: message,
                icon: 'error',
                confirmButtonText: 'OK'
            });
        },
        
        showSuccess(message) {
            swal.fire({
                title: 'Success',
                text: message,
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
        },
        
        showInfo(message) {
            swal.fire({
                title: 'No Results',
                text: message,
                icon: 'info',
                confirmButtonText: 'OK'
            });
        },
        
        destroySelect2() {
            if (this.select2UserSelect && this.select2UserSelect.select2) {
                this.select2UserSelect.off('change');
                this.select2UserSelect.select2('destroy');
                this.select2UserSelect = null;
            }
        },
        
        collapsible_component_mounted() {
            if (this.$refs.collapsible_filters) {
                this.$refs.collapsible_filters.show_warning_icon(false);
            }
        }
    },
    async mounted() {
        console.log('SearchByUser component mounted');
        
        // Load users
        await this.loadUsers();
        
        // Initialize Select2 after component is mounted
        this.$nextTick(() => {
            setTimeout(() => {
                this.initializeSelect2();
            }, 300);
        });
    },
    beforeDestroy() {
        if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
            this.$refs.search_datatable.vmDataTable.destroy(true);
        }
        this.destroySelect2();
    },
    beforeUnmount() {
        this.destroySelect2();
    },
    
    watch: {
        pageSize(newSize) {
            if (this.$refs.search_datatable && this.$refs.search_datatable.vmDataTable) {
                this.$refs.search_datatable.vmDataTable.page.len(newSize).draw();
            }
        }
    }
};
</script>

<style scoped>
/* Similar styles to search_by_text.vue */
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

/* Badge styling for status */
:deep(.badge) {
    font-size: 0.85em;
    padding: 0.35em 0.65em;
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

.toggle_filters_button {
	color: blue !important;
}
</style>
