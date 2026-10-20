<template>
    <div class="container my-4">
        <div
            v-if="$route.query.debug?.toLowerCase() === 'true'"
            class="text-muted small mb-2"
        >
            src/components/internal/bulk_update/bulk_update.vue
        </div>

        <div class="d-flex align-items-center gap-3 mb-4">
            <h2 class="mb-0">Bulk Update</h2>
            <span class="text-muted"
                >Apply cohort / treatment / operation changes across many
                polygons at once</span
            >
        </div>

        <!-- Step 1: polygons -->
        <div class="card mb-4">
            <div class="card-header"><h5 class="mb-0">1. Polygons</h5></div>
            <div class="card-body">
                <ul class="nav nav-tabs mb-3">
                    <li class="nav-item">
                        <button
                            type="button"
                            class="nav-link"
                            :class="{ active: section1Tab === 'proposal' }"
                            @click="section1Tab = 'proposal'"
                        >
                            Select by Proposal
                        </button>
                    </li>
                    <li class="nav-item">
                        <button
                            type="button"
                            class="nav-link"
                            :class="{ active: section1Tab === 'polygons' }"
                            @click="section1Tab = 'polygons'"
                        >
                            Select by Polygon IDs
                        </button>
                    </li>
                    <li class="nav-item">
                        <button
                            type="button"
                            class="nav-link"
                            :class="{ active: section1Tab === 'excel' }"
                            @click="section1Tab = 'excel'"
                        >
                            Excel Upload
                        </button>
                    </li>
                </ul>

                <!-- Tab: Select by Proposal -->
                <div v-show="section1Tab === 'proposal'">
                    <div class="input-group mb-2">
                        <input
                            v-model="proposalSearch"
                            type="text"
                            class="form-control"
                            placeholder="Search proposal ID / lodgement number"
                            @keyup.enter="searchProposals(1)"
                        />
                        <button
                            type="button"
                            class="btn btn-outline-secondary"
                            @click="searchProposals(1)"
                        >
                            Search
                        </button>
                    </div>

                    <!-- Paginated proposal checkbox list -->
                    <div
                        class="border rounded p-2 mb-2"
                        style="max-height: 200px; overflow-y: auto"
                    >
                        <div v-if="proposalLoading" class="text-center py-2">
                            <div class="spinner-border spinner-border-sm"></div>
                        </div>
                        <div
                            v-else-if="!proposalResults.length"
                            class="text-muted small py-2"
                        >
                            No proposals found. Search to load.
                        </div>
                        <div
                            v-for="p in proposalResults"
                            v-else
                            :key="p.id"
                            class="form-check"
                        >
                            <input
                                class="form-check-input"
                                type="checkbox"
                                :id="'proposal-' + p.id"
                                :checked="selectedProposals.has(p.id)"
                                @change="
                                    toggleProposal(p.id, p.lodgement_number)
                                "
                            />
                            <label
                                class="form-check-label"
                                :for="'proposal-' + p.id"
                            >
                                {{ p.lodgement_number || p.id }}
                            </label>
                        </div>
                    </div>
                    <div
                        class="d-flex justify-content-between align-items-center mb-2"
                    >
                        <button
                            type="button"
                            class="btn btn-sm btn-outline-secondary"
                            :disabled="proposalPage <= 1"
                            @click="searchProposals(proposalPage - 1)"
                        >
                            Prev
                        </button>
                        <span class="small text-muted"
                            >Page {{ proposalPage }} /
                            {{ proposalTotalPages }}</span
                        >
                        <button
                            type="button"
                            class="btn btn-sm btn-outline-secondary"
                            :disabled="proposalPage >= proposalTotalPages"
                            @click="searchProposals(proposalPage + 1)"
                        >
                            Next
                        </button>
                    </div>

                    <!-- Selected proposals -->
                    <div v-if="selectedProposals.size" class="mb-2">
                        <span
                            class="badge bg-secondary me-1 mb-1"
                            v-for="pid in selectedProposalsList"
                            :key="pid"
                        >
                            {{ proposalLabels[pid] || pid }}
                            <a
                                href="#"
                                class="text-white text-decoration-none ms-1"
                                @click.prevent="
                                    toggleProposal(pid, proposalLabels[pid])
                                "
                                >&times;</a
                            >
                        </span>
                    </div>

                    <!-- Paginated polygon checkbox list -->
                    <div v-if="selectedProposals.size">
                        <div
                            class="d-flex justify-content-between align-items-center mb-1"
                        >
                            <span class="form-label mb-0"
                                >Polygons of selected proposal(s)</span
                            >
                            <div>
                                <button
                                    type="button"
                                    class="btn btn-sm btn-primary me-1"
                                    :disabled="polygonLoading || !polygonCount"
                                    @click="selectAllPolygons"
                                >
                                    Select all ({{ polygonCount }})
                                </button>
                                <button
                                    type="button"
                                    class="btn btn-sm btn-outline-danger"
                                    @click="clearPolygonSelection"
                                >
                                    Clear
                                </button>
                            </div>
                        </div>
                        <div
                            class="border rounded p-2 mb-2"
                            style="max-height: 200px; overflow-y: auto"
                        >
                            <div v-if="polygonLoading" class="text-center py-2">
                                <div
                                    class="spinner-border spinner-border-sm"
                                ></div>
                            </div>
                            <div
                                v-else-if="!polygonResults.length"
                                class="text-muted small py-2"
                            >
                                No polygons for the selected proposal(s).
                            </div>
                            <div
                                v-for="pl in polygonResults"
                                v-else
                                :key="pl.polygon_id"
                                class="form-check"
                            >
                                <input
                                    class="form-check-input"
                                    type="checkbox"
                                    :id="'polygon-' + pl.polygon_id"
                                    :checked="
                                        selectedPolygons.has(pl.polygon_id)
                                    "
                                    @change="togglePolygon(pl.polygon_id)"
                                />
                                <label
                                    class="form-check-label"
                                    :for="'polygon-' + pl.polygon_id"
                                >
                                    {{ pl.polygon_id }}
                                    <span class="text-muted small">{{
                                        pl.name || ''
                                    }}</span>
                                </label>
                            </div>
                        </div>
                        <div
                            class="d-flex justify-content-between align-items-center"
                        >
                            <button
                                type="button"
                                class="btn btn-sm btn-outline-secondary"
                                :disabled="polygonPage <= 1"
                                @click="loadPolygonPage(polygonPage - 1)"
                            >
                                Prev
                            </button>
                            <span class="small text-muted"
                                >Page {{ polygonPage }} /
                                {{ polygonTotalPages }}</span
                            >
                            <button
                                type="button"
                                class="btn btn-sm btn-outline-secondary"
                                :disabled="polygonPage >= polygonTotalPages"
                                @click="loadPolygonPage(polygonPage + 1)"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Tab: Select by Polygon IDs -->
                <div v-show="section1Tab === 'polygons'">
                    <label for="polygonIds" class="form-label">
                        Polygon IDs
                        <span class="text-muted"
                            >(comma-, space-, newline- or
                            semicolon-separated)</span
                        >
                    </label>
                    <textarea
                        id="polygonIds"
                        v-model="polygonIdsText"
                        class="form-control"
                        rows="8"
                        placeholder="e.g. 402346, 402347, 402348"
                    ></textarea>
                </div>

                <!-- Tab: Excel Upload -->
                <div v-show="section1Tab === 'excel'">
                    <label for="excelUpload" class="form-label">
                        Upload Excel Spreadsheet
                    </label>
                    <input
                        id="excelUpload"
                        ref="excelInput"
                        type="file"
                        class="form-control"
                        accept=".xlsx,.xls"
                        @change="onExcelFileSelected"
                    />
                    <div class="form-text mt-1">
                        Upload the completed bulk-update template (download it
                        from the "2. Preview" header). The spreadsheet is
                        validated before any changes are applied; errors are
                        reported with their row and column location.
                    </div>
                    <div v-if="excelFileName" class="mt-2 small text-muted">
                        Selected file: {{ excelFileName }}
                    </div>
                    <div class="mt-3 d-flex gap-2">
                        <button
                            type="button"
                            class="btn btn-primary"
                            :disabled="uploading || !excelFile"
                            @click="uploadExcel"
                        >
                            <span
                                v-if="uploading"
                                class="spinner-border spinner-border-sm me-1"
                            ></span>
                            {{
                                uploading ? 'Uploading...' : 'Upload and Apply'
                            }}
                        </button>
                        <button
                            type="button"
                            class="btn btn-outline-secondary"
                            @click="clearExcel"
                        >
                            Clear
                        </button>
                    </div>

                    <!-- Upload summary + resolve (shown after upload) -->
                    <div v-if="uploadResult" class="mt-4">
                        <h6 class="mb-2">
                            <i class="bi bi-list-check me-1"></i>
                            Upload summary
                        </h6>
                        <table class="table table-sm table-striped">
                            <thead>
                                <tr>
                                    <th>Polygon</th>
                                    <th>Cohort changes</th>
                                    <th>New treatments</th>
                                    <th>Updated treatments</th>
                                    <th>Operation</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr
                                    v-for="r in uploadResult.results"
                                    :key="r.polygon_id"
                                >
                                    <td>
                                        {{ r.polygon_id }}
                                        <span class="text-muted small"
                                            >(cohort {{ r.cohort_id }})</span
                                        >
                                    </td>
                                    <td>
                                        <div
                                            v-if="
                                                r.cohort_changes &&
                                                r.cohort_changes.length
                                            "
                                            class="small"
                                        >
                                            <div
                                                v-for="c in r.cohort_changes"
                                                :key="c.field"
                                            >
                                                <code>{{
                                                    fieldLabel(c.field)
                                                }}</code
                                                >: {{ fmtVal(c.old) }} →
                                                {{ fmtVal(c.new) }}
                                            </div>
                                        </div>
                                        <span v-else class="text-muted">-</span>
                                    </td>
                                    <td>
                                        <span
                                            v-for="tid in r.treatments_created"
                                            :key="tid"
                                            class="badge bg-success me-1"
                                            >new #{{ tid }}</span
                                        >
                                        <span
                                            v-if="!r.treatments_created.length"
                                            class="text-muted"
                                            >-</span
                                        >
                                    </td>
                                    <td>
                                        <div
                                            v-if="
                                                r.treatment_changes &&
                                                r.treatment_changes.length
                                            "
                                            class="small"
                                        >
                                            <div
                                                v-for="t in r.treatment_changes"
                                                :key="t.treatment_id"
                                            >
                                                <span class="badge bg-info me-1"
                                                    >#{{ t.treatment_id }}</span
                                                >
                                                <span
                                                    v-for="c in t.changes"
                                                    :key="c.field"
                                                >
                                                    <code>{{
                                                        fieldLabel(c.field)
                                                    }}</code
                                                    >: {{ fmtVal(c.old) }} →
                                                    {{ fmtVal(c.new) }};
                                                </span>
                                            </div>
                                        </div>
                                        <span v-else class="text-muted">-</span>
                                    </td>
                                    <td>
                                        <div
                                            v-if="r.operation_created"
                                            class="small"
                                        >
                                            <span class="badge bg-success"
                                                >new #{{
                                                    r.operation_created
                                                }}</span
                                            >
                                        </div>
                                        <div
                                            v-else-if="r.operation_updated"
                                            class="small"
                                        >
                                            <span class="badge bg-info"
                                                >updated #{{
                                                    r.operation_updated
                                                }}</span
                                            >
                                            <span
                                                v-for="c in r.operation_changes ||
                                                []"
                                                :key="c.field"
                                            >
                                                <code>{{
                                                    fieldLabel(c.field)
                                                }}</code
                                                >: {{ fmtVal(c.old) }} →
                                                {{ fmtVal(c.new) }};
                                            </span>
                                        </div>
                                        <span v-else class="text-muted">-</span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>

                        <div class="d-flex align-items-center mt-2">
                            <button
                                type="button"
                                class="btn btn-primary"
                                :disabled="excelResolving"
                                @click="resolveUploadedPolygons"
                            >
                                <span
                                    v-if="excelResolving"
                                    class="spinner-border spinner-border-sm me-1"
                                ></span>
                                {{
                                    excelResolving
                                        ? 'Resolving...'
                                        : 'Resolve Uploaded Polygons'
                                }}
                            </button>
                        </div>

                        <div v-if="excelPreview" class="mt-3">
                            <table class="table table-sm table-striped">
                                <thead>
                                    <tr>
                                        <th>Polygon ID</th>
                                        <th>Name</th>
                                        <th>Compartment</th>
                                        <th>Proposal</th>
                                        <th>Cohort</th>
                                        <th>Objective</th>
                                        <th>Species</th>
                                        <th>Treatments</th>
                                        <th>Operation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr
                                        v-for="p in excelPreview.polygons"
                                        :key="p.polygon_id"
                                    >
                                        <td>
                                            {{ p.polygon_id }}
                                            <a
                                                :href="viewLink(p)"
                                                target="_blank"
                                                class="text-decoration-none ms-1"
                                                title="View form (read-only)"
                                            >
                                                <i class="bi bi-eye"></i>
                                            </a>
                                        </td>
                                        <td>{{ p.name || '-' }}</td>
                                        <td>{{ p.compartment || '-' }}</td>
                                        <td>{{ p.proposal_id }}</td>
                                        <td>{{ p.cohort_id }}</td>
                                        <td>{{ p.obj_code || '-' }}</td>
                                        <td>{{ p.species || '-' }}</td>
                                        <td>{{ p.treatment_count }}</td>
                                        <td>
                                            {{
                                                p.operation
                                                    ? p.operation.fea_id
                                                    : '-'
                                            }}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <div
                    v-if="section1Tab !== 'excel'"
                    class="mt-3 d-flex align-items-center"
                >
                    <button
                        type="button"
                        class="btn btn-primary"
                        :disabled="resolving || !hasAnyPolygons"
                        @click="resolvePolygons"
                    >
                        <span
                            v-if="resolving"
                            class="spinner-border spinner-border-sm me-1"
                        ></span>
                        {{ resolving ? 'Resolving...' : 'Resolve Polygons' }}
                    </button>
                    <span class="ms-3 text-muted"
                        >Selected: {{ combinedPolygonCount }} polygon(s)</span
                    >
                    <span v-if="resolveError" class="text-danger ms-3">{{
                        resolveError
                    }}</span>
                </div>
            </div>
        </div>

        <!-- Preview -->
        <div v-if="resolved" class="card mb-4">
            <div
                class="card-header d-flex justify-content-between align-items-center"
            >
                <h5 class="mb-0">2. Preview</h5>
                <div class="d-flex align-items-center gap-2">
                    <span
                        class="badge"
                        :class="preview.found ? 'bg-success' : 'bg-danger'"
                    >
                        {{ preview.found }} of
                        {{ preview.requested }} polygon(s) will be processed
                    </span>
                    <button
                        type="button"
                        class="btn btn-sm btn-outline-success"
                        :disabled="exporting || !preview.found"
                        @click="exportTemplate"
                    >
                        <span
                            v-if="exporting"
                            class="spinner-border spinner-border-sm me-1"
                        ></span>
                        <i v-else class="bi bi-file-earmark-excel me-1"></i>
                        Export Excel Template
                    </button>
                </div>
            </div>
            <div class="card-body">
                <table
                    v-if="preview.polygons.length"
                    class="table table-sm table-striped"
                >
                    <thead>
                        <tr>
                            <th>Polygon ID</th>
                            <th>Name</th>
                            <th>Compartment</th>
                            <th>Proposal</th>
                            <th>Cohort</th>
                            <th>Objective</th>
                            <th>Species</th>
                            <th>Treatments</th>
                            <th>Operation</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="p in preview.polygons" :key="p.polygon_id">
                            <td>
                                {{ p.polygon_id }}
                                <a
                                    :href="`/internal/proposal/${p.proposal_id}/cohorts/${p.cohort_id}/polygon/${p.polygon_id}?readonly=true`"
                                    target="_blank"
                                    class="text-decoration-none ms-1"
                                    title="View form (read-only)"
                                >
                                    <i class="bi bi-eye"></i>
                                </a>
                            </td>
                            <td>{{ p.name || '-' }}</td>
                            <td>{{ p.compartment || '-' }}</td>
                            <td>{{ p.proposal_id }}</td>
                            <td>{{ p.cohort_id }}</td>
                            <td>{{ p.obj_code || '-' }}</td>
                            <td>{{ p.species || '-' }}</td>
                            <td>{{ p.treatment_count }}</td>
                            <td>
                                {{ p.operation ? p.operation.fea_id : '-' }}
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div v-else class="alert alert-warning mb-0">
                    No polygons could be processed. See exclusions below.
                </div>

                <div v-if="preview.excluded.length" class="mt-3">
                    <h6>Excluded (not processed)</h6>
                    <table class="table table-sm table-bordered">
                        <thead>
                            <tr>
                                <th>Polygon ID</th>
                                <th>Name</th>
                                <th>Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                v-for="e in preview.excluded"
                                :key="e.polygon_id"
                            >
                                <td>{{ e.polygon_id }}</td>
                                <td>{{ e.name || '-' }}</td>
                                <td>{{ e.reason }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Step 3: what to change -->
        <div v-if="resolved" class="card mb-4">
            <div class="card-header">
                <h5 class="mb-0">3. Changes to apply</h5>
            </div>
            <div class="card-body">
                <!-- Cohort -->
                <div class="border rounded p-3 mb-3">
                    <div class="form-check mb-3">
                        <input
                            id="cohortEnabled"
                            v-model="sections.cohort.enabled"
                            type="checkbox"
                            class="form-check-input"
                        />
                        <label
                            for="cohortEnabled"
                            class="form-check-label fw-bold"
                            >Update current cohort</label
                        >
                    </div>
                    <div v-if="sections.cohort.enabled" class="row">
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Objective Code</label>
                            <select
                                v-model="sections.cohort.fields.obj_code"
                                class="form-select"
                            >
                                <option value="">No change</option>
                                <option
                                    v-for="o in lookups.objectives"
                                    :key="o.obj_code"
                                    :value="o.obj_code"
                                >
                                    {{ o.obj_code }} - {{ o.description || '' }}
                                </option>
                            </select>
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Species</label>
                            <select
                                v-model="sections.cohort.fields.species"
                                class="form-select"
                            >
                                <option value="">No change</option>
                                <option
                                    v-for="s in lookups.species"
                                    :key="s.species"
                                    :value="s.species"
                                >
                                    {{ s.species }} -
                                    {{
                                        s.short_description ||
                                        s.full_description ||
                                        ''
                                    }}
                                </option>
                            </select>
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >Regeneration Method</label
                            >
                            <select
                                v-model="sections.cohort.fields.regen_method"
                                class="form-select"
                            >
                                <option value="">No change</option>
                                <option
                                    v-for="m in lookups.regeneration_methods"
                                    :key="m.regen_method"
                                    :value="m.regen_method"
                                >
                                    {{ m.regen_method }} -
                                    {{ m.description || '' }}
                                </option>
                            </select>
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Site Quality</label>
                            <input
                                v-model="sections.cohort.fields.site_quality"
                                type="text"
                                class="form-control"
                                maxlength="6"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Target BA (m²/ha)</label>
                            <input
                                v-model.number="
                                    sections.cohort.fields.target_ba_m2ha
                                "
                                type="number"
                                step="0.1"
                                min="0"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >Residual BA (m²/ha)</label
                            >
                            <input
                                v-model.number="
                                    sections.cohort.fields.resid_ba_m2ha
                                "
                                type="number"
                                step="0.1"
                                min="0"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Target SPHA</label>
                            <input
                                v-model.number="
                                    sections.cohort.fields.target_spha
                                "
                                type="number"
                                min="0"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Residual SPHA</label>
                            <input
                                v-model.number="
                                    sections.cohort.fields.resid_spha
                                "
                                type="number"
                                min="0"
                                step="0.1"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Percentage Area</label>
                            <input
                                v-model.number="sections.cohort.fields.pct_area"
                                type="number"
                                min="0"
                                max="100"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Year Last Cut</label>
                            <input
                                v-model.number="
                                    sections.cohort.fields.year_last_cut
                                "
                                type="number"
                                min="1900"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Operation Date</label>
                            <input
                                v-model="sections.cohort.fields.op_date"
                                type="datetime-local"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Regeneration Date</label>
                            <input
                                v-model="sections.cohort.fields.regen_date"
                                type="datetime-local"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >Secondary Regeneration Date</label
                            >
                            <input
                                v-model="sections.cohort.fields.regen_date2"
                                type="datetime-local"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Complete Date</label>
                            <input
                                v-model="sections.cohort.fields.complete_date"
                                type="datetime-local"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >Herbicide Application</label
                            >
                            <input
                                v-model="
                                    sections.cohort.fields.herbicide_app_spec
                                "
                                type="text"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">VRP</label>
                            <input
                                v-model.number="sections.cohort.fields.vrp"
                                type="number"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >VRP Total Area (ha)</label
                            >
                            <input
                                v-model.number="
                                    sections.cohort.fields.vrp_tot_area
                                "
                                type="number"
                                min="0"
                                step="0.1"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label">Stand</label>
                            <input
                                v-model="sections.cohort.fields.stand"
                                type="text"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >Regeneration Values Calculated</label
                            >
                            <select
                                v-model="sections.cohort.fields.regen_done"
                                class="form-select"
                            >
                                <option value="">No change</option>
                                <option :value="true">Yes</option>
                                <option :value="false">No</option>
                            </select>
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >Treatments Inserted</label
                            >
                            <select
                                v-model="sections.cohort.fields.treatments"
                                class="form-select"
                            >
                                <option value="">No change</option>
                                <option :value="true">Yes</option>
                                <option :value="false">No</option>
                            </select>
                        </div>
                        <div class="col-md-4 mb-2">
                            <label class="form-label"
                                >Extra Info Required</label
                            >
                            <select
                                v-model="sections.cohort.fields.extra_info"
                                class="form-select"
                            >
                                <option value="">No change</option>
                                <option :value="true">Yes</option>
                                <option :value="false">No</option>
                            </select>
                        </div>
                        <div class="col-md-12 mb-2">
                            <label class="form-label">Comments</label>
                            <textarea
                                v-model="sections.cohort.fields.comments"
                                class="form-control"
                                rows="2"
                                maxlength="250"
                            ></textarea>
                        </div>
                    </div>
                </div>

                <!-- Treatments -->
                <div class="border rounded p-3 mb-3">
                    <div class="form-check mb-3">
                        <input
                            id="treatmentEnabled"
                            v-model="sections.treatment.enabled"
                            type="checkbox"
                            class="form-check-input"
                        />
                        <label
                            for="treatmentEnabled"
                            class="form-check-label fw-bold"
                            >Apply treatments</label
                        >
                    </div>
                    <div v-if="sections.treatment.enabled" class="row">
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Mode</label>
                            <select
                                v-model="sections.treatment.mode"
                                class="form-select"
                            >
                                <option value="create">
                                    Create new treatment on each cohort
                                </option>
                                <option value="update">
                                    Update matching existing treatments
                                </option>
                            </select>
                        </div>
                        <template v-if="sections.treatment.mode === 'create'">
                            <div class="col-md-3 mb-2">
                                <label class="form-label">Task *</label>
                                <select
                                    v-model="sections.treatment.fields.task"
                                    class="form-select"
                                >
                                    <option value="">Select task</option>
                                    <option
                                        v-for="t in lookups.tasks"
                                        :key="t.task"
                                        :value="t.task"
                                    >
                                        {{ t.task_name }} ({{ t.task }})
                                    </option>
                                </select>
                            </div>
                        </template>
                        <template v-else>
                            <div class="col-md-3 mb-2">
                                <label class="form-label">Match task</label>
                                <select
                                    v-model="sections.treatment.match.task"
                                    class="form-select"
                                >
                                    <option value="">Any task</option>
                                    <option
                                        v-for="t in lookups.tasks"
                                        :key="t.task"
                                        :value="t.task"
                                    >
                                        {{ t.task_name }} ({{ t.task }})
                                    </option>
                                </select>
                            </div>
                            <div class="col-md-3 mb-2">
                                <label class="form-label">Match status</label>
                                <select
                                    v-model="sections.treatment.match.status"
                                    class="form-select"
                                >
                                    <option value="">Any status</option>
                                    <option value="P">Planned</option>
                                    <option value="D">Completed</option>
                                    <option value="C">Cancelled</option>
                                    <option value="F">Failed</option>
                                    <option value="W">Written Off</option>
                                    <option value="X">Not Required</option>
                                </select>
                            </div>
                        </template>
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Status</label>
                            <select
                                v-model="sections.treatment.fields.status"
                                class="form-select"
                            >
                                <option value="">No change</option>
                                <option value="P">Planned</option>
                                <option value="D">Completed</option>
                                <option value="C">Cancelled</option>
                                <option value="F">Failed</option>
                                <option value="W">Written Off</option>
                                <option value="X">Not Required</option>
                            </select>
                        </div>
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Planned Year</label>
                            <input
                                v-model.number="
                                    sections.treatment.fields.plan_yr
                                "
                                type="number"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Planned Month</label>
                            <input
                                v-model.number="
                                    sections.treatment.fields.plan_mth
                                "
                                type="number"
                                min="1"
                                max="12"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Area Percentage</label>
                            <input
                                v-model.number="
                                    sections.treatment.fields.pct_area
                                "
                                type="number"
                                min="0"
                                max="100"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Complete Date</label>
                            <input
                                v-model="
                                    sections.treatment.fields.complete_date
                                "
                                type="date"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-6 mb-2">
                            <label class="form-label">Organisation</label>
                            <input
                                v-model="sections.treatment.fields.organisation"
                                type="text"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-6 mb-2">
                            <label class="form-label">Reference</label>
                            <input
                                v-model="sections.treatment.fields.reference"
                                type="text"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-12 mb-2">
                            <label class="form-label">Results</label>
                            <textarea
                                v-model="sections.treatment.fields.results"
                                class="form-control"
                                rows="2"
                            ></textarea>
                        </div>
                    </div>
                </div>

                <!-- Operation -->
                <div class="border rounded p-3 mb-3">
                    <div class="form-check mb-3">
                        <input
                            id="operationEnabled"
                            v-model="sections.operation.enabled"
                            type="checkbox"
                            class="form-check-input"
                        />
                        <label
                            for="operationEnabled"
                            class="form-check-label fw-bold"
                            >Apply operation</label
                        >
                    </div>
                    <div v-if="sections.operation.enabled" class="row">
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Mode</label>
                            <select
                                v-model="sections.operation.mode"
                                class="form-select"
                            >
                                <option value="create">
                                    Create new operation and link
                                </option>
                                <option value="update">
                                    Update existing linked operation
                                </option>
                            </select>
                        </div>
                        <div class="col-md-3 mb-2">
                            <label class="form-label"
                                >FEA ID
                                <span
                                    v-if="sections.operation.mode === 'create'"
                                    >*</span
                                ></label
                            >
                            <input
                                v-model="sections.operation.fields.fea_id"
                                type="text"
                                maxlength="20"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-3 mb-2">
                            <label class="form-label">DAS ID</label>
                            <input
                                v-model.number="
                                    sections.operation.fields.das_id
                                "
                                type="number"
                                class="form-control"
                            />
                        </div>
                        <div class="col-md-3 mb-2">
                            <label class="form-label">Plan Release</label>
                            <input
                                v-model="sections.operation.fields.plan_release"
                                type="text"
                                maxlength="50"
                                class="form-control"
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Apply -->
        <div v-if="resolved" class="d-flex align-items-center gap-3">
            <button
                type="button"
                class="btn btn-success btn-lg"
                :disabled="applying"
                @click="confirmApply"
            >
                <span
                    v-if="applying"
                    class="spinner-border spinner-border-sm me-1"
                ></span>
                {{
                    applying
                        ? 'Applying...'
                        : `Apply to ${preview.found} polygon(s)`
                }}
            </button>
            <span class="text-muted"
                >A confirmation will be shown before anything is written.</span
            >
        </div>

        <!-- Results -->
        <div v-if="result" class="card mt-4">
            <div class="card-header"><h5 class="mb-0">Results</h5></div>
            <div class="card-body">
                <div class="alert alert-success">
                    {{ result.results.length }} polygon(s) processed.
                </div>
                <table
                    v-if="result.results.length"
                    class="table table-sm table-striped"
                >
                    <thead>
                        <tr>
                            <th>Polygon</th>
                            <th>Cohort</th>
                            <th>Cohort updated</th>
                            <th>Treatments created</th>
                            <th>Treatments updated</th>
                            <th>Operation</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="r in result.results" :key="r.polygon_id">
                            <td>{{ r.polygon_id }}</td>
                            <td>{{ r.cohort_id }}</td>
                            <td>{{ r.cohort_updated ? 'Yes' : '-' }}</td>
                            <td>
                                {{
                                    r.treatments_created.length
                                        ? r.treatments_created.join(', ')
                                        : '-'
                                }}
                            </td>
                            <td>
                                {{
                                    r.treatments_updated.length
                                        ? r.treatments_updated.join(', ')
                                        : '-'
                                }}
                            </td>
                            <td>
                                {{
                                    r.operation_created ||
                                    r.operation_updated ||
                                    '-'
                                }}
                            </td>
                            <td>
                                <span
                                    v-if="r.notes.length"
                                    class="text-warning"
                                    >{{ r.notes.join('; ') }}</span
                                >
                                <span v-else>-</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
                <div v-if="result.excluded.length" class="mt-3">
                    <h6>Excluded</h6>
                    <table class="table table-sm table-bordered">
                        <thead>
                            <tr>
                                <th>Polygon ID</th>
                                <th>Name</th>
                                <th>Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                v-for="e in result.excluded"
                                :key="e.polygon_id"
                            >
                                <td>{{ e.polygon_id }}</td>
                                <td>{{ e.name || '-' }}</td>
                                <td>{{ e.reason }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';
import { FIELD_LABELS } from '@/utils/fieldLabels';

export default {
    name: 'BulkUpdate',
    data() {
        return {
            polygonIdsText: '',
            section1Tab: 'proposal',
            resolving: false,
            resolved: false,
            resolveError: null,
            preview: { requested: 0, found: 0, excluded: [], polygons: [] },

            // Proposal-driven selection
            proposalSearch: '',
            proposalResults: [],
            proposalPage: 1,
            proposalCount: 0,
            proposalLoading: false,
            selectedProposals: new Set(),
            proposalLabels: {},

            // Polygon checkbox list
            polygonResults: [],
            polygonPage: 1,
            polygonCount: 0,
            polygonLoading: false,
            selectedPolygons: new Set(),

            lookups: {
                objectives: [],
                species: [],
                regeneration_methods: [],
                tasks: [],
            },
            sections: {
                cohort: {
                    enabled: false,
                    fields: {
                        obj_code: '',
                        species: '',
                        regen_method: '',
                        site_quality: '',
                        target_ba_m2ha: '',
                        resid_ba_m2ha: '',
                        target_spha: '',
                        resid_spha: '',
                        comments: '',
                        op_date: '',
                        pct_area: '',
                        year_last_cut: '',
                        regen_date: '',
                        regen_date2: '',
                        regen_done: '',
                        complete_date: '',
                        herbicide_app_spec: '',
                        vrp: '',
                        vrp_tot_area: '',
                        stand: '',
                        extra_info: '',
                        treatments: '',
                    },
                },
                treatment: {
                    enabled: false,
                    mode: 'create',
                    match: { task: '', status: '' },
                    fields: {
                        task: '',
                        status: '',
                        plan_yr: '',
                        plan_mth: '',
                        pct_area: '',
                        complete_date: '',
                        organisation: '',
                        results: '',
                        reference: '',
                    },
                },
                operation: {
                    enabled: false,
                    mode: 'create',
                    fields: { fea_id: '', das_id: '', plan_release: '' },
                },
            },
            exporting: false,
            excelFile: null,
            excelFileName: '',
            uploading: false,
            applying: false,
            result: null,
            uploadResult: null,
            excelPreview: null,
            excelResolving: false,
        };
    },
    computed: {
        proposalTotalPages() {
            return Math.max(1, Math.ceil(this.proposalCount / 10));
        },
        polygonTotalPages() {
            return Math.max(1, Math.ceil(this.polygonCount / 20));
        },
        selectedProposalsList() {
            return Array.from(this.selectedProposals);
        },
        combinedPolygonIds() {
            const ids = new Set(this.selectedPolygons);
            const text = (this.polygonIdsText || '').trim();
            if (text) {
                const tokens = text
                    .replace(/,/g, ' ')
                    .replace(/;/g, ' ')
                    .split(/\s+/);
                tokens.forEach((t) => {
                    if (t && /^\d+$/.test(t)) ids.add(parseInt(t, 10));
                });
            }
            return Array.from(ids).sort((a, b) => a - b);
        },
        combinedPolygonCount() {
            return this.combinedPolygonIds.length;
        },
        hasAnyPolygons() {
            return this.combinedPolygonIds.length > 0;
        },
        uploadedPolygonIds() {
            if (!this.uploadResult || !this.uploadResult.results) return [];
            return this.uploadResult.results.map((r) => r.polygon_id);
        },
    },
    methods: {
        clean(obj) {
            const out = {};
            for (const [k, v] of Object.entries(obj)) {
                if (v === '' || v === null || v === undefined) continue;
                out[k] = v;
            }
            return out;
        },
        async searchProposals(page = 1) {
            this.proposalLoading = true;
            try {
                const params = new URLSearchParams();
                const s = this.proposalSearch.trim();
                if (s) params.set('search', s);
                params.set('page', String(page));
                const res = await fetch(
                    `${api_endpoints.bulk_update_proposals}?${params.toString()}`
                );
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.error || 'Failed to load proposals');
                }
                this.proposalResults = data.results || [];
                this.proposalCount = data.count || 0;
                this.proposalPage = page;
            } catch (e) {
                console.error('Failed to load proposals', e);
            } finally {
                this.proposalLoading = false;
            }
        },
        toggleProposal(id, lodgementNumber) {
            if (this.selectedProposals.has(id)) {
                this.selectedProposals.delete(id);
                delete this.proposalLabels[id];
            } else {
                this.selectedProposals.add(id);
                this.proposalLabels[id] = lodgementNumber || id;
            }
            this.refreshPolygons();
        },
        async refreshPolygons() {
            if (!this.selectedProposals.size) {
                this.polygonResults = [];
                this.polygonCount = 0;
                this.polygonPage = 1;
                this.selectedPolygons = new Set();
                return;
            }
            await this.pruneSelectedPolygons();
            await this.loadPolygonPage(1);
        },
        proposalIdsParam() {
            return Array.from(this.selectedProposals)
                .sort((a, b) => a - b)
                .join(',');
        },
        async fetchAllPolygonIds() {
            const params = new URLSearchParams({
                proposal_ids: this.proposalIdsParam(),
                all_ids: '1',
            });
            const res = await fetch(
                `${api_endpoints.bulk_update_polygons}?${params.toString()}`
            );
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || 'Failed to load polygons');
            }
            return data.polygon_ids || [];
        },
        async pruneSelectedPolygons() {
            try {
                const allowed = new Set(await this.fetchAllPolygonIds());
                this.selectedPolygons = new Set(
                    [...this.selectedPolygons].filter((x) => allowed.has(x))
                );
            } catch (e) {
                console.error('Failed to prune selected polygons', e);
            }
        },
        async loadPolygonPage(page = 1) {
            this.polygonLoading = true;
            try {
                const params = new URLSearchParams({
                    proposal_ids: this.proposalIdsParam(),
                });
                params.set('page', String(page));
                const res = await fetch(
                    `${api_endpoints.bulk_update_polygons}?${params.toString()}`
                );
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.error || 'Failed to load polygons');
                }
                this.polygonResults = data.results || [];
                this.polygonCount = data.count || 0;
                this.polygonPage = page;
            } catch (e) {
                console.error('Failed to load polygons', e);
            } finally {
                this.polygonLoading = false;
            }
        },
        togglePolygon(id) {
            if (this.selectedPolygons.has(id)) this.selectedPolygons.delete(id);
            else this.selectedPolygons.add(id);
        },
        async selectAllPolygons() {
            this.polygonLoading = true;
            try {
                const ids = await this.fetchAllPolygonIds();
                ids.forEach((id) => this.selectedPolygons.add(id));
            } catch (e) {
                console.error('Failed to select all polygons', e);
            } finally {
                this.polygonLoading = false;
            }
        },
        clearPolygonSelection() {
            this.selectedPolygons = new Set();
        },
        async exportTemplate() {
            this.exporting = true;
            try {
                const res = await fetch(
                    api_endpoints.bulk_update_export_template,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCSRFToken(),
                        },
                        body: JSON.stringify({
                            polygon_ids: this.combinedPolygonIds,
                        }),
                    }
                );
                if (!res.ok) {
                    const data = await res.json().catch(() => ({}));
                    throw new Error(data.error || 'Export failed');
                }
                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                let filename = 'bulk_update_template.xlsx';
                const disposition = res.headers.get('Content-Disposition');
                if (disposition) {
                    const match = disposition.match(/filename="([^"]+)"/);
                    if (match) filename = match[1];
                }
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                URL.revokeObjectURL(url);
            } catch (e) {
                await swal.fire({
                    icon: 'error',
                    title: 'Export failed',
                    text: String(e.message || e),
                });
            } finally {
                this.exporting = false;
            }
        },
        onExcelFileSelected(event) {
            const file = event.target.files[0];
            if (file) {
                this.excelFile = file;
                this.excelFileName = file.name;
                // Choosing a (new) file invalidates any previous upload summary.
                this.uploadResult = null;
                this.excelPreview = null;
            }
        },
        clearExcel() {
            this.excelFile = null;
            this.excelFileName = '';
            this.uploadResult = null;
            this.excelPreview = null;
            this.excelResolving = false;
            const input = this.$refs.excelInput;
            if (input) input.value = '';
        },
        async uploadExcel() {
            if (!this.excelFile) {
                await swal.fire({
                    icon: 'warning',
                    title: 'No file selected',
                    text: 'Select an Excel spreadsheet to upload.',
                });
                return;
            }
            this.uploading = true;
            try {
                const formData = new FormData();
                formData.append('file', this.excelFile);
                const res = await fetch(api_endpoints.bulk_update_upload, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCSRFToken() },
                    body: formData,
                });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    if (data.errors && data.errors.length) {
                        await this.showValidationErrors(data.errors);
                    } else {
                        const detail =
                            data.error ||
                            (data.details
                                ? JSON.stringify(data.details)
                                : 'Upload failed');
                        await swal.fire({
                            icon: 'error',
                            title: 'Upload failed',
                            text: String(detail),
                        });
                    }
                    return;
                }
                this.uploadResult = data;
                this.excelPreview = null;
                await swal.fire({
                    icon: 'success',
                    title: 'Upload complete',
                    text: `${data.processed} polygon(s) processed.`,
                });
            } catch (e) {
                await swal.fire({
                    icon: 'error',
                    title: 'Upload failed',
                    text: String(e.message || e),
                });
            } finally {
                this.uploading = false;
            }
        },
        showValidationErrors(errors) {
            const maxRows = 100;
            const shown = errors.slice(0, maxRows);
            const escapeHtml = (s) =>
                String(s)
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;');
            const rows = shown
                .map(
                    (e) =>
                        `<tr><td>${escapeHtml(e.row)}</td><td>${escapeHtml(
                            e.column
                        )}</td><td>${escapeHtml(e.message)}</td></tr>`
                )
                .join('');
            const extra =
                errors.length > maxRows
                    ? `<p class="mt-2 mb-0"><em>...and ${
                          errors.length - maxRows
                      } more error(s) not shown.</em></p>`
                    : '';
            return swal.fire({
                icon: 'error',
                title: 'Validation errors in uploaded file',
                html:
                    `<div style="max-height:320px; overflow-y:auto; text-align:left; font-size:0.85rem;">` +
                    `<table class="table table-sm table-bordered mb-2"><thead><tr>` +
                    `<th>Row</th><th>Column</th><th>Message</th>` +
                    `</tr></thead><tbody>${rows}</tbody></table>${extra}</div>`,
                width: 720,
                confirmButtonText: 'OK',
            });
        },
        fmtVal(v) {
            if (v === null || v === undefined) return '(empty)';
            return String(v);
        },
        fieldLabel(name) {
            return FIELD_LABELS[name] || name;
        },
        bulkChangesQuery(polygonId) {
            if (!this.uploadResult) return '';
            const r = this.uploadResult.results.find(
                (x) => x.polygon_id === polygonId
            );
            if (!r) return '';
            const payload = {
                cohort: r.cohort_changes || [],
                treatments_created: r.treatments_created || [],
                treatments_updated: r.treatment_changes || [],
                operation_created: r.operation_created || null,
                operation_updated: r.operation_updated || null,
                operation_changes: r.operation_changes || [],
            };
            return encodeURIComponent(JSON.stringify(payload));
        },
        viewLink(p) {
            const base = `/internal/proposal/${p.proposal_id}/cohorts/${p.cohort_id}/polygon/${p.polygon_id}?readonly=true`;
            const bc = this.bulkChangesQuery(p.polygon_id);
            return bc ? `${base}&bulkchanges=${bc}` : base;
        },
        async resolveUploadedPolygons() {
            if (!this.uploadedPolygonIds.length) return;
            this.excelResolving = true;
            try {
                const res = await fetch(api_endpoints.bulk_update_preview, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify({
                        polygon_ids: this.uploadedPolygonIds,
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.error || 'Resolve failed');
                }
                this.excelPreview = data;
            } catch (e) {
                await swal.fire({
                    icon: 'error',
                    title: 'Resolve failed',
                    text: String(e.message || e),
                });
            } finally {
                this.excelResolving = false;
            }
        },
        buildPayload() {
            const payload = { polygon_ids: this.combinedPolygonIds };
            if (this.sections.cohort.enabled) {
                const fields = this.clean(this.sections.cohort.fields);
                if (Object.keys(fields).length) payload.cohort = { fields };
            }
            if (this.sections.treatment.enabled) {
                payload.treatments = {
                    mode: this.sections.treatment.mode,
                    fields: this.clean(this.sections.treatment.fields),
                };
                if (this.sections.treatment.mode === 'update') {
                    payload.treatments.match = this.clean(
                        this.sections.treatment.match
                    );
                }
            }
            if (this.sections.operation.enabled) {
                payload.operation = {
                    mode: this.sections.operation.mode,
                    fields: this.clean(this.sections.operation.fields),
                };
            }
            return payload;
        },
        validatePayload() {
            const payload = this.buildPayload();
            const enabled = Object.keys(payload).filter(
                (k) => k !== 'polygon_ids'
            ).length;
            if (!enabled) {
                swal.fire({
                    icon: 'warning',
                    title: 'Nothing selected',
                    text: 'Enable at least one section and provide a value.',
                });
                return null;
            }
            if (
                payload.cohort &&
                !Object.keys(payload.cohort.fields || {}).length
            ) {
                swal.fire({
                    icon: 'warning',
                    title: 'Cohort section',
                    text: 'Provide at least one cohort field to change.',
                });
                return null;
            }
            if (payload.treatments) {
                if (
                    payload.treatments.mode === 'create' &&
                    !(payload.treatments.fields || {}).task
                ) {
                    swal.fire({
                        icon: 'error',
                        title: 'Validation Error',
                        text: 'Must select Task.',
                    });
                    return null;
                }
                if (
                    payload.treatments.mode === 'update' &&
                    !(payload.treatments.match || {}).task &&
                    !(payload.treatments.match || {}).status
                ) {
                    swal.fire({
                        icon: 'error',
                        title: 'Validation Error',
                        text: 'Update mode requires a Task and/or Status filter.',
                    });
                    return null;
                }
            }
            if (payload.operation) {
                if (
                    payload.operation.mode === 'create' &&
                    !(payload.operation.fields || {}).fea_id
                ) {
                    swal.fire({
                        icon: 'error',
                        title: 'Validation Error',
                        text: 'Must enter FEA ID.',
                    });
                    return null;
                }
            }
            return payload;
        },
        async loadLookups() {
            try {
                const res = await fetch(api_endpoints.combined_lookups);
                if (res.ok) {
                    const data = await res.json();
                    this.lookups.objectives = data.objectives || [];
                    this.lookups.species = data.species || [];
                    this.lookups.regeneration_methods =
                        data.regeneration_methods || [];
                }
            } catch (e) {
                console.error('Failed to load lookups', e);
            }
            try {
                const res = await fetch(api_endpoints.tasks);
                if (res.ok) {
                    const data = await res.json();
                    this.lookups.tasks = data.results || data || [];
                }
            } catch (e) {
                console.error('Failed to load tasks', e);
            }
        },
        async resolvePolygons() {
            if (!this.hasAnyPolygons) {
                this.resolveError =
                    'Enter polygon IDs or select polygons from proposals.';
                return;
            }
            this.resolving = true;
            this.resolveError = null;
            this.resolved = false;
            this.result = null;
            try {
                const res = await fetch(api_endpoints.bulk_update_preview, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify({
                        polygon_ids: this.combinedPolygonIds,
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(
                        data.error ||
                            (data.details && data.details.join(', ')) ||
                            'Resolve failed'
                    );
                }
                this.preview = data;
                this.resolved = true;
            } catch (e) {
                this.resolveError = e.message;
            } finally {
                this.resolving = false;
            }
        },
        async refreshPreview() {
            try {
                const res = await fetch(api_endpoints.bulk_update_preview, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify({
                        polygon_ids: this.combinedPolygonIds,
                    }),
                });
                const data = await res.json();
                if (res.ok) {
                    this.preview = data;
                }
            } catch (e) {
                console.error('Failed to refresh preview', e);
            }
        },
        async confirmApply() {
            const payload = this.validatePayload();
            if (!payload) return;
            const confirm = await swal.fire({
                icon: 'warning',
                title: 'Apply bulk update?',
                html: `This will update <strong>${this.preview.found}</strong> polygon(s). This cannot be undone.<br>${this.preview.excluded.length} polygon(s) will be skipped.`,
                showCancelButton: true,
                confirmButtonText: 'Yes, apply',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#198754',
            });
            if (!confirm.isConfirmed) return;
            await this.apply(payload);
        },
        async apply(payload) {
            this.applying = true;
            try {
                const res = await fetch(api_endpoints.bulk_update, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken(),
                    },
                    body: JSON.stringify(payload),
                });
                const data = await res.json();
                if (!res.ok) {
                    const detail = Array.isArray(data.details)
                        ? data.details.join('<br>')
                        : data.details || data.error || 'Apply failed';
                    throw {
                        message: detail,
                        isHtml: Array.isArray(data.details),
                    };
                }
                this.result = data;
                await this.refreshPreview();
                await swal.fire({
                    icon: 'success',
                    title: 'Applied',
                    text: 'Bulk update completed.',
                });
            } catch (e) {
                await swal.fire({
                    icon: 'error',
                    title: 'Apply failed',
                    html: e.isHtml ? e.message : String(e.message),
                });
            } finally {
                this.applying = false;
            }
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
        this.loadLookups();
        this.searchProposals(1);
    },
};
</script>
