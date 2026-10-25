<template>
    <div class="rich-diff">
        <div class="d-flex align-items-center gap-2 mb-2">
            <span class="small fw-semibold">View:</span>
            <div class="btn-group btn-group-sm">
                <button
                    type="button"
                    class="btn"
                    :class="
                        mode === 'split'
                            ? 'btn-primary'
                            : 'btn-outline-secondary'
                    "
                    @click="mode = 'split'"
                >
                    Side-by-side
                </button>
                <button
                    type="button"
                    class="btn"
                    :class="
                        mode === 'inline'
                            ? 'btn-primary'
                            : 'btn-outline-secondary'
                    "
                    @click="mode = 'inline'"
                >
                    Unified
                </button>
            </div>
        </div>

        <template v-if="mode === 'split'">
            <table class="table table-sm table-bordered mb-0 diff-table">
                <thead>
                    <tr>
                        <th class="field-col">Field</th>
                        <th>Old</th>
                        <th>New</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="c in changes" :key="c.field">
                        <td class="field-col align-top">
                            <code>{{ fieldLabel(c.field) }}</code>
                        </td>
                        <td
                            class="diff-cell align-top"
                            v-html="c.old_side"
                        ></td>
                        <td
                            class="diff-cell align-top"
                            v-html="c.new_side"
                        ></td>
                    </tr>
                </tbody>
            </table>
        </template>
        <template v-else>
            <div v-for="c in changes" :key="c.field" class="mb-2">
                <code class="fw-semibold">{{ fieldLabel(c.field) }}</code>
                <div class="diff-cell" v-html="c.inline"></div>
            </div>
        </template>
    </div>
</template>

<script>
import { FIELD_LABELS } from '@/utils/fieldLabels';

export default {
    name: 'RichDiff',
    props: {
        changes: { type: Array, default: () => [] },
    },
    data() {
        return { mode: 'split' };
    },
    methods: {
        fieldLabel(name) {
            return FIELD_LABELS[name] || name;
        },
    },
};
</script>

<style scoped>
.field-col {
    width: 22%;
    white-space: nowrap;
}
.diff-cell {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.85rem;
    white-space: pre-wrap;
    word-break: break-word;
}
.diff-cell :deep(del) {
    background-color: #ffd7d7;
    text-decoration: line-through;
    color: #a00;
}
.diff-cell :deep(ins) {
    background-color: #d4f7d4;
    text-decoration: none;
    color: #063;
}
.diff-cell :deep(pre.highlight) {
    margin: 0;
    white-space: pre-wrap;
    font-family: inherit;
    font-size: inherit;
}
.diff-cell :deep(.diff-line.diff-del) {
    background-color: #ffd7d7;
}
.diff-cell :deep(.diff-line.diff-ins) {
    background-color: #d4f7d4;
}
</style>
