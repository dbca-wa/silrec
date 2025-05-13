<template lang="html">
    <div v-if="competitive_process" class="container">
        <div class="row">
            <h3>
                Competitive Process: {{ competitive_process.lodgement_number }}
            </h3>
            <div class="col-md-3">
                <CommsLogs
                    :comms_url="comms_url"
                    :logs_url="logs_url"
                    :comms_add_url="comms_add_url"
                    :disable_add_entry="false"
                />
                <Workflow
                    ref="workflow"
                    :key="cp_id"
                    :competitive-process="competitive_process"
                    :processing="processing"
                    :discarded="discarded"
                    :declined="declined"
                    :finalised="finalised"
                    :can-action="canAction"
                    :can-unlock="canUnlock"
                    :can-assess="canAssess"
                    :can_user_edit="competitive_process.can_user_edit"
                    class="mt-2"
                    @assign-request-user="assignRequestUser"
                    @assign-to="assignTo"
                    @issue-complete="issueComplete"
                    @issue-discard="issueDiscard"
                    @issue-unlock="issueUnlock"
                />
            </div>
            <div class="col-md-9">
                <ul id="pills-tab" class="nav nav-pills" role="tablist">
                    <li class="nav-item mr-1" role="presentation">
                        <button
                            id="pills-parties-tab"
                            class="nav-link active"
                            data-bs-toggle="pill"
                            data-bs-target="#pills-parties"
                            role="tab"
                            aria-controls="pills-parties"
                            aria-selected="true"
                        >
                            Parties
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
                            @click="mapTabClicked"
                        >
                            Map
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
                            Details
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button
                            id="pills-outcome-tab"
                            class="nav-link"
                            data-bs-toggle="pill"
                            data-bs-target="#pills-outcome"
                            role="tab"
                            aria-controls="pills-outcome"
                            aria-selected="false"
                            @click="outcomeTabClicked"
                        >
                            Outcome
                        </button>
                    </li>
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
                </ul>
                <div id="pills-tabContent" class="tab-content">
                    <div
                        id="pills-parties"
                        class="tab-pane fade show active"
                        role="tabpanel"
                        aria-labelledby="pills-parties-tab"
                    >
                        <FormSection
                            :form-collapse="false"
                            label="Parties"
                            index="parties"
                        >
                            <TableParties
                                ref="competitive_process_parties"
                                :key="cp_id"
                                level="internal"
                                :competitive-process-parties="
                                    competitive_process.competitive_process_parties
                                "
                                :competitive-process-id="competitive_process.id"
                                :accessing-user="
                                    competitive_process.accessing_user
                                "
                                :processing="processing"
                                :discarded="discarded"
                                :declined="declined"
                                :completed="completed"
                                :finalised="finalised"
                                :readonly="readonly"
                                @add-detail="addDetail"
                                @update-party-date="updatePartyDate"
                                @add-party="addParty"
                            />
                        </FormSection>
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
                            index="map"
                        >
                            <!--
                                validate-feature: event callback function to execute code to validate a feature. Needs to call `finishDrawing` on the map component to complete the drawing
                             -->
                            <MapComponent
                                ref="component_map"
                                :key="componentMapKey"
                                :context="competitive_process"
                                :proposal-ids="[-1]"
                                :ows-query="owsQuery"
                                :feature-collection="
                                    geometriesToFeatureCollection
                                "
                                style-by="assessor"
                                :filterable="false"
                                :drawable="!readonly"
                                :editable="!readonly"
                                :navbar-buttons-disabled="processing"
                                :saving-features="processing"
                                level="internal"
                                @validate-feature="validateFeature.bind(this)()"
                                @refresh-from-response="refreshFromResponse"
                                @finished-drawing="onFinishedDrawing"
                                @deleted-features="onFinishedDrawing"
                            />
                        </FormSection>
                    </div>
                    <div
                        id="pills-details"
                        class="tab-pane fade"
                        role="tabpanel"
                        aria-labelledby="pills-details-tab"
                    >
                        <FormSection
                            :form-collapse="false"
                            label="Details"
                            index="details"
                        >
                            <FormSection
                                :form-collapse="false"
                                label="Categorisation"
                                index="categorisation"
                            >
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="col-form-label"
                                            >Site Name</label
                                        >
                                    </div>
                                    <div class="col-sm-9">
                                        <input
                                            id="site_name"
                                            v-model="
                                                competitive_process.site_name
                                            "
                                            class="form-control"
                                            type="text"
                                            name="site_name"
                                            :readonly="readonly"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="col-form-label"
                                            >Site Comments</label
                                        >
                                    </div>
                                    <div class="col-sm-9">
                                        <textarea
                                            id="site_comments"
                                            v-model="
                                                competitive_process.site_comments
                                            "
                                            class="form-control"
                                            type="text"
                                            name="site_comments"
                                            style="height: 200px"
                                            :readonly="readonly"
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-sm-3">
                                        <label class="col-form-label"
                                            >Groups</label
                                        >
                                    </div>
                                    <div class="col-sm-9">
                                        <Multiselect
                                            v-model="competitive_process.groups"
                                            label="name"
                                            track-by="id"
                                            placeholder="Select Groups"
                                            :options="groups"
                                            :hide-selected="true"
                                            :multiple="true"
                                            :searchable="true"
                                            :loading="loadingGroups"
                                            :disabled="readonly"
                                        />
                                    </div>
                                </div>
                            </FormSection>
                            <FormSection
                                :form-collapse="false"
                                label="Geospatial Data"
                                index="geospatial-data"
                            >
                                <GISDataDetails
                                    v-if="competitive_process.gis_data"
                                    :selected-data="
                                        competitive_process.gis_data
                                    "
                                    :searchable="true"
                                    :readonly="readonly"
                                    @update:selected-data="updateGISData"
                                />
                            </FormSection>
                        </FormSection>
                    </div>
                    <div
                        id="pills-outcome"
                        class="tab-pane fade"
                        role="tabpanel"
                        aria-labelledby="pills-outcome-tab"
                    >
                        <FormSection
                            :form-collapse="false"
                            label="Outcome"
                            index="outcome"
                        >
                            <div class="row mb-2">
                                <div class="col-sm-3">
                                    <label
                                        for="competitive_process_winner"
                                        class="control-label"
                                        >Winner</label
                                    >
                                </div>
                                <div class="col-sm-4">
                                    <select
                                        id="competitive_process_winner"
                                        ref="select_winner"
                                        v-model="competitive_process.winner_id"
                                        class="form-control"
                                        :disabled="elementDisabled"
                                    >
                                        <option></option>
                                        <option
                                            v-for="party in possibleWinner"
                                            :key="party.id"
                                            :value="party.id"
                                        >
                                            <template v-if="party.id != 0">
                                                <template
                                                    v-if="party.is_person"
                                                >
                                                    {{ party.person.fullname }}
                                                </template>
                                                <template
                                                    v-else-if="
                                                        party.is_organisation
                                                    "
                                                >
                                                    {{
                                                        party.organisation
                                                            .ledger_organisation_name
                                                    }}
                                                </template>
                                            </template>
                                        </option>
                                    </select>
                                </div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-sm-3">
                                    <label
                                        :for="
                                            hasWinner
                                                ? 'competitive-process-outcome-winner-details'
                                                : 'competitive-process-outcome-no-winner-details'
                                        "
                                        class="control-label"
                                        >Details</label
                                    >
                                </div>
                                <div class="col-sm-9">
                                    <RichText
                                        :id="
                                            hasWinner
                                                ? 'competitive-process-outcome-winner-details'
                                                : 'competitive-process-outcome-no-winner-details'
                                        "
                                        ref="details"
                                        :key="cp_id"
                                        :proposal-data="outcomeDetails"
                                        placeholder-text="Add some details here"
                                        :readonly="elementDisabled"
                                        @text-changed="detailsTextChanged"
                                    />
                                </div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-sm-3">
                                    <label
                                        for="competitive_process_documents"
                                        class="control-label"
                                        >Documents</label
                                    >
                                </div>
                                <div class="col-sm-9">
                                    <FileField
                                        id="competitive_process_document"
                                        ref="competitive_process_document"
                                        :key="cp_id"
                                        :readonly="elementDisabled"
                                        name="competitive_process_document"
                                        :is-repeatable="true"
                                        :document-action-url="
                                            competitiveProcessDocumentUrl
                                        "
                                        :replace_button_by_text="true"
                                    />
                                </div>
                            </div>
                        </FormSection>
                    </div>
                    <div
                        id="pills-related-items"
                        class="tab-pane fade"
                        role="tabpanel"
                        aria-labelledby="pills-related-items-tab"
                    >
                        <FormSection
                            :form-collapse="false"
                            label="Related Items"
                            index="related_items"
                        >
                            <TableRelatedItems
                                :key="cp_id"
                                :ajax-url="related_items_ajax_url"
                            />
                        </FormSection>
                    </div>
                </div>
            </div>
        </div>
        <div v-if="displaySaveBtns" class="navbar fixed-bottom bg-navbar me-1">
            <div class="container">
                <div class="col-md-12 text-end">
                    <button
                        v-if="processing"
                        type="button"
                        class="btn btn-primary me-1"
                        disabled
                    >
                        Save and Continue&nbsp;<i
                            class="fa-solid fa-spinner fa-spin"
                        ></i>
                    </button>
                    <input
                        v-else
                        type="button"
                        class="btn btn-primary me-1"
                        value="Save and Continue"
                        :disabled="disableSaveAndContinueBtn"
                        @click.prevent="save_and_continue()"
                    />

                    <button
                        v-if="processing"
                        type="button"
                        class="btn btn-primary me-1"
                        disabled
                    >
                        Save and Exit&nbsp;<i
                            class="fa-solid fa-spinner fa-spin"
                        ></i>
                    </button>
                    <input
                        v-else
                        type="button"
                        class="btn btn-primary me-1"
                        value="Save and Exit"
                        :disabled="disableSaveAndExitBtn"
                        @click.prevent="save_and_exit()"
                    />
                </div>
            </div>
        </div>
    </div>
    <BootstrapSpinner v-else :loading="true" class="text-primary" />
</template>

<script>
import { api_endpoints, helpers, constants, utils } from '@/utils/hooks.js';
import { v4 as uuid } from 'uuid';
import CommsLogs from '@common-utils/comms_logs.vue';
import Workflow from '@common-utils/workflow_competitive_process.vue';
import FormSection from '@/components/forms/section_toggle.vue';
import TableParties from '@common-utils/table_parties.vue';
import MapComponent from '@/components/common/component_map.vue';
import RichText from '@/components/forms/RichText.vue';
import FileField from '@/components/forms/filefield_immediate.vue';
import TableRelatedItems from '@/components/common/table_related_items.vue';
import GISDataDetails from '@/components/common/gis_data_details.vue';
import Multiselect from 'vue-multiselect';

import {
    owsQuery,
    validateFeature,
} from '@/components/common/map_functions.js';

export default {
    name: 'CompetitiveProcess',
    components: {
        CommsLogs,
        GISDataDetails,
        Workflow,
        TableParties,
        FormSection,
        MapComponent,
        Multiselect,
        RichText,
        FileField,
        TableRelatedItems,
    },
    data: function () {
        let vm = this;
        return {
            cp_id: uuid(), // competitive process id
            competitive_process: null,
            can_modify: true,
            show_col_status_when_submitted: true,
            componentMapKey: 0,
            // For Comms Log
            comms_url: helpers.add_endpoint_json(
                api_endpoints.competitive_process,
                vm.$route.params.competitive_process_id + '/comms_log'
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.competitive_process,
                vm.$route.params.competitive_process_id + '/add_comms_log'
            ),
            logs_url: helpers.add_endpoint_json(
                api_endpoints.competitive_process,
                vm.$route.params.competitive_process_id + '/action_log'
            ),
            loadingGroups: false,
            groups: [],
            processing: false,
            owsQuery: owsQuery,
            validateFeature: validateFeature,
            detailsTexts: {},
        };
    },
    computed: {
        disableSaveAndContinueBtn: function () {
            if (this.processing) return true;
            return false;
        },
        disableSaveAndExitBtn: function () {
            if (this.processing) return true;
            return false;
        },
        hasWinner: function () {
            /** Returns whether this CP has a winner */

            return (
                ![null, ''].includes(this.competitive_process.winner_id) &&
                !isNaN(this.competitive_process.winner_id)
            );
        },
        winnerApplicationApproved: function () {
            /** Returns whether the winner's lease/license Proposal has been approved
             *  or false when the winner is different from the originating proposal's
             *  applicant.
             */

            let winner_party_id = this.competitive_process.winner_id;
            let winner_party = this.partyById(winner_party_id);
            // The ID of the winning party's applicant
            let winner_applicant_id;
            if (winner_party) {
                winner_applicant_id = winner_party.is_person
                    ? winner_party.person_id
                    : winner_party.is_organisation
                      ? winner_party.organisation_id
                      : -1;
            } else {
                console.warn(
                    `No related party found for winner ID ${winner_party_id}.`
                );
                return false;
            }

            let generated_proposals =
                this.competitive_process.generated_proposal;
            if (!generated_proposals) {
                return false;
            }

            // The winner's lease/license Applications
            let winner_applications = generated_proposals.filter(
                (proposal) => proposal.applicant_obj.id == winner_applicant_id
            );
            if (!winner_applications || winner_applications.length == 0) {
                return false;
            }

            // Statuses that indicate an Proposal has been approved
            let status_approved = [
                constants.PROPOSAL_STATUS.APPROVED_APPLICATION.TEXT,
                constants.PROPOSAL_STATUS.APPROVED_COMPETITIVE_PROCESS.TEXT,
                constants.PROPOSAL_STATUS.APPROVED_EDITING_INVOICING.TEXT,
                constants.PROPOSAL_STATUS.DISCARDED.TEXT,
            ];

            // The winner's lease/license Proposals that have not been approved
            let open_applications = winner_applications.filter(
                (proposal) =>
                    !status_approved.includes(proposal.processing_status)
            );

            if (open_applications.length == 0) {
                return true;
            } else if (open_applications.length == 1) {
                return false;
            } else {
                let winner_name = winner_party.is_person
                    ? winner_party.person.fullname
                    : winner_party.is_organisation
                      ? winner_party.organisation.trading_name
                      : 'Unknown';
                console.warn(
                    `Multiple open Applications found for winner ID ${winner_party_id}. (${winner_name})`
                );
                return false;
            }
        },
        finalised: function () {
            /** Returns whether this competitive process is finalized.
             *  A CP is finalized when it is completed or discarded,
             *  when a winner has been selected and when the winner's license Proposal has
             *  been approved.
             *  A finalized CP can not be unlocked anymore.
             */

            return (
                (this.completed || this.discarded) &&
                this.hasWinner &&
                this.winnerApplicationApproved
            );
        },
        canAction: function () {
            return this.competitive_process.can_accessing_user_process;
        },
        canUnlock: function () {
            return this.competitive_process.can_accessing_user_unlock;
        },
        canAssess: function () {
            return this.competitive_process.can_accessing_user_view;
        },
        related_items_ajax_url: function () {
            return (
                '/api/competitive_process/' +
                this.competitive_process.id +
                '/related_items/'
            );
        },
        competitiveProcessDocumentUrl: function () {
            return helpers.add_endpoint_join(
                api_endpoints.competitive_process,
                '/' +
                    this.competitive_process.id +
                    '/process_competitive_process_document/'
            );
        },
        readonly: function () {
            return (
                this.competitive_process?.assigned_officer?.id !==
                this.competitive_process?.accessing_user?.id
            );
        },
        displaySaveBtns: function () {
            return true;
        },
        competitive_process_form_url: function () {
            return helpers.add_endpoint_json(
                api_endpoints.competitive_process,
                this.competitive_process.id
            );
        },
        competitive_process_discard_url: function () {
            return (
                '/api/competitive_process/' +
                this.competitive_process.id +
                '/discard/'
            );
        },
        competitive_process_complete_url: function () {
            return (
                '/api/competitive_process/' +
                this.competitive_process.id +
                '/complete/'
            );
        },
        competitive_process_unlock_url: function () {
            return (
                '/api/competitive_process/' +
                this.competitive_process.id +
                '/unlock/'
            );
        },
        discarded: function () {
            return (
                this.competitive_process &&
                this.competitive_process.status_id ===
                    constants.COMPETITIVE_PROCESS_STATUS.DISCARDED.ID
            );
        },
        declined: function () {
            return (
                this.competitive_process &&
                this.competitive_process.status_id ===
                    constants.COMPETITIVE_PROCESS_STATUS.COMPLETED_DECLINED.ID
            );
        },
        completed: function () {
            /** Returns whether this CP is completed */

            return (
                this.competitive_process &&
                [
                    constants.COMPETITIVE_PROCESS_STATUS.COMPLETED_APPLICATION
                        .ID,
                    constants.COMPETITIVE_PROCESS_STATUS.COMPLETED_DECLINED.ID,
                ].includes(this.competitive_process.status_id)
            );
        },
        elementDisabled: function () {
            // Returns whether an element is disabled
            // True while processing (saving), when discarded, or when finalized
            return (
                this.readonly ||
                this.processing ||
                this.discarded ||
                this.finalised ||
                this.declined ||
                this.completed
            );
        },
        possibleWinner: function () {
            // Returns list of possible winners without newly added parties
            return this.competitive_process.competitive_process_parties.filter(
                (party) => party.id > 0 && !party.removed_at
            );
        },
        /**
         * Returns competitive process geometries as a FeatureCollection adding whether
         * the geometry is from the competitive process or from a proposal.
         */
        geometriesToFeatureCollection: function () {
            let vm = this;

            let featureCollection = {
                ...vm.competitive_process.competitive_process_geometries,
            };
            Object.keys(featureCollection['features']).forEach(function (key) {
                featureCollection['features'][key]['properties']['source'] =
                    'competitive_process';
                // Create competitive process model object using the same field names as for proposal
                let model = {
                    id: vm.competitive_process.id,
                    details_url: vm.competitive_process.details_url,
                    application_type_name_display: vm.competitive_process.label,
                    lodgement_number: vm.competitive_process.lodgement_number,
                    lodgement_date_display:
                        vm.competitive_process.created_at_display,
                    processing_status_display: vm.competitive_process.status,
                };
                featureCollection['features'][key]['model'] = model;
            });

            return featureCollection;
        },
        outcomeDetails: function () {
            /** Returns the outcome details text
             */

            // This is here to re-evalute the computed property after fetching details texts
            this.cp_id;

            if (this.competitive_process.details) {
                return this.competitive_process.details;
            } else {
                // Use standard text from admin
                let id = Object.prototype.hasOwnProperty.call(
                    this.$refs,
                    'details'
                )
                    ? this.$refs.details.id
                    : '';
                return this.detailsTexts[id] || '';
            }
        },
    },
    created: function () {
        this.fetchCompetitiveProcess();
        utils.fetchKeyValueLookup(api_endpoints.groups, '').then((data) => {
            this.groups = data;
        });
    },
    mounted: function () {},
    methods: {
        mapTabClicked: function () {
            this.$refs.component_map.forceToRefreshMap();
        },
        outcomeTabClicked: function () {
            let vm = this;
            let initialisers = [
                utils.fetchUrl(`${api_endpoints.details_text}key-value-list/`),
            ];
            Promise.all(initialisers).then((data) => {
                for (let detailText of data[0]) {
                    vm.detailsTexts[detailText.target] = detailText.body;
                }
                vm.cp_id = uuid();
            });

            vm.initSelectWinner();
        },
        initSelectWinner: function () {
            let vm = this;

            $(vm.$refs.select_winner)
                .select2({
                    theme: 'bootstrap-5',
                    allowClear: true,
                    placeholder: 'No winner',
                })
                .on('select2:select', function (e) {
                    var selected_winner = $(e.currentTarget);
                    vm.competitive_process.winner_id = Number(
                        selected_winner.val()
                    );
                    vm.$nextTick(async () => {
                        vm.cp_id = uuid();
                    });
                })
                .on('select2:unselecting', function () {
                    var self = $(this);
                    setTimeout(() => {
                        self.select2('close');
                    }, 0);
                })
                .on('select2:unselect', function () {
                    vm.competitive_process.winner_id = null;
                    vm.$nextTick(async () => {
                        vm.cp_id = uuid();
                    });
                });
        },
        detailsTextChanged: function (new_text) {
            this.competitive_process.details = new_text;
        },
        save_and_continue: function () {
            this.save();
        },
        save_and_exit: async function () {
            await this.save();
            this.$router.push({ name: 'internal-dashboard' });
        },
        constructPayload: function () {
            let vm = this;

            // Shallow (?) copy competitive_process object into payload
            let payload = { ...vm.competitive_process };
            if (vm.$refs.component_map) {
                // Update geometry data of the competitive process
                let geojson_str = vm.$refs.component_map.getJSONFeatures();
                payload['competitive_process_geometries'] = geojson_str;
            }

            let custom_row_apps = {};
            for (let a_party of vm.competitive_process
                .competitive_process_parties) {
                if (Object.hasOwn(a_party, 'custom_row_app')) {
                    custom_row_apps[a_party.id] = JSON.parse(
                        JSON.stringify(a_party.custom_row_app)
                    );
                    a_party.custom_row_app = undefined; // Remove custom_row_app in order to JSON.stringify()
                }
            }

            return payload;
        },
        set_custom_rows_property(property, value) {
            let vm = this;
            if (!vm.$refs.competitive_process_parties) {
                return;
            }
            Object.keys(
                vm.$refs.competitive_process_parties.custom_row_apps
            ).forEach(function (key) {
                vm.$refs.competitive_process_parties.custom_row_apps[key][
                    'instance'
                ][property] = value;
            });
        },
        save: async function (
            show_confirmation = true,
            increment_map_key = true
        ) {
            let vm = this;

            vm.processing = true;
            // Saving, so set custom row to processing
            vm.set_custom_rows_property('processing', true);

            let save_continue = true;
            // The current winner as saved in the database
            let current_winner_id = vm.competitive_process.winner
                ? vm.competitive_process.winner.id
                : null;
            // The new winner as selected in the form
            let new_winner_id = vm.competitive_process.winner_id;

            // On an unlocked CP check if the winner has been changed
            if (
                vm.competitive_process.status_id ==
                    constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS_UNLOCKED
                        .ID &&
                current_winner_id != new_winner_id
            ) {
                let info_text = '';
                current_winner_id == null && new_winner_id != null
                    ? (info_text =
                          'A winner has been selected for this competitive process.')
                    : current_winner_id != null && new_winner_id == null
                      ? (info_text =
                            'The winner has been removed from this competitive process. Saving will discard their proposal.')
                      : (info_text =
                            "The winner has been changed for this competitive process. Saving will discard the previous winner's proposal.");

                // Issue a warning that saving with a changed winner potentially will discard their proposal
                await swal
                    .fire({
                        title: 'The outcome has changed',
                        html: `${info_text} Do you wish to continue?<br /><br />Please make sure Details and Documents are correct for the new outcome.<br />`,
                        icon: 'question',
                        reverseButtons: true,
                        showCancelButton: true,
                        confirmButtonText: 'Continue',
                        confirmButtonColor: '#0d6efd',
                    })
                    .then(async (result) => {
                        if (!result.isConfirmed) {
                            save_continue = false;
                        }
                    });
            }

            if (!save_continue) {
                vm.processing = false;
                return;
            }

            let payload = vm.constructPayload();
            fetch(vm.competitive_process_form_url, {
                body: JSON.stringify(payload),
                method: 'PUT',
            })
                .then(async (response) => {
                    if (!response.ok) {
                        return response.text().then((text) => {
                            throw new Error(text);
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then((data) => {
                    vm.competitive_process = Object.assign(data, {});
                    if (show_confirmation) {
                        swal.fire({
                            title: 'Saved',
                            text: 'Competitive process has been saved',
                            icon: 'success',
                            confirmButtonColor: '#0d6efd',
                        });
                    }
                    // Done save, set custom row back to not processing
                    vm.set_custom_rows_property('processing', false);
                    vm.$nextTick(async () => {
                        vm.cp_id = uuid();
                        if (increment_map_key) {
                            vm.incrementComponentMapKey();
                        }
                    });
                })
                .catch((error) => {
                    swal.fire({
                        title: 'Please fix following errors before saving',
                        text: error,
                        icon: 'error',
                        confirmButtonColor: '#0d6efd',
                    });
                    vm.set_custom_rows_property('processing', false);
                })
                .finally(() => {
                    vm.processing = false;
                });
        },
        issueComplete: async function () {
            let vm = this;
            try {
                vm.processing = true;
                let description = '';
                if (vm.competitive_process.winner_id) {
                    for (let party of vm.competitive_process
                        .competitive_process_parties) {
                        if (party.id === vm.competitive_process.winner_id) {
                            if (party.is_person) {
                                description =
                                    '<strong>' +
                                    party.person.fullname +
                                    '</strong> is selected as a winner.';
                                break;
                            } else if (party.is_organisation) {
                                description =
                                    '<strong>' +
                                    party.organisation
                                        .ledger_organisation_name +
                                    '</strong> is selected as a winner.';
                                break;
                            }
                            return;
                        }
                    }
                } else {
                    description = '<strong>No winner</strong> selected';
                }
                swal.fire({
                    title: 'Complete this competitive process',
                    html:
                        'Are you sure you want to complete this competitive process?<br />' +
                        description,
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonText: 'Complete',
                    confirmButtonColor: '#0d6efd',
                    reverseButtons: true,
                }).then(async (result) => {
                    if (result.isConfirmed) {
                        // When Yes
                        let payload = vm.constructPayload();

                        utils
                            .fetchUrl(vm.competitive_process_complete_url, {
                                body: JSON.stringify(payload),
                                method: 'POST',
                            })
                            .then(async () => {
                                await new swal({
                                    title: 'Completed',
                                    text: 'Competitive process has been completed',
                                    icon: 'success',
                                });
                                this.$router.push({
                                    name: 'internal-dashboard',
                                });
                            })
                            .catch(async (error) => {
                                await swal.fire({
                                    title: 'Please fix following errors before completing',
                                    text: error,
                                    icon: 'error',
                                    confirmButtonColor: '#0d6efd',
                                });
                            })
                            .finally(() => {
                                vm.processing = false;
                            });
                    } else {
                        vm.processing = false;
                    }
                });
            } catch (err) {
                console.error(err);
            }
        },
        issueDiscard: async function () {
            let vm = this;
            try {
                vm.processing = true;
                swal.fire({
                    title: 'Discard this competitive process',
                    text: 'Are you sure you want to discard this competitive process?',
                    icon: 'question',
                    reverseButtons: true,
                    showCancelButton: true,
                    confirmButtonText: 'Discard',
                    confirmButtonColor: '#0d6efd',
                }).then(async (result) => {
                    if (result.isConfirmed) {
                        // When Yes
                        let payload = vm.constructPayload();
                        await fetch(vm.competitive_process_discard_url, {
                            body: JSON.stringify(payload),
                            method: 'POST',
                        })
                            .then(async (response) => {
                                if (!response.ok) {
                                    return response.text().then((text) => {
                                        throw new Error(text);
                                    });
                                } else {
                                    return await response.json();
                                }
                            })
                            .then(async () => {
                                await swal.fire({
                                    title: 'Discarded',
                                    text: 'Competitive process has been discarded',
                                    icon: 'success',
                                });
                                this.$router.push({
                                    name: 'internal-dashboard',
                                });
                            })
                            .catch((error) => {
                                swal.fire({
                                    title: 'Please fix following errors before discarding',
                                    text: JSON.parse(error.message),
                                    icon: 'error',
                                    confirmButtonColor: '#0d6efd',
                                });
                                vm.processing = false;
                            });
                    }
                    vm.processing = false;
                });
            } catch (err) {
                console.error(err);
            }
        },
        issueUnlock: async function () {
            let vm = this;
            swal.fire({
                title: 'Unlock this competitive process',
                text: "Unlocking this competitive process will change the status to 'In Progress (Unlocked)'\
                            and allow to change the outcome to a different winner.\
                            Are you sure you want to unlock this competitive process?",
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Unlock',
                confirmButtonColor: '#0d6efd',
                reverseButtons: true,
            }).then(async (result) => {
                if (result.isConfirmed) {
                    vm.processing = true;
                    // When Yes
                    let payload = vm.constructPayload();
                    await utils
                        .fetchUrl(vm.competitive_process_unlock_url, {
                            body: JSON.stringify(payload),
                            method: 'POST',
                        })
                        .then(async (data) => {
                            vm.competitive_process = Object.assign({}, data);
                            await swal.fire({
                                title: 'Unlocked',
                                text: 'Competitive process has been unlocked',
                                icon: 'success',
                            });
                            vm.processing = false;
                            vm.$nextTick(async () => {
                                vm.cp_id = uuid();
                            });
                        })
                        .catch(async (error) => {
                            await swal.fire({
                                title: 'Error unlocking competitive process',
                                text: error,
                                icon: 'error',
                            });
                            vm.processing = false;
                        });
                } else if (result.isDenied) {
                    // When No
                } else {
                    // When cancel
                }
            });
        },
        refreshFromResponse: function (data) {
            Object.assign(this.competitive_process, data);
            this.incrementComponentMapKey();
        },
        updateTableByFeatures: function () {},
        featureGeometryUpdated: function () {},
        popupClosed: function () {},
        assignedOfficerPayload: function (user) {
            /* Return the payload for assigning an officer to a competitive process.
             *  If the user is a number, it is assumed to be a user ID.
             *  Creates a user dictionary from the user ID if user is not already
             *  a dictionary.
             *  Else if the user is null, it is assumed to be unassigning the officer.
             */

            let assigned_officer = user;
            if (user != null && !isNaN(Number(user))) {
                // Get the assigned officer dictionary from the user ID if user isa number
                // or string representation of a number
                assigned_officer = this.partyById(
                    Number(user),
                    this.competitive_process.allowed_editors
                );
            }
            // Return the payload
            return {
                body: JSON.stringify({ assigned_officer: assigned_officer }),
                method: 'POST',
            };
        },
        assignTo: async function () {
            let vm = this;
            let unassign = true;

            unassign =
                this.competitive_process.assigned_officer != null &&
                this.competitive_process.assigned_officer != 'undefined'
                    ? false
                    : true;

            let payload = this.assignedOfficerPayload(
                this.competitive_process.assigned_officer
            );

            if (unassign) {
                vm.assign_api_call('unassign');
            } else {
                vm.assign_api_call('assign_user', payload);
            }
        },
        assignRequestUser: async function () {
            let payload = this.assignedOfficerPayload(
                this.competitive_process.accessing_user
            );
            this.assign_api_call('assign_user', payload);
        },
        assign_api_call: async function (api_function, payload) {
            let vm = this;
            if (typeof api_function === 'undefined') {
                api_function = 'assign_user';
            }
            if (typeof payload === 'undefined') {
                payload = {};
            }

            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.competitive_process,
                    `${vm.competitive_process.id}/${api_function}`
                ),
                payload
            )
                .then(async (response) => {
                    if (!response.ok) {
                        return response.text().then((text) => {
                            throw new Error(text);
                        });
                    } else {
                        return await response.json();
                    }
                })
                .then((data) => {
                    vm.competitive_process = Object.assign({}, data);
                    vm.updateAssignedOfficerSelect();
                })
                .catch((error) => {
                    this.updateAssignedOfficerSelect();
                    console.error(error);
                    swal.fire({
                        title: 'Proposal Error',
                        text: error,
                        icon: 'error',
                    });
                });
        },
        fetchCompetitiveProcess: async function () {
            let vm = this;
            try {
                const res = await fetch(
                    `${api_endpoints.competitive_process}${vm.$route.params.competitive_process_id}/`
                );
                if (!res.ok) throw new Error(res.statusText); // 400s or 500s error
                let competitive_process = await res.json();
                vm.competitive_process = competitive_process;
            } catch (err) {
                console.error({ err });
            }
        },
        updateAssignedOfficerSelect: function () {
            let vm = this;
            if (
                [
                    constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS.ID,
                    constants.COMPETITIVE_PROCESS_STATUS.IN_PROGRESS_UNLOCKED
                        .ID,
                ].includes(vm.competitive_process.status_id)
            ) {
                let assigned_officer = vm.competitive_process.assigned_officer;
                let _id = assigned_officer ? assigned_officer.id : null;
                vm.$refs.workflow.updateAssignedOfficerSelect(_id);
            } else {
                console.warn('Skipping assignment of selected officer');
            }
        },
        partyById: function (party_id, party_dict) {
            /** Returns the party with ID `party_id` from the dictionary `party_dict`,
             *  or null if the party ID is null (e.g. when chosing no winner),
             *  or when no party for the respective ID can not be found.
             *  Defaults to the competitive process party when `party_dict` is not provided.
             */

            if (party_id == null) {
                return null; // e.g. no winner outcome
            }

            if (party_dict == null) {
                party_dict =
                    this.competitive_process.competitive_process_parties;
            }

            let idx = party_dict.findIndex((p) => p.id == party_id);
            if (idx == -1) {
                console.warn(`There is no party with ID ${party_id}.`);
                return null;
            }
            // Return the party
            return party_dict[idx];
        },
        addDetail: function (new_party_data) {
            /** Callback for `add-detail` event emitted by custom-row */

            // This party's ID
            let id = Object.keys(new_party_data)[0];
            // Get the related competitive process party
            let party = this.partyById(id);
            if (party) {
                // Add new party detail
                party.party_details.push(new_party_data[id]);
            } else {
                console.error(`Can not add data to party with ID ${id}.`);
            }
        },
        addParty: function (new_party_data) {
            /** Callback for `add-party` event emitted by custom-row */

            // Add new party
            this.competitive_process.competitive_process_parties.push(
                new_party_data
            );
            this.save(true, false);
            this.$refs.competitive_process_parties.$refs.parties_datatable.vmDataTable.draw();
        },
        updatePartyDate: function (e) {
            console.log('e', e);
            let party =
                this.competitive_process.competitive_process_parties.find(
                    (party) => party.id == e.party_id
                );
            party[e.date_field] = e.new_date;
            console.log('party', party);
        },
        incrementComponentMapKey: function () {
            this.componentMapKey++;
        },
        updateGISData: function (property, val) {
            if (
                this.competitive_process.gis_data[property].find(
                    (item) => item.id == val.id
                )
            ) {
                this.competitive_process.gis_data[property] =
                    this.competitive_process.gis_data[property].filter(
                        (item) => item.id != val.id
                    );
            } else {
                this.competitive_process.gis_data[property].push({
                    id: val.id,
                    name: val.name,
                });
            }
        },
        onFinishedDrawing: function () {
            if (this.$refs.component_map.autoSave) {
                this.saveMapFeatures();
            }
        },
        saveMapFeatures: function () {
            // Save the entire proposal including the map features without reloading the map
            this.save(false, false);
        },
    },
};
</script>
