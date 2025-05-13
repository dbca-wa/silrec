<template>
    <div class="container" id="SearchDash">
        <Select2Search
            label="Person"
            :lookupApiEndpoint="api_endpoints.person_lookup"
            redirectPath="/internal/person/details/"
        />

        <Select2Search
            label="Organisation"
            :lookupApiEndpoint="api_endpoints.organisation_lookup"
            redirectPath="/internal/organisations/"
        />

        <Select2SearchReferenceNumber
            label="Reference Number"
            :lookupApiEndpoint="api_endpoints.search_reference"
        />
    </div>
</template>

<script>
import Select2SearchReferenceNumber from './Select2SearchReferenceNumber.vue';
import { api_endpoints } from '@/utils/hooks.js';

export default {
    name: 'InternalSearch',
    data() {
        return {
            api_endpoints: api_endpoints,
        };
    },
    components: {
        Select2SearchReferenceNumber,
    },
};
</script>
