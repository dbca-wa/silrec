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
                <path
                    d="M9.64 7.64c.23-.5.36-1.05.36-1.64 0-2.21-1.79-4-4-4S2 3.79 2 6s1.79 4 4 4c.59 0 1.14-.13 1.64-.36L10 12l-2.36 2.36C7.14 14.13 6.59 14 6 14c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4c0-.59-.13-1.14-.36-1.64L12 14l7 7h3v-1L9.64 7.64zM6 8c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm0 12c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm6-7.5c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zM19 3l-6 6 2 2 7-7V3z"
                />
            </svg>
        </button>

        <!-- Cut Tool Panel -->
        <div v-if="isCutModeActive" class="cut-panel">
            <div class="cut-panel-header">
                <h3>Cut Polygon</h3>
                <button @click="cancelCut" class="close-btn">×</button>
            </div>

            <div class="cut-panel-content">
                <!-- Step indicators - different for cut vs post-cut -->
                <div v-if="cutStep < 2" class="two-column-layout">
                    <!-- Left column: Step labels -->
                    <div class="steps-column">
                        <div
                            class="step-row"
                            :class="{
                                active: currentStep === 1,
                                completed: selectedPolygon,
                            }"
                        >
                            <div class="step-content">
                                <span class="step-number">1</span>
                                <span class="step-text">Select polygon</span>
                            </div>
                            <span v-if="selectedPolygon" class="step-check"
                                >✓</span
                            >
                        </div>
                        <div
                            class="step-row"
                            :class="{
                                active: currentStep === 2,
                                completed: point1,
                            }"
                        >
                            <div class="step-content">
                                <span class="step-number">2</span>
                                <span class="step-text">First point</span>
                            </div>
                            <span v-if="point1" class="step-check">✓</span>
                        </div>
                        <div
                            class="step-row"
                            :class="{
                                active: currentStep === 3,
                                completed: point2,
                            }"
                        >
                            <div class="step-content">
                                <span class="step-number">3</span>
                                <span class="step-text">Second point</span>
                            </div>
                            <span v-if="point2" class="step-check">✓</span>
                        </div>
                    </div>

                    <!-- Right column: Values - aligned with steps -->
                    <div class="values-column">
                        <div
                            class="value-row"
                            :class="{ 'has-value': selectedPolygonId }"
                        >
                            <span class="value-label">ID:</span>
                            <span class="value-content">{{
                                selectedPolygonId || '—'
                            }}</span>
                        </div>
                        <div class="value-row" :class="{ 'has-value': point1 }">
                            <span class="value-label">P1:</span>
                            <span class="value-content">{{
                                point1
                                    ? `[${point1[0].toFixed(4)}, ${point1[1].toFixed(4)}]`
                                    : '—'
                            }}</span>
                        </div>
                        <div class="value-row" :class="{ 'has-value': point2 }">
                            <span class="value-label">P2:</span>
                            <span class="value-content">{{
                                point2
                                    ? `[${point2[0].toFixed(4)}, ${point2[1].toFixed(4)}]`
                                    : '—'
                            }}</span>
                        </div>
                    </div>
                </div>

                <!-- Post-cut state (cutStep === 2) - also use two columns -->
                <div v-if="cutStep === 2" class="two-column-layout post-cut">
                    <!-- Left column: Message with placeholders for alignment -->
                    <div class="steps-column">
                        <div class="step-row completed">
                            <div class="step-content">
                                <span class="step-number">✓</span>
                                <span class="step-text">Cut completed</span>
                            </div>
                        </div>
                        <div class="step-row placeholder"></div>
                        <div class="step-row placeholder"></div>
                    </div>

                    <!-- Right column: Values - aligned with steps -->
                    <div class="values-column">
                        <div class="value-row has-value">
                            <span class="value-label">ID:</span>
                            <span class="value-content">{{
                                selectedPolygonId
                            }}</span>
                        </div>
                        <div class="value-row has-value">
                            <span class="value-label">P1:</span>
                            <span class="value-content"
                                >[{{ point1[0].toFixed(4) }},
                                {{ point1[1].toFixed(4) }}]</span
                            >
                        </div>
                        <div class="value-row has-value">
                            <span class="value-label">P2:</span>
                            <span class="value-content"
                                >[{{ point2[0].toFixed(4) }},
                                {{ point2[1].toFixed(4) }}]</span
                            >
                        </div>
                    </div>
                </div>

                <div v-if="errorMessage" class="error-message">
                    {{ errorMessage }}
                </div>

                <div class="cut-panel-actions">
                    <!-- Different buttons based on cut step -->
                    <template v-if="cutStep < 2">
                        <button class="cancel-btn" @click="cancelCut">
                            Cancel
                        </button>
                        <button
                            class="cut-action-btn"
                            :disabled="!canCut"
                            @click="performCut"
                        >
                            Cut Polygon
                        </button>
                    </template>

                    <template v-else-if="cutStep === 2">
                        <div class="undo-redo-group">
                            <button
                                class="undo-btn"
                                @click="undoCut"
                                :disabled="!canUndo"
                                :title="
                                    canUndo ? 'Undo cut' : 'Nothing to undo'
                                "
                            >
                                <svg
                                    width="14"
                                    height="14"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                >
                                    <path
                                        d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"
                                    />
                                </svg>
                                <span>Undo</span>
                            </button>
                            <button
                                class="redo-btn"
                                @click="redoCut"
                                :disabled="!canRedo"
                                :title="
                                    canRedo ? 'Redo cut' : 'Nothing to redo'
                                "
                            >
                                <svg
                                    width="14"
                                    height="14"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                >
                                    <path
                                        d="M18.4 10.6C16.55 8.99 14.15 8 11.5 8c-4.65 0-8.58 3.03-9.96 7.22L3.9 16c1.05-3.19 4.05-5.5 7.6-5.5 1.96 0 3.73.72 5.12 1.88L12.5 16h9V7l-3.1 3.6z"
                                    />
                                </svg>
                                <span>Redo</span>
                            </button>
                        </div>
                        <button class="save-btn" @click="saveCut">Save</button>
                    </template>
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
import { helpers } from '@/utils/hooks';

export default {
    name: 'CutPolygonTool',
    props: {
        map: {
            type: Object,
            required: true,
        },
        layer3: {
            type: Object,
            required: true,
        },
        hasLayer3: {
            type: Boolean,
            default: false,
        },
        proposalId: {
            type: [Number, String],
            default: null,
        },
        highlightStyle: {
            type: Object,
            default: () =>
                new Style({
                    fill: new Fill({ color: 'rgba(255, 255, 0, 0.6)' }),
                    stroke: new Stroke({
                        color: 'rgba(255, 255, 0, 1)',
                        width: 3,
                    }),
                }),
        },
    },
    emits: [
        'update-processed-geometry',
        'disable-select-interaction',
        'enable-select-interaction',
        'clear-selection',
    ],
    data() {
        return {
            isCutModeActive: false,
            cutStep: 0, // 0: initial, 1: cutting in progress, 2: cut completed
            currentStep: 1,
            selectedPolygon: null,
            selectedPolygonId: null,
            selectedPolygonGeoJSON: null,
            point1: null,
            point2: null,
            errorMessage: null,

            // History for undo/redo
            history: [], // Array of states (each state is a features array)
            currentHistoryIndex: -1,

            // Track the currently highlighted polygon (may be different from selectedPolygon after undo)
            highlightedPolygon: null,

            // Backup for original polygon
            backupOriginalPolygon: null,
            backupOriginalPolygonId: null,

            // Cut result features
            cutFeatures: [],
            cutTimestamp: null,

            // Temporary layers for visualization
            pointLayer: null,
            lineLayer: null,

            // Click handler reference
            clickHandler: null,

            // Format for GeoJSON conversion
            geoJSONFormat: new GeoJSON(),
        };
    },
    computed: {
        getButtonTitle() {
            return this.isCutModeActive ? 'Exit Cut Mode' : 'Cut Polygon Tool';
        },
        canCut() {
            return (
                this.selectedPolygon &&
                this.point1 &&
                this.point2 &&
                !this.errorMessage
            );
        },
        canUndo() {
            return this.currentHistoryIndex > 0;
        },
        canRedo() {
            return this.currentHistoryIndex < this.history.length - 1;
        },
    },
    watch: {
        isCutModeActive(active) {
            if (active) {
                this.activateCutMode();
            } else {
                this.deactivateCutMode();
            }
        },
    },
    beforeUnmount() {
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

            // Remove highlight from any highlighted polygon
            this.removeHighlight();

            // Clear any selected feature from the map's select interaction
            this.clearMapSelection();

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
                        stroke: new Stroke({ color: 'white', width: 2 }),
                    }),
                }),
                zIndex: 100,
            });

            // Line layer for showing the cut line
            this.lineLayer = new VectorLayer({
                source: new VectorSource(),
                style: new Style({
                    stroke: new Stroke({
                        color: 'rgba(255, 165, 0, 0.8)',
                        width: 3,
                        lineDash: [5, 5],
                    }),
                }),
                zIndex: 99,
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
            this.cutStep = 0;
            this.currentStep = 1;
            this.selectedPolygon = null;
            this.selectedPolygonId = null;
            this.selectedPolygonGeoJSON = null;
            this.highlightedPolygon = null;
            this.backupOriginalPolygon = null;
            this.backupOriginalPolygonId = null;
            this.cutFeatures = [];
            this.cutTimestamp = null;
            this.point1 = null;
            this.point2 = null;
            this.errorMessage = null;

            // Clear history
            this.history = [];
            this.currentHistoryIndex = -1;

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

                // Create backup for undo/redo
                this.backupOriginalPolygon = feature.clone();

                // Extract polygon ID from various possible property names
                this.selectedPolygonId =
                    feature.get('polygon_id') ||
                    feature.get('id') ||
                    feature.get('poly_id') ||
                    feature.get('fea_id') ||
                    'unknown';

                this.backupOriginalPolygonId = this.selectedPolygonId;

                // Convert to GeoJSON for logging and cutting
                this.selectedPolygonGeoJSON =
                    this.geoJSONFormat.writeFeatureObject(feature, {
                        featureProjection: 'EPSG:4326',
                        dataProjection: 'EPSG:4326',
                    });

                console.log(
                    'Selected polygon GeoJSON:',
                    JSON.stringify(this.selectedPolygonGeoJSON)
                );
                console.log('Selected polygon ID:', this.selectedPolygonId);

                // Remove any existing highlight first
                this.removeHighlight();

                // Highlight the selected polygon
                this.highlightedPolygon = feature;
                this.highlightSelectedPolygon();

                // Move to next step
                this.currentStep = 2;
                this.errorMessage = null;
            } else {
                this.errorMessage =
                    'No polygon selected. Click on a polygon from the Processed layer.';
            }
        },

        highlightSelectedPolygon() {
            if (this.highlightedPolygon && this.layer3) {
                // Store original style
                const originalStyle = this.highlightedPolygon.getStyle();
                this.highlightedPolygon.set('_original_style', originalStyle);

                // Apply highlight style
                this.highlightedPolygon.setStyle(this.highlightStyle);
            }
        },

        removeHighlight() {
            // Remove highlight from any previously highlighted polygon
            if (this.highlightedPolygon && this.layer3) {
                console.log('Removing highlight from polygon');

                // Restore original style
                const originalStyle =
                    this.highlightedPolygon.get('_original_style');
                if (originalStyle) {
                    this.highlightedPolygon.setStyle(originalStyle);
                } else {
                    this.highlightedPolygon.setStyle(null);
                }

                // Remove the stored style property
                this.highlightedPolygon.unset('_original_style');

                // Force a style update
                this.highlightedPolygon.changed();
            }

            // Also check if selectedPolygon is different and remove its highlight
            if (
                this.selectedPolygon &&
                this.selectedPolygon !== this.highlightedPolygon &&
                this.layer3
            ) {
                const originalStyle =
                    this.selectedPolygon.get('_original_style');
                if (originalStyle) {
                    this.selectedPolygon.setStyle(originalStyle);
                } else {
                    this.selectedPolygon.setStyle(null);
                }
                this.selectedPolygon.unset('_original_style');
                this.selectedPolygon.changed();
            }

            // Clear references
            this.highlightedPolygon = null;
        },

        selectPoint1(coordinate) {
            this.point1 = coordinate;

            // Add point to point layer
            const pointFeature = new Feature({
                geometry: new Point(coordinate),
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
                geometry: new Point(coordinate),
            });
            this.pointLayer.getSource().addFeature(pointFeature);

            // Draw line between points
            this.drawCutLine();

            console.log('Point 2 selected:', coordinate);

            // Check if points are valid (not identical)
            if (
                this.point1[0] === this.point2[0] &&
                this.point1[1] === this.point2[1]
            ) {
                this.errorMessage = 'Points must be different';
            } else {
                this.errorMessage = null;
            }
        },

        drawCutLine() {
            if (!this.point1 || !this.point2) return;

            const lineFeature = new Feature({
                geometry: new LineString([this.point1, this.point2]),
            });

            this.lineLayer.getSource().clear();
            this.lineLayer.getSource().addFeature(lineFeature);
        },

        // Save current state to history
        saveStateToHistory(features) {
            // Create a deep copy of features for history
            const featuresCopy = features.map((f) => {
                const cloned = f.clone();
                // Copy over any important properties that clone might miss
                const props = f.getProperties();
                Object.keys(props).forEach((key) => {
                    if (key !== 'geometry') {
                        cloned.set(key, props[key]);
                    }
                });
                return cloned;
            });

            // Trim history if we're not at the end
            if (this.currentHistoryIndex < this.history.length - 1) {
                this.history = this.history.slice(
                    0,
                    this.currentHistoryIndex + 1
                );
            }

            this.history.push(featuresCopy);
            this.currentHistoryIndex = this.history.length - 1;

            console.log(
                `History saved. Index: ${this.currentHistoryIndex}, Length: ${this.history.length}`
            );

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
            const featuresToAdd = stateFeatures.map((f) => f.clone());
            source.addFeatures(featuresToAdd);

            // Update current history index
            this.currentHistoryIndex = index;

            // Force render
            this.layer3.changed();
            this.map.render();

            // Emit updated geometry to parent
            const updatedGeoJSON = {
                type: 'FeatureCollection',
                features: featuresToAdd.map((f) =>
                    this.geoJSONFormat.writeFeatureObject(f, {
                        featureProjection: 'EPSG:4326',
                        dataProjection: 'EPSG:4326',
                    })
                ),
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
                this.map.getInteractions().forEach((interaction) => {
                    if (interaction.constructor.name === 'Select') {
                        console.log(
                            'Found select interaction, clearing features'
                        );
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
                }, 10);
            }
        },

        performCut() {
            if (!this.canCut) return;

            try {
                console.log(
                    'Performing cut operation with polygon-splitter...'
                );

                // Get the polygon geometry
                const polygonGeometry = this.selectedPolygonGeoJSON.geometry;

                // Create the cut line
                const cutLine = {
                    type: 'LineString',
                    coordinates: [
                        [this.point1[0], this.point1[1]],
                        [this.point2[0], this.point2[1]],
                    ],
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
                this.cutFeatures = [];
                this.cutTimestamp = Date.now();

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
                        properties: {
                            ...this.selectedPolygonGeoJSON.properties,
                        },
                    };

                    try {
                        const feature = this.geoJSONFormat.readFeature(
                            geoJSONFeature,
                            {
                                featureProjection: 'EPSG:4326',
                                dataProjection: 'EPSG:4326',
                            }
                        );

                        // Set unique ID
                        const newId = `${this.selectedPolygonId}_cut_${index + 1}_${this.cutTimestamp}`;
                        feature.set('polygon_id', newId);
                        feature.set('id', newId);
                        feature.set('poly_id', newId);
                        feature.set(
                            'original_polygon_id',
                            this.selectedPolygonId
                        );
                        feature.set('cut_timestamp', this.cutTimestamp); // Group cut results by timestamp

                        this.cutFeatures.push(feature);
                    } catch (e) {
                        console.warn(
                            'Error creating feature:',
                            e,
                            geoJSONFeature
                        );
                    }
                });

                console.log('Created cut features:', this.cutFeatures.length);

                if (this.cutFeatures.length === 0) {
                    throw new Error('No valid cut features created');
                }

                // Get current features before modification
                const source = this.layer3.getSource();
                const currentFeatures = source.getFeatures();

                // Create updated features array
                const updatedFeatures = [];

                // Keep all features except the selected one
                for (const feature of currentFeatures) {
                    const featureId =
                        feature.get('polygon_id') ||
                        feature.get('id') ||
                        feature.get('poly_id') ||
                        feature.get('fea_id');

                    const featureIdStr = featureId ? featureId.toString() : '';
                    const selectedIdStr = this.selectedPolygonId
                        ? this.selectedPolygonId.toString()
                        : '';

                    if (featureIdStr === selectedIdStr) {
                        console.log('Found original feature to replace');
                        continue;
                    }
                    updatedFeatures.push(feature);
                }

                // Add the new cut features
                updatedFeatures.push(...this.cutFeatures);

                // Save state to history BEFORE updating the layer
                // This saves the original state (with the original polygon)
                this.saveStateToHistory(currentFeatures);

                // Save the cut state to history as well
                this.saveStateToHistory(updatedFeatures);

                // Now update the layer with cut features
                source.clear();
                source.addFeatures(updatedFeatures);

                // Remove the cut line and points (clear temp layers)
                if (this.lineLayer) {
                    this.lineLayer.getSource().clear();
                }
                if (this.pointLayer) {
                    this.pointLayer.getSource().clear();
                }

                // Force a render
                this.layer3.changed();
                this.map.render();

                // Emit updated geometry to parent (for real-time updates)
                const updatedGeoJSON = {
                    type: 'FeatureCollection',
                    features: updatedFeatures.map((f) =>
                        this.geoJSONFormat.writeFeatureObject(f, {
                            featureProjection: 'EPSG:4326',
                            dataProjection: 'EPSG:4326',
                        })
                    ),
                };

                this.$emit('update-processed-geometry', updatedGeoJSON);

                // Remove highlight from selected polygon before moving to post-cut state
                this.removeHighlight();

                // Move to post-cut state (cutStep = 2)
                this.cutStep = 2;
            } catch (error) {
                console.error('Error performing cut:', error);
                this.errorMessage = `Cut failed: ${error.message}. Please try a different cut line.`;
            }
        },

        undoCut() {
            if (!this.canUndo) return;

            console.log('Undo cut');

            // Remove highlight before applying history state
            this.removeHighlight();

            // Apply the previous state from history
            this.applyStateFromHistory(this.currentHistoryIndex - 1);

            // After undo, we need to find and highlight the original polygon again
            setTimeout(() => {
                // Find the restored original polygon in the layer
                const source = this.layer3.getSource();
                const features = source.getFeatures();

                // Look for the polygon with the original ID
                const restoredPolygon = features.find((f) => {
                    const id =
                        f.get('polygon_id') || f.get('id') || f.get('poly_id');
                    return (
                        id &&
                        id.toString() ===
                            this.backupOriginalPolygonId?.toString()
                    );
                });

                if (restoredPolygon) {
                    // Update references
                    this.selectedPolygon = restoredPolygon;
                    this.selectedPolygonId = this.backupOriginalPolygonId;
                    this.highlightedPolygon = restoredPolygon;

                    // Re-apply highlight
                    this.highlightSelectedPolygon();

                    // Update the GeoJSON for potential redo
                    this.selectedPolygonGeoJSON =
                        this.geoJSONFormat.writeFeatureObject(restoredPolygon, {
                            featureProjection: 'EPSG:4326',
                            dataProjection: 'EPSG:4326',
                        });
                }

                // Force a map render
                this.map.render();
            }, 50);
        },

        redoCut() {
            if (!this.canRedo) return;

            console.log('Redo cut');

            // Remove highlight before applying history state
            this.removeHighlight();

            // Apply the next state from history
            this.applyStateFromHistory(this.currentHistoryIndex + 1);

            // After redo, we need to find and highlight the cut features
            setTimeout(() => {
                // Find the cut features and highlight the first one? Or maybe don't highlight at all
                // For now, just clear the highlight since we're back to cut state
                this.highlightedPolygon = null;

                // Force a map render
                this.map.render();
            }, 50);
        },

        async saveCut() {
            console.log('Saving cut operation');

            if (!this.proposalId) {
                this.errorMessage = 'No proposal ID available';
                return;
            }

            try {
                // Get the current state from the layer
                const source = this.layer3.getSource();
                const allFeatures = source.getFeatures();

                // Build the updated GeoJSON
                const updatedGeoJSON = {
                    type: 'FeatureCollection',
                    features: allFeatures.map((f) =>
                        this.geoJSONFormat.writeFeatureObject(f, {
                            featureProjection: 'EPSG:4326',
                            dataProjection: 'EPSG:4326',
                        })
                    ),
                };

                // Find original polygon IDs (from backup)
                const originalPolygonIds = this.backupOriginalPolygonId
                    ? [this.backupOriginalPolygonId]
                    : [];

                // Find new polygon IDs (from cut features)
                const newPolygonIds = this.cutFeatures.map(
                    (f) => f.get('polygon_id') || f.get('id')
                );

                // Prepare data for API
                const saveData = {
                    updated_geojson: updatedGeoJSON,
                    original_polygon_ids: originalPolygonIds,
                    new_polygon_ids: newPolygonIds,
                    operation: 'cut',
                    cut_line: [
                        [this.point1[0], this.point1[1]],
                        [this.point2[0], this.point2[1]],
                    ],
                };

                console.log('Saving cut to API:', saveData);

                // Make API call to save the cut geometry
                const response = await fetch(
                    `/api/proposal/${this.proposalId}/save_cut_geometry/`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': helpers.getCookie('csrftoken'),
                        },
                        body: JSON.stringify(saveData),
                    }
                );

                const data = await response.json();

                if (data.success) {
                    console.log('Cut saved successfully');

                    // Show success message
                    alert('Cut geometry saved successfully.');

                    // Exit cut mode
                    this.cancelCut();
                } else {
                    this.errorMessage =
                        data.error || 'Failed to save cut geometry';
                    console.error('Save failed:', data.error);
                }
            } catch (error) {
                console.error('Error saving cut:', error);
                this.errorMessage = `Error saving: ${error.message}`;
            }
        },

        cancelCut() {
            console.log('Cancelling cut mode');

            // Remove highlight from any highlighted polygon
            this.removeHighlight();

            // Clear any selected feature from the map's select interaction
            this.clearMapSelection();

            // Force a complete map refresh
            setTimeout(() => {
                this.forceMapRefresh();
            }, 50);

            // Remove temporary layers
            this.removeTempLayers();

            // Exit cut mode
            this.isCutModeActive = false;
        },

        cleanup() {
            this.removeHighlight();
            this.removeTempLayers();
            if (this.clickHandler) {
                this.map.un('click', this.clickHandler);
            }
        },
    },
};
</script>

<style scoped>
.cut-polygon-tool {
    position: relative;
}

.control-btn.cut-btn {
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
    top: 60px;
    right: 55px;
    width: 300px;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    z-index: 1000;
}

.cut-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px;
    border-bottom: 1px solid #eee;
    background: #f8f9fa;
    border-radius: 4px 4px 0 0;
}

.cut-panel-header h3 {
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

.cut-panel-content {
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
    width: 24px;
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

/* Post-cut specific */
.post-cut .step-row.completed .step-number {
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

.cut-panel-actions {
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
.cut-action-btn,
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

.cut-action-btn {
    background: #28a745;
    color: white;
    width: 100%;
}

.cut-action-btn:hover:not(:disabled) {
    background: #218838;
}

.cut-action-btn:disabled {
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

/* Hide old styles that are no longer needed */
.instruction-steps,
.post-cut-message,
.selected-polygon-info,
.points-container,
.point-info {
    display: none;
}
</style>
