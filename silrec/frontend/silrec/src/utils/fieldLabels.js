// Human-readable form labels for model field names, used by the bulk-update
// summary table and the cohort detail "Recent changes" panel.
export const FIELD_LABELS = {
    // Cohort
    obj_code: 'Objective Code',
    species: 'Species',
    regen_method: 'Regeneration Method',
    site_quality: 'Site Quality',
    target_ba_m2ha: 'Target BA (m²/ha)',
    resid_ba_m2ha: 'Residual BA (m²/ha)',
    target_spha: 'Target SPHA',
    resid_spha: 'Residual SPHA',
    pct_area: 'Percentage Area',
    year_last_cut: 'Year Last Cut',
    op_date: 'Operation Date',
    regen_date: 'Regeneration Date',
    regen_date2: 'Secondary Regeneration Date',
    regen_done: 'Regeneration Values Calculated',
    complete_date: 'Complete Date',
    herbicide_app_spec: 'Herbicide Application',
    vrp: 'VRP',
    vrp_tot_area: 'VRP Total Area (ha)',
    stand: 'Stand',
    extra_info: 'Extra Info Required',
    treatments: 'Treatments Inserted',
    comments: 'Comments',
    // Treatment
    task: 'Task',
    status: 'Status',
    plan_yr: 'Planned Year',
    plan_mth: 'Planned Month',
    organisation: 'Organisation',
    results: 'Results',
    reference: 'Reference',
    // Operation
    fea_id: 'FEA ID',
    das_id: 'DAS ID',
    plan_release: 'Plan Release',
};

export function fieldLabel(name) {
    return FIELD_LABELS[name] || name;
}
