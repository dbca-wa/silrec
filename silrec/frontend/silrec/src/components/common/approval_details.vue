<template lang="html">
    <div class="container m-0 p-0">
        <div class="row">
            <div id="approval-details" class="col-md-12">
                <FormSection
                    :form-collapse="false"
                    :label="label"
                    index="fs-details-details"
                >
                    <div class="container">
                        <div class="row">
                            <div class="col-6">
                                <form
                                    v-if="approval_details.approval_type"
                                    class="form-horizontal mb-2"
                                >
                                    <div class="mb-3 row">
                                        <label
                                            for="txt-approval-type"
                                            class="col-6 col-form-label"
                                            >Approval Type</label
                                        >
                                        <div class="col-6">
                                            <input
                                                id="txt-approval-type"
                                                v-model="
                                                    approval_details.approval_type
                                                "
                                                type="text"
                                                class="form-control"
                                                name="ApprovalType"
                                                :readonly="true"
                                            />
                                        </div>
                                    </div>
                                </form>
                            </div>

                            <div
                                v-if="Object.keys(approval_details).length > 0"
                                class="col-6"
                            >
                                <form
                                    v-if="approval_details.licence_document"
                                    class="form-horizontal mb-2"
                                >
                                    <div class="mb-3 row">
                                        <label
                                            for="txt-license-document"
                                            class="col-6 col-form-label pull-right"
                                            >{{
                                                approval_details.approval_type
                                            }}</label
                                        >

                                        <div class="col-6 col-form-label">
                                            <span
                                                v-if="
                                                    approval_details.licence_document.endsWith(
                                                        '.pdf'
                                                    )
                                                "
                                                class="fa fa-file-pdf form-label"
                                                style="color: red"
                                            >
                                                &nbsp;
                                            </span>
                                            <span
                                                v-else
                                                class="fa fa-file"
                                                style="color: red"
                                            >
                                                &nbsp;
                                            </span>
                                            <a
                                                id="txt-license-document"
                                                target="_blank"
                                                :href="
                                                    approval_details.licence_document
                                                "
                                                class="form-label pull-left"
                                                >Approval.pdf</a
                                            >
                                        </div>
                                    </div>
                                </form>
                                <BootstrapAlert
                                    v-else
                                    class="alert alert-danger mb-0"
                                    role="alert"
                                    icon="exclamation-triangle-fill"
                                >
                                    NO LICENSE DOCUMENT
                                </BootstrapAlert>
                            </div>
                        </div>

                        <form
                            v-if="approval_details.renewed_from"
                            class="form-horizontal mb-2"
                        >
                            <div class="mb-3 row">
                                <label
                                    for="txt-start-date"
                                    class="col-3 col-form-label"
                                    >Renewed From</label
                                >
                                <div class="col-3">
                                    <a
                                        :href="
                                            '/internal/approval/' +
                                            approval_details.renewed_from_id
                                        "
                                        >{{ approval_details.renewed_from }}</a
                                    >
                                </div>
                            </div>
                        </form>

                        <form
                            v-if="approval_details.start_date"
                            class="form-horizontal mb-2"
                        >
                            <div class="mb-3 row">
                                <label
                                    for="txt-start-date"
                                    class="col-3 col-form-label"
                                    >Commencement</label
                                >
                                <div class="col-3">
                                    <input
                                        id="txt-start-date"
                                        v-model="approval_details.start_date"
                                        type="text"
                                        class="form-control"
                                        name="StartDate"
                                        :readonly="true"
                                    />
                                </div>
                            </div>
                        </form>

                        <form
                            v-if="approval_details.expiry_date"
                            class="form-horizontal mb-2"
                        >
                            <div class="mb-3 row">
                                <label
                                    for="txt-expiry-date"
                                    class="col-3 col-form-label"
                                    >Expiry</label
                                >
                                <div class="col-3">
                                    <input
                                        id="txt-expiry-date"
                                        v-model="approval_details.expiry_date"
                                        type="text"
                                        class="form-control"
                                        name="ExpiryDate"
                                        :readonly="true"
                                    />
                                </div>
                            </div>
                        </form>

                        <GisDataDetails
                            :selected-data="externalApprovalGisData"
                            :searchable="false"
                            :readonly="true"
                            placeholder="N/A"
                            @update:selected-data="
                                approval_details.gis_data = $event // Update gis data example
                            "
                        />
                    </div>
                </FormSection>
            </div>
        </div>
    </div>
</template>
<script>
import FormSection from '@/components/forms/section_toggle.vue';
import GisDataDetails from '@/components/common/gis_data_details.vue';

export default {
    name: 'ApprovalDetails',
    components: {
        FormSection,
        GisDataDetails,
    },
    props: {
        approvalDetails: {
            type: Object,
            default() {
                return {};
            },
        },
        label: {
            type: String,
            required: false,
            default: 'Details',
        },
    },
    data: function () {
        return {
            approval_details: {},
        };
    },
    computed: {
        externalApprovalGisData() {
            let properties = [
                'regions',
                'districts',
                'lgas',
                'names',
                'categories',
                // 'identifiers',
                // 'vestings',
                // 'acts',
                // 'tenures',
            ];

            if (this.approval_details.gis_data === undefined) return {};

            // Return a GIS data dictionary of only the properties we want
            return Object.fromEntries(
                Object.entries(
                    JSON.parse(JSON.stringify(this.approval_details.gis_data))
                ).filter(([k]) => properties.includes(k))
            );
        },
    },
    mounted: function () {
        let vm = this;
        vm.$nextTick(() => {
            vm.approval_details = Object.assign({}, vm.approvalDetails);
        });
    },
};
</script>
