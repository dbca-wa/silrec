<template>
  <div class="cohort-form">
    <form @submit.prevent="saveCohort">
      <div class="row">
        <div class="col-md-6">
          <div class="form-group">
            <label for="objCode">Objective Code</label>
            <input
              id="objCode"
              v-model="cohortData.obj_code"
              type="text"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
        <div class="col-md-6">
          <div class="form-group">
            <label for="species">Species</label>
            <input
              id="species"
              v-model="cohortData.species"
              type="text"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
      </div>

      <div class="row mt-3">
        <div class="col-md-4">
          <div class="form-group">
            <label for="targetBa">Target BA (m²/ha)</label>
            <input
              id="targetBa"
              v-model.number="cohortData.target_ba_m2ha"
              type="number"
              step="0.1"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="residualBa">Residual BA (m²/ha)</label>
            <input
              id="residualBa"
              v-model.number="cohortData.resid_ba_m2ha"
              type="number"
              step="0.1"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="siteQuality">Site Quality</label>
            <input
              id="siteQuality"
              v-model="cohortData.site_quality"
              type="text"
              class="form-control"
              :readonly="readOnly"
            />
          </div>
        </div>
      </div>

      <div class="row mt-3">
        <div class="col-md-12">
          <div class="form-group">
            <label for="comments">Comments</label>
            <textarea
              id="comments"
              v-model="cohortData.comments"
              class="form-control"
              rows="3"
              :readonly="readOnly"
            ></textarea>
          </div>
        </div>
      </div>

      <div v-if="!readOnly" class="mt-4">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'CohortForm',
  props: {
    cohortId: {
      type: [Number, String],
      required: true
    },
    polygonId: {
      type: [Number, String],
      required: true
    },
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      cohortData: {
        obj_code: '',
        species: '',
        target_ba_m2ha: null,
        resid_ba_m2ha: null,
        site_quality: '',
        comments: ''
      },
      saving: false
    };
  },
  methods: {
    async loadCohortData() {
      try {
        const response = await this.$http.get(`${api_endpoints.cohorts}${this.cohortId}/`);
        this.cohortData = { ...response.data };
      } catch (error) {
        console.error('Error loading cohort data:', error);
        this.$emit('error', 'Failed to load cohort data');
      }
    },
    async saveCohort() {
      this.saving = true;
      try {
        const response = await this.$http.put(
          `${api_endpoints.cohorts}${this.cohortId}/`,
          this.cohortData
        );
        this.$emit('cohort-updated', response.data);
        this.$emit('success', 'Cohort updated successfully');
      } catch (error) {
        console.error('Error saving cohort:', error);
        this.$emit('error', 'Failed to save cohort data');
      } finally {
        this.saving = false;
      }
    }
  },
  mounted() {
    this.loadCohortData();
  }
};
</script>
