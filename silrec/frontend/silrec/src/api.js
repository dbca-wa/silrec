export default {
    account: '/api/users/request_user_account/',
    applicants_dict: '/api/applicants_dict',
    application_statuses_dict: '/api/application_statuses_dict',
    application_types_dict: '/api/application_types_dict',
    application_types: '/api/application_types/',
    approval_statuses_dict: '/api/approval_statuses_dict',
    approval_types_dict: '/api/approval_types_dict',
    approvals_paginated_list: '/api/approval_paginated',
    approvals: '/api/approvals/',
    approval_transfers: '/api/approval_transfers/',
    charge_methods: '/api/charge_methods/',
    company_names: '/api/company_names',
    competitive_process_statuses_dict: '/api/competitive_process_statuses_dict',
    competitive_process: '/api/competitive_process/',
    compliance_assessments: '/api/compliance_assessments/',
    compliance_statuses_dict: '/api/compliance_statuses_dict',
    compliance_referrals: '/api/compliance_referrals/',
    compliances_paginated: '/api/compliance_paginated/',
    compliances: '/api/compliances/',
    countries: '/api/countries',
    cpi_calculation_methods: '/api/cpi_calculation_methods/',
    create_organisation: '/api/create_organisation/',
    external_referee_invites: '/api/external_referee_invites/',
    fee_configurations: '/api/fee_configurations',
    fee_seasons_dict: '/api/fee_seasons_dict',
    filtered_organisations: '/api/filtered_organisations',
    invoices: '/api/invoices/',
    invoicing_details: '/api/invoicing_details/',
    my_organisations: '/api/my_organisations/',
    oracle_codes: '/api/oracle_codes/',
    organisation_access_group_members: '/api/organisation_access_group_members',
    organisation_contacts: '/api/organisation_contacts.json',
    organisation_contacts_paginated: '/api/organisation_contacts_paginated/',
    organisation_lookup: '/api/organisations/organisation_lookup',
    organisation_requests_paginated: '/api/organisation_requests_paginated/',
    organisation_requests: '/api/organisation_requests/',
    organisations: '/api/organisations/',
    payment_system_id: '/api/payment_system_id',
    person_lookup: '/api/users/person_lookup/',
    profile: '/api/profile',
    proposal_by_uuid: '/api/proposal_by_uuid/',
    proposal_requirements: '/api/proposal_requirements.json',
    proposal_standard_requirements:
        '/api/proposal_standard_requirements/application_type_standard_requirements/',
    proposal: '/api/proposal/',
    proposals_paginated_list: '/api/proposal_paginated/', // both for external and internal
    proposals: '/api/proposal.json',
    referrals: '/api/referrals.json',
    repetition_types: '/api/repetition_types/',
    search_reference: '/api/search_reference/',
    submitter_profile: '/api/submitter_profile',
    temporary_document: '/api/temporary_document/',
    users: '/api/users/',

    // ------------------- GIS Data Endpoints -------------------

    acts: '/api/acts/',
    categories: '/api/categories/',
    districts: '/api/districts/',
    groups: '/api/groups/',
    identifiers: '/api/identifiers/',
    lgas: '/api/lgas/',
    names: '/api/names/',
    regions: '/api/regions/',
    tenures: '/api/tenures/',
    vestings: '/api/vestings/',

    lookupApprovalDetails: function (id) {
        return `/api/approvals/${id}/lookup_approval.json`;
    },
    lookupApprovalHistory: function (id) {
        return `/api/approvals/${id}/approval_history?format=datatables`;
    },
    decline_proposal: function (id) {
        return `/api/proposal/${id}/final_decline/`;
    },
    discard_proposal: function (id) {
        return `/api/proposal/${id}/discard/`;
    },

    // ------------------- ledger ui

    request_user_id: '/api/request_user_id/',
    account_details: '/api/account/',
    updateAccountDetails: function (id) {
        return `/ledger-ui/api/update-account-details/${id}/`;
    },

    details_text: '/api/detailstext/',
};
