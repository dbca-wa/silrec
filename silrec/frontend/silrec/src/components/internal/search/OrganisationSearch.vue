<template lang="html">
    <div class="row form-group">
        <div class="col-md-3">
            <label :for="index" class="ms-3">
                <strong>{{ 'Search ' + label }}:</strong>
            </label>
        </div>
        <div class="col-md-5">
            <select
                :id="index"
                :ref="index"
                :name="index"
                class="form-control"
                @change="checkResults"
            />
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';

export default {
    name: 'Select2SearchOrganisation',
    props: {
        label: {
            type: String,
            required: true,
        },
        lookupApiEndpoint: {
            type: String,
            required: true,
        },
        theme: {
            type: String,
            default: 'bootstrap-5',
        },
    },
    emits: ['selected', 'new-organisation'],
    data: function () {
        return {
            email_user: null,
            uuid: uuid(),
            term: null,
            index: 'search-' + this.label.toLowerCase().replace(' ', '-'),
        };
    },
    mounted: function () {
        this.initialiseLookup();
    },
    methods: {
        initialiseLookup: function () {
            let vm = this;
            $(`#${vm.index}`)
                .select2({
                    minimumInputLength: 2,
                    theme: vm.theme,
                    allowClear: true,
                    placeholder: 'Start Typing the Organisation Name or ABN',
                    ajax: {
                        url: vm.lookupApiEndpoint,
                        dataType: 'json',
                        data: function (params) {
                            vm.term = params.term;
                            let query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
                        },
                        processResults: function (data) {
                            if (0 == data.results.length) {
                                $(`#${vm.index}`).select2('close');
                                vm.$emit('new-organisation', vm.term);
                                return {
                                    results: [],
                                };
                            }

                            return {
                                results: data.results,
                            };
                        },
                    },
                })
                .on('select2:open', function () {
                    const searchField = $(
                        `[aria-controls='select2-${vm.index}-results']`
                    );
                    searchField[0].focus();
                })
                .on('select2:select', function (e) {
                    var data = e.params.data;
                    vm.$emit('selected', data);
                });
        },
        checkResults: function () {
            let vm = this;
            let selected = $(`#${vm.index}`).select2('data');
            if (selected.length > 0) {
                window.location.href = vm.redirectPath + selected[0].id;
            }
        },
    },
};
</script>
