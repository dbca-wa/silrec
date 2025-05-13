<template lang="html">
    <div class="">
        <div v-if="debug">components/form.vue</div>
        <div
            v-if="proposal && show_application_title"
            id="scrollspy-heading"
            class=""
        >
            <h3>
                {{ applicationTypeText }} - {{ proposalTypeText }}:
                {{ proposal.lodgement_number }}
            </h3>
        </div>

        <div class="">
            <ul id="pills-tab" class="nav nav-pills" role="tablist">
                <li class="nav-item mr-1" role="presentation">
                    <button
                        id="pills-applicant-tab"
                        class="nav-link active"
                        data-bs-toggle="pill"
                        data-bs-target="#pills-applicant"
                        role="tab"
                        aria-controls="pills-applicant"
                        aria-selected="true"
                    >
                        <template v-if="is_external"
                            >Provide Proponent Information</template
                        >
                        <template v-else>Proponent</template>
                    </button>
                </li>
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
                <template v-if="show_related_items_tab">
                    <li class="nav-item" role="presentation">
                        <button
                            id="pills-related-items-tab"
                            class="nav-link"
                            data-bs-toggle="pill"
                            data-bs-target="#pills-related-items"
                            role="tab"
                            aria-controls="pills-related-items"
                            aria-selected="false"
                        >
                            Related Items
                        </button>
                    </li>
                </template>
            </ul>
            <div id="pills-tabContent" class="tab-content">
                <div
                    id="pills-applicant"
                    class="tab-pane fade show active"
                    role="tabpanel"
                    aria-labelledby="pills-applicant-tab"
                >
                    <Applicant
                        v-if="'individual' == proposal.applicant_type"
                        id="proposalStartApplicant"
                        :proposal-id="proposal.id"
                        :proposal-applicant="proposal.proposal_applicant"
                        :readonly="readonly"
                        :collapse-form-sections="false"
                    />
                    <OrganisationApplicant
                        v-else
                        :org="proposal.applicant_obj"
                        :is-internal="is_internal"
                    />
                </div>
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
                    <RegistrationOfInterest
                        v-if="registrationOfInterest"
                        ref="registration_of_interest"
                        :proposal="proposal"
                        :readonly="readonly"
                    >
                        <template #slot_proposal_details_assessment_comments>
                            <slot
                                name="slot_proposal_details_assessment_comments"
                            ></slot>
                        </template>

                        <template #slot_proposal_impact_assessment_comments>
                            <slot
                                name="slot_proposal_impact_assessment_comments"
                            ></slot>
                        </template>
                    </RegistrationOfInterest>

                    <LeaseLicence
                        v-if="leaseLicence"
                        ref="lease_licence"
                        :proposal="proposal"
                        :is_internal="is_internal"
                        :readonly="readonly"
                    >
                        <template
                            #slot_proposal_tourism_details_assessment_comments
                        >
                            <slot
                                name="slot_proposal_tourism_details_assessment_comments"
                            ></slot>
                        </template>

                        <template
                            #slot_proposal_general_details_assessment_comments
                        >
                            <slot
                                name="slot_proposal_general_details_assessment_comments"
                            ></slot>
                        </template>
                    </LeaseLicence>

                    <FormSection
                        v-if="is_internal"
                        label="Geospatial Data"
                        index="other_section"
                    >
                        <slot name="slot_gis_data_assessment_comments"></slot>
                        <GisDataDetails
                            :selected-data="gis_data"
                            :readonly="is_external && leaseLicence"
                            @update:selected-data="
                                (property, value) => {
                                    $emit('update:GisData', property, value);
                                }
                            "
                        />
                    </FormSection>

                    <FormSection
                        v-if="is_internal || proposal.site_name"
                        label="Categorisation"
                        index="categorisation"
                    >
                        <slot
                            name="slot_categorisation_assessment_comments"
                        ></slot>

                        <div
                            v-if="is_internal || proposal.site_name"
                            class="row mb-3"
                        >
                            <div class="col-sm-3">
                                <label class="col-form-label">Site Name</label>
                            </div>
                            <div class="col-sm-9">
                                <input
                                    id="site_name"
                                    ref="site_name"
                                    v-model="proposal.site_name"
                                    class="form-control"
                                    type="text"
                                    name="site_name"
                                    :disabled="!can_assess"
                                />
                            </div>
                        </div>
                        <div v-if="is_internal || is_referee" class="row mb-3">
                            <div class="col-sm-3">
                                <label class="col-form-label">Groups</label>
                            </div>
                            <div class="col-sm-9">
                                <Multiselect
                                    id="groups"
                                    ref="groups"
                                    v-model="proposal.groups"
                                    label="name"
                                    track-by="id"
                                    placeholder="Select Groups"
                                    :options="groups"
                                    :hide-selected="true"
                                    :multiple="true"
                                    :searchable="true"
                                    :loading="loadingGroups"
                                    :disabled="!can_assess"
                                />
                            </div>
                        </div>
                    </FormSection>

                    <FormSection
                        label="Deed Poll"
                        :subtitle="leaseLicence ? 'Mandatory' : 'Optional'"
                        index="deed_poll"
                    >
                        <slot name="slot_deed_poll_assessment_comments"></slot>
                        <div class="col-sm-12 section-style">
                            <BootstrapAlert
                                :type="leaseLicence ? 'warning' : 'primary'"
                                :icon="
                                    leaseLicence
                                        ? 'exclamation-triangle-fill'
                                        : 'info-fill'
                                "
                            >
                                <ul class="list-group">
                                    <li class="list-group-item">
                                        <template v-if="leaseLicence">
                                            It is a requirement of all
                                            proponents
                                        </template>
                                        <template v-else>You may wish</template>
                                        to sign a deed poll to release and
                                        indemnify the State of Western
                                        Australia.
                                    </li>
                                    <li class="list-group-item">
                                        The deed poll must be signed, dated and
                                        have a witness signature.
                                    </li>
                                    <li class="list-group-item">
                                        Once signed, dated and witnessed, please
                                        scan and attach the deed poll below.
                                    </li>
                                </ul>
                            </BootstrapAlert>

                            <BootstrapAlert type="danger">
                                <span class="fw-bold">Please note:</span>
                                electronic or digital signatures cannot be
                                accepted.
                            </BootstrapAlert>

                            <label for="deed_poll_document" class="mb-3"
                                >Deed poll:</label
                            >
                            <FileField
                                id="deed_poll_document"
                                ref="deed_poll_document"
                                :readonly="readonly"
                                name="deed_poll_document"
                                :is-repeatable="true"
                                :document-action-url="deedPollDocumentUrl"
                                :replace_button_by_text="true"
                            />
                        </div>
                    </FormSection>

                    <template
                        v-if="
                            is_internal ||
                            proposal.additional_document_types.length > 0
                        "
                    >
                        <FormSection
                            label="Additional Documents"
                            index="additional_documents"
                        >
                            <slot
                                name="slot_additional_documents_assessment_comments"
                            ></slot>
                        </FormSection>
                    </template>
                </div>

                <!-- Related Items tab is shown on the internal proposal page -->
                <template v-if="show_related_items_tab">
                    <div
                        id="pills-related-items"
                        class="tab-pane fade"
                        role="tabpanel"
                        aria-labelledby="pills-related-items-tab"
                    >
                        <slot name="slot_section_related_items"></slot>
                    </div>
                </template>
            </div>
        </div>
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
        RegistrationOfInterest,
        LeaseLicence,
        Applicant,
        OrganisationApplicant,
        FormSection,
        FileField,
        MapComponent,
        Multiselect,
        GisDataDetails,
    },
    props: {
        show_related_items_tab: {
            type: Boolean,
            default: false,
        },
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

            /*
            componentMapOn: false,
            */
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
                ...vm.proposal.proposalgeometry,
            };

            for (let feature of proposalgeometries['features']) {
                feature['properties']['source'] = 'registration_of_interest';
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

            return featureCollection;
        },
    },
    created: function () {
        if (this.is_internal || this.is_referee) {
            utils.fetchKeyValueLookup(api_endpoints.groups, '').then((data) => {
                this.groups = data;
            });
        }
        this.uuid = uuid();
    },
    mounted: function () {
        this.$emit('formMounted');
    },
    methods: {
        incrementComponentMapKey: function () {
            this.uuid = uuid();
        },
        toggleComponentMapOn: function () {
            //this.incrementComponentMapKey()
            //this.componentMapOn = true;
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
