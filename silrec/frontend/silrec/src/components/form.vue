<template lang="html">
    <div class="">
        <div v-if="proposal">
		    JM - {{proposal.id}}
        </div>
        <div v-if="debug">components/form.vue</div>
        <div
            v-if="proposal"
            id="scrollspy-heading"
            class=""
        >
            <h3>
		    {{proposal.id}}
            </h3>
        </div>
	            <!--JM {{geometriesToFeatureCollection}}-->
                    <FormSection
                        :form-collapse="false"
                        label="Map"
                        index="proposal_geometry"
                    >
                        <slot name="slot_map_assessment_comments"></slot>
                        <MapComponent
                            ref="component_map"
                            :key="componentMapKey"
                            :context="proposal"
                            :proposal-ids="[-1]"
                            :featureCollection="geometriesToFeatureCollection"
                            :featureCollection2="geometriesToFeatureCollection2"
                            :featureCollection3="geometriesToFeatureCollection2"
                            :ows-query="owsQuery"
                            style-by="assessor"
                            :filterable="false"
                            :drawable="is_internal || !leaseLicence"
                            :editable="true"
                            :navbar-buttons-disabled="navbarButtonsDisabled"
                            :saving-features="savingInProgress"
                            level="internal"
                            :map-info-text="
                                is_internal
                                    ? ''
                                    : leaseLicence
                                      ? 'You cannot change the area anymore at this stage.</br>Display layers to check attributes of polygons with the <b>info</b> tool.</br>You can <b>save</b> the proposal and continue at a later time.'
                                      : 'Use the <b>draw</b> tool to draw the area of the proposal you are interested in on the map.</br>Display layers to check attributes of polygons with the <b>info</b> tool.</br>You can <b>save</b> the proposal and continue at a later time.'
                            "
                            @validate-feature="validateFeature.bind(this)()"
                            @refresh-from-response="refreshFromResponse"
                            @finished-drawing="$emit('finished-drawing')"
                            @deleted-features="$emit('deleted-features')"
                        />
                    </FormSection>

	    <!--
        <div class="">
            <ul id="pills-tab" class="nav nav-pills" role="tablist">
                <li class="nav-item" role="presentation">
                    <button
                        id="pills-map-tab"
                        class="nav-link"
                        data-bs-toggle="pill"
                        data-bs-target="#pills-map"
                        role="tab"
                        aria-controls="pills-map"
                        aria-selected="false"
                        @click="toggleComponentMapOn"
                    >
                        <template v-if="is_external"
                            ><span v-if="!is_internal && leaseLicence">
                                View Land Area (Map)</span
                            >
                            <span v-else> Indicate Land Area (Map)</span>
                        </template>
                        <template v-else>Map</template>
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button
                        id="pills-details-tab"
                        class="nav-link"
                        data-bs-toggle="pill"
                        data-bs-target="#pills-details"
                        role="tab"
                        aria-controls="pills-details"
                        aria-selected="false"
                    >
                        <template v-if="is_external"
                            >Provide Further Details
                        </template>
                        <template v-else>Details</template>
                    </button>
                </li>
            </ul>
                <div
                    id="pills-map"
                    class="tab-pane fade"
                    role="tabpanel"
                    aria-labelledby="pills-map-tab"
                >
                    <FormSection
                        :form-collapse="false"
                        label="Map"
                        index="proposal_geometry"
                    >
                        <slot name="slot_map_assessment_comments"></slot>
                        <MapComponent
                            ref="component_map"
                            :key="componentMapKey"
                            :context="proposal"
                            :proposal-ids="[-1]"
                            :feature-collection="geometriesToFeatureCollection"
                            :ows-query="owsQuery"
                            style-by="assessor"
                            :filterable="false"
                            :drawable="is_internal || !leaseLicence"
                            :editable="true"
                            :navbar-buttons-disabled="navbarButtonsDisabled"
                            :saving-features="savingInProgress"
                            level="internal"
                            :map-info-text="
                                is_internal
                                    ? ''
                                    : leaseLicence
                                      ? 'You cannot change the area anymore at this stage.</br>Display layers to check attributes of polygons with the <b>info</b> tool.</br>You can <b>save</b> the proposal and continue at a later time.'
                                      : 'Use the <b>draw</b> tool to draw the area of the proposal you are interested in on the map.</br>Display layers to check attributes of polygons with the <b>info</b> tool.</br>You can <b>save</b> the proposal and continue at a later time.'
                            "
                            @validate-feature="validateFeature.bind(this)()"
                            @refresh-from-response="refreshFromResponse"
                            @finished-drawing="$emit('finished-drawing')"
                            @deleted-features="$emit('deleted-features')"
                        />
                    </FormSection>
                </div>
                <div
                    id="pills-details"
                    class="tab-pane fade"
                    role="tabpanel"
                    aria-labelledby="pills-details-tab"
                >
                </div>
        </div>
	    -->
    </div>
</template>

<script>
import Applicant from '@/components/common/applicant.vue';
import OrganisationApplicant from '@/components/common/organisation_applicant.vue';
import FormSection from '@/components/forms/section_toggle.vue';
import FileField from '@/components/forms/filefield_immediate.vue';
import MapComponent from '@/components/common/component_map.vue';
import RegistrationOfInterest from './form_registration_of_interest.vue';
import LeaseLicence from './form_lease_licence.vue';
import Multiselect from 'vue-multiselect';
import GisDataDetails from '@/components/common/gis_data_details.vue';
import { v4 as uuid } from 'uuid';

import { api_endpoints, helpers, utils } from '@/utils/hooks';
import {
    owsQuery,
    validateFeature,
} from '@/components/common/map_functions.js';
/*
import Confirmation from '@/components/common/confirmation.vue'
*/
export default {
    name: 'ProposalForm',
    components: {
//        RegistrationOfInterest,
//        LeaseLicence,
//        Applicant,
//        OrganisationApplicant,
        FormSection,
//        FileField,
        MapComponent,
//        Multiselect,
//        GisDataDetails,
    },
    props: {
//        show_related_items_tab: {
//            type: Boolean,
//            default: false,
//        },
        proposal: {
            type: Object,
            required: true,
        },
        show_application_title: {
            type: Boolean,
            default: true,
        },
        submitterId: {
            type: Number,
            default: null,
        },
        canEditActivities: {
            type: Boolean,
            default: true,
        },
        is_external: {
            type: Boolean,
            default: false,
        },
        is_internal: {
            type: Boolean,
            default: false,
        },
        can_assess: {
            type: Boolean,
            default: false,
        },
        is_referee: {
            type: Boolean,
            default: false,
        },
        hasReferralMode: {
            type: Boolean,
            default: false,
        },
        hasAssessorMode: {
            type: Boolean,
            default: false,
        },
        referral: {
            type: Object,
            required: false,
            default: null,
        },
        readonly: {
            type: Boolean,
            default: true,
        },
        registrationOfInterest: {
            type: Boolean,
            default: true,
        },
        leaseLicence: {
            type: Boolean,
            default: true,
        },
        navbarButtonsDisabled: {
            type: Boolean,
            default: false,
        },
        savingInProgress: {
            type: Boolean,
            default: false,
        },
    },
    emits: [
        'refreshFromResponse',
        'formMounted',
        'update:GisData',
        'finished-drawing',
        'deleted-features',
    ],
    data: function () {
        return {
            can_modify: true,
            show_col_status_when_submitted: true,

            values: null,
            profile: {},
            uuid: null,
            keep_current_vessel: true,
            showPaymentTab: false,
            detailsText: null,
            defaultLocality: {
                id: null,
                proposal_id: this.proposal.id,
                district: null,
                lga: '',
            },
            districts: null,
            lgas: null,
            groups: [],
            api_endpoints: api_endpoints,

            loadingGroups: false,
            owsQuery: owsQuery,
            validateFeature: validateFeature,
        };
    },
    computed: {
        debug: function () {
            if (this.$route.query.debug) {
                return this.$route.query.debug === 'true';
            }
            return false;
        },
        proposalId: function () {
	    console.log('form.vue ' + this.proposal);
            return this.proposal ? this.proposal.id : null;
        },
        deedPollDocumentUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_deed_poll_document/'
            );
        },
        supportingDocumentsUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.proposal,
                this.proposal.id + '/process_deed_poll_document/'
            );
        },
        profileVar: function () {
            if (this.is_external) {
                return this.profile;
            } else if (this.proposal) {
                return this.proposal.submitter;
            } else {
                return null;
            }
        },
        applicantType: function () {
            if (this.proposal) {
                return this.proposal.applicant_type;
            } else {
                return null;
            }
        },
        applicationTypeText: function () {
            let text = '';
            if (this.proposal) {
                text = this.proposal.application_type.name_display;
            }
            return text;
        },
        proposalTypeText: function () {
            let text = '';
            if (this.proposal) {
                text = this.proposal.proposal_type.description;
            }
            return text;
        },
        gis_data: function () {
            if (this.proposal) {
                return {
                    regions: this.proposal.regions,
                    districts: this.proposal.districts,
                    lgas: this.proposal.lgas,
                    names: this.proposal.names,
                    categories: this.proposal.categories,
                    identifiers: this.proposal.identifiers,
                    vestings: this.proposal.vestings,
                    acts: this.proposal.acts,
                    tenures: this.proposal.tenures,
                };
            } else {
                return {};
            }
        },
        componentMapKey: function () {
            return `component-map-${this.uuid}`;
        },
        /**
         * Returns proposal geometries as a FeatureCollection
         */
        geometriesToFeatureCollection: function () {
            let vm = this;

            let featureCollection = {
                type: 'FeatureCollection',
                features: [],
            };

            let proposalgeometries = {
                ...(vm.proposal.proposalgeometry ? vm.proposal.proposalgeometry : {}),
            };

//            let proposalgeometries = {
//                ...(proposal_geometry ? proposal_geometry : {}),
//            };
            console.log('JM1: ' + JSON.stringify(proposalgeometries))

            //return featureCollection; // TODO - JM

            if (Object.keys(proposalgeometries).length !== 0) {
                for (let feature of proposalgeometries['features']) {
                    feature['properties']['source'] = 'Proposal';
                    let model = {
                        id: vm.proposal.id,
                        details_url: vm.proposal.details_url,
                        application_type_name_display:
                            vm.proposal.application_type.name_display,
                        lodgement_number: vm.proposal.lodgement_number,
                        lodgement_date_display: moment(
                            vm.proposal.lodgement_date
                        ).format('DD/MM/YYYY'),
                        processing_status_display: vm.proposal.processing_status,
                    };

                    feature['model'] = model;
                    featureCollection['features'].push(feature);
                }
                console.log('featureCollection: ' + featureCollection)
            } else {
                console.log('WARN: Shapefile featureCollection is empty')
            }
            return featureCollection;
        },
        geometriesToFeatureCollection2: function () {
            let vm = this;

            let featureCollection = {
                type: 'FeatureCollection',
                features: [],
            };

            let proposalgeometries = {
                ...(vm.proposal.proposalgeometry_hist ? vm.proposal.proposalgeometry_hist : {}),
            };

//            let proposalgeometries = {
//                ...(proposal_geometry ? proposal_geometry : {}),
//            };
            console.log('JM1: ' + JSON.stringify(proposalgeometries))

            //return featureCollection; // TODO - JM

            if (Object.keys(proposalgeometries).length !== 0) {
                for (let feature of proposalgeometries['features']) {
                    feature['properties']['source'] = 'Proposal';
                    let model = {
                        id: vm.proposal.id,
                        details_url: vm.proposal.details_url,
                        application_type_name_display:
                            vm.proposal.application_type.name_display,
                        lodgement_number: vm.proposal.lodgement_number,
                        lodgement_date_display: moment(
                            vm.proposal.lodgement_date
                        ).format('DD/MM/YYYY'),
                        processing_status_display: vm.proposal.processing_status,
                    };

                    feature['model'] = model;
                    featureCollection['features'].push(feature);
                }
                console.log('featureCollection: ' + featureCollection)
            } else {
                console.log('WARN: Shapefile featureCollection is empty')
            }
            return featureCollection;
        }, 
        geometriesToFeatureCollection3: function () {
            let vm = this;

            let featureCollection = {
                type: 'FeatureCollection',
                features: [],
            };

            let proposalgeometries = {
                ...(vm.proposal.proposalgeometry_processed ? vm.proposal.proposalgeometry_processed : {}),
            };

//            let proposalgeometries = {
//                ...(proposal_geometry ? proposal_geometry : {}),
//            };
            console.log('JM1: ' + JSON.stringify(proposalgeometries))

            //return featureCollection; // TODO - JM

            if (Object.keys(proposalgeometries).length !== 0) {
                for (let feature of proposalgeometries['features']) {
                    feature['properties']['source'] = 'Proposal';
                    let model = {
                        id: vm.proposal.id,
                        details_url: vm.proposal.details_url,
                        application_type_name_display:
                            vm.proposal.application_type.name_display,
                        lodgement_number: vm.proposal.lodgement_number,
                        lodgement_date_display: moment(
                            vm.proposal.lodgement_date
                        ).format('DD/MM/YYYY'),
                        processing_status_display: vm.proposal.processing_status,
                    };

                    feature['model'] = model;
                    featureCollection['features'].push(feature);
                }
                console.log('featureCollection: ' + featureCollection)
            } else {
                console.log('WARN: Shapefile featureCollection is empty')
            }
            return featureCollection;
        },
       geometriesToFeatureCollection2: function () {
            let vm = this;

            let featureCollection = {
                type: 'FeatureCollection',
                features: [],
            };

            let proposalgeometries = {
                ...(vm.proposal.proposalgeometry_hist ? vm.proposal.proposalgeometry_hist : {}),
            };

//            let proposalgeometries = {
//                ...(proposal_geometry ? proposal_geometry : {}),
//            };
            console.log('JM1: ' + JSON.stringify(proposalgeometries))

            //return featureCollection; // TODO - JM

            if (Object.keys(proposalgeometries).length !== 0) {
                for (let feature of proposalgeometries['features']) {
                    feature['properties']['source'] = 'Proposal';
                    let model = {
                        id: vm.proposal.id,
                        details_url: vm.proposal.details_url,
                        application_type_name_display:
                            vm.proposal.application_type.name_display,
                        lodgement_number: vm.proposal.lodgement_number,
                        lodgement_date_display: moment(
                            vm.proposal.lodgement_date
                        ).format('DD/MM/YYYY'),
                        processing_status_display: vm.proposal.processing_status,
                    };

                    feature['model'] = model;
                    featureCollection['features'].push(feature);
                }
                console.log('featureCollection: ' + featureCollection)
            } else {
                console.log('WARN: Shapefile featureCollection is empty')
            }
            return featureCollection;
        },

    },
    created: function () {
//        if (this.is_internal || this.is_referee) {
//            utils.fetchKeyValueLookup(api_endpoints.groups, '').then((data) => {
//                this.groups = data;
//            });
//        }
        this.uuid = uuid();
    },
    mounted: function () {
        this.$emit('formMounted');
        console.log('form.vue ' + this.proposal.lodgement_number)
    },
    methods: {
        incrementComponentMapKey: function () {
            this.uuid = uuid();
        },
        toggleComponentMapOn: function () {
            this.incrementComponentMapKey()
            this.componentMapOn = true;
            this.$nextTick(() => {
                this.$refs.component_map.forceToRefreshMap();
            });
        },
        refreshFromResponse: function (data) {
            this.$emit('refreshFromResponse', data);
        },
    },
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
