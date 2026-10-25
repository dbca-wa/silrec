<template>
    <div class="container-fluid my-4" :class="{ 'er-maximized': maximized }">
        <div v-if="!maximized" class="d-flex align-items-center gap-2 mb-3">
            <h2 class="mb-0">Entity Relationship Diagram</h2>
            <span class="text-muted d-none d-md-inline"
                >Polygon at the centre — zoom out to reveal more levels</span
            >
            <button
                type="button"
                class="btn btn-sm btn-outline-secondary ms-auto"
                :title="maximized ? 'Restore' : 'Maximise'"
                @click="toggleMaximize"
            >
                <i
                    class="fa-solid"
                    :class="maximized ? 'fa-compress' : 'fa-expand'"
                ></i>
            </button>
        </div>

        <div class="row">
            <!-- Selection panel -->
            <div v-if="!sidebarCollapsed" class="col-md-3">
                <div class="card">
                    <div
                        class="card-header d-flex justify-content-between align-items-center"
                    >
                        <span class="fw-bold">Models</span>
                        <div class="d-flex align-items-center gap-1">
                            <button
                                type="button"
                                class="btn btn-sm btn-outline-secondary"
                                @click="selectAll"
                            >
                                All
                            </button>
                            <button
                                type="button"
                                class="btn btn-sm btn-outline-secondary"
                                @click="resetLevel"
                            >
                                Base
                            </button>
                            <button
                                type="button"
                                class="btn btn-sm btn-outline-secondary"
                                title="Hide table list"
                                @click="toggleSidebar"
                            >
                                <i class="fa-solid fa-angles-left"></i>
                            </button>
                        </div>
                    </div>
                    <div
                        class="card-body p-0 d-flex flex-column"
                        style="height: 75vh"
                    >
                        <!-- Models (60%) -->
                        <div class="p-2" style="height: 60%; overflow-y: auto">
                            <div
                                v-for="group in orderedGroups"
                                :key="group.key"
                                class="mb-3"
                            >
                                <div class="d-flex align-items-center mb-1">
                                    <input
                                        type="checkbox"
                                        class="form-check-input me-2"
                                        :checked="isGroupAllSelected(group)"
                                        @change="toggleGroup(group.key)"
                                    />
                                    <strong class="me-1">{{
                                        group.name
                                    }}</strong>
                                    <span class="text-muted small"
                                        >({{ selectedGroupCount(group) }}/{{
                                            group.models.length
                                        }})</span
                                    >
                                </div>
                                <div class="ms-4">
                                    <div
                                        v-for="m in group.models"
                                        :key="m.name"
                                        class="form-check"
                                    >
                                        <input
                                            type="checkbox"
                                            class="form-check-input"
                                            :id="'er-' + m.name"
                                            :checked="selected.has(m.name)"
                                            @change="toggleModel(m.name)"
                                        />
                                        <label
                                            class="form-check-label small"
                                            :for="'er-' + m.name"
                                            :title="m.verbose_name"
                                            >{{ m.name }}</label
                                        >
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Pan and Zoom (40%) -->
                        <div
                            class="border-top d-flex flex-column"
                            style="height: 40%; min-height: 0"
                        >
                            <div
                                class="d-flex align-items-center gap-2 px-2 pt-2 small"
                            >
                                <span class="fw-bold">Pan and Zoom</span>
                                <input
                                    type="range"
                                    class="form-range flex-grow-1 er-zoom-slider"
                                    min="0"
                                    max="1000"
                                    :value="zoomSliderValue"
                                    @input="onZoomSlider"
                                    title="Zoom"
                                />
                            </div>
                            <div class="px-2 pt-2">
                                <div class="position-relative">
                                    <input
                                        v-model="searchText"
                                        type="text"
                                        class="form-control form-control-sm"
                                        placeholder="Search & focus table…"
                                        @focus="onSearchFocus"
                                        @input="searchOpen = true"
                                        @blur="onSearchBlur"
                                    />
                                    <ul
                                        v-if="
                                            searchOpen &&
                                            filteredSearchOptions.length
                                        "
                                        class="er-search-dropdown list-unstyled mb-0"
                                    >
                                        <li
                                            v-for="opt in filteredSearchOptions"
                                            :key="opt"
                                            @mousedown.prevent="
                                                onSearchSelect(opt)
                                            "
                                        >
                                            {{ opt }}
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            <div class="p-2 flex-grow-1" style="min-height: 0">
                                <svg
                                    v-if="layout.boxes.length"
                                    ref="minimapSvg"
                                    class="er-minimap"
                                    :viewBox="`0 0 ${layout.width} ${layout.height}`"
                                    width="100%"
                                    height="100%"
                                    preserveAspectRatio="xMidYMid meet"
                                    @pointerdown="onMinimapPointerDown"
                                    @wheel.prevent="onMinimapWheel"
                                >
                                    <rect
                                        v-for="b in layout.boxes"
                                        :key="'m' + b.model.name"
                                        :x="b.x"
                                        :y="b.y"
                                        :width="b.w"
                                        :height="b.h"
                                        :fill="darken(boxFill(b), 0.65)"
                                        :stroke="darken(boxStroke(b), 0.65)"
                                        stroke-width="0.5"
                                    ></rect>
                                    <path
                                        v-for="(e, i) in layout.edges"
                                        :key="'ml' + i"
                                        :d="e.d"
                                        fill="none"
                                        stroke="#5a685a"
                                        stroke-width="0.5"
                                    ></path>
                                    <rect
                                        :x="viewportRect.x"
                                        :y="viewportRect.y"
                                        :width="viewportRect.w"
                                        :height="viewportRect.h"
                                        fill="rgba(27, 83, 120, 0.12)"
                                        stroke="#1b5378"
                                        stroke-width="1.5"
                                    ></rect>
                                </svg>
                                <div
                                    v-else
                                    class="text-muted small text-center py-3"
                                >
                                    Loading…
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Diagram -->
            <div
                class="er-diagram-col"
                :class="sidebarCollapsed ? 'col-md-12' : 'col-md-9'"
            >
                <button
                    v-if="sidebarCollapsed"
                    type="button"
                    class="btn btn-sm btn-light er-reopen-btn"
                    title="Show table list"
                    @click="toggleSidebar"
                >
                    <i class="fa-solid fa-angles-right"></i>
                </button>
                <div
                    v-if="edgePopup"
                    class="er-edge-popup"
                    :style="{
                        left: edgePopup.x + 14 + 'px',
                        top: edgePopup.y + 14 + 'px',
                    }"
                    @mouseenter="onPopupEnter"
                    @mouseleave="onPopupLeave"
                >
                    <div class="er-edge-popup-title">
                        {{ edgePopup.edge.from }}.{{ edgePopup.edge.field }} →
                        {{ edgePopup.edge.to }}
                    </div>
                    <button
                        type="button"
                        class="btn btn-sm btn-light er-edge-popup-item"
                        @click="selectTable(edgePopup.edge.from)"
                    >
                        <i class="bi bi-table me-1"></i
                        >{{ edgePopup.edge.from }}
                    </button>
                    <button
                        type="button"
                        class="btn btn-sm btn-light er-edge-popup-item"
                        @click="selectTable(edgePopup.edge.to)"
                    >
                        <i class="bi bi-table me-1"></i>{{ edgePopup.edge.to }}
                    </button>
                </div>
                <div v-if="loading" class="text-center py-5">
                    <div class="spinner-border"></div>
                </div>
                <div v-else-if="error" class="alert alert-danger">
                    {{ error }}
                </div>
                <div v-else-if="!layout.boxes.length" class="alert alert-info">
                    Select one or more models on the left to view their
                    relationships.
                </div>
                <div v-else class="er-viewport-wrap">
                    <div
                        ref="viewport"
                        class="er-viewport"
                        :class="{ dragging }"
                        @wheel.prevent="onWheel"
                        @mousedown="onMousedown"
                    >
                        <svg
                            ref="svgEl"
                            :width="layout.width"
                            :height="layout.height"
                            :viewBox="`0 0 ${layout.width} ${layout.height}`"
                        >
                            <defs>
                                <marker
                                    id="er-arrow"
                                    viewBox="0 0 10 10"
                                    refX="9"
                                    refY="5"
                                    markerWidth="7"
                                    markerHeight="7"
                                    orient="auto-start-reverse"
                                >
                                    <path
                                        d="M 0 0 L 10 5 L 0 10 z"
                                        fill="#7a9a7a"
                                    ></path>
                                </marker>
                                <marker
                                    id="er-arrow-hover"
                                    viewBox="0 0 10 10"
                                    refX="9"
                                    refY="5"
                                    markerWidth="8"
                                    markerHeight="8"
                                    orient="auto-start-reverse"
                                >
                                    <path
                                        d="M 0 0 L 10 5 L 0 10 z"
                                        fill="#e74c3c"
                                    ></path>
                                </marker>
                            </defs>

                            <g
                                :transform="`translate(${panX} ${panY}) scale(${zoom})`"
                            >
                                <!-- Relationship edges (dotted) -->
                                <g
                                    v-for="(e, i) in layout.edges"
                                    :key="'e' + i"
                                    @mouseenter="onEdgeEnter(e, $event)"
                                    @mouseleave="onEdgeLeave"
                                >
                                    <title>
                                        {{ e.from }}.{{ e.field }} → {{ e.to }}
                                    </title>
                                    <path
                                        :d="e.d"
                                        fill="none"
                                        stroke="transparent"
                                        stroke-width="10"
                                        pointer-events="stroke"
                                    ></path>
                                    <path
                                        :d="e.d"
                                        fill="none"
                                        stroke-linejoin="round"
                                        stroke-linecap="round"
                                        :stroke="
                                            hoveredEdge === e
                                                ? '#e74c3c'
                                                : '#8aa08a'
                                        "
                                        :stroke-width="
                                            hoveredEdge === e ? 2 : 1
                                        "
                                        :stroke-dasharray="
                                            hoveredEdge === e ? 'none' : '4 3'
                                        "
                                        :marker-end="
                                            hoveredEdge === e
                                                ? 'url(#er-arrow-hover)'
                                                : 'url(#er-arrow)'
                                        "
                                    ></path>
                                    <text
                                        v-if="e.srcLabel"
                                        :x="e.srcLabel.x"
                                        :y="e.srcLabel.y"
                                        class="er-cardinality"
                                        text-anchor="middle"
                                        dominant-baseline="central"
                                    >
                                        {{ e.srcLabel.text }}
                                    </text>
                                    <text
                                        v-if="e.tgtLabel"
                                        :x="e.tgtLabel.x"
                                        :y="e.tgtLabel.y"
                                        class="er-cardinality"
                                        text-anchor="middle"
                                        dominant-baseline="central"
                                    >
                                        {{ e.tgtLabel.text }}
                                    </text>
                                </g>

                                <!-- Model boxes -->
                                <g
                                    v-for="b in layout.boxes"
                                    :key="b.model.name"
                                >
                                    <rect
                                        :x="b.x"
                                        :y="b.y"
                                        :width="b.w"
                                        :height="b.h"
                                        :fill="boxFill(b)"
                                        :stroke="
                                            isHighlighted(b)
                                                ? '#e74c3c'
                                                : boxStroke(b)
                                        "
                                        :stroke-width="
                                            isHighlighted(b)
                                                ? 2.5
                                                : b.isCenter
                                                  ? 2
                                                  : 1
                                        "
                                    ></rect>
                                    <rect
                                        :x="b.x"
                                        :y="b.y"
                                        :width="b.w"
                                        :height="HEADER_H"
                                        :fill="headerFill(b)"
                                        :stroke="
                                            isHighlighted(b)
                                                ? '#e74c3c'
                                                : boxStroke(b)
                                        "
                                        :stroke-width="
                                            isHighlighted(b)
                                                ? 2.5
                                                : b.isCenter
                                                  ? 2
                                                  : 1
                                        "
                                    ></rect>
                                    <text
                                        :x="b.x + 8"
                                        :y="b.y + HEADER_H - 8"
                                        class="er-title"
                                        :fill="titleFill(b)"
                                    >
                                        {{ b.model.name }}
                                    </text>
                                    <text
                                        v-for="(f, fi) in displayFields(
                                            b.model
                                        )"
                                        :key="f.name"
                                        :x="b.x + 8"
                                        :y="b.y + HEADER_H + 11 + fi * ROW_H"
                                        :fill="fieldColor(f)"
                                        :font-weight="f.pk ? 'bold' : 'normal'"
                                        class="er-field"
                                    >
                                        {{ fieldText(f) }}
                                    </text>
                                    <text
                                        v-if="
                                            b.model.fields.length > MAX_FIELDS
                                        "
                                        :x="b.x + 8"
                                        :y="
                                            b.y +
                                            HEADER_H +
                                            11 +
                                            Math.min(
                                                b.model.fields.length,
                                                MAX_FIELDS
                                            ) *
                                                ROW_H
                                        "
                                        fill="#6c757d"
                                        class="er-field"
                                    >
                                        +{{
                                            b.model.fields.length - MAX_FIELDS
                                        }}
                                        more fields
                                    </text>
                                </g>

                                <!-- Hover highlight overlay (above boxes) -->
                                <g v-if="hoveredEdge" pointer-events="none">
                                    <path
                                        :d="hoveredEdge.d"
                                        fill="none"
                                        stroke="#e74c3c"
                                        stroke-width="3"
                                        marker-end="url(#er-arrow-hover)"
                                    ></path>
                                    <text
                                        v-if="hoveredEdge.srcLabel"
                                        :x="hoveredEdge.srcLabel.x"
                                        :y="hoveredEdge.srcLabel.y"
                                        class="er-cardinality-hover"
                                        text-anchor="middle"
                                        dominant-baseline="central"
                                    >
                                        {{ hoveredEdge.srcLabel.text }}
                                    </text>
                                    <text
                                        v-if="hoveredEdge.tgtLabel"
                                        :x="hoveredEdge.tgtLabel.x"
                                        :y="hoveredEdge.tgtLabel.y"
                                        class="er-cardinality-hover"
                                        text-anchor="middle"
                                        dominant-baseline="central"
                                    >
                                        {{ hoveredEdge.tgtLabel.text }}
                                    </text>
                                </g>
                            </g>
                        </svg>
                    </div>

                    <!-- Level / zoom toolbar -->
                    <div class="er-toolbar">
                        <button
                            type="button"
                            class="btn btn-sm btn-light"
                            title="Zoom in (fewer levels)"
                            @click="zoomIn"
                        >
                            +
                        </button>
                        <button
                            type="button"
                            class="btn btn-sm btn-light er-toolbar-pct"
                            title="Reset to base view"
                            @click="resetLevel"
                        >
                            L1–L{{ level }}
                        </button>
                        <button
                            type="button"
                            class="btn btn-sm btn-light"
                            title="Zoom out (more levels)"
                            @click="zoomOut"
                        >
                            −
                        </button>
                        <button
                            type="button"
                            class="btn btn-sm btn-light"
                            title="Fit to window"
                            @click="fitView"
                        >
                            Fit
                        </button>
                        <button
                            v-if="maximized"
                            type="button"
                            class="btn btn-sm btn-light"
                            title="Restore"
                            @click="toggleMaximize"
                        >
                            <i class="fa-solid fa-compress"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { api_endpoints } from '@/utils/hooks';

const BOX_W = 240;
const HEADER_H = 26;
const ROW_H = 13;
const MAX_FIELDS = 20;
const RING_GAP = 64;
const MARGIN = 40;
const MIN_ZOOM = 0.05;
const MAX_ZOOM = 2;
// Floor for "focus on table": keeps the focused table prominent even when its
// immediate neighbours are spread far apart (far ones then sit out of pan).
const MIN_FOCUS_ZOOM = 0.875;
const ROUTE_CELL = 32;
const ROUTE_PAD = 14;
const ROUTE_TURN_PENALTY = 1;

function boxHeight(model) {
    const n = Math.min(model.fields.length, MAX_FIELDS);
    const extra = model.fields.length > MAX_FIELDS ? 1 : 0;
    return HEADER_H + (n + extra) * ROW_H + 10;
}

function edgePoints(a, b) {
    const ax = a.x + a.w / 2;
    const ay = a.y + a.h / 2;
    const bx = b.x + b.w / 2;
    const by = b.y + b.h / 2;
    const dx = bx - ax;
    const dy = by - ay;
    const dist = Math.hypot(dx, dy) || 1;
    const ux = dx / dist;
    const uy = dy / dist;
    return {
        x1: ax + ux * (a.w / 2),
        y1: ay + uy * (a.h / 2),
        x2: bx - ux * (b.w / 2),
        y2: by - uy * (b.h / 2),
    };
}

// --- Orthogonal edge routing ------------------------------------------------
// Relationship lines are drawn as axis-aligned polylines that route AROUND the
// table boxes instead of straight through them. A coarse grid + A* finds a path
// that avoids every box (inflated by ROUTE_PAD for clearance); the result is
// simplified to the fewest orthogonal segments. When no route exists (e.g. the
// tables touch) we fall back to a straight line.

function routeGrid(boxes, width, height) {
    const cols = Math.max(2, Math.ceil(width / ROUTE_CELL) + 2);
    const rows = Math.max(2, Math.ceil(height / ROUTE_CELL) + 2);
    const blocked = new Uint8Array(cols * rows);
    const idx = (cx, cy) => cy * cols + cx;
    for (const b of boxes) {
        const c0 = Math.max(0, Math.floor((b.x - ROUTE_PAD) / ROUTE_CELL));
        const r0 = Math.max(0, Math.floor((b.y - ROUTE_PAD) / ROUTE_CELL));
        const c1 = Math.min(
            cols - 1,
            Math.ceil((b.x + b.w + ROUTE_PAD) / ROUTE_CELL) - 1
        );
        const r1 = Math.min(
            rows - 1,
            Math.ceil((b.y + b.h + ROUTE_PAD) / ROUTE_CELL) - 1
        );
        for (let cy = r0; cy <= r1; cy++) {
            for (let cx = c0; cx <= c1; cx++) blocked[idx(cx, cy)] = 1;
        }
    }
    return {
        cols,
        rows,
        idx,
        cellOf(x, y) {
            return [
                Math.min(cols - 1, Math.max(0, Math.floor(x / ROUTE_CELL))),
                Math.min(rows - 1, Math.max(0, Math.floor(y / ROUTE_CELL))),
            ];
        },
        centerOf(cx, cy) {
            return { x: (cx + 0.5) * ROUTE_CELL, y: (cy + 0.5) * ROUTE_CELL };
        },
        isFree(cx, cy) {
            return (
                cx >= 0 &&
                cy >= 0 &&
                cx < cols &&
                cy < rows &&
                !blocked[idx(cx, cy)]
            );
        },
    };
}

function makeRouter(grid) {
    const { cols, rows, idx, isFree } = grid;
    const n = cols * rows;
    const g = new Float64Array(n);
    const came = new Int32Array(n).fill(-1);
    const stamp = new Int32Array(n);
    const dirIn = new Int32Array(n).fill(-1);
    const dirs = [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1],
    ];
    let token = 0;

    return function (sx, sy, tx, ty) {
        token += 1;
        const start = idx(sx, sy);
        const end = idx(tx, ty);
        if (start === end) return null;
        const h = (cx, cy) => Math.abs(cx - tx) + Math.abs(cy - ty);
        const heap = [];
        const push = (node, gv) => {
            const cx = node % cols;
            const cy = (node - cx) / cols;
            heap.push([gv + h(cx, cy), gv, node]);
            let i = heap.length - 1;
            while (i > 0) {
                const p = (i - 1) >> 1;
                if (heap[p][0] <= heap[i][0]) break;
                [heap[p], heap[i]] = [heap[i], heap[p]];
                i = p;
            }
        };
        const pop = () => {
            const top = heap[0];
            const last = heap.pop();
            if (heap.length) {
                heap[0] = last;
                let i = 0;
                for (;;) {
                    const l = 2 * i + 1;
                    const r = l + 1;
                    let m = i;
                    if (l < heap.length && heap[l][0] < heap[m][0]) m = l;
                    if (r < heap.length && heap[r][0] < heap[m][0]) m = r;
                    if (m === i) break;
                    [heap[m], heap[i]] = [heap[i], heap[m]];
                    i = m;
                }
            }
            return top;
        };
        g[start] = 0;
        stamp[start] = token;
        push(start, 0);
        while (heap.length) {
            const [, gv, cur] = pop();
            if (cur === end) break;
            if (gv > g[cur]) continue;
            const cx = cur % cols;
            const cy = (cur - cx) / cols;
            for (let d = 0; d < 4; d++) {
                const nx = cx + dirs[d][0];
                const ny = cy + dirs[d][1];
                if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
                const ni = idx(nx, ny);
                if (ni !== start && ni !== end && !isFree(nx, ny)) continue;
                const penalty =
                    dirIn[cur] === -1 || dirIn[cur] === d
                        ? 0
                        : ROUTE_TURN_PENALTY;
                const ng = g[cur] + 1 + penalty;
                if (stamp[ni] !== token || ng < g[ni]) {
                    g[ni] = ng;
                    came[ni] = cur;
                    dirIn[ni] = d;
                    stamp[ni] = token;
                    push(ni, ng);
                }
            }
        }
        if (stamp[end] !== token) return null;
        const cells = [];
        let cur = end;
        while (cur !== start) {
            cells.push(cur);
            cur = came[cur];
            if (cur < 0) return null;
        }
        cells.push(start);
        cells.reverse();
        return cells.map((ci) => {
            const cx = ci % cols;
            return grid.centerOf(cx, (ci - cx) / cols);
        });
    };
}

function simplifyPath(points) {
    const out = [];
    for (const p of points) {
        while (out.length >= 2) {
            const a = out[out.length - 2];
            const b = out[out.length - 1];
            const cross = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
            if (Math.abs(cross) < 1e-6) out.pop();
            else break;
        }
        out.push(p);
    }
    return out;
}

function pathToD(points) {
    return points
        .map(
            (pt, i) =>
                `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`
        )
        .join(' ');
}

// True if the segment (x1,y1)-(x2,y2) passes through the interior of the
// axis-aligned rect r = {x, y, w, h} (Liang-Barsky clipping).
function segmentIntersectsRect(x1, y1, x2, y2, r) {
    let t0 = 0;
    let t1 = 1;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const p = [-dx, dx, -dy, dy];
    const q = [x1 - r.x, r.x + r.w - x1, y1 - r.y, r.y + r.h - y1];
    for (let i = 0; i < 4; i++) {
        if (p[i] === 0) {
            if (q[i] < 0) return false;
        } else {
            const t = q[i] / p[i];
            if (p[i] < 0) {
                if (t > t1) return false;
                if (t > t0) t0 = t;
            } else {
                if (t < t0) return false;
                if (t < t1) t1 = t;
            }
        }
    }
    return t0 < t1;
}

function routeEdge(a, b, grid, router) {
    const p = edgePoints(a, b);
    const dx = p.x2 - p.x1;
    const dy = p.y2 - p.y1;
    const len = Math.hypot(dx, dy) || 1;
    const ux = dx / len;
    const uy = dy / len;
    const [sx, sy] = grid.cellOf(
        p.x1 + ux * (ROUTE_PAD + ROUTE_CELL),
        p.y1 + uy * (ROUTE_PAD + ROUTE_CELL)
    );
    const [tx, ty] = grid.cellOf(
        p.x2 - ux * (ROUTE_PAD + ROUTE_CELL),
        p.y2 - uy * (ROUTE_PAD + ROUTE_CELL)
    );
    const mid = router(sx, sy, tx, ty);
    let path;
    if (mid && mid.length >= 2) {
        path = [{ x: p.x1, y: p.y1 }, ...mid, { x: p.x2, y: p.y2 }];
    } else {
        path = [
            { x: p.x1, y: p.y1 },
            { x: p.x2, y: p.y2 },
        ];
    }
    path = simplifyPath(path);
    return { path, d: pathToD(path) };
}

// Place a set of models on concentric rings (hub-and-spoke).
function layoutMainRings(models, depthByName) {
    if (!models.length) return { raw: [], centerName: null };

    let minLevel = Infinity;
    const rings = {};
    for (const m of models) {
        const lvl = depthByName[m.name] || 1;
        minLevel = Math.min(minLevel, lvl);
        (rings[lvl] = rings[lvl] || []).push(m);
    }

    const heights = {};
    let maxH = 0;
    for (const m of models) {
        heights[m.name] = boxHeight(m);
        maxH = Math.max(maxH, heights[m.name]);
    }

    const raw = [];
    let prevOuter = maxH / 2;
    let centerName = null;
    const sortedLevels = Object.keys(rings)
        .map(Number)
        .sort((a, b) => a - b);
    for (const lvl of sortedLevels) {
        const list = rings[lvl];
        const ringIdx = lvl - minLevel;
        if (ringIdx === 0 && list.length === 1) {
            const h = heights[list[0].name];
            raw.push({
                model: list[0],
                cx: 0,
                cy: 0,
                w: BOX_W,
                h,
                depth: 0,
                isCenter: true,
            });
            centerName = list[0].name;
            prevOuter = maxH / 2;
            continue;
        }
        const n = list.length;
        const tangential =
            n <= 1 ? 0 : (BOX_W + RING_GAP) / (2 * Math.sin(Math.PI / n));
        const radius = Math.max(tangential, prevOuter + RING_GAP + maxH / 2);
        list.forEach((m, i) => {
            const angle = (i / n) * 2 * Math.PI - Math.PI / 2;
            raw.push({
                model: m,
                cx: radius * Math.cos(angle),
                cy: radius * Math.sin(angle),
                w: BOX_W,
                h: heights[m.name],
                depth: ringIdx,
            });
        });
        prevOuter = radius + maxH / 2;
    }
    return { raw, centerName };
}

function bboxOf(raw) {
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    for (const r of raw) {
        minX = Math.min(minX, r.cx - r.w / 2);
        minY = Math.min(minY, r.cy - r.h / 2);
        maxX = Math.max(maxX, r.cx + r.w / 2);
        maxY = Math.max(maxY, r.cy + r.h / 2);
    }
    return { minX, minY, maxX, maxY };
}

// Stack the outermost-ring tables vertically in columns on the right side.
function stackOuter(models, mainBBox) {
    if (!models.length) return [];
    const heights = models.map((m) => boxHeight(m));
    const maxH = Math.max(...heights);
    const gap = RING_GAP;
    const perCol = 8;
    const raw = [];
    models.forEach((m, i) => {
        const col = Math.floor(i / perCol);
        const row = i % perCol;
        const cx = mainBBox.maxX + gap + BOX_W / 2 + col * (BOX_W + gap);
        const cy =
            -(perCol * (maxH + gap)) / 2 +
            (maxH + gap) / 2 +
            row * (maxH + gap);
        raw.push({
            model: m,
            cx,
            cy,
            w: BOX_W,
            h: heights[i],
            isOuter: true,
        });
    });
    return raw;
}

// Full layout: main tables on concentric rings around Polygon; the outermost
// ring (disconnected / auxiliary tables) stacked in columns on the right.
function computeLayout(models, depthByName) {
    if (!models.length) {
        return { boxes: [], edges: [], width: 0, height: 0, centerName: null };
    }

    // Highest relationship level = the outermost ring.
    let maxLevel = 1;
    for (const m of models)
        maxLevel = Math.max(maxLevel, depthByName[m.name] || 1);

    const outer = [];
    const main = [];
    if (maxLevel > 1) {
        for (const m of models) {
            if ((depthByName[m.name] || 1) === maxLevel) outer.push(m);
            else main.push(m);
        }
    } else {
        main.push(...models);
    }
    if (!main.length) {
        main.push(...outer);
        outer.length = 0;
    }

    const { raw: mainRaw, centerName } = layoutMainRings(main, depthByName);
    const mainBBox = bboxOf(mainRaw);
    const raw = mainRaw.concat(stackOuter(outer, mainBBox));

    const bb = bboxOf(raw);
    const boxes = [];
    const boxByName = {};
    for (const r of raw) {
        const x = r.cx - r.w / 2 - bb.minX + MARGIN;
        const y = r.cy - r.h / 2 - bb.minY + MARGIN;
        boxes.push({
            model: r.model,
            x,
            y,
            w: r.w,
            h: r.h,
            depth: r.depth !== undefined ? r.depth : 0,
            isCenter: !!r.isCenter,
            isOuter: !!r.isOuter,
        });
        boxByName[r.model.name] = { x, y, w: r.w, h: r.h };
    }

    const width = bb.maxX - bb.minX + 2 * MARGIN;
    const height = bb.maxY - bb.minY + 2 * MARGIN;

    const grid = routeGrid(boxes, width, height);
    const router = makeRouter(grid);
    // Boxes inflated by the routing clearance, used to decide whether a straight
    // line would cut through a table (in which case it is routed around it).
    const inflated = boxes.map((bx) => ({
        name: bx.model.name,
        x: bx.x - ROUTE_PAD,
        y: bx.y - ROUTE_PAD,
        w: bx.w + 2 * ROUTE_PAD,
        h: bx.h + 2 * ROUTE_PAD,
    }));

    const edges = [];
    for (const m of models) {
        const a = boxByName[m.name];
        for (const f of m.fields) {
            if (f.related_model && boxByName[f.related_model]) {
                const b = boxByName[f.related_model];
                if (a === b) continue;
                const relation = f.relation || 'fk';
                const p = edgePoints(a, b);
                let crosses = false;
                for (const r of inflated) {
                    if (r.name === m.name || r.name === f.related_model)
                        continue;
                    if (segmentIntersectsRect(p.x1, p.y1, p.x2, p.y2, r)) {
                        crosses = true;
                        break;
                    }
                }
                const path = crosses
                    ? routeEdge(a, b, grid, router).path
                    : [
                          { x: p.x1, y: p.y1 },
                          { x: p.x2, y: p.y2 },
                      ];
                const first = path[0];
                const second = path[1];
                const last = path[path.length - 1];
                const prev = path[path.length - 2];
                const d1x = second.x - first.x;
                const d1y = second.y - first.y;
                const l1 = Math.hypot(d1x, d1y) || 1;
                const d2x = last.x - prev.x;
                const d2y = last.y - prev.y;
                const l2 = Math.hypot(d2x, d2y) || 1;
                const srcText = relation === 'o2o' ? '1' : 'N';
                const tgtText = relation === 'm2m' ? 'N' : '1';
                edges.push({
                    from: m.name,
                    to: f.related_model,
                    field: f.name,
                    relation,
                    path,
                    d: pathToD(path),
                    srcLabel: {
                        text: srcText,
                        x: first.x + (d1x / l1) * 18,
                        y: first.y + (d1y / l1) * 18,
                    },
                    tgtLabel: {
                        text: tgtText,
                        x: last.x - (d2x / l2) * 18,
                        y: last.y - (d2y / l2) * 18,
                    },
                });
            }
        }
    }

    return { boxes, edges, width, height, centerName };
}

export default {
    name: 'ERDiagram',
    data() {
        return {
            groups: [],
            excluded: new Set(),
            level: 2,
            loading: false,
            error: null,
            zoom: 1,
            panX: 0,
            panY: 0,
            dragging: false,
            maximized: false,
            sidebarCollapsed: false,
            hoveredEdge: null,
            edgePopup: null,
            viewportW: 0,
            viewportH: 0,
            minimapDragging: false,
            searchText: '',
            searchOpen: false,
            pendingFocus: null,
            BOX_W,
            HEADER_H,
            ROW_H,
            MAX_FIELDS,
        };
    },
    computed: {
        // Sidebar display order: Forest Blocks and Lookups first, then Main
        // and Proposals at the bottom.
        orderedGroups() {
            const order = ['forest_blocks', 'lookups', 'main', 'proposals'];
            return order
                .map((key) => this.groups.find((g) => g.key === key))
                .filter(Boolean);
        },
        // 1-based relationship level for every model (L1 = Polygon).
        depthByName() {
            const byName = {};
            for (const g of this.groups)
                for (const m of g.models) byName[m.name] = m;

            const adj = {};
            for (const m of Object.values(byName)) {
                adj[m.name] = adj[m.name] || new Set();
                for (const f of m.fields) {
                    if (f.related_model && byName[f.related_model]) {
                        adj[m.name].add(f.related_model);
                        (adj[f.related_model] =
                            adj[f.related_model] || new Set()).add(m.name);
                    }
                }
            }

            const depth = {};
            if (byName['Polygon']) {
                depth['Polygon'] = 0;
                const queue = ['Polygon'];
                while (queue.length) {
                    const cur = queue.shift();
                    for (const nb of adj[cur] || []) {
                        if (depth[nb] === undefined) {
                            depth[nb] = depth[cur] + 1;
                            queue.push(nb);
                        }
                    }
                }
            }

            let maxd = 0;
            for (const v of Object.values(depth)) maxd = Math.max(maxd, v);
            const levels = {};
            for (const m of Object.values(byName)) {
                const d =
                    depth[m.name] === undefined ? maxd + 1 : depth[m.name];
                levels[m.name] = d + 1;
            }
            return levels;
        },
        maxLevel() {
            let mx = 1;
            for (const v of Object.values(this.depthByName))
                mx = Math.max(mx, v);
            return mx;
        },
        // Tables rendered: every model except those manually excluded via the
        // checkbox list. All levels are always laid out; `level` only controls
        // how far the view is zoomed (which rings are in view), so deeper
        // rings sit "out of pan" and can be reached by panning.
        selected() {
            const s = new Set();
            for (const g of this.groups) {
                for (const m of g.models) {
                    if (!this.excluded.has(m.name)) s.add(m.name);
                }
            }
            return s;
        },
        selectedModels() {
            const out = [];
            for (const group of this.groups) {
                for (const model of group.models) {
                    if (this.selected.has(model.name)) {
                        out.push({
                            ...model,
                            group: group.key,
                            groupName: group.name,
                        });
                    }
                }
            }
            return out;
        },
        layout() {
            return computeLayout(this.selectedModels, this.depthByName);
        },
        // Visible region of the main viewport, in diagram (world) coordinates.
        viewportRect() {
            const z = this.zoom || 1;
            return {
                x: -this.panX / z,
                y: -this.panY / z,
                w: this.viewportW / z,
                h: this.viewportH / z,
            };
        },
        // Slider position: 0 = zoomed out (MIN_ZOOM), 1000 = zoomed in (MAX_ZOOM).
        zoomSliderValue() {
            const z = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, this.zoom));
            const p = Math.log(z / MIN_ZOOM) / Math.log(MAX_ZOOM / MIN_ZOOM);
            return Math.round(p * 1000);
        },
        // Flat list of table names in sidebar order, for the search dropdown.
        allTableNames() {
            const names = [];
            for (const g of this.orderedGroups)
                for (const m of g.models) names.push(m.name);
            return names;
        },
        searchOptions() {
            return ['All', ...this.allTableNames];
        },
        filteredSearchOptions() {
            const q = this.searchText.trim().toLowerCase();
            if (!q) return this.searchOptions;
            return this.searchOptions.filter((n) =>
                n.toLowerCase().includes(q)
            );
        },
    },
    watch: {
        level() {
            this.refit(true);
        },
        selectedModels() {
            if (this.pendingFocus) {
                const name = this.pendingFocus;
                this.pendingFocus = null;
                this.$nextTick(() => this.fitToTable(name));
                return;
            }
            this.refit(false);
        },
    },
    methods: {
        async loadData() {
            this.loading = true;
            this.error = null;
            try {
                const res = await fetch(api_endpoints.er_diagram);
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.error || 'Failed to load schema');
                }
                this.groups = data.groups || [];
                this.level = 2;
                // Default: Main and Proposals unchecked (except Proposal);
                // Forest Blocks and Lookups fully checked.
                const exclude = [];
                for (const g of this.groups) {
                    if (g.key === 'forest_blocks' || g.key === 'lookups') {
                        continue;
                    }
                    for (const m of g.models) {
                        if (m.name !== 'Proposal') exclude.push(m.name);
                    }
                }
                this.excluded = new Set(exclude);
            } catch (e) {
                this.error = String(e.message || e);
            } finally {
                this.loading = false;
            }
        },
        toggleModel(name) {
            const ex = new Set(this.excluded);
            if (ex.has(name)) ex.delete(name);
            else ex.add(name);
            this.excluded = ex;
        },
        toggleGroup(key) {
            const group = this.groups.find((g) => g.key === key);
            if (!group) return;
            const ex = new Set(this.excluded);
            const allShown = group.models.every((m) =>
                this.selected.has(m.name)
            );
            group.models.forEach((m) => {
                if (allShown) ex.add(m.name);
                else ex.delete(m.name);
            });
            this.excluded = ex;
        },
        selectAll() {
            this.excluded = new Set();
            this.level = this.maxLevel;
        },
        resetLevel() {
            this.level = 2;
        },
        isGroupAllSelected(group) {
            return (
                group.models.length > 0 &&
                group.models.every((m) => this.selected.has(m.name))
            );
        },
        selectedGroupCount(group) {
            return group.models.filter((m) => this.selected.has(m.name)).length;
        },
        displayFields(model) {
            return model.fields.slice(0, MAX_FIELDS);
        },
        fieldText(field) {
            let t = field.name;
            if (field.relation === 'fk' || field.relation === 'o2o') t += ' →';
            else if (field.relation === 'm2m') t += ' ✱';
            return t;
        },
        fieldColor(field) {
            if (field.pk) return '#212529';
            if (field.relation === 'fk' || field.relation === 'o2o')
                return '#0d6efd';
            if (field.relation === 'm2m') return '#198754';
            return '#6c757d';
        },
        isL2(b) {
            return (this.depthByName[b.model.name] || 1) === 2;
        },
        // Darken a #rrggbb colour by `factor` (1 = unchanged, 0.65 = 35% darker).
        darken(hex, factor) {
            const n = parseInt(hex.slice(1), 16);
            const r = Math.round(((n >> 16) & 255) * factor);
            const g = Math.round(((n >> 8) & 255) * factor);
            const b = Math.round((n & 255) * factor);
            return (
                '#' +
                ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
            );
        },
        boxFill(b) {
            if (b.isOuter) return '#e8f0fb';
            if (this.isL2(b)) return '#fdf3e0';
            if (b.isCenter) return '#d6ead6';
            return '#f3f9f3';
        },
        headerFill(b) {
            if (b.isOuter) return '#cddcf3';
            if (this.isL2(b)) return '#f0dcae';
            if (b.isCenter) return '#a9d0a9';
            return '#d9ead9';
        },
        boxStroke(b) {
            if (b.isOuter) return '#7d93c0';
            if (this.isL2(b)) return '#c09a4a';
            if (b.isCenter) return '#3d7a3d';
            return '#7a9a7a';
        },
        titleFill(b) {
            if (b.isOuter) return '#2f3d63';
            if (this.isL2(b)) return '#5c4716';
            if (b.isCenter) return '#1c4b1c';
            return '#212529';
        },
        isHighlighted(b) {
            return (
                this.hoveredEdge &&
                (b.model.name === this.hoveredEdge.from ||
                    b.model.name === this.hoveredEdge.to)
            );
        },
        // --- level-driven zoom ---
        zoomIn() {
            this.level = Math.max(1, this.level - 1);
        },
        zoomOut() {
            this.level = Math.min(this.maxLevel, this.level + 1);
        },
        onWheel(e) {
            const el = this.$refs.viewport;
            const rect = el ? el.getBoundingClientRect() : null;
            const ax = rect ? e.clientX - rect.left : null;
            const ay = rect ? e.clientY - rect.top : null;
            const factor = Math.pow(1.1, -e.deltaY / 100);
            this.setZoom(this.zoom * factor, ax, ay);
        },
        onMinimapWheel(e) {
            const factor = Math.pow(1.1, -e.deltaY / 100);
            this.setZoom(this.zoom * factor);
        },
        onZoomSlider(e) {
            const p = Number(e.target.value) / 1000;
            this.setZoom(MIN_ZOOM * Math.pow(MAX_ZOOM / MIN_ZOOM, p));
        },
        // Continuous geometric zoom. Anchors on the given viewport point
        // (defaults to the centre) so the world point under it stays fixed.
        setZoom(newZoom, anchorX = null, anchorY = null) {
            const z = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom));
            if (z === this.zoom) return;
            const el = this.$refs.viewport;
            const vw = el ? el.clientWidth : this.viewportW;
            const vh = el ? el.clientHeight : this.viewportH;
            if (vw && vh) {
                const ax = anchorX != null ? anchorX : vw / 2;
                const ay = anchorY != null ? anchorY : vh / 2;
                const wx = (ax - this.panX) / this.zoom;
                const wy = (ay - this.panY) / this.zoom;
                this.zoom = z;
                this.panX = ax - wx * z;
                this.panY = ay - wy * z;
            } else {
                this.zoom = z;
            }
        },
        onSearchSelect(name) {
            this.searchOpen = false;
            this.searchText = name === 'All' ? '' : name;
            this.zoomToTable(name);
        },
        onSearchBlur() {
            this._blurTimer = setTimeout(() => {
                this.searchOpen = false;
                this._blurTimer = null;
            }, 150);
        },
        onSearchFocus() {
            if (this._blurTimer) {
                clearTimeout(this._blurTimer);
                this._blurTimer = null;
            }
            this.searchOpen = true;
        },
        onEdgeEnter(e, event) {
            this.hoveredEdge = e;
            if (this._edgePopupTimer) {
                clearTimeout(this._edgePopupTimer);
                this._edgePopupTimer = null;
            }
            this.edgePopup = {
                edge: e,
                x: event.clientX,
                y: event.clientY,
            };
        },
        onEdgeLeave() {
            this.hoveredEdge = null;
            this.schedulePopupHide();
        },
        onPopupEnter() {
            if (this._edgePopupTimer) {
                clearTimeout(this._edgePopupTimer);
                this._edgePopupTimer = null;
            }
        },
        onPopupLeave() {
            this.schedulePopupHide();
        },
        schedulePopupHide() {
            if (this._edgePopupTimer) clearTimeout(this._edgePopupTimer);
            this._edgePopupTimer = setTimeout(() => {
                this.edgePopup = null;
                this._edgePopupTimer = null;
            }, 150);
        },
        selectTable(name) {
            if (this._edgePopupTimer) {
                clearTimeout(this._edgePopupTimer);
                this._edgePopupTimer = null;
            }
            this.edgePopup = null;
            this.hoveredEdge = null;
            this.zoomToTable(name);
        },
        // Focus the view on one table plus its immediately-connected neighbours.
        zoomToTable(name) {
            if (name === 'All') {
                this.selectAll();
                return;
            }
            if (this.excluded.has(name)) {
                // Auto-check first; the `selectedModels` watcher then fits the
                // view once the table is actually rendered.
                this.pendingFocus = name;
                this.excluded = new Set(
                    [...this.excluded].filter((n) => n !== name)
                );
            } else {
                // Already rendered — layout is current, fit immediately.
                this.fitToTable(name);
            }
        },
        fitToTable(name, attempt = 0) {
            const boxes = this.layout.boxes;
            const box = boxes.find((b) => b.model.name === name);
            if (!box) {
                if (attempt < 3) {
                    this.$nextTick(() => this.fitToTable(name, attempt + 1));
                }
                return;
            }
            const neighbours = new Set([name]);
            for (const e of this.layout.edges) {
                if (e.from === name) neighbours.add(e.to);
                else if (e.to === name) neighbours.add(e.from);
            }
            let minX = Infinity;
            let minY = Infinity;
            let maxX = -Infinity;
            let maxY = -Infinity;
            for (const b of boxes) {
                if (!neighbours.has(b.model.name)) continue;
                minX = Math.min(minX, b.x);
                minY = Math.min(minY, b.y);
                maxX = Math.max(maxX, b.x + b.w);
                maxY = Math.max(maxY, b.y + b.h);
            }
            if (minX === Infinity) return;
            const PAD = 60;
            minX -= PAD;
            minY -= PAD;
            maxX += PAD;
            maxY += PAD;
            const el = this.$refs.viewport;
            const vw = el ? el.clientWidth : this.viewportW;
            const vh = el ? el.clientHeight : this.viewportH;
            if (!vw || !vh) return;
            const s = Math.min(vw / (maxX - minX), vh / (maxY - minY));
            // Floor the zoom so the focused table stays prominent; far-away
            // neighbours then fall out of pan rather than shrinking the table.
            const newZoom = Math.max(MIN_FOCUS_ZOOM, Math.min(s, MAX_ZOOM));
            const cx = box.x + box.w / 2;
            const cy = box.y + box.h / 2;
            this.zoom = newZoom;
            this.panX = vw / 2 - cx * newZoom;
            this.panY = vh / 2 - cy * newZoom;
        },
        fitView(preserveCenter = false) {
            const el = this.$refs.viewport;
            if (!el || !this.layout.boxes.length) return;
            this.viewportW = el.clientWidth;
            this.viewportH = el.clientHeight;
            // Fit to the rings up to the current level. Deeper rings stay laid
            // out "out of pan" and are reachable by panning at the same zoom.
            const boxes = this.layout.boxes.filter(
                (b) => (this.depthByName[b.model.name] || 1) <= this.level
            );
            if (!boxes.length) return;
            let minX = Infinity;
            let minY = Infinity;
            let maxX = -Infinity;
            let maxY = -Infinity;
            for (const b of boxes) {
                minX = Math.min(minX, b.x);
                minY = Math.min(minY, b.y);
                maxX = Math.max(maxX, b.x + b.w);
                maxY = Math.max(maxY, b.y + b.h);
            }
            const contentW = maxX - minX;
            const contentH = maxY - minY;
            const s = Math.min(
                el.clientWidth / contentW,
                el.clientHeight / contentH
            );
            const newZoom = Math.max(MIN_ZOOM, Math.min(s, MAX_ZOOM));

            const vw = el.clientWidth;
            const vh = el.clientHeight;
            let centerX;
            let centerY;
            if (preserveCenter) {
                // Keep the world point currently at the viewport centre fixed,
                // so zooming happens at the user's current (panned) location.
                centerX = (vw / 2 - this.panX) / this.zoom;
                centerY = (vh / 2 - this.panY) / this.zoom;
            } else {
                centerX = (minX + maxX) / 2;
                centerY = (minY + maxY) / 2;
            }
            this.zoom = newZoom;
            this.panX = vw / 2 - centerX * newZoom;
            this.panY = vh / 2 - centerY * newZoom;
        },
        refit(preserveCenter = false) {
            this.$nextTick(() => {
                requestAnimationFrame(() => this.fitView(preserveCenter));
            });
        },
        toggleMaximize() {
            if (this.maximized) {
                this.maximized = false;
                if (document.fullscreenElement) {
                    document.exitFullscreen().catch(() => {});
                }
            } else {
                this.maximized = true;
                const el = this.$el;
                if (el && el.requestFullscreen) {
                    el.requestFullscreen().catch(() => {});
                }
            }
            this.$nextTick(() => this.updateViewportSize());
        },
        onFullscreenChange() {
            if (!document.fullscreenElement && this.maximized) {
                this.maximized = false;
            }
            this.$nextTick(() => this.updateViewportSize());
        },
        toggleSidebar() {
            this.sidebarCollapsed = !this.sidebarCollapsed;
            this.$nextTick(() => this.updateViewportSize());
        },
        updateViewportSize() {
            const el = this.$refs.viewport;
            if (el) {
                this.viewportW = el.clientWidth;
                this.viewportH = el.clientHeight;
            }
        },
        onResize() {
            this.updateViewportSize();
        },
        minimapTransform() {
            const svg = this.$refs.minimapSvg;
            if (!svg || !this.layout.width || !this.layout.height) return null;
            const rect = svg.getBoundingClientRect();
            const s = Math.min(
                rect.width / this.layout.width,
                rect.height / this.layout.height
            );
            const ox = (rect.width - this.layout.width * s) / 2;
            const oy = (rect.height - this.layout.height * s) / 2;
            return { s, ox, oy, rect };
        },
        onMinimapPointerDown(e) {
            this.minimapDragging = true;
            this._mmStart = {
                clientX: e.clientX,
                clientY: e.clientY,
                panX: this.panX,
                panY: this.panY,
            };
            window.addEventListener('pointermove', this.onMinimapPointerMove);
            window.addEventListener('pointerup', this.onMinimapPointerUp);
            e.preventDefault();
        },
        onMinimapPointerMove(e) {
            if (!this.minimapDragging) return;
            const t = this.minimapTransform();
            if (!t) return;
            const dx = (e.clientX - this._mmStart.clientX) / t.s;
            const dy = (e.clientY - this._mmStart.clientY) / t.s;
            this.panX = this._mmStart.panX - dx * this.zoom;
            this.panY = this._mmStart.panY - dy * this.zoom;
        },
        onMinimapPointerUp() {
            this.minimapDragging = false;
            window.removeEventListener(
                'pointermove',
                this.onMinimapPointerMove
            );
            window.removeEventListener('pointerup', this.onMinimapPointerUp);
        },
        // --- pan ---
        onMousedown(e) {
            if (e.button !== 0) return;
            this.dragging = true;
            this._drag = {
                x: e.clientX,
                y: e.clientY,
                panX: this.panX,
                panY: this.panY,
            };
            window.addEventListener('mousemove', this._dragMove);
            window.addEventListener('mouseup', this._dragEnd);
            e.preventDefault();
        },
        _dragMove(e) {
            if (!this.dragging) return;
            this.panX = this._drag.panX + (e.clientX - this._drag.x);
            this.panY = this._drag.panY + (e.clientY - this._drag.y);
        },
        _dragEnd() {
            this.dragging = false;
            window.removeEventListener('mousemove', this._dragMove);
            window.removeEventListener('mouseup', this._dragEnd);
        },
    },
    async mounted() {
        await this.loadData();
        this.$nextTick(() => this.fitView());
        document.addEventListener('fullscreenchange', this.onFullscreenChange);
        window.addEventListener('resize', this.onResize);
    },
    beforeUnmount() {
        window.removeEventListener('mousemove', this._dragMove);
        window.removeEventListener('mouseup', this._dragEnd);
        window.removeEventListener('pointermove', this.onMinimapPointerMove);
        window.removeEventListener('pointerup', this.onMinimapPointerUp);
        window.removeEventListener('resize', this.onResize);
        document.removeEventListener(
            'fullscreenchange',
            this.onFullscreenChange
        );
    },
};
</script>

<style scoped>
.er-viewport-wrap {
    position: relative;
}
.er-diagram-col {
    position: relative;
}
.er-reopen-btn {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 10;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
.er-minimap {
    display: block;
    touch-action: none;
    cursor: crosshair;
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 4px;
}
.er-zoom-slider {
    min-width: 70px;
}
.er-search-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 30;
    max-height: 200px;
    overflow-y: auto;
    margin: 2px 0 0;
    padding: 0;
    background: #fff;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}
.er-search-dropdown li {
    padding: 4px 10px;
    cursor: pointer;
    font-size: 0.85rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.er-search-dropdown li:hover {
    background: #e9f0f9;
}
.er-edge-popup {
    position: fixed;
    z-index: 1060;
    min-width: 200px;
    max-width: 280px;
    padding: 6px;
    background: #fff;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
}
.er-edge-popup-title {
    padding: 2px 6px 6px;
    font-size: 0.75rem;
    color: #6c757d;
    word-break: break-all;
}
.er-edge-popup-item {
    display: block;
    width: 100%;
    text-align: left;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.er-edge-popup-item:last-child {
    margin-bottom: 0;
}
.er-viewport {
    position: relative;
    overflow: hidden;
    height: 75vh;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    cursor: grab;
    user-select: none;
}
.er-viewport.dragging {
    cursor: grabbing;
}
.er-maximized {
    position: fixed;
    inset: 0;
    z-index: 1050;
    background: #fff;
    margin: 0;
    padding: 1rem;
    overflow: auto;
}
.er-maximized .er-viewport {
    height: calc(100vh - 48px);
}
.er-toolbar {
    position: absolute;
    top: 8px;
    right: 8px;
    display: flex;
    gap: 2px;
    padding: 2px;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid #dee2e6;
    border-radius: 6px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
.er-toolbar .btn {
    line-height: 1.2;
}
.er-toolbar-pct {
    min-width: 62px;
    font-variant-numeric: tabular-nums;
}
.er-title {
    font-size: 12px;
    font-weight: bold;
}
.er-field {
    font-size: 10px;
    font-family:
        'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}
.er-cardinality {
    font-size: 10px;
    font-weight: bold;
    fill: #44536e;
    stroke: #ffffff;
    stroke-width: 3px;
    paint-order: stroke;
}
.er-cardinality-hover {
    font-size: 12px;
    font-weight: bold;
    fill: #e74c3c;
    stroke: #ffffff;
    stroke-width: 3px;
    paint-order: stroke;
}
</style>
