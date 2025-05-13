<template>
    <div id="approvalsDash" class="container">
        <ul id="pills-tab" class="nav nav-pills" role="tablist">
            <li class="nav-item">
                <a
                    id="pills-approvals-tab"
                    class="nav-link active"
                    data-bs-toggle="pill"
                    href="#pills-approvals"
                    role="tab"
                    aria-controls="pills-approvals"
                    aria-selected="true"
                    @click="tabClicked('approvals')"
                    >Approvals</a
                >
            </li>
            <li class="nav-item">
                <a
                    id="pills-map-tab"
                    class="nav-link"
                    data-bs-toggle="pill"
                    href="#pills-map"
                    role="tab"
                    aria-controls="pills-map"
                    aria-selected="false"
                    @click="mapTabClicked"
                    >Map</a
                >
            </li>
        </ul>
        <div id="pills-tabContent" class="tab-content">
            <div
                id="pills-approvals"
                class="tab-pane active"
                role="tabpanel"
                aria-labelledby="pills-approvals-tab"
            >
                <FormSection
                    :form-collapse="false"
                    label="Approvals"
                    index="approvals"
                >
                    <ApprovalsTable
                        ref="approvals_table"
                        level="internal"
                        :approval-type-filter="approvalTypeFilter"
                    />
                </FormSection>
            </div>
            <div
                id="pills-map"
                class="tab-pane"
                role="tabpanel"
                aria-labelledby="pills-map-tab"
            >
                <FormSection
                    v-if="loadMap"
                    :form-collapse="false"
                    label="Map"
                    index="map"
                >
                    <MapComponent
                        ref="component_map_with_filters"
                        level="internal"
                    />
                </FormSection>
            </div>
        </div>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import ApprovalsTable from '@/components/common/table_approvals.vue';
import MapComponent from '@/components/common/component_map.vue';

export default {
    name: 'InternalApprovalsDashboard',
    components: {
        FormSection,
        ApprovalsTable,
        MapComponent,
    },
    data() {
        return {
            approvalTypeFilter: ['ml', 'aap', 'aup'],
            loadMap: false,
        };
    },
    methods: {
        tabClicked: function (param) {
            if (param == 'approvals') {
                this.$refs.approvals_table.adjust_table_width();
            }
        },
        mapTabClicked: function () {
            this.loadMap = true;
            // this.$nextTick(() => {
            //     this.$refs.component_map_with_filters.forceToRefreshMap()
            // })
        },
    },
};
</script>
