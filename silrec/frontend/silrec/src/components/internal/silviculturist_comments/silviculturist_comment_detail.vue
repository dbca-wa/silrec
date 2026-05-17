<template>
    <div class="container">
        <div class="header-actions mb-4">
            <button class="btn btn-secondary" @click="goBack">
                <i class="bi bi-arrow-left"></i> Back
            </button>
            <h2 class="page-title">Silviculturist Comment Detail</h2>
        </div>

        <div v-if="loading" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <div v-if="error" class="alert alert-danger">{{ error }}</div>

        <div v-if="!loading && !error && comment" class="card">
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-3">Comment ID</dt>
                    <dd class="col-sm-9">{{ comment.s_comment_id }}</dd>

                    <dt class="col-sm-3">Comment</dt>
                    <dd class="col-sm-9">{{ comment.comment || 'N/A' }}</dd>

                    <dt class="col-sm-3">Scope</dt>
                    <dd class="col-sm-9">{{ comment.scope || 'N/A' }}</dd>

                    <dt class="col-sm-3">Required Action</dt>
                    <dd class="col-sm-9">{{ comment.required_action || 'N/A' }}</dd>

                    <dt class="col-sm-3">Action Complete</dt>
                    <dd class="col-sm-9">{{ comment.action_complete ? 'Yes' : 'No' }}</dd>

                    <dt class="col-sm-3">Treatment</dt>
                    <dd class="col-sm-9">{{ comment.treatment || 'N/A' }}</dd>

                    <dt class="col-sm-3">Easting</dt>
                    <dd class="col-sm-9">{{ comment.easting_note_taken || 'N/A' }}</dd>

                    <dt class="col-sm-3">Northing</dt>
                    <dd class="col-sm-9">{{ comment.northing_note_taken || 'N/A' }}</dd>

                    <dt class="col-sm-3">Created On</dt>
                    <dd class="col-sm-9">{{ comment.created_on || 'N/A' }}</dd>

                    <dt class="col-sm-3">Created By</dt>
                    <dd class="col-sm-9">{{ comment.created_by || 'N/A' }}</dd>
                </dl>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'SilviculturistCommentDetail',
    props: {
        commentId: {
            type: [Number, String],
            required: true,
        },
    },
    data() {
        return {
            loading: true,
            error: null,
            comment: null,
        };
    },
    async mounted() {
        await this.fetchComment();
    },
    methods: {
        async fetchComment() {
            this.loading = true;
            this.error = null;
            try {
                const response = await fetch(
                    `${api_endpoints.silviculturist_comments}${this.commentId}/`
                );
                if (!response.ok) throw new Error('Failed to load comment');
                this.comment = await response.json();
            } catch (e) {
                this.error = e.message;
            } finally {
                this.loading = false;
            }
        },
        goBack() {
            this.$router.go(-1);
        },
    },
};
</script>
