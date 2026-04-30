# SILREC — Group Permissions & Workflow Matrix

## Groups

- **User**
- **Operator**
- **Assessor**
- **Reviewer**
- **Silrec Admin** (superuser-level, unrestricted)

## Permission Matrix by Processing Status

| Group | `draft` | `processing_shapefile` | `with_assessor` | `with_reviewer` | `review_completed` |
|---|---|---|---|---|---|
| **User** | Read-Only | Read-Only | Read-Only | Read-Only | Read-Only |
| **Operator** | Read-Write | Read-Write | Read-Only | Read-Only | Read-Only |
| **Assessor** | Read-Write | Read-Write | Read-Write | — | — |
| **Reviewer** | Read-Only | Read-Only | Read-Only | Can transition | Read-Only |

## Detailed Breakdown

### User (`isReadOnlyUser = true`)
- **All statuses**: Read-only.
- Form fields: greyed-out / disabled.
- Action buttons: None visible. No Upload/Process/Revert/Keep/Delete shapefile buttons. No Add/Create/Save/Cancel buttons. No workflow transition buttons.
- Datatable actions: "View" (eye icon) replaces "Edit". No Delete shown.

### Operator (`isOperatorUser = true`, `isReadOnlyUser = false`)
- **draft**: Read-Write. Form fields editable. Upload Shapefile button **active** (blue, clickable). Shapefile Delete active. Workflow buttons hidden. "Add Treatment" / "Save and Continue" / "Save" / "Cancel" / "Update" buttons hidden throughout all sub-forms (cohort, treatment, operation).
- **processing_shapefile**: Read-Write. Same as draft except Upload Shapefile and Delete buttons **greyed-out and disabled**.
- **with_assessor, with_reviewer, review_completed**: Read-Only. All form fields disabled. All action/hidden.

### Assessor (`isReadOnlyUser = false`)
- **draft**: Read-Write. Upload Shapefile button active.
- **processing_shapefile**: Read-Write. Upload Shapefile button **greyed-out and disabled** (same logic as Operator via `shapefileDisabled`).
- **with_assessor**: Read-Write. Full access. Workflow buttons active: "Send to Reviewer", "Return to Draft".

### Reviewer (`isReadOnlyUser = true`, with special exception)
- **with_reviewer**: Form fields read-only/greyed-out. Two workflow buttons visible and active: **"Send to Review Completed"** (green) and **"Return to Assessor"** (grey).
- **All other statuses**: Read-Only. No workflow buttons. Shapefile section shows uploaded filename only — no Upload/Process/Revert/Keep/Delete buttons.

### Silrec Admin
- Unrestricted. Full read-write in all statuses. All buttons active. Admin link visible in Options dropdown.

## Key Files Implementing This Logic

| Logic | File |
|---|---|
| `is_readonly_user` / `is_operator_user` API fields | `silrec/components/users/api.py:60-64` |
| `isReadOnlyUser`, `isOperatorUser`, `isAssessorUser`, `isReviewerUser`, `canEditForStatus()` | `src/mixins/permissions.js` |
| `readonly` computed (proposal-level gate) | `src/components/internal/proposals/proposal.vue:605` |
| `displaySaveBtns` (workflow buttons visibility) | `src/components/internal/proposals/proposal.vue:428` |
| `showFormActions` (cohort save/action buttons) | `src/components/internal/cohorts/cohort_detail.vue:444` |
| `showActions` (treatment/operation form buttons) | `src/components/internal/treatments/treatment_detail.vue`, `src/components/internal/operations/operation_details.vue` |
| `showShapefileActions` / `shapefileDisabled` | `src/components/form.vue:627` |
| `canEdit` (cohort detail form fields) | `src/components/internal/cohorts/cohort_detail.vue:442` |
| `IsAssessor` / `IsReviewer` / `IsSilrecAdmin` DRF permissions | `silrec/components/forest_blocks/api.py` |
| Navigation menu visibility (`has_access`) | `silrec/templates/webtemplate_dbca/includes/primary_menu.html` |
| Admin link (Options dropdown) | `silrec/templates/webtemplate_dbca/includes/staff_menu.html` |
