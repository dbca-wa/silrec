<!-- cut_polygon_tool.vue -->
<template>
  <div class="cut-polygon-tool">
    <button 
      class="control-btn cut-btn"
      @click="toggleCutMode"
      :class="{ active: isCutModeActive }"
      :title="getButtonTitle"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M9.64 7.64c.23-.5.36-1.05.36-1.64 0-2.21-1.79-4-4-4S2 3.79 2 6s1.79 4 4 4c.59 0 1.14-.13 1.64-.36L10 12l-2.36 2.36C7.14 14.13 6.59 14 6 14c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4c0-.59-.13-1.14-.36-1.64L12 14l7 7h3v-1L9.64 7.64zM6 8c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm0 12c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm6-7.5c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zM19 3l-6 6 2 2 7-7V3z"/>
      </svg>
    </button>

    <!-- Cut Tool Panel -->
    <div v-if="isCutModeActive" class="cut-panel">
      <div class="cut-panel-header">
        <h3>Cut Polygon</h3>
        <button @click="cancelCut" class="close-btn">×</button>
      </div>
      
      <div class="cut-panel-content">
        <div class="instruction-steps">
          <div class="step" :class="{ active: currentStep === 1, completed: selectedPolygon }">
            <span class="step-number">1</span>
            <span class="step-text">Select polygon to cut</span>
            <span v-if="selectedPolygon" class="step-check">✓</span>
          </div>
          <div class="step" :class="{ active: currentStep === 2, completed: point1 }">
            <span class="step-number">2</span>
            <span class="step-text">Select first point</span>
            <span v-if="point1" class="step-check">✓</span>
          </div>
          <div class="step" :class="{ active: currentStep === 3, completed: point2 }">
            <span class="step-number">3</span>
            <span class="step-text">Select second point</span>
            <span v-if="point2" class="step-check">✓</span>
          </div>
        </div>

        <div v-if="selectedPolygon" class="selected-polygon-info">
          <strong>Selected Polygon ID:</strong> {{ selectedPolygonId }}
        </div>

        <div v-if="point1" class="point-info">
          <strong>Point 1:</strong> [{{ point1[0].toFixed(4) }}, {{ point1[1].toFixed(4) }}]
        </div>

        <div v-if="point2" class="point-info">
          <strong>Point 2:</strong> [{{ point2[0].toFixed(4) }}, {{ point2[1].toFixed(4) }}]
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div class="cut-panel-actions">
          <button 
            class="cancel-btn"
            @click="cancelCut"
          >
            Cancel
          </button>
          <button 
            class="cut-action-btn"
            :disabled="!canCut"
            @click="performCut"
          >
            Cut Polygon
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import Feature from 'ol/Feature';
import Point from 'ol/geom/Point';
import LineString from 'ol/geom/LineString';
import Polygon from 'ol/geom/Polygon';
import { Style, Circle as CircleStyle, Fill, Stroke } from 'ol/style';
import GeoJSON from 'ol/format/GeoJSON';
import polygonSplitter from 'polygon-splitter';

export default {
  name: 'CutPolygonTool',
  props: {
    map: {
      type: Object,
      required: true
    },
    layer3: {
      type: Object,
      required: true
    },
    hasLayer3: {
      type: Boolean,
      default: false
    },
    proposalId: {
      type: [Number, String],
      default: null
    },
    highlightStyle: {
      type: Object,
      default: () => new Style({
        fill: new Fill({ color: 'rgba(255, 255, 0, 0.6)' }),
        stroke: new Stroke({ color: 'rgba(255, 255, 0, 1)', width: 3 })
      })
    }
  },
  emits: ['update-processed-geometry', 'disable-select-interaction', 'enable-select-interaction'],
  data() {
    return {
      isCutModeActive: false,
      currentStep: 1,
      selectedPolygon: null,
      selectedPolygonId: null,
      selectedPolygonGeoJSON: null,
      point1: null,
      point2: null,
      errorMessage: null,
      
      // Temporary layers for visualization
      pointLayer: null,
      lineLayer: null,
      
      // Click handler reference
      clickHandler: null,
      
      // Format for GeoJSON conversion
      geoJSONFormat: new GeoJSON()
    };
  },
  computed: {
    getButtonTitle() {
      return this.isCutModeActive ? 'Exit Cut Mode' : 'Cut Polygon Tool';
    },
    canCut() {
      return this.selectedPolygon && this.point1 && this.point2 && !this.errorMessage;
    }
  },
  watch: {
    isCutModeActive(active) {
      if (active) {
        this.activateCutMode();
      } else {
        this.deactivateCutMode();
      }
    }
  },
  beforeDestroy() {
    this.cleanup();
  },
  methods: {
    toggleCutMode() {
      this.isCutModeActive = !this.isCutModeActive;
    },

    activateCutMode() {
      console.log('Cut mode activated');
      
      // Disable parent's select interaction
      this.$emit('disable-select-interaction');
      
      // Create temporary layers for visualization
      this.createTempLayers();
      
      // Set up click handler
      this.clickHandler = this.handleMapClick.bind(this);
      this.map.on('click', this.clickHandler);
      
      // Change cursor style
      this.map.getTargetElement().style.cursor = 'crosshair';
      
      // Reset state
      this.resetState();
    },

    deactivateCutMode() {
      console.log('Cut mode deactivated');
      
      // Remove click handler
      if (this.clickHandler) {
        this.map.un('click', this.clickHandler);
        this.clickHandler = null;
      }
      
      // Remove temporary layers
      this.removeTempLayers();
      
      // Reset cursor
      this.map.getTargetElement().style.cursor = '';
      
      // Re-enable parent's select interaction
      this.$emit('enable-select-interaction');
      
      // Reset state
      this.resetState();
    },

    createTempLayers() {
      // Point layer for showing selected points
      this.pointLayer = new VectorLayer({
        source: new VectorSource(),
        style: new Style({
          image: new CircleStyle({
            radius: 6,
            fill: new Fill({ color: 'rgba(255, 0, 0, 0.8)' }),
            stroke: new Stroke({ color: 'white', width: 2 })
          })
        }),
        zIndex: 100
      });
      
      // Line layer for showing the cut line
      this.lineLayer = new VectorLayer({
        source: new VectorSource(),
        style: new Style({
          stroke: new Stroke({
            color: 'rgba(255, 165, 0, 0.8)',
            width: 3,
            lineDash: [5, 5]
          })
        }),
        zIndex: 99
      });
      
      this.map.addLayer(this.pointLayer);
      this.map.addLayer(this.lineLayer);
    },

    removeTempLayers() {
      if (this.pointLayer) {
        this.map.removeLayer(this.pointLayer);
        this.pointLayer = null;
      }
      if (this.lineLayer) {
        this.map.removeLayer(this.lineLayer);
        this.lineLayer = null;
      }
    },

    resetState() {
      this.currentStep = 1;
      this.selectedPolygon = null;
      this.selectedPolygonId = null;
      this.selectedPolygonGeoJSON = null;
      this.point1 = null;
      this.point2 = null;
      this.errorMessage = null;
      
      // Clear temp layers
      if (this.pointLayer) {
        this.pointLayer.getSource().clear();
      }
      if (this.lineLayer) {
        this.lineLayer.getSource().clear();
      }
    },

    handleMapClick(event) {
      const coordinate = event.coordinate;
      console.log('Cut tool click at:', coordinate);
      
      switch (this.currentStep) {
        case 1:
          this.selectPolygon(coordinate);
          break;
        case 2:
          this.selectPoint1(coordinate);
          break;
        case 3:
          this.selectPoint2(coordinate);
          break;
      }
    },

    selectPolygon(coordinate) {
      // Check if layer3 exists and is visible
      if (!this.layer3 || !this.layer3.getVisible()) {
        this.errorMessage = 'Layer 3 (Processed) is not visible';
        return;
      }
      
      // Find feature at click location
      const feature = this.map.forEachFeatureAtPixel(
        this.map.getPixelFromCoordinate(coordinate),
        (feature, layer) => {
          return layer === this.layer3 ? feature : null;
        }
      );
      
      if (feature) {
        this.selectedPolygon = feature;
        
        // Extract polygon ID from various possible property names
        this.selectedPolygonId = feature.get('polygon_id') || 
                                feature.get('id') || 
                                feature.get('poly_id') ||
                                feature.get('fea_id') ||
                                'unknown';
        
        // Convert to GeoJSON for logging and cutting
        this.selectedPolygonGeoJSON = this.geoJSONFormat.writeFeatureObject(feature, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        });
        
        console.log('Selected polygon GeoJSON:', JSON.stringify(this.selectedPolygonGeoJSON));
        console.log('Selected polygon ID:', this.selectedPolygonId);
        
        // Highlight the selected polygon
        this.highlightSelectedPolygon();
        
        // Move to next step
        this.currentStep = 2;
        this.errorMessage = null;
      } else {
        this.errorMessage = 'No polygon selected. Click on a polygon from the Processed layer.';
      }
    },

    highlightSelectedPolygon() {
      if (this.selectedPolygon && this.layer3) {
        // Store original style
        const originalStyle = this.selectedPolygon.getStyle();
        this.selectedPolygon.set('_original_style', originalStyle);
        
        // Apply highlight style
        this.selectedPolygon.setStyle(this.highlightStyle);
      }
    },

    removeHighlight() {
      if (this.selectedPolygon) {
        // Restore original style
        const originalStyle = this.selectedPolygon.get('_original_style');
        if (originalStyle) {
          this.selectedPolygon.setStyle(originalStyle);
        } else {
          this.selectedPolygon.setStyle(null);
        }
        this.selectedPolygon.unset('_original_style');
      }
    },

    selectPoint1(coordinate) {
      this.point1 = coordinate;
      
      // Add point to point layer
      const pointFeature = new Feature({
        geometry: new Point(coordinate)
      });
      this.pointLayer.getSource().addFeature(pointFeature);
      
      console.log('Point 1 selected:', coordinate);
      
      // Move to next step
      this.currentStep = 3;
    },

    selectPoint2(coordinate) {
      this.point2 = coordinate;
      
      // Add second point
      const pointFeature = new Feature({
        geometry: new Point(coordinate)
      });
      this.pointLayer.getSource().addFeature(pointFeature);
      
      // Draw line between points
      this.drawCutLine();
      
      console.log('Point 2 selected:', coordinate);
      
      // Check if points are valid (not identical)
      if (this.point1[0] === this.point2[0] && this.point1[1] === this.point2[1]) {
        this.errorMessage = 'Points must be different';
      } else {
        this.errorMessage = null;
      }
    },

    drawCutLine() {
      if (!this.point1 || !this.point2) return;
      
      const lineFeature = new Feature({
        geometry: new LineString([this.point1, this.point2])
      });
      
      this.lineLayer.getSource().clear();
      this.lineLayer.getSource().addFeature(lineFeature);
    },

performCut() {
  if (!this.canCut) return;
  
  try {
    console.log('Performing cut operation with polygon-splitter...');
    
    // Get the polygon geometry
    const polygonGeometry = this.selectedPolygonGeoJSON.geometry;
    
    // Create the cut line
    const cutLine = {
      type: 'LineString',
      coordinates: [
        [this.point1[0], this.point1[1]],
        [this.point2[0], this.point2[1]]
      ]
    };
    
    console.log('Cut line:', cutLine);
    
    // Split the polygon
    const splitResult = polygonSplitter(polygonGeometry, cutLine);
    console.log('Raw split result:', splitResult);
    
    // Ensure we have an array of results
    let splitPolygons = [];
    
    if (Array.isArray(splitResult)) {
      splitPolygons = splitResult;
    } else if (splitResult && splitResult.geometry) {
      // If it's a Feature, extract the geometry
      splitPolygons = [splitResult.geometry];
    } else if (splitResult && splitResult.type === 'Feature') {
      splitPolygons = [splitResult.geometry];
    } else {
      splitPolygons = [splitResult];
    }
    
    console.log('Split polygons:', splitPolygons);
    
    if (splitPolygons.length === 0) {
      throw new Error('No split results generated');
    }
    
    // Convert split results to OpenLayers features
    const cutFeatures = [];
    const timestamp = Date.now();
    
    splitPolygons.forEach((geom, index) => {
      // Ensure we have a geometry object
      let geometry = geom;
      
      // If it's a Feature, extract geometry
      if (geom && geom.type === 'Feature') {
        geometry = geom.geometry;
      }
      
      // If geometry is still not valid, skip
      if (!geometry || !geometry.type || !geometry.coordinates) {
        console.warn('Invalid geometry:', geom);
        return;
      }
      
      const geoJSONFeature = {
        type: 'Feature',
        geometry: geometry,
        properties: { ...this.selectedPolygonGeoJSON.properties }
      };
      
      try {
        const feature = this.geoJSONFormat.readFeature(geoJSONFeature, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        });
        
        // Set unique ID
        const newId = `${this.selectedPolygonId}_cut_${index + 1}_${timestamp}`;
        feature.set('polygon_id', newId);
        feature.set('id', newId);
        feature.set('poly_id', newId);
        feature.set('original_polygon_id', this.selectedPolygonId);
        
        cutFeatures.push(feature);
      } catch (e) {
        console.warn('Error creating feature:', e, geoJSONFeature);
      }
    });
    
    console.log('Created cut features:', cutFeatures.length);
    
    if (cutFeatures.length === 0) {
      throw new Error('No valid cut features created');
    }
    
    // Update the layer
    const source = this.layer3.getSource();
    const allFeatures = source.getFeatures();
    const updatedFeatures = [];
    let originalFound = false;
    
    // Keep all features except the selected one
    for (const feature of allFeatures) {
      const featureId = feature.get('polygon_id') || 
                       feature.get('id') || 
                       feature.get('poly_id') ||
                       feature.get('fea_id');
      
      const featureIdStr = featureId ? featureId.toString() : '';
      const selectedIdStr = this.selectedPolygonId ? this.selectedPolygonId.toString() : '';
      
      if (featureIdStr === selectedIdStr) {
        console.log('Found original feature to replace');
        originalFound = true;
        continue;
      }
      updatedFeatures.push(feature);
    }
    
    // Add the new cut features
    updatedFeatures.push(...cutFeatures);
    
    console.log('Updating layer: kept', (updatedFeatures.length - cutFeatures.length), 
                'original features, added', cutFeatures.length, 'new cut features');
    
    // Update the layer
    source.clear();
    source.addFeatures(updatedFeatures);
    
    // Force a render
    this.layer3.changed();
    
    // Emit updated geometry to parent
    const updatedGeoJSON = {
      type: 'FeatureCollection',
      features: updatedFeatures.map(f => 
        this.geoJSONFormat.writeFeatureObject(f, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        })
      )
    };
    
    this.$emit('update-processed-geometry', updatedGeoJSON);
    
    // Refresh the map
    this.map.render();
    
    // Exit cut mode
    this.cancelCut();
    
  } catch (error) {
    console.error('Error performing cut:', error);
    this.errorMessage = `Cut failed: ${error.message}. Please try a different cut line.`;
  }
},

    cancelCut() {
      this.removeHighlight();
      this.removeTempLayers();
      this.isCutModeActive = false;
    },

    cleanup() {
      this.removeHighlight();
      this.removeTempLayers();
      if (this.clickHandler) {
        this.map.un('click', this.clickHandler);
      }
    }
  }
};
</script>


<style scoped>
/* Keep all the existing styles - they remain the same */
.cut-polygon-tool {
  position: relative;
}

.control-btn.cut-btn {
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

.control-btn.cut-btn:hover {
  background: #f5f5f5;
  transform: scale(1.05);
}

.control-btn.cut-btn.active {
  background: #007bff;
  color: white;
  border-color: #0056b3;
}

.cut-panel {
  position: absolute;
  top: 50px;
  right: 0;
  width: 300px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  z-index: 1000;
}

.cut-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 4px 4px 0 0;
}

.cut-panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #666;
  padding: 0 4px;
}

.close-btn:hover {
  color: #333;
}

.cut-panel-content {
  padding: 12px;
}

.instruction-steps {
  margin-bottom: 15px;
}

.step {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  margin: 4px 0;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #ccc;
}

.step.active {
  border-left-color: #007bff;
  background: #e7f1ff;
}

.step.completed {
  border-left-color: #28a745;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: #6c757d;
  color: white;
  border-radius: 50%;
  font-size: 11px;
  font-weight: bold;
  margin-right: 8px;
}

.step.active .step-number {
  background: #007bff;
}

.step.completed .step-number {
  background: #28a745;
}

.step-text {
  font-size: 12px;
  color: #495057;
  flex: 1;
}

.step-check {
  color: #28a745;
  font-weight: bold;
  margin-left: 8px;
}

.selected-polygon-info,
.point-info {
  background: #e7f1ff;
  padding: 8px 10px;
  border-radius: 4px;
  margin: 8px 0;
  font-size: 11px;
  word-break: break-all;
  border-left: 3px solid #007bff;
}

.point-info {
  background: #fff3cd;
  border-left-color: #ffc107;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 8px 10px;
  border-radius: 4px;
  margin: 8px 0;
  font-size: 11px;
  border-left: 3px solid #dc3545;
}

.cut-panel-actions {
  display: flex;
  gap: 8px;
  margin-top: 15px;
  border-top: 1px solid #eee;
  padding-top: 12px;
}

.cancel-btn,
.cut-action-btn {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn {
  background: #6c757d;
  color: white;
}

.cancel-btn:hover {
  background: #5a6268;
}

.cut-action-btn {
  background: #28a745;
  color: white;
}

.cut-action-btn:hover:not(:disabled) {
  background: #218838;
}

.cut-action-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
