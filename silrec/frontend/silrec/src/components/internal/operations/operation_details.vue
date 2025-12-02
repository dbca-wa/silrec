<template>
  <div class="container mt-4">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/operations/operation_details.vue</div>
    <div class="header-actions mb-4">
      <button class="btn btn-secondary" @click="goBack">
        <i class="bi bi-arrow-left"></i> Back
      </button>
      <h2 class="page-title">
        {{ operationId ? (readOnly ? 'View Operation' : 'Edit Operation') : 'Add New Operation' }}
      </h2>
    </div>

    <div class="card">
      <div class="card-body">
        <OperationForm
          :operation-id="operationId"
          :cohort-id="$route.params.cohortId"
          :fea-id="feaId"
          :read-only="readOnly"
          @operation-saved="handleOperationSaved"
          @cancel="goBack"
        />
      </div>
    </div>
  </div>
</template>

<script>
import OperationForm from './operations_form.vue';

export default {
  name: 'OperationDetails',
  components: {
    OperationForm
  },
  props: {
    operationId: {
      type: [String, Number],
      default: null
    },
    cohortId: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      feaId: '',
      readOnly: false
    };
  },
  computed: {
    isEditMode() {
      return this.$route.name === 'edit-operation';
    },
    isViewMode() {
      return this.$route.name === 'view-operation';
    },
    isNewMode() {
      return this.$route.name === 'new-operation';
    }
  },
  methods: {
    goBack() {
      this.$router.go(-1);
    },
    handleOperationSaved(operationData) {
      // Navigate back to cohort detail
      this.$router.push(`/internal/cohorts/${this.$route.params.cohortId}`);
    }
  },
  mounted() {
    // Set read-only based on route
    this.readOnly = this.isViewMode;
    
    // If in new mode and cohortId is provided, try to get FEA ID
    if (this.isNewMode && this.cohortId) {
      // This would typically come from an API call
      // For now, we'll leave it empty and let the form handle it
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
