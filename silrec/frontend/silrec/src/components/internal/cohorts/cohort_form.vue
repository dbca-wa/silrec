<template>
    <div class="cohort-form">
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">
            src/components/internal/cohorts/cohort_form.vue
        </div>
        <div v-if="loadingLookups" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading lookups...</span>
            </div>
            <p class="mt-2">Loading lookup data...</p>
        </div>

        <div v-else-if="lookupError" class="alert alert-warning">
            <i class="bi bi-exclamation-triangle"></i>
            Unable to load lookup data: {{ lookupError }}
        </div>

        <div v-else>
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group mb-3">
                        <label for="objCode" class="form-label required"
                            >Objective Code</label
                        >
                        <div class="searchable-select">
                            <input
                                id="objCode"
                                v-model="objectiveSearch"
                                type="text"
                                class="form-control"
                                :readonly="readOnly"
                                placeholder="Type to search objectives..."
                                @focus="showObjectiveDropdown = true"
                                @blur="onObjectiveBlur"
                                @input="filterObjectives"
                            />
                            <div
                                v-if="showObjectiveDropdown"
                                class="dropdown-options"
                            >
                                <div
                                    v-for="objective in filteredObjectives"
                                    :key="objective.id"
                                    class="dropdown-option"
                                    @mousedown="selectObjective(objective)"
                                >
                                    <strong>{{ objective.obj_code }}</strong> -
                                    {{
                                        objective.description ||
                                        'No description'
                                    }}
                                </div>
                                <div
                                    v-if="filteredObjectives.length === 0"
                                    class="dropdown-option no-results"
                                >
                                    No objectives found
                                </div>
                            </div>
                        </div>
                        <div class="form-text">
                            Silvicultural or management objective
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group mb-3">
                        <label for="species" class="form-label">Species</label>
                        <div class="searchable-select">
                            <input
                                id="species"
                                v-model="speciesSearch"
                                type="text"
                                class="form-control"
                                :readonly="readOnly"
                                placeholder="Type to search species..."
                                @focus="showSpeciesDropdown = true"
                                @blur="onSpeciesBlur"
                                @input="filterSpecies"
                            />
                            <div
                                v-if="showSpeciesDropdown"
                                class="dropdown-options"
                            >
                                <div
                                    v-for="species in filteredSpecies"
                                    :key="species.id"
                                    class="dropdown-option"
                                    @mousedown="selectSpecies(species)"
                                >
                                    <strong>{{ species.species }}</strong> -
                                    {{
                                        species.short_description ||
                                        species.full_description ||
                                        'No description'
                                    }}
                                </div>
                                <div
                                    v-if="filteredSpecies.length === 0"
                                    class="dropdown-option no-results"
                                >
                                    No species found
                                </div>
                            </div>
                        </div>
                        <div class="form-text">
                            Dominant overstorey API species
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div class="form-group mb-3">
                        <label for="regenMethod" class="form-label required"
                            >Regeneration Method</label
                        >
                        <div class="searchable-select">
                            <input
                                id="regenMethod"
                                v-model="regenMethodSearch"
                                type="text"
                                class="form-control"
                                :readonly="readOnly"
                                placeholder="Type to search regeneration methods..."
                                @focus="showRegenMethodDropdown = true"
                                @blur="onRegenMethodBlur"
                                @input="filterRegenMethods"
                            />
                            <div
                                v-if="showRegenMethodDropdown"
                                class="dropdown-options"
                            >
                                <div
                                    v-for="method in filteredRegenMethods"
                                    :key="method.id"
                                    class="dropdown-option"
                                    @mousedown="selectRegenMethod(method)"
                                >
                                    <strong>{{ method.regen_method }}</strong> -
                                    {{ method.description || 'No description' }}
                                </div>
                                <div
                                    v-if="filteredRegenMethods.length === 0"
                                    class="dropdown-option no-results"
                                >
                                    No regeneration methods found
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group mb-3">
                        <label for="siteQuality" class="form-label"
                            >Site Quality</label
                        >
                        <input
                            id="siteQuality"
                            v-model="formData.site_quality"
                            type="text"
                            class="form-control"
                            :readonly="readOnly"
                            maxlength="6"
                        />
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-4">
                    <div class="form-group mb-3">
                        <label for="targetBa" class="form-label"
                            >Target BA (m²/ha)</label
                        >
                        <input
                            id="targetBa"
                            v-model.number="formData.target_ba_m2ha"
                            type="number"
                            step="0.1"
                            min="0"
                            class="form-control"
                            :readonly="readOnly"
                        />
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group mb-3">
                        <label for="residualBa" class="form-label"
                            >Residual BA (m²/ha)</label
                        >
                        <input
                            id="residualBa"
                            v-model.number="formData.resid_ba_m2ha"
                            type="number"
                            step="0.1"
                            min="0"
                            class="form-control"
                            :readonly="readOnly"
                        />
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="form-group mb-3">
                        <label for="targetSpha" class="form-label"
                            >Target SPHA</label
                        >
                        <input
                            id="targetSpha"
                            v-model.number="formData.target_spha"
                            type="number"
                            min="0"
                            class="form-control"
                            :readonly="readOnly"
                        />
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-12">
                    <div class="form-group mb-3">
                        <label for="comments" class="form-label"
                            >Comments</label
                        >
                        <textarea
                            id="comments"
                            v-model="formData.comments"
                            class="form-control"
                            rows="3"
                            :readonly="readOnly"
                            maxlength="250"
                        ></textarea>
                        <div class="form-text">
                            {{
                                formData.comments
                                    ? formData.comments.length
                                    : 0
                            }}/250 characters
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'CohortForm',
    props: {
        cohortData: {
            type: Object,
            required: true,
        },
        readOnly: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            formData: {},
            lookups: {
                objectives: [],
                species: [],
                regeneration_methods: [],
            },
            loadingLookups: false,
            lookupError: null,

            // Search and dropdown states
            objectiveSearch: '',
            speciesSearch: '',
            regenMethodSearch: '',
            showObjectiveDropdown: false,
            showSpeciesDropdown: false,
            showRegenMethodDropdown: false,

            // Filtered lists
            filteredObjectives: [],
            filteredSpecies: [],
            filteredRegenMethods: [],
        };
    },
    watch: {
        cohortData: {
            handler(newData) {
                this.initializeFormData(newData);
            },
            immediate: true,
            deep: true,
        },
    },
    methods: {
        initializeFormData(cohortData) {
            this.formData = {
                obj_code: cohortData.obj_code || '',
                species: cohortData.species || '',
                regen_method: cohortData.regen_method || '',
                target_ba_m2ha: cohortData.target_ba_m2ha || null,
                resid_ba_m2ha: cohortData.resid_ba_m2ha || null,
                target_spha: cohortData.target_spha || null,
                site_quality: cohortData.site_quality || '',
                comments: cohortData.comments || '',
            };

            // Initialize search fields with current values
            this.initializeSearchFields();
        },

        initializeSearchFields() {
            // Set search fields to display current values
            if (this.formData.obj_code && this.lookups.objectives.length > 0) {
                const currentObj = this.lookups.objectives.find(
                    (obj) => obj.obj_code === this.formData.obj_code
                );
                this.objectiveSearch = currentObj
                    ? `${currentObj.obj_code} - ${currentObj.description || ''}`
                    : this.formData.obj_code;
            }

            if (this.formData.species && this.lookups.species.length > 0) {
                const currentSpecies = this.lookups.species.find(
                    (sp) => sp.species === this.formData.species
                );
                this.speciesSearch = currentSpecies
                    ? `${currentSpecies.species} - ${currentSpecies.short_description || currentSpecies.full_description || ''}`
                    : this.formData.species;
            }

            if (
                this.formData.regen_method &&
                this.lookups.regeneration_methods.length > 0
            ) {
                const currentMethod = this.lookups.regeneration_methods.find(
                    (method) =>
                        method.regen_method === this.formData.regen_method
                );
                this.regenMethodSearch = currentMethod
                    ? `${currentMethod.regen_method} - ${currentMethod.description || ''}`
                    : this.formData.regen_method;
            }
        },

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
                this.lookups.objectives = data.objectives || [];
                this.lookups.species = data.species || [];
                this.lookups.regeneration_methods =
                    data.regeneration_methods || [];

                // Initialize filtered lists with all items
                this.filteredObjectives = [...this.lookups.objectives];
                this.filteredSpecies = [...this.lookups.species];
                this.filteredRegenMethods = [
                    ...this.lookups.regeneration_methods,
                ];

                // Re-initialize search fields with lookups loaded
                this.initializeSearchFields();

                console.log('Lookups loaded successfully:', {
                    objectives: this.lookups.objectives.length,
                    species: this.lookups.species.length,
                    regeneration_methods:
                        this.lookups.regeneration_methods.length,
                });
            } catch (error) {
                console.error('Error loading lookups:', error);
                this.lookupError = error.message;
                await swal.fire({
                    icon: 'error',
                    title: 'Load Failed',
                    text: 'Failed to load lookup data',
                    confirmButtonText: 'OK',
                });
            } finally {
                this.loadingLookups = false;
            }
        },

        // Objective methods
        filterObjectives() {
            const searchTerm = this.objectiveSearch.toLowerCase();
            this.filteredObjectives = this.lookups.objectives.filter(
                (obj) =>
                    obj.obj_code.toLowerCase().includes(searchTerm) ||
                    (obj.description &&
                        obj.description.toLowerCase().includes(searchTerm))
            );
        },

        selectObjective(objective) {
            this.formData.obj_code = objective.obj_code;
            this.objectiveSearch = `${objective.obj_code} - ${objective.description || ''}`;
            this.showObjectiveDropdown = false;
        },

        onObjectiveBlur() {
            // Use setTimeout to allow click event to register before hiding dropdown
            setTimeout(() => {
                this.showObjectiveDropdown = false;
            }, 200);
        },

        // Species methods
        filterSpecies() {
            const searchTerm = this.speciesSearch.toLowerCase();
            this.filteredSpecies = this.lookups.species.filter(
                (sp) =>
                    sp.species.toLowerCase().includes(searchTerm) ||
                    (sp.short_description &&
                        sp.short_description
                            .toLowerCase()
                            .includes(searchTerm)) ||
                    (sp.full_description &&
                        sp.full_description.toLowerCase().includes(searchTerm))
            );
        },

        selectSpecies(species) {
            this.formData.species = species.species;
            this.speciesSearch = `${species.species} - ${species.short_description || species.full_description || ''}`;
            this.showSpeciesDropdown = false;
        },

        onSpeciesBlur() {
            setTimeout(() => {
                this.showSpeciesDropdown = false;
            }, 200);
        },

        // Regeneration Method methods
        filterRegenMethods() {
            const searchTerm = this.regenMethodSearch.toLowerCase();
            this.filteredRegenMethods =
                this.lookups.regeneration_methods.filter(
                    (method) =>
                        method.regen_method
                            .toLowerCase()
                            .includes(searchTerm) ||
                        (method.description &&
                            method.description
                                .toLowerCase()
                                .includes(searchTerm))
                );
        },

        selectRegenMethod(method) {
            this.formData.regen_method = method.regen_method;
            this.regenMethodSearch = `${method.regen_method} - ${method.description || ''}`;
            this.showRegenMethodDropdown = false;
        },

        onRegenMethodBlur() {
            setTimeout(() => {
                this.showRegenMethodDropdown = false;
            }, 200);
        },

        // Helper method to get display value for a lookup field
        getLookupDisplayValue(fieldName, value) {
            const lookupMap = {
                obj_code: {
                    data: this.lookups.objectives,
                    key: 'obj_code',
                    display: 'description',
                },
                species: {
                    data: this.lookups.species,
                    key: 'species',
                    display: 'short_description',
                },
                regen_method: {
                    data: this.lookups.regeneration_methods,
                    key: 'regen_method',
                    display: 'description',
                },
            };

            const config = lookupMap[fieldName];
            if (!config || !value) return value;

            const item = config.data.find((item) => item[config.key] === value);
            return item
                ? `${item[config.key]} - ${item[config.display] || 'No description'}`
                : value;
        },
    },
    mounted() {
        this.loadLookups();
    },
};
</script>

<style scoped>
.cohort-form {
    max-width: 100%;
}

.form-group {
    margin-bottom: 1rem;
}

.form-label {
    font-weight: 500;
    margin-bottom: 0.5rem;
}

.form-label.required::after {
    content: ' *';
    color: #dc3545;
}

.form-control:read-only {
    background-color: #e9ecef;
    opacity: 1;
}

.form-text {
    font-size: 0.75rem;
    color: #6c757d;
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
    z-index: 9999; /* Increased to dominate other components */
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

/* Loading state */
.spinner-border {
    width: 3rem;
    height: 3rem;
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

/* Ensure no other components can overlap */
* {
    position: relative;
}

.searchable-select .dropdown-options {
    position: absolute !important;
}
</style>
