<template>
  <div class="map-container">
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
            Layer 1
          </label>
        </div>
        <div class="layer-item" v-if="hasLayer2">
          <label>
            <input 
              type="checkbox" 
              v-model="layer2Visible" 
              @change="toggleLayer('layer2')"
            >
            Layer 2
          </label>
        </div>
      </div>
    </div>

    <!-- Map control buttons -->
    <div class="map-controls">
      <button 
        class="control-btn zoom-to-layer-btn"
        @click="zoomToActiveLayer"
        :title="hasLayer2 ? 'Zoom to Layer 2' : 'Zoom to Layer 1'"
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
    }
  },
  emits: ['refresh-from-response'],
  data() {
    return {
      map: null,
      layer1: null,
      layer2: null,
      layer1Visible: true,
      layer2Visible: true,
      showLayerControl: false,
      hasLayer2: false
    };
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
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initializeMap();
      this.hasLayer2 = !!this.featureCollection2;
      this.layer2Visible = this.hasLayer2;
    });
  },
  beforeUnmount() {
    if (this.map) {
      this.map.setTarget(null);
    }
  },
  methods: {
    initializeMap() {
      // Create vector sources and layers
      const layer1Source = new VectorSource();
      const layer2Source = new VectorSource();

      // Style for layer 1
      const layer1Style = new Style({
        fill: new Fill({
          color: 'rgba(255, 0, 0, 0.3)' // Red with opacity
        }),
        stroke: new Stroke({
          color: 'rgba(255, 0, 0, 0.8)',
          width: 2
        })
      });

      // Style for layer 2
      const layer2Style = new Style({
        fill: new Fill({
          color: 'rgba(0, 0, 255, 0.3)' // Blue with opacity
        }),
        stroke: new Stroke({
          color: 'rgba(0, 0, 255, 0.8)',
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

      // Base layer (OSM)
      const baseLayer = new TileLayer({
        source: new OSM()
      });

      // Initialize the map - simplified as per your note
      this.map = new Map({
        target: this.$refs.mapContainer,
        layers: [baseLayer, this.layer1, this.layer2],
        view: new View({
          projection: 'EPSG:4326',
          center: fromLonLat([121.5, -24.5], 'EPSG:4326'), // Center of WA
          zoom: 6,
        })                                                                                                                                            
      });

      // Load initial data if available
      if (this.featureCollection) {
        this.updateLayer1(this.featureCollection);
      }
      if (this.featureCollection2) {
        this.updateLayer2(this.featureCollection2);
      }

      // Ensure map updates when container resizes
      window.addEventListener('resize', this.handleResize);
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
      
      // Auto-zoom to layer 1 if it's the only layer
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
      
      // Auto-zoom to layer 2 if it exists
      if (features.length > 0) {
        this.zoomToLayer('layer2');
      }
    },

    toggleLayer(layerName) {
      if (layerName === 'layer1') {
        this.layer1.setVisible(this.layer1Visible);
      } else if (layerName === 'layer2' && this.layer2) {
        this.layer2.setVisible(this.layer2Visible);
      }
    },

    zoomToActiveLayer() {
      if (this.hasLayer2 && this.layer2Visible) {
        this.zoomToLayer('layer2');
      } else if (this.layer1Visible) {
        this.zoomToLayer('layer1');
      }
    },

    zoomToLayer(layerName) {
      const layer = layerName === 'layer1' ? this.layer1 : this.layer2;
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
    }
  }
};
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 600px; /* Fixed height - adjust as needed */
  min-height: 400px;
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
}

.control-btn:hover {
  background: #f5f5f5;
}

.layer-control-popup {
  position: absolute;
  top: 50px;
  right: 10px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 1000;
  min-width: 150px;
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
</style>
