# SILREC — Group Permissions & Workflow Matrix

## Groups

- **User**
- **Operator**
- **Reviewer**
- **Silrec Admin** (superuser-level, unrestricted)

## Permission Matrix by Processing Status

| Group | `draft` | `processing_shapefile` | `with_operator` | `with_reviewer` | `review_completed` |
|---|---|---|---|---|---|
| **User** | Read-Only | Read-Only | Read-Only | Read-Only | Read-Only |
| **Operator** | Read-Write | Read-Write | Read-Write | — | — |
| **Reviewer** | Read-Only | Read-Only | Read-Only | Can transition | Read-Only |

## Detailed Breakdown

### User (`isReadOnlyUser = true`)
- src/components/form.vue
- **All statuses**: Read-only.
- Form fields: greyed-out / disabled.
- Action buttons: None visible. No Upload/Process/Revert/Keep/Delete shapefile buttons. No Add/Create/Save/Cancel buttons. No workflow transition buttons.
- Datatable actions: "View" (eye icon) replaces "Edit". No Delete shown.

### Operator (`isReadOnlyUser = false`)
- **draft**: Read-Write. Upload Shapefile button active.
- **processing_shapefile**: Read-Write. Upload Shapefile button **greyed-out and disabled**.
- **with_operator**: Read-Write. Full access. Workflow buttons active: "Send to Reviewer", "Return to Draft".
- **Keep**: When clicked, sets processing_status to `with_operator`.

### Reviewer (`isReadOnlyUser = true`, with special exception)
- **with_reviewer**: Form fields read-only/greyed-out. Two workflow buttons visible and active: **"Send to Review Completed"** (green) and **"Return to Operator"** (grey).
- **All other statuses**: Read-Only. No workflow buttons. Shapefile section shows uploaded filename only — no Upload/Process/Revert/Keep/Delete buttons.

### Silrec Admin
- Unrestricted. Full read-write in all statuses. All buttons active. Admin link visible in Options dropdown.

## Key Files Implementing This Logic

| Logic | File |
|---|---|
| `is_readonly_user` API field | `silrec/components/users/api.py` |
| `isReadOnlyUser`, `isOperatorUser`, `isReviewerUser`, `canEditForStatus()` | `src/mixins/permissions.js` |
| `readonly` computed (proposal-level gate) | `src/components/internal/proposals/proposal.vue` |
| `displaySaveBtns` (workflow buttons visibility) | `src/components/internal/proposals/proposal.vue` |
| `showFormActions` (cohort save/action buttons) | `src/components/internal/cohorts/cohort_detail.vue` |
| `showActions` (treatment/operation form buttons) | `src/components/internal/treatments/treatment_detail.vue`, `src/components/internal/operations/operation_details.vue` |
| `showShapefileActions` / `shapefileDisabled` | `src/components/form.vue` |
| `canEdit` (cohort detail form fields) | `src/components/internal/cohorts/cohort_detail.vue` |
| `IsOperator` / `IsReviewer` / `IsSilrecAdmin` DRF permissions | `silrec/components/forest_blocks/api.py` |
| Navigation menu visibility (`has_access`) | `silrec/templates/webtemplate_dbca/includes/primary_menu.html` |
| Admin link (Options dropdown) | `silrec/templates/webtemplate_dbca/includes/staff_menu.html` |
| Transition rules (`can_transition_to`) | `silrec/components/proposals/models.py` |
