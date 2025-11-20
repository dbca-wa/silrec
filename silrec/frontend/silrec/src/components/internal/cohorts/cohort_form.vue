<template>
  <div class="cohort-form">
    <div class="row">
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="objCode" class="form-label required">Objective Code</label>
          <input
            id="objCode"
            v-model="formData.obj_code"
            type="text"
            class="form-control"
            :readonly="readOnly"
            required
            maxlength="20"
          />
          <div class="form-text">Silvicultural or management objective</div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="species" class="form-label">Species</label>
          <input
            id="species"
            v-model="formData.species"
            type="text"
            class="form-control"
            :readonly="readOnly"
            maxlength="3"
          />
          <div class="form-text">Dominant overstorey API species</div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="regenMethod" class="form-label required">Regeneration Method</label>
          <input
            id="regenMethod"
            v-model="formData.regen_method"
            type="text"
            class="form-control"
            :readonly="readOnly"
            required
          />
        </div>
      </div>
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="siteQuality" class="form-label">Site Quality</label>
          <input
            id="siteQuality"
            v-model="formData.site_quality"
            type="text"
            class="form-control"
            :readonly="readOnly"
            maxlength="6"
          />
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-4">
        <div class="form-group mb-3">
          <label for="targetBa" class="form-label">Target BA (m²/ha)</label>
          <input
            id="targetBa"
            v-model.number="formData.target_ba_m2ha"
            type="number"
            step="0.1"
            min="0"
            class="form-control"
            :readonly="readOnly"
          />
        </div>
      </div>
      <div class="col-md-4">
        <div class="form-group mb-3">
          <label for="residualBa" class="form-label">Residual BA (m²/ha)</label>
          <input
            id="residualBa"
            v-model.number="formData.resid_ba_m2ha"
            type="number"
            step="0.1"
            min="0"
            class="form-control"
            :readonly="readOnly"
          />
        </div>
      </div>
      <div class="col-md-4">
        <div class="form-group mb-3">
          <label for="targetSpha" class="form-label">Target SPHA</label>
          <input
            id="targetSpha"
            v-model.number="formData.target_spha"
            type="number"
            min="0"
            class="form-control"
            :readonly="readOnly"
          />
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-12">
        <div class="form-group mb-3">
          <label for="comments" class="form-label">Comments</label>
          <textarea
            id="comments"
            v-model="formData.comments"
            class="form-control"
            rows="3"
            :readonly="readOnly"
            maxlength="250"
          ></textarea>
          <div class="form-text">{{ formData.comments ? formData.comments.length : 0 }}/250 characters</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CohortForm',
  props: {
    cohortData: {
      type: Object,
      required: true
    },
    readOnly: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      formData: {}
    };
  },
  watch: {
    cohortData: {
      handler(newData) {
        this.initializeFormData(newData);
      },
      immediate: true,
      deep: true
    }
  },
  methods: {
    initializeFormData(cohortData) {
      this.formData = {
        obj_code: cohortData.obj_code || '',
        species: cohortData.species || '',
        regen_method: cohortData.regen_method || '',
        target_ba_m2ha: cohortData.target_ba_m2ha || null,
        resid_ba_m2ha: cohortData.resid_ba_m2ha || null,
        target_spha: cohortData.target_spha || null,
        site_quality: cohortData.site_quality || '',
        comments: cohortData.comments || ''
      };
    }
  }
};
</script>

<style scoped>
.cohort-form {
  max-width: 100%;
}

.form-group {
  margin-bottom: 1rem;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.form-label.required::after {
  content: " *";
  color: #dc3545;
}

.form-control:read-only {
  background-color: #e9ecef;
  opacity: 1;
}

.form-text {
  font-size: 0.75rem;
  color: #6c757d;
}
</style>
