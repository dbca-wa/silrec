<template>
  <div class="treatment-extras-table">
    <div v-if="loading" class="text-center p-3">
      <div class="spinner-border spinner-border-sm" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <span class="ms-2">Loading treatment details...</span>
    </div>

    <div v-else-if="error" class="alert alert-warning">
      <i class="bi bi-exclamation-triangle"></i> {{ error }}
    </div>

    <div v-else-if="treatmentExtras.length === 0" class="text-muted text-center p-3">
      <i class="bi bi-info-circle"></i> No additional treatment details found.
    </div>

    <div v-else class="table-responsive">
      <table class="table table-sm table-striped">
        <thead>
          <tr>
            <th>Reschedule Reason</th>
            <th>Success Rate</th>
            <th>Stocking Rate</th>
            <th>Species Assessed</th>
            <th>Assessment Type</th>
            <th v-if="!readOnly">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="extra in treatmentExtras" :key="extra.treatment_xtra_id">
            <!-- ... existing table cells ... -->
            <td v-if="!readOnly" class="action-column">
              <router-link 
                :to="`/internal/treatment-extra/${extra.treatment_xtra_id}`"
                class="btn btn-sm btn-outline-primary me-1"
                title="Edit Details"
              >
                <i class="bi bi-pencil"></i>
              </router-link>
              <button 
                class="btn btn-sm btn-outline-danger"
                @click="deleteExtra(extra.treatment_xtra_id)"
                title="Delete Details"
              >
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- Add Extra Button -->
      <div v-if="!readOnly && treatmentId" class="mt-3">
        <router-link 
          :to="`/internal/treatment/${treatmentId}/extra/new`"
          class="btn btn-outline-primary btn-sm"
        >
          <i class="bi bi-plus"></i> Add Treatment Details
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'TreatmentExtrasTable',
  // ... rest of the component remains the same, remove modal-related code
  methods: {
    // Remove editExtra, addExtra, closeEditModal methods
    // Keep loadTreatmentExtras, deleteExtra, refreshData
  }
};
</script>
