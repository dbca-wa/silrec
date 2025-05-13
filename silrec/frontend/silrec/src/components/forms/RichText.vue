<script setup>
import { ref, computed, nextTick, watch } from 'vue';
import { ClassicEditor, Essentials, Paragraph, Bold, Italic } from 'ckeditor5';
import { Ckeditor } from '@ckeditor/ckeditor5-vue';

import 'ckeditor5/ckeditor5.css';

const props = defineProps({
    id: {
        type: String,
        required: true,
    },
    proposalData: {
        type: String,
        default: '',
    },
    isRequired: {
        type: Boolean,
        default: false,
    },
    readonly: {
        type: Boolean,
        default: false,
    },
    placeholderText: {
        type: String,
        default: '',
    },
});

const emit = defineEmits(['textChanged']);

const detailsText = ref('');

watch(detailsText, () => {
    if (props.proposalData == detailsText.value) {
        // Only emit if the text was changed through input, not through the parent component
        return;
    }
    emit('textChanged', detailsText.value);
});

const config = computed(() => {
    return {
        licenseKey: 'GPL',
        plugins: [Essentials, Paragraph, Bold, Italic],
        toolbar: ['undo', 'redo', '|', 'bold', 'italic'],
    };
});

function focus() {
    nextTick(() => {
        $('.ck-editor__editable').focus();
    });
}

defineExpose({
    focus,
});

if (props.proposalData) {
    detailsText.value = props.proposalData;
}

if (props.placeholderText) {
    config.value.placeholder = props.placeholderText;
}

config.value.readOnly = props.readonly;
</script>
<template lang="html">
    <ckeditor
        :id="id"
        v-model="detailsText"
        :editor="ClassicEditor"
        :config="config"
        :required="isRequired"
        :disabled="readonly"
        :read-only="readonly"
    />
</template>
