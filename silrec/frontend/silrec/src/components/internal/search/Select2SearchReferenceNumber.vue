<template lang="html">
    <FormSection :label="'Search ' + label" :index="index">
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
                />
            </div>
        </div>
    </FormSection>
</template>

<script>
import { v4 as uuid } from 'uuid';
import FormSection from '@/components/forms/section_toggle.vue';

export default {
    name: 'Select2SearchReferenceNumber',
    components: {
        FormSection,
    },
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
    data: function () {
        return {
            email_user: null,
            uuid: uuid(),
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
                    placeholder: 'Select ' + vm.label,
                    ajax: {
                        url: vm.lookupApiEndpoint,
                        dataType: 'json',
                        data: function (params) {
                            let query = {
                                term: params.term,
                                type: 'public',
                            };
                            return query;
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
                    window.location = data['redirect_url'];
                });
        },
    },
};
</script>
