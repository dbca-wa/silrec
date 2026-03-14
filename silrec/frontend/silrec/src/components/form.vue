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
                    <div class="d-flex align-items-center flex-wrap">
                        <button 
                            class="btn btn-primary me-2"
                            @click="triggerShapefileUpload"
                            :disabled="uploadingShapefile"
                        >
                            <i class="bi bi-upload me-2"></i>
                            Upload Shapefile
                        </button>

                        <!-- Display uploaded filename -->
                        <div v-if="fileNameToDisplay" class="ms-2 uploaded-filename">
                            <i class="bi bi-file-earmark-zip me-1"></i>
                            <span class="text-muted">Uploaded:</span>
                            <strong class="ms-1">{{ fileNameToDisplay }}</strong>
                        </div>
                        
                        <!-- In the template, update the button section -->
                        <div class="ms-auto d-flex gap-2">
                            <button 
                                class="btn btn-warning revert-btn"
                                @click="openRevertDialog"
                                :disabled="!hasProcessedData || revertingShapefile"
                                :title="!hasProcessedData ? 'No processed data to revert' : ''"
                            >
                                <i class="bi bi-arrow-counterclockwise me-2"></i>
                                <span v-if="revertingShapefile">
                                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                    Reverting...
                                </span>
                                <span v-else>Revert</span>
                            </button>
                            
                            <button 
                                class="btn btn-success process-btn"
                                @click="openProcessDialog"
                                :disabled="!hasShapefile || processingShapefile"
                                :title="!hasShapefile ? 'Upload a shapefile first' : ''"
                            >
                                <i class="bi bi-gear me-2"></i>
                                <span v-if="processingShapefile">
                                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                    Processing...
                                </span>
                                <span v-else>Process Shapefile</span>
                            </button>
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
                    
                    <!-- Processing Error -->
                    <div v-if="processError" class="alert alert-danger mt-2">
                        {{ processError }}
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
                @update-processed-geometry="handleProcessedGeometryUpdate"
                @refresh-datatable="refreshPolygonCohortTable"
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

        <!-- Debug Snapshot Toggle -->
        <SnapshotDebugToggle
            v-if="$route.query.debug?.toLowerCase() === 'true'"
            :proposal-id="proposalId"
            :user-id="currentUserId"
            :show-debug="true"
            ref="snapshotDebugToggle"
        />

    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import FileField from '@/components/forms/filefield_immediate.vue';
import MapComponent from '@/components/common/component_map.vue';
import Multiselect from 'vue-multiselect';
import GisDataDetails from '@/components/common/gis_data_details.vue';
import SnapshotDebugToggle from '@/components/common/SnapshotDebugToggle.vue';
import { v4 as uuid } from 'uuid';
import Swal from 'sweetalert2';

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
        SnapshotDebugToggle,
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
            
            // Shapefile processing states
            processingShapefile: false,
            processError: null,
            
            // Temporary filename for immediate feedback (until proposal updates)
            selectedFileName: '',
            
            // Map key – used only if we must force a full remount (rare)
            componentMapKey: 0,
            
            // Current user ID (you'll need to set this from your auth system)
            currentUserId: null,

            // Shapefile processing states
            processingShapefile: false,
            processError: null,
            
            // Add these new properties
            revertingShapefile: false,
            revertError: null,

        };
    },
    computed: {
        proposalId: function () {
            return this.proposal ? this.proposal.id : null;
        },
        // Computed property for the stored filename from proposal
        storedFileName: function () {
            return this.proposal ? this.proposal.shapefile_name : null;
        },
        // Display filename: show selectedFileName during upload, otherwise storedFileName
        fileNameToDisplay: function () {
            return this.selectedFileName || this.storedFileName;
        },
        // Check if shapefile exists
        hasShapefile: function () {
            return !!(this.storedFileName || this.proposal.shapefile_json);
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

            // Use processed geometries if available
            if (vm.proposal && vm.proposal.proposalgeometry_processed) {
                if (vm.proposal.proposalgeometry_processed.type === 'FeatureCollection') {
                    return vm.proposal.proposalgeometry_processed;
                }
            }

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

        // Check if there's processed data to revert
        hasProcessedData: function () {
            return !!(this.proposal && 
                    (this.proposal.proposalgeometry_processed || 
                    this.proposal.proposalgeometry_processed_iters ||
                    this.proposal.geojson_data_processed ||
                    this.proposal.geojson_data_processed_iters));
        }
    },
    created: function () {
        this.uuid = uuid();
        
        // Get current user ID from your auth system
        // This depends on how your app manages user authentication
        this.getCurrentUser();
    },
    mounted: function () {
        this.$emit('formMounted');
    },
    beforeDestroy: function () {   // Changed from beforeUnmount to beforeDestroy for Vue 2
        // Cleanup if needed
    },
    methods: {
        handleProcessedGeometryUpdate(updatedGeoJSON) {
            // Update the proposal's processed geometry data
            //this.proposal.proposalgeometry_processed = updatedGeoJSON;
            // Optionally trigger an API call to save
            //this.$emit('refreshFromResponse', this.proposal);
        },

        /*
        Map refresh: removed key increment on upload; map will update via prop watchers.
        forceToRefreshMap is still available for resizing if necessary.
        */
        refreshFromResponse: function (data) {
            this.$emit('refreshFromResponse', data);
        },
        
        // Get current user
        getCurrentUser: async function () {
            try {
                // You'll need to implement this based on your auth system
                // This is just an example
                const response = await fetch('/api/user/');
                const data = await response.json();
                this.currentUserId = data.id;
            } catch (error) {
                console.error('Error getting current user:', error);
                
                // Fallback: try to get from the proposal submitter
                if (this.proposal && this.proposal.submitter_obj) {
                    this.currentUserId = this.proposal.submitter_obj.id;
                }
            }
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

            // Store selected filename immediately
            this.selectedFileName = file.name;
            
            // Reset previous upload state
            this.uploadSuccess = false;
            this.uploadError = null;
            this.processError = null;

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
            
            // Simulated progress interval – will be cleared on error/success
            let progressInterval = null;
            
            try {
                const url = helpers.add_endpoint_join(
                    this.api_endpoints.proposal,
                    this.proposalId + '/upload_shapefile/'
                );
                
                const csrfToken = helpers.getCookie('csrftoken');
                
                // Simulate upload progress (will be cleared in finally)
                progressInterval = setInterval(() => {
                    if (this.uploadProgress < 90) {
                        this.uploadProgress += 10;
                        this.uploadStatus = `Uploading... ${this.uploadProgress}%`;
                    }
                }, 300);
                
                const response = await fetch(url, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': csrfToken,
                    },
                });
                
                clearInterval(progressInterval);
                this.uploadProgress = 100;
                this.uploadStatus = 'Upload complete, processing...';
                
                if (!response.ok) {
                    let errorMessage = `Upload failed: ${response.status} ${response.statusText}`;
                    try {
                        const errorData = await response.json();
                        if (errorData.error) {
                            errorMessage = errorData.error;
                        }
                        if (errorData.details) {
                            errorMessage += ` - ${errorData.details}`;
                        }
                    } catch (e) {
                        console.error('Error parsing error response:', e);
                    }
                    throw new Error(errorMessage);
                }
                
                const data = await response.json();
                
                this.uploadStatus = 'Processing shapefile...';
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                if (data.success && data.proposal) {
                    this.uploadSuccess = true;
                    this.uploadStatus = 'Shapefile processed successfully!';
                    
                    // Emit refresh event to update parent component
                    this.$emit('refreshFromResponse', data.proposal);
                    
                    // Force map resize after data update (without remounting)
                    await this.$nextTick();
                    if (this.$refs.component_map && this.$refs.component_map.forceToRefreshMap) {
                        setTimeout(() => {
                            this.$refs.component_map.forceToRefreshMap();
                        }, 500);
                    }
                    
                    // Clear success message after 5 seconds
                    setTimeout(() => {
                        this.uploadSuccess = false;
                    }, 5000);
                } else {
                    throw new Error(data.message || 'Unexpected response from server');
                }
                
            } catch (error) {
                console.error('Error uploading shapefile:', error);
                
                // Stop progress simulation if it's still running
                if (progressInterval) {
                    clearInterval(progressInterval);
                    progressInterval = null;
                }
                
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
                // Do not clear selectedFileName here – it will be replaced by storedFileName after refresh
            }
        },
        
        clearFileInput: function () {
            if (this.$refs.shapefileInput) {
                this.$refs.shapefileInput.value = '';
            }
        },
        
    // Shapefile Processing Methods
    openProcessDialog: function () {
        if (!this.hasShapefile) {
            Swal.fire({
                icon: 'warning',
                title: 'No Shapefile',
                text: 'Please upload a shapefile first',
                confirmButtonColor: '#3085d6'
            });
            return;
        }
        
        // Show SweetAlert2 dialog with compact horizontal layout
        Swal.fire({
            title: 'Process Shapefile',
            html: `
                <div style="padding: 5px 0;">
                    <div style="display: flex; align-items: center; gap: 10px; margin: 10px 0;">
                        <label for="threshold" style="font-weight: bold; min-width: 120px; text-align: right;">Threshold Value:</label>
                        <div style="flex: 1;">
                            <input 
                                type="number" 
                                id="threshold" 
                                class="swal2-input" 
                                value="5.0" 
                                min="0.1" 
                                max="100" 
                                step="0.1"
                                style="width: 100%; margin: 0;"
                            >
                        </div>
                    </div>
                    <div style="font-size: 0.85em; color: #6c757d; text-align: left; margin-top: 5px; padding-left: 130px;">
                        Higher values remove more sliver polygons. Default is 5.0.
                    </div>
                </div>
            `,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Process',
            cancelButtonText: 'Cancel',
            confirmButtonColor: '#28a745',
            cancelButtonColor: '#6c757d',
            showConfirmButton: true,
            showLoaderOnConfirm: true, // This shows a spinner on the button
            preConfirm: () => {
                const threshold = document.getElementById('threshold').value;
                
                // Validate threshold
                const thresholdValue = parseFloat(threshold);
                if (isNaN(thresholdValue) || thresholdValue < 0.1 || thresholdValue > 100) {
                    Swal.showValidationMessage('Threshold must be between 0.1 and 100');
                    return false;
                }
                
                return {
                    threshold: thresholdValue
                };
            }
        }).then((result) => {
            if (result.isConfirmed && result.value) {
                this.processShapefile(result.value.threshold);
            }
        });
    },

    processShapefile: async function (threshold) {
        // Show processing dialog with spinner
        Swal.fire({
            title: 'Processing Shapefile',
            html: 'Please wait while the shapefile is being processed...',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        
        this.processingShapefile = true;
        this.processError = null;
        
        try {
            const url = helpers.add_endpoint_join(
                this.api_endpoints.proposal,
                this.proposalId + '/process_shapefile/'
            );
            
            const csrfToken = helpers.getCookie('csrftoken');
            
            const payload = {
                threshold: threshold,
                user_id: this.currentUserId,
                proposal_id: this.proposalId
            };
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            // Close loading dialog
            Swal.close();
            
            if (!response.ok) {
                throw new Error(data.error || data.message || 'Failed to process shapefile');
            }
            
            // Success
            if (data.success) {
                // Show compact success message
                const successHtml = `
                    <div style="text-align: center;">
                        <p style="margin-bottom: 10px;">${data.message || 'Shapefile processed successfully!'}</p>
                        ${data.feature_count ? `<p style="font-size: 0.9em; color: #6c757d;">Features processed: ${data.feature_count}</p>` : ''}
                    </div>
                `;
                
                if (data.warnings && data.warnings.length) {
                    await Swal.fire({
                        icon: 'warning',
                        title: 'Processing Complete with Warnings',
                        html: `
                            <div style="text-align: left;">
                                <p>${data.message || 'Shapefile processed with warnings'}</p>
                                <div style="margin-top: 10px; max-height: 150px; overflow-y: auto;">
                                    <ul style="margin: 0; padding-left: 20px;">
                                        ${data.warnings.map(w => `<li style="font-size: 0.9em;">${w}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        `,
                        confirmButtonColor: '#ffc107',
                        confirmButtonText: 'OK'
                    });
                } else {
                    await Swal.fire({
                        icon: 'success',
                        title: 'Success',
                        html: successHtml,
                        confirmButtonColor: '#28a745',
                        timer: 2000,
                        timerProgressBar: true,
                        showConfirmButton: true
                    });
                }
                
                // Update the proposal data with the processed version
                if (data.proposal) {
                    this.$emit('refreshFromResponse', data.proposal);
                }
                
                // Always refresh the map
                this.refreshMapAfterProcessing();
                
            } else {
                throw new Error(data.message || 'Unknown error occurred');
            }
            
        } catch (error) {
            console.error('Error processing shapefile:', error);
            
            // Close loading dialog
            Swal.close();
            
            // Show compact error message
            await Swal.fire({
                icon: 'error',
                title: 'Processing Failed',
                html: `
                    <div style="text-align: center;">
                        <p style="color: #dc3545;">${error.message || 'An error occurred while processing the shapefile'}</p>
                    </div>
                `,
                confirmButtonColor: '#dc3545'
            });
            
            this.processError = error.message;
        } finally {
            this.processingShapefile = false;
        }
    },        

        refreshMapAfterProcessing: function () {
            // Method 1: Increment map key to force full remount (if needed)
            // this.componentMapKey += 1;
            
            // Method 2: Use map's refresh method
            this.$nextTick(() => {
                if (this.$refs.component_map && this.$refs.component_map.forceToRefreshMap) {
                    // Small delay to ensure data is updated
                    setTimeout(() => {
                        this.$refs.component_map.forceToRefreshMap();
                    }, 500);
                }
            });
        },

        // Add this method to refresh the polygon cohort table
        refreshPolygonCohortTable: function () {
            console.log('Refreshing polygon cohort table from parent');
            // Find the PolygonCohortTable component in the DOM
            // Since it's inside the MapComponent, we need to access it through the map component's ref
            if (this.$refs.component_map && this.$refs.component_map.$refs.polygonCohortTable) {
                this.$refs.component_map.$refs.polygonCohortTable.refreshData();
            } else {
                console.warn('PolygonCohortTable ref not found');
                // Fallback: try to find by query selector
                setTimeout(() => {
                    const tableComponent = document.querySelector('[data-table="polygon-cohort"]');
                    if (tableComponent && tableComponent.__vue__) {
                        tableComponent.__vue__.refreshData();
                    }
                }, 500);
            }
        },

        // Open revert confirmation dialog
        openRevertDialog: function () {
            Swal.fire({
                title: 'Revert Changes',
                html: `
                    <div style="text-align: left;">
                        <p>Are you sure you want to revert all changes made by the last shapefile processing operation?</p>
                        <p style="font-weight: bold; color: #dc3545;">This action cannot be undone!</p>
                        <p>This will:</p>
                        <ul style="margin-top: 5px;">
                            <li>Restore the proposal to its state before processing</li>
                            <li>Remove any new polygons and cohorts created</li>
                            <li>Restore original geometry data</li>
                        </ul>
                    </div>
                `,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Yes, Revert Changes',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
                showLoaderOnConfirm: true,
                preConfirm: () => {
                    return this.revertShapefileProcessing();
                }
            }).then((result) => {
                if (result.isConfirmed && result.value) {
                    // Success message already shown in revert method
                }
            });
        },
        
        // Revert shapefile processing
        revertShapefileProcessing: async function () {
            this.revertingShapefile = true;
            this.revertError = null;
            
            // Show processing dialog
            Swal.fire({
                title: 'Reverting Changes',
                html: 'Please wait while reverting to previous state...',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });
            
            try {
                const url = helpers.add_endpoint_join(
                    this.api_endpoints.proposal,
                    this.proposalId + '/revert_shapefile_processing/'
                );
                
                const csrfToken = helpers.getCookie('csrftoken');
                
                const payload = {
                    user_id: this.currentUserId,
                    proposal_id: this.proposalId
                };
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify(payload)
                });
                
                const data = await response.json();
                
                // Close loading dialog
                Swal.close();
                
                if (!response.ok) {
                    throw new Error(data.error || data.message || 'Failed to revert changes');
                }
                
                // Success
                if (data.success) {
                    await Swal.fire({
                        icon: 'success',
                        title: 'Revert Successful',
                        html: `
                            <div style="text-align: center;">
                                <p>${data.message || 'Successfully reverted to previous state'}</p>
                                ${data.records_removed ? `<p style="font-size: 0.9em; color: #6c757d;">Records removed: ${data.records_removed}</p>` : ''}
                            </div>
                        `,
                        confirmButtonColor: '#28a745',
                        timer: 3000,
                        timerProgressBar: true
                    });
                    
                    // Update the proposal data with the reverted version
                    if (data.proposal) {
                        this.$emit('refreshFromResponse', data.proposal);
                    }
                    
                    // Always refresh the map
                    this.refreshMapAfterProcessing();
                    
                    // Refresh the datatable
                    this.refreshPolygonCohortTable();
                    
                } else {
                    throw new Error(data.message || 'Unknown error occurred');
                }
                
            } catch (error) {
                console.error('Error reverting changes:', error);
                
                // Close loading dialog
                Swal.close();
                
                // Show error message
                await Swal.fire({
                    icon: 'error',
                    title: 'Revert Failed',
                    html: `
                        <div style="text-align: center;">
                            <p style="color: #dc3545;">${error.message || 'An error occurred while reverting changes'}</p>
                        </div>
                    `,
                    confirmButtonColor: '#dc3545'
                });
                
                this.revertError = error.message;
            } finally {
                this.revertingShapefile = false;
            }
        }

    },
    
    watch: {
        // Watch for changes in proposal data and update map if needed
        'proposal.proposalgeometry_processed': {
            handler: function (newVal, oldVal) {
                if (newVal && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
                    // Map will update via prop watchers, but we can force a refresh if needed
                    this.refreshMapAfterProcessing();
                }
            },
            deep: true
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
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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

.process-btn {
    min-width: 160px;
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

/* Responsive adjustments */
@media (max-width: 768px) {
    .d-flex.align-items-center.flex-wrap {
        flex-direction: column;
        align-items: flex-start !important;
    }

    .uploaded-filename {
        margin-left: 0 !important;
        margin-top: 10px;
        max-width: 100%;
    }

    .ms-auto {
        margin-left: 0 !important;
        margin-top: 10px;
        width: 100%;
    }

    .revert-btn,
    .process-btn {
        width: 100%;
    }

    .d-flex.gap-2 {
        flex-direction: column;
        width: 100%;
    }
}
</style>
