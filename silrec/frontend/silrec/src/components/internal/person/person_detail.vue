<template>
    <div id="personDash" class="container">
        <h3>{{ userHeader }}</h3>
        <div class="row">
            <div class="col-md-3">
                <CommsLogs
                    :comms_url="comms_url"
                    :logs_url="logs_url"
                    :comms_add_url="comms_add_url"
                    :disable_add_entry="false"
                />
            </div>

            <div class="col-md-9">
                <ul id="pills-tab" class="nav nav-pills" role="tablist">
                    <li class="nav-item">
                        <a
                            id="pills-details-tab"
                            class="nav-link active"
                            data-toggle="pill"
                            href="#pills-details"
                            role="tab"
                            aria-controls="pills-details"
                            aria-selected="true"
                        >
                            Details
                        </a>
                    </li>
                    <li class="nav-item">
                        <a
                            id="pills-approvals-tab"
                            class="nav-link"
                            data-toggle="pill"
                            href="#pills-approvals"
                            role="tab"
                            aria-controls="pills-approvals"
                            aria-selected="false"
                        >
                            Approvals
                        </a>
                    </li>
                </ul>
                <div id="pills-tabContent" class="tab-content">
                    <div
                        id="pills-details"
                        class="tab-pane show active"
                        role="tabpanel"
                        aria-labelledby="pills-details-tab"
                    >
                        <EmailUser
                            v-if="user"
                            id="person-details"
                            :email-user="user"
                            :readonly="true"
                        />
                    </div>
                    <div
                        id="pills-approvals"
                        class="tab-pane fade"
                        role="tabpanel"
                        aria-labelledby="pills-approvals-tab"
                    >
                        <FormSection
                            :form-collapse="true"
                            label="Applications"
                            subtitle=""
                            index="applications"
                        >
                            <ApplicationsTable
                                v-if="user"
                                level="organisation_view"
                                :target-email-user-id="user.id"
                            />
                        </FormSection>

                        <FormSection
                            :form-collapse="true"
                            label="Approvals"
                            subtitle=""
                            index="approvals"
                        >
                            <AppprovalsTable
                                v-if="user"
                                level="organisation_view"
                                :target-email-user-id="user.id"
                            />
                        </FormSection>

                        <FormSection
                            :form-collapse="true"
                            label="Compliances with Requirements"
                            subtitle=""
                            index="compliances"
                        >
                            <CompliancesTable
                                v-if="user"
                                level="internal"
                                :target-email-user-id="user.id"
                            />
                        </FormSection>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import FormSection from '@/components/forms/section_toggle.vue';
import ApplicationsTable from '@/components/common/table_proposals.vue';
import AppprovalsTable from '@/components/common/table_approvals.vue';
import CompliancesTable from '@/components/common/table_compliances.vue';
import { api_endpoints, helpers, constants } from '@/utils/hooks.js';
import CommsLogs from '@common-utils/comms_logs.vue';
import EmailUser from '@/components/internal/person/emailuser.vue';

export default {
    name: 'PersonDetail',
    components: {
        FormSection,
        ApplicationsTable,
        AppprovalsTable,
        CompliancesTable,
        CommsLogs,
        EmailUser,
    },
    data() {
        let vm = this;
        return {
            user: null,
            errorMessage: null,
            allApprovalTypeFilter: ['ml', 'aap', 'aup'],
            wlaApprovalTypeFilter: ['wla'],

            comms_url: helpers.add_endpoint_json(
                api_endpoints.users,
                vm.$route.params.id + '/comms_log'
            ),
            comms_add_url: helpers.add_endpoint_json(
                api_endpoints.users,
                vm.$route.params.id + '/add_comms_log'
            ),
            logs_url: helpers.add_endpoint_json(
                api_endpoints.users,
                vm.$route.params.id + '/action_log'
            ),
        };
    },
    computed: {
        userHeader: function () {
            if (this.user) {
                if (this.user.dob) {
                    return (
                        this.user.first_name +
                        ' ' +
                        this.user.last_name +
                        '(DOB: ' +
                        this.user.dob +
                        ')'
                    );
                } else {
                    return this.user.first_name + ' ' + this.user.last_name;
                }
            }
            return '';
        },
    },
    created: async function () {
        this.fetchUser(this.$route.params.id);
    },
    mounted: function () {
        var triggerTabList = [].slice.call(
            document.querySelectorAll('#pills-tab a')
        );
        triggerTabList.forEach(function (triggerEl) {
            var tabTrigger = new bootstrap.Tab(triggerEl);
            triggerEl.addEventListener('click', function (event) {
                event.preventDefault();
                tabTrigger.show();
            });
        });
    },
    methods: {
        fetchUser: function (id) {
            let vm = this;
            fetch(api_endpoints.users + id + '/')
                .then(async (response) => {
                    const data = await response.json();
                    if (!response.ok) {
                        const error =
                            (data && data.message) || response.statusText;
                        console.error(error);
                        return Promise.reject(error);
                    }
                    vm.user = data;
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error('There was an error!', error);
                });
        },
    },
};
</script>

<style scoped>
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
</style>
