<template>
  <div class="cohort-detail-container">
    <div v-if="debug">internal/proposals/cohorts/cohort_detail.vue</div>
    <div class="header-actions mb-4">
      <button class="btn btn-secondary" @click="$router.push('/')">
        <i class="bi bi-arrow-left"></i> Back to Map
      </button>
      <h2 class="page-title">
        Cohort Details - 
        <span v-if="cohortData.obj_code">Objective: {{ cohortData.obj_code }}</span>
        <span v-else>Cohort {{ $route.params.cohortId }}</span>
      </h2>
      
      <!-- Add Treatment Button -->
      <router-link 
        v-if="canEdit"
        :to="`/internal/cohort/${$route.params.cohortId}/treatment/new`"
        class="btn btn-primary"
      >
        <i class="bi bi-plus"></i> Add Treatment
      </router-link>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Cohort Information -->
    <div v-if="!loading && !error" class="card mb-4">
      <div class="card-header">
        <h5 class="card-title mb-0">Cohort Information</h5>
      </div>
      <div class="card-body">
        <CohortForm 
          :cohort-id="$route.params.cohortId"
          :polygon-id="$route.params.polygonId"
          :read-only="!canEdit"
          @cohort-updated="handleCohortUpdated"
          @error="handleError"
        />
      </div>
    </div>

    <!-- Treatments Section -->
    <div v-if="!loading && !error" class="card">
      <div class="card-header">
        <h5 class="card-title mb-0">Treatments</h5>
      </div>
      <div class="card-body">
        <TreatmentsTable 
          ref="treatmentsTable"
          :cohort-id="$route.params.cohortId"
          :read-only="!canEdit"
          @treatment-updated="refreshTreatments"
        />
      </div>
    </div>
  </div>
</template>

<script>
import CohortForm from '@/components/internal/cohorts/cohort_form.vue';
import TreatmentsTable from '@/components/internal/treatments/treatments_table.vue';
import { api_endpoints, helpers } from '@/utils/hooks';

export default {
  name: 'CohortDetail',
  components: {
    CohortForm,
    TreatmentsTable
  },
  data() {
    return {
      loading: false,
      error: null,
      cohortData: {},
      userPermissions: []
    };
  },
  computed: {
    canEdit() {
      return true;
      const editRoles = ['Assessors', 'Reviewers', 'Silrec Admin'];
      return this.userPermissions.some(perm => editRoles.includes(perm));
    },
    debug: function () {
        if (this.$route.query.debug) {
            return this.$route.query.debug === 'true';
        }
        return false;
    },
  },
  methods: {
    async loadCohortData() {
        this.loading = true;
        this.error = null;
        
        try {
          console.log('Loading cohort data from:', `${api_endpoints.cohorts}${this.$route.params.cohortId}/`);
          
          const response = await fetch(`${api_endpoints.cohorts}${this.$route.params.cohortId}/`);
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const data = await response.json();
          this.cohortData = data;
          console.log('Cohort data loaded successfully:', this.cohortData);
          
        } catch (error) {
          console.error('Error loading cohort data:', error);
          this.error = 'Failed to load cohort data. Please check if the cohort exists.';
        } finally {
          this.loading = false;
        }
    },

    handleCohortUpdated(updatedData) {
      this.cohortData = { ...this.cohortData, ...updatedData };
      this.$emit('cohort-updated');
    },
    refreshTreatments() {
      if (this.$refs.treatmentsTable) {
        this.$refs.treatmentsTable.refreshData();
      }
    },
    handleError(errorMessage) {
      this.error = errorMessage;
    },
    loadUserPermissions() {
      this.userPermissions = helpers.getUserPermissions();
    }
  },
  mounted() {
    this.loadCohortData();
    this.loadUserPermissions();
  },
  watch: {
    '$route.params.cohortId': {
      handler() {
        this.loadCohortData();
      },
      immediate: true
    }
  }
};
</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.page-title {
  margin: 0;
  flex-grow: 1;
}
</style>
