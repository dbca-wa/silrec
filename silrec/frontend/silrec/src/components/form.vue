<template lang="html">
    <div class="">
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">src/components/form.vue</div>
        <div
            v-if="proposal"
            id="scrollspy-heading"
            class=""
        >
        </div>
        
        <!-- Shapefile Upload Section -->
        <FormSection
            :form-collapse="false"
            label="Shapefile Upload"
            index="shapefile_upload"
        >
            <div class="shapefile-upload-container">
                <div class="upload-controls">
                    <div class="d-flex align-items-center">
                        <button 
                            class="btn btn-primary"
                            @click="triggerShapefileUpload"
                            :disabled="uploadingShapefile"
                        >
                            <i class="bi bi-upload me-2"></i>
                            Upload Shapefile
                        </button>

                        <!--<div v-if="uploadedFileName" class="ms-3">-->
                        <div class="ms-3">
                        <button 
                            class="btn btn-primary process-btn"
                            @click="!triggerShapefileProcess"
                            :disabled="uploadingShapefile"
                        >
                            <i class="bi bi-upload me-2"></i>
                            Process Shapefile
                        </button>
                        </div>

                       
                        <!-- Display uploaded filename -->
                        <div v-if="uploadedFileName" class="ms-3 uploaded-filename">
                            <i class="bi bi-file-earmark-zip me-1"></i>
                            <span class="text-muted">Uploaded:</span>
                            <strong class="ms-1">{{ uploadedFileName }}</strong>
                        </div>
                        
                    </div>
                    
                    <input 
                        type="file" 
                        ref="shapefileInput"
                        accept=".zip"
                        style="display: none"
                        @change="handleShapefileUpload"
                    >
                    
                    <!-- Upload Progress -->
                    <div v-if="uploadingShapefile" class="upload-progress mt-2">
                        <div class="progress">
                            <div 
                                class="progress-bar progress-bar-striped progress-bar-animated" 
                                role="progressbar" 
                                :style="{ width: uploadProgress + '%' }"
                            >
                                {{ uploadProgress }}%
                            </div>
                        </div>
                        <small class="text-muted">{{ uploadStatus }}</small>
                    </div>
                    
                    <!-- Upload Error -->
                    <div v-if="uploadError" class="alert alert-danger mt-2">
                        {{ uploadError }}
                    </div>
                    
                    <!-- Success Message -->
                    <div v-if="uploadSuccess" class="alert alert-success mt-2">
                        <i class="bi bi-check-circle me-2"></i>
                        Shapefile uploaded and processed successfully!
                    </div>
                </div>
                
                <div class="upload-info mt-2">
                    <small class="text-muted">
                        <i class="bi bi-info-circle me-1"></i>
                        Upload a .zip file containing shapefile components (.shp, .shx, .dbf, .prj)
                    </small>
                </div>
            </div>
        </FormSection>

        <!-- Map Component -->
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
                :featureCollection3="geometriesToFeatureCollection3"
                :featureCollection4="geometriesToFeatureCollection4"
                :displayFieldsConfig="displayFieldsConfig"
                :additionalFieldsConfig="additionalFieldsConfig"
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

export default {
    name: 'ProposalForm',
    components: {
        FormSection,
        MapComponent,
    },
    props: {
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
            displayFieldsConfig: [
                { key: 'name', label: 'Name' },
                { key: 'Block', label: 'Block' },
                { key: 'Compno', label: 'Comp No' }
            ],
            additionalFieldsConfig:[
                { key: 'Region', label: 'Region' },
                { key: 'fea_id', label: 'Feature ID' },
                { key: 'Area', label: 'Area' },
                { key: 'Ops_status', label: 'Status' }
            ],
            
            // Shapefile upload states
            uploadingShapefile: false,
            uploadProgress: 0,
            uploadStatus: '',
            uploadError: null,
            uploadSuccess: false,
            uploadedFileName: '',
            
            // Add this to force map refresh
            componentMapKey: 0,
        };
    },
    computed: {
        proposalId: function () {
            return this.proposal ? this.proposal.id : null;
        },
        uploadedFileName: function () {
            return this.proposal ? this.proposal.shapefile_name : null;
        },
        geometriesToFeatureCollection: function () {
            let vm = this;
            let featureCollection = {
                type: 'FeatureCollection',
                features: [],
            };

            if (vm.proposal && vm.proposal.shapefile_json) {
                // If shapefile_json exists, use it directly
                if (vm.proposal.shapefile_json.type === 'FeatureCollection') {
                    return vm.proposal.shapefile_json;
                }
            }

            // Fallback to existing logic
            let proposalgeometries = {
                ...(vm.proposal.proposalgeometry ? vm.proposal.proposalgeometry : {}),
            };

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
            }
            return featureCollection;
        },
        geometriesToFeatureCollection4: function () {
            let vm = this;
            let proposalgeometries = {
                ...(vm.proposal.proposalgeometry_processed_iters ? vm.proposal.proposalgeometry_processed_iters : {}),
            };

            const resultList = [];
            for (const key in proposalgeometries) {
                let featureCollection = {
                    type: 'FeatureCollection',
                    features: [],
                    cht_init: Object,
                    cht_new: Object,
                };

                if (Object.keys(proposalgeometries[key]).length !== 0) {
                    for (let feature of proposalgeometries[key]['features']) {
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
                    featureCollection['cht_init'] = proposalgeometries[key]['cht_init'];
                    featureCollection['cht_new'] = proposalgeometries[key]['cht_new'];
                }

                resultList.push(featureCollection);
            }

            return resultList;
        },
    },
    created: function () {
        this.uuid = uuid();
    },
    mounted: function () {
        this.$emit('formMounted');
    },
    methods: {
        /*
        Improved map refresh logic:
            Increment componentMapKey to force Vue to re-create the MapComponent
            Wait for $nextTick() to ensure DOM is updated
            Call forceToRefreshMap() after a short delay to ensure the map is fully initialized
        */
        incrementComponentMapKey: function () {
            this.componentMapKey += 1;
        },
        toggleComponentMapOn: function () {
            this.incrementComponentMapKey()
            this.componentMapOn = true;
            this.$nextTick(() => {
                if (this.$refs.component_map && this.$refs.component_map.forceToRefreshMap) {
                    this.$refs.component_map.forceToRefreshMap();
                }
            });
        },
        refreshFromResponse: function (data) {
            this.$emit('refreshFromResponse', data);
        },
        
        // Shapefile Upload Methods
        triggerShapefileUpload: function () {
            this.$refs.shapefileInput.click();
        },

        handleShapefileUpload: function (event) {
            const file = event.target.files[0];
            if (!file) {
                return;
            }

            // Store the file name immediately
            if (file.name !== null || file.name !== undefined || file.name !== '') {
                console.log('1')
                this.uploadedFileName = file.name;
            } else {
                console.log('2')
                this.uploadedFileName = this.proposal.shapefile_name;
            }
            
            // Reset previous upload state (but keep filename)
            this.uploadSuccess = false;
            this.uploadError = null;

            // Validate file type
            if (!file.name.toLowerCase().endsWith('.zip')) {
                this.uploadError = 'Please upload a .zip file';
                this.clearFileInput();
                return;
            }

            this.uploadShapefile(file);
        },

        uploadShapefile: async function (file) {
            this.uploadingShapefile = true;
            this.uploadProgress = 0;
            this.uploadStatus = 'Preparing upload...';
            this.uploadError = null;
            this.uploadSuccess = false;
            
            const formData = new FormData();
            formData.append('shapefile', file);
            formData.append('proposal_id', this.proposalId);
            
            try {
                // Create upload endpoint URL
                const url = helpers.add_endpoint_join(
                    this.api_endpoints.proposal,
                    this.proposalId + '/upload_shapefile/'
                );
                
                // Get CSRF token
                const csrfToken = helpers.getCookie('csrftoken');
                
                // Simulate upload progress (since fetch doesn't support progress events)
                const progressInterval = setInterval(() => {
                    if (this.uploadProgress < 90) {
                        this.uploadProgress += 10;
                        this.uploadStatus = `Uploading... ${this.uploadProgress}%`;
                    }
                }, 300);
                
                // Use fetch API instead of $http
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken,
                        // Don't set Content-Type for FormData, let browser set it
                    },
                });
                
                clearInterval(progressInterval);
                this.uploadProgress = 100;
                this.uploadStatus = 'Upload complete, processing...';
                
                // Check if response is OK
                if (!response.ok) {
                    let errorMessage = `Upload failed: ${response.status} ${response.statusText}`;
                    
                    // Try to get error details from response body
                    try {
                        const errorData = await response.json();
                        if (errorData.error) {
                            errorMessage = errorData.error;
                        }
                        if (errorData.details) {
                            errorMessage += ` - ${errorData.details}`;
                        }
                    } catch (e) {
                        // If we can't parse JSON, use status text
                        console.error('Error parsing error response:', e);
                    }
                    
                    throw new Error(errorMessage);
                }
                
                // Parse successful response
                const data = await response.json();
                
                // Update status
                this.uploadStatus = 'Processing shapefile...';
                
                // Wait a moment for processing feedback
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // Handle success
                this.uploadSuccess = true;
                this.uploadStatus = 'Shapefile processed successfully!';
                
                // Check if data contains the expected structure
                if (data.success && data.proposal) {
                    // Emit refresh event to update parent component
                    this.$emit('refreshFromResponse', data.proposal);
                    
                    // Force map refresh by incrementing the key
                    this.incrementComponentMapKey();
                    
                    // Wait for Vue to update the DOM
                    await this.$nextTick();
                    
                    // Also call forceToRefreshMap on the map component
                    if (this.$refs.component_map && this.$refs.component_map.forceToRefreshMap) {
                        // Give the map a moment to initialize
                        setTimeout(() => {
                            this.$refs.component_map.forceToRefreshMap();
                        }, 500);
                    }
                    
                    // Clear success message after 5 seconds
                    setTimeout(() => {
                        this.uploadSuccess = false;
                    }, 5000);
                } else {
                    // Handle unexpected response structure
                    throw new Error(data.message || 'Unexpected response from server');
                }
                
            } catch (error) {
                console.error('Error uploading shapefile:', error);
                
                let errorMessage = 'Failed to upload shapefile';
                if (error.message) {
                    errorMessage = error.message;
                }
                
                this.uploadError = errorMessage;
                
                // Clear error after 10 seconds
                setTimeout(() => {
                    this.uploadError = null;
                }, 10000);
            } finally {
                this.uploadingShapefile = false;
                this.uploadProgress = 0;
                this.uploadStatus = '';
                this.clearFileInput();
            }
        },
        
        clearFileInput: function () {
            if (this.$refs.shapefileInput) {
                this.$refs.shapefileInput.value = '';
            }
        }
    }
};
</script>

<style lang="css" scoped>
/* Shapefile Upload Styles */
.shapefile-upload-container {
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 4px;
    border: 1px solid #dee2e6;
}

.upload-controls {
    margin-bottom: 10px;
}

.uploaded-filename {
    padding: 8px 12px;
    background-color: #e9ecef;
    border-radius: 4px;
    border: 1px solid #dee2e6;
    font-size: 0.9em;
}

.upload-progress {
    max-width: 400px;
}

.alert {
    max-width: 400px;
}

.upload-info {
    font-size: 0.9em;
}

/* Existing styles */
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
    display-inline: block;
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

.process-btn {
  float: right;
}
</style>
