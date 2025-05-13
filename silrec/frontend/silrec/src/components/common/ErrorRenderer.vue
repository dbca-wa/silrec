<template>
    <template v-if="typeof errors === 'string'">
        {{ errors }}
    </template>
    <template v-else>
        <template v-if="Array.isArray(errors)">
            <template v-if="errors.length > 1">
                <ul class="errors-list">
                    <li v-for="(error, index) in errors" :key="index">
                        {{ error.detail }}
                    </li>
                </ul>
            </template>
            <template v-else>
                <template v-if="typeof errors[0] === 'object'">
                    <template v-if="Object.keys(errors[0]).length > 1">
                        <template v-if="Object.hasOwn(errors[0], 'detail')">
                            {{ errors[0].detail }}
                        </template>
                        <template v-else>
                            <ul class="errors-list">
                                <li v-for="(error, key) in errors" :key="key">
                                    <span class="fw-bold">{{ key }}</span
                                    >: {{ error }}
                                </li>
                            </ul>
                        </template>
                    </template>
                    <template v-else>
                        <span class="fw-bold">{{
                            Object.keys(errors[0])[0]
                        }}</span
                        >: {{ Object.values(errors[0])[0] }}
                    </template>
                </template>
                <template v-else>
                    {{ errors[0] }}
                </template>
            </template>
        </template>

        <template v-else-if="typeof errors === 'object'">
            <template v-if="Object.keys(errors).length > 1">
                <ul class="errors-list">
                    <li v-for="(error, key) in errors" :key="key">
                        <span class="fw-bold">{{ key }}</span
                        >: {{ error }}
                    </li>
                </ul>
            </template>
            <template v-else>
                <span class="fw-bold">{{ Object.keys(errors)[0] }}</span
                >: {{ Object.values(errors)[0] }}
            </template>
        </template>
    </template>
</template>

<script>
export default {
    name: 'ErrorRenderer',
    props: {
        errors: {
            type: [Object, String, Array],
            required: true,
        },
    },
};
</script>
<style scoped>
.errors-list {
    margin-bottom: 0;
}
</style>
