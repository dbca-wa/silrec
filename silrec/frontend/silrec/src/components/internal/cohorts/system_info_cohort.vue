<template>
    <div class="system-information">
        <div class="system-info-grid">
            <div class="info-section">
                <h6 class="section-title">Created Details</h6>
                <div class="info-row">
                    <div class="info-label">Created On:</div>
                    <div class="info-value">
                        {{ formatDateTime(cohortData.created_on) }}
                    </div>
                </div>
                <div class="info-row">
                    <div class="info-label">Created By:</div>
                    <div class="info-value">
                        {{ cohortData.created_by || 'Not available' }}
                    </div>
                </div>
            </div>

            <div class="info-section">
                <h6 class="section-title">Last Modification</h6>
                <div class="info-row">
                    <div class="info-label">Updated On:</div>
                    <div class="info-value">
                        {{ formatDateTime(cohortData.updated_on) }}
                    </div>
                </div>
                <div class="info-row">
                    <div class="info-label">Updated By:</div>
                    <div class="info-value">
                        {{ cohortData.updated_by || 'Not available' }}
                    </div>
                </div>
            </div>

            <!--
      <div class="info-section">
        <h6 class="section-title">Cohort Metadata</h6>
        <div class="info-row">
          <div class="info-label">Cohort ID:</div>
          <div class="info-value">{{ cohortData.cohort_id }}</div>
        </div>
        <div class="info-row">
          <div class="info-label">Objective Code:</div>
          <div class="info-value">{{ cohortData.obj_code || 'Not set' }}</div>
        </div>
        <div class="info-row">
          <div class="info-label">Species:</div>
          <div class="info-value">{{ cohortData.species || 'Not set' }}</div>
        </div>
      </div>

      <div class="info-section">
        <h6 class="section-title">Status Flags</h6>
        <div class="info-row">
          <div class="info-label">Treatments:</div>
          <div class="info-value">
            <span class="badge" :class="cohortData.treatments ? 'bg-success' : 'bg-secondary'">
              {{ cohortData.treatments ? 'Yes' : 'No' }}
            </span>
          </div>
        </div>
        <div class="info-row">
          <div class="info-label">Regeneration Done:</div>
          <div class="info-value">
            <span class="badge" :class="cohortData.regen_done ? 'bg-success' : 'bg-secondary'">
              {{ cohortData.regen_done ? 'Yes' : 'No' }}
            </span>
          </div>
        </div>
        <div class="info-row">
          <div class="info-label">Extra Info:</div>
          <div class="info-value">
            <span class="badge" :class="cohortData.extra_info ? 'bg-warning' : 'bg-secondary'">
              {{ cohortData.extra_info ? 'Required' : 'Not required' }}
            </span>
          </div>
        </div>
      </div>
-->
        </div>

        <!-- Additional technical details -->
        <!--
    <div class="technical-details mt-4">
      <h6 class="section-title">Technical Details</h6>
      <div class="details-grid">
        <div class="detail-item">
          <span class="detail-label">Operation ID:</span>
          <span class="detail-value">{{ cohortData.op_id || 'N/A' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Operation Date:</span>
          <span class="detail-value">{{ formatDateTime(cohortData.op_date) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Year Last Cut:</span>
          <span class="detail-value">{{ cohortData.year_last_cut || 'N/A' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Stand:</span>
          <span class="detail-value">{{ cohortData.stand || 'N/A' }}</span>
        </div>
      </div>
    </div>
-->
    </div>
</template>

<script>
export default {
    name: 'SystemInformation',
    props: {
        cohortData: {
            type: Object,
            required: true,
        },
    },
    methods: {
        formatDateTime(dateTimeString) {
            if (!dateTimeString) return 'N/A';
            const date = new Date(dateTimeString);
            return date.toLocaleString('en-AU', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
            });
        },
    },
};
</script>

<style scoped>
.system-information {
    padding: 10px 0;
}

.system-info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

.info-section {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
}

.section-title {
    color: #495057;
    font-weight: 600;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #dee2e6;
    font-size: 0.9rem;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    padding: 4px 0;
}

.info-label {
    font-weight: 500;
    color: #6c757d;
    font-size: 0.85rem;
    flex: 1;
}

.info-value {
    font-weight: 400;
    color: #212529;
    font-size: 0.85rem;
    flex: 1;
    text-align: right;
}

.badge {
    font-size: 0.75rem;
    padding: 0.25em 0.6em;
}

.technical-details {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
}

.details-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.detail-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid #e9ecef;
}

.detail-item:last-child {
    border-bottom: none;
}

.detail-label {
    font-weight: 500;
    color: #6c757d;
    font-size: 0.8rem;
}

.detail-value {
    font-weight: 400;
    color: #212529;
    font-size: 0.8rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .system-info-grid {
        grid-template-columns: 1fr;
    }

    .details-grid {
        grid-template-columns: 1fr;
    }
}
</style>
