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

                        <!-- Display uploaded filename with delete button -->
                        <div v-if="fileNameToDisplay" class="ms-2 uploaded-filename">
                            <i class="bi bi-file-earmark-zip me-1"></i>
                            <span class="text-muted">Uploaded:</span>
                            <strong class="ms-1">{{ fileNameToDisplay }}</strong>
                            
                            <!-- Delete button -->
                            <button 
                                class="btn btn-sm btn-link text-danger ms-2 p-0"
                                @click="confirmDeleteShapefile"
                                :disabled="uploadingShapefile || !hasShapefile"
                                :title="'Delete current shapefile'"
                            >
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>
                        
                        <!-- Process and Revert buttons -->
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
                    
                    <!-- Hidden file input for shapefile upload -->
                    <input 
                        type="file" 
                        ref="shapefileInput"
                        accept=".zip,.shp,.shx,.dbf,.prj"
                        :multiple="true"
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
                        Upload either:
                        <ul class="mt-1 mb-0 ps-3">
                            <li>A single <strong>.zip</strong> file containing all shapefile components</li>
                            <li>OR select multiple files: <strong>.shp, .shx, .dbf, .prj</strong> (select all at once)</li>
                        </ul>
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
import MapComponent from '@/components/common/component_map.vue';
import SnapshotDebugToggle from '@/components/common/SnapshotDebugToggle.vue';
import { v4 as uuid } from 'uuid';
import Swal from 'sweetalert2';
import moment from 'moment';

import { api_endpoints, helpers } from '@/utils/hooks';
//import {
//    owsQuery,
//    validateFeature,
//} from '@/components/common/map_functions.js';

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
            //owsQuery: owsQuery,
            //validateFeature: validateFeature,
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
            
            // Current user ID
            currentUserId: null,
            
            // Revert states
            revertingShapefile: false,
            revertError: null,

            // Pending upload for confirmation flow
            pendingUpload: null,

            // to force map re-render
            componentMapKey: 0, 
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
                    // Log for debugging
                    console.log('Returning shapefile_json with', vm.proposal.shapefile_json.features?.length, 'features');
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
        
        // to force map refresh when key changes
        mapKey: function() {
            // Combine relevant data that should trigger a map refresh
            return JSON.stringify({
                shapefile: this.proposal?.shapefile_json,
                processed: this.proposal?.proposalgeometry_processed,
                hist: this.proposal?.proposalgeometry_hist
            });
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
        
        // Get current user ID
        this.getCurrentUser();
    },
    mounted: function () {
        this.$emit('formMounted');
    },
    beforeDestroy: function () {
        // Cleanup if needed
    },
    methods: {
        handleProcessedGeometryUpdate(updatedGeoJSON) {
            // Update the proposal's processed geometry data
            // this.proposal.proposalgeometry_processed = updatedGeoJSON;
            // this.$emit('refreshFromResponse', this.proposal);
        },

        refreshFromResponse: function (data) {
            this.$emit('refreshFromResponse', data);
        },
        
        // Get current user
        getCurrentUser: async function () {
            try {
                // Try the correct user endpoint
                const response = await fetch('/api/users/current/');
                if (!response.ok) {
                    throw new Error('Failed to fetch user');
                }
                const data = await response.json();
                this.currentUserId = data.id;
            } catch (error) {
                console.error('Error getting current user:', error);
                
                // Fallback: try to get from the proposal submitter
                if (this.proposal && this.proposal.submitter_obj) {
                    this.currentUserId = this.proposal.submitter_obj.id;
                    console.log('Using submitter from proposal:', this.currentUserId);
                } else {
                    // Try to get from localStorage or session if available
                    const userStr = localStorage.getItem('user');
                    if (userStr) {
                        try {
                            const user = JSON.parse(userStr);
                            this.currentUserId = user.id;
                        } catch (e) {
                            console.error('Error parsing user from localStorage:', e);
                        }
                    }
                }
            }
        },
        
        // Shapefile Upload Methods
        triggerShapefileUpload: function () {
            this.$refs.shapefileInput.click();
        },

        handleShapefileUpload: function (event) {
            const files = event.target.files;
            if (!files || files.length === 0) {
                return;
            }

            // Store files for potential confirmation flow
            this.pendingUpload = files;

            // Check if there's an existing shapefile
            if (this.hasShapefile) {
                this.showReplaceConfirmation();
            } else {
                this.processUploadedFiles();
            }
        },

        showReplaceConfirmation: function () {
            Swal.fire({
                title: 'Replace Existing Shapefile?',
                html: `
                    <div style="text-align: left;">
                        <p>Uploading a new shapefile will:</p>
                        <ul style="margin-top: 5px;">
                            <li>Delete the current shapefile: <strong>${this.fileNameToDisplay || 'Unknown'}</strong></li>
                            <li>Clear all processed geometry data</li>
                            <li>Remove any generated polygons and cohorts</li>
                        </ul>
                        <p style="font-weight: bold; color: #dc3545; margin-top: 15px;">This action cannot be undone!</p>
                    </div>
                `,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Yes, Replace',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
            }).then((result) => {
                if (result.isConfirmed) {
                    this.processUploadedFiles(true);
                } else {
                    this.clearFileInput();
                    this.pendingUpload = null;
                }
            });
        },

        processUploadedFiles: async function (confirmed = false) {
            const files = this.pendingUpload;
            if (!files) return;

            // Reset previous upload state
            this.uploadSuccess = false;
            this.uploadError = null;
            this.processError = null;
            
            // Case 1: Single ZIP file
            if (files.length === 1 && files[0].name.toLowerCase().endsWith('.zip')) {
                this.selectedFileName = files[0].name;
                await this.uploadShapefile(files[0], confirmed);
                return;
            }

            // Case 2: Multiple shapefile components
            const shapefileComponents = this.validateShapefileComponents(files);
            if (shapefileComponents.valid) {
                // Use the .shp filename for display
                const shpFile = shapefileComponents.files.find(f => 
                    f.name.toLowerCase().endsWith('.shp')
                );
                this.selectedFileName = shpFile ? shpFile.name.replace('.shp', ' (components)') : 'Shapefile components';
                
                // Create a zip on the fly
                await this.createAndUploadShapefileZip(shapefileComponents.files, confirmed);
            } else {
                this.uploadError = shapefileComponents.error || 'Invalid file selection. Please select either a single .zip file OR all required shapefile components (.shp, .shx, .dbf, .prj)';
                this.clearFileInput();
                
                // Auto-clear error after 10 seconds
                setTimeout(() => {
                    this.uploadError = null;
                }, 10000);
            }
            
            this.pendingUpload = null;
        },

        validateShapefileComponents: function (files) {
            const allowedExtensions = ['.shp', '.shx', '.dbf', '.prj'];
            const requiredExtensions = ['.shp', '.shx', '.dbf']; // .prj is optional
            const fileMap = new Map();
            
            // Check each file extension
            for (let file of files) {
                const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
                if (!allowedExtensions.includes(ext)) {
                    return {
                        valid: false,
                        error: `Invalid file type: ${file.name}. Allowed: .shp, .shx, .dbf, .prj`
                    };
                }
                fileMap.set(ext, file);
            }
            
            // Check for required components
            const missingComponents = requiredExtensions.filter(ext => !fileMap.has(ext));
            if (missingComponents.length > 0) {
                return {
                    valid: false,
                    error: `Missing required shapefile components: ${missingComponents.join(', ')}`
                };
            }
            
            return {
                valid: true,
                files: Array.from(fileMap.values())
            };
        },

        createAndUploadShapefileZip: async function (files, confirmed = false) {
            this.uploadingShapefile = true;
            this.uploadProgress = 0;
            this.uploadStatus = 'Creating zip file...';
            
            try {
                // Use JSZip to create a zip file
                const JSZip = (await import('jszip')).default;
                const zip = new JSZip();
                
                // Add each file to the zip
                files.forEach(file => {
                    zip.file(file.name, file);
                });
                
                // Generate the zip file
                this.uploadStatus = 'Compressing files...';
                const content = await zip.generateAsync({ 
                    type: 'blob',
                    compression: 'DEFLATE',
                    compressionOptions: { level: 6 }
                }, (metadata) => {
                    // Update progress during compression
                    this.uploadProgress = Math.round(metadata.percent);
                    this.uploadStatus = `Compressing... ${this.uploadProgress}%`;
                });
                
                // Create a File object from the blob
                const zipFileName = `shapefile_${Date.now()}.zip`;
                const zipFile = new File([content], zipFileName, { type: 'application/zip' });
                
                // Upload the generated zip
                await this.uploadShapefile(zipFile, confirmed);
                
            } catch (error) {
                console.error('Error creating zip file:', error);
                this.uploadError = 'Failed to create zip file from components';
                this.uploadingShapefile = false;
                this.clearFileInput();
            }
        },

        clearFileInput: function () {
            if (this.$refs.shapefileInput) {
                this.$refs.shapefileInput.value = '';
                // For multiple file input, we need to clear differently
                if (this.$refs.shapefileInput.files) {
                    this.$refs.shapefileInput.files = null;
                }
            }
        },

        uploadShapefile: async function (file, confirmed = false) {
            this.uploadingShapefile = true;
            this.uploadProgress = 0;
            this.uploadStatus = 'Preparing upload...';
            this.uploadError = null;
            this.uploadSuccess = false;
            
            const formData = new FormData();
            formData.append('shapefile', file);
            formData.append('proposal_id', this.proposalId);
            formData.append('confirm_replace', confirmed ? 'true' : 'false');
            
            let progressInterval = null;
            
            try {
                const url = helpers.add_endpoint_join(
                    this.api_endpoints.proposal,
                    this.proposalId + '/upload_shapefile/'
                );
                
                const csrfToken = helpers.getCookie('csrftoken');
                
                // Simulate upload progress
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
                
                const data = await response.json();
                
                if (data.requires_confirmation) {
                    this.uploadingShapefile = false;
                    this.clearFileInput();
                    
                    const result = await Swal.fire({
                        title: 'Replace Existing Shapefile?',
                        html: `
                            <div style="text-align: left;">
                                <p>${data.message}</p>
                                <p>Existing file: <strong>${data.existing_filename}</strong></p>
                                <p style="font-weight: bold; color: #dc3545; margin-top: 15px;">This action cannot be undone!</p>
                            </div>
                        `,
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Yes, Replace',
                        cancelButtonText: 'Cancel',
                        confirmButtonColor: '#dc3545',
                    });
                    
                    if (result.isConfirmed) {
                        // Retry with confirmation
                        formData.set('confirm_replace', 'true');
                        this.uploadShapefile(file, true);
                    }
                    return;
                }
                
                this.uploadProgress = 100;
                this.uploadStatus = 'Upload complete, processing...';
                
                if (!response.ok) {
                    throw new Error(data.error || data.message || 'Upload failed');
                }
                
                if (data.success && data.proposal) {
                    this.uploadSuccess = true;
                    this.uploadStatus = 'Shapefile processed successfully!';
                    
                    // CRITICAL: Update the proposal data first
                    this.$emit('refreshFromResponse', data.proposal);
                    
                    // Wait for the data to propagate
                    await this.$nextTick();
                    
                    // Force map to refresh by incrementing the key
                    this.componentMapKey++;
                    
                    // Then trigger map refresh with multiple approaches
                    this.refreshMapAfterUpload();
                    
                    // Show success message
                    Swal.fire({
                        icon: 'success',
                        title: 'Upload Successful',
                        html: `
                            <div style="text-align: center;">
                                <p>${data.feature_count} features loaded from shapefile</p>
                            </div>
                        `,
                        timer: 2000,
                        showConfirmButton: false
                    });
                    
                    // Clear success message after 5 seconds
                    setTimeout(() => {
                        this.uploadSuccess = false;
                    }, 5000);
                } else {
                    throw new Error(data.message || 'Unexpected response from server');
                }
                
            } catch (error) {
                console.error('Error uploading shapefile:', error);
                
                if (progressInterval) {
                    clearInterval(progressInterval);
                }
                
                this.uploadError = error.message || 'Failed to upload shapefile';
                
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

        refreshMapAfterUpload: function () {
            console.log('Refreshing map after upload...');
            
            // Wait for Vue to update the DOM
            this.$nextTick(() => {
                // Approach 1: Direct map refresh method
                if (this.$refs.component_map) {
                    console.log('Calling forceToRefreshMap on component_map');
                    if (this.$refs.component_map.forceToRefreshMap) {
                        this.$refs.component_map.forceToRefreshMap();
                    }
                    
                    // Approach 2: If forceToRefreshMap doesn't exist, try to update layers directly
                    if (this.$refs.component_map.map) {
                        console.log('Direct map update - updating size');
                        this.$refs.component_map.map.updateSize();
                    }
                    
                    // Approach 3: Force map layer updates if available
                    if (this.$refs.component_map.layer1 && this.proposal.shapefile_json) {
                        console.log('Updating layer1 with new geometry');
                        this.$refs.component_map.updateLayer1(this.proposal.shapefile_json);
                    }
                    
                    // Approach 4: Emit event to map component
                    this.$refs.component_map.$emit('refresh-geometries');
                } else {
                    console.warn('component_map ref not available');
                }
                
                // Approach 5: Also try to refresh polygon cohort table
                this.refreshPolygonCohortTable();
            });
            
            // Additional refresh after a short delay to ensure everything is loaded
            setTimeout(() => {
                if (this.$refs.component_map && this.$refs.component_map.map) {
                    console.log('Delayed map update');
                    this.$refs.component_map.map.updateSize();
                    if (this.$refs.component_map.layer1 && this.proposal.shapefile_json) {
                        this.$refs.component_map.updateLayer1(this.proposal.shapefile_json);
                    }
                }
            }, 500);
        },

        refreshPolygonCohortTable: function () {
            console.log('Refreshing polygon cohort table from parent');
            if (this.$refs.component_map && this.$refs.component_map.$refs.polygonCohortTable) {
                this.$refs.component_map.$refs.polygonCohortTable.refreshData();
            } else {
                console.warn('PolygonCohortTable ref not found');
                setTimeout(() => {
                    const tableComponent = document.querySelector('[data-table="polygon-cohort"]');
                    if (tableComponent && tableComponent.__vue__) {
                        tableComponent.__vue__.refreshData();
                    }
                }, 500);
            }
        },

        confirmDeleteShapefile: function () {
            Swal.fire({
                title: 'Delete Shapefile?',
                html: `
                    <div style="text-align: left;">
                        <p>Are you sure you want to delete the current shapefile?</p>
                        <p>This will:</p>
                        <ul style="margin-top: 5px;">
                            <li>Permanently delete the file from the server</li>
                            <li>Clear all geometry data from the proposal</li>
                            <li>Remove any generated polygons and cohorts</li>
                        </ul>
                        <p style="font-weight: bold; color: #dc3545; margin-top: 15px;">This action cannot be undone!</p>
                    </div>
                `,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Yes, Delete',
                cancelButtonText: 'Cancel',
                confirmButtonColor: '#dc3545',
            }).then((result) => {
                if (result.isConfirmed) {
                    this.deleteShapefile();
                }
            });
        },

        deleteShapefile: async function () {
            this.uploadingShapefile = true;
            
            try {
                const url = helpers.add_endpoint_join(
                    this.api_endpoints.proposal,
                    this.proposalId + '/delete_shapefile/'
                );
                
                const csrfToken = helpers.getCookie('csrftoken');
                
                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        proposal_id: this.proposalId
                    })
                });
                
                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to delete shapefile');
                }
                
                const data = await response.json();
                
                if (data.success) {
                    // Clear local state
                    this.selectedFileName = '';
                    
                    // Update proposal data
                    if (data.proposal) {
                        this.$emit('refreshFromResponse', data.proposal);
                    }
                    
                    Swal.fire({
                        icon: 'success',
                        title: 'Deleted',
                        text: 'Shapefile deleted successfully',
                        timer: 2000,
                        showConfirmButton: false
                    });
                    
                    // Refresh map
                    this.refreshMapAfterProcessing();
                }
                
            } catch (error) {
                console.error('Error deleting shapefile:', error);
                
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: error.message || 'Failed to delete shapefile'
                });
            } finally {
                this.uploadingShapefile = false;
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
                showLoaderOnConfirm: true,
                preConfirm: () => {
                    const threshold = document.getElementById('threshold').value;
                    const thresholdValue = parseFloat(threshold);
                    
                    if (isNaN(thresholdValue) || thresholdValue < 0.1 || thresholdValue > 100) {
                        Swal.showValidationMessage('Threshold must be between 0.1 and 100');
                        return false;
                    }
                    
                    return { threshold: thresholdValue };
                }
            }).then((result) => {
                if (result.isConfirmed && result.value) {
                    this.processShapefile(result.value.threshold);
                }
            });
        },

        processShapefile: async function (threshold) {
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
                
                Swal.close();
                
                if (!response.ok) {
                    throw new Error(data.error || data.message || 'Failed to process shapefile');
                }
                
                if (data.success) {
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
                            confirmButtonColor: '#ffc107'
                        });
                    } else {
                        await Swal.fire({
                            icon: 'success',
                            title: 'Success',
                            html: `
                                <div style="text-align: center;">
                                    <p>${data.message || 'Shapefile processed successfully!'}</p>
                                    ${data.feature_count ? `<p style="font-size: 0.9em; color: #6c757d;">Features processed: ${data.feature_count}</p>` : ''}
                                    ${data.dump_info && data.dump_info.dump_filename ? `
                                        <hr style="margin: 10px 0;">
                                        <div style="font-size: 0.85em; color: #495057; text-align: left;">
                                            <p><strong>Database Export:</strong></p>
                                            <p>File: <code>${data.dump_info.dump_filename}</code></p>
                                            <p>Size: ${(data.dump_info.dump_size_bytes / 1024 / 1024).toFixed(2)} MB</p>
                                        </div>
                                    ` : ''}
                                </div>
                            `,
                            confirmButtonColor: '#28a745',
                            timer: 2000
                        });
                    }
                    
                    // Update the proposal data with the processed version
                    if (data.proposal) {
                        this.$emit('refreshFromResponse', data.proposal);
                    }
                    
                    // Refresh the map
                    this.refreshMapAfterProcessing();
                    
                } else {
                    throw new Error(data.message || 'Unknown error occurred');
                }
                
            } catch (error) {
                console.error('Error processing shapefile:', error);
                
                Swal.close();
                
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
            this.$nextTick(() => {
                if (this.$refs.component_map && this.$refs.component_map.forceToRefreshMap) {
                    setTimeout(() => {
                        this.$refs.component_map.forceToRefreshMap();
                    }, 500);
                }
            });
        },

        refreshPolygonCohortTable: function () {
            console.log('Refreshing polygon cohort table from parent');
            if (this.$refs.component_map && this.$refs.component_map.$refs.polygonCohortTable) {
                this.$refs.component_map.$refs.polygonCohortTable.refreshData();
            } else {
                console.warn('PolygonCohortTable ref not found');
                setTimeout(() => {
                    const tableComponent = document.querySelector('[data-table="polygon-cohort"]');
                    if (tableComponent && tableComponent.__vue__) {
                        tableComponent.__vue__.refreshData();
                    }
                }, 500);
            }
        },

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
        
        revertShapefileProcessing: async function () {
            this.revertingShapefile = true;
            this.revertError = null;
            
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
                
                Swal.close();
                
                if (!response.ok) {
                    throw new Error(data.error || data.message || 'Failed to revert changes');
                }
                
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
                        timer: 3000
                    });
                    
                    if (data.proposal) {
                        this.$emit('refreshFromResponse', data.proposal);
                    }
                    
                    this.refreshMapAfterProcessing();
                    this.refreshPolygonCohortTable();
                    
                } else {
                    throw new Error(data.message || 'Unknown error occurred');
                }
                
            } catch (error) {
                console.error('Error reverting changes:', error);
                
                Swal.close();
                
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
        'proposal.shapefile_json': {
            handler: function(newVal, oldVal) {
                if (newVal && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
                    console.log('Shapefile JSON changed, refreshing map');
                    this.refreshMapAfterUpload();
                }
            },
            deep: true
        },
        
        // Watch for changes in processed geometries
        'proposal.proposalgeometry_processed': {
            handler: function (newVal, oldVal) {
                if (newVal && JSON.stringify(newVal) !== JSON.stringify(oldVal)) {
                    console.log('Processed geometry changed, refreshing map');
                    this.refreshMapAfterProcessing();
                }
            },
            deep: true
        },
        
        // Watch map key to force re-render if needed
        mapKey: function() {
            console.log('Map key changed, refreshing map');
            this.componentMapKey++;
            this.refreshMapAfterUpload();
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
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-flex;
    align-items: center;
}

.uploaded-filename button {
    opacity: 0.6;
    transition: opacity 0.2s;
}

.uploaded-filename button:hover {
    opacity: 1;
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

.upload-info ul {
    margin-top: 5px;
    margin-bottom: 5px;
}

.process-btn {
    min-width: 160px;
}

.revert-btn {
    min-width: 100px;
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
