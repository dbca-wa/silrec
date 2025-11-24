<template>
  <div class="container">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/treatments/treatment_detail.vue</div>
    <div class="header-actions mb-4">
      <button class="btn btn-secondary" @click="goBack">
        <i class="bi bi-arrow-left"></i> Back
      </button>
      <h2 class="page-title">
        {{ isNew ? 'Add New Treatment' : 'Edit Treatment' }}
      </h2>
    </div>

    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-if="!loading && !error" class="card">
      <div class="card-body">
        <TreatmentForm
          :treatment-id="treatmentId"
          :cohort-id="cohortId"
          :read-only="readOnly"
          @treatment-saved="handleTreatmentSaved"
          @cancel="goBack"
          @error="handleError"
        />
      </div>
    </div>
<!--
-->
  </div>
</template>

<script>
import TreatmentForm from './treatments_form.vue';
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'TreatmentDetail',
  components: {
    TreatmentForm
  },
  props: {
    treatmentId: {
      type: [Number, String],
      default: null
    },
    cohortId: {
      type: [Number, String],
      default: null
    }
  },
  data() {
    return {
      loading: false,
      error: null,
      treatmentData: {},
      readOnly: false
    };
  },
  computed: {
    isNew() {
      return !this.treatmentId;
    }
  },
  methods: {
    goBack() {
        this.$router.go(-1);
    },
    handleTreatmentSaved(treatmentData) {
        this.$emit('treatment-saved', treatmentData);
        this.goBack();
    },
    handleError(errorMessage) {
        this.error = errorMessage;
        swal.fire({
            icon: 'error',
            title: 'Error',
            text: errorMessage,
            confirmButtonText: 'OK'
        });
    },
    async loadTreatmentData() {
        if (this.isNew) return;
        
        this.loading = true;
        try {
            const response = await fetch(`${api_endpoints.treatments}${this.treatmentId}/`);
            console.log("JM2 :" + `${api_endpoints.treatments}${this.treatmentId}/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.treatmentData = await response.json();
        } catch (error) {
            console.error('Error loading treatment data:', error);
            this.error = 'Failed to load treatment data';
            await swal.fire({
                icon: 'error',
                title: 'Load Failed',
                text: 'Failed to load treatment data',
                confirmButtonText: 'OK'
            });
        } finally {
            this.loading = false;
        }
    }
  },
  mounted() {
    this.loadTreatmentData();
  }
};
</script>

<style scoped>
.treatment-detail-container {
  padding: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.page-title {
  margin: 0;
  color: #333;
}
</style>
