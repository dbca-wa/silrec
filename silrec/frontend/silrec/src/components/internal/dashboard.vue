<template>
    <div id="externalDash" class="container">
        <div v-if="is_debug">src/components/internal/dashboard.vue</div>
        <ul
            v-if="show_tabs"
            id="pills-tab"
            class="nav nav-pills"
            role="tablist"
        >
            <li class="nav-item">
                <a
                    id="pills-applications-tab"
                    class="nav-link"
                    data-bs-toggle="pill"
                    href="#pills-applications"
                    role="tab"
                    aria-controls="pills-applications"
                    aria-selected="true"
                    @click="tabClicked('applications')"
                    >Proposals</a
                >
            </li>
            <li v-if="show_competitive_processes_tab" class="nav-item">
                <a
                    id="pills-competitive-processes-tab"
                    class="nav-link"
                    data-bs-toggle="pill"
                    href="#pills-competitive-processes"
                    role="tab"
                    aria-controls="pills-competitive-processes"
                    aria-selected="false"
                    @click="tabClicked('competitive-processes')"
                    >Competitive Processes</a
                >
            </li>
            <li v-if="show_applications_datatable" class="nav-item">
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
                id="pills-applications"
                class="tab-pane active"
                role="tabpanel"
                aria-labelledby="pills-applications-tab"
            >
                <FormSection
                    v-if="show_applications_datatable"
                    :form-collapse="false"
                    label="Proposals"
                    index="applications"
                >
                    <ApplicationsTable
                        ref="applications_table"
                        level="internal"
                        filter-application-type-cache-name="filterApplicationType"
                        filter-application-status-cache-name="filterApplicationStatus"
                        filter-proposal-lodged-from-cache-name="filterApplicationLodgedFrom"
                        filter-proposal-lodged-to-cache-name="filterApplicationLodgedTo"
                        @filter-appied="filterAppliedApplications()"
                    />
                </FormSection>
                <FormSection
                    :form-collapse="false"
                    label="Proposals Referred to Me"
                    index="leases_and_licences"
                >
                    <ApplicationsReferredToMeTable
                        v-if="accessing_user"
                        ref="applications_referred_to_me_table"
                        level="internal"
                        :email_user_id_assigned="accessing_user.id"
                        filter-application-type-cache-name="filterApplicationTypeForApplicationReferredToMeTable"
                        filter-application-status-cache-name="filterApplicationStatusForApplicationReferredToMeTable"
                        filter-proposal-lodged-from-cache-name="filterApplicationLodgedFromForApplicationReferredToMeTable"
                        filter-proposal-lodged-to-cache-name="filterApplicationLodgedToForApplicationReferredToMeTable"
                    />
                </FormSection>
            </div>
            <div
                v-if="show_competitive_processes_tab"
                id="pills-competitive-processes"
                class="tab-pane"
                role="tabpanel"
                aria-labelledby="pills-competitive-processes-tab"
            >
                <FormSection
                    :form-collapse="false"
                    label="Competitive Processes"
                    index="competitive_processes"
                >
                    <CompetitiveProcessesTable
                        ref="competitive_processes_table"
                    />
                </FormSection>
            </div>
            <div
                id="pills-map"
                class="tab-pane"
                role="tabpanel"
                aria-labelledby="pills-map-tab"
            >
                <FormSection :form-collapse="false" label="Map" index="map">
                    <MapComponent
                        v-if="loadMap"
                        ref="component_map_with_filters"
                        level="internal"
                        @filter-appied="filterAppliedMap"
                    />
                </FormSection>
            </div>
        </div>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import ApplicationsTable from '@/components/common/table_proposals.vue';
import ApplicationsReferredToMeTable from '@/components/common/table_proposals.vue';
import CompetitiveProcessesTable from '@/components/common/table_competitive_processes.vue';
import MapComponent from '@/components/common/component_map.vue';
import { api_endpoints } from '@/utils/hooks.js';

export default {
    name: 'InternalDashboard',
    components: {
        FormSection,
        ApplicationsTable,
        ApplicationsReferredToMeTable,
        CompetitiveProcessesTable,
        MapComponent,
    },
    data() {
        return {
            accessing_user: null,
            loadMap: false,
            proposals_url: api_endpoints.proposals_paginated_external,
            approvals_url: api_endpoints.approvals_paginated_external,
            compliances_url: api_endpoints.compliances_paginated,
            system_name: api_endpoints.system_name,
        };
    },
    computed: {
        is_debug: function () {
            return Object.prototype.hasOwnProperty.call(
                this.$route.query,
                'debug'
            ) && this.$route.query.debug == 'true'
                ? true
                : false;
        },
        is_external: function () {
            return this.level == 'external';
        },
        is_internal: function () {
            return this.level == 'internal';
        },
        show_applications_datatable: function () {
            if (this.accessing_user) {
                return (
                    this.accessing_user.is_assessor ||
                    this.accessing_user.is_approver ||
                    this.accessing_user.is_finance_officer
                );
            } else {
                return false;
            }
        },
        show_competitive_processes_tab: function () {
            if (this.accessing_user) {
                return this.accessing_user.is_competitive_process_editor;
            } else {
                return false;
            }
        },
        show_tabs: function () {
            return (
                this.show_applications_datatable ||
                this.show_competitive_processes_tab
            );
        },
    },
    mounted: async function () {
        const res = await fetch('/api/profile');
        const resData = await res.json();
        this.accessing_user = resData;
        this.$nextTick(function () {
            // eslint-disable-next-line no-undef
            chevron_toggle.init();
            this.set_active_tab('pills-applications');
        });
    },
    methods: {
        tabClicked: function (param) {
            if (param == 'applications') {
                if (this.show_applications_datatable) {
                    this.$refs.applications_table.adjust_table_width();
                }
                this.$refs.applications_referred_to_me_table.adjust_table_width();
            } else if (param === 'competitive-processes') {
                this.$refs.competitive_processes_table.adjust_table_width();
            }
        },
        mapTabClicked: function () {
            this.loadMap = true;
        },
        set_active_tab: function (tab_href_name) {
            if (!this.show_tabs) return;
            let elem = $('#pills-tab a[href="#' + tab_href_name + '"]');
            let tab = bootstrap.Tab.getInstance(elem);
            if (!tab) tab = new bootstrap.Tab(elem);
            tab.show();
        },
        filterAppliedApplications: function () {
            if (this.$refs.component_map_with_filters) {
                this.$refs.component_map_with_filters.updateFilters();
                this.$refs.component_map_with_filters.applyFiltersFrontEnd();
            }
        },
        filterAppliedMap: function () {
            this.$refs.applications_table.updateFilters();
        },
    },
};
</script>

<style lang="css" scoped>
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

.admin > div {
    display: inline-block;
    vertical-align: top;
    margin-right: 1em;
}
</style>
