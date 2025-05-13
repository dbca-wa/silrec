<template>
    <div id="app">
        <router-view></router-view>
    </div>
</template>

<script>
export default {
    name: 'App',
};
</script>

<style>
.popover {
    max-width: 100% !important;
}
.select2-container--disabled,
.select2-container--focus {
    z-index: 1;
}
</style>
