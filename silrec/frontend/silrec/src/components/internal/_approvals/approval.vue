<template>
    <div v-if="approval" id="internalApproval" class="container">
        <div class="row">
            <div class="col">
                <h3>
                    {{ approval.approval_type }}:
                    {{ approval.lodgement_number }}
                    <small
                        v-if="approval.original_leaselicence_number"
                        class="text-muted"
                    >
                        (Migrated from:
                        {{ approval.original_leaselicence_number }})</small
                    >
                </h3>
            </div>
        </div>
        <div class="row">
            <div class="col-md-3">
                <div class="row mb-2">
                    <CommsLogs
                        :comms_url="comms_url"
                        :logs_url="logs_url"
                        :comms_add_url="comms_add_url"
                        :disable_add_entry="false"
                    />
                </div>

                <StatusPanel :status="approval.status" />

                <div
                    v-if="
                        'Current (Pending Renewal Review)' == approval.status &&
                        approval.can_renew
                    "
                    class="row mt-2 mb-2"
                >
                    <div class="col">
                        <div class="card card-default">
                            <div class="card-header">Review Renewal</div>
                            <div class="card-body card-collapse">
                                <div class="mb-2">
                                    <button
                                        class="btn btn-primary btn-licensing"
                                        @click="renewalReview(true)"
                                    >
                                        Allow Renewal
                                    </button>
                                </div>
                                <div>
                                    <button
                                        class="btn btn-danger btn-licensing"
                                        @click="renewalReview(false)"
                                    >
                                        Disallow Renewal
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    v-if="showReviewInvoicingDetailsAction"
                    class="card card-default mt-2 mb-2"
                >
                    <div class="card-header">Review Invoicing Details</div>
                    <div class="card-body card-collapse">
                        <div class="mb-2">
                            <button
                                class="btn btn-primary btn-licensing"
                                @click="
                                    reviewInvoicingDetails(
                                        approval.id,
                                        approval.lodgement_number
                                    )
                                "
                            >
                                Review Invoicing Details
                            </button>
                        </div>
                    </div>
                </div>
                <div
                    v-if="showEditingInvoicingOptions"
                    class="card card-default sticky-top mt-2 mb-2"
                >
                    <div class="card-header">Edit Invoicing Details</div>
                    <div class="card-body card-collapse">
                        <div class="mb-2">
                            <textarea
                                ref="comment_text"
                                v-model="
                                    approval.invoicing_details.comment_text
                                "
                                class="form-control mb-3"
                                rows="4"
                                placeholder="Enter the reason you are editing the invoicing details here."
                            ></textarea>
                            <button
                                class="btn btn-primary btn-licensing"
                                @click.prevent="completeEditingInvoicing()"
                            >
                                Complete Editing
                            </button>
                        </div>
                        <div>
                            <button
                                class="btn btn-secondary btn-licensing"
                                @click.prevent="cancelEditingInvoicing()"
                            >
                                Cancel Editing
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-9">
                <BootstrapAlert type="success"
                    >This {{ approval.approval_type }} was approved by
                    <span class="fw-bold">{{ approval.approved_by }}</span> on
                    <span class="fw-bold">{{
                        new Date(approval.issue_date).toLocaleDateString()
                    }}</span>
                    <span>
                        ({{ approval.current_proposal_proposal_type }})</span
                    ></BootstrapAlert
                >
                <ul id="pills-tab" class="nav nav-pills" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button
                            id="pills-holder-tab"
                            class="nav-link active"
                            data-bs-toggle="pill"
                            data-bs-target="#pills-holder"
                            role="tab"
                            aria-controls="pills-holder"
                            aria-selected="true"
                        >
                            Applicant
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
                            aria-selected="true"
                        >
                            Details
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
                            aria-selected="true"
                            @click="tabClicked('map')"
                        >
                            Map
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button
                            id="pills-invoicing-tab"
                            class="nav-link"
                            data-bs-toggle="pill"
                            data-bs-target="#pills-invoicing"
                            role="tab"
                            aria-controls="pills-invoicing"
                            aria-selected="true"
                            @click="tabClicked('invoicing')"
                        >
                            Invoicing
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
                            aria-selected="true"
                        >
                            Related Items
                        </button>
                    </li>
                </ul>

                <div id="pills-tabContent" class="tab-content">
                    <div
                        id="pills-holder"
                        class="tab-pane fade show active"
                        role="tabpanel"
                        aria-labelledby="pills-holder-tab"
                    >
                        <Applicant
                            v-if="'individual' == approval.applicant_type"
                            id="approvalHolder"
                            :proposal-id="approval.current_proposal.id"
                            :proposal-applicant="
                                approval.current_proposal.proposal_applicant
                            "
                            :readonly="true"
                            :collapse-form-sections="false"
                            customer-type="holder"
                        />
                        <OrganisationApplicant
                            v-else
                            :org="approval.holder_obj"
                            :is-internal="true"
                        />
                    </div>

                    <div
                        id="pills-details"
                        class="tab-pane fade"
                        role="tabpanel"
                    >
                        <ApprovalDetails
                            :approval-details="approval"
                            label="License"
                        />
                    </div>

                    <div id="pills-map" class="tab-pane fade" role="tabpanel">
                        <MapComponent
                            v-if="loadMap"
                            ref="component_map"
                            :key="componentMapKey"
                            :context="approval"
                            :proposal-ids="[-1]"
                            :feature-collection="approval.geometry_objs"
                            style-by="assessor"
                            :filterable="false"
                            :drawable="false"
                            :editable="true"
                            level="internal"
                        />
                    </div>

                    <div
                        id="pills-invoicing"
                        class="tab-pane fade"
                        role="tabpanel"
                        aria-labelledby="pills-invoicing-tab"
                    >
                        <FormSection
                            class="mb-3"
                            :form-collapse="false"
                            label="Invoice Records"
                            index="invoicing_details"
                        >
                            <InvoicesTable
                                v-if="loadInvoices"
                                ref="invoice_table"
                                :approval-id="approval.id"
                                level="internal"
                            />
                        </FormSection>
                        <BootstrapSpinner
                            v-if="savingInvoicingDetails"
                            class="text-primary"
                        ></BootstrapSpinner>
                        <FormSection
                            v-if="loadInvoices && showEditingInvoicingOptions"
                            :form-collapse="false"
                            label="Edit Invoicing Details"
                            index="invoicing_details"
                        >
                            <InvoicingDetails
                                context="Approval"
                                :invoicing-details="approval.invoicing_details"
                                :start-date="approval.start_date"
                                :expiry-date="approval.expiry_date"
                                :issue-date="approval.issue_date"
                                :proposal-processing-status-id="
                                    approval.current_proposal_processing_status
                                "
                                :approval-type="approval.approval_type"
                                :proposal-type-code="
                                    approval.current_proposal_proposal_type_code
                                "
                                @update-invoicing-details="
                                    updateInvoicingDetails
                                "
                            />
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
                                :ajax-url="related_items_ajax_url"
                            />
                        </FormSection>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import CommsLogs from '@common-utils/comms_logs.vue';
import Applicant from '@/components/common/applicant.vue';
import OrganisationApplicant from '@/components/common/organisation_applicant.vue';
import InvoicesTable from '@/components/common/table_invoices.vue';
import FormSection from '@/components/forms/section_toggle.vue';
import { api_endpoints, constants, helpers, utils } from '@/utils/hooks';
import Swal from 'sweetalert2';
import TableRelatedItems from '@/components/common/table_related_items.vue';
import InvoicingDetails from '@/components/common/invoicing_details.vue';
import MapComponent from '@/components/common/component_map.vue';
import ApprovalDetails from '@/components/common/approval_details.vue';
import currency from 'currency.js';
export default {
    name: 'ApprovalDetail',
    components: {
        CommsLogs,
        FormSection,
        Applicant,
        OrganisationApplicant,
        InvoicesTable,
        TableRelatedItems,
        InvoicingDetails,
        MapComponent,
        ApprovalDetails,
    },
    data() {
        let vm = this;
        return {
            showExpired: false,
            moorings_datatable_id: 'moorings-datatable-' + uuid(),
            ml_vessels_datatable_id: 'ml-vessels-datatable-' + uuid(),
            ml_authorised_users_datatable_id:
                'ml-authorised-users-datatable-' + uuid(),
            loading: [],
            approval: null,
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            adBody: 'adBody' + uuid(),
            pBody: 'pBody' + uuid(),
            cBody: 'cBody' + uuid(),
            oBody: 'oBody' + uuid(),
            org: {
                address: {},
            },
            loadInvoices: false,
            savingInvoicingDetails: false,
            loadMap: false,
            // Filters
            logs_url: helpers.add_endpoint_json(
                api_endpoints.approvals,
                vm.$route.params.approval_id + '/action_log'
            ),
            comms_url: helpers.add_endpoint_json(
                api_endpoints.approvals,
                vm.$route.params.approval_id + '/comms_log'
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.approvals,
                vm.$route.params.approval_id + '/add_comms_log'
            ),
            related_items_ajax_url: helpers.add_endpoint_join(
                api_endpoints.approvals,
                vm.$route.params.approval_id + '/related_items'
            ),
            componentMapKey: 0,
        };
    },
    computed: {
        debug: function () {
            // eslint-disable-next-line no-prototype-builtins
            return this.$route.query.hasOwnProperty('debug') &&
                this.$route.query.debug === 'true'
                ? true
                : false;
        },
        isLoading: function () {
            return this.loading.length > 0;
        },
        showEditingInvoicingOptions: function () {
            return (
                this.approval &&
                constants.APPROVAL_STATUS.CURRENT_EDITING_INVOICING.TEXT ==
                    this.approval.status
            );
        },
        showReviewInvoicingDetailsAction: function () {
            return (
                this.approval &&
                [
                    constants.APPROVAL_STATUS.CURRENT.TEXT,
                    constants.APPROVAL_STATUS.CURRENT_PENDING_RENEWAL.TEXT,
                    constants.APPROVAL_STATUS.CURRENT_PENDING_RENEWAL_REVIEW
                        .TEXT,
                ].includes(this.approval.status) &&
                constants.PROPOSAL_STATUS.APPROVED.ID ==
                    this.approval.current_proposal_processing_status
            );
        },
    },
    created: async function () {
        const response = await fetch(
            helpers.add_endpoint_json(
                api_endpoints.approvals,
                this.$route.params.approval_id
            )
        );
        const resData = await response.json();
        this.approval = Object.assign({}, resData);
        this.approval.applicant_id = resData.applicant_id;
        if (this.approval.submitter.postal_address == null) {
            this.approval.submitter.postal_address = {};
        }
        if (window.location.hash == '#edit-invoicing') {
            this.showInvoicingTab();
        }
    },
    mounted: function () {},
    methods: {
        tabClicked: function (param) {
            if (param == 'invoicing') {
                this.loadInvoices = true;
            } else if (param === 'map') {
                this.loadMap = true;
                this.$nextTick(() => {
                    this.$refs.component_map.forceToRefreshMap();
                });
            }
        },
        showInvoicingTab: function () {
            this.$nextTick(function () {
                var tab_element = document.querySelector(
                    '#pills-invoicing-tab'
                );
                var tab = new bootstrap.Tab(tab_element);
                this.loadInvoices = true;
                tab.show();
                window.scrollTo(0, document.body.scrollHeight);
            });
        },
        formatDate: function (data) {
            return data ? moment(data).format(this.DATE_TIME_FORMAT) : '';
        },
        renewalReview: function (canBeRenewed) {
            let vm = this;
            let action = canBeRenewed ? 'Allow' : 'Disallow';
            let confirmButtonColour = canBeRenewed ? '#226fbb' : '#dc143c';
            Swal.fire({
                title: `${action} Renewal`,
                text: `You are about to ${action} renewal of approval ${vm.approval.lodgement_number}.`,
                icon: 'question',
                reverseButtons: true,
                showCancelButton: true,
                confirmButtonText: `${action} Renewal`,
                confirmButtonColor: `${confirmButtonColour}`,
            }).then((result) => {
                if (result.isConfirmed) {
                    let vm = this;
                    const requestOptions = {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ can_be_renewed: canBeRenewed }),
                    };
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.approvals,
                            vm.approval.id + '/review_renewal'
                        ),
                        requestOptions
                    ).then(
                        async (response) => {
                            const data = await response.json();
                            if (!response.ok) {
                                const error =
                                    (data && data.message) ||
                                    response.statusText;
                                console.error(error);
                                return Promise.reject(error);
                            }
                            let successMessage =
                                'The approval status has been reset to Current and will expire without being renewed.';
                            if (canBeRenewed) {
                                successMessage =
                                    'The approval holder has been notified that they may renew the approval.';
                            }
                            Swal.fire(
                                'Renewal Review Complete',
                                successMessage,
                                'success'
                            );
                            vm.approval = Object.assign({}, data);
                        },
                        (error) => {
                            console.error(error);
                        }
                    );
                }
            });
        },
        reviewInvoicingDetails: function (
            approval_id,
            // eslint-disable-next-line no-unused-vars
            approval_lodgement_number
        ) {
            let vm = this;
            Swal.fire({
                title: 'Approval Review Invoice Details',
                text: 'Are you sure you want to review the invoice details for this approval?',
                icon: 'question',
                showCancelButton: true,
                reverseButtons: true,
                confirmButtonText: 'Review Invoice Details',
                confirmButtonColor: '#226fbb',
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    let requestOptions = {
                        method: 'PATCH',
                    };
                    fetch(
                        helpers.add_endpoint_join(
                            api_endpoints.approvals,
                            approval_id + '/review_invoice_details/'
                        ),
                        requestOptions
                    ).then(
                        async (response) => {
                            const data = await response.json();
                            if (!response.ok) {
                                const error =
                                    (data && data.message) ||
                                    response.statusText;
                                console.error(error);
                                Promise.reject(error);
                            }
                            vm.approval = Object.assign({}, data);
                            vm.showInvoicingTab();
                        },
                        (error) => {
                            console.error(error);
                        }
                    );
                }
            });
        },
        updateInvoicingDetails: function (value) {
            this.approval.invoicing_details = value;
        },
        getGrossTurnoverChanges: function () {
            if (
                this.approval.invoicing_details.charge_method_key ==
                constants.CHARGE_METHODS.PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE
                    .ID
            ) {
                return this.getGrossTurnoverChangesAdvance();
            } else if (
                this.approval.invoicing_details.charge_method_key ==
                constants.CHARGE_METHODS.PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS
                    .ID
            ) {
                return this.getGrossTurnoverChangesArrears();
            }
            return [];
        },
        getGrossTurnoverChangesAdvance: function () {
            let annualTurnoverChanges = [];
            let annualTurnoverDiscrepencyChanges = [];
            for (
                let i = 0;
                i <
                this.approval.invoicing_details.gross_turnover_percentages
                    .length;
                i++
            ) {
                let gross_turnover_percentage =
                    this.approval.invoicing_details.gross_turnover_percentages[
                        i
                    ];
                let financial_year_has_passed = helpers.financialYearHasPassed(
                    gross_turnover_percentage.financial_year
                );

                // Invoices that need to be generated when there is just an estimate of GTO
                if (
                    financial_year_has_passed &&
                    !gross_turnover_percentage.estimate_locked &&
                    gross_turnover_percentage.estimated_gross_turnover !=
                        null &&
                    gross_turnover_percentage.gross_turnover == null
                ) {
                    let invoice_amount = currency(
                        gross_turnover_percentage.estimated_gross_turnover
                    ).multiply(gross_turnover_percentage.percentage / 100);
                    annualTurnoverChanges.push({
                        year: gross_turnover_percentage.year,
                        percentage: gross_turnover_percentage.percentage,
                        estimated_gross_turnover:
                            gross_turnover_percentage.estimated_gross_turnover,
                        gross_turnover:
                            gross_turnover_percentage.gross_turnover,
                        invoice_amount: invoice_amount,
                    });
                }
                // Invoices that needs to be generated when there is both an estimate and an actual GTO
                if (
                    financial_year_has_passed &&
                    !gross_turnover_percentage.locked &&
                    gross_turnover_percentage.discrepency != null &&
                    gross_turnover_percentage.discrepency != 0
                ) {
                    let invoice_amount = 0;
                    if (
                        gross_turnover_percentage.estimated_gross_turnover !=
                        gross_turnover_percentage.gross_turnover
                    ) {
                        invoice_amount = currency(
                            gross_turnover_percentage.discrepency_invoice_amount
                        );
                    }

                    annualTurnoverDiscrepencyChanges.push({
                        year: gross_turnover_percentage.year,
                        percentage: gross_turnover_percentage.percentage,
                        estimated_gross_turnover:
                            gross_turnover_percentage.estimated_gross_turnover,
                        gross_turnover:
                            gross_turnover_percentage.gross_turnover,
                        discrepency:
                            gross_turnover_percentage.gross_turnover -
                            gross_turnover_percentage.estimated_gross_turnover,
                        invoice_amount: invoice_amount,
                    });
                }
            }
            return {
                annualTurnoverChanges: annualTurnoverChanges,
                annualTurnoverDiscrepencyChanges:
                    annualTurnoverDiscrepencyChanges,
                quarterlyTurnoverChanges: [],
                count:
                    annualTurnoverChanges.length +
                    annualTurnoverDiscrepencyChanges.length,
            };
        },
        getGrossTurnoverChangesArrears: function () {
            let annualTurnoverChanges = [];
            let quarterlyTurnoverChanges = [];
            for (
                let i = 0;
                i <
                this.approval.invoicing_details.gross_turnover_percentages
                    .length;
                i++
            ) {
                let gross_turnover_percentage =
                    this.approval.invoicing_details.gross_turnover_percentages[
                        i
                    ];
                if (
                    !gross_turnover_percentage.locked &&
                    gross_turnover_percentage.gross_turnover != null &&
                    gross_turnover_percentage.discrepency != null &&
                    gross_turnover_percentage.discrepency != 0
                ) {
                    annualTurnoverChanges.push({
                        year: gross_turnover_percentage.year,
                        percentage: gross_turnover_percentage.percentage,
                        gross_turnover:
                            gross_turnover_percentage.gross_turnover,
                        discrepency: gross_turnover_percentage.discrepency,
                        invoice_amount:
                            gross_turnover_percentage.discrepency_invoice_amount,
                    });
                }
                let quarters = gross_turnover_percentage.quarters;
                for (let j = 0; j < quarters.length; j++) {
                    if (
                        !quarters[j].locked &&
                        quarters[j].gross_turnover != null
                    ) {
                        quarterlyTurnoverChanges.push({
                            year: this.approval.invoicing_details
                                .gross_turnover_percentages[i].year,
                            quarter:
                                this.approval.invoicing_details
                                    .gross_turnover_percentages[i].quarters[j]
                                    .quarter,
                            percentage:
                                this.approval.invoicing_details
                                    .gross_turnover_percentages[i].percentage,
                            gross_turnover:
                                this.approval.invoicing_details
                                    .gross_turnover_percentages[i].quarters[j]
                                    .gross_turnover,
                        });
                    }
                }
            }
            return {
                annualTurnoverChanges: annualTurnoverChanges,
                quarterlyTurnoverChanges: quarterlyTurnoverChanges,
                count:
                    annualTurnoverChanges.length +
                    quarterlyTurnoverChanges.length,
            };
        },
        completeEditingInvoicing: function () {
            if (
                !this.approval.invoicing_details.comment_text ||
                this.approval.invoicing_details.comment_text.trim() == ''
            ) {
                this.$refs.comment_text.focus();
                return;
            }
            let changes = this.getGrossTurnoverChanges();
            if (changes.count > 0) {
                let quarterlyChangesHtml = '';
                let annualChangesHtml = '';
                let annualChangesDiscrepencyHtml = '';
                if (changes.quarterlyTurnoverChanges.length > 0) {
                    quarterlyChangesHtml = this.getQuarterlyTurnoverChangesHtml(
                        changes.quarterlyTurnoverChanges
                    );
                }
                if (changes.annualTurnoverChanges.length > 0) {
                    annualChangesHtml = this.getAnnualTurnoverChangesHtml(
                        changes.annualTurnoverChanges
                    );
                }
                if (
                    changes.annualTurnoverDiscrepencyChanges &&
                    changes.annualTurnoverDiscrepencyChanges.length > 0
                ) {
                    annualChangesDiscrepencyHtml =
                        this.getAnnualTurnoverChangesAdvanceDiscrepencyHtml(
                            changes.annualTurnoverDiscrepencyChanges
                        );
                }

                swal.fire({
                    title: 'Confirm Gross Turnover Amounts',
                    html:
                        '<p class="mb-3">You have entered the following gross turnover amounts for <strong>Approval: ' +
                        this.approval.lodgement_number +
                        '</strong>:</p>' +
                        quarterlyChangesHtml +
                        '<br/>' +
                        annualChangesHtml +
                        '<br/>' +
                        annualChangesDiscrepencyHtml +
                        '<p>When you click the confirm button, invoice records will be generated with the amounts listed.</p>' +
                        '<p class="fs-6 text-muted">* An oracle invoice must be attached to each invoice record before the request for payment will be sent.</p>',
                    icon: 'info',
                    imageWidth: 100,
                    customClass: 'swal-extra-wide',
                    reverseButtons: true,
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    confirmButtonText: 'Confirm Gross Turnover Amounts',
                }).then((result) => {
                    if (result.isConfirmed) {
                        this.saveInvoicingDetails();
                    }
                });
            } else {
                this.saveInvoicingDetails();
            }
        },
        getQuarterlyTurnoverChangesHtml: function (turnoverChanges) {
            if (turnoverChanges.length == 0) {
                return '';
            }
            let changesHtml = '';
            changesHtml = `<div class="mb-3 float-left">Quarterly Turnover Amounts</div>`;
            changesHtml += '<table class="table table-sm table-striped">';
            changesHtml +=
                '<thead><tr><th>Financial Year</th><th>Quarter</th><th>Percentage</th><th>Gross Turnover</th><th>Invoice Amount</th></tr></thead><tbody>';
            for (let i = 0; i < turnoverChanges.length; i++) {
                let invoice_amount = currency(
                    turnoverChanges[i].gross_turnover
                ).multiply(turnoverChanges[i].percentage / 100);

                changesHtml += `<tr><td>${turnoverChanges[i].year - 1}-${
                    turnoverChanges[i].year
                }</td><td>Q${turnoverChanges[i].quarter}</td><td>${
                    turnoverChanges[i].percentage
                }%</td><td>$${currency(
                    turnoverChanges[i].gross_turnover
                )}</td><td>$${invoice_amount}</td></tr>`;
            }
            changesHtml += '</tbody></table>';
            return changesHtml;
        },
        getAnnualTurnoverChangesHtml: function (turnoverChanges) {
            if (
                this.approval.invoicing_details.charge_method_key ==
                constants.CHARGE_METHODS.PERCENTAGE_OF_GROSS_TURNOVER_IN_ADVANCE
                    .ID
            ) {
                return this.getAnnualTurnoverChangesAdvanceHtml(
                    turnoverChanges
                );
            } else if (
                this.approval.invoicing_details.charge_method_key ==
                constants.CHARGE_METHODS.PERCENTAGE_OF_GROSS_TURNOVER_IN_ARREARS
                    .ID
            ) {
                return this.getAnnualTurnoverChangesArrearsHtml(
                    turnoverChanges
                );
            }
        },
        getAnnualTurnoverChangesAdvanceHtml: function (turnoverChanges) {
            if (turnoverChanges.length == 0) {
                return '';
            }

            let changesHtml = '';
            changesHtml = `<div class="mb-3 float-left">Annual Turnover Estimates</div>`;
            changesHtml += '<table class="table table-sm table-striped">';
            changesHtml +=
                '<thead><tr><th>Financial Year</th><th>Percentage</th><th>Estimated Gross Turnover</th><th>Actual Gross Turnover</th><th>Invoice Amount</th></tr></thead><tbody>';
            for (let i = 0; i < turnoverChanges.length; i++) {
                let gross_turnover = 'Not Yet Available';
                if (
                    turnoverChanges[i].gross_turnover &&
                    turnoverChanges[i].gross_turnover > 0
                ) {
                    gross_turnover = `$${currency(
                        turnoverChanges[i].gross_turnover
                    )}`;
                }
                changesHtml += `<tr><td>${turnoverChanges[i].year - 1}-${
                    turnoverChanges[i].year
                }</td><td>${turnoverChanges[i].percentage}%</td><td>$${currency(
                    turnoverChanges[i].estimated_gross_turnover
                )}</td><td>${gross_turnover}</td><td>$${
                    turnoverChanges[i].invoice_amount
                }</td></tr>`;
            }
            changesHtml += '</tbody></table>';
            return changesHtml;
        },
        getAnnualTurnoverChangesAdvanceDiscrepencyHtml: function (
            turnoverChanges
        ) {
            if (turnoverChanges.length == 0) {
                return '';
            }

            let changesHtml = '';
            changesHtml = `<div class="mb-3 float-left">Annual Turnover Discrepencies</div>`;
            changesHtml += '<table class="table table-sm table-striped">';
            changesHtml +=
                '<thead><tr><th>Financial Year</th><th>Percentage</th><th>Discrepency</th><th>Invoice Amount</th></tr></thead><tbody>';
            for (let i = 0; i < turnoverChanges.length; i++) {
                let suffix = 'Debit';
                let discrepencyClass = 'danger';
                if (turnoverChanges[i].invoice_amount < 0) {
                    suffix = 'Credit';
                    discrepencyClass = 'success';
                }
                changesHtml += `<tr><td>${turnoverChanges[i].year - 1}-${
                    turnoverChanges[i].year
                }</td><td>${turnoverChanges[i].percentage}%</td><td>$${
                    turnoverChanges[i].discrepency
                }</td><td class="text-${discrepencyClass}">$${Math.abs(
                    turnoverChanges[i].invoice_amount
                )} ${suffix}</td></tr>`;
            }
            changesHtml += '</tbody></table>';
            return changesHtml;
        },
        getAnnualTurnoverChangesArrearsHtml: function (turnoverChanges) {
            if (turnoverChanges.length == 0) {
                return '';
            }

            let changesHtml = '';
            changesHtml = `<div class="mb-3 float-left">Annual Turnover Discrepencies</div>`;
            changesHtml += '<table class="table table-sm table-striped">';
            changesHtml +=
                '<thead><tr><th>Financial Year</th><th>Percentage</th><th>Discrepency</th><th>Invoice Amount</th></tr></thead><tbody>';
            for (let i = 0; i < turnoverChanges.length; i++) {
                let suffix = 'Debit';
                let discrepencyClass = 'danger';
                if (turnoverChanges[i].invoice_amount < 0) {
                    suffix = 'Credit';
                    discrepencyClass = 'success';
                }
                changesHtml += `<tr><td>${turnoverChanges[i].year - 1}-${
                    turnoverChanges[i].year
                }</td><td>${turnoverChanges[i].percentage}%</td><td>$${currency(
                    turnoverChanges[i].discrepency
                )}</td><td class="text-${discrepencyClass}">$${Math.abs(
                    turnoverChanges[i].invoice_amount
                )} ${suffix}</td></tr>`;
            }
            changesHtml += '</tbody></table>';
            return changesHtml;
        },
        getTotalOfFinancialQuarters(year) {
            var gross_turnover_percentage =
                this.approval.invoicing_details.gross_turnover_percentages.find(
                    (item) => item.year == year
                );
            if (!gross_turnover_percentage) {
                return 0;
            }
            return gross_turnover_percentage.quarters.reduce(function (a, b) {
                return a + b['gross_turnover'];
            }, 0);
        },
        saveInvoicingDetails: function () {
            this.savingInvoicingDetails = true;
            const requestOptions = {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.approval.invoicing_details),
            };
            utils
                .fetchUrl(
                    api_endpoints.invoicing_details +
                        `${this.approval.invoicing_details.id}/complete_editing/`,
                    requestOptions
                )
                .then((data) => {
                    swal.fire({
                        title: 'Invoicing Details Saved',
                        text: 'The invoicing details have been saved.',
                        icon: 'success',
                        confirmButtonText: 'OK',
                        confirmButtonColor: '#3085d6',
                    });
                    this.approval = Object.assign({}, data);
                    this.$refs.invoice_table.$refs.invoices_datatable.vmDataTable.draw();
                })
                .catch((error) => {
                    Swal.fire({
                        title: 'Error Saving Invoicing Details',
                        text: error,
                        icon: 'error',
                    });
                })
                .finally(() => {
                    this.savingInvoicingDetails = false;
                });
        },
        cancelEditingInvoicing: function () {
            let vm = this;
            Swal.fire({
                title: 'Cancel Editing Invoicing Details',
                text: 'Are you sure you want to cancel editing invoicing details (any unsaved changes may be lost)?',
                icon: 'question',
                showCancelButton: true,
                reverseButtons: true,
                confirmButtonText: 'Cancel Editing',
                cancelButtonText: 'Continue Editing',
                confirmButtonColor: '#226fbb',
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    let requestOptions = {
                        method: 'PATCH',
                    };
                    fetch(
                        helpers.add_endpoint_join(
                            api_endpoints.approvals,
                            vm.approval.id + '/cancel_editing_invoicing/'
                        ),
                        requestOptions
                    ).then(
                        async (response) => {
                            const data = await response.json();
                            if (!response.ok) {
                                const error =
                                    (data && data.message) ||
                                    response.statusText;
                                console.error(error);
                                Promise.reject(error);
                            }
                            vm.approval = Object.assign({}, data);
                        },
                        (error) => {
                            console.error(error);
                        }
                    );
                }
            });
        },
    },
};
</script>
<style scoped>
.sticky-top {
    top: 0.5em;
}
</style>
