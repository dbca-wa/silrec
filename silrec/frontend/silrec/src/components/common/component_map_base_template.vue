<template>
    <div>
        <div class="map-container" :class="{ maximised: isMaximised }">
            <div ref="mapContainer" class="map"></div>

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
            </div>
        </div>
    </div>
</template>

<script>
import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import { fromLonLat } from 'ol/proj';
import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';

export default {
    name: 'BaseMap',
    data() {
        return {
            map: null,
            isMaximised: false,
        };
    },
    mounted() {
        this.$nextTick(() => {
            this.initializeMap();
            window.addEventListener('resize', this.handleResize);
            document.addEventListener('keydown', this.handleEscape);
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
            const baseLayer = new TileLayer({ source: new OSM() });

            this.map = new Map({
                target: this.$refs.mapContainer,
                layers: [baseLayer],
                view: new View({
                    projection: 'EPSG:4326',
                    center: fromLonLat([121.5, -24.5], 'EPSG:4326'),
                    zoom: 6,
                }),
            });
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
            if (this.map)
                setTimeout(() => {
                    this.map.updateSize();
                }, 100);
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
</style>
