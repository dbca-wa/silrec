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

export default {
    path: '/internal',
    component: RouterView,
    children: [
        {
            path: '/internal',
            component: InternalDashboard,
            name: 'internal-dashboard',
        },
        {
            path: 'approvals',
            component: ApprovalDash,
            name: 'internal-approvals-dash',
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
    ],
};
