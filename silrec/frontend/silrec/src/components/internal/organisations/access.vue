<template>
    <div id="internalOrgAccess" class="container">
        <div v-if="access" class="row">
            <h3>Organisation Access Request: {{ access.lodgement_number }}</h3>
            <div class="col-md-3">
                <CommsLogs
                    :comms_url="comms_url"
                    :logs_url="logs_url"
                    :comms_add_url="comms_add_url"
                    :disable_add_entry="false"
                />
                <div class="row">
                    <div class="col">
                        <div class="card card-default mt-2">
                            <div class="card-header">Workflow</div>
                            <div class="card-body card-collapse">
                                <div class="row">
                                    <div class="col-sm-12">
                                        <strong>Status</strong><br />
                                        {{ access.status }}
                                    </div>
                                    <div class="col-sm-12 top-buffer-s">
                                        <strong>Currently assigned to</strong
                                        ><br />
                                        <div class="form-group">
                                            <select
                                                v-show="isLoading"
                                                class="form-select"
                                            >
                                                <option value="">
                                                    Loading...
                                                </option>
                                            </select>
                                            <select
                                                v-if="!isLoading"
                                                v-model="
                                                    access.assigned_officer
                                                "
                                                :disabled="
                                                    isFinalised ||
                                                    !is_organisation_access_officer
                                                "
                                                class="form-select"
                                                @change="assignTo"
                                            >
                                                <option value="null">
                                                    Unassigned
                                                </option>
                                                <option
                                                    v-for="member in members"
                                                    :key="member.id"
                                                    :value="member.id"
                                                >
                                                    {{ member.name }}
                                                </option>
                                            </select>
                                            <a
                                                v-if="
                                                    !isFinalised &&
                                                    is_organisation_access_officer &&
                                                    access.assigned_officer !=
                                                        profile.id
                                                "
                                                class="actionBtn pull-right"
                                                @click.prevent="assignMyself()"
                                                >Assign to me</a
                                            >
                                        </div>
                                    </div>
                                    <div
                                        v-if="
                                            !isFinalised &&
                                            is_organisation_access_officer &&
                                            current_user_is_assigned()
                                        "
                                        class="col-sm-12 top-buffer-s"
                                    >
                                        <strong>Action</strong><br />
                                        <button
                                            class="btn btn-primary"
                                            @click.prevent="acceptRequest()"
                                        >
                                            Accept</button
                                        ><br />
                                        <button
                                            class="btn btn-primary top-buffer-s"
                                            @click.prevent="declineRequest()"
                                        >
                                            Decline
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-9">
                <FormSection
                    :form-collapse="false"
                    label="Organisation Access Request"
                    index="organisation-access-request"
                >
                    <div class="row">
                        <div class="col-sm-12">
                            <form class="form-horizontal" name="access_form">
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >Requested by:</label
                                    >
                                    <div class="col-sm-9">
                                        {{ access.requester_name }}
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >Role:
                                    </label>
                                    <div class="col-sm-9">
                                        {{ access.role }}
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >Organisation</label
                                    >
                                    <div class="col-sm-9">
                                        <input
                                            v-model="access.name"
                                            type="text"
                                            disabled
                                            class="form-control"
                                            name="name"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >ABN</label
                                    >
                                    <div class="col-sm-9">
                                        <input
                                            v-model="access.abn"
                                            type="text"
                                            disabled
                                            class="form-control"
                                            name="abn"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >Letter</label
                                    >
                                    <div class="col-sm-9">
                                        <i
                                            class="fa-solid fa-file-pdf fa-lg ps-1"
                                        ></i
                                        >&nbsp;
                                        <a
                                            target="_blank"
                                            :href="access.identification_url"
                                            >Letter</a
                                        >
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >Phone</label
                                    >
                                    <div class="col-sm-9">
                                        <input
                                            v-model="
                                                access.requester.phone_number
                                            "
                                            type="text"
                                            disabled
                                            class="form-control"
                                            name="phone"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >Mobile</label
                                    >
                                    <div class="col-sm-9">
                                        <input
                                            v-model="
                                                access.requester.mobile_number
                                            "
                                            type="text"
                                            disabled
                                            class="form-control"
                                            name="mobile"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <label for="" class="col-sm-3 control-label"
                                        >Email</label
                                    >
                                    <div class="col-sm-9">
                                        <input
                                            v-model="access.requester.email"
                                            type="text"
                                            disabled
                                            class="form-control"
                                            name="email"
                                            placeholder=""
                                        />
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </FormSection>
            </div>
        </div>
        <div v-else class="row">
            <BootstrapSpinner class="text-primary" />
        </div>
    </div>
</template>
<script>
import CommsLogs from '@common-utils/comms_logs.vue';
import Swal from 'sweetalert2';
import { api_endpoints, constants, helpers } from '@/utils/hooks';
export default {
    name: 'OrganisationAccess',
    components: {
        CommsLogs,
    },
    data() {
        let vm = this;
        return {
            loading: [],
            profile: {},
            loadingOrganisationRequest: false,
            access: null,
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            members: [],
            // Filters
            logs_url: helpers.add_endpoint_json(
                api_endpoints.organisation_requests,
                vm.$route.params.access_id + '/action_log'
            ),
            comms_url: helpers.add_endpoint_json(
                api_endpoints.organisation_requests,
                vm.$route.params.access_id + '/comms_log'
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.organisation_requests,
                vm.$route.params.access_id + '/add_comms_log'
            ),
            actionDtOptions: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                order: [[2, 'desc']],
                dom:
                    "<'row'<'col-sm-5'l><'col-sm-6'f>>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'row'<'col-sm-5'i><'col-sm-7'p>>",
                processing: true,
                ajax: {
                    url: helpers.add_endpoint_json(
                        api_endpoints.organisation_requests,
                        vm.$route.params.access_id + '/action_log'
                    ),
                    dataSrc: '',
                },
                columns: [
                    {
                        data: 'who',
                    },
                    {
                        data: 'what',
                    },
                    {
                        data: 'when',
                        mRender: function (data) {
                            return moment(data).format(vm.DATE_TIME_FORMAT);
                        },
                    },
                ],
            },
            dtHeaders: ['Who', 'What', 'When'],
            actionsTable: null,
            commsDtOptions: {
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                deferRender: true,
                autowidth: true,
                order: [[0, 'desc']],
                processing: true,
                ajax: {
                    url: helpers.add_endpoint_json(
                        api_endpoints.organisation_requests,
                        vm.$route.params.access_id + '/comms_log'
                    ),
                    dataSrc: '',
                },
                columns: [
                    {
                        title: 'Date',
                        data: 'created',
                        render: function (date) {
                            return moment(date).format(vm.DATE_TIME_FORMAT);
                        },
                    },
                    {
                        title: 'Type',
                        data: 'type',
                    },
                    {
                        title: 'Reference',
                        data: 'reference',
                    },
                    {
                        title: 'To',
                        data: 'to',
                        render: vm.commaToNewline,
                    },
                    {
                        title: 'CC',
                        data: 'cc',
                        render: vm.commaToNewline,
                    },
                    {
                        title: 'From',
                        data: 'fromm',
                        render: vm.commaToNewline,
                    },
                    {
                        title: 'Subject/Desc.',
                        data: 'subject',
                    },
                    {
                        title: 'Text',
                        data: 'text',
                        render: function (value) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 100,
                                    omission: ellipsis,
                                    separator: ' ',
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template(
                                    '<a href="#" ' +
                                        'role="button" ' +
                                        'data-toggle="popover" ' +
                                        'data-trigger="click" ' +
                                        'data-placement="top auto"' +
                                        'data-html="true" ' +
                                        'data-content="<%= text %>" ' +
                                        '>more</a>'
                                );
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value,
                                });
                            }

                            return result;
                        },
                    },
                    {
                        title: 'Documents',
                        data: 'documents',
                        render: function (values) {
                            var result = '';
                            _.forEach(values, function (value) {
                                // We expect an array [docName, url]
                                // if it's a string it is the url
                                var docName = '',
                                    url = '';
                                if (_.isArray(value) && value.length > 1) {
                                    docName = value[0];
                                    url = value[1];
                                }
                                if (typeof s === 'string') {
                                    url = value;
                                    // display the first  chars of the filename
                                    docName = _.last(value.split('/'));
                                    docName = _.truncate(docName, {
                                        length: 18,
                                        omission: '...',
                                        separator: ' ',
                                    });
                                }
                                result +=
                                    '<a href="' +
                                    url +
                                    '" target="_blank"><p>' +
                                    docName +
                                    '</p></a><br>';
                            });
                            return result;
                        },
                    },
                ],
            },
            commsTable: null,
        };
    },
    computed: {
        isLoading: function () {
            return this.loading.length > 0;
        },
        isFinalised: function () {
            return (
                this.access.status == 'Approved' ||
                this.access.status == 'Declined'
            );
        },
        is_organisation_access_officer: function () {
            if (this.profile) {
                return this.profile.is_organisation_access_officer;
            }
            return false;
        },
    },
    mounted: function () {
        const id = this.$route.params.access_id;
        this.fetchOrganisationRequest(id);
        this.fetchAccessGroupMembers();
        this.fetchProfile();
    },
    methods: {
        commaToNewline(s) {
            return s.replace(/[,;]/g, '\n');
        },
        fetchAccessGroupMembers: function () {
            let vm = this;
            fetch(api_endpoints.organisation_access_group_members)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.members = data;
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error('There was an error!', error);
                });
        },
        assignMyself: function () {
            let vm = this;
            fetch(
                helpers.add_endpoint_json(
                    api_endpoints.organisation_requests,
                    vm.access.id + '/assign_request_user'
                )
            )
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.access = data;
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error('There was an error!', error);
                });
        },
        assignTo: function () {
            let vm = this;
            if (vm.access.assigned_officer != 'null') {
                const requestOptions = {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: vm.access.assigned_officer,
                    }),
                };
                fetch(
                    helpers.add_endpoint_json(
                        api_endpoints.organisation_requests,
                        vm.access.id + '/assign_user'
                    ),
                    requestOptions
                )
                    .then(async (response) => {
                        const data = await response.json();
                        if (!response.ok) {
                            const error =
                                (data && data.message) || response.statusText;
                            console.error(error);
                            return Promise.reject(error);
                        }
                        vm.access = data;
                    })
                    .catch((error) => {
                        this.errorMessage = constants.ERRORS.API_ERROR;
                        console.error('There was an error!', error);
                    });
            } else {
                const requestOptions = {
                    method: 'PATCH',
                };
                fetch(
                    helpers.add_endpoint_json(
                        api_endpoints.organisation_requests,
                        vm.access.id + '/unassign'
                    ),
                    requestOptions
                )
                    .then(async (response) => {
                        const data = await response.json();
                        if (!response.ok) {
                            const error =
                                (data && data.message) || response.statusText;
                            console.error(error);
                            return Promise.reject(error);
                        }
                        vm.access = data;
                    })
                    .catch((error) => {
                        this.errorMessage = constants.ERRORS.API_ERROR;
                        console.error('There was an error!', error);
                    });
            }
        },
        acceptRequest: function () {
            let vm = this;
            Swal.fire({
                title: 'Accept Organisation Request',
                text: 'Are you sure you want to accept this organisation request?',
                type: 'question',
                showCancelButton: true,
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
                confirmButtonText: 'Accept',
            }).then((result) => {
                if (result.isConfirmed) {
                    const requestOptions = {
                        method: 'PATCH',
                    };
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.organisation_requests,
                            vm.access.id + '/accept'
                        ),
                        requestOptions
                    )
                        .then(async (response) => {
                            const data = await response.json();
                            if (!response.ok) {
                                const error =
                                    (data && data.message) ||
                                    response.statusText;
                                console.error(error);
                                return Promise.reject(error);
                            }
                            vm.access = data;
                            Swal.fire(
                                'Success',
                                'Organisation request accepted. The user will be notified by email.',
                                'success'
                            );
                        })
                        .catch((error) => {
                            console.error('There was an error!', error);
                            let text = helpers.apiVueResourceError(error);
                            if (typeof text == 'object') {
                                if (Object.hasOwn(text, 'email')) {
                                    text = text.email[0];
                                }
                            }
                            Swal.fire(
                                'Error',
                                'Organisation request cannot be accepted because of the following error: ' +
                                    text,
                                'error'
                            );
                        });
                }
            });
        },
        declineRequest: function () {
            let vm = this;
            Swal.fire({
                title: 'Decline Organisation Request',
                text: 'Are you sure you want to decline this organisation request?',
                type: 'question',
                showCancelButton: true,
                reverseButtons: true,
                buttonsStyling: false,
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary me-2',
                },
                confirmButtonText: 'Decline',
            }).then((result) => {
                if (result.isConfirmed) {
                    const requestOptions = {
                        method: 'PATCH',
                    };
                    fetch(
                        helpers.add_endpoint_json(
                            api_endpoints.organisation_requests,
                            vm.access.id + '/decline'
                        ),
                        requestOptions
                    )
                        .then(async (response) => {
                            const data = await response.json();
                            if (!response.ok) {
                                const error =
                                    (data && data.message) ||
                                    response.statusText;
                                console.error(error);
                                return Promise.reject(error);
                            }
                            vm.access = data;
                            Swal.fire(
                                'Success',
                                'Organisation request declined. The user will be notified by email.',
                                'success'
                            );
                        })
                        .catch((error) => {
                            this.errorMessage = constants.ERRORS.API_ERROR;
                            console.error('There was an error!', error);
                        });
                }
            });
        },
        fetchOrganisationRequest: function (id) {
            let vm = this;
            vm.loadingOrganisationRequest = true;
            fetch(api_endpoints.organisation_requests + `${id}/`)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.access = data;
                    vm.loadingOrganisationRequest = false;
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error('There was an error!', error);
                });
        },
        fetchProfile: function () {
            let vm = this;
            fetch(api_endpoints.profile)
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.profile = data;
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error('There was an error!', error);
                });
        },
        current_user_is_assigned: function () {
            let vm = this;
            if (vm.access.assigned_officer == vm.profile.id) return true;
            else return false;
        },
    },
};
</script>
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}

.actionBtn {
    cursor: pointer;
}

.hidePopover {
    display: none;
}
</style>
