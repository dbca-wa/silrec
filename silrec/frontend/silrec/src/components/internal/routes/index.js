import { RouterView } from 'vue-router';
import InternalDashboard from '@/components/internal/dashboard.vue';
import OrgAccessTable from '@/components/internal/organisations/access-dashboard.vue';
import OrgAccess from '@/components/internal/organisations/access.vue';
import OrganisationsDashboard from '@/components/internal/organisations/dashboard.vue';
import Organisation from '@/components/internal/organisations/manage.vue';
import AddOrganisation from '@/components/internal/organisations/add.vue';
import Proposal from '@/components/internal/proposals/proposal.vue';
import ApprovalDash from '@/components/internal/approvals/dashboard.vue';
import ComplianceDash from '@/components/internal/compliances/dashboard.vue';
import InvoicesDash from '@/components/internal/invoices/dashboard.vue';
import Search from '@/components/internal/search/dashboard.vue';
import PersonDetail from '@/components/internal/person/person_detail.vue';
import Compliance from '../compliances/access.vue';
import Approval from '@/components/internal/approvals/approval.vue';
import CompetitiveProcess from '@/components/internal/competitive_process/competitive_process.vue';
import ProposalMigrate from '@/components/internal/proposal_migrate.vue';

//import { createRouter, createWebHistory  } from 'vue-router'
//import ProposalMap from '@/components/ProposalMap.vue'
import CohortDetail from '@/components/internal/cohorts/cohort_detail.vue'
import TreatmentDetail from '@/components/internal/treatments/treatment_detail.vue'
import TreatmentExtraDetail from '@/components/internal/treatments/treatment_extra_detail.vue'
import TreatmentsDash from '@/components/internal/treatments/dashboard.vue';
import ComponentMap2 from '@/components/common/component_map2.vue';
import OperationDetails from '@/components/internal/operations/operation_details.vue';


export default {
    path: '/internal',
    component: RouterView,
    children: [
        {
            path: '/internal',
            component: InternalDashboard,
            name: 'internal-dashboard',
        },
//        {
//            path: 'approvals',
//            component: ApprovalDash,
//            name: 'internal-approvals-dash',
//        },
        {
            path: 'treatments',
            component: TreatmentsDash,
            name: 'internal-treatments-dash',
        },
        {
            path: 'map',
            component: ComponentMap2,
            name: 'internal-map2',
        },
        {
            path: 'approval/:approval_id',
            component: Approval,
            name: 'internal-approval-detail',
        },
        {
            path: 'compliances',
            component: ComplianceDash,
            name: 'internal-compliances-dash',
        },
        {
            path: 'compliance/:compliance_id',
            component: Compliance,
        },
        {
            path: 'invoices',
            component: InvoicesDash,
            name: 'internal-invoices-dash',
        },
        {
            path: 'search',
            component: Search,
            name: 'internal-search',
        },
        {
            path: 'person/details/:id',
            component: PersonDetail,
            name: 'internal-person-detail',
        },
        {
            path: 'organisations',
            component: RouterView,
            children: [
                {
                    path: '',
                    component: OrganisationsDashboard,
                    name: 'organisations-dashboard',
                },
                {
                    path: 'add',
                    component: AddOrganisation,
                    name: 'add-organisation',
                },
                {
                    path: 'access',
                    component: OrgAccessTable,
                    name: 'org-access-dash',
                },
                {
                    path: 'access/:access_id',
                    component: OrgAccess,
                    name: 'org-access',
                },
                {
                    path: ':org_id',
                    component: Organisation,
                    name: 'internal-org-detail',
                },
            ],
        },
        {
            path: 'proposal/',
            component: ProposalMigrate,
            name: 'migrate_proposal',
        },

        {
            path: 'proposal/:proposal_id',
            component: Proposal,
            name: 'internal-proposal',
        },
        {
            path: 'competitive_process/:competitive_process_id',
            component: CompetitiveProcess,
            name: 'internal-competitive-process',
        },
        {
            path: 'proposal/:proposal_id/cohorts/:cohortId/polygon/:polygonId',
            name: 'cohort-detail',
            component: CohortDetail,
            props: true

        },
        {
            path: 'cohorts/:cohortId',
            name: 'cohort-detail-simple',
            component: CohortDetail,
            props: true

        },
        // New treatment routes
        {
            path: 'treatment/:treatmentId',
            name: 'treatment-detail',
            component: TreatmentDetail,
            props: true
        },
        {
            path: 'treatment/:treatmentId/treatment-extra/:treatmentExtraId',
            name: 'treatment-extra-detail',
            component: TreatmentExtraDetail,
            props: true
        },
        {
            path: 'cohorts/:cohortId/treatment/new',
            name: 'new-treatment',
            component: TreatmentDetail,
            props: true
        },
        {
            path: 'treatment/:treatmentId/extra/new',
            name: 'new-treatment-extra',
            component: TreatmentExtraDetail,
            props: true
        },

//        // Operations section
//        {
//            path: 'cohorts/:cohortId/operation/new',
//            name: 'new-operation',
//            component: OperationDetails,
//            props: true,
//            //meta: { requiresAuth: true }
//        },
//        {
//            path: 'operation/:operationId/edit',
//            name: 'edit-operation',
//            component: OperationDetails,
//            props: true,
//            //meta: { requiresAuth: true }
//        },
//        {
//            path: 'operation/:operationId',
//            name: 'view-operation',
//            component: OperationDetails,
//            props: true,
//            //meta: { requiresAuth: true }
//        }
    ],
};
