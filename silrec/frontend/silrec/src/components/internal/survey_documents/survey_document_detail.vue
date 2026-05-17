<template>
    <div class="container">
        <div class="header-actions mb-4">
            <button class="btn btn-secondary" @click="goBack">
                <i class="bi bi-arrow-left"></i> Back
            </button>
            <h2 class="page-title">Survey Document Detail</h2>
        </div>

        <div v-if="loading" class="text-center">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>

        <div v-if="error" class="alert alert-danger">{{ error }}</div>

        <div v-if="!loading && !error && doc" class="card">
            <div class="card-body">
                <dl class="row">
                    <dt class="col-sm-3">Document ID</dt>
                    <dd class="col-sm-9">{{ doc.document_id }}</dd>

                    <dt class="col-sm-3">Title</dt>
                    <dd class="col-sm-9">{{ doc.title || 'N/A' }}</dd>

                    <dt class="col-sm-3">Description</dt>
                    <dd class="col-sm-9">{{ doc.description || 'N/A' }}</dd>

                    <dt class="col-sm-3">Document Type</dt>
                    <dd class="col-sm-9">{{ doc.document_type || 'N/A' }}</dd>

                    <dt class="col-sm-3">Treatment</dt>
                    <dd class="col-sm-9">{{ doc.treatment || 'N/A' }}</dd>

                    <dt class="col-sm-3">File Name</dt>
                    <dd class="col-sm-9">{{ doc.file_name || 'N/A' }}</dd>

                    <dt class="col-sm-3">File Size</dt>
                    <dd class="col-sm-9">{{ doc.file_size_display || doc.file_size || 'N/A' }}</dd>

                    <dt class="col-sm-3">Uploaded By</dt>
                    <dd class="col-sm-9">{{ doc.uploaded_by_display || doc.uploaded_by || 'N/A' }}</dd>

                    <dt class="col-sm-3">Created On</dt>
                    <dd class="col-sm-9">{{ doc.created_on || 'N/A' }}</dd>
                </dl>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

export default {
    name: 'SurveyDocumentDetail',
    props: {
        documentId: {
            type: [Number, String],
            required: true,
        },
    },
    data() {
        return {
            loading: true,
            error: null,
            doc: null,
        };
    },
    async mounted() {
        await this.fetchDocument();
    },
    methods: {
        async fetchDocument() {
            this.loading = true;
            this.error = null;
            try {
                const response = await fetch(
                    `${api_endpoints.survey_assessment_documents}${this.documentId}/`
                );
                if (!response.ok) throw new Error('Failed to load document');
                this.doc = await response.json();
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
