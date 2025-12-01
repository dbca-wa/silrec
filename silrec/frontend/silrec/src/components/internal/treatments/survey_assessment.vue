<template>
  <div class="survey-assessment">
    <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/internal/treatments/survey_assessment.vue</div>

    <!-- Documents Table -->
    <div class="table-responsive" v-if="documents.length > 0">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Type</th>
            <th>Title</th>
            <th>File</th>
            <th>Status</th>
            <th>Date</th>
            <th>Uploaded By</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="doc in documents" 
            :key="doc.document_id"
            :class="getRowClass(doc)"
          >
            <td>
              <span >
                {{ getDocumentTypeLabel(doc.document_type) }}
              </span>
            </td>
            <td class="document-title">
              <strong>{{ doc.title }}</strong>
              <div v-if="doc.description" class="text-muted small">
                {{ truncateText(doc.description, 50) }}
              </div>
              <span v-if="doc.marked_deleted" class="text-danger small">
                <i class="bi bi-exclamation-circle me-1"></i>Marked for deletion
              </span>
            </td>
            <td>
              <div v-if="doc.file">
                <i :class="doc.file_icon" class="me-1"></i>
                {{ truncateText(doc.file_name, 50) }}
                <small class="text-muted d-block">({{ doc.file_size_display }})</small>
              </div>
              <div v-else-if="doc.file_url">
                <i class="bi bi-link-45deg me-1"></i>
                <a :href="doc.file_url" target="_blank" class="text-truncate d-inline-block" style="max-width: 200px;">
                  {{ doc.file_url }}
                </a>
              </div>
              <span v-else class="text-muted">No file</span>
            </td>
            <td>
              <span class="badge" :class="getStatusBadge(doc.status)">
                {{ getStatusLabel(doc.status) }}
              </span>
            </td>
            <td>{{ formatDate(doc.document_date) }}</td>
            <td>{{ doc.uploaded_by_display || doc.uploaded_by || 'N/A' }}</td>
            <td>
              <div class="btn-group btn-group-sm">
                <button 
                  v-if="doc.file || doc.file_url"
                  class="btn btn-outline-primary"
                  @click="viewDocument(doc)"
                  title="View Document"
                  :disabled="doc.marked_deleted"
                >
                  <i class="bi bi-eye"></i>
                </button>
                <button 
                  v-if="!readOnly"
                  class="btn btn-sm btn-outline-primary"
                  @click="editDocument(doc)"
                  title="Edit Document"
                  :disabled="doc.marked_deleted"
                >
                  <i class="bi bi-pencil"></i>
                </button>
                <button 
                  v-if="!readOnly"
                  class="btn btn-outline-danger"
                  @click="deleteDocument(doc)"
                  :title="doc.marked_deleted ? 'Restore Document' : 'Delete Document'"
                >
                  <i :class="doc.marked_deleted ? 'bi bi-arrow-counterclockwise' : 'bi bi-trash'"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-else class="text-center py-4 text-muted">
      <p>No survey or assessment documents found for this treatment.</p>
    </div>

    <!-- Add/Edit Document Modal -->
    <div class="modal fade" :class="{ 'show d-block': showDocumentModal }" tabindex="-1" v-if="showDocumentModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header py-2">
            <h5 class="modal-title h6">{{ editingDocument ? 'Edit Document' : 'Add New Document' }}</h5>
            <button type="button" class="btn-close btn-sm" @click="closeModal"></button>
          </div>
          <div class="modal-body py-2">
            <form @submit.prevent="saveDocument">
              <div class="row g-2">
                <div class="col-md-4">
                  <div class="form-group mb-1">
                    <label for="documentType" class="form-label small fw-bold">Document Type *</label>
                    <select
                      id="documentType"
                      v-model="documentData.document_type"
                      class="form-select form-select-sm"
                      :disabled="readOnly"
                      required
                    >
                      <option value="">Select Type</option>
                      <option v-for="type in documentTypes" :key="type.value" :value="type.value">
                        {{ type.label }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="form-group mb-1">
                    <label for="documentStatus" class="form-label small fw-bold">Status</label>
                    <select
                      id="documentStatus"
                      v-model="documentData.status"
                      class="form-select form-select-sm"
                      :disabled="readOnly"
                    >
                      <option v-for="status in statusChoices" :key="status.value" :value="status.value">
                        {{ status.label }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="col-md-4">
                  <div class="form-group mb-1">
                    <label for="documentDate" class="form-label small fw-bold">Document Date</label>
                    <input
                      id="documentDate"
                      v-model="documentData.document_date"
                      type="date"
                      class="form-control form-control-sm"
                      :readonly="readOnly"
                    />
                  </div>
                </div>
              </div>

              <div class="row mt-1">
                <div class="col-md-12">
                  <div class="form-group mb-1">
                    <label for="documentTitle" class="form-label small fw-bold">Title *</label>
                    <input
                      id="documentTitle"
                      v-model="documentData.title"
                      type="text"
                      class="form-control form-control-sm"
                      :readonly="readOnly"
                      placeholder="Enter document title..."
                      required
                    />
                  </div>
                </div>
              </div>

              <div class="row mt-1">
                <div class="col-md-12">
                  <div class="form-group mb-1">
                    <label for="documentDescription" class="form-label small fw-bold">Description</label>
                    <textarea
                      id="documentDescription"
                      v-model="documentData.description"
                      class="form-control form-control-sm"
                      rows="2"
                      :readonly="readOnly"
                      placeholder="Enter document description..."
                    ></textarea>
                  </div>
                </div>
              </div>


              <div class="row mt-1">
                  <div class="col-md-12">
                    <div class="form-group mb-1">
                      <label class="form-label small fw-bold">Document Source</label>
                      <div class="row">
                        <div class="col-auto">
                          <div class="form-check">
                            <input
                              id="sourceFile"
                              v-model="documentSource"
                              type="radio"
                              value="file"
                              class="form-check-input"
                              :disabled="readOnly"
                            />
                            <label for="sourceFile" class="form-check-label ms-1">Upload File</label>
                          </div>
                        </div>
                        <div class="col-auto">
                          <div class="form-check">
                            <input
                              id="sourceUrl"
                              v-model="documentSource"
                              type="radio"
                              value="url"
                              class="form-check-input"
                              :disabled="readOnly"
                            />
                            <label for="sourceUrl" class="form-check-label ms-1">External URL</label>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
              </div>

              <div class="row mt-1" v-if="documentSource === 'file'">
                <div class="col-md-12">
                  <div class="form-group mb-1">
                    <label for="documentFile" class="form-label small fw-bold">Upload File</label>
                    <input
                      id="documentFile"
                      type="file"
                      class="form-control form-control-sm"
                      :disabled="readOnly"
                      @change="handleFileUpload"
                      ref="fileInput"
                      accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.bmp,.zip,.rar,.7z"
                    />
                    <div class="form-text small">
                      Supported formats: PDF, Word, Excel, Images, Compressed files. Max size: 50MB
                    </div>
                    <div v-if="uploadedFile" class="mt-1">
                      <span class="badge bg-info small">
                        <i :class="getFileIcon(uploadedFile.name)" class="me-1"></i>
                        {{ uploadedFile.name }} ({{ formatFileSize(uploadedFile.size) }})
                      </span>
                    </div>
                    <!-- Show existing file in edit mode -->
                    <div v-else-if="editingDocument && editingDocument.file_name" class="mt-1">
                      <span class="badge bg-secondary small">
                        <i :class="editingDocument.file_icon || getFileIcon(editingDocument.file_name)" class="me-1"></i>
                        {{ editingDocument.file_name }}
                        <span v-if="editingDocument.file_size_display" class="ms-1">({{ editingDocument.file_size_display }})</span>
                      </span>
                      <div class="form-text small mt-1">
                        Existing file. Upload a new file to replace.
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="row mt-1" v-if="documentSource === 'url'">
                <div class="col-md-12">
                  <div class="form-group mb-1">
                    <label for="documentUrl" class="form-label small fw-bold">Document URL</label>
                    <input
                      id="documentUrl"
                      v-model="documentData.file_url"
                      type="url"
                      class="form-control form-control-sm"
                      :readonly="readOnly"
                      placeholder="https://example.com/document.pdf"
                    />
                  </div>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer py-2">
            <button type="button" class="btn btn-sm btn-secondary" @click="closeModal">
              Cancel
            </button>
            <button 
              type="button" 
              class="btn btn-sm btn-primary" 
              @click="saveDocument" 
              :disabled="saving || !isFormValid"
            >
              <span v-if="saving" class="spinner-border spinner-border-sm me-1"></span>
              {{ saving ? 'Saving...' : (editingDocument ? 'Update' : 'Save') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Modal Backdrop -->
    <div class="modal-backdrop fade show" v-if="showDocumentModal"></div>
  </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
  name: 'SurveyAssessment',
  props: {
    treatmentId: {
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
      documents: [],
      documentData: {
        document_type: 'survey',
        title: '',
        description: '',
        file: null,
        file_url: '',
        status: 'draft',
        document_date: new Date().toISOString().split('T')[0],
        treatment: this.treatmentId
      },
      documentSource: 'file',
      uploadedFile: null,
      documentTypes: [],
      statusChoices: [],
      showDocumentModal: false,
      editingDocument: null,
      saving: false
    };
  },
  computed: {
    isFormValid() {
      if (!this.documentData.title || !this.documentData.document_type) {
        return false;
      }
      
      // For edit mode with existing file, allow saving even if no new file is uploaded
      if (this.documentSource === 'file' && !this.uploadedFile && !this.editingDocument?.file) {
        return false;
      }
      
      if (this.documentSource === 'url' && !this.documentData.file_url) {
        return false;
      }
      
      return true;
    }
  },
  methods: {
    async loadDocuments() {
      try {
        const response = await fetch(`${api_endpoints.survey_assessment_documents}?treatment_id=${this.treatmentId}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        // Initialize marked_deleted property for each document
        this.documents = (data.results || data).map(doc => ({
          ...doc,
          marked_deleted: doc.marked_deleted || false
        }));
      } catch (error) {
        console.error('Error loading documents:', error);
        await this.showError('Load Failed', 'Failed to load survey/assessment documents');
      }
    },
    
    async loadLookups() {
      try {
        const [typesResponse, statusesResponse] = await Promise.all([
          fetch(`${api_endpoints.survey_assessment_documents}document_types/`),
          fetch(`${api_endpoints.survey_assessment_documents}status_choices/`)
        ]);
        
        if (typesResponse.ok) {
          this.documentTypes = await typesResponse.json();
        }
        
        if (statusesResponse.ok) {
          this.statusChoices = await statusesResponse.json();
        }
      } catch (error) {
        console.error('Error loading lookups:', error);
      }
    },
    
    async saveDocument() {
      if (!this.validateForm()) {
        return;
      }

      this.saving = true;
      try {
        const formData = new FormData();
        
        // Append all document data to formData
        Object.keys(this.documentData).forEach(key => {
          if (key !== 'file' && this.documentData[key] !== null) {
            formData.append(key, this.documentData[key]);
          }
        });
        formData.append('treatment_id', this.treatmentId);
        
        // Append file if uploaded
        if (this.uploadedFile) {
          formData.append('file', this.uploadedFile);
        } else if (this.editingDocument && this.editingDocument.file && this.documentSource === 'file') {
          // In edit mode with existing file but no new file uploaded
          // We need to indicate that we want to keep the existing file
          // This depends on your backend API - you might need to handle it differently
          formData.append('keep_existing_file', 'true');
        }
        
        let url, method;
        if (this.editingDocument) {
          url = `${api_endpoints.survey_assessment_documents}${this.editingDocument.document_id}/`;
          method = 'PATCH';
        } else {
          url = api_endpoints.survey_assessment_documents;
          method = 'POST';
        }

        console.log('URL:', url);
        console.log('Method:', method);
        console.log('Form data keys:', Array.from(formData.keys()));
        
        const response = await fetch(url, {
          method: method,
          headers: {
            'X-CSRFToken': this.getCSRFToken()
          },
          body: formData
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error('Backend error response:', errorData);
          throw new Error(`HTTP error! status: ${response.status}, details: ${JSON.stringify(errorData)}`);
        }

        await this.showSuccess('Success!', `Document ${this.editingDocument ? 'updated' : 'created'} successfully`);
        
        this.closeModal();
        await this.loadDocuments();
        this.$emit('document-updated');

      } catch (error) {
        console.error('Error saving document:', error);
        await this.handleSaveError(error);
      } finally {
        this.saving = false;
      }
    },
    
    async deleteDocument(document) {
      // If document is already marked as deleted, restore it
      if (document.marked_deleted) {
        try {
          const response = await fetch(`${api_endpoints.survey_assessment_documents}${document.document_id}/`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ marked_deleted: false })
          });

          if (!response.ok) {
            // Try to get more detailed error information
            let errorText = 'Unknown error';
            try {
              const errorData = await response.json();
              console.error('Backend error response:', errorData);
              errorText = JSON.stringify(errorData);
            } catch (e) {
              errorText = await response.text();
            }
            throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
          }

          document.marked_deleted = false;
          this.documents = [...this.documents];
          await this.showSuccess('Restored!', 'Document has been restored');
          this.$emit('document-updated');
        } catch (error) {
          console.error('Error restoring document:', error);
          await this.showError('Restore Failed', 'Failed to restore document: ' + error.message);
        }
        return;
      }

      // For draft status - allow physical delete
      if (document.status === 'draft') {
        const result = await swal.fire({
          icon: 'warning',
          title: 'Delete Document?',
          text: 'Are you sure you want to delete this document? This action cannot be undone.',
          showCancelButton: true,
          confirmButtonText: 'Yes, delete it!',
          cancelButtonText: 'Cancel',
          confirmButtonColor: '#d33'
        });

        if (result.isConfirmed) {
          try {
            const response = await fetch(`${api_endpoints.survey_assessment_documents}${document.document_id}/`, {
              method: 'DELETE',
              headers: {
                'X-CSRFToken': this.getCSRFToken()
              }
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            await this.showSuccess('Deleted!', 'Document has been deleted successfully');
            await this.loadDocuments();
            this.$emit('document-updated');
          } catch (error) {
            console.error('Error deleting document:', error);
            await this.showError('Delete Failed', 'Failed to delete document');
          }
        }
      } else {
        // For non-draft status - mark as deleted in backend and UI
        const result = await swal.fire({
          icon: 'info',
          title: 'Mark Document for Deletion?',
          html: `
            <div class="text-start">
              <p>This document has status: <strong>${this.getStatusLabel(document.status)}</strong></p>
              <p>Non-draft documents cannot be permanently deleted.</p>
              <p>The document will be:</p>
              <ul class="text-start">
                <li>Struck through in the list</li>
                <li>Viewable but not editable</li>
                <li>Restorable by clicking the delete icon again</li>
              </ul>
            </div>
          `,
          showCancelButton: true,
          confirmButtonText: 'Mark for Deletion',
          cancelButtonText: 'Cancel',
          confirmButtonColor: '#6c757d'
        });

        if (result.isConfirmed) {
          try {
            // Make PATCH request to update marked_deleted field in backend
            const response = await fetch(`${api_endpoints.survey_assessment_documents}${document.document_id}/`, {
              method: 'PATCH',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
              },
              body: JSON.stringify({ marked_deleted: true })
            });

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Update the local state
            document.marked_deleted = true;
            this.documents = [...this.documents]; // Trigger reactivity
            await this.showSuccess('Marked!', 'Document has been marked for deletion');
            this.$emit('document-updated');
          } catch (error) {
            console.error('Error marking document as deleted:', error);
            await this.showError('Mark Failed', 'Failed to mark document as deleted');
          }
        }
      }
    },
    
    viewDocument(document) {
      if (document.marked_deleted) {
        this.showInfo('Document Marked for Deletion', 'This document is marked for deletion but can still be viewed.');
      }
      
      if (document.file_url) {
        window.open(document.file_url, '_blank');
      } else if (document.file) {
        this.downloadDocument(document, true);
      }
    },
    
    async downloadDocument(document, openInNewTab = false) {
      try {
        if (document.file_url) {
          if (openInNewTab) {
            window.open(document.file_url, '_blank');
          } else {
            window.location.href = document.file_url;
          }
          return;
        }
        
        const response = await fetch(`${api_endpoints.survey_assessment_documents}${document.document_id}/download/`, {
          headers: {
            'X-CSRFToken': this.getCSRFToken()
          }
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        if (openInNewTab && this.isFileTypeViewable(document.file_type)) {
          window.open(url, '_blank');
        } else {
          const a = document.createElement('a');
          a.href = url;
          a.download = document.file_name || 'document';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }
        
        setTimeout(() => window.URL.revokeObjectURL(url), 100);
        
      } catch (error) {
        console.error('Error downloading document:', error);
        await this.showError('Download Failed', 'Failed to download document');
      }
    },
    
    isFileTypeViewable(fileType) {
      const viewableTypes = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp'];
      return viewableTypes.includes(fileType?.toLowerCase());
    },
    
    editDocument(document) {
      if (document.marked_deleted) {
        this.showInfo('Cannot Edit', 'This document is marked for deletion and cannot be edited.');
        return;
      }
      
      this.editingDocument = document;
      this.documentData = {
        document_type: document.document_type,
        title: document.title,
        description: document.description || '',
        file_url: document.file_url || '',
        status: document.status,
        document_date: document.document_date ? document.document_date.split('T')[0] : new Date().toISOString().split('T')[0],
        treatment: this.treatmentId
      };
      
      // Determine source based on whether there's a file or URL
      this.documentSource = document.file_url ? 'url' : 'file';
      this.uploadedFile = null;
      this.showDocumentModal = true;
    },
    
    addNewDocument() {
      this.editingDocument = null;
      this.documentData = {
        document_type: 'survey',
        title: '',
        description: '',
        file: null,
        file_url: '',
        status: 'draft',
        document_date: new Date().toISOString().split('T')[0],
        treatment: this.treatmentId
      };
      this.documentSource = 'file';
      this.uploadedFile = null;
      this.showDocumentModal = true;
    },
    
    handleFileUpload(event) {
      const file = event.target.files[0];
      if (file) {
        if (file.size > 50 * 1024 * 1024) {
          this.showError('File Too Large', 'File size must be less than 50MB');
          this.$refs.fileInput.value = '';
          return;
        }
        
        const allowedExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'zip', 'rar', '7z'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!allowedExtensions.includes(fileExtension)) {
          this.showError('Invalid File Type', `Allowed types: ${allowedExtensions.join(', ')}`);
          this.$refs.fileInput.value = '';
          return;
        }
        
        this.uploadedFile = file;
        this.documentData.file_url = '';
      }
    },
    
    closeModal() {
      this.showDocumentModal = false;
      this.editingDocument = null;
      this.resetDocumentForm();
    },
    
    resetDocumentForm() {
      this.documentData = {
        document_type: 'survey',
        title: '',
        description: '',
        file: null,
        file_url: '',
        status: 'draft',
        document_date: new Date().toISOString().split('T')[0],
        treatment: this.treatmentId
      };
      this.documentSource = 'file';
      this.uploadedFile = null;
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },
    
    validateForm() {
      if (!this.documentData.title.trim()) {
        this.showError('Validation Error', 'Title is required');
        return false;
      }
      
      if (!this.documentData.document_type) {
        this.showError('Validation Error', 'Document type is required');
        return false;
      }
      
      if (this.documentSource === 'file' && !this.uploadedFile && !this.editingDocument?.file) {
        this.showError('Validation Error', 'Please select a file to upload');
        return false;
      }
      
      if (this.documentSource === 'url' && !this.documentData.file_url.trim()) {
        this.showError('Validation Error', 'Please enter a valid URL');
        return false;
      }
      
      return true;
    },
    
    async handleSaveError(error) {
      let errorMessage = 'Failed to save document';
      
      if (error.message && error.message.includes('details:')) {
        try {
          const details = error.message.split('details:')[1];
          const errorData = JSON.parse(details);
          errorMessage = typeof errorData === 'object' ? 
            (errorData.error || Object.values(errorData).flat().join(', ')) : 
            details;
        } catch (e) {
          errorMessage = error.message;
        }
      }
      
      await this.showError('Save Error', errorMessage);
    },
    
    getDocumentTypeLabel(type) {
      const typeObj = this.documentTypes.find(t => t.value === type);
      return typeObj ? typeObj.label : type;
    },
    
    getStatusLabel(status) {
      const statusObj = this.statusChoices.find(s => s.value === status);
      return statusObj ? statusObj.label : status;
    },
    
    getDocumentTypeBadge(type) {
      const badgeClasses = {
        survey: 'bg-primary',
        assessment: 'bg-success',
        photo: 'bg-info',
        map: 'bg-warning',
        other: 'bg-secondary'
      };
      return badgeClasses[type] || 'bg-secondary';
    },
    
    getStatusBadge(status) {
      const badgeClasses = {
        draft: 'bg-secondary',
        final: 'bg-success',
        reviewed: 'bg-info',
        archived: 'bg-warning'
      };
      return badgeClasses[status] || 'bg-secondary';
    },
    
    getFileIcon(fileName) {
      if (!fileName) return 'bi-file-earmark';
      const extension = fileName.split('.').pop().toLowerCase();
      const iconMap = {
        pdf: 'bi-file-pdf',
        doc: 'bi-file-word',
        docx: 'bi-file-word',
        xls: 'bi-file-excel',
        xlsx: 'bi-file-excel',
        jpg: 'bi-file-image',
        jpeg: 'bi-file-image',
        png: 'bi-file-image',
        gif: 'bi-file-image',
        bmp: 'bi-file-image',
        zip: 'bi-file-zip',
        rar: 'bi-file-zip',
        '7z': 'bi-file-zip'
      };
      return iconMap[extension] || 'bi-file-earmark';
    },
    
    formatFileSize(bytes) {
      if (!bytes) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    truncateText(text, length) {
      if (!text) return '';
      return text.length > length ? text.substring(0, length) + '...' : text;
    },
    
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },
    
    // New method to get row classes
    getRowClass(doc) {
      const classes = [];
      if (doc.marked_deleted) {
        classes.push('deleted-row');
      }
      return classes;
    },
    
    async showSuccess(title, text) {
      await swal.fire({
        icon: 'success',
        title: title,
        text: text,
        timer: 3000,
        showConfirmButton: false
      });
    },
    
    async showError(title, text) {
      await swal.fire({
        icon: 'error',
        title: title,
        text: text,
        confirmButtonText: 'OK'
      });
    },

    async showInfo(title, text) {
      await swal.fire({
        icon: 'info',
        title: title,
        text: text,
        confirmButtonText: 'OK'
      });
    },
    
    getCSRFToken() {
      const name = 'csrftoken';
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  },
  mounted() {
    this.loadDocuments();
    this.loadLookups();
  },
  watch: {
    treatmentId: {
      handler(newVal) {
        if (newVal) {
          this.loadDocuments();
          this.resetDocumentForm();
        }
      },
      immediate: true
    },
    
    documentSource(newSource) {
      if (newSource === 'file') {
        this.documentData.file_url = '';
      } else if (newSource === 'url') {
        this.uploadedFile = null;
        if (this.$refs.fileInput) {
          this.$refs.fileInput.value = '';
        }
      }
    }
  }
};
</script>

<style scoped>
.survey-assessment {
  margin-bottom: 1rem;
}

.document-title {
  max-width: 250px;
}

.table {
  font-size: 0.875rem;
}

.btn-group-sm > .btn {
  padding: 0.25rem 0.5rem;
}

.badge {
  font-size: 0.75rem;
}

/* Deleted row styling - Fixed to apply to all cells */
.deleted-row td {
  text-decoration: line-through !important;
  opacity: 0.7;
}

.deleted-row:hover td {
  background-color: #f8f9fa !important;
  opacity: 0.9;
}

/* Modal Styles - More Compact */
.modal {
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-dialog {
  max-width: 700px;
}

.modal-content {
  border: none;
  border-radius: 0.375rem;
  box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
}

.modal-header {
  border-bottom: 1px solid #dee2e6;
  padding: 0.5rem 1rem;
  background-color: white;
}

.modal-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.modal-body {
  padding: 0.5rem 1rem;
  background-color: white;
}

.modal-footer {
  border-top: 1px solid #dee2e6;
  padding: 0.5rem 1rem;
  background-color: white;
}

.form-group {
  margin-bottom: 0.5rem;
}

.form-label {
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #495057;
  font-size: 0.85rem;
}

.form-text {
  font-size: 0.8rem;
  color: #6c757d;
}

.form-check {
  margin-bottom: 0;
}

/* Smaller form controls */
.form-control-sm,
.form-select-sm {
  font-size: 0.85rem;
  padding: 0.25rem 0.5rem;
}

/* Smaller buttons */
.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.85rem;
}

/* Fix for form-check labels not being visible */
.form-check .form-check-label {
  font-size: 0.9rem !important;
  color: #495057 !important;
}
</style>
