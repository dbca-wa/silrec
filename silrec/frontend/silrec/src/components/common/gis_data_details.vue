<template lang="html">
    <div
        v-for="(data, idx) in selectedData"
        :key="newKey(idx)"
        :set="selected_data_item = selected_data(idx)"
    >
        <form v-if="data" class="form-horizontal mb-2">
            <div class="mb-3 row">
                <label
                    :for="`txt-gis-data-${idx}`"
                    :class="bsClassLabel"
                    class="col-form-label text-capitalize"
                    >{{ idx }}</label
                >
                <div :class="bsClassSelection">
                    <Multiselect
                        :id="`txt-gis-data-${idx}`"
                        v-model="selected_data_item"
                        :label="label"
                        :track-by="trackBy"
                        :placeholder="taggedPlaceholder({ property: idx })"
                        :options="gis_data[idx] || selected_data[idx] || []"
                        :hide-selected="hideSelected"
                        :multiple="multiple"
                        :searchable="searchable"
                        :disabled="readonly"
                        :loading="loading_indicators[idx] || false"
                        @search-change="ajaxLookupGeodata(idx, $event)"
                        @remove="removeHandler(idx, $event)"
                        @select="selectHandler(idx, $event)"
                    />
                </div>
            </div>
        </form>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import Multiselect from 'vue-multiselect';
import { api_endpoints, utils, helpers } from '@/utils/hooks';

export default {
    name: 'GisDataDetails',
    components: {
        Multiselect,
    },
    props: {
        /**
         * A dictionary of pre-selected geodata. e.g. {'regions': [{'id': 1, 'name': 'Region 1'}]}
         */
        selectedData: {
            type: Object,
            required: true,
            default: function () {
                return {};
            },
        },
        /**
         * A template string placeholder text to display in the input field in the form of
         * "This is a ${property} placeholder text" where ${property} is a supposed to
         * dynamically replaced by the respective property name.
         */
        placeholder: {
            type: String,
            required: false,
            default: 'Start typing to search ${property}',
        },
        /**
         * The name of the property name to use as the label for the geodata.
         */
        label: {
            type: String,
            required: false,
            default: 'name',
        },
        /**
         * The property to use as the unique identifier for the geodata.
         */
        trackBy: {
            type: String,
            required: false,
            default: 'id',
        },
        bsClassLabel: {
            type: String,
            required: false,
            default: 'col-3',
        },
        bsClassSelection: {
            type: String,
            required: false,
            default: 'col-9',
        },
        searchable: {
            type: Boolean,
            required: false,
            default: true,
        },
        readonly: {
            type: Boolean,
            required: false,
            default: false,
        },
        multiple: {
            type: Boolean,
            required: false,
            default: true,
        },
        hideSelected: {
            type: Boolean,
            required: false,
            default: true,
        },
    },
    emits: ['update:selectedData'],
    data() {
        return {
            gis_data: {
                default() {
                    return {};
                },
            },
            loading_indicators: {
                default() {
                    return {};
                },
            },
            keys: {
                default() {
                    return {};
                },
            },
        };
    },
    computed: {
        selected_data: {
            get: function () {
                return (idx) => {
                    return this.selectedData[idx];
                };
            },
        },
    },
    mounted: function () {
        let vm = this;
        vm.$nextTick(() => {
            vm.gis_data_selected = Object.assign({}, vm.selectedData);
        });
    },
    methods: {
        /**
         * Sets a list of geodata for a given property (e.g. 'regions', 'districts', 'vestings')
         * @param {String} property The property to lookup
         * @param {String} query The query to search for
         */
        ajaxLookupGeodata: function (property, query) {
            let vm = this;
            vm.loading_indicators[property] = true;
            utils
                .fetchKeyValueLookup(api_endpoints[property], query)
                .then((data) => {
                    vm.loading_indicators[property] = false;
                    vm.gis_data[property] = data;
                });
        },
        selectHandler: function (property, value) {
            let vm = this;
            vm.$emit('update:selectedData', property, value);
            vm.keys[property] = uuid();
        },
        removeHandler: function (property, value) {
            let vm = this;
            vm.$emit('update:selectedData', property, value);
            vm.keys[property] = uuid();
        },
        /**
         * Returns a placeholder string with dynamically inserted geodata property name
         * @param {*} params A dictionary of a parameter to be used in the placeholder. e.g. {'property': 'Xyz'}
         */
        taggedPlaceholder: function (params) {
            let vm = this;
            // A reference to the template tag function
            // eslint-disable-next-line no-unused-vars
            const template = helpers.template;
            // Split
            let parts = vm.placeholder
                .replace('${property}', '||${property}||')
                .split('||');
            // Remove empty parts
            parts = parts.filter((part) => part !== '');
            // Construct a template string for evaluation
            let evalString = 'template`';
            for (let part of parts) {
                if (part != '${property}') {
                    // Don't overwrite. Property should already be in the params dictionary
                    params[part] = part;
                    evalString += '${"' + part + '"}';
                } else {
                    evalString += '${"property"}';
                }
            }
            evalString += '`';
            // TODO: Refactor to not use eval. Strongly discouraged for security reasons
            // Evaluate the template string
            const _placeholder = eval(evalString);
            // Return the evaluated template string
            return _placeholder(params);
        },
        newKey: function (idx) {
            let vm = this;
            if (!vm.keys[idx]) {
                vm.keys[idx] = uuid();
            }
            return vm.keys[idx];
        },
    },
};
</script>
