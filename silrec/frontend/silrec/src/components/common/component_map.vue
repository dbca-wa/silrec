<template>
  <div>
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/common/component_map.vue</div>
    <div class="map-container" :class="{ 'maximised': isMaximised }">
        <div ref="mapContainer" class="map"></div>

        <!-- Layer control popup -->
        <div v-if="showLayerControl" class="layer-control-popup">
        <div class="popup-header">
            <h3>Layers</h3>
            <button @click="showLayerControl = false" class="close-btn">×</button>
        </div>
        <div class="layer-list">
            <div class="layer-item">
            <label>
                <input 
                type="checkbox" 
                v-model="layer1Visible" 
                @change="toggleLayer('layer1')"
                >
                Shapefile Layer
            </label>
            </div>
            <div class="layer-item" v-if="hasLayer2">
            <label>
                <input 
                type="checkbox" 
                v-model="layer2Visible" 
                @change="toggleLayer('layer2')"
                >
                Pre-processed (current) Layer
            </label>
            </div>
            <div class="layer-item" v-if="hasLayer3">
            <label>
                <input 
                type="checkbox" 
                v-model="layer3Visible" 
                @change="toggleLayer('layer3')"
                >
                Processed
            </label>
            </div>
            <!-- New Layer 4 with nested radio buttons -->
            <div class="layer-item" v-if="hasLayer4">
            <label>
                <input 
                type="checkbox" 
                v-model="layer4Visible" 
                @change="toggleLayer('layer4')"
                >
                Geometry Collections
            </label>
            
            <!-- Nested radio buttons for geometry collections -->
                <div v-if="layer4Visible" class="nested-radio-group">
                <div 
                    v-for="(geometry, index) in geometryCollections" 
                    :key="index"
                    class="radio-item"
                >
                    <div class="geometry-item-header">
                        <div class="radio-label">
                            <input 
                            type="radio" 
                            :value="index"
                            v-model="selectedGeometryIndex"
                            @change="toggleGeometryCollection(index)"
                            >
                            <span>Polygon {{ index + 1 }} ({{ index + 1 }}st iter)</span>
                        </div>
                        <button 
                            v-if="geometry.cht_init || geometry.cht_new"
                            @click="openChtDialog(index)"
                            class="cht-link-btn"
                            title="View Cohort Data"
                        >
                            <i class="bi bi-table"></i>
                        </button>
                    </div>
                </div>
                </div>
            </div>
        </div>
        </div>

        <!-- Feature info popup -->
        <div v-if="selectedFeature" class="feature-popup">
        <div class="popup-header">
            <h3>Feature Details</h3>
            <button @click="closeFeaturePopup" class="close-btn">×</button>
        </div>
        <div class="feature-content">
            <!-- Basic attributes table -->
            <table class="feature-table basic-attributes compact">
            <tbody>
                <tr v-for="field in displayFields" :key="field.key">
                <th class="field-label">{{ field.label }}:</th>
                <td class="field-value">{{ getFeatureValue(selectedFeature, field.key) }}</td>
                </tr>
            </tbody>
            </table>
            
            <!-- Information icon toggle -->
            <div class="info-toggle-section compact">
            <button 
                class="info-toggle-btn"
                @click="showAdditionalInfo = !showAdditionalInfo"
                :title="showAdditionalInfo ? 'Hide additional details' : 'Show additional details'"
            >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                </svg>
                <span class="toggle-text">
                {{ showAdditionalInfo ? 'Less details' : 'More details...' }}
                </span>
            </button>
            </div>

            <!-- Additional attributes in multi-column layout -->
            <div v-if="showAdditionalInfo && additionalFields.length > 0" class="additional-attributes compact">
            <h4 class="additional-title">Additional Information</h4>
            <div class="attributes-grid">
                <div 
                v-for="field in additionalFields" 
                :key="field.key"
                class="attribute-item"
                >
                <span class="attribute-label">{{ field.label }}:</span>
                <span class="attribute-value">{{ getFeatureValue(selectedFeature, field.key) }}</span>
                </div>
            </div>
            </div>
        </div>
        </div>

        <!-- CHT Data Dialog -->
        <div v-if="showChtDialog && currentChtData" class="cht-dialog-overlay" @click="showChtDialog = false">
        <div class="cht-dialog" @click.stop>
            <div class="popup-header">
            <h3>Cohort Data - Polygon {{ selectedGeometryIndex + 1 }}</h3>
            <div class="header-actions">
                <button @click="exportChtToExcel" class="export-excel-btn" title="Export to Excel">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 4px;">
                    <path d="M19.5 3.5L18 2l-1.5 1.5L15 2l-1.5 1.5L12 2l-1.5 1.5L9 2 7.5 3.5 6 2v14h13.5V2zM15 17H9v-1.5h6zm0-3.5H9V12h6zm0-3.5H9V8.5h6z"/>
                </svg>
                Export Excel
                </button>
                <button @click="showChtDialog = false" class="close-btn">×</button>
            </div>
            </div>

            <div class="cht-content">
            <!-- CHT Init Table -->
            <div class="cht-table-section" v-if="currentChtData.cht_init">
                <h4>Initial  - 'Polygon - AC2P - Cohort'</h4>
                <div class="table-container">
                <table class="cht-table">
                    <thead>
                    <tr>
                        <th v-for="key in getChtInitKeys(currentChtData.cht_init)" :key="'init-' + key">
                        {{ key }}
                        </th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr v-for="(row, index) in parseChtData(currentChtData.cht_init)" :key="'init-row-' + index">
                        <td v-for="key in getChtInitKeys(currentChtData.cht_init)" :key="'init-' + key + '-' + index">
                        {{ row[key] }}
                        </td>
                    </tr>
                    </tbody>
                </table>
                </div>
            </div>

            <!-- CHT New Table -->
            <div class="cht-table-section" v-if="currentChtData.cht_new">
                <h4>New - 'Polygon - AC2P - Cohort'</h4>
                <div class="table-container">
                <table class="cht-table">
                    <thead>
                    <tr>
                        <th v-for="key in getChtNewKeys(currentChtData.cht_new)" :key="'new-' + key">
                        {{ key }}
                        </th>
                    </tr>
                    </thead>
                    <tbody>
                    <tr v-for="(row, index) in parseChtData(currentChtData.cht_new)" :key="'new-row-' + index">
                        <td v-for="key in getChtNewKeys(currentChtData.cht_new)" :key="'new-' + key + '-' + index">
                        {{ row[key] }}
                        </td>
                    </tr>
                    </tbody>
                </table>
                </div>
            </div>
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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path v-if="!isMaximised" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
              <path v-if="isMaximised" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
            </svg>
          </button>
          
          <button 
            class="control-btn zoom-to-layer-btn"
            @click="zoomToActiveLayer"
            :title="getZoomToLayerTitle"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
              <path d="M12 10h-2v2H9v-2H7V9h2V7h1v2h2v1z"/>
            </svg>
          </button>
          
          <button 
            class="control-btn layer-control-btn"
            @click="showLayerControl = !showLayerControl"
            title="Toggle Layers"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M3 17v2h6v-2H3zM3 5v2h10V5H3zm10 16v-2h8v-2h-8v-2h-2v6h2zM7 9v2H3v2h4v2h2V9H7zm14 4v-2H11v2h10zm-6-4h2V7h4V5h-4V3h-2v6z"/>
            </svg>
          </button>

          <!-- Merge button – now below layer control -->
          <button 
            v-if="hasLayer3"
            class="control-btn merge-btn"
            @click="openMergeModal"
            :class="{ 'active': mergeStep === 2 }"
            :title="mergeStep === 2 ? 'Merge completed' : 'Merge two polygons'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          </button>
        </div>

        <!-- Merge Modal – floating panel at bottom‑right -->
        <div v-if="showMergeModal" class="merge-modal-panel">
          <div class="merge-modal-header">
            <h3>Merge Polygons</h3>
            <button @click="closeMergeModal" class="close-btn">&times;</button>
          </div>
          <div class="merge-modal-body">
            <div v-if="mergeStep === 0">
              <p>Select two adjacent polygons from the Processed layer.</p>
              <p>After selection, click <strong>Merge</strong> to combine them.</p>
            </div>
            <div v-else-if="mergeStep === 1">
              <p>Selected {{ mergeSelectedFeatures.length }}/2 polygons.</p>
              <p v-if="mergeSelectedFeatures.length === 2">
                Ready to merge. Click Merge below.
              </p>
              <p v-else>Please select two polygons.</p>
            </div>
            <div v-else-if="mergeStep === 2">
              <p>Merge completed. You can now Revert or Save.</p>
            </div>
          </div>
          <div class="merge-modal-footer">
            <button
              v-if="mergeStep < 2"
              class="btn btn-secondary"
              @click="closeMergeModal"
            >
              Cancel
            </button>
            <button
              v-if="mergeStep === 1 && mergeSelectedFeatures.length === 2"
              class="btn btn-primary"
              @click="performMergeAndTransition"
            >
              Merge
            </button>
            <button
              v-if="mergeStep === 2"
              class="btn btn-warning"
              @click="revertMerge"
            >
              Revert
            </button>
            <button
              v-if="mergeStep === 2"
              class="btn btn-success"
              @click="saveMerge"
            >
              Save
            </button>
          </div>
        </div>
    </div>

    <div>
        <PolygonCohortTable 
        :proposalId="currentProposalId"
        :initialVisible="showDataTable"
        @polygon-selected="onPolygonSelected"
        @zoom-to-polygon="onZoomToPolygon"
        />
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
import { singleClick } from 'ol/events/condition';
import * as XLSX from 'xlsx';
import * as turf from '@turf/turf';
import PolygonCohortTable from '@/components/common/table_polygon_cohort.vue';
import { helpers } from '@/utils/hooks';

export default {
  name: 'MapComponent',
  components: {
    PolygonCohortTable
  },
  props: {
    proposalId: {
      type: [Number, String],
      default: null
    },
    proposalIds: {
      type: Array,
      default: () => [-1]
    },
    featureCollection: {
      type: Object,
      default: null
    },
    featureCollection2: {
      type: Object,
      default: null
    },
    featureCollection3: {
      type: Object,
      default: null
    },
    featureCollection4: {
      type: Array,
      default: () => []
    },
    context: {
      type: Object,
      default: null
    }
  },
  emits: ['refresh-from-response', 'update-processed-geometry'],
  data() {
    return {
      map: null,
      layer1: null,
      layer2: null,
      layer3: null,
      layer4: null,
      layer1Visible: true,
      layer2Visible: true,
      layer3Visible: true,
      layer4Visible: false,
      showLayerControl: false,
      hasLayer2: false,
      hasLayer3: false,
      hasLayer4: false,
      selectedFeature: null,
      selectInteraction: null,
      showAdditionalInfo: false,
      isMaximised: false,
      geometryCollections: [],
      selectedGeometryIndex: null,
      highlightStyle: new Style({
        fill: new Fill({
          color: 'rgba(255, 255, 0, 0.6)'
        }),
        stroke: new Stroke({
          color: 'rgba(255, 255, 0, 1)',
          width: 3
        })
      }),
      layer4Style: function(feature) {
        const polyType = feature.get('poly_type');
        const baseColor = 'rgba(255, 255, 255, 0.6)';
        const defaultColor = 'rgba(100, 100, 100, 0.5)';
        
        return new Style({
            fill: new Fill({
            color: polyType === 'BASE' ? baseColor : defaultColor
            }),
            stroke: new Stroke({
            color: 'rgba(255, 165, 0, 0.8)',
            width: 2
            })
        });
      },
      showChtDialog: false,
      currentChtData: null,
      currentProposalId: null,
      showDataTable: true,
      selectedPolygonId: null,
      polygonHighlightLayer: null,

      // Merge mode properties
      mergeModeActive: false,
      mergeSelectedFeatures: [],
      mergeClickHandler: null,      // reference to the click listener

      // Flag to prevent multiple initializations
      mapInitialized: false,

      // Global click handler reference for cleanup
      globalClickHandler: null,

      // NEW: merge workflow
      showMergeModal: false,
      mergeStep: 0,               // 0: not started, 1: selecting, 2: merged
      backupFeatures: null,       // store original features before merge
      mergedFeatureId: null,      // track merged feature (for revert)

      displayFields: [
        { key: 'Block', label: 'Block' },
        { key: 'Compno', label: 'Comp No' },
        { key: 'fea_id', label: 'FEA ID' },
        { key: 'area_ha', label: 'Area (ha)' },
        { key: 'obj_code', label: 'Objective Code' },
        { key: 'resid_ba_m2ha', label: 'Residual BA (m²/ha)' },
        { key: 'target_ba_m2ha', label: 'Target BA (m²/ha)' },
        { key: 'species', label: 'Species' }
      ],
      additionalFields: [
        { key: 'region', label: 'Region' },
        { key: 'op_date', label: 'Operation Date (year)' },
        { key: 'regen_date', label: 'Regeneration Date (year)' },
        { key: 'resid_spha', label: 'Residual SPHA' },
        { key: 'target_spha', label: 'Target SPHA' }
      ]
    };
  },
  computed: {
    getZoomToLayerTitle() {
      if (this.hasLayer4 && this.layer4Visible && this.selectedGeometryIndex !== null) {
        return `Zoom to Geometry ${this.selectedGeometryIndex + 1}`;
      } else if (this.hasLayer3 && this.layer3Visible) {
        return 'Zoom to Layer 3';
      } else if (this.hasLayer2 && this.layer2Visible) {
        return 'Zoom to Layer 2';
      } else {
        return 'Zoom to Layer 1';
      }
    }
  },
  watch: {
    featureCollection: {
        handler(newGeoJSON) {
            console.log('Feature collection updated:', newGeoJSON);
            this.updateLayer1(newGeoJSON);
            if (this.map) {
                setTimeout(() => {
                    this.map.updateSize();
                }, 100);
            }
        },
        deep: true,
        immediate: true
    },
    featureCollection2: {
      handler(newGeoJSON) {
        this.updateLayer2(newGeoJSON);
      },
      deep: true
    },
    featureCollection3: {
      handler(newGeoJSON) {
        console.log('Feature collection3 updated, length:', newGeoJSON?.features?.length);
        if (this.ignoreNextPropUpdate) {
          console.log('Ignoring featureCollection3 update (merge just happened)');
          this.ignoreNextPropUpdate = false;
          return;
        }
        this.updateLayer3(newGeoJSON);
      },
      deep: true
    },
    featureCollection4: {
      handler(newGeometryList) {
        console.log('featureCollection4 updated:', newGeometryList);
        this.updateLayer4(newGeometryList);
        if (this.layer4Visible && newGeometryList.length > 0) {
          if (this.selectedGeometryIndex === null || this.selectedGeometryIndex >= newGeometryList.length) {
            this.selectedGeometryIndex = 0;
          }
          this.displayGeometryCollection(this.selectedGeometryIndex);
        } else if (newGeometryList.length === 0) {
          this.selectedGeometryIndex = null;
        }
      },
      deep: true
    },
    proposalId: {
      handler(newVal) {
        this.currentProposalId = this.ensureNumber(newVal);
      },
      immediate: true
    },
    '$route.params.proposal_id': {
      handler(newVal) {
        if (newVal && !this.currentProposalId) {
          this.currentProposalId = this.ensureNumber(newVal);
        }
      },
      immediate: true
    },
    context: {
      handler(newVal) {
        if (newVal && newVal.id && !this.currentProposalId) {
          this.currentProposalId = this.ensureNumber(newVal.id);
        }
      },
      deep: true,
      immediate: true
    },
    mergeSelectedFeatures: {
      handler(newVal) {
        console.log('mergeSelectedFeatures changed:', newVal.length, newVal);
      },
      deep: true
    }
  },
  mounted() {
    console.log('MapComponent mounted, container exists:', !!this.$refs.mapContainer);
    this.$nextTick(() => {
      this.initializeMapWithRetry();
    });
  },
  beforeDestroy() {
    console.log('MapComponent beforeDestroy');
    if (this.map) {
      if (this.globalClickHandler) {
        this.map.un('click', this.globalClickHandler);
      }
      if (this.mergeClickHandler) {
        this.map.un('click', this.mergeClickHandler);
      }
      this.map.setTarget(null);
    }
    window.removeEventListener('resize', this.handleResize);
    document.removeEventListener('keydown', this.handleEscape);
  },
  methods: {
    initializeMapWithRetry(retries = 5) {
      const container = this.$refs.mapContainer;
      if (!container) {
        console.warn('Map container ref not found');
        return;
      }
      const width = container.offsetWidth;
      const height = container.offsetHeight;
      console.log(`Map container dimensions: ${width}x${height}`);
      if (width > 0 && height > 0) {
        this.initializeMap();
      } else if (retries > 0) {
        console.log(`Map container has zero dimensions, retrying... (${retries} left)`);
        setTimeout(() => {
          this.initializeMapWithRetry(retries - 1);
        }, 100);
      } else {
        console.warn('Map container still has zero dimensions after retries, initializing anyway.');
        this.initializeMap();
      }
    },

    forceToRefreshMap: function() {
        if (this.map) {
            this.map.updateSize();
            if (this.featureCollection) {
                this.updateLayer1(this.featureCollection);
            }
        }
    },

    async exportChtToExcel() {
        if (!this.currentChtData) return;

        try {
            const workbook = XLSX.utils.book_new();

            if (this.currentChtData.cht_init) {
                const initData = this.parseChtData(this.currentChtData.cht_init);
                if (initData.length > 0) {
                    const initWorksheet = XLSX.utils.json_to_sheet(initData);
                    XLSX.utils.book_append_sheet(workbook, initWorksheet, 'Initial_Cohorts');
                }
            }

            if (this.currentChtData.cht_new) {
                const newData = this.parseChtData(this.currentChtData.cht_new);
                if (newData.length > 0) {
                    const newWorksheet = XLSX.utils.json_to_sheet(newData);
                    XLSX.utils.book_append_sheet(workbook, newWorksheet, 'New_Cohorts');
                }
            }

            const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
            const filename = `cohort_data_polygon_${this.selectedGeometryIndex + 1}_${timestamp}.xlsx`;

            XLSX.writeFile(workbook, filename);

            await swal.fire({
                icon: 'success',
                title: 'Export Successful',
                text: `Data exported to ${filename}`,
                timer: 3000,
                showConfirmButton: false,
                customClass: {
                    popup: 'swal2-popup-custom'
                }
            });

        } catch (error) {
            console.error('Error exporting to Excel:', error);
            await swal.fire({
                icon: 'error',
                title: 'Export Failed',
                text: 'Error exporting data to Excel. Please try again.',
                confirmButtonText: 'OK',
                customClass: {
                    popup: 'swal2-popup-custom'
                }
            });
        }
    },

    openChtDialog(geometryIndex) {
        const geometry = this.geometryCollections[geometryIndex];
        if (geometry && (geometry.cht_init || geometry.cht_new)) {
        this.selectedGeometryIndex = geometryIndex;
        this.currentChtData = {
            cht_init: geometry.cht_init,
            cht_new: geometry.cht_new
        };
        this.showChtDialog = true;
        }
    },

    parseChtData(chtJsonString) {
        try {
        const data = JSON.parse(chtJsonString);
        const keys = Object.keys(data);
        if (keys.length === 0) return [];
        
        const rowCount = data[keys[0]] ? Object.keys(data[keys[0]]).length : 0;
        const rows = [];
        
        for (let i = 0; i < rowCount; i++) {
            const row = {};
            keys.forEach(key => {
            row[key] = data[key] ? data[key][i] : null;
            });
            rows.push(row);
        }
        
        return rows;
        } catch (error) {
        console.error('Error parsing CHT data:', error);
        return [];
        }
    },

    getChtInitKeys(chtInitJson) {
        try {
            const data = JSON.parse(chtInitJson);
            return Object.keys(data);
        } catch (error) {
            return [];
        }
    },

    getChtNewKeys(chtNewJson) {
        try {
            const data = JSON.parse(chtNewJson);
            return Object.keys(data);
        } catch (error) {
            return [];
        }
    },

    initializeMap() {
      if (this.mapInitialized) return;
      console.log('initializeMap called');
      this.mapInitialized = true;

      const layer1Source = new VectorSource();
      const layer2Source = new VectorSource();
      const layer3Source = new VectorSource();
      const layer4Source = new VectorSource();

      const layer1Style = new Style({
        fill: new Fill({ color: 'rgba(255, 0, 0, 0.3)' }),
        stroke: new Stroke({ color: 'rgba(255, 0, 0, 0.8)', width: 2 })
      });

      const layer2Style = new Style({
        fill: new Fill({ color: 'rgba(0, 0, 255, 0.3)' }),
        stroke: new Stroke({ color: 'rgba(0, 0, 255, 0.8)', width: 2 })
      });

      const layer3Style = new Style({
        fill: new Fill({ color: 'rgba(68, 68, 68, 0.3)' }),
        stroke: new Stroke({ color: 'rgba(68, 68, 68, 0.8)', width: 2 })
      });

      this.layer1 = new VectorLayer({
        source: layer1Source,
        style: layer1Style,
        visible: this.layer1Visible
      });

      this.layer2 = new VectorLayer({
        source: layer2Source,
        style: layer2Style,
        visible: this.layer2Visible
      });

      // Layer3 with style function that respects feature styles
      this.layer3 = new VectorLayer({
        source: layer3Source,
        style: function(feature) {
          if (feature.getStyle && feature.getStyle()) {
            return feature.getStyle();
          }
          return layer3Style;
        },
        visible: this.layer3Visible
      });

      this.layer4 = new VectorLayer({
        source: layer4Source,
        style: this.layer4Style,
        visible: this.layer4Visible,
        zIndex: 10
      });

      const baseLayer = new TileLayer({ source: new OSM() });

      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [baseLayer, this.layer1, this.layer2, this.layer3, this.layer4],
        view: new View({
          projection: 'EPSG:4326',
          center: fromLonLat([121.5, -24.5], 'EPSG:4326'),
          zoom: 6,
        })
      });

      console.log('Map created, interactions count:', this.map.getInteractions().getLength());

      // Add global click listener for debugging
      this.globalClickHandler = (evt) => {
        console.log('Map click at', evt.coordinate);
      };
      this.map.on('click', this.globalClickHandler);

      this.setupSelectInteraction();

      if (this.featureCollection) {
        this.updateLayer1(this.featureCollection);
      }
      if (this.featureCollection2) {
        this.updateLayer2(this.featureCollection2);
      }
      if (this.featureCollection3) {
        this.updateLayer3(this.featureCollection3);
      }
      if (this.featureCollection4 && this.featureCollection4.length > 0) {
        this.updateLayer4(this.featureCollection4);
      }

      window.addEventListener('resize', this.handleResize);
      document.addEventListener('keydown', this.handleEscape);
    },

    setupSelectInteraction() {
      if (this.selectInteraction) {
        this.map.removeInteraction(this.selectInteraction);
      }

      this.selectInteraction = new Select({
        condition: singleClick,
        layers: [this.layer1, this.layer2, this.layer3, this.layer4],
        style: this.highlightStyle,
        multi: false
      });

      this.selectInteraction.on('select', (event) => {
        console.log('Default select interaction fired, selected:', event.selected.length);
        if (event.selected.length > 0) {
          this.selectedFeature = event.selected[0];
          this.showAdditionalInfo = false;
        } else {
          this.selectedFeature = null;
          this.showAdditionalInfo = false;
        }
      });

      this.map.addInteraction(this.selectInteraction);
      console.log('Select interaction added, total interactions:', this.map.getInteractions().getLength());
    },

    // Merge mode methods (adapted for modal)
    toggleMergeMode() {
      console.log('toggleMergeMode, current active:', this.mergeModeActive);
      if (this.mergeModeActive) {
        this.cancelMerge();
      } else {
        this.startMergeMode();
      }
    },

    startMergeMode() {
      console.log('startMergeMode called');
      if (!this.hasLayer3 || !this.layer3Visible) {
        alert('Please make the Processed layer visible first.');
        return;
      }
      this.mergeModeActive = true;
      this.mergeSelectedFeatures = [];
      
      // Remove default select interaction while in merge mode
      this.map.removeInteraction(this.selectInteraction);
      console.log('Default select interaction removed');
      
      // Add a custom click handler for layer3
      this.mergeClickHandler = (evt) => {
        // Check if the modal is still open and we're in step 1
        if (!this.showMergeModal || this.mergeStep !== 1) return;

        const pixel = this.map.getEventPixel(evt.originalEvent);
        const feature = this.map.forEachFeatureAtPixel(pixel, (feature, layer) => {
          // Only consider features from layer3
          if (layer === this.layer3) {
            return feature;
          }
          return null;
        });

        if (feature) {
          this.handleMergeClick(feature);
        }
      };
      this.map.on('click', this.mergeClickHandler);
    },

    cancelMerge() {
      console.log('cancelMerge called');
      this.mergeModeActive = false;
      this.mergeSelectedFeatures = [];
      // Remove custom click handler
      if (this.mergeClickHandler) {
        this.map.un('click', this.mergeClickHandler);
        this.mergeClickHandler = null;
      }
      // Restore default select interaction
      this.setupSelectInteraction();
    },

    handleMergeClick(feature) {
      console.log('handleMergeClick called with feature', feature);
      
      // Check if already selected
      const index = this.mergeSelectedFeatures.findIndex(f => f === feature);
      if (index !== -1) {
        // If already selected, remove it
        this.mergeSelectedFeatures.splice(index, 1);
        // Remove highlight style
        feature.setStyle(null);
      } else {
        // If not selected, add if less than 2
        if (this.mergeSelectedFeatures.length < 2) {
          this.mergeSelectedFeatures.push(feature);
          // Apply highlight style
          feature.setStyle(this.highlightStyle);
        } else {
          // Already have 2 selected – do nothing (or alert)
          alert('You can only select two polygons. Deselect one first.');
        }
      }
      
      // Force refresh of styles
      this.map.render();
    },

    // Helper to close polygon rings
    closePolygon(geojson) {
      if (geojson && geojson.geometry && geojson.geometry.type === 'Polygon') {
        const coordinates = geojson.geometry.coordinates;
        coordinates.forEach(ring => {
          if (ring.length > 0) {
            const first = ring[0];
            const last = ring[ring.length - 1];
            if (first[0] !== last[0] || first[1] !== last[1]) {
              ring.push(first);
            }
          }
        });
      }
      return geojson;
    },

    // NEW: open modal, reset step
    openMergeModal() {
      if (this.mergeStep === 2) {
        // Already merged – show revert/save options
        this.showMergeModal = true;
        return;
      }
      // Start new merge process
      this.mergeStep = 1;           // Set to selecting mode immediately
      this.mergeSelectedFeatures = [];
      this.showMergeModal = true;
      this.startMergeMode();   // starts selection mode
    },

    closeMergeModal() {
      this.showMergeModal = false;
      if (this.mergeStep < 2) {
        this.cancelMerge();    // clean up selection interactions
        this.mergeStep = 0;
      }
    },

    performMergeAndTransition() {
      // Call performMerge on the two selected features
      this.performMerge(this.mergeSelectedFeatures[0], this.mergeSelectedFeatures[1])
        .then(() => {
          this.mergeStep = 2;
          // Keep modal open, now showing Revert/Save
        })
        .catch(() => {
          // Merge failed – stay in step 1
          alert('Merge failed. See console for details.');
        });
    },

    revertMerge() {
      // Restore original two features without affecting others
      const source = this.layer3.getSource();
      
      // Remove the merged feature (which is the original feature1 with updated geometry)
      // We can identify it by the mergeId we stored
      const mergedFeature = source.getFeatures().find(f => f.get('mergeId') === this.mergedFeatureId);
      if (mergedFeature) {
        source.removeFeature(mergedFeature);
      }
      
      // Add back the two original clones
      source.addFeature(this.backupFeatures.f1);
      source.addFeature(this.backupFeatures.f2);
      
      // Remove highlight from restored features
      this.backupFeatures.f1.setStyle(null);
      this.backupFeatures.f2.setStyle(null);
      
      // Update source change and render
      source.changed();
      this.map.render();
      
      // Reset merge state and close modal
      this.mergeStep = 0;
      this.mergeSelectedFeatures = [];
      this.showMergeModal = false;
      this.cancelMerge(); // clean up selection mode
    },

    saveMerge() {
      // Prepare the updated GeoJSON
      const source = this.layer3.getSource();
      const format = new GeoJSON();
      const allFeatures = source.getFeatures();
      const updatedFC = {
        type: 'FeatureCollection',
        features: allFeatures.map(f => format.writeFeatureObject(f, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        }))
      };

      // Send to server
      fetch(`/api/proposal/${this.currentProposalId}/save_merged_geometry/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': helpers.getCookie('csrftoken')
        },
        body: JSON.stringify({
          updated_geojson: updatedFC,
          original_polygon_ids: this.backupFeatures.originalIds,
          merged_polygon_id: this.mergedFeatureId
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          this.mergeStep = 0;
          this.showMergeModal = false;
          alert('Merged geometry saved successfully.');
        } else {
          alert('Save failed: ' + data.error);
        }
      })
      .catch(err => {
        console.error(err);
        alert('Error saving.');
      });
    },

    // Modified performMerge to update feature1 in place
    performMerge(feature1, feature2) {
      const format = new GeoJSON();
      const geojson1 = format.writeFeatureObject(feature1, {
        featureProjection: 'EPSG:4326',
        dataProjection: 'EPSG:4326'
      });
      const geojson2 = format.writeFeatureObject(feature2, {
        featureProjection: 'EPSG:4326',
        dataProjection: 'EPSG:4326'
      });

      // Close polygons to satisfy GeoJSON spec
      const closed1 = this.closePolygon(geojson1);
      const closed2 = this.closePolygon(geojson2);

      // Clean coordinates (remove redundant points)
      const cleaned1 = turf.cleanCoords(closed1);
      const cleaned2 = turf.cleanCoords(closed2);

      // Rewind to correct orientation
      const rewound1 = turf.rewind(cleaned1, { mutate: true });
      const rewound2 = turf.rewind(cleaned2, { mutate: true });

      console.log('Cleaned/Rewound GeoJSON1:', JSON.stringify(rewound1.geometry, null, 2));
      console.log('Cleaned/Rewound GeoJSON2:', JSON.stringify(rewound2.geometry, null, 2));

      if (!rewound1.geometry || !rewound2.geometry) {
        console.error('One of the features has no geometry');
        alert('Invalid polygon geometry. Cannot merge.');
        this.cancelMerge();
        return Promise.reject();
      }

      if (rewound1.geometry.type !== 'Polygon' || rewound2.geometry.type !== 'Polygon') {
        console.error('Geometry types:', rewound1.geometry.type, rewound2.geometry.type);
        alert('Only polygons can be merged. Selected features are not polygons.');
        this.cancelMerge();
        return Promise.reject();
      }

      try {
        const featureCollection = turf.featureCollection([rewound1, rewound2]);
        const union = turf.union(featureCollection);
        console.log('Union result:', union);
        console.log('Union geometry:', JSON.stringify(union.geometry, null, 2));

        if (union.geometry.type !== 'Polygon') {
          alert('Cannot merge these polygons: the result would be a MultiPolygon. Please select adjacent polygons.');
          this.cancelMerge();
          return Promise.reject();
        }

        const cleanedUnion = turf.buffer(union, 0);
        if (cleanedUnion.geometry.type !== 'Polygon') {
          alert('Cleaned union is not a polygon – merge failed.');
          this.cancelMerge();
          return Promise.reject();
        }

        const simplified = turf.simplify(cleanedUnion, { tolerance: 0.00001, highQuality: false });
        console.log('Simplified geometry vertices count:', turf.coordAll(simplified).length);

        const areaHa = turf.area(simplified) / 10000;
        console.log('Merged polygon area (ha):', areaHa);

        const source = this.layer3.getSource();
        console.log('Before removal, source features count:', source.getFeatures().length);

        // **Store backup before modifying**
        this.backupFeatures = {
          f1: feature1.clone(),
          f2: feature2.clone(),
          originalIds: [feature1.get('id'), feature2.get('id')]
        };

        // Update feature1 in place
        const newGeometry = format.readGeometry(simplified.geometry, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        });
        feature1.setGeometry(newGeometry);
        feature1.set('area_ha', areaHa);
        feature1.set('merged', true);
        const mergedId = 'merged_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        feature1.set('mergeId', mergedId);
        this.mergedFeatureId = mergedId;

        // Apply bright style
        feature1.setStyle(new Style({
          fill: new Fill({ color: 'rgba(0, 255, 0, 0.5)' }),
          stroke: new Stroke({ color: 'rgba(0, 0, 0, 1)', width: 3 })
        }));

        // Remove feature2
        source.removeFeature(feature2);
        console.log('After removal, source features count:', source.getFeatures().length);

        source.changed();
        this.layer3.changed();

        const mergedExtent = feature1.getGeometry().getExtent();
        this.map.render();
        this.map.getView().fit(mergedExtent, { padding: [50, 50, 50, 50], duration: 500 });

        const allFeatures = source.getFeatures();
        const updatedFC = {
          type: 'FeatureCollection',
          features: allFeatures.map(f => format.writeFeatureObject(f, {
            featureProjection: 'EPSG:4326',
            dataProjection: 'EPSG:4326'
          }))
        };
        console.log('updatedFC features count:', updatedFC.features.length);

        this.ignoreNextPropUpdate = true;
        this.$emit('update-processed-geometry', updatedFC);

        this.cancelMerge();   // clean up selection mode
        return Promise.resolve();

      } catch (error) {
        console.error('Merge error details:', error);
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Stack:', error.stack);
        alert(`An error occurred while merging polygons: ${error.message}`);
        return Promise.reject();
      }
    },

    getFeatureValue(feature, fieldKey) {
      if (!feature) return 'N/A';
      
      let value = feature.get(fieldKey);
      
      if (value === undefined || value === null) {
        const properties = feature.getProperties();
        value = properties[fieldKey];
      }
      
      if (value === undefined || value === null) {
        const originalProperties = feature.get('properties');
        value = originalProperties ? originalProperties[fieldKey] : undefined;
      }

      // Format date fields to show only year
      if ((fieldKey === 'op_date' || fieldKey === 'regen_date') && value) {
        try {
          const date = new Date(value);
          return date.getFullYear().toString();
        } catch (e) {
          return value;
        }
      }

      // Format numeric fields
      if ((fieldKey === 'area_ha' || fieldKey === 'resid_ba_m2ha' || fieldKey === 'target_ba_m2ha') && value) {
        try {
          const numValue = parseFloat(value);
          return !isNaN(numValue) ? numValue.toFixed(2) : value;
        } catch (e) {
          return value;
        }
      }
      
      return value !== undefined && value !== null ? value : 'N/A';
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
      }, 100);
    },

    handleEscape(event) {
      if (event.key === 'Escape' && this.isMaximised) {
        this.isMaximised = false;
        setTimeout(() => {
          this.map.updateSize();
        }, 100);
      }
    },

    handleResize() {
      if (this.map) {
        setTimeout(() => {
          this.map.updateSize();
        }, 100);
      }
    },

    updateLayer1(geoJSON) {
      if (!this.layer1 || !geoJSON) return;
      
      const format = new GeoJSON();
      const features = format.readFeatures(geoJSON, {
        featureProjection: 'EPSG:4326',
        dataProjection: 'EPSG:4326'
      });
      
      this.layer1.getSource().clear();
      this.layer1.getSource().addFeatures(features);
      console.log('Layer1 updated, features added:', features.length);
      
      if (features.length > 0 && !this.hasLayer2) {
        this.zoomToLayer('layer1');
      }
    },

    updateLayer2(geoJSON) {
      if (!this.layer2 || !geoJSON) return;
      
      this.hasLayer2 = true;
      this.layer2Visible = true;
      this.layer2.setVisible(true);
      
      const format = new GeoJSON();
      const features = format.readFeatures(geoJSON, {
        featureProjection: 'EPSG:4326',
        dataProjection: 'EPSG:4326'
      });
      
      this.layer2.getSource().clear();
      this.layer2.getSource().addFeatures(features);
      console.log('Layer2 updated, features added:', features.length);
      
      if (features.length > 0) {
        this.zoomToLayer('layer2');
      }
    },

    updateLayer3(geoJSON) {
      if (!this.layer3 || !geoJSON) return;
      
      this.hasLayer3 = true;
      this.layer3Visible = true;
      this.layer3.setVisible(true);
      
      const format = new GeoJSON();
      const features = format.readFeatures(geoJSON, {
        featureProjection: 'EPSG:4326',
        dataProjection: 'EPSG:4326'
      });
      
      this.layer3.getSource().clear();
      this.layer3.getSource().addFeatures(features);
      console.log('Layer3 updated, features added:', features.length);
      
      if (features.length > 0) {
        this.zoomToLayer('layer3');
      }
    },

    updateLayer4(geometryList) {
      if (!this.layer4) return;
      
      this.hasLayer4 = geometryList.length > 0;
      this.geometryCollections = geometryList;
      
      this.layer4.getSource().clear();
      
      if (this.layer4Visible && geometryList.length > 0) {
        if (this.selectedGeometryIndex === null || this.selectedGeometryIndex >= geometryList.length) {
          this.selectedGeometryIndex = 0;
        }
        this.displayGeometryCollection(this.selectedGeometryIndex);
      } else if (geometryList.length === 0) {
        this.selectedGeometryIndex = null;
      }
    },

    toggleGeometryCollection(geometryIndex) {
      console.log('Selecting geometry index:', geometryIndex);
      this.selectedGeometryIndex = parseInt(geometryIndex);
      this.displayGeometryCollection(this.selectedGeometryIndex);
    },

    displayGeometryCollection(geometryIndex) {
      if (!this.layer4 || !this.geometryCollections[geometryIndex]) {
        console.log('Cannot display geometry - layer4:', this.layer4, 'geometry at index:', geometryIndex);
        return;
      }
      
      const format = new GeoJSON();
      const features = format.readFeatures(this.geometryCollections[geometryIndex], {
        featureProjection: 'EPSG:4326',
        dataProjection: 'EPSG:4326'
      });
      
      this.layer4.getSource().clear();
      this.layer4.getSource().addFeatures(features);
      
      if (features.length > 0) {
        this.zoomToLayer('layer4');
      }
    },

    toggleLayer(layerName) {
      if (layerName === 'layer1') {
        this.layer1.setVisible(this.layer1Visible);
      } else if (layerName === 'layer2' && this.layer2) {
        this.layer2.setVisible(this.layer2Visible);
      } else if (layerName === 'layer3' && this.layer3) {
        this.layer3.setVisible(this.layer3Visible);
      } else if (layerName === 'layer4' && this.layer4) {
        this.layer4.setVisible(this.layer4Visible);
        if (this.layer4Visible && this.hasLayer4) {
          if (this.selectedGeometryIndex === null && this.geometryCollections.length > 0) {
            this.selectedGeometryIndex = 0;
          }
          if (this.selectedGeometryIndex !== null) {
            this.displayGeometryCollection(this.selectedGeometryIndex);
          }
        }
      }
    },

    zoomToActiveLayer() {
      if (this.hasLayer4 && this.layer4Visible && this.selectedGeometryIndex !== null) {
        this.zoomToLayer('layer4');
      } else if (this.hasLayer3 && this.layer3Visible) {
        this.zoomToLayer('layer3');
      } else if (this.hasLayer2 && this.layer2Visible) {
        this.zoomToLayer('layer2');
      } else if (this.layer1Visible) {
        this.zoomToLayer('layer1');
      }
    },

    zoomToLayer(layerName) {
      let layer;
      if (layerName === 'layer1') {
        layer = this.layer1;
      } else if (layerName === 'layer2') {
        layer = this.layer2;
      } else if (layerName === 'layer3') {
        layer = this.layer3;
      } else if (layerName === 'layer4') {
        layer = this.layer4;
      }
      
      if (!layer || !layer.getVisible()) return;

      const source = layer.getSource();
      const features = source.getFeatures();
      
      if (features.length > 0) {
        const extent = source.getExtent();
        this.map.getView().fit(extent, {
          padding: [20, 20, 20, 20],
          duration: 1000
        });
      }
    },

    refreshFromResponse() {
      this.$emit('refresh-from-response');
    },

    testLayer4() {
      console.log('Testing Layer 4...');
      console.log('Layer4 visible:', this.layer4.getVisible());
      console.log('Layer4 source features:', this.layer4.getSource().getFeatures().length);

      this.layer4.getSource().changed();
      this.map.render();
    },

    toggleDataTable() {
      this.showDataTable = !this.showDataTable;
    },

    ensureNumber(value) {
      if (value === null || value === undefined) return null;
      const num = Number(value);
      return isNaN(num) ? null : num;
    },

    onPolygonSelected(polygonId) {
        console.log('Polygon selected:', polygonId);
        this.selectedPolygonId = polygonId;
        this.closeFeaturePopup();
        this.highlightPolygonInLayers(polygonId);
    },

    onZoomToPolygon(polygonId) {
        console.log('Zoom to polygon:', polygonId);
        this.selectedPolygonId = polygonId;
        this.zoomToPolygonInLayers(polygonId);
    },

    highlightPolygonInLayers(polygonId) {
        if (!this.map || !polygonId) return;

        const layers = [this.layer1, this.layer2, this.layer3, this.layer4];

        for (const layer of layers) {
            if (!layer || !layer.getVisible()) continue;

            const source = layer.getSource();
            const features = source.getFeatures();

            const foundFeature = this.findFeatureById(features, polygonId);

            if (foundFeature) {
            this.selectInteraction.getFeatures().clear();
            this.selectInteraction.getFeatures().push(foundFeature);
            this.selectedFeature = foundFeature;
            this.showAdditionalInfo = false;
            console.log('Found and highlighted polygon in layer:', layer);
            return;
            }
        }

        console.warn('Polygon with ID', polygonId, 'not found in any visible layer');
    },

    zoomToPolygonInLayers(polygonId) {
        if (!this.map || !polygonId) return;

        const layers = [this.layer1, this.layer2, this.layer3, this.layer4];

        for (const layer of layers) {
            if (!layer || !layer.getVisible()) continue;

            const source = layer.getSource();
            const features = source.getFeatures();

            const foundFeature = this.findFeatureById(features, polygonId);

            if (foundFeature) {
            this.selectInteraction.getFeatures().clear();
            this.selectInteraction.getFeatures().push(foundFeature);
            this.selectedFeature = foundFeature;
            this.showAdditionalInfo = false;
            this.zoomToFeature(foundFeature);
            console.log('Found and zoomed to polygon in layer:', layer);
            return;
            }
        }

        console.warn('Polygon with ID', polygonId, 'not found in any visible layer');
    },

    findFeatureById(features, polygonId) {
        return features.find(feature => {
            const featureId = feature.get('id') || 
                            feature.get('polygon_id') || 
                            feature.get('poly_id') ||
                            feature.get('name') ||
                            feature.get('fea_id') ||
                            (feature.get('properties') && (
                            feature.get('properties').id ||
                            feature.get('properties').polygon_id ||
                            feature.get('properties').poly_id ||
                            feature.get('properties').name ||
                            feature.get('properties').fea_id
                            ));

            return featureId && featureId.toString() === polygonId.toString();
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
            maxZoom: 15
            });
        }
    },

  }
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
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
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

.control-btn.merge-btn.active {
  background-color: #007bff;
  color: white;
  border-color: #0056b3;
}

.layer-control-popup,
.feature-popup {
  position: absolute;
  top: 50px;
  right: 10px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 1000;
  min-width: 280px;
  max-width: 400px;
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
  font-size: 14px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #333;
}

.layer-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.layer-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
}

.layer-item input[type="checkbox"] {
  margin: 0;
}

.nested-radio-group {
  margin-left: 16px;
  margin-top: 6px;
  padding-left: 8px;
  border-left: 2px solid #e0e0e0;
}

.radio-item {
  margin: 4px 0;
}

.radio-item label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
}

.radio-item input[type="radio"] {
  margin: 0;
}

.feature-content {
  font-size: 13px;
}

/* Compact table styles */
.feature-table.basic-attributes.compact {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}

.feature-table.basic-attributes.compact th,
.feature-table.basic-attributes.compact td {
  padding: 2px 6px;
  text-align: left;
  border-bottom: 1px solid #eee;
  line-height: 1.2;
}

.feature-table.basic-attributes.compact th {
  font-weight: 600;
  color: #555;
  white-space: nowrap;
  padding-right: 10px;
  width: 45%;
  font-size: 12px;
}

.feature-table.basic-attributes.compact td {
  color: #333;
  word-break: break-word;
  font-size: 12px;
}

/* Compact info toggle */
.info-toggle-section.compact {
  margin: 8px 0;
  padding: 6px 0;
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
  padding: 2px 6px;
  border-radius: 3px;
  transition: all 0.2s;
  font-size: 12px;
}

.info-toggle-btn:hover {
  background-color: #f8f9fa;
}

.toggle-text {
  font-weight: 500;
}

/* Compact additional attributes */
.additional-attributes.compact {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eee;
}

.additional-attributes.compact .additional-title {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #555;
}

.additional-attributes.compact .attributes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 4px;
}

.additional-attributes.compact .attribute-item {
  display: flex;
  flex-direction: column;
  padding: 4px;
  background: #f8f9fa;
  border-radius: 3px;
  border: 1px solid #e9ecef;
  min-height: auto;
}

.additional-attributes.compact .attribute-label {
  font-size: 10px;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 1px;
  line-height: 1.1;
}

.additional-attributes.compact .attribute-value {
  font-size: 11px;
  color: #333;
  font-weight: 500;
  word-break: break-word;
  line-height: 1.2;
}

.geometry-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.cht-link-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 3px;
  transition: background-color 0.2s;
}

.cht-link-btn:hover {
  background-color: #f0f0f0;
}

.cht-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10001;
}

.cht-dialog {
  background: white;
  border-radius: 8px;
  padding: 16px;
  max-width: 90vw;
  max-height: 90vh;
  width: 950px;
  overflow: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.cht-content {
  max-height: 70vh;
  overflow-y: auto;
}

.cht-table-section {
  margin-bottom: 20px;
}

.cht-table-section h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 15px;
  border-bottom: 2px solid #007bff;
  padding-bottom: 4px;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.cht-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.cht-table th,
.cht-table td {
  padding: 6px 8px;
  text-align: left;
  border-bottom: 1px solid #eee;
  border-right: 1px solid #eee;
  white-space: nowrap;
}

.cht-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
  position: sticky;
  top: 0;
}

.cht-table tr:hover {
  background-color: #f5f5f5;
}

.cht-table th:last-child,
.cht-table td:last-child {
  border-right: none;
}

/* Floating merge panel - match layer control popup */
.merge-modal-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 300px;
  max-width: 400px;
  min-width: 280px;
  background: white;
  border-radius: 4px;
  border: 1px solid #ccc;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 10001;
  pointer-events: auto;
  font-size: 13px;
}

.merge-modal-header {
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.merge-modal-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.merge-modal-body {
  padding: 12px;
}

.merge-modal-body p {
  margin: 0 0 8px 0;
  font-size: 13px;
  line-height: 1.4;
}

.merge-modal-footer {
  padding: 8px 12px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.merge-modal-footer .btn {
  padding: 6px 12px;
  font-size: 13px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: white;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
}

.merge-modal-footer .btn:hover {
  background: #f5f5f5;
}

.merge-modal-footer .btn-primary {
  background: #007bff;
  color: white;
  border-color: #0056b3;
}

.merge-modal-footer .btn-primary:hover {
  background: #0069d9;
}

.merge-modal-footer .btn-secondary {
  background: #6c757d;
  color: white;
  border-color: #545b62;
}

.merge-modal-footer .btn-secondary:hover {
  background: #5a6268;
}

.merge-modal-footer .btn-success {
  background: #28a745;
  color: white;
  border-color: #1e7e34;
}

.merge-modal-footer .btn-success:hover {
  background: #218838;
}

.merge-modal-footer .btn-warning {
  background: #ffc107;
  color: black;
  border-color: #d39e00;
}

.merge-modal-footer .btn-warning:hover {
  background: #e0a800;
}

.btn { padding: 0.5rem 1rem; border: none; border-radius: 4px; cursor: pointer; }
.btn-primary { background: #007bff; color: white; }
.btn-secondary { background: #6c757d; color: white; }
.btn-success { background: #28a745; color: white; }
.btn-warning { background: #ffc107; color: black; }

:deep(.swal2-container) {
    z-index: 10003 !important;
}

:deep(.swal2-popup) {
    z-index: 10004 !important;
}

:deep(.swal2-backdrop-show) {
    z-index: 10003 !important;
}

</style>

<style>
/* Global styles for SweetAlert2 in this component context */
.swal2-popup-custom {
    z-index: 10004 !important;
}

.swal2-container {
    z-index: 10003 !important;
}
</style>
