<template>
  <div class="additional-cohort-fields">
    <div v-if="debug" class="alert alert-info debug-info">
      <strong>Debug Info:</strong><br>
      Component Mounted: {{ componentMounted }}<br>
      Form Initialized: {{ formInitialized }}<br>
      Cohort ID: {{ cohortData.cohort_id }}<br>
      Data Timestamp: {{ dataTimestamp }}
    </div>

    <div class="row">
      <!-- Operation Information -->
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="opId" class="form-label">Operation ID</label>
          <input
            id="opId"
            v-model.number="formData.op_id"
            type="number"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Operation identifier</div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="opDate" class="form-label">Operation Date</label>
          <input
            id="opDate"
            v-model="formData.op_date"
            type="datetime-local"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Date of operation boundary creation</div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="yearLastCut" class="form-label">Year Last Cut</label>
          <input
            id="yearLastCut"
            v-model.number="formData.year_last_cut"
            type="number"
            min="1900"
            :max="new Date().getFullYear()"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Year of last harvest</div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="pctArea" class="form-label">Percentage Area</label>
          <input
            id="pctArea"
            v-model.number="formData.pct_area"
            type="number"
            min="0"
            max="100"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Percentage of stand area (0-100)</div>
        </div>
      </div>
    </div>

    <!-- Regeneration Information -->
    <div class="row">
      <div class="col-md-4">
        <div class="form-group mb-3">
          <label for="regenDate" class="form-label">Regeneration Date</label>
          <input
            id="regenDate"
            v-model="formData.regen_date"
            type="datetime-local"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Date of majority regeneration</div>
        </div>
      </div>
      
      <div class="col-md-4">
        <div class="form-group mb-3">
          <label for="regenDate2" class="form-label">Secondary Regeneration Date</label>
          <input
            id="regenDate2"
            v-model="formData.regen_date2"
            type="datetime-local"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Date of secondary regeneration</div>
        </div>
      </div>
      
      <div class="col-md-4">
        <div class="form-group mb-3">
          <label for="regenMethod" class="form-label">Regeneration Method</label>
          <input
            id="regenMethod"
            v-model="formData.regen_method"
            type="text"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Method of regeneration</div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label class="form-check-label">
            <input
              v-model="formData.regen_done"
              type="checkbox"
              class="form-check-input"
              :disabled="readOnly"
            />
            Regeneration Values Calculated
          </label>
          <div class="form-text">Yes if regeneration values have been calculated</div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label class="form-check-label">
            <input
              v-model="formData.treatments"
              type="checkbox"
              class="form-check-input"
              :disabled="readOnly"
            />
            Treatments Inserted
          </label>
          <div class="form-text">Yes if treatments have been inserted for this cohort</div>
        </div>
      </div>
    </div>

    <!-- Stocking Information -->
    <div class="row">
      <div class="col-md-3">
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
          <div class="form-text">Target stems per hectare</div>
        </div>
      </div>
      
      <div class="col-md-3">
        <div class="form-group mb-3">
          <label for="residSpha" class="form-label">Residual SPHA</label>
          <input
            id="residSpha"
            v-model.number="formData.resid_spha"
            type="number"
            min="0"
            step="0.1"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Residual stems per hectare</div>
        </div>
      </div>
      
      <div class="col-md-3">
        <div class="form-group mb-3">
          <label for="targetBa" class="form-label">Target BA (m²/ha)</label>
          <input
            id="targetBa"
            v-model.number="formData.target_ba_m2ha"
            type="number"
            min="0"
            step="0.1"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Target basal area</div>
        </div>
      </div>
      
      <div class="col-md-3">
        <div class="form-group mb-3">
          <label for="residBa" class="form-label">Residual BA (m²/ha)</label>
          <input
            id="residBa"
            v-model.number="formData.resid_ba_m2ha"
            type="number"
            min="0"
            step="0.1"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Residual basal area</div>
        </div>
      </div>
    </div>

    <!-- Additional Fields -->
    <div class="row">
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="completeDate" class="form-label">Complete Date</label>
          <input
            id="completeDate"
            v-model="formData.complete_date"
            type="datetime-local"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Date of completion of all activities</div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="herbicideAppSpec" class="form-label">Herbicide Application</label>
          <input
            id="herbicideAppSpec"
            v-model="formData.herbicide_app_spec"
            type="text"
            class="form-control"
            :readonly="readOnly"
            placeholder="Herbicide application specification"
            maxlength="50"
          />
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="vrp" class="form-label">Vegetation Retention Patch</label>
          <input
            id="vrp"
            v-model.number="formData.vrp"
            type="number"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">VRP number</div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="vrpTotArea" class="form-label">VRP Total Area (ha)</label>
          <input
            id="vrpTotArea"
            v-model.number="formData.vrp_tot_area"
            type="number"
            min="0"
            step="0.1"
            class="form-control"
            :readonly="readOnly"
          />
          <div class="form-text">Vegetation retention patch total area</div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label for="stand" class="form-label">Stand</label>
          <input
            id="stand"
            v-model="formData.stand"
            type="text"
            class="form-control"
            :readonly="readOnly"
            maxlength="10"
          />
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="form-group mb-3">
          <label class="form-check-label">
            <input
              v-model="formData.extra_info"
              type="checkbox"
              class="form-check-input"
              :disabled="readOnly"
            />
            Extra Info Required
          </label>
          <div class="form-text">Additional attributes in cohort_xtra table</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdditionalCohortFields',
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
      formData: {},
      debug: false,
      componentMounted: false,
      formInitialized: false,
      dataTimestamp: null
    };
  },
  mounted() {
    console.log('AdditionalCohortFields MOUNTED with data:', this.cohortData);
    this.componentMounted = true;
    this.debug = this.$route.query.debug === 'true';
    this.initializeForm();
  },
  methods: {
    initializeForm() {
      if (!this.cohortData || !this.cohortData.cohort_id) {
        console.log('No cohort data available for initialization');
        return;
      }

      console.log('Initializing form with cohort data:', this.cohortData);
      
      this.formData = {
        op_id: this.cohortData.op_id || null,
        op_date: this.formatDateTimeForInput(this.cohortData.op_date),
        pct_area: this.cohortData.pct_area || null,
        year_last_cut: this.cohortData.year_last_cut || null,
        treatments: !!this.cohortData.treatments,
        regen_date: this.formatDateTimeForInput(this.cohortData.regen_date),
        regen_date2: this.formatDateTimeForInput(this.cohortData.regen_date2),
        regen_method: this.cohortData.regen_method || '',
        regen_done: !!this.cohortData.regen_done,
        complete_date: this.formatDateTimeForInput(this.cohortData.complete_date),
        target_ba_m2ha: this.cohortData.target_ba_m2ha || null,
        resid_ba_m2ha: this.cohortData.resid_ba_m2ha || null,
        target_spha: this.cohortData.target_spha || null,
        resid_spha: this.cohortData.resid_spha || null,
        herbicide_app_spec: this.cohortData.herbicide_app_spec || '',
        vrp: this.cohortData.vrp || null,
        vrp_tot_area: this.cohortData.vrp_tot_area || null,
        extra_info: !!this.cohortData.extra_info,
        stand: this.cohortData.stand || ''
      };

      this.formInitialized = true;
      this.dataTimestamp = new Date().toISOString();
      console.log('Form initialized successfully:', this.formData);
    },
    
    formatDateTimeForInput(dateTimeString) {
      if (!dateTimeString) return '';
      try {
        const date = new Date(dateTimeString);
        if (isNaN(date.getTime())) {
          console.warn('Invalid date:', dateTimeString);
          return '';
        }
        return date.toISOString().slice(0, 16);
      } catch (error) {
        console.error('Error formatting date:', dateTimeString, error);
        return '';
      }
    }
  }
};
</script>

<style scoped>
.additional-cohort-fields {
  max-height: 70vh;
  overflow-y: auto;
}

.form-text {
  font-size: 0.75rem;
  color: #6c757d;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.form-control:read-only {
  background-color: #e9ecef;
  opacity: 1;
}

.debug-info {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 10px;
  margin-bottom: 15px;
  font-size: 0.875rem;
}
</style>
