<template>
    <div class="silviculturist-comment">
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">
            src/components/internal/treatments/silviculturist_comment.vue
        </div>

        <!-- Comments Table -->
        <div class="table-responsive" v-if="comments.length > 0">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Comment</th>
                        <th>Required Action</th>
                        <th>Action Complete</th>
                        <th>Created By</th>
                        <th>Created On</th>
                        <th v-if="!readOnly">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="comment in comments" :key="comment.s_comment_id">
                        <td class="comment-text">
                            {{ truncateText(comment.comment, 50) }}
                        </td>
                        <td>{{ comment.required_action || 'N/A' }}</td>
                        <td>
                            <span
                                v-if="comment.action_complete"
                                class="badge bg-success"
                            >
                                {{ formatDate(comment.action_complete) }}
                            </span>
                            <span v-else class="badge bg-warning">Pending</span>
                        </td>
                        <td>{{ comment.created_by }}</td>
                        <td>{{ formatDate(comment.created_on) }}</td>
                        <td v-if="!readOnly">
                            <div class="btn-group btn-group-sm">
                                <button
                                    class="btn btn-outline-primary"
                                    @click="editComment(comment)"
                                    title="Edit Comment"
                                >
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button
                                    class="btn btn-outline-danger"
                                    @click="deleteComment(comment)"
                                    title="Delete Comment"
                                >
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div v-else class="text-center py-4 text-muted">
            <p>No silviculturist comments found for this treatment.</p>
        </div>

        <!-- Add/Edit Comment Modal -->
        <div
            class="modal fade"
            :class="{ 'show d-block': showCommentModal }"
            tabindex="-1"
            v-if="showCommentModal"
        >
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            {{
                                editingComment
                                    ? 'Edit Silviculturist Comment'
                                    : 'Add New Silviculturist Comment'
                            }}
                        </h5>
                        <button
                            type="button"
                            class="btn-close"
                            @click="closeModal"
                        ></button>
                    </div>
                    <div class="modal-body">
                        <form @submit.prevent="saveComment">
                            <div class="row">
                                <div class="col-md-12">
                                    <div class="form-group">
                                        <label
                                            for="commentText"
                                            class="form-label"
                                            >Comment *</label
                                        >
                                        <textarea
                                            id="commentText"
                                            v-model="commentData.comment"
                                            class="form-control"
                                            rows="4"
                                            :readonly="readOnly"
                                            placeholder="Enter detailed comment..."
                                            required
                                        ></textarea>
                                    </div>
                                </div>
                            </div>

                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label
                                            for="requiredAction"
                                            class="form-label"
                                            >Required Action</label
                                        >
                                        <input
                                            id="requiredAction"
                                            v-model="
                                                commentData.required_action
                                            "
                                            type="text"
                                            class="form-control"
                                            :readonly="readOnly"
                                            placeholder="Specify any required follow-up action..."
                                        />
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label
                                            for="actionComplete"
                                            class="form-label"
                                            >Action Complete Date</label
                                        >
                                        <input
                                            id="actionComplete"
                                            v-model="
                                                commentData.action_complete
                                            "
                                            type="date"
                                            class="form-control"
                                            :readonly="readOnly"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div class="row mt-3">
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label for="easting" class="form-label"
                                            >Easting</label
                                        >
                                        <input
                                            id="easting"
                                            v-model.number="
                                                commentData.easting_note_taken
                                            "
                                            type="number"
                                            class="form-control"
                                            :readonly="readOnly"
                                            placeholder="Easting coordinate"
                                        />
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label for="northing" class="form-label"
                                            >Northing</label
                                        >
                                        <input
                                            id="northing"
                                            v-model.number="
                                                commentData.northing_note_taken
                                            "
                                            type="number"
                                            class="form-control"
                                            :readonly="readOnly"
                                            placeholder="Northing coordinate"
                                        />
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button
                            type="button"
                            class="btn btn-secondary"
                            @click="closeModal"
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            class="btn btn-primary"
                            @click="saveComment"
                            :disabled="saving"
                        >
                            <span
                                v-if="saving"
                                class="spinner-border spinner-border-sm me-1"
                            ></span>
                            {{
                                saving
                                    ? 'Saving...'
                                    : editingComment
                                      ? 'Update Comment'
                                      : 'Save Comment'
                            }}
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal Backdrop -->
        <div class="modal-backdrop fade show" v-if="showCommentModal"></div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'SilviculturistComment',
    props: {
        treatmentId: {
            type: [Number, String],
            required: true,
        },
        readOnly: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            comments: [],
            commentData: {
                comment: '',
                required_action: '',
                action_complete: null,
                easting_note_taken: null,
                northing_note_taken: null,
                scope: 'treatment',
                treatment: this.treatmentId,
            },
            showCommentModal: false,
            editingComment: null,
            saving: false,
        };
    },
    methods: {
        async loadComments() {
            try {
                console.log(
                    `${api_endpoints.silviculturist_comments}?treatment=${this.treatmentId}`
                );
                const response = await fetch(
                    `${api_endpoints.silviculturist_comments}?treatment=${this.treatmentId}`
                );
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                this.comments = data.results || data;
            } catch (error) {
                console.error('Error loading silviculturist comments:', error);
                await swal.fire({
                    icon: 'error',
                    title: 'Load Failed',
                    text: 'Failed to load silviculturist comments',
                    confirmButtonText: 'OK',
                });
            }
        },
        async saveComment() {
            if (!this.validateForm()) {
                return;
            }

            this.saving = true;
            try {
                let url, method;
                if (this.editingComment) {
                    url = `${api_endpoints.silviculturist_comments}${this.editingComment.s_comment_id}/`;
                    method = 'PUT';
                } else {
                    url = api_endpoints.silviculturist_comments;
                    method = 'POST';
                }

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify(this.commentData),
                });

                if (!response.ok) {
                    let errorDetail = '';
                    try {
                        const errorData = await response.clone().json();
                        errorDetail = JSON.stringify(errorData);
                    } catch (e) {
                        try {
                            errorDetail = await response.clone().text();
                        } catch (textError) {
                            errorDetail = 'Could not read error response';
                        }
                    }
                    throw new Error(
                        `HTTP error! status: ${response.status}, details: ${errorDetail}`
                    );
                }

                const responseData = await response.json();

                await swal.fire({
                    icon: 'success',
                    title: 'Success!',
                    text: `Comment ${this.editingComment ? 'updated' : 'created'} successfully`,
                    timer: 3000,
                    showConfirmButton: false,
                });

                this.closeModal();
                await this.loadComments();
                this.$emit('comment-updated');
            } catch (error) {
                console.error('Error saving comment:', error);
                await this.handleSaveError(error);
            } finally {
                this.saving = false;
            }
        },
        async deleteComment(comment) {
            const result = await swal.fire({
                icon: 'warning',
                title: 'Delete Comment?',
                text: 'Are you sure you want to delete this comment? This action cannot be undone.',
                showCancelButton: true,
                confirmButtonText: 'Yes, delete it!',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#d33',
            });

            if (result.isConfirmed) {
                try {
                    const response = await fetch(
                        `${api_endpoints.silviculturist_comments}${comment.s_comment_id}/`,
                        {
                            method: 'DELETE',
                            headers: {
                                'X-CSRFToken': this.getCSRFToken(),
                            },
                        }
                    );

                    if (!response.ok) {
                        throw new Error(
                            `HTTP error! status: ${response.status}`
                        );
                    }

                    await swal.fire({
                        icon: 'success',
                        title: 'Deleted!',
                        text: 'Comment has been deleted successfully',
                        timer: 3000,
                        showConfirmButton: false,
                    });

                    await this.loadComments();
                    this.$emit('comment-updated');
                } catch (error) {
                    console.error('Error deleting comment:', error);
                    await swal.fire({
                        icon: 'error',
                        title: 'Delete Failed',
                        text: 'Failed to delete comment',
                        confirmButtonText: 'OK',
                    });
                }
            }
        },
        editComment(comment) {
            this.editingComment = comment;
            this.commentData = {
                comment: comment.comment || '',
                required_action: comment.required_action || '',
                action_complete: comment.action_complete
                    ? comment.action_complete.split('T')[0]
                    : null,
                easting_note_taken: comment.easting_note_taken,
                northing_note_taken: comment.northing_note_taken,
                scope: 'treatment',
                treatment: this.treatmentId,
            };
            this.showCommentModal = true;
        },
        addNewComment() {
            this.editingComment = null;
            this.commentData = {
                comment: '',
                required_action: '',
                action_complete: null,
                easting_note_taken: null,
                northing_note_taken: null,
                scope: 'treatment',
                treatment: this.treatmentId,
            };
            this.showCommentModal = true;
        },
        closeModal() {
            this.showCommentModal = false;
            this.editingComment = null;
            this.resetCommentForm();
        },
        resetCommentForm() {
            this.commentData = {
                comment: '',
                required_action: '',
                action_complete: null,
                easting_note_taken: null,
                northing_note_taken: null,
                scope: 'treatment',
                treatment: this.treatmentId,
            };
        },
        validateForm() {
            if (!this.commentData.comment.trim()) {
                swal.fire({
                    icon: 'error',
                    title: 'Validation Error',
                    text: 'Comment is required',
                    confirmButtonText: 'OK',
                });
                return false;
            }
            return true;
        },
        async handleSaveError(error) {
            let errorMessage = 'Failed to save comment';

            if (error.message && error.message.includes('403')) {
                errorMessage =
                    'You do not have permission to create or update comments. Please contact an administrator.';
            } else if (error.message && error.message.includes('details:')) {
                try {
                    const details = error.message.split('details:')[1];
                    try {
                        const errorData = JSON.parse(details);
                        if (typeof errorData === 'object') {
                            errorMessage =
                                errorData.error ||
                                Object.values(errorData).flat().join(', ');
                        } else {
                            errorMessage = details;
                        }
                    } catch (e) {
                        errorMessage = details;
                    }
                } catch (e) {
                    errorMessage = error.message;
                }
            } else {
                errorMessage = error.message || 'Unknown error occurred';
            }

            await swal.fire({
                icon: 'error',
                title: 'Save Error',
                text: errorMessage,
                confirmButtonText: 'OK',
                confirmButtonColor: '#d33',
            });
        },
        truncateText(text, length) {
            if (!text) return '';
            return text.length > length
                ? text.substring(0, length) + '...'
                : text;
        },
        formatDate(dateString) {
            if (!dateString) return 'N/A';
            const date = new Date(dateString);
            return date.toLocaleDateString();
        },
        getCSRFToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === name + '=') {
                        cookieValue = decodeURIComponent(
                            cookie.substring(name.length + 1)
                        );
                        break;
                    }
                }
            }
            return cookieValue;
        },
    },
    mounted() {
        this.loadComments();
    },
    watch: {
        treatmentId: {
            handler(newVal) {
                if (newVal) {
                    this.loadComments();
                    this.resetCommentForm();
                }
            },
            immediate: true,
        },
    },
};
</script>

<style scoped>
.silviculturist-comment {
    margin-bottom: 1rem;
}

.comment-text {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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

/* Modal Styles */
.modal {
    background-color: rgba(0, 0, 0, 0.5);
}

.modal-dialog {
    max-width: 800px;
}

.modal-content {
    border: none;
    border-radius: 0.5rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.modal-header {
    border-bottom: 4px solid #dee2e6;
    padding: 1rem 1.5rem;
    background-color: white;
}

.modal-title {
    font-weight: 600;
    background-color: white;
    color: #495057;
}

.modal-body {
    padding: 1.5rem;
    background-color: white;
    color: #495057;
}

.modal-footer {
    border-top: 4px solid #dee2e6;
    padding: 1rem 1.5rem;
    background-color: white;
}

.form-group {
    margin-bottom: 1rem;
}

.form-label {
    font-weight: 500;
    margin-bottom: 0.5rem;
    color: #495057;
}
</style>
