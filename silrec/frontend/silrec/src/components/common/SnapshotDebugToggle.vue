<template>
  <div v-if="showDebug" class="snapshot-debug-container" :class="{ 'expanded': expanded }">
    <div class="debug-toggle" @click="expanded = !expanded">
      <i class="bi" :class="expanded ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
      <span class="badge bg-secondary">Debug Mode</span>
      <span class="badge" :class="enabled ? 'bg-success' : 'bg-secondary'">
        {{ enabled ? 'Enabled' : 'Disabled' }}
      </span>
    </div>
    
    <div v-if="expanded" class="debug-panel">
      <div class="debug-header">
        <h6>Snapshot Debug Tools</h6>
        <div class="debug-controls">
          <button 
            class="btn btn-sm btn-outline-primary" 
            @click="toggleEnabled"
            :class="{ 'active': enabled }"
          >
            <i class="bi" :class="enabled ? 'bi-toggle-on' : 'bi-toggle-off'"></i>
            {{ enabled ? 'Disable' : 'Enable' }}
          </button>
        </div>
      </div>
      
      <div v-if="enabled" class="debug-content">
        <!-- Snapshot Creation Buttons -->
        <div class="row mb-2">
          <div class="col-6">
            <button 
              class="btn btn-sm btn-primary w-100"
              @click="createSnapshot('before_process')"
              :disabled="creatingSnapshot"
            >
              <span v-if="creatingSnapshot" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-camera me-1"></i>
              Take Before Snapshot
            </button>
          </div>
          <div class="col-6">
            <button 
              class="btn btn-sm btn-warning w-100"
              @click="createSnapshot('after_process')"
              :disabled="creatingSnapshot"
            >
              <span v-if="creatingSnapshot" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-camera me-1"></i>
              Take After Snapshot
            </button>
          </div>
        </div>
        
        <!-- List Snapshots Button -->
        <div class="row mb-2">
          <div class="col-12">
            <button 
              class="btn btn-sm btn-info w-100"
              @click="listSnapshots"
              :disabled="loadingSnapshots"
            >
              <span v-if="loadingSnapshots" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-list me-1"></i>
              List Snapshots
            </button>
          </div>
        </div>
        
        <!-- Snapshots List -->
        <div v-if="snapshots.length > 0" class="snapshot-list">
          <h6>Available Snapshots</h6>
          <div class="list-group">
            <div 
              v-for="snapshot in snapshots" 
              :key="snapshot.id"
              class="list-group-item list-group-item-action"
              :class="{ 'selected': selectedSnapshot === snapshot.id }"
              @click="selectSnapshot(snapshot)"
            >
              <div class="d-flex justify-content-between align-items-center">
                <div>
                  <strong>{{ snapshot.tag }}</strong>
                  <small class="text-muted d-block">
                    {{ formatDate(snapshot.timestamp) }}
                  </small>
                </div>
                <div>
                  <span class="badge bg-info">{{ snapshot.metadata?.record_counts?.polygon || 0 }} polygons</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Compare Button (visible when 2 snapshots selected) -->
          <div v-if="selectedSnapshot && selectedSnapshot2" class="mt-2">
            <button 
              class="btn btn-sm btn-success w-100"
              @click="compareSnapshots"
              :disabled="comparing"
            >
              <span v-if="comparing" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-bar-chart me-1"></i>
              Compare Selected Snapshots
            </button>
          </div>
        </div>
        
        <!-- Comparison Results -->
        <div v-if="comparisonResult" class="comparison-results mt-3">
          <h6>Comparison Results</h6>
          <div class="comparison-summary">
            <div class="alert" :class="comparisonResult.summary?.total_changes === 0 ? 'alert-success' : 'alert-warning'">
              <strong>Total Changes: {{ comparisonResult.summary?.total_changes || 0 }}</strong><br>
              Tables with changes: {{ comparisonResult.summary?.tables_with_changes?.length || 0 }}<br>
              Tables unchanged: {{ comparisonResult.summary?.tables_unchanged?.length || 0 }}
            </div>
          </div>
          
          <div class="table-changes">
            <div 
              v-for="(tableComp, tableName) in comparisonResult.tables" 
              :key="tableName"
              class="table-change-item"
              :class="{ 'has-changes': tableComp.has_changes }"
            >
              <div class="table-header" @click="toggleTableDetails(tableName)">
                <i class="bi" :class="expandedTables[tableName] ? 'bi-chevron-down' : 'bi-chevron-right'"></i>
                <strong>{{ tableName }}</strong>
                <span class="badge" :class="tableComp.has_changes ? 'bg-warning' : 'bg-success'">
                  {{ tableComp.count_before }} → {{ tableComp.count_after }}
                </span>
              </div>
              
              <div v-if="expandedTables[tableName] && tableComp.has_changes" class="table-details">
                <div class="row">
                  <div class="col-4">
                    <div class="change-stat">
                      <span class="label">Added:</span>
                      <span class="value text-success">{{ tableComp.added_count }}</span>
                    </div>
                  </div>
                  <div class="col-4">
                    <div class="change-stat">
                      <span class="label">Removed:</span>
                      <span class="value text-danger">{{ tableComp.removed_count }}</span>
                    </div>
                  </div>
                  <div class="col-4">
                    <div class="change-stat">
                      <span class="label">Modified:</span>
                      <span class="value text-warning">{{ tableComp.modified_count }}</span>
                    </div>
                  </div>
                </div>
                
                <div v-if="tableComp.modified && tableComp.modified.length > 0" class="modified-examples">
                  <small>Modified Examples:</small>
                  <ul>
                    <li v-for="mod in tableComp.modified.slice(0, 3)" :key="mod.id">
                      <span class="badge bg-secondary">{{ mod.id }}</span>
                      <ul>
                        <li v-for="diff in mod.differences.slice(0, 2)" :key="diff.field">
                          {{ diff.field }}: {{ truncateValue(diff.before) }} → {{ truncateValue(diff.after) }}
                        </li>
                      </ul>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api_endpoints, helpers } from '@/utils/hooks';
import Swal from 'sweetalert2';

export default {
  name: 'SnapshotDebugToggle',
  props: {
    proposalId: {
      type: Number,
      required: true
    },
    userId: {
      type: Number,
      required: true
    },
    showDebug: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      expanded: false,
      enabled: false,
      creatingSnapshot: false,
      loadingSnapshots: false,
      comparing: false,
      snapshots: [],
      selectedSnapshot: null,
      selectedSnapshot2: null,
      comparisonResult: null,
      expandedTables: {}
    };
  },
  mounted() {
    // Log when component is mounted for debugging
    console.log('SnapshotDebugToggle mounted', {
      proposalId: this.proposalId,
      userId: this.userId,
      showDebug: this.showDebug
    });
    
    // Auto-expand when debug is enabled
    if (this.showDebug) {
      this.expanded = true;
    }
  },
  methods: {
    toggleEnabled() {
      this.enabled = !this.enabled;
      if (this.enabled) {
        this.listSnapshots();
      } else {
        this.resetState();
      }
    },
    
    resetState() {
      this.snapshots = [];
      this.selectedSnapshot = null;
      this.selectedSnapshot2 = null;
      this.comparisonResult = null;
      this.expandedTables = {};
    },
    
    async createSnapshot(tag) {
      this.creatingSnapshot = true;
      
      try {
        const url = '/api/snapshot-debug/';
        const csrfToken = helpers.getCookie('csrftoken');
        
        const payload = {
          proposal_id: this.proposalId,
          user_id: this.userId,
          tag: tag
        };
        
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
          await Swal.fire({
            icon: 'success',
            title: 'Snapshot Created',
            html: `
              <p>Snapshot ID: <strong>${data.snapshot.id}</strong></p>
              <p>Tag: ${data.snapshot.tag}</p>
              <p>Records: ${JSON.stringify(data.snapshot.record_counts)}</p>
            `,
            timer: 3000
          });
          
          // Refresh snapshot list
          this.listSnapshots();
        } else {
          throw new Error(data.error || 'Failed to create snapshot');
        }
      } catch (error) {
        console.error('Error creating snapshot:', error);
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: error.message
        });
      } finally {
        this.creatingSnapshot = false;
      }
    },
    
    async listSnapshots() {
      this.loadingSnapshots = true;
      
      try {
        const url = `/api/snapshot-debug/?action=list&proposal_id=${this.proposalId}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
          this.snapshots = data.snapshots;
          console.log('Loaded snapshots:', this.snapshots);
        }
      } catch (error) {
        console.error('Error listing snapshots:', error);
      } finally {
        this.loadingSnapshots = false;
      }
    },
    
    selectSnapshot(snapshot) {
      if (!this.selectedSnapshot) {
        this.selectedSnapshot = snapshot.id;
        this.selectedSnapshot2 = null;
      } else if (!this.selectedSnapshot2 && this.selectedSnapshot !== snapshot.id) {
        this.selectedSnapshot2 = snapshot.id;
      } else {
        // Reset selection
        this.selectedSnapshot = snapshot.id;
        this.selectedSnapshot2 = null;
        this.comparisonResult = null;
      }
    },
    
    async compareSnapshots() {
      if (!this.selectedSnapshot || !this.selectedSnapshot2) return;
      
      this.comparing = true;
      
      try {
        const url = `/api/snapshot-debug/?action=compare&snapshot1=${this.selectedSnapshot}&snapshot2=${this.selectedSnapshot2}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
          this.comparisonResult = data.comparison;
          console.log('Comparison result:', this.comparisonResult);
        }
      } catch (error) {
        console.error('Error comparing snapshots:', error);
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: 'Failed to compare snapshots'
        });
      } finally {
        this.comparing = false;
      }
    },
    
    toggleTableDetails(tableName) {
      this.$set(this.expandedTables, tableName, !this.expandedTables[tableName]);
    },
    
    formatDate(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleString();
    },
    
    truncateValue(value) {
      if (value === null || value === undefined) return 'null';
      const str = String(value);
      return str.length > 30 ? str.substring(0, 30) + '...' : str;
    }
  }
};
</script>

<style scoped>
.snapshot-debug-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 2147483647; /* Maximum z-index value */
  max-width: 500px;
  font-size: 12px;
  pointer-events: auto;
}

.debug-toggle {
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
  transition: all 0.2s ease;
}

.debug-toggle:hover {
  background: #e9ecef;
  transform: scale(1.02);
}

.debug-panel {
  margin-top: 5px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  padding: 12px;
  max-height: 70vh;
  overflow-y: auto;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.debug-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 5px;
  border-bottom: 1px solid #eee;
}

.debug-header h6 {
  margin: 0;
  font-weight: 600;
  font-size: 13px;
}

.debug-controls .btn-sm {
  padding: 2px 8px;
  font-size: 11px;
}

.snapshot-list {
  max-height: 200px;
  overflow-y: auto;
  margin-top: 10px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.list-group-item {
  cursor: pointer;
  padding: 8px 10px;
  border-bottom: 1px solid #dee2e6;
  transition: background-color 0.2s;
}

.list-group-item:last-child {
  border-bottom: none;
}

.list-group-item:hover {
  background-color: #f8f9fa;
}

.list-group-item.selected {
  background-color: #e7f1ff;
  border-left: 3px solid #0d6efd;
}

.comparison-results {
  border-top: 1px solid #dee2e6;
  padding-top: 10px;
  margin-top: 10px;
}

.table-change-item {
  margin-bottom: 8px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  overflow: hidden;
}

.table-header {
  padding: 8px 10px;
  background: #f8f9fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.table-header i {
  font-size: 12px;
  width: 16px;
}

.table-details {
  padding: 10px;
  background: white;
  border-top: 1px solid #dee2e6;
}

.has-changes .table-header {
  background: #fff3cd;
  color: #856404;
}

.change-stat {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 3px;
  margin-bottom: 2px;
}

.change-stat .label {
  color: #6c757d;
}

.change-stat .value {
  font-weight: 600;
}

.modified-examples {
  margin-top: 8px;
  padding-top: 5px;
  border-top: 1px dashed #dee2e6;
}

.modified-examples small {
  color: #6c757d;
  display: block;
  margin-bottom: 5px;
}

.modified-examples ul {
  margin: 0;
  padding-left: 20px;
}

.modified-examples li {
  margin-bottom: 5px;
  font-size: 11px;
}

.modified-examples ul ul {
  margin-top: 2px;
  padding-left: 15px;
}

.badge {
  font-size: 10px;
  padding: 3px 6px;
}

/* Ensure the debug panel doesn't get hidden behind other elements */
.debug-panel {
  position: relative;
  z-index: 2147483646;
  margin-bottom: 55px;
}

/* Make sure the toggle is always visible */
.snapshot-debug-container.expanded .debug-toggle {
  background: #0d6efd;
  color: white;
}

.snapshot-debug-container.expanded .debug-toggle .badge.bg-secondary {
  background-color: rgba(255,255,255,0.2) !important;
  color: white;
}
</style>
