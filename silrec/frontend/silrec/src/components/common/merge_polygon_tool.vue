<template>
  <div>
    <!-- Merge button (small icon) with toggle behavior -->
    <button
      v-if="hasLayer3"
      class="control-btn merge-btn"
      @click="toggleMergeModal"
      :class="{ active: mergeStep === 2 || showMergeModal }"
      :title="mergeStep === 2 ? 'Merge completed' : 'Merge two polygons'"
    >
      <svg width="20" height="22" viewBox="0 0 24 24" fill="currentColor">
        <!-- Simple combine/merge icon (two overlapping squares) -->
        <path d="M8 5v14l11-7z"/>
        <rect x="4" y="4" width="10" height="10" rx="1" stroke="currentColor" fill="none" stroke-width="2"/>
        <rect x="10" y="10" width="10" height="10" rx="1" stroke="currentColor" fill="none" stroke-width="2"/>
      </svg>
    </button>

    <!-- Merge Modal – floating panel inside map container -->
    <div v-if="showMergeModal" class="merge-modal-panel" @click.stop>
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
</template>

<script>
import * as turf from '@turf/turf';
import { Style, Fill, Stroke } from 'ol/style';
import GeoJSON from 'ol/format/GeoJSON';
import { helpers } from '@/utils/hooks';

export default {
  name: 'MergePolygonTool',
  props: {
    map: { type: Object, required: true },
    layer3: { type: Object, required: true },
    hasLayer3: { type: Boolean, default: false },
    proposalId: { type: [Number, String], required: true },
    highlightStyle: { type: Object, required: true }
  },
  emits: ['update-processed-geometry', 'disable-select-interaction', 'enable-select-interaction'],
  data() {
    return {
      showMergeModal: false,
      mergeStep: 0,
      mergeSelectedFeatures: [],
      mergeClickHandler: null,
      backupFeatures: null,
      mergedFeatureId: null,
    };
  },
  methods: {
    // Toggle modal open/close
    toggleMergeModal() {
      if (this.showMergeModal) {
        this.closeMergeModal();
      } else {
        this.openMergeModal();
      }
    },
    openMergeModal() {
      if (this.mergeStep === 2) {
        this.showMergeModal = true;
        return;
      }
      this.mergeStep = 1;
      this.mergeSelectedFeatures = [];
      this.showMergeModal = true;
      this.startMergeMode();
    },
    closeMergeModal() {
      this.showMergeModal = false;
      if (this.mergeStep < 2) {
        this.cancelMerge();
        this.mergeStep = 0;
      }
    },
    startMergeMode() {
      if (!this.hasLayer3 || !this.layer3.getVisible()) {
        alert('Please make the Processed layer visible first.');
        return;
      }
      this.$emit('disable-select-interaction');

      if (this.mergeClickHandler) {
        this.map.un('click', this.mergeClickHandler);
      }
      this.mergeClickHandler = (evt) => {
        if (!this.showMergeModal || this.mergeStep !== 1) return;

        const pixel = this.map.getEventPixel(evt.originalEvent);
        const feature = this.map.forEachFeatureAtPixel(pixel, (feature, layer) => {
          if (layer === this.layer3) return feature;
          return null;
        });

        if (feature) {
          this.handleMergeClick(feature);
        }
      };
      this.map.on('click', this.mergeClickHandler);
    },
    cancelMerge() {
      this.$emit('enable-select-interaction');

      if (this.mergeClickHandler) {
        this.map.un('click', this.mergeClickHandler);
        this.mergeClickHandler = null;
      }
      this.mergeSelectedFeatures.forEach(f => f.setStyle(null));
      this.mergeSelectedFeatures = [];
    },
    handleMergeClick(feature) {
      const index = this.mergeSelectedFeatures.findIndex(f => f === feature);
      if (index !== -1) {
        this.mergeSelectedFeatures.splice(index, 1);
        feature.setStyle(null);
      } else {
        if (this.mergeSelectedFeatures.length < 2) {
          this.mergeSelectedFeatures.push(feature);
          feature.setStyle(this.highlightStyle);
        } else {
          alert('You can only select two polygons. Deselect one first.');
        }
      }
      this.map.render();
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
    async performMerge(feature1, feature2) {
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

      const source = this.layer3.getSource();

      this.backupFeatures = {
        f1: feature1.clone(),
        f2: feature2.clone(),
        originalIds: [feature1.get('id'), feature2.get('id')]
      };

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

      feature1.setStyle(new Style({
        fill: new Fill({ color: 'rgba(0, 255, 0, 0.5)' }),
        stroke: new Stroke({ color: 'rgba(0, 0, 0, 1)', width: 3 })
      }));

      source.removeFeature(feature2);
      source.changed();
      this.layer3.changed();
      this.map.render();

      const mergedExtent = feature1.getGeometry().getExtent();
      this.map.getView().fit(mergedExtent, { padding: [50, 50, 50, 50], duration: 500 });

      const allFeatures = source.getFeatures();
      const updatedFC = {
        type: 'FeatureCollection',
        features: allFeatures.map(f => format.writeFeatureObject(f, {
          featureProjection: 'EPSG:4326',
          dataProjection: 'EPSG:4326'
        }))
      };
      this.$emit('update-processed-geometry', updatedFC);

      this.cancelMerge();
      return true;
    },
    async performMergeAndTransition() {
      try {
        await this.performMerge(this.mergeSelectedFeatures[0], this.mergeSelectedFeatures[1]);
        this.mergeStep = 2;
      } catch (error) {
        console.error(error);
        alert('Merge failed: ' + error.message);
      }
    },
    revertMerge() {
      const source = this.layer3.getSource();
      const merged = source.getFeatures().find(f => f.get('mergeId') === this.mergedFeatureId);
      if (merged) source.removeFeature(merged);
      source.addFeature(this.backupFeatures.f1);
      source.addFeature(this.backupFeatures.f2);
      source.changed();
      this.layer3.changed();
      this.map.render();

      this.mergeStep = 1;
      this.mergeSelectedFeatures.forEach(f => f.setStyle(null));
      this.mergeSelectedFeatures = [this.backupFeatures.f1, this.backupFeatures.f2];
      this.backupFeatures.f1.setStyle(this.highlightStyle);
      this.backupFeatures.f2.setStyle(this.highlightStyle);
      this.map.render();

      this.cancelMerge();
      this.$emit('disable-select-interaction');
      this.startMergeMode();
    },
    saveMerge() {
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

      fetch(`/api/proposal/${this.proposalId}/save_merged_geometry/`, {
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
    }
  },
  beforeDestroy() {
    if (this.mergeClickHandler) {
      this.map.un('click', this.mergeClickHandler);
    }
    this.$emit('enable-select-interaction');
  }
};
</script>

<style scoped>
.control-btn.merge-btn.active {
  background-color: #007bff;
  color: white;
  border-color: #0056b3;
}

.merge-modal-panel {
  position: absolute;
  top: 60px;
  right: 10px;
  width: 300px;
  max-width: 400px;
  min-width: 280px;
  background: white;
  border-radius: 4px;
  border: 1px solid #ccc;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 1001;
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
</style>
