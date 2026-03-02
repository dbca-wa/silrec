<template>
  <div class="merge-polygon-tool">
    <!-- Merge button (small icon) with toggle behavior -->
    <button
      v-if="hasLayer3"
      class="control-btn merge-btn"
      @click="toggleMergeMode"
      :class="{ active: isMergeModeActive }"
      :title="getButtonTitle"
    >
      <svg width="20" height="22" viewBox="0 0 24 24" fill="currentColor">
        <!-- Simple combine/merge icon (two overlapping squares) -->
        <path d="M8 5v14l11-7z"/>
        <rect x="4" y="4" width="10" height="10" rx="1" stroke="currentColor" fill="none" stroke-width="2"/>
        <rect x="10" y="10" width="10" height="10" rx="1" stroke="currentColor" fill="none" stroke-width="2"/>
      </svg>
    </button>

    <!-- Merge Tool Panel -->
    <div v-if="isMergeModeActive" class="merge-panel">
      <div class="merge-panel-header">
        <h3>Merge Polygons</h3>
        <button @click="cancelMerge" class="close-btn">×</button>
      </div>
      
      <div class="merge-panel-content">
        <!-- Step indicators - different for merge vs post-merge -->
        <div v-if="mergeStep < 2" class="two-column-layout">
          <!-- Left column: Step labels -->
          <div class="steps-column">
            <div class="step-row" :class="{ active: mergeStep === 1, completed: mergeSelectedFeatures.length >= 1 }">
              <div class="step-content">
                <span class="step-number">1</span>
                <span class="step-text">Select first polygon</span>
              </div>
              <span v-if="mergeSelectedFeatures.length >= 1" class="step-check">✓</span>
            </div>
            <div class="step-row" :class="{ active: mergeStep === 1, completed: mergeSelectedFeatures.length >= 2 }">
              <div class="step-content">
                <span class="step-number">2</span>
                <span class="step-text">Select second polygon</span>
              </div>
              <span v-if="mergeSelectedFeatures.length >= 2" class="step-check">✓</span>
            </div>
          </div>
          
          <!-- Right column: Values - aligned with steps -->
          <div class="values-column">
            <div class="value-row" :class="{ 'has-value': mergeSelectedFeatures[0] }">
              <span class="value-label">ID1:</span>
              <span class="value-content">{{ getPolygonId(mergeSelectedFeatures[0]) || '—' }}</span>
            </div>
            <div class="value-row" :class="{ 'has-value': mergeSelectedFeatures[1] }">
              <span class="value-label">ID2:</span>
              <span class="value-content">{{ getPolygonId(mergeSelectedFeatures[1]) || '—' }}</span>
            </div>
          </div>
        </div>

        <!-- Post-merge state (mergeStep === 2) - also use two columns -->
        <div v-if="mergeStep === 2" class="two-column-layout post-merge">
          <!-- Left column: Message with placeholders for alignment -->
          <div class="steps-column">
            <div class="step-row completed">
              <div class="step-content">
                <span class="step-number">✓</span>
                <span class="step-text">Merge completed</span>
              </div>
            </div>
            <div class="step-row placeholder"></div>
          </div>
          
          <!-- Right column: Values - aligned with steps -->
          <div class="values-column">
            <div class="value-row has-value">
              <span class="value-label">ID:</span>
              <span class="value-content">{{ mergedFeatureId || '—' }}</span>
            </div>
            <div class="value-row has-value">
              <span class="value-label">Area:</span>
              <span class="value-content">{{ mergedArea ? mergedArea.toFixed(2) + ' ha' : '—' }}</span>
            </div>
          </div>
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <div class="merge-panel-actions">
          <!-- Different buttons based on merge step -->
          <template v-if="mergeStep < 2">
            <button 
              class="cancel-btn"
              @click="cancelMerge"
            >
              Cancel
            </button>
            <button 
              class="merge-action-btn"
              :disabled="!canMerge"
              @click="performMerge"
            >
              Merge Polygons
            </button>
          </template>

          <template v-else-if="mergeStep === 2">
            <div class="undo-redo-group">
              <button 
                class="undo-btn"
                @click="undoMerge"
                :disabled="!canUndo"
                :title="canUndo ? 'Undo merge' : 'Nothing to undo'"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/>
                </svg>
                <span>Undo</span>
              </button>
              <button 
                class="redo-btn"
                @click="redoMerge"
                :disabled="!canRedo"
                :title="canRedo ? 'Redo merge' : 'Nothing to redo'"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.4 10.6C16.55 8.99 14.15 8 11.5 8c-4.65 0-8.58 3.03-9.96 7.22L3.9 16c1.05-3.19 4.05-5.5 7.6-5.5 1.96 0 3.73.72 5.12 1.88L12.5 16h9V7l-3.1 3.6z"/>
                </svg>
                <span>Redo</span>
              </button>
            </div>
            <button 
              class="save-btn"
              @click="saveMerge"
            >
              Save
            </button>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as turf from '@turf/turf';
import { Style, Fill, Stroke } from 'ol/style';
import GeoJSON from 'ol/format/GeoJSON';
import { helpers } from '@/utils/hooks';
import Feature from 'ol/Feature';

export default {
  name: 'MergePolygonTool',
  props: {
    map: { type: Object, required: true },
    layer3: { type: Object, required: true },
    hasLayer3: { type: Boolean, default: false },
    proposalId: { type: [Number, String], required: true },
    highlightStyle: { type: Object, required: true }
  },
  emits: [
    'update-processed-geometry', 
    'disable-select-interaction', 
    'enable-select-interaction',
    'clear-selection'
  ],
  data() {
    return {
      isMergeModeActive: false,
      mergeStep: 0, // 0: initial, 1: selecting polygons, 2: merge completed
      mergeSelectedFeatures: [],
      errorMessage: null,
      
      // History for undo/redo
      history: [],          // Array of states (each state is a features array)
      currentHistoryIndex: -1,
      
      // Track the currently highlighted polygons
      highlightedPolygons: [],
      
      // Track the merged polygon separately (for green highlight)
      mergedPolygon: null,
      
      // Track the currently selected polygon IDs for reference after undo/redo
      selectedPolygonIds: [],
      
      // Backup for original polygons
      backupFeatures: null,
      mergedFeatureId: null,
      mergedArea: null,
      
      // Click handler reference
      mergeClickHandler: null,
      
      // Format for GeoJSON conversion
      geoJSONFormat: new GeoJSON()
    };
  },
  computed: {
    getButtonTitle() {
      return this.isMergeModeActive ? 'Exit Merge Mode' : 'Merge Polygons Tool';
    },
    canMerge() {
      return this.mergeSelectedFeatures.length === 2 && !this.errorMessage;
    },
    canUndo() {
      return this.currentHistoryIndex > 0;
    },
    canRedo() {
      return this.currentHistoryIndex < this.history.length - 1;
    }
  },
  watch: {
    isMergeModeActive(active) {
      if (active) {
        this.activateMergeMode();
      } else {
        this.deactivateMergeMode();
      }
    }
  },
  beforeDestroy() {
    this.cleanup();
  },
  methods: {
    toggleMergeMode() {
      this.isMergeModeActive = !this.isMergeModeActive;
    },

    activateMergeMode() {
      console.log('Merge mode activated');
      
      // Disable parent's select interaction
      this.$emit('disable-select-interaction');
      
      // Set up click handler
      this.mergeClickHandler = this.handleMapClick.bind(this);
      this.map.on('click', this.mergeClickHandler);
      
      // Change cursor style
      this.map.getTargetElement().style.cursor = 'crosshair';
      
      // Reset state
      this.resetState();
    },

    deactivateMergeMode() {
      console.log('Merge mode deactivated');
      
      // Remove click handler
      if (this.mergeClickHandler) {
        this.map.un('click', this.mergeClickHandler);
        this.mergeClickHandler = null;
      }
      
      // Reset cursor
      this.map.getTargetElement().style.cursor = '';
      
      // Force remove all highlights and refresh map
      this.forceRemoveAllHighlightsAndRefresh();
      
      // Clear any selected feature from the map's select interaction
      this.clearMapSelection();
      
      // Re-enable parent's select interaction
      this.$emit('enable-select-interaction');
      
      // Reset state
      this.resetState();
    },

    resetState() {
      this.mergeStep = 0;
      this.mergeSelectedFeatures = [];
      this.selectedPolygonIds = [];
      this.highlightedPolygons = [];
      this.mergedPolygon = null;
      this.errorMessage = null;
      this.backupFeatures = null;
      this.mergedFeatureId = null;
      this.mergedArea = null;
      
      // Clear history
      this.history = [];
      this.currentHistoryIndex = -1;
    },

    handleMapClick(event) {
      if (this.mergeStep === 2) return; // Don't handle clicks in post-merge state
      
      const pixel = this.map.getEventPixel(event.originalEvent);
      const feature = this.map.forEachFeatureAtPixel(pixel, (feature, layer) => {
        if (layer === this.layer3) return feature;
        return null;
      });

      if (feature) {
        this.handleMergeClick(feature);
      }
    },

    handleMergeClick(feature) {
      // Check if layer3 exists and is visible
      if (!this.layer3 || !this.layer3.getVisible()) {
        this.errorMessage = 'Layer 3 (Processed) is not visible';
        return;
      }
      
      const featureId = this.getPolygonId(feature);
      const index = this.mergeSelectedFeatures.findIndex(f => f === feature);
      
      if (index !== -1) {
        // Deselect the feature
        this.mergeSelectedFeatures.splice(index, 1);
        this.selectedPolygonIds.splice(index, 1);
        this.removeHighlightFromPolygon(feature);
      } else {
        // Select the feature if less than 2 are selected
        if (this.mergeSelectedFeatures.length < 2) {
          this.mergeSelectedFeatures.push(feature);
          this.selectedPolygonIds.push(featureId);
          this.highlightPolygon(feature);
          
          // Move to merge step 1 if we have at least one polygon
          this.mergeStep = 1;
        } else {
          this.errorMessage = 'You can only select two polygons. Deselect one first.';
        }
      }
      
      // Clear error if we have valid selection
      if (this.mergeSelectedFeatures.length === 2) {
        this.errorMessage = null;
      }
      
      this.map.render();
    },

    highlightPolygon(feature) {
      if (feature && this.layer3) {
        // Store original style
        const originalStyle = feature.getStyle();
        feature.set('_original_style', originalStyle);
        
        // Apply highlight style
        feature.setStyle(this.highlightStyle);
        
        // Track highlighted polygon
        this.highlightedPolygons.push(feature);
      }
    },

    removeHighlightFromPolygon(feature) {
      if (feature && this.layer3) {
        // Restore original style
        const originalStyle = feature.get('_original_style');
        if (originalStyle) {
          feature.setStyle(originalStyle);
        } else {
          feature.setStyle(null);
        }
        
        // Remove the stored style property
        feature.unset('_original_style');
        
        // Force a style update
        feature.changed();
        
        // Remove from tracked highlights
        const idx = this.highlightedPolygons.findIndex(f => f === feature);
        if (idx !== -1) {
          this.highlightedPolygons.splice(idx, 1);
        }
      }
    },

    removeHighlights() {
      console.log('Removing all highlights, count:', this.highlightedPolygons.length);
      
      // Remove highlight from all tracked polygons
      this.highlightedPolygons.forEach(feature => {
        if (feature && this.layer3) {
          const originalStyle = feature.get('_original_style');
          if (originalStyle) {
            feature.setStyle(originalStyle);
          } else {
            feature.setStyle(null);
          }
          feature.unset('_original_style');
          feature.changed();
        }
      });
      this.highlightedPolygons = [];
      
      // Also check selected features
      this.mergeSelectedFeatures.forEach(feature => {
        if (feature && this.layer3) {
          const originalStyle = feature.get('_original_style');
          if (originalStyle) {
            feature.setStyle(originalStyle);
          } else {
            feature.setStyle(null);
          }
          feature.unset('_original_style');
          feature.changed();
        }
      });
    },

    forceRemoveAllHighlightsAndRefresh() {
      console.log('Force removing all highlights and refreshing map');
      
      if (!this.layer3 || !this.map) return;
      
      const source = this.layer3.getSource();
      const features = source.getFeatures();
      
      // First, store all features
      const featuresCopy = features.map(f => {
        // Create a plain object representation for later
        const props = f.getProperties();
        const geometry = f.getGeometry();
        return { props, geometry };
      });
      
      // Completely clear the layer
      source.clear();
      
      // Re-add all features with NO styles
      featuresCopy.forEach(({ props, geometry }) => {
        const newFeature = new Feature({
          geometry: geometry.clone()
        });
        
        // Copy all properties except style-related ones
        Object.keys(props).forEach(key => {
          if (key !== '_original_style' && key !== 'geometry') {
            newFeature.set(key, props[key]);
          }
        });
        
        // Ensure no style is set
        newFeature.setStyle(null);
        source.addFeature(newFeature);
      });
      
      // Force multiple renders and updates
      this.layer3.changed();
      this.map.render();
      this.map.updateSize();
      
      // Do a second render after a tiny delay
      setTimeout(() => {
        this.layer3.changed();
        this.map.render();
        
        // Also trigger a view change and change back to force redraw
        const view = this.map.getView();
        const center = view.getCenter();
        const zoom = view.getZoom();
        view.setZoom(zoom + 0.01);
        setTimeout(() => {
          view.setZoom(zoom);
          this.map.render();
        }, 10);
      }, 10);
      
      // Clear tracking arrays
      this.highlightedPolygons = [];
      this.mergedPolygon = null;
    },

    removeMergedPolygonHighlight() {
      console.log('Removing merged polygon highlight');
      
      if (this.mergedPolygon && this.layer3) {
        this.mergedPolygon.setStyle(null);
        this.mergedPolygon.changed();
        this.mergedPolygon = null;
      }
      
      // Also try to find any polygon with mergeId and reset its style
      if (this.layer3 && this.mergedFeatureId) {
        const source = this.layer3.getSource();
        const features = source.getFeatures();
        const mergedPolygon = features.find(f => f.get('mergeId') === this.mergedFeatureId);
        
        if (mergedPolygon) {
          mergedPolygon.setStyle(null);
          mergedPolygon.changed();
        }
      }
    },

    getPolygonId(feature) {
      if (!feature) return null;
      return feature.get('polygon_id') || 
             feature.get('id') || 
             feature.get('poly_id') ||
             feature.get('fea_id') ||
             'unknown';
    },

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

    // Save current state to history
    saveStateToHistory(features) {
      // Create a deep copy of features for history
      const featuresCopy = features.map(f => {
        const cloned = f.clone();
        // Copy over any important properties that clone might miss
        const props = f.getProperties();
        Object.keys(props).forEach(key => {
          if (key !== 'geometry') {
            cloned.set(key, props[key]);
          }
        });
        return cloned;
      });
      
      // Trim history if we're not at the end
      if (this.currentHistoryIndex < this.history.length - 1) {
        this.history = this.history.slice(0, this.currentHistoryIndex + 1);
      }
      
      this.history.push(featuresCopy);
      this.currentHistoryIndex = this.history.length - 1;
      
      console.log(`History saved. Index: ${this.currentHistoryIndex}, Length: ${this.history.length}`);
      
      // Force computed properties to update
      this.$forceUpdate();
    },

    // Apply a state from history
    applyStateFromHistory(index) {
      if (index < 0 || index >= this.history.length) return;
      
      const stateFeatures = this.history[index];
      
      // Clear current layer
      const source = this.layer3.getSource();
      source.clear();
      
      // Add features from history state
      const featuresToAdd = stateFeatures.map(f => f.clone());
      source.addFeatures(featuresToAdd);
      
      // Update current history index
      this.currentHistoryIndex = index;
      
      // Force render
      this.layer3.changed();
      this.map.render();
      
      // Emit updated geometry to parent
      const updatedGeoJSON = {
        type: 'FeatureCollection',
        features: featuresToAdd.map(f => 
          this.geoJSONFormat.writeFeatureObject(f, {
            featureProjection: 'EPSG:4326',
            dataProjection: 'EPSG:4326'
          })
        )
      };
      
      this.$emit('update-processed-geometry', updatedGeoJSON);
      
      console.log(`Applied history index: ${index}`);
    },

    // Clear any selected feature from the map
    clearMapSelection() {
      console.log('Clearing map selection');
      
      // Emit event to parent to clear its selection
      this.$emit('clear-selection');
      
      // Also try to clear any select interactions directly
      if (this.map) {
        this.map.getInteractions().forEach(interaction => {
          if (interaction.constructor.name === 'Select') {
            console.log('Found select interaction, clearing features');
            interaction.getFeatures().clear();
          }
        });
        
        // Force a render
        this.map.render();
      }
    },

    // Force a complete map refresh
    forceMapRefresh() {
      if (this.map) {
        console.log('Forcing complete map refresh');
        
        // Update all layer sources
        if (this.layer3) {
          this.layer3.getSource().changed();
          this.layer3.changed();
        }
        
        // Force map to re-render
        this.map.render();
        this.map.updateSize();
        
        // Also update the view slightly to force a redraw
        const view = this.map.getView();
        const center = view.getCenter();
        const zoom = view.getZoom();
        view.setZoom(zoom + 0.01);
        setTimeout(() => {
          view.setZoom(zoom);
          this.map.render();
        }, 10);
      }
    },

    async performMerge() {
      if (!this.canMerge) return;
      
      try {
        console.log('Performing merge operation...');
        
        const feature1 = this.mergeSelectedFeatures[0];
        const feature2 = this.mergeSelectedFeatures[1];
        
        const format = new GeoJSON();
        const geojson1 = format.writeFeatureObject(feature1, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        });
        const geojson2 = format.writeFeatureObject(feature2, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        });

        const closed1 = this.closePolygon(geojson1);
        const closed2 = this.closePolygon(geojson2);

        const cleaned1 = turf.cleanCoords(closed1);
        const cleaned2 = turf.cleanCoords(closed2);

        const rewound1 = turf.rewind(cleaned1, { mutate: true });
        const rewound2 = turf.rewind(cleaned2, { mutate: true });

        if (!rewound1.geometry || !rewound2.geometry) {
          throw new Error('Invalid polygon geometry');
        }
        if (rewound1.geometry.type !== 'Polygon' || rewound2.geometry.type !== 'Polygon') {
          throw new Error('Selected features are not polygons');
        }

        const featureCollection = turf.featureCollection([rewound1, rewound2]);
        const union = turf.union(featureCollection);
        if (!union || union.geometry.type !== 'Polygon') {
          throw new Error('Merge result would be a MultiPolygon');
        }

        const cleanedUnion = turf.buffer(union, 0);
        if (!cleanedUnion || cleanedUnion.geometry.type !== 'Polygon') {
          throw new Error('Cleaned union is not a polygon');
        }

        const simplified = turf.simplify(cleanedUnion, { tolerance: 0.00001, highQuality: false });
        const areaHa = turf.area(simplified) / 10000;
        this.mergedArea = areaHa;

        const source = this.layer3.getSource();
        const currentFeatures = source.getFeatures();

        // Save backup for undo/redo
        this.backupFeatures = {
          f1: feature1.clone(),
          f2: feature2.clone(),
          originalIds: [this.getPolygonId(feature1), this.getPolygonId(feature2)]
        };

        // Create merged feature
        const newGeometry = format.readGeometry(simplified.geometry, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        });
        
        // Create merged ID
        const mergedId = 'merged_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        this.mergedFeatureId = mergedId;

        // Create updated features array (remove the two original polygons, add merged one)
        const updatedFeatures = currentFeatures.filter(f => 
          f !== feature1 && f !== feature2
        );

        // Create the merged feature with properties from first polygon
        const mergedProps = { ...feature1.getProperties() };
        delete mergedProps.geometry;
        
        const mergedFeature = new Feature({
          geometry: newGeometry
        });
        
        // Set properties
        Object.keys(mergedProps).forEach(key => {
          if (key !== '_original_style') {
            mergedFeature.set(key, mergedProps[key]);
          }
        });
        
        mergedFeature.set('area_ha', areaHa);
        mergedFeature.set('merged', true);
        mergedFeature.set('mergeId', mergedId);
        mergedFeature.set('polygon_id', mergedId);
        mergedFeature.set('id', mergedId);
        
        // Apply a temporary style to highlight the merged polygon
        mergedFeature.setStyle(new Style({
          fill: new Fill({ color: 'rgba(0, 255, 0, 0.5)' }),
          stroke: new Stroke({ color: 'rgba(0, 0, 0, 1)', width: 3 })
        }));

        updatedFeatures.push(mergedFeature);

        // Save state to history
        this.saveStateToHistory(currentFeatures);  // Original state
        this.saveStateToHistory(updatedFeatures);  // Merged state

        // Update the layer
        source.clear();
        source.addFeatures(updatedFeatures);
        
        // Remove highlights from selected polygons
        this.removeHighlights();
        
        // Store reference to merged polygon for later cleanup
        this.mergedPolygon = mergedFeature;
        
        // Force render
        this.layer3.changed();
        this.map.render();

        // Zoom to merged polygon
        const mergedExtent = mergedFeature.getGeometry().getExtent();
        this.map.getView().fit(mergedExtent, { padding: [50, 50, 50, 50], duration: 500 });

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

        // Move to post-merge state
        this.mergeStep = 2;
        
        // Clear selected features
        this.mergeSelectedFeatures = [];
        this.selectedPolygonIds = [];

      } catch (error) {
        console.error('Error performing merge:', error);
        this.errorMessage = `Merge failed: ${error.message}`;
      }
    },

    undoMerge() {
      if (!this.canUndo) return;
      
      console.log('Undo merge');
      
      // Remove highlights before applying history state
      this.removeHighlights();
      
      // Remove merged polygon highlight
      this.removeMergedPolygonHighlight();
      
      // Apply the previous state from history
      this.applyStateFromHistory(this.currentHistoryIndex - 1);
      
      // After undo, find and highlight the original polygons
      setTimeout(() => {
        const source = this.layer3.getSource();
        const features = source.getFeatures();
        
        // Clear any existing highlights
        this.highlightedPolygons = [];
        
        if (this.backupFeatures && this.backupFeatures.originalIds) {
          console.log('Found backup IDs:', this.backupFeatures.originalIds);
          
          // Find and highlight the original polygons
          const originalPolygons = features.filter(f => {
            const id = this.getPolygonId(f);
            return id && this.backupFeatures.originalIds.includes(id);
          });
          
          console.log('Found original polygons to highlight:', originalPolygons.length);
          
          originalPolygons.forEach(polygon => {
            // Store original style
            const originalStyle = polygon.getStyle();
            polygon.set('_original_style', originalStyle);
            
            // Apply highlight style
            polygon.setStyle(this.highlightStyle);
            
            // Track highlighted polygon
            this.highlightedPolygons.push(polygon);
          });
        }
        
        // Clear merged references
        this.mergedFeatureId = null;
        this.mergedArea = null;
        this.mergedPolygon = null;
        
        // Force a map render
        this.map.render();
      }, 50);
    },

    redoMerge() {
      if (!this.canRedo) return;
      
      console.log('Redo merge');
      
      // Remove highlights before applying history state
      this.removeHighlights();
      
      // Remove merged polygon highlight
      this.removeMergedPolygonHighlight();
      
      // Apply the next state from history
      this.applyStateFromHistory(this.currentHistoryIndex + 1);
      
      // After redo, find and highlight the merged polygon
      setTimeout(() => {
        const source = this.layer3.getSource();
        const features = source.getFeatures();
        
        // Clear any existing highlights
        this.highlightedPolygons = [];
        
        // Find the merged polygon
        const mergedPolygon = features.find(f => f.get('mergeId') === this.mergedFeatureId);
        
        if (mergedPolygon) {
          console.log('Found merged polygon to highlight');
          
          // Clear any selected features
          this.mergeSelectedFeatures = [];
          this.selectedPolygonIds = [];
          
          // Store reference and highlight the merged polygon
          this.mergedPolygon = mergedPolygon;
          mergedPolygon.setStyle(new Style({
            fill: new Fill({ color: 'rgba(0, 255, 0, 0.5)' }),
            stroke: new Stroke({ color: 'rgba(0, 0, 0, 1)', width: 3 })
          }));
        }
        
        // Force a map render
        this.map.render();
      }, 50);
    },

    saveMerge() {
      console.log('Saving merge operation');
      
      if (!this.proposalId) {
        this.errorMessage = 'No proposal ID available';
        return;
      }
      
      // Get the current state from the layer
      const source = this.layer3.getSource();
      const allFeatures = source.getFeatures();
      
      // Build the updated GeoJSON
      const updatedGeoJSON = {
        type: 'FeatureCollection',
        features: allFeatures.map(f => 
          this.geoJSONFormat.writeFeatureObject(f, {
            featureProjection: 'EPSG:4326',
            dataProjection: 'EPSG:4326'
          })
        )
      };

      fetch(`/api/proposal/${this.proposalId}/save_merged_geometry/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': helpers.getCookie('csrftoken')
        },
        body: JSON.stringify({
          updated_geojson: updatedGeoJSON,
          original_polygon_ids: this.backupFeatures ? this.backupFeatures.originalIds : [],
          merged_polygon_id: this.mergedFeatureId
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          console.log('Merge saved successfully');
          alert('Merged geometry saved successfully.');
          this.cancelMerge();
        } else {
          this.errorMessage = data.error || 'Failed to save merged geometry';
          alert('Save failed: ' + data.error);
        }
      })
      .catch(err => {
        console.error(err);
        this.errorMessage = 'Error saving: ' + err.message;
        alert('Error saving.');
      });
    },

    cancelMerge() {
      console.log('Cancelling merge mode');
      
      // Force remove all highlights and refresh map
      this.forceRemoveAllHighlightsAndRefresh();
      
      // Clear any selected feature from the map's select interaction
      this.clearMapSelection();
      
      // Force a complete map refresh multiple times
      setTimeout(() => {
        this.forceMapRefresh();
      }, 50);
      
      setTimeout(() => {
        this.forceMapRefresh();
      }, 150);
      
      // Exit merge mode
      this.isMergeModeActive = false;
    },

    cleanup() {
      this.forceRemoveAllHighlightsAndRefresh();
      if (this.mergeClickHandler) {
        this.map.un('click', this.mergeClickHandler);
      }
    }
  }
};
</script>

<style scoped>
.merge-polygon-tool {
  position: relative;
}

.control-btn.merge-btn {
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

.control-btn.merge-btn:hover {
  background: #f5f5f5;
  transform: scale(1.05);
}

.control-btn.merge-btn.active {
  background: #007bff;
  color: white;
  border-color: #0056b3;
}

.merge-panel {
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

.merge-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
  border-radius: 4px 4px 0 0;
}

.merge-panel-header h3 {
  margin: 0;
  font-size: 13px;
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
  line-height: 1;
}

.close-btn:hover {
  color: #333;
}

.merge-panel-content {
  padding: 10px;
}

/* Two-column layout */
.two-column-layout {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.steps-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.values-column {
  flex: 1;
  min-width: 0;
  background: #f8f9fa;
  border-radius: 4px;
  padding: 4px 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Step rows - exactly matching height with value rows */
.step-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 6px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #ccc;
  height: 28px;
  box-sizing: border-box;
}

.step-row.active {
  border-left-color: #007bff;
  background: #e7f1ff;
}

.step-row.completed {
  border-left-color: #28a745;
}

.step-row.placeholder {
  background: transparent;
  border-left-color: transparent;
  visibility: hidden;
}

.step-content {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}

/* Value rows - fixed height to match step rows */
.value-row {
  display: flex;
  align-items: center;
  padding: 4px 6px;
  font-size: 10px;
  border-bottom: 1px dashed #e9ecef;
  height: 28px;
  box-sizing: border-box;
}

.value-row:last-child {
  border-bottom: none;
}

.value-label {
  font-weight: 600;
  color: #495057;
  width: 32px;
  flex-shrink: 0;
}

.value-content {
  color: #212529;
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.value-row.has-value .value-content {
  color: #007bff;
  font-weight: 500;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: #6c757d;
  color: white;
  border-radius: 50%;
  font-size: 10px;
  font-weight: bold;
  flex-shrink: 0;
}

.step-row.active .step-number {
  background: #007bff;
}

.step-row.completed .step-number {
  background: #28a745;
}

.step-text {
  font-size: 11px;
  color: #495057;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-check {
  color: #28a745;
  font-weight: bold;
  font-size: 11px;
  flex-shrink: 0;
  margin-left: 4px;
}

/* Post-merge specific */
.post-merge .step-row.completed .step-number {
  background: #28a745;
  font-size: 12px;
  line-height: 1;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 6px 8px;
  border-radius: 4px;
  margin: 4px 0;
  font-size: 10px;
  border-left: 3px solid #dc3545;
  line-height: 1.3;
}

.merge-panel-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
  border-top: 1px solid #eee;
  padding-top: 8px;
}

.undo-redo-group {
  display: flex;
  gap: 6px;
  width: 100%;
}

.undo-btn,
.redo-btn,
.cancel-btn,
.merge-action-btn,
.save-btn {
  flex: 1;
  padding: 6px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  line-height: 1.2;
}

.undo-btn svg,
.redo-btn svg,
.save-btn svg {
  width: 14px;
  height: 14px;
}

.undo-btn:disabled,
.redo-btn:disabled {
  background: #e9ecef;
  color: #adb5bd;
  cursor: not-allowed;
  opacity: 0.7;
}

.undo-btn:disabled:hover,
.redo-btn:disabled:hover {
  background: #e9ecef;
  transform: none;
}

.undo-btn {
  background: #6c757d;
  color: white;
}

.undo-btn:hover:not(:disabled) {
  background: #5a6268;
}

.redo-btn {
  background: #6c757d;
  color: white;
}

.redo-btn:hover:not(:disabled) {
  background: #5a6268;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  width: 100%;
}

.cancel-btn:hover {
  background: #5a6268;
}

.merge-action-btn {
  background: #28a745;
  color: white;
  width: 100%;
}

.merge-action-btn:hover:not(:disabled) {
  background: #218838;
}

.merge-action-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.save-btn {
  background: #007bff;
  color: white;
  width: 100%;
}

.save-btn:hover {
  background: #0069d9;
}
</style>
