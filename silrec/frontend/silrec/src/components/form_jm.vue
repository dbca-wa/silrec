<template lang="html">
    <div>
        <div v-if="proposal">
            {{ proposal.lodgement_number }}
        </div>
    </div>
</template>

<script>
export default {
    name: 'ProposalForm',
    components: {},
    props: {
        proposal: {
            type: Object,
            required: true,
        },
        is_internal: {
            type: Boolean,
            default: false,
        },
    },
    data: function () {
        return {};
    },
    computed: {},
    created: function () {},
    mounted: function () {
        //console.log('form.vue ' + this.proposal.lodgement_number)
    },
    methods: {},
};
</script>

<style lang="css" scoped>
.question-title {
    padding-left: 15px;
}

.section-style {
    padding-left: 15px;
    margin-bottom: 20px;
}

.list-inline-item {
    padding-right: 15px;
}

.section {
    text-transform: capitalize;
}

.list-group {
    margin-bottom: 0;
}

.fixed-top {
    position: fixed;
    top: 56px;
}

.nav-item {
    margin-bottom: 2px;
}

.nav-item > li > a {
    background-color: yellow !important;
    color: #fff;
}

.nav-item > li.active > a,
.nav-item > li.active > a:hover,
.nav-item > li.active > a:focus {
    color: white;
    background-color: blue;
    border: 1px solid #888888;
}

.admin > div {
    display: inline-block;
    vertical-align: top;
    margin-right: 1em;
}

.nav-pills .nav-link {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    border-top-left-radius: 0.5em;
    border-top-right-radius: 0.5em;
    margin-right: 0.25em;
}

.nav-pills .nav-link {
    background: lightgray;
}

.nav-pills .nav-link.active {
    background: gray;
}
</style>
