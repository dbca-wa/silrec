import { RouterView } from 'vue-router';
import ExternalDashboard from '@/components/external/dashboard.vue';
import Proposal from '@/components/external/proposal.vue';
import ExternalReferralProposal from '@/components/internal/proposals/proposal.vue';
import ProposalApply from '@/components/external/proposal_apply.vue';
import ProposalSubmit from '@/components/external/proposal_submit.vue';
import Organisation from '@/components/external/organisations/manage.vue';
import Compliance from '../compliances/access.vue';
import ComplianceSubmit from '../compliances/submit.vue';
import Approval from '../approvals/approval.vue';
import ApprovalTransfer from '../approvals/approval_transfer.vue';
import ApprovalTransferConfirmation from '../approvals/approval_transfer_confirmation.vue';
import InvoicesDash from '@/components/internal/invoices/dashboard.vue';
import InvoicePaymentSuccess from '@/components/external/invoices/payment_success.vue';
import InvoicePaymentFailure from '@/components/external/invoices/payment_failure.vue';

export default {
    path: '/external',
    component: RouterView,
    children: [
        {
            path: '/external/',
            component: ExternalDashboard,
            name: 'external-dashboard',
        },
        {
            path: 'approval/:approval_id',
            component: Approval,
            name: 'external-approval-detail',
        },
        {
            path: 'approval/:approval_id/transfer',
            component: ApprovalTransfer,
            name: 'external-approval-transfer',
        },
        {
            path: 'approval/:approval_id/transfer/initiated',
            component: ApprovalTransferConfirmation,
            name: 'external-approval-transfer-initiated',
        },
        {
            path: 'organisations/manage/:org_id',
            component: Organisation,
        },
        {
            path: 'compliance/:compliance_id',
            component: Compliance,
        },
        {
            path: 'compliance/submit/:compliance_id',
            component: ComplianceSubmit,
            name: 'submit_compliance',
        },
        {
            path: 'proposal/',
            component: ProposalApply,
            name: 'apply_proposal',
        },
        {
            path: 'proposal/submit/:proposal_id',
            component: ProposalSubmit,
            name: 'submit-proposal',
        },
        {
            path: 'proposal/:proposal_id/referral/',
            component: ExternalReferralProposal,
            name: 'proposal_referral',
        },
        {
            path: 'proposal/:proposal_id',
            component: Proposal,
            name: 'draft_proposal',
        },
        {
            path: 'invoices',
            component: InvoicesDash,
            name: 'external-invoices-dash',
        },
        {
            path: 'invoice/:invoice_id/payment-success',
            component: InvoicePaymentSuccess,
            name: 'external-invoice-payment-success',
        },
        {
            path: 'invoice/:invoice_id/payment-failure',
            component: InvoicePaymentFailure,
            name: 'external-invoice-payment-failure',
        },
    ],
};
