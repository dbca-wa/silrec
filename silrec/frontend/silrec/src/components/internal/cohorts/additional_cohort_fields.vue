<template>
    <div class="additional-cohort-fields">
        <div v-if="$route.query.debug?.toLowerCase() === 'true'">
            src/components/internal/cohorts/additional_cohort_fields.vue
        </div>
        <div class="row">
            <!-- Operation Information -->
            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="opId" class="form-label">Operation ID</label>
                    <input
                        id="opId"
                        v-model.number="formData.op_id"
                        type="number"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>

            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="opDate" class="form-label"
                        >Operation Date</label
                    >
                    <input
                        id="opDate"
                        v-model="formData.op_date"
                        type="datetime-local"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="yearLastCut" class="form-label"
                        >Year Last Cut</label
                    >
                    <input
                        id="yearLastCut"
                        v-model.number="formData.year_last_cut"
                        type="number"
                        min="1900"
                        :max="new Date().getFullYear()"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>

            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="pctArea" class="form-label"
                        >Percentage Area</label
                    >
                    <input
                        id="pctArea"
                        v-model.number="formData.pct_area"
                        type="number"
                        min="0"
                        max="100"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>
        </div>

        <!-- Regeneration Information -->
        <div class="row">
            <div class="col-md-4">
                <div class="form-group mb-3">
                    <label for="regenDate" class="form-label"
                        >Regeneration Date</label
                    >
                    <input
                        id="regenDate"
                        v-model="formData.regen_date"
                        type="datetime-local"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>

            <div class="col-md-4">
                <div class="form-group mb-3">
                    <label for="regenDate2" class="form-label"
                        >Secondary Regeneration Date</label
                    >
                    <input
                        id="regenDate2"
                        v-model="formData.regen_date2"
                        type="datetime-local"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>

            <div class="col-md-4">
                <div class="form-group mb-3">
                    <label for="completeDate" class="form-label"
                        >Complete Date</label
                    >
                    <input
                        id="completeDate"
                        v-model="formData.complete_date"
                        type="datetime-local"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label class="form-check-label">
                        <input
                            v-model="formData.regen_done"
                            type="checkbox"
                            class="form-check-input"
                            :disabled="readOnly"
                            @change="markChanged"
                        />
                        Regeneration Values Calculated
                    </label>
                </div>
            </div>

            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label class="form-check-label">
                        <input
                            v-model="formData.treatments"
                            type="checkbox"
                            class="form-check-input"
                            :disabled="readOnly"
                            @change="markChanged"
                        />
                        Treatments Inserted
                    </label>
                </div>
            </div>
        </div>

        <!-- Stocking Information -->
        <div class="row">
            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="residSpha" class="form-label"
                        >Residual SPHA</label
                    >
                    <input
                        id="residSpha"
                        v-model.number="formData.resid_spha"
                        type="number"
                        min="0"
                        step="0.1"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>

            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="herbicideAppSpec" class="form-label"
                        >Herbicide Application</label
                    >
                    <input
                        id="herbicideAppSpec"
                        v-model="formData.herbicide_app_spec"
                        type="text"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>
        </div>

        <!-- Additional Fields -->
        <div class="row">
            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="vrp" class="form-label"
                        >Vegetation Retention Patch</label
                    >
                    <input
                        id="vrp"
                        v-model.number="formData.vrp"
                        type="number"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>

            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="vrpTotArea" class="form-label"
                        >VRP Total Area (ha)</label
                    >
                    <input
                        id="vrpTotArea"
                        v-model.number="formData.vrp_tot_area"
                        type="number"
                        min="0"
                        step="0.1"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label for="stand" class="form-label">Stand</label>
                    <input
                        id="stand"
                        v-model="formData.stand"
                        type="text"
                        class="form-control"
                        :readonly="readOnly"
                        @input="markChanged"
                    />
                </div>
            </div>

            <div class="col-md-6">
                <div class="form-group mb-3">
                    <label class="form-check-label">
                        <input
                            v-model="formData.extra_info"
                            type="checkbox"
                            class="form-check-input"
                            :disabled="readOnly"
                            @change="markChanged"
                        />
                        Extra Info Required
                    </label>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'AdditionalCohortFields',
    props: {
        cohortData: {
            type: Object,
            required: true,
        },
        readOnly: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            formData: {},
            hasChanges: false,
            initialData: {},
        };
    },
    mounted() {
        this.initializeForm();
    },
    methods: {
        initializeForm() {
            if (!this.cohortData || !this.cohortData.cohort_id) return;

            this.formData = {
                op_id: this.cohortData.op_id || null,
                op_date: this.formatDateTimeForInput(this.cohortData.op_date),
                pct_area: this.cohortData.pct_area || null,
                year_last_cut: this.cohortData.year_last_cut || null,
                treatments: !!this.cohortData.treatments,
                regen_date: this.formatDateTimeForInput(
                    this.cohortData.regen_date
                ),
                regen_date2: this.formatDateTimeForInput(
                    this.cohortData.regen_date2
                ),
                regen_done: !!this.cohortData.regen_done,
                complete_date: this.formatDateTimeForInput(
                    this.cohortData.complete_date
                ),
                resid_spha: this.cohortData.resid_spha || null,
                herbicide_app_spec: this.cohortData.herbicide_app_spec || '',
                vrp: this.cohortData.vrp || null,
                vrp_tot_area: this.cohortData.vrp_tot_area || null,
                extra_info: !!this.cohortData.extra_info,
                stand: this.cohortData.stand || '',
            };

            this.initialData = JSON.parse(JSON.stringify(this.formData));
            this.hasChanges = false;
        },

        formatDateTimeForInput(dateTimeString) {
            if (!dateTimeString) return '';
            try {
                const date = new Date(dateTimeString);
                return isNaN(date.getTime())
                    ? ''
                    : date.toISOString().slice(0, 16);
            } catch (error) {
                return '';
            }
        },

        formatDateTimeForAPI(dateTimeString) {
            if (!dateTimeString) return null;
            try {
                const date = new Date(dateTimeString);
                return isNaN(date.getTime()) ? null : date.toISOString();
            } catch (error) {
                return null;
            }
        },

        getFormDataForAPI() {
            const apiData = { ...this.formData };
            const dateFields = [
                'op_date',
                'regen_date',
                'regen_date2',
                'complete_date',
            ];
            dateFields.forEach((field) => {
                apiData[field] = this.formatDateTimeForAPI(apiData[field]);
            });
            return apiData;
        },

        markChanged() {
            if (this.readOnly) return;
            this.hasChanges = true;
            this.$emit('field-changed');
        },

        checkForChanges() {
            const currentData = JSON.stringify(this.formData);
            const initialData = JSON.stringify(this.initialData);
            this.hasChanges = currentData !== initialData;
            return this.hasChanges;
        },

        resetChangeTracking() {
            this.initialData = JSON.parse(JSON.stringify(this.formData));
            this.hasChanges = false;
        },
    },
    watch: {
        cohortData: {
            handler(newData) {
                this.initializeForm();
            },
            immediate: true,
            deep: true,
        },
    },
};
</script>
