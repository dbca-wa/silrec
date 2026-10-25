<template>
    <div class="geom-diff mb-3">
        <!-- Collapsed state: compact toggle row -->
        <div
            v-if="collapsed"
            class="d-flex align-items-center gap-2 geom-collapsed"
        >
            <button
                type="button"
                class="btn btn-link btn-sm p-0"
                title="Expand"
                @click="collapsed = false"
            >
                <i class="bi bi-chevron-right"></i>
            </button>
            <code class="small fw-semibold">{{ fieldLabel }}</code>
            <span v-if="summaryText" class="text-muted small">
                {{ summaryText }}
            </span>
        </div>

        <!-- Expanded state -->
        <template v-else>
            <div class="d-flex align-items-center gap-2 mb-1">
                <button
                    type="button"
                    class="btn btn-link btn-sm p-0"
                    title="Collapse"
                    @click="collapsed = true"
                >
                    <i class="bi bi-chevron-down"></i>
                </button>
                <code class="small fw-semibold">{{ fieldLabel }}</code>
            </div>

            <div
                v-if="hasBoth"
                class="d-flex align-items-center gap-3 mb-2 flex-wrap"
            >
                <label class="text-muted small text-nowrap mb-0"
                    >Zoom all geometries:</label
                >
                <input
                    v-model="zoomSlider"
                    type="range"
                    min="0"
                    max="100"
                    class="form-range"
                    style="max-width: 220px"
                    @input="applyZoom"
                />
                <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary"
                    @click="resetZoom"
                >
                    Reset
                </button>
                <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary"
                    title="Maximise view"
                    @click="toggleSectionFullscreen"
                >
                    <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <path
                            d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"
                        />
                    </svg>
                    Maximise
                </button>
            </div>

            <div ref="section" class="geom-section geom-maps row g-3">
                <div class="geom-box col-md-6">
                    <div class="text-muted small">Old geometry</div>
                    <div v-if="oldGeojson" class="geom-map-wrap">
                        <div ref="oldMapEl" class="geom-map"></div>
                        <div class="geom-map-controls">
                            <select
                                v-model="layers.old"
                                class="form-select form-select-sm"
                                title="Base layer"
                            >
                                <option value="street">Layer</option>
                                <option value="satellite">Satellite</option>
                            </select>
                            <button
                                type="button"
                                class="btn btn-light btn-sm"
                                title="Maximise"
                                @click="toggleMapFullscreen('old')"
                            >
                                <svg
                                    width="14"
                                    height="14"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2.2"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                >
                                    <path
                                        d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"
                                    />
                                </svg>
                            </button>
                        </div>
                        <div v-if="oldSummary" class="geom-summary">
                            {{ oldSummary }}
                        </div>
                    </div>
                    <div v-else class="geom-empty text-muted small">
                        (no previous geometry)
                    </div>
                </div>
                <div class="geom-box col-md-6">
                    <div class="text-muted small">New geometry</div>
                    <div v-if="newGeojson" class="geom-map-wrap">
                        <div ref="newMapEl" class="geom-map"></div>
                        <div class="geom-map-controls">
                            <select
                                v-model="layers.new"
                                class="form-select form-select-sm"
                                title="Base layer"
                            >
                                <option value="street">Layer</option>
                                <option value="satellite">Satellite</option>
                            </select>
                            <button
                                type="button"
                                class="btn btn-light btn-sm"
                                title="Maximise"
                                @click="toggleMapFullscreen('new')"
                            >
                                <svg
                                    width="14"
                                    height="14"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2.2"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                >
                                    <path
                                        d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"
                                    />
                                </svg>
                            </button>
                        </div>
                        <div v-if="newSummary" class="geom-summary">
                            {{ newSummary }}
                        </div>
                    </div>
                    <div v-else class="geom-empty text-muted small">
                        (no new geometry)
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import 'ol/ol.css';
import Feature from 'ol/Feature';
import Map from 'ol/Map';
import View from 'ol/View';
import GeoJSON from 'ol/format/GeoJSON';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import XYZ from 'ol/source/XYZ';
import { Style, Fill, Stroke } from 'ol/style';
import { fromLonLat } from 'ol/proj';
import { defaults as defaultControls } from 'ol/control';

const SATELLITE_URL =
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

// Geometry fields that render collapsed by default (expanded on demand).
const COLLAPSED_BY_DEFAULT = new Set(['geojson_data_processed_iters']);

export default {
    name: 'GeomDiff',
    props: {
        change: { type: Object, required: true },
    },
    data() {
        return {
            maps: {},
            layers: { old: 'street', new: 'street' },
            zoomSlider: 50,
            collapsed: COLLAPSED_BY_DEFAULT.has(this.change.field),
        };
    },
    computed: {
        oldGeojson() {
            return this.change.old_geojson || null;
        },
        newGeojson() {
            return this.change.new_geojson || null;
        },
        oldSummary() {
            return this.change.old_summary || '';
        },
        newSummary() {
            return this.change.new_summary || '';
        },
        summaryText() {
            const parts = [];
            if (this.oldSummary) parts.push(this.oldSummary);
            if (this.newSummary) parts.push(this.newSummary);
            return parts.join(' \u2192 ');
        },
        hasBoth() {
            return !!(this.oldGeojson && this.newGeojson);
        },
        fieldLabel() {
            return this.change.field;
        },
    },
    watch: {
        'layers.old'(val) {
            this.setLayer('old', val);
        },
        'layers.new'(val) {
            this.setLayer('new', val);
        },
        collapsed(val) {
            if (val) {
                this.disposeMaps();
            } else {
                this.$nextTick(this.initMaps);
            }
        },
    },
    mounted() {
        this.$nextTick(this.initMaps);
    },
    beforeUnmount() {
        this.disposeMaps();
    },
    methods: {
        readFeatures(geojson) {
            const format = new GeoJSON();
            const opts = {
                dataProjection: 'EPSG:4326',
                featureProjection: 'EPSG:3857',
            };
            if (
                geojson.type === 'FeatureCollection' ||
                geojson.type === 'Feature'
            ) {
                return format.readFeatures(geojson, opts);
            }
            if (geojson.coordinates) {
                const geom = format.readGeometry(geojson, opts);
                return [new Feature({ geometry: geom })];
            }
            return [];
        },
        initMaps() {
            if (this.oldGeojson && this.$refs.oldMapEl && !this.maps.old) {
                this.createMap('old', this.$refs.oldMapEl, this.oldGeojson);
            }
            if (this.newGeojson && this.$refs.newMapEl && !this.maps.new) {
                this.createMap('new', this.$refs.newMapEl, this.newGeojson);
            }
        },
        createMap(key, el, geojson) {
            const street = new TileLayer({
                source: new OSM(),
                visible: this.layers[key] === 'street',
            });
            const satellite = new TileLayer({
                source: new XYZ({ url: SATELLITE_URL }),
                visible: this.layers[key] === 'satellite',
            });

            const vectorSource = new VectorSource();
            const vectorLayer = new VectorLayer({
                source: vectorSource,
                style: new Style({
                    fill: new Fill({ color: 'rgba(51, 122, 183, 0.35)' }),
                    stroke: new Stroke({
                        color: 'rgba(51, 122, 183, 1)',
                        width: 2,
                    }),
                }),
            });

            const map = new Map({
                target: el,
                layers: [street, satellite, vectorLayer],
                controls: defaultControls(),
                view: new View({
                    projection: 'EPSG:3857',
                    center: fromLonLat([121.5, -24.5]),
                    zoom: 6,
                }),
            });

            const features = this.readFeatures(geojson);
            vectorSource.addFeatures(features);

            let baseZoom = 6;
            if (features.length) {
                const extent = vectorSource.getExtent();
                if (extent && isFinite(extent[0]) && isFinite(extent[3])) {
                    map.getView().fit(extent, { padding: [20, 20, 20, 20] });
                    baseZoom = map.getView().getZoom();
                }
            }

            const onFullscreenChange = () => {
                setTimeout(() => map.updateSize(), 50);
            };
            document.addEventListener('fullscreenchange', onFullscreenChange);

            this.maps[key] = {
                map,
                street,
                satellite,
                baseZoom,
                onFullscreenChange,
            };
        },
        setLayer(key, val) {
            const m = this.maps[key];
            if (!m) return;
            m.street.setVisible(val === 'street');
            m.satellite.setVisible(val === 'satellite');
        },
        disposeMaps() {
            Object.values(this.maps).forEach((m) => {
                if (m.onFullscreenChange) {
                    document.removeEventListener(
                        'fullscreenchange',
                        m.onFullscreenChange
                    );
                }
                m.map.setTarget(null);
            });
            this.maps = {};
        },
        applyZoom() {
            const delta = ((parseInt(this.zoomSlider, 10) - 50) / 50) * 5;
            Object.values(this.maps).forEach((m) =>
                m.map.getView().setZoom(m.baseZoom + delta)
            );
        },
        resetZoom() {
            this.zoomSlider = 50;
            this.applyZoom();
        },
        toggleFullscreen(el) {
            if (!el) return;
            if (!document.fullscreenElement) {
                const fn =
                    el.requestFullscreen ||
                    el.webkitRequestFullscreen ||
                    el.msRequestFullscreen;
                if (fn) fn.call(el);
            } else {
                const fn =
                    document.exitFullscreen ||
                    document.webkitExitFullscreen ||
                    document.msExitFullscreen;
                if (fn) fn.call(document);
            }
        },
        toggleMapFullscreen(key) {
            this.toggleFullscreen(this.$refs[key + 'MapEl']);
        },
        toggleSectionFullscreen() {
            this.toggleFullscreen(this.$refs.section);
        },
    },
};
</script>

<style scoped>
.geom-collapsed {
    padding: 4px 0;
}
.geom-maps {
    margin: 0;
}
.geom-map-wrap {
    position: relative;
    margin-top: 4px;
}
.geom-empty {
    min-height: 60px;
    display: flex;
    align-items: center;
    margin-top: 4px;
    padding: 8px 12px;
    border: 1px dashed #ccc;
    border-radius: 4px;
    background: #f8f9fa;
}
.geom-map {
    height: 300px;
    width: 100%;
    border: 1px solid #ccc;
    border-radius: 4px;
}
.geom-map-controls {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 1;
    display: flex;
    gap: 4px;
    align-items: center;
}
.geom-map-controls .form-select {
    width: auto;
    font-size: 12px;
    padding: 2px 6px;
}
.geom-map-controls .btn {
    line-height: 1;
    padding: 3px 6px;
    border: 1px solid #ccc;
}
.geom-summary {
    position: absolute;
    bottom: 10px;
    left: 10px;
    z-index: 1;
    padding: 5px 9px;
    font:
        13px/15px Arial,
        Helvetica,
        sans-serif;
    background: rgba(255, 255, 255, 0.9);
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    white-space: nowrap;
    color: #333;
    pointer-events: none;
}
.geom-section:fullscreen {
    background: #fff;
    padding: 16px;
    overflow: auto;
}
.geom-section:fullscreen .geom-map {
    height: calc(100vh - 160px);
}
</style>
