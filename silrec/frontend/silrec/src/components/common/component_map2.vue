<template>
  <div>
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/common/component_map2.vue</div>
    <div class="map-container" :class="{ 'maximised': isMaximised }">
        <div ref="mapContainer" class="map"></div>

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
        
        </div>
    </div>

    <!-- New DataTable Section -->
    <div class="datatable-container mt-4">
        <div class="card">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0">Search Polygons</h5>
                <div>
                    <button 
                        class="btn btn-sm btn-light me-2"
                        @click="toggleTable"
                        :title="tableVisible ? 'Hide table' : 'Show table'"
                    >
                        <i class="bi" :class="tableVisible ? 'bi-eye-slash' : 'bi-eye'"></i>
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
                <!-- Filters -->
                <div class="row mb-3">
                    <div class="col-md-2">
                        <label for="filterObjCode" class="form-label">Objective Code</label>
                        <input
                            v-model="filters.obj_code"
                            type="text"
                            class="form-control form-control-sm"
                            id="filterObjCode"
                            placeholder="Filter by obj_code..."
                        />
                    </div>
                    <div class="col-md-2">
                        <label for="filterCompartment" class="form-label">Compartment</label>
                        <input
                            v-model="filters.compartment"
                            type="text"
                            class="form-control form-control-sm"
                            id="filterCompartment"
                            placeholder="Filter by compartment..."
                        />
                    </div>
                    <div class="col-md-2">
                        <label for="filterBlock" class="form-label">Block</label>
                        <input
                            v-model="filters.block"
                            type="text"
                            class="form-control form-control-sm"
                            id="filterBlock"
                            placeholder="Filter by block..."
                        />
                    </div>
                    <div class="col-md-2">
                        <label for="filterDistrict" class="form-label">District</label>
                        <input
                            v-model="filters.district"
                            type="text"
                            class="form-control form-control-sm"
                            id="filterDistrict"
                            placeholder="Filter by district..."
                        />
                    </div>
                    <div class="col-md-2">
                        <label for="filterZfeaId" class="form-label">FEA ID</label>
                        <input
                            v-model="filters.zfea_id"
                            type="text"
                            class="form-control form-control-sm"
                            id="filterZfeaId"
                            placeholder="Filter by FEA ID..."
                        />
                    </div>
                    <div class="col-md-2">
                        <label for="filterTreatmentStatus" class="form-label">Treatment Status</label>
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
                    <div class="col-md-2">
                        <label for="filterCreatedFrom" class="form-label">Created From</label>
                        <input
                            v-model="filters.created_from"
                            type="date"
                            class="form-control form-control-sm"
                            id="filterCreatedFrom"
                        />
                    </div>
                    <div class="col-md-2">
                        <label for="filterCreatedTo" class="form-label">Created To</label>
                        <input
                            v-model="filters.created_to"
                            type="date"
                            class="form-control form-control-sm"
                            id="filterCreatedTo"
                        />
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

export default {
  name: 'MapComponent',
  components: {
    datatable
  },
  props: {
    featureCollection: {
      type: Object,
      default: null
    },
    displayFieldsConfig: {
      type: Array,
      default: () => [
        { key: 'name', label: 'Name' },
        { key: 'Block', label: 'Block' },
        { key: 'Compno', label: 'Comp No' }
      ]
    },
    additionalFieldsConfig: {
      type: Array,
      default: () => [
        { key: 'Region', label: 'Region' },
        { key: 'fea_id', label: 'Feature ID' },
        { key: 'area', label: 'Area' },
        { key: 'status', label: 'Status' },
        { key: 'type', label: 'Type' },
        { key: 'owner', label: 'Owner' }
      ]
    },
    context: {
      type: Object,
      default: null
    }
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
          color: 'rgba(255, 255, 0, 0.6)'
        }),
        stroke: new Stroke({
          color: 'rgba(255, 255, 0, 1)',
          width: 3
        })
      }),

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
        created_to: ''
      },
      filteredPolygons: []
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
        'Actions'
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
          data: function(d) {
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
            const hasFilters = Object.values(vm.filters).some(val => val !== '');
            if (!hasFilters) {
              // Return empty result if no filters
              d.return_empty = true;
            }
          }
        },
        columns: [
        {
            data: 'polygon_id',
            name: 'polygon_id',
            visible: false,
            orderable: true
        },
        {
            data: 'name',
            name: 'name',
            orderable: true,
            render: function(data, type, row) {
            return data || 'N/A';
            }
        },
        {
            data: 'compartment_details.compartment',
            name: 'compartment__compartment',
            orderable: true,
            render: function(data, type, row) {
            return data || 'N/A';
            }
        },
        {
            data: 'area_ha',
            name: 'area_ha',
            orderable: true,
            render: function(data, type, row) {
            return data ? data.toFixed(2) : 'N/A';
            }
        },
        {
            data: 'zfea_id',
            name: 'zfea_id',
            orderable: true,
            render: function(data, type, row) {
            return data || 'N/A';
            }
        },
        {
            data: 'obj_codes',
            name: 'assignchttoply__cohort__obj_code',
            orderable: true,
            render: function(data, type, row) {
            return data || 'N/A';
            }
        },
        {
            data: 'species_list',
            name: 'assignchttoply__cohort__species',
            orderable: true,
            render: function(data, type, row) {
            return data || 'N/A';
            }
        },
        {
            data: 'primary_cohort.target_ba_m2ha',
            name: 'assignchttoply__cohort__target_ba_m2ha',
            orderable: true,
            render: function(data, type, row) {
            return data ? data.toFixed(2) : 'N/A';
            }
        },
        {
            data: 'primary_cohort.resid_ba_m2ha',
            name: 'assignchttoply__cohort__resid_ba_m2ha',
            orderable: true,
            render: function(data, type, row) {
            return data ? data.toFixed(2) : 'N/A';
            }
        },
        {
            data: 'treatment_statuses',
            name: 'assignchttoply__cohort__treatment__status',
            orderable: true,
            render: function(data, type, row) {
            return data || 'N/A';
            }
        },
        {
            data: 'created_on_formatted',
            name: 'created_on',
            orderable: true,
            render: function(data, type, row) {
            return data || 'N/A';
            }
        },
        {
            data: 'polygon_id',
            orderable: false,
            searchable: false,
            className: 'action-column',
            render: function(data, type, row) {
            return `
                <button class="btn btn-sm btn-outline-primary me-1 view-polygon-btn" data-polygon-id="${data}" title="View Details">
                <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-info zoom-polygon-btn" data-polygon-id="${data}" title="Zoom to Polygon">
                <i class="bi bi-zoom-in"></i>
                </button>
            `;
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
          // Store the filtered data and update map
          vm.filteredPolygons = settings.json.data || [];
          vm.updateMapWithFilteredData();
          
          // Re-attach event listeners
          vm.attachEventListeners();
        }
      };
    }
  },
  watch: {
    featureCollection: {
      handler(newGeoJSON) {
        this.updateLayer1(newGeoJSON);
      },
      deep: true
    },
    // Watch all filters and refresh data when they change
    filters: {
      handler() {
        this.debouncedRefreshData();
      },
      deep: true
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initializeMap();
    });
    
    // Setup debounced refresh
    this.debouncedRefreshData = this.debounce(this.refreshData, 500);
  },
  beforeUnmount() {
    if (this.map) {
      this.map.setTarget(null);
    }
    window.removeEventListener('resize', this.handleResize);
    document.removeEventListener('keydown', this.handleEscape);
  },
  methods: {
    initializeMap() {
      // Create vector sources and layers
      const layer1Source = new VectorSource();

      // Style for layer 1
      const layer1Style = new Style({
        fill: new Fill({
          color: 'rgba(255, 0, 0, 0.3)'
        }),
        stroke: new Stroke({
          color: 'rgba(255, 0, 0, 0.8)',
          width: 2
        })
      });

      // Create layers
      this.layer1 = new VectorLayer({
        source: layer1Source,
        style: layer1Style,
        visible: this.layer1Visible
      });

      // Base layer (OSM)
      const baseLayer = new TileLayer({
        source: new OSM()
      });

      // Initialize the map
      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [baseLayer, this.layer1],
        view: new View({
          projection: 'EPSG:4326',
          center: fromLonLat([121.5, -24.5], 'EPSG:4326'),
          zoom: 6,
        })                                                                                                                                            
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

    setupSelectInteraction() {
      if (this.selectInteraction) {
        this.map.removeInteraction(this.selectInteraction);
      }

      this.selectInteraction = new Select({
        condition: click,
        layers: [this.layer1],
        style: this.highlightStyle,
        multi: false
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
        value = originalProperties ? originalProperties[fieldKey] : undefined;
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
          duration: 1000
        });
      }
    },

    refreshFromResponse() {
      this.$emit('refresh-from-response');
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
        if (this.$refs.polygon_datatable && this.$refs.polygon_datatable.vmDataTable) {
          await this.$refs.polygon_datatable.vmDataTable.ajax.reload();
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

    updateMapWithFilteredData() {
      if (!this.layer1) return;

      // Clear existing features
      this.layer1.getSource().clear();

      // Create GeoJSON from filtered polygons
      const features = this.filteredPolygons.map(polygon => {
        if (polygon.geom) {
          const format = new GeoJSON();
          const feature = format.readFeature(polygon.geom, {
            featureProjection: 'EPSG:4326',
            dataProjection: 'EPSG:4326'
          });
          
          // Add polygon data as properties
          feature.setProperties({
            ...polygon,
            id: polygon.polygon_id,
            polygon_id: polygon.polygon_id,
            name: polygon.name
          });
          
          return feature;
        }
        return null;
      }).filter(feature => feature !== null);

      // Add features to map
      this.layer1.getSource().addFeatures(features);

      // Zoom to show all features if there are any
      if (features.length > 0) {
        const extent = this.layer1.getSource().getExtent();
        this.map.getView().fit(extent, {
          padding: [50, 50, 50, 50],
          duration: 1000
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
      $(this.$el).on('click', '.view-polygon-btn', function() {
        const polygonId = $(this).data('polygon-id');
        vm.handlePolygonSelection(polygonId);
      });
      
      $(this.$el).on('click', '.zoom-polygon-btn', function() {
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
      return features.find(feature => {
        const featureId = feature.get('polygon_id') || 
                         feature.get('id') || 
                         (feature.get('properties') && feature.get('properties').polygon_id);

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
    }
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

.datatable-container {
  margin-top: 20px;
}

:deep(.action-column) {
  white-space: nowrap;
  width: 120px;
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
</style>
