<template>
    <div class="version-history">
        <button
            type="button"
            class="btn btn-outline-secondary btn-sm"
            @click="toggle"
        >
            <i class="bi bi-clock-history me-1"></i> History
        </button>

        <div v-if="open" class="card mt-2 version-history-panel">
            <div
                class="card-header py-2 d-flex justify-content-between align-items-center"
            >
                <span class="fw-bold">Change History</span>
                <button
                    type="button"
                    class="btn-close"
                    aria-label="Close"
                    @click="open = false"
                ></button>
            </div>
            <div class="card-body py-2">
                <div v-if="loading" class="text-muted small">Loading…</div>
                <div v-else-if="error" class="text-danger small">
                    {{ error }}
                </div>
                <div v-else-if="!versions.length" class="text-muted small">
                    No history recorded yet.
                </div>
                <template v-else>
                    <ul class="list-group list-group-flush mb-2 version-list">
                        <li
                            v-for="(v, i) in versions"
                            :key="v.version_id"
                            class="list-group-item py-1 px-2 version-item"
                            :class="{ active: selectedIndex === i }"
                            role="button"
                            @click="select(i)"
                        >
                            <div class="d-flex justify-content-between small">
                                <span class="fw-semibold">{{
                                    v.user || 'System'
                                }}</span>
                                <span class="text-muted">{{
                                    fmtDate(v.date)
                                }}</span>
                            </div>
                            <div v-if="v.comment" class="text-muted small">
                                {{ v.comment }}
                            </div>
                        </li>
                    </ul>

                    <div v-if="diffLoading" class="text-muted small">
                        Loading diff…
                    </div>
                    <div v-else-if="diffError" class="text-danger small">
                        {{ diffError }}
                    </div>
                    <div v-else-if="diff">
                        <div
                            v-if="!diff.changes.length"
                            class="text-muted small"
                        >
                            No field changes in this version.
                        </div>
                        <RichDiff v-else :changes="diff.changes" />
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';
import RichDiff from '@/components/internal/rich_diff.vue';

export default {
    name: 'VersionHistory',
    components: { RichDiff },
    props: {
        model: { type: String, required: true },
        pk: { type: [Number, String], default: null },
    },
    data() {
        return {
            open: false,
            loading: false,
            error: null,
            versions: [],
            selectedIndex: null,
            diff: null,
            diffLoading: false,
            diffError: null,
        };
    },
    watch: {
        pk() {
            if (this.open) this.loadHistory();
        },
    },
    methods: {
        toggle() {
            this.open = !this.open;
            if (this.open && !this.versions.length) this.loadHistory();
        },
        async loadHistory() {
            if (!this.pk) return;
            this.loading = true;
            this.error = null;
            this.versions = [];
            this.selectedIndex = null;
            this.diff = null;
            this.diffError = null;
            try {
                const res = await fetch(
                    api_endpoints.version_history(this.model, this.pk)
                );
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                this.versions = data.versions || [];
            } catch (e) {
                this.error = String(e.message || e);
            } finally {
                this.loading = false;
            }
        },
        async select(i) {
            if (this.selectedIndex === i) return;
            this.selectedIndex = i;
            this.diff = null;
            this.diffError = null;
            const current = this.versions[i];
            const previous = this.versions[i + 1];
            if (!previous) {
                this.diff = { changes: [] };
                this.diffError = 'This is the oldest recorded version.';
                return;
            }
            this.diffLoading = true;
            try {
                const res = await fetch(
                    api_endpoints.version_diff(
                        this.model,
                        this.pk,
                        previous.version_id,
                        current.version_id
                    )
                );
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                this.diff = await res.json();
            } catch (e) {
                this.diffError = String(e.message || e);
            } finally {
                this.diffLoading = false;
            }
        },
        fmtDate(v) {
            if (!v) return '';
            const d = new Date(v);
            if (isNaN(d.getTime())) return String(v);
            return d.toLocaleString();
        },
    },
};
</script>

<style scoped>
.version-item {
    cursor: pointer;
}
.version-item.active {
    background-color: #e9f0f9;
    color: inherit;
}
.version-list {
    max-height: 220px;
    overflow-y: auto;
}
</style>
