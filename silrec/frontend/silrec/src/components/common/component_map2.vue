<template>
    <div class="container">
        <h1>Map Search</h1>
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">
            src/components/common/component_map2.vue
        </div>
        <div class="map-container" :class="{ maximised: isMaximised }">
            <div ref="mapContainer" class="map"></div>

            <!-- Feature info popup -->
            <div
                v-if="selectedFeature"
                class="feature-popup"
                :style="popupStyle"
            >
                <div class="popup-header">
                    <h3>Feature Details</h3>
                    <button @click="closeFeaturePopup" class="close-btn">
                        ×
                    </button>
                </div>
                <div class="feature-content">
                    <!-- Basic attributes table -->
                    <table class="feature-table basic-attributes">
                        <tbody>
                            <tr>
                                <th class="field-label">Block:</th>
                                <td class="field-value">
                                    {{
                                        getFeatureValue(
                                            selectedFeature,
                                            'compartment_details.block'
                                        )
                                    }}
                                </td>
                            </tr>
                            <tr>
                                <th class="field-label">Comp No.:</th>
                                <td class="field-value">
                                    {{
                                        getFeatureValue(
                                            selectedFeature,
                                            'compartment_details.compartment'
                                        )
                                    }}
                                </td>
                            </tr>
                            <tr>
                                <th class="field-label">FEA ID:</th>
                                <td class="field-value">
                                    {{
                                        getFeatureValue(
                                            selectedFeature,
                                            'zfea_id'
                                        )
                                    }}
                                </td>
                            </tr>
                            <tr>
                                <th class="field-label">Area (ha):</th>
                                <td class="field-value">
                                    {{
                                        getFeatureValue(
                                            selectedFeature,
                                            'area_ha'
                                        )
                                    }}
                                </td>
                            </tr>
                            <tr>
                                <th class="field-label">Objective Code:</th>
                                <td class="field-value">
                                    {{
                                        getFeatureValue(
                                            selectedFeature,
                                            'primary_cohort.obj_code'
                                        )
                                    }}
                                </td>
                            </tr>
                            <tr>
                                <th class="field-label">Target BA:</th>
                                <td class="field-value">
                                    {{
                                        getFeatureValue(
                                            selectedFeature,
                                            'primary_cohort.target_ba_m2ha'
                                        )
                                    }}
                                </td>
                            </tr>
                            <tr>
                                <th class="field-label">Species:</th>
                                <td class="field-value">
                                    {{
                                        getFeatureValue(
                                            selectedFeature,
                                            'primary_cohort.species'
                                        )
                                    }}
                                </td>
                            </tr>
                        </tbody>
                    </table>

                    <!-- Information icon toggle -->
                    <div class="info-toggle-section">
                        <button
                            class="info-toggle-btn"
                            @click="showAdditionalInfo = !showAdditionalInfo"
                            :title="
                                showAdditionalInfo
                                    ? 'Hide additional details'
                                    : 'Show additional details'
                            "
                        >
                            <svg
                                width="14"
                                height="14"
                                viewBox="0 0 24 24"
                                fill="currentColor"
                            >
                                <path
                                    d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"
                                />
                            </svg>
                            <span class="toggle-text">
                                {{
                                    showAdditionalInfo
                                        ? 'Less details'
                                        : 'More details...'
                                }}
                            </span>
                        </button>
                    </div>

                    <!-- Additional attributes in table layout -->
                    <div
                        v-if="showAdditionalInfo"
                        class="additional-attributes"
                    >
                        <table class="feature-table basic-attributes">
                            <tbody>
                                <tr>
                                    <th class="field-label">Region:</th>
                                    <td class="field-value">
                                        {{
                                            getFeatureValue(
                                                selectedFeature,
                                                'compartment_details.region'
                                            )
                                        }}
                                    </td>
                                </tr>
                                <tr>
                                    <th class="field-label">Operation Date:</th>
                                    <td class="field-value">
                                        {{
                                            getFeatureYear(
                                                selectedFeature,
                                                'primary_cohort.op_date'
                                            )
                                        }}
                                    </td>
                                </tr>
                                <tr>
                                    <th class="field-label">
                                        Regeneration Date:
                                    </th>
                                    <td class="field-value">
                                        {{
                                            getFeatureYear(
                                                selectedFeature,
                                                'primary_cohort.regen_date'
                                            )
                                        }}
                                    </td>
                                </tr>
                                <tr>
                                    <th class="field-label">Residual SPHA:</th>
                                    <td class="field-value">
                                        {{
                                            getFeatureValue(
                                                selectedFeature,
                                                'primary_cohort.resid_spha'
                                            )
                                        }}
                                    </td>
                                </tr>
                                <tr>
                                    <th class="field-label">Target SPHA:</th>
                                    <td class="field-value">
                                        {{
                                            getFeatureValue(
                                                selectedFeature,
                                                'primary_cohort.target_spha'
                                            )
                                        }}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Map control buttons -->
            <div class="map-controls">
                <button
                    class="control-btn maximise-btn"
                    @click="toggleMaximise"
                    :title="isMaximised ? 'Minimise map' : 'Maximise map'"
                >
                    <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                    >
                        <path
                            v-if="!isMaximised"
                            d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"
                        />
                        <path
                            v-if="isMaximised"
                            d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"
                        />
                    </svg>
                </button>

                <button
                    class="control-btn zoom-to-layer-btn"
                    @click="zoomToActiveLayer"
                    :title="getZoomToLayerTitle"
                >
                    <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                    >
                        <path
                            d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
                        />
                        <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z" />
                    </svg>
                </button>
            </div>
        </div>

        <!-- New DataTable Section -->
        <div class="datatable-container mt-4">
            <div class="card">
                <div
                    class="card-header bg-primary text-white d-flex justify-content-between align-items-center"
                >
                    <h5 class="mb-0">Search Polygons</h5>
                    <div>
                        <button
                            class="btn btn-sm btn-light me-2"
                            @click="toggleTable"
                            :title="tableVisible ? 'Hide table' : 'Show table'"
                        >
                            <i
                                class="bi"
                                :class="
                                    tableVisible ? 'bi-eye-slash' : 'bi-eye'
                                "
                            ></i>
                            {{ tableVisible ? 'Hide Table' : 'Show Table' }}
                        </button>
                        <button
                            class="btn btn-sm btn-light"
                            @click="refreshData"
                            title="Refresh data"
                        >
                            <i class="bi bi-arrow-clockwise"></i>
                            Refresh
                        </button>
                    </div>
                </div>

                <div v-if="tableVisible" class="card-body">
                    <!-- Updated Filters with Chained Objective Classification and Objective Code -->
                    <div class="row mb-3">
                        <!-- Objective Classification Filter (Parent) -->
                        <div class="col-md-2">
                            <label
                                for="filterObjClassification"
                                class="form-label"
                                >Objective Classification</label
                            >
                            <select
                                v-model="filterObjClassificationId"
                                class="form-select form-select-sm"
                                id="filterObjClassification"
                                @change="onObjectiveClassificationChange"
                            >
                                <option value="all">All Classifications</option>
                                <option
                                    v-for="classification in objectiveClassifications"
                                    :key="classification.id"
                                    :value="classification.id"
                                >
                                    {{ classification.obj_class }} -
                                    {{ classification.description }}
                                </option>
                            </select>
                        </div>

                        <!-- Objective Code Filter (Child - dependent on classification) -->
                        <div class="col-md-2">
                            <label for="filterObjCode" class="form-label"
                                >Objective Code</label
                            >
                            <div class="dropdown" ref="objectiveDropdown">
                                <button
                                    class="form-select form-select-sm text-start dropdown-toggle"
                                    type="button"
                                    @click="toggleDropdown('objective')"
                                    :class="{
                                        'text-muted': !filters.obj_code,
                                        'bg-light': isObjectiveDisabled,
                                    }"
                                    :disabled="isObjectiveDisabled"
                                >
                                    {{ getObjectiveDisplayText }}
                                </button>
                                <div
                                    class="dropdown-menu p-2"
                                    :class="{ show: dropdowns.objective }"
                                    style="
                                        width: 100%;
                                        max-height: 300px;
                                        overflow-y: auto;
                                    "
                                >
                                    <div class="mb-2">
                                        <input
                                            v-model="objectiveSearch"
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="Search objectives..."
                                            @input="filterObjectiveOptions"
                                            @click.stop
                                        />
                                    </div>
                                    <div class="dropdown-divider"></div>
                                    <button
                                        class="dropdown-item small"
                                        :class="{ active: !filters.obj_code }"
                                        @click="selectObjective('')"
                                    >
                                        All Objectives
                                    </button>
                                    <button
                                        v-for="objective in filteredObjectives"
                                        :key="objective.obj_code"
                                        class="dropdown-item small text-truncate"
                                        :class="{
                                            active:
                                                filters.obj_code ===
                                                objective.obj_code,
                                        }"
                                        @click="
                                            selectObjective(objective.obj_code)
                                        "
                                        :title="
                                            objective.obj_code +
                                            ' - ' +
                                            objective.description
                                        "
                                    >
                                        <strong>{{
                                            objective.obj_code
                                        }}</strong>
                                        - {{ objective.description }}
                                    </button>
                                    <div
                                        v-if="filteredObjectives.length === 0"
                                        class="dropdown-item text-muted small"
                                    >
                                        No objectives found
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Compartment Filter -->
                        <div class="col-md-2">
                            <label for="filterCompartment" class="form-label"
                                >Compartment</label
                            >
                            <div class="dropdown" ref="compartmentDropdown">
                                <button
                                    class="form-select form-select-sm text-start dropdown-toggle"
                                    type="button"
                                    @click="toggleDropdown('compartment')"
                                    :class="{
                                        'text-muted': !filters.compartment,
                                    }"
                                >
                                    {{ getCompartmentDisplayText }}
                                </button>
                                <div
                                    class="dropdown-menu p-2"
                                    :class="{ show: dropdowns.compartment }"
                                    style="
                                        width: 100%;
                                        max-height: 300px;
                                        overflow-y: auto;
                                    "
                                >
                                    <div class="mb-2">
                                        <input
                                            v-model="compartmentSearch"
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="Search compartments..."
                                            @input="filterCompartmentOptions"
                                            @click.stop
                                        />
                                    </div>
                                    <div class="dropdown-divider"></div>
                                    <button
                                        class="dropdown-item small"
                                        :class="{
                                            active: !filters.compartment,
                                        }"
                                        @click="selectCompartment('')"
                                    >
                                        All Compartments
                                    </button>
                                    <button
                                        v-for="compartment in filteredCompartments"
                                        :key="compartment.id"
                                        class="dropdown-item small"
                                        :class="{
                                            active:
                                                filters.compartment ===
                                                compartment.id,
                                        }"
                                        @click="
                                            selectCompartment(compartment.id)
                                        "
                                    >
                                        {{ compartment.id }}
                                    </button>
                                    <div
                                        v-if="filteredCompartments.length === 0"
                                        class="dropdown-item text-muted small"
                                    >
                                        No compartments found
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Block Filter -->
                        <div class="col-md-2">
                            <label for="filterBlock" class="form-label"
                                >Block</label
                            >
                            <div class="dropdown" ref="blockDropdown">
                                <button
                                    class="form-select form-select-sm text-start dropdown-toggle"
                                    type="button"
                                    @click="toggleDropdown('block')"
                                    :class="{ 'text-muted': !filters.block }"
                                >
                                    {{ getBlockDisplayText }}
                                </button>
                                <div
                                    class="dropdown-menu p-2"
                                    :class="{ show: dropdowns.block }"
                                    style="
                                        width: 100%;
                                        max-height: 300px;
                                        overflow-y: auto;
                                    "
                                >
                                    <div class="mb-2">
                                        <input
                                            v-model="blockSearch"
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="Search blocks..."
                                            @input="filterBlockOptions"
                                            @click.stop
                                        />
                                    </div>
                                    <div class="dropdown-divider"></div>
                                    <button
                                        class="dropdown-item small"
                                        :class="{ active: !filters.block }"
                                        @click="selectBlock('')"
                                    >
                                        All Blocks
                                    </button>
                                    <button
                                        v-for="block in filteredBlocks"
                                        :key="block"
                                        class="dropdown-item small"
                                        :class="{
                                            active: filters.block === block,
                                        }"
                                        @click="selectBlock(block)"
                                    >
                                        {{ block }}
                                    </button>
                                    <div
                                        v-if="filteredBlocks.length === 0"
                                        class="dropdown-item text-muted small"
                                    >
                                        No blocks found
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- District Filter -->
                        <div class="col-md-2">
                            <label for="filterDistrict" class="form-label"
                                >District</label
                            >
                            <div class="dropdown" ref="districtDropdown">
                                <button
                                    class="form-select form-select-sm text-start dropdown-toggle"
                                    type="button"
                                    @click="toggleDropdown('district')"
                                    :class="{ 'text-muted': !filters.district }"
                                >
                                    {{ getDistrictDisplayText }}
                                </button>
                                <div
                                    class="dropdown-menu p-2"
                                    :class="{ show: dropdowns.district }"
                                    style="
                                        width: 100%;
                                        max-height: 300px;
                                        overflow-y: auto;
                                    "
                                >
                                    <div class="mb-2">
                                        <input
                                            v-model="districtSearch"
                                            type="text"
                                            class="form-control form-control-sm"
                                            placeholder="Search districts..."
                                            @input="filterDistrictOptions"
                                            @click.stop
                                        />
                                    </div>
                                    <div class="dropdown-divider"></div>
                                    <button
                                        class="dropdown-item small"
                                        :class="{ active: !filters.district }"
                                        @click="selectDistrict('')"
                                    >
                                        All Districts
                                    </button>
                                    <button
                                        v-for="district in filteredDistricts"
                                        :key="district"
                                        class="dropdown-item small"
                                        :class="{
                                            active:
                                                filters.district === district,
                                        }"
                                        @click="selectDistrict(district)"
                                    >
                                        {{ district }}
                                    </button>
                                    <div
                                        v-if="filteredDistricts.length === 0"
                                        class="dropdown-item text-muted small"
                                    >
                                        No districts found
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Rest of the filters (FEA ID, Treatment Status, Date Filters) -->
                    <div class="row mb-3">
                        <!-- FEA ID Filter -->
                        <div class="col-md-2">
                            <label for="filterZfeaId" class="form-label"
                                >FEA ID</label
                            >
                            <input
                                v-model="filters.zfea_id"
                                type="text"
                                class="form-control form-control-sm"
                                id="filterZfeaId"
                                placeholder="Filter by FEA ID..."
                            />
                        </div>

                        <!-- Treatment Status Filter -->
                        <div class="col-md-2">
                            <label
                                for="filterTreatmentStatus"
                                class="form-label"
                                >Treatment Status</label
                            >
                            <select
                                v-model="filters.treatment_status"
                                class="form-select form-select-sm"
                                id="filterTreatmentStatus"
                            >
                                <option value="">All Status</option>
                                <option value="P">Planned</option>
                                <option value="D">Completed</option>
                                <option value="C">Cancelled</option>
                                <option value="F">Failed</option>
                                <option value="W">Written Off</option>
                                <option value="X">Not Required</option>
                            </select>
                        </div>

                        <div class="col-md-2"></div>

                        <!-- Date Filters -->
                        <div class="col-md-2">
                            <label for="filterCreatedFrom" class="form-label"
                                >Created From</label
                            >
                            <input
                                v-model="filters.created_from"
                                type="date"
                                class="form-control form-control-sm"
                                id="filterCreatedFrom"
                            />
                        </div>
                        <div class="col-md-2">
                            <label for="filterCreatedTo" class="form-label"
                                >Created To</label
                            >
                            <input
                                v-model="filters.created_to"
                                type="date"
                                class="form-control form-control-sm"
                                id="filterCreatedTo"
                            />
                        </div>
                        <div class="col-md-2">
                            <div class="form-group">
                                <label
                                    for="post_2024_only"
                                    class="form-check-label"
                                >
                                    <br />
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

                    <!-- DataTable -->
                    <div class="row">
                        <div class="col-12">
                            <datatable
                                :id="datatable_id"
                                ref="polygon_datatable"
                                :dt-options="dtOptions"
                                :dt-headers="dtHeaders"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import GeoJSON from 'ol/format/GeoJSON';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { Style, Fill, Stroke } from 'ol/style';
import { fromLonLat } from 'ol/proj';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import { Select } from 'ol/interaction';
import { click } from 'ol/events/condition';
import datatable from '@/utils/vue/datatable.vue';
import { api_endpoints } from '@/utils/hooks';
import { v4 as uuid } from 'uuid';
import permissionsMixin from '@/mixins/permissions';

export default {
    name: 'MapComponent',
    mixins: [permissionsMixin],
    components: {
        datatable,
    },
    props: {
        featureCollection: {
            type: Object,
            default: null,
        },
        displayFieldsConfig: {
            type: Array,
            default: () => [
                { key: 'name', label: 'Name' },
                { key: 'Block', label: 'Block' },
                { key: 'Compno', label: 'Comp No' },
            ],
        },
        additionalFieldsConfig: {
            type: Array,
            default: () => [
                { key: 'Region', label: 'Region' },
                { key: 'fea_id', label: 'Feature ID' },
                { key: 'area', label: 'Area' },
                { key: 'status', label: 'Status' },
                { key: 'type', label: 'Type' },
                { key: 'owner', label: 'Owner' },
            ],
        },
        context: {
            type: Object,
            default: null,
        },
        readOnly: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['refresh-from-response'],
    data() {
        return {
            map: null,
            layer1: null,
            layer1Visible: true,
            showLayerControl: false,
            selectedFeature: null,
            selectInteraction: null,
            showAdditionalInfo: false,
            isMaximised: false,
            geometryCollections: [],
            selectedGeometryIndex: null,
            highlightStyle: new Style({
                fill: new Fill({
                    color: 'rgba(255, 255, 0, 0.6)',
                }),
                stroke: new Stroke({
                    color: 'rgba(255, 255, 0, 1)',
                    width: 3,
                }),
            }),

            // Lookup data
            lookupData: {
                objectives_with_classification: null,
                compartments: [],
                blocks: [],
                districts: [],
            },

            // Filter state
            filterObjClassificationId: 'all',
            filterPost2024Only: true,

            // Search terms for filterable selects
            objectiveSearch: '',
            compartmentSearch: '',
            blockSearch: '',
            districtSearch: '',

            // Filtered options for display
            filteredObjectives: [],
            filteredCompartments: [],
            filteredBlocks: [],
            filteredDistricts: [],

            // Dropdown state
            dropdowns: {
                objective: false,
                compartment: false,
                block: false,
                district: false,
            },

            // DataTable related data
            datatable_id: 'polygon-map-table-' + uuid(),
            tableVisible: true,
            filters: {
                obj_code: '',
                compartment: '',
                block: '',
                district: '',
                zfea_id: '',
                treatment_status: '',
                created_from: '',
                created_to: '',
            },
            filteredPolygons: [],
            mapHeight: 600, // Default map height

            // Debounced refresh function
            debouncedRefreshData: null,
        };
    },
    computed: {
        displayFields() {
            return this.displayFieldsConfig || [];
        },
        additionalFields() {
            return this.additionalFieldsConfig || [];
        },
        getZoomToLayerTitle() {
            return 'Zoom to visible features';
        },

        // Objective classification computed properties
        objectiveClassifications() {
            return (
                this.lookupData.objectives_with_classification
                    ?.classifications || []
            );
        },

        allObjectives() {
            return (
                this.lookupData.objectives_with_classification?.objectives || []
            );
        },

        isObjectiveDisabled() {
            return (
                !this.lookupData.objectives_with_classification
                    ?.classification_table_exists ||
                (this.filterObjClassificationId !== 'all' &&
                    this.objectiveClassifications.length === 0)
            );
        },

        getObjectiveDisplayText() {
            if (this.isObjectiveDisabled) {
                return 'Select classification first';
            }
            if (!this.filters.obj_code) return 'All Objectives';
            const objective = this.allObjectives.find(
                (obj) => obj.obj_code === this.filters.obj_code
            );
            return objective
                ? `${objective.obj_code} - ${objective.description}`
                : this.filters.obj_code;
        },

        getCompartmentDisplayText() {
            return this.filters.compartment || 'All Compartments';
        },
        getBlockDisplayText() {
            return this.filters.block || 'All Blocks';
        },
        getDistrictDisplayText() {
            return this.filters.district || 'All Districts';
        },
        popupStyle() {
            // Calculate max height based on map container height
            const maxHeight = this.mapHeight * 0.8; // 80% of map height
            return {
                'max-height': `${maxHeight}px`,
                'overflow-y': 'auto',
            };
        },
        dtHeaders() {
            return [
                'ID',
                'Polygon Name',
                'Compartment',
                'Area (ha)',
                'FEA ID',
                'Objective Code',
                'Species',
                'Target BA',
                'Residual BA',
                'Treatment Status',
                'Created Date',
                'Actions',
            ];
        },
        dtOptions() {
            let vm = this;

            return {
                autoWidth: false,
                responsive: true,
                serverSide: true,
                searching: false, // We use our own filters
                processing: true,
                ajax: {
                    url: api_endpoints.polygon_search,
                    dataSrc: 'data',
                    data: function (d) {
                        // Add our custom filters to the DataTables request
                        d.obj_code = vm.filters.obj_code;
                        d.compartment = vm.filters.compartment;
                        d.block = vm.filters.block;
                        d.district = vm.filters.district;
                        d.zfea_id = vm.filters.zfea_id;
                        d.treatment_status = vm.filters.treatment_status;
                        d.created_from = vm.filters.created_from;
                        d.created_to = vm.filters.created_to;

                        // Only search if at least one filter is provided
                        const hasFilters = Object.values(vm.filters).some(
                            (val) => val !== ''
                        );
                        if (!hasFilters) {
                            // Return empty result if no filters
                            d.return_empty = true;
                        }
                    },
                },
                columns: [
                    {
                        data: 'polygon_id',
                        name: 'polygon_id',
                        visible: false,
                        orderable: true,
                    },
                    {
                        data: 'name',
                        name: 'name',
                        orderable: true,
                        render: function (data, type, row) {
                            return data || 'N/A';
                        },
                    },
                    {
                        data: 'compartment_details.compartment',
                        name: 'compartment__compartment',
                        orderable: true,
                        render: function (data, type, row) {
                            return data || 'N/A';
                        },
                    },
                    {
                        data: 'area_ha',
                        name: 'area_ha',
                        orderable: true,
                        render: function (data, type, row) {
                            return data ? data.toFixed(2) : 'N/A';
                        },
                    },
                    {
                        data: 'zfea_id',
                        name: 'zfea_id',
                        orderable: true,
                        render: function (data, type, row) {
                            return data || 'N/A';
                        },
                    },
                    {
                        data: 'obj_codes',
                        name: 'assignchttoply__cohort__obj_code',
                        orderable: true,
                        render: function (data, type, row) {
                            return data || 'N/A';
                        },
                    },
                    {
                        data: 'species_list',
                        name: 'assignchttoply__cohort__species',
                        orderable: true,
                        render: function (data, type, row) {
                            return data || 'N/A';
                        },
                    },
                    {
                        data: 'primary_cohort.target_ba_m2ha',
                        name: 'assignchttoply__cohort__target_ba_m2ha',
                        orderable: true,
                        render: function (data, type, row) {
                            return data ? data.toFixed(2) : 'N/A';
                        },
                    },
                    {
                        data: 'primary_cohort.resid_ba_m2ha',
                        name: 'assignchttoply__cohort__resid_ba_m2ha',
                        orderable: true,
                        render: function (data, type, row) {
                            return data ? data.toFixed(2) : 'N/A';
                        },
                    },
                    {
                        data: 'treatment_statuses',
                        name: 'assignchttoply__cohort__treatment__status',
                        orderable: true,
                        render: function (data, type, row) {
                            return data || 'N/A';
                        },
                    },
                    {
                        data: 'created_on_formatted',
                        name: 'created_on',
                        orderable: true,
                        render: function (data, type, row) {
                            return data || 'N/A';
                        },
                    },
                    {
                        data: 'polygon_id',
                        orderable: false,
                        searchable: false,
                        className: 'action-column',
                        render: function (data, type, row) {
                            const cohortId = row.primary_cohort
                                ? row.primary_cohort.cohort_id
                                : null;
                            const isReadOnly = vm.readOnly || vm.isReadOnlyUser;

                            return `
                ${
                    cohortId && !isReadOnly
                        ? `
                <a href="proposal/-1/cohorts/${cohortId}/polygon/${data}" class="btn btn-sm btn-outline-primary me-1" title="Edit Cohort">
                     <i class="bi bi-pencil"></i>
                     Edit
                </a>
                `
                        : cohortId
                          ? `
                <a href="/internal/cohorts/${cohortId}" class="btn btn-sm btn-outline-info me-1" title="View Cohort">
                     <i class="bi bi-eye"></i>
                     View
                </a>
                `
                          : ''
                }
                <button class="btn btn-sm btn-outline-primary me-1 view-polygon-btn" data-polygon-id="${data}" title="View Details">
                <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-info zoom-polygon-btn" data-polygon-id="${data}" title="Zoom to Polygon">
                <i class="bi bi-zoom-in"></i>
                </button>
            `;
                        },
                    },
                ],
                dom:
                    "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
                language: {
                    processing:
                        '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading...</span>',
                },
                drawCallback: function (settings) {
                    // Store the filtered data and update map
                    vm.filteredPolygons = settings.json.data || [];
                    vm.updateMapWithFilteredData();

                    // Re-attach event listeners
                    vm.attachEventListeners();
                },
            };
        },
    },
    watch: {
        featureCollection: {
            handler(newGeoJSON) {
                this.updateLayer1(newGeoJSON);
            },
            deep: true,
        },
        // Watch all filters and refresh data when they change
        filters: {
            handler() {
                if (this.debouncedRefreshData) {
                    this.debouncedRefreshData();
                }
            },
            deep: true,
        },
        filterObjClassificationId: {
            handler() {
                this.onObjectiveClassificationChange();
            },
        },
        isMaximised() {
            // Update map height when maximised state changes
            this.$nextTick(() => {
                this.updateMapHeight();
            });
        },
    },
    async mounted() {
        this.fetchCurrentUser();

        this.$nextTick(() => {
            this.initializeMap();
        });

        // Setup debounced refresh
        this.debouncedRefreshData = this.debounce(this.refreshData, 500);

        // Load lookup data
        await this.loadLookupData();

        // Add click outside listener to close dropdowns
        document.addEventListener('click', this.handleClickOutside);

        // Update map height after mount
        this.$nextTick(() => {
            this.updateMapHeight();
        });
    },
    beforeUnmount() {
        if (this.map) {
            this.map.setTarget(null);
        }
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('keydown', this.handleEscape);
        document.removeEventListener('click', this.handleClickOutside);
    },
    methods: {
        initializeMap() {
            // Create vector sources and layers
            const layer1Source = new VectorSource();

            // Style for layer 1
            const layer1Style = new Style({
                fill: new Fill({
                    color: 'rgba(255, 0, 0, 0.3)',
                }),
                stroke: new Stroke({
                    color: 'rgba(255, 0, 0, 0.8)',
                    width: 2,
                }),
            });

            // Create layers
            this.layer1 = new VectorLayer({
                source: layer1Source,
                style: layer1Style,
                visible: this.layer1Visible,
            });

            // Base layer (OSM)
            const baseLayer = new TileLayer({
                source: new OSM(),
            });

            // Initialize the map
            this.map = new Map({
                target: this.$refs.mapContainer,
                layers: [baseLayer, this.layer1],
                view: new View({
                    projection: 'EPSG:4326',
                    center: fromLonLat([121.5, -24.5], 'EPSG:4326'),
                    zoom: 6,
                }),
            });

            // Add select interaction
            this.setupSelectInteraction();

            // Load initial data if available
            if (this.featureCollection) {
                this.updateLayer1(this.featureCollection);
            }

            window.addEventListener('resize', this.handleResize);
            document.addEventListener('keydown', this.handleEscape);
        },

        updateMapHeight() {
            // Get the actual height of the map container
            if (this.$refs.mapContainer) {
                this.mapHeight = this.$refs.mapContainer.clientHeight;
            }
        },

        setupSelectInteraction() {
            if (this.selectInteraction) {
                this.map.removeInteraction(this.selectInteraction);
            }

            this.selectInteraction = new Select({
                condition: click,
                layers: [this.layer1],
                style: this.highlightStyle,
                multi: false,
            });

            this.selectInteraction.on('select', (event) => {
                if (event.selected.length > 0) {
                    this.selectedFeature = event.selected[0];
                    this.showAdditionalInfo = false;
                } else {
                    this.selectedFeature = null;
                    this.showAdditionalInfo = false;
                }
            });

            this.map.addInteraction(this.selectInteraction);
        },

        getFeatureValue(feature, fieldKey) {
            if (!feature) return 'N/A';

            // Handle nested properties with dot notation
            if (fieldKey.includes('.')) {
                const keys = fieldKey.split('.');
                let value = feature.get(keys[0]);

                for (
                    let i = 1;
                    i < keys.length && value !== undefined && value !== null;
                    i++
                ) {
                    value = value[keys[i]];
                }

                return value !== undefined && value !== null ? value : 'N/A';
            }

            // Try different property access methods
            let value = feature.get(fieldKey);

            // If not found, try properties object
            if (value === undefined || value === null) {
                const properties = feature.getProperties();
                value = properties[fieldKey];
            }

            // If still not found, try the original properties
            if (value === undefined || value === null) {
                const originalProperties = feature.get('properties');
                value = originalProperties
                    ? originalProperties[fieldKey]
                    : undefined;
            }

            // Format numbers to 2 decimal places if they are numeric
            if (typeof value === 'number') {
                return value.toFixed(2);
            }

            return value !== undefined && value !== null ? value : 'N/A';
        },

        getFeatureYear(feature, fieldKey) {
            const value = this.getFeatureValue(feature, fieldKey);
            if (value === 'N/A') return 'N/A';

            try {
                // Try to parse the date and extract year
                const date = new Date(value);
                if (!isNaN(date.getTime())) {
                    return date.getFullYear().toString();
                }
            } catch (e) {
                console.warn('Could not parse date:', value);
            }

            return value;
        },

        closeFeaturePopup() {
            this.selectedFeature = null;
            this.showAdditionalInfo = false;
            if (this.selectInteraction) {
                this.selectInteraction.getFeatures().clear();
            }
        },

        toggleMaximise() {
            this.isMaximised = !this.isMaximised;
            setTimeout(() => {
                this.map.updateSize();
                this.updateMapHeight();
            }, 100);
        },

        handleEscape(event) {
            if (event.key === 'Escape' && this.isMaximised) {
                this.isMaximised = false;
                setTimeout(() => {
                    this.map.updateSize();
                    this.updateMapHeight();
                }, 100);
            }
        },

        handleResize() {
            if (this.map) {
                setTimeout(() => {
                    this.map.updateSize();
                    this.updateMapHeight();
                }, 100);
            }
        },

        updateLayer1(geoJSON) {
            if (!this.layer1 || !geoJSON) return;

            const format = new GeoJSON();
            const features = format.readFeatures(geoJSON, {
                featureProjection: 'EPSG:4326',
                dataProjection: 'EPSG:4326',
            });

            this.layer1.getSource().clear();
            this.layer1.getSource().addFeatures(features);

            if (features.length > 0) {
                this.zoomToLayer('layer1');
            }
        },

        zoomToActiveLayer() {
            this.zoomToLayer('layer1');
        },

        zoomToLayer(layerName) {
            let layer;
            layer = this.layer1;

            if (!layer || !layer.getVisible()) return;

            const source = layer.getSource();
            const features = source.getFeatures();

            if (features.length > 0) {
                const extent = source.getExtent();
                this.map.getView().fit(extent, {
                    padding: [20, 20, 20, 20],
                    duration: 1000,
                });
            }
        },

        refreshFromResponse() {
            this.$emit('refresh-from-response');
        },

        // Handle objective classification change
        onObjectiveClassificationChange() {
            // Clear selected objective when classification changes
            this.filters.obj_code = '';
            this.objectiveSearch = '';
            this.dropdowns.objective = false;

            // Update filtered objectives based on new classification
            this.updateFilteredObjectives();

            // Refresh the data table
            this.refreshData();
        },

        // Update filtered objectives based on selected classification
        updateFilteredObjectives() {
            if (!this.allObjectives.length) {
                this.filteredObjectives = [];
                return;
            }

            if (this.filterObjClassificationId === 'all') {
                // Show all objectives
                this.filteredObjectives = [...this.allObjectives];
            } else {
                // Filter objectives by selected classification
                this.filteredObjectives = this.allObjectives.filter(
                    (objective) =>
                        objective.classification &&
                        objective.classification.id ===
                            parseInt(this.filterObjClassificationId)
                );
            }
        },

        // Lookup data methods
        async loadLookupData() {
            try {
                const response = await fetch(api_endpoints.combined_lookups, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                this.lookupData = data;

                // Initialize filtered objectives
                this.updateFilteredObjectives();

                // Initialize other filtered options
                this.filteredCompartments = this.lookupData.compartments || [];
                this.filteredBlocks = this.lookupData.blocks || [];
                this.filteredDistricts = this.lookupData.districts || [];
            } catch (error) {
                console.error('Error loading lookup data:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Load Failed',
                    text: 'Failed to load filter options. Please try again.',
                    confirmButtonText: 'OK',
                });
            }
        },

        // Dropdown management methods
        toggleDropdown(dropdownName) {
            // Close all other dropdowns first
            Object.keys(this.dropdowns).forEach((key) => {
                if (key !== dropdownName) {
                    this.dropdowns[key] = false;
                }
            });

            // Toggle the current dropdown
            this.dropdowns[dropdownName] = !this.dropdowns[dropdownName];
        },

        closeAllDropdowns() {
            Object.keys(this.dropdowns).forEach((key) => {
                this.dropdowns[key] = false;
            });
        },

        handleClickOutside(event) {
            // Check if click is outside any dropdown
            const objectiveDropdown = this.$refs.objectiveDropdown;
            const compartmentDropdown = this.$refs.compartmentDropdown;
            const blockDropdown = this.$refs.blockDropdown;
            const districtDropdown = this.$refs.districtDropdown;

            if (
                objectiveDropdown &&
                !objectiveDropdown.contains(event.target) &&
                compartmentDropdown &&
                !compartmentDropdown.contains(event.target) &&
                blockDropdown &&
                !blockDropdown.contains(event.target) &&
                districtDropdown &&
                !districtDropdown.contains(event.target)
            ) {
                this.closeAllDropdowns();
            }
        },

        // Selection methods
        selectObjective(value) {
            this.filters.obj_code = value;
            this.objectiveSearch = ''; // Clear search when selection is made
            this.filterObjectiveOptions(); // Reset filtered list
            this.closeAllDropdowns(); // Close dropdown after selection
        },

        selectCompartment(value) {
            this.filters.compartment = value;
            this.compartmentSearch = '';
            this.filterCompartmentOptions();
            this.closeAllDropdowns();
        },

        selectBlock(value) {
            this.filters.block = value;
            this.blockSearch = '';
            this.filterBlockOptions();
            this.closeAllDropdowns();
        },

        selectDistrict(value) {
            this.filters.district = value;
            this.districtSearch = '';
            this.filterDistrictOptions();
            this.closeAllDropdowns();
        },

        // Filtering methods
        filterObjectiveOptions() {
            // Start with the current filtered objectives (already filtered by classification)
            let filtered = this.filteredObjectives;

            if (this.objectiveSearch) {
                const searchTerm = this.objectiveSearch.toLowerCase();
                filtered = filtered.filter(
                    (obj) =>
                        (obj.obj_code &&
                            obj.obj_code.toLowerCase().includes(searchTerm)) ||
                        (obj.description &&
                            obj.description.toLowerCase().includes(searchTerm))
                );
            }

            // Update the display list
            this.filteredObjectives = filtered;
        },

        filterCompartmentOptions() {
            if (!this.compartmentSearch) {
                this.filteredCompartments = this.lookupData.compartments || [];
                return;
            }

            const searchTerm = this.compartmentSearch.toLowerCase();
            this.filteredCompartments = (
                this.lookupData.compartments || []
            ).filter(
                (comp) => comp.id && comp.id.toLowerCase().includes(searchTerm)
            );
        },

        filterBlockOptions() {
            if (!this.blockSearch) {
                this.filteredBlocks = this.lookupData.blocks || [];
                return;
            }

            const searchTerm = this.blockSearch.toLowerCase();
            this.filteredBlocks = (this.lookupData.blocks || []).filter(
                (block) => block && block.toLowerCase().includes(searchTerm)
            );
        },

        filterDistrictOptions() {
            if (!this.districtSearch) {
                this.filteredDistricts = this.lookupData.districts || [];
                return;
            }

            const searchTerm = this.districtSearch.toLowerCase();
            this.filteredDistricts = (this.lookupData.districts || []).filter(
                (district) =>
                    district && district.toLowerCase().includes(searchTerm)
            );
        },

        // DataTable methods
        toggleTable() {
            this.tableVisible = !this.tableVisible;
            if (this.tableVisible) {
                this.$nextTick(() => {
                    this.refreshData();
                });
            }
        },

        async refreshData() {
            try {
                if (
                    this.$refs.polygon_datatable &&
                    this.$refs.polygon_datatable.vmDataTable
                ) {
                    await this.$refs.polygon_datatable.vmDataTable.ajax.reload();
                }
            } catch (error) {
                console.error('Error refreshing data:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Refresh Failed',
                    text: 'Failed to refresh table data. Please try again.',
                    confirmButtonText: 'OK',
                });
            }
        },

        updateMapWithFilteredData() {
            if (!this.layer1) return;

            // Clear existing features
            this.layer1.getSource().clear();

            // Create GeoJSON from filtered polygons
            const features = this.filteredPolygons
                .map((polygon) => {
                    if (polygon.geom) {
                        const format = new GeoJSON();
                        const feature = format.readFeature(polygon.geom, {
                            featureProjection: 'EPSG:4326',
                            dataProjection: 'EPSG:4326',
                        });

                        // Add polygon data as properties
                        feature.setProperties({
                            ...polygon,
                            id: polygon.polygon_id,
                            polygon_id: polygon.polygon_id,
                            name: polygon.name,
                        });

                        return feature;
                    }
                    return null;
                })
                .filter((feature) => feature !== null);

            // Add features to map
            this.layer1.getSource().addFeatures(features);

            // Zoom to show all features if there are any
            if (features.length > 0) {
                const extent = this.layer1.getSource().getExtent();
                this.map.getView().fit(extent, {
                    padding: [50, 50, 50, 50],
                    duration: 1000,
                });
            }
        },

        // Helper method for debouncing
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Attach event listeners to action buttons
        attachEventListeners() {
            const vm = this;

            // Remove existing listeners to prevent duplicates
            $(this.$el).off('click', '.view-polygon-btn');
            $(this.$el).off('click', '.zoom-polygon-btn');

            // Attach new listeners
            $(this.$el).on('click', '.view-polygon-btn', function () {
                const polygonId = $(this).data('polygon-id');
                vm.handlePolygonSelection(polygonId);
            });

            $(this.$el).on('click', '.zoom-polygon-btn', function () {
                const polygonId = $(this).data('polygon-id');
                vm.handleZoomToPolygon(polygonId);
            });
        },

        handlePolygonSelection(polygonId) {
            // Find and highlight the polygon
            this.highlightPolygonInLayer(polygonId);
        },

        handleZoomToPolygon(polygonId) {
            // Find and zoom to the polygon
            this.zoomToPolygonInLayer(polygonId);
        },

        highlightPolygonInLayer(polygonId) {
            if (!this.map || !polygonId) return;

            const source = this.layer1.getSource();
            const features = source.getFeatures();

            const foundFeature = this.findFeatureById(features, polygonId);

            if (foundFeature) {
                // Highlight the found feature
                this.selectInteraction.getFeatures().clear();
                this.selectInteraction.getFeatures().push(foundFeature);

                // Show feature details in popup
                this.selectedFeature = foundFeature;
                this.showAdditionalInfo = false;

                console.log('Found and highlighted polygon:', polygonId);
            } else {
                console.warn('Polygon with ID', polygonId, 'not found');
            }
        },

        zoomToPolygonInLayer(polygonId) {
            if (!this.map || !polygonId) return;

            const source = this.layer1.getSource();
            const features = source.getFeatures();

            const foundFeature = this.findFeatureById(features, polygonId);

            if (foundFeature) {
                // Highlight the found feature
                this.selectInteraction.getFeatures().clear();
                this.selectInteraction.getFeatures().push(foundFeature);

                // Show feature details in popup
                this.selectedFeature = foundFeature;
                this.showAdditionalInfo = false;

                // Zoom to the selected feature
                this.zoomToFeature(foundFeature);

                console.log('Found and zoomed to polygon:', polygonId);
            } else {
                console.warn('Polygon with ID', polygonId, 'not found');
            }
        },

        findFeatureById(features, polygonId) {
            return features.find((feature) => {
                const featureId =
                    feature.get('polygon_id') ||
                    feature.get('id') ||
                    (feature.get('properties') &&
                        feature.get('properties').polygon_id);

                return (
                    featureId && featureId.toString() === polygonId.toString()
                );
            });
        },

        zoomToFeature(feature) {
            if (!feature || !this.map) return;

            const geometry = feature.getGeometry();
            if (geometry) {
                const extent = geometry.getExtent();
                this.map.getView().fit(extent, {
                    padding: [50, 50, 50, 50],
                    duration: 1000,
                    maxZoom: 15,
                });
            }
        },
    },
};
</script>

<style scoped>
.map-container {
    position: relative;
    width: 100%;
    height: 600px;
    min-height: 400px;
    transition: all 0.3s ease;
}

.map-container.maximised {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 10000;
    background: white;
}

.map {
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
}

.map-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    z-index: 1000;
}

.control-btn {
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #333;
    width: 36px;
    height: 36px;
    transition: all 0.2s ease;
}

.control-btn:hover {
    background: #f5f5f5;
    transform: scale(1.05);
}

/* Compact Feature Popup Styles */
.feature-popup {
    position: absolute;
    top: 50px;
    right: 10px;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    min-width: 260px;
    max-width: 320px;
    /* max-height and overflow-y are now set dynamically */
}

.popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    border-bottom: 1px solid #eee;
    padding-bottom: 6px;
}

.popup-header h3 {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
}

.close-btn {
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    color: #666;
    padding: 2px;
    line-height: 1;
}

.close-btn:hover {
    color: #333;
}

.feature-content {
    font-size: 12px;
}

.feature-table.basic-attributes {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
}

.feature-table.basic-attributes th,
.feature-table.basic-attributes td {
    padding: 3px 6px;
    text-align: left;
    border-bottom: 1px solid #f0f0f0;
    line-height: 1.2;
}

.feature-table.basic-attributes th {
    font-weight: 600;
    color: #555;
    white-space: nowrap;
    padding-right: 10px;
    width: 40%;
    font-size: 11px;
}

.feature-table.basic-attributes td {
    color: #333;
    word-break: break-word;
    font-size: 11px;
}

.feature-table.basic-attributes tr:last-child th,
.feature-table.basic-attributes tr:last-child td {
    border-bottom: none;
}

.info-toggle-section {
    margin: 10px 0;
    padding: 8px 0;
    border-top: 1px solid #eee;
    border-bottom: 1px solid #eee;
}

.info-toggle-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: none;
    border: none;
    color: #007bff;
    cursor: pointer;
    padding: 3px 6px;
    border-radius: 3px;
    transition: all 0.2s;
    font-size: 11px;
    width: 100%;
    justify-content: center;
}

.info-toggle-btn:hover {
    background-color: #f8f9fa;
}

.toggle-text {
    font-weight: 500;
}

.additional-attributes {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #eee;
}

/* Custom scrollbar for the popup */
.feature-popup::-webkit-scrollbar {
    width: 6px;
}

.feature-popup::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.feature-popup::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.feature-popup::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

.datatable-container {
    margin-top: 20px;
}

:deep(.action-column) {
    white-space: nowrap;
    width: 150px;
}

:deep(.btn-sm) {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
}

:deep(.dataTables_wrapper) {
    font-size: 0.875rem;
}

:deep(.table) {
    margin-bottom: 0;
}

/* Additional styles for the filter dropdowns */
.dropdown-toggle::after {
    float: right;
    margin-top: 0.5rem;
}

.dropdown-menu {
    min-width: 100%;
}

.dropdown-item.active {
    background-color: #0d6efd;
    color: white;
}

.dropdown-item:hover {
    background-color: #f8f9fa;
    color: #000;
}

.dropdown-item.active:hover {
    background-color: #0b5ed7;
    color: white;
}

/* Ensure the search inputs are properly styled */
.form-control-sm {
    font-size: 0.875rem;
}

/* Style for truncated text in dropdown items */
.text-truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Custom dropdown show class */
.dropdown-menu.show {
    display: block;
}

button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
</style>
