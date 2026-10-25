<template>
    <div class="container-fluid my-4">
        <h2 class="mb-3">Change History</h2>

        <!-- Filters -->
        <div class="card mb-3">
            <div class="card-body py-2">
                <div class="row g-2 align-items-end">
                    <div class="col-md-3">
                        <label class="form-label small mb-1">Model</label>
                        <select
                            v-model="filters.model"
                            class="form-select form-select-sm"
                        >
                            <option value="">All models</option>
                            <option
                                v-for="m in models"
                                :key="m.key"
                                :value="m.key"
                            >
                                {{ m.label }}
                            </option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label small mb-1">User</label>
                        <select
                            v-model="filters.user"
                            class="form-select form-select-sm"
                        >
                            <option value="">All users</option>
                            <option
                                v-for="u in users"
                                :key="u.id"
                                :value="u.id"
                            >
                                {{ u.name }}
                            </option>
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small mb-1">From</label>
                        <input
                            v-model="filters.from"
                            type="date"
                            class="form-control form-control-sm"
                        />
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small mb-1">To</label>
                        <input
                            v-model="filters.to"
                            type="date"
                            class="form-control form-control-sm"
                        />
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small mb-1">Search</label>
                        <input
                            v-model="filters.search"
                            type="text"
                            class="form-control form-control-sm"
                            placeholder="Comment / record…"
                            @keyup.enter="applyFilters"
                        />
                    </div>
                </div>
                <div class="d-flex gap-2 mt-2">
                    <button
                        type="button"
                        class="btn btn-primary btn-sm"
                        @click="applyFilters"
                    >
                        Apply
                    </button>
                    <button
                        type="button"
                        class="btn btn-outline-secondary btn-sm"
                        @click="clearFilters"
                    >
                        Clear
                    </button>
                </div>
            </div>
        </div>

        <!-- Results -->
        <div v-if="loading" class="text-center py-4">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
        <div v-else-if="error" class="alert alert-danger">
            {{ error }}
        </div>
        <div v-else-if="!results.length" class="text-muted">
            No history found.
        </div>
        <template v-else>
            <p class="text-muted small mb-2">{{ count }} revision(s)</p>

            <div v-for="r in results" :key="r.revision_id" class="card mb-2">
                <div
                    class="card-header py-1 d-flex justify-content-between align-items-center flex-wrap"
                >
                    <div>
                        <strong>{{ r.user || 'System' }}</strong>
                        <span class="text-muted small ms-2">{{
                            fmtDate(r.date)
                        }}</span>
                        <span
                            v-if="r.comment"
                            class="badge bg-light text-dark ms-2"
                            >{{ r.comment }}</span
                        >
                    </div>
                    <span class="text-muted small"
                        >{{ r.changes.length }} record(s)</span
                    >
                </div>
                <div class="card-body py-1">
                    <div
                        v-for="c in r.changes"
                        :key="c.version_id"
                        class="change-row py-1"
                    >
                        <div class="d-flex align-items-start">
                            <button
                                type="button"
                                class="btn btn-link btn-sm p-0 me-1"
                                @click="toggleDiff(c)"
                            >
                                <i
                                    class="bi"
                                    :class="
                                        isExpanded(c.version_id)
                                            ? 'bi-chevron-down'
                                            : 'bi-chevron-right'
                                    "
                                ></i>
                            </button>
                            <span class="badge bg-secondary">{{
                                modelLabel(c.model)
                            }}</span>
                            <span class="ms-2">{{ c.repr }}</span>
                        </div>
                        <div v-if="isExpanded(c.version_id)" class="ms-4 mt-1">
                            <div
                                v-if="diffState(c.version_id).loading"
                                class="text-muted small"
                            >
                                Loading…
                            </div>
                            <div
                                v-else-if="diffState(c.version_id).error"
                                class="text-danger small"
                            >
                                {{ diffState(c.version_id).error }}
                            </div>
                            <div v-else-if="diffState(c.version_id).data">
                                <div
                                    v-if="
                                        !diffState(c.version_id).data.changes
                                            .length
                                    "
                                    class="text-muted small"
                                >
                                    No field changes.
                                </div>
                                <RichDiff
                                    v-else
                                    :changes="
                                        diffState(c.version_id).data.changes
                                    "
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Pagination -->
            <nav v-if="totalPages > 1" class="mt-3">
                <ul class="pagination pagination-sm">
                    <li class="page-item" :class="{ disabled: page <= 1 }">
                        <button class="page-link" @click="goPage(page - 1)">
                            Prev
                        </button>
                    </li>
                    <li class="page-item disabled">
                        <span class="page-link"
                            >{{ page }} / {{ totalPages }}</span
                        >
                    </li>
                    <li
                        class="page-item"
                        :class="{ disabled: page >= totalPages }"
                    >
                        <button class="page-link" @click="goPage(page + 1)">
                            Next
                        </button>
                    </li>
                </ul>
            </nav>
        </template>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';
import RichDiff from '@/components/internal/rich_diff.vue';

const PAGE_SIZE = 25;

export default {
    name: 'HistoryView',
    components: { RichDiff },
    data() {
        return {
            loading: false,
            error: null,
            models: [],
            users: [],
            filters: { model: '', user: '', from: '', to: '', search: '' },
            page: 1,
            count: 0,
            results: [],
            expanded: new Set(),
            details: {}, // version_id -> {loading, error, data}
        };
    },
    computed: {
        totalPages() {
            return Math.max(1, Math.ceil(this.count / PAGE_SIZE));
        },
    },
    mounted() {
        this.loadOptions();
        this.fetchHistory();
    },
    methods: {
        async loadOptions() {
            try {
                const res = await fetch(api_endpoints.history_options);
                if (res.ok) {
                    const data = await res.json();
                    this.models = data.models || [];
                    this.users = data.users || [];
                }
            } catch {
                // Non-fatal; filters just won't populate.
            }
        },
        buildQuery() {
            const p = new URLSearchParams();
            if (this.filters.model) p.set('model', this.filters.model);
            if (this.filters.user) p.set('user', this.filters.user);
            if (this.filters.from) p.set('from', this.filters.from);
            if (this.filters.to) p.set('to', this.filters.to);
            if (this.filters.search) p.set('search', this.filters.search);
            p.set('page', this.page);
            return p.toString();
        },
        async fetchHistory() {
            this.loading = true;
            this.error = null;
            try {
                const res = await fetch(
                    `${api_endpoints.history}?${this.buildQuery()}`
                );
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                this.count = data.count || 0;
                this.results = data.results || [];
            } catch (e) {
                this.error = String(e.message || e);
            } finally {
                this.loading = false;
            }
        },
        applyFilters() {
            this.page = 1;
            this.expanded = new Set();
            this.details = {};
            this.fetchHistory();
        },
        clearFilters() {
            this.filters = {
                model: '',
                user: '',
                from: '',
                to: '',
                search: '',
            };
            this.applyFilters();
        },
        goPage(p) {
            if (p < 1 || p > this.totalPages) return;
            this.page = p;
            this.fetchHistory();
        },
        isExpanded(versionId) {
            return this.expanded.has(versionId);
        },
        diffState(versionId) {
            return this.details[versionId] || {};
        },
        async toggleDiff(c) {
            const vid = c.version_id;
            if (this.expanded.has(vid)) {
                this.expanded.delete(vid);
                this.expanded = new Set(this.expanded);
                return;
            }
            this.expanded.add(vid);
            this.expanded = new Set(this.expanded);
            this.details[vid] = { loading: true, error: null, data: null };
            try {
                const res = await fetch(
                    api_endpoints.version_diff_by_version(c.model, c.pk, vid)
                );
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                this.details[vid] = {
                    loading: false,
                    error: null,
                    data: await res.json(),
                };
            } catch (e) {
                this.details[vid] = {
                    loading: false,
                    error: String(e.message || e),
                    data: null,
                };
            }
        },
        modelLabel(key) {
            const m = this.models.find((x) => x.key === key);
            return m ? m.label : key;
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
.change-row {
    border-bottom: 1px solid #f0f0f0;
}
.change-row:last-child {
    border-bottom: none;
}
</style>
