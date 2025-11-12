<template>
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
            Historical Layer
          </label>
        </div>
        <!--
        -->
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
              <label>
                <input 
                  type="radio" 
                  :value="index"
                  v-model="selectedGeometryIndex"
                  @change="toggleGeometryCollection(index)"
                >
                Polygon {{ index + 1 }} ({{ index + 1  }}st iteration)
              </label>
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
        <table class="feature-table basic-attributes">
          <tbody>
            <tr v-for="field in displayFields" :key="field.key">
              <th class="field-label">{{ field.label }}:</th>
              <td class="field-value">{{ getFeatureValue(selectedFeature, field.key) }}</td>
            </tr>
          </tbody>
        </table>
        
        <!-- Information icon toggle -->
        <div class="info-toggle-section">
          <button 
            class="info-toggle-btn"
            @click="showAdditionalInfo = !showAdditionalInfo"
            :title="showAdditionalInfo ? 'Hide additional details' : 'Show additional details'"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
            </svg>
            <span class="toggle-text">
              {{ showAdditionalInfo ? 'Less details' : 'More details...' }}
            </span>
          </button>
        </div>

        <!-- Additional attributes in multi-column layout -->
        <div v-if="showAdditionalInfo && additionalFields.length > 0" class="additional-attributes">
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

export default {
  name: 'MapComponent',
  props: {
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
    // Add the missing props
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
    // Add context prop if needed
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
      layer4Style: new Style({
        fill: new Fill({
          color: 'rgba(255, 165, 0, 0.3)'
        }),
        stroke: new Stroke({
          color: 'rgba(255, 165, 0, 0.8)',
          width: 2
        })
      })
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
        this.updateLayer1(newGeoJSON);
      },
      deep: true
    },
    featureCollection2: {
      handler(newGeoJSON) {
        this.updateLayer2(newGeoJSON);
      },
      deep: true
    },
    featureCollection3: {
      handler(newGeoJSON) {
        this.updateLayer3(newGeoJSON);
      },
      deep: true
    },
    featureCollection4: {
      handler(newGeometryList) {
        this.updateLayer4(newGeometryList);
      },
      deep: true
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initializeMap();
      this.hasLayer2 = !!this.featureCollection2;
      this.layer2Visible = this.hasLayer2;

      this.hasLayer3 = !!this.featureCollection3;
      this.layer3Visible = this.hasLayer3;

      this.hasLayer4 = !!this.featureCollection4 && this.featureCollection4.length > 0;
      this.layer4Visible = false;
    });
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
      const layer2Source = new VectorSource();
      const layer3Source = new VectorSource();
      const layer4Source = new VectorSource();

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

      // Style for layer 2
      const layer2Style = new Style({
        fill: new Fill({
          color: 'rgba(0, 0, 255, 0.3)'
        }),
        stroke: new Stroke({
          color: 'rgba(0, 0, 255, 0.8)',
          width: 2
        })
      });

      // Style for layer 3
      const layer3Style = new Style({
        fill: new Fill({
          color: 'rgba(68, 68, 68, 0.3)'
        }),
        stroke: new Stroke({
          color: 'rgba(68, 68, 68, 0.8)',
          width: 2
        })
      });

      // Create layers
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

      this.layer3 = new VectorLayer({
        source: layer3Source,
        style: layer3Style,
        visible: this.layer3Visible
      });

      this.layer4 = new VectorLayer({
        source: layer4Source,
        style: this.layer4Style,
        visible: this.layer4Visible,
        zIndex: 10
      });

      // Base layer (OSM)
      const baseLayer = new TileLayer({
        source: new OSM()
      });

      // Initialize the map
      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [baseLayer, this.layer1, this.layer2, this.layer3, this.layer4],
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
        condition: click,
        layers: [this.layer1, this.layer2, this.layer3, this.layer4],
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
      
      if (features.length > 0) {
        this.zoomToLayer('layer3');
      }
    },

    updateLayer4(geometryList) {
      if (!this.layer4 || !geometryList) return;
      
      this.hasLayer4 = geometryList.length > 0;
      this.geometryCollections = geometryList;
      
      this.layer4.getSource().clear();
      
      if (this.selectedGeometryIndex !== null && geometryList[this.selectedGeometryIndex]) {
        this.displayGeometryCollection(this.selectedGeometryIndex);
      }
    },

    toggleGeometryCollection(geometryIndex) {
      console.log('Selecting geometry index:', geometryIndex);
      this.selectedGeometryIndex = parseInt(geometryIndex);
      this.displayGeometryCollection(this.selectedGeometryIndex);
    },

    displayGeometryCollection(geometryIndex) {
      console.log('GEOM1: ' + JSON.stringify(this.geometryCollections[geometryIndex]))
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
        if (this.layer4Visible && this.hasLayer4 && this.selectedGeometryIndex === null && this.geometryCollections.length > 0) {
          this.selectedGeometryIndex = 0;
          this.displayGeometryCollection(0);
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

.layer-control-popup,
.feature-popup {
  position: absolute;
  top: 50px;
  right: 10px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 1000;
  min-width: 280px;
  max-width: 500px;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
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
  gap: 8px;
}

.layer-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.layer-item input[type="checkbox"] {
  margin: 0;
}

.nested-radio-group {
  margin-left: 20px;
  margin-top: 8px;
  padding-left: 10px;
  border-left: 2px solid #e0e0e0;
}

.radio-item {
  margin: 6px 0;
}

.radio-item label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
}

.radio-item input[type="radio"] {
  margin: 0;
}

.feature-content {
  font-size: 14px;
}

.feature-table.basic-attributes {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 15px;
}

.feature-table.basic-attributes th,
.feature-table.basic-attributes td {
  padding: 4px 8px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.feature-table.basic-attributes th {
  font-weight: 600;
  color: #555;
  white-space: nowrap;
  padding-right: 15px;
}

.feature-table.basic-attributes td {
  color: #333;
  word-break: break-word;
}

.info-toggle-section {
  margin: 15px 0;
  padding: 10px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
}

.info-toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  font-size: 13px;
}

.info-toggle-btn:hover {
  background-color: #f8f9fa;
}

.toggle-text {
  font-weight: 500;
}

.additional-attributes {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.additional-title {
  margin: 0 0 12px 0;
  font-size: 13px;
  font-weight: 600;
  color: #555;
}

.attributes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.attribute-item {
  display: flex;
  flex-direction: column;
  padding: 6px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.attribute-label {
  font-size: 11px;
  font-weight: 600;
  color: #6c757d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.attribute-value {
  font-size: 12px;
  color: #333;
  font-weight: 500;
  word-break: break-word;
}
</style>
