<template>
    <button v-if="isLoading" disabled>
        <div class="spinner-border spinner-border-sm text-light" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    </button>
    <button @click="click" v-else>
        {{ text }}
    </button>
</template>

<script>
export default {
    name: 'BootstrapLoadingButton',
    props: {
        text: {
            type: String,
            required: true,
        },
        isLoading: {
            type: Boolean,
            default: false,
        },
    },
    emits: ['click'],
    methods: {
        click() {
            this.$emit('click');
        },
    },
};
</script>
