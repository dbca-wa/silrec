# SILREC — Vue Forms That Mutate the Database

All Vue components that create, update, or delete records via API calls.

---

## Proposal

| File | Method | Endpoint | Action |
|---|---|---|---|
| `table_proposals.vue` | POST | `/api/proposal/` | Create new proposal |
| `proposal_apply.vue` | POST | `/api/proposal/` | External: create proposal |
| `proposal_migrate.vue` | POST | `/api/proposal/migrate/` | Migrate legacy proposal |
| `form.vue` | POST | `/api/proposal/{id}/upload_shapefile/` | Upload shapefile |
| `form.vue` | DELETE | `/api/proposal/{id}/delete_shapefile/` | Delete shapefile |
| `form.vue` | POST | `/api/proposal/{id}/process_shapefile/` | Process shapefile |
| `form.vue` | POST | `/api/proposal/{id}/workflow_options/` | Keep transition |
| `form.vue` | POST | `/api/proposal/{id}/revert_shapefile_processing/` | Revert |
| `proposal.vue` | POST | `/api/proposal/{id}/` | Save proposal form |
| `proposal.vue` | POST | `/api/proposal/{id}/transition_status/` | Status transitions |
| `proposal.vue` | POST | `/api/proposal/{id}/assign_to` | Assign officer |
| `proposal_requirements.vue` | PATCH | `/api/proposal_requirements/{id}/discard` | Discard requirement |
| `proposal_add_requirement.vue` | PUT | `/api/proposal_requirements/{id}/` | Update requirement |
| `proposal_add_requirement.vue` | POST | `/api/proposal_requirements/` | Create requirement |
| `merge_polygon_tool.vue` | POST | `/api/proposal/{id}/save_merged_geometry/` | Save merged geometry |
| `cut_polygon_tool.vue` | POST | `/api/proposal/{id}/save_cut_geometry/` | Save cut geometry |
| `amendment_request.vue` | POST | `/api/amendment_request.json` | Send amendment |
| `add_comm_log.vue` | POST | `/api/proposal/{id}/add_comms_log` | Add comm log entry |

---

## Cohort

| File | Method | Endpoint | Action |
|---|---|---|---|
| `cohort_detail.vue` | PUT | `/api/cohorts/{id}/` | Auto-save cohort fields |
| `cohort_detail.vue` | PUT | `/api/cohorts/{id}/` | Save all cohort fields |

---

## Treatment

| File | Method | Endpoint | Action |
|---|---|---|---|
| `treatments_form.vue` | PUT | `/api/treatments/{id}/` | Update treatment |
| `treatments_form.vue` | POST | `/api/treatments/` | Create treatment |
| `treatments_table.vue` | DELETE | `/api/treatments/{id}/` | Delete treatment |

---

## Prescription

| File | Method | Endpoint | Action |
|---|---|---|---|
| `prescription_form.vue` | PUT | `/api/prescriptions/{id}/` | Update prescription |
| `prescription_form.vue` | POST | `/api/prescriptions/` | Create prescription |

---

## Treatment Extra

| File | Method | Endpoint | Action |
|---|---|---|---|
| `treatments_extras_table.vue` | DELETE | `/api/treatment-extras/{id}/` | Delete treatment extra |

---

## Silviculturist Comment

| File | Method | Endpoint | Action |
|---|---|---|---|
| `silviculturist_comment.vue` | PUT | `/api/silviculturist-comments/{id}/` | Update comment |
| `silviculturist_comment.vue` | POST | `/api/silviculturist-comments/` | Create comment |
| `silviculturist_comment.vue` | DELETE | `/api/silviculturist-comments/{id}/` | Delete comment |

---

## Survey Assessment Document

| File | Method | Endpoint | Action |
|---|---|---|---|
| `survey_assessment.vue` | PATCH | `/api/survey-assessment-documents/{id}/` | Update document |
| `survey_assessment.vue` | POST | `/api/survey-assessment-documents/` | Create document (file upload) |
| `survey_assessment.vue` | PATCH | `/api/survey-assessment-documents/{id}/` | Restore document |
| `survey_assessment.vue` | DELETE | `/api/survey-assessment-documents/{id}/` | Delete draft document |
| `survey_assessment.vue` | PATCH | `/api/survey-assessment-documents/{id}/` | Mark document deleted |

---

## Operation

| File | Method | Endpoint | Action |
|---|---|---|---|
| `operations_form.vue` | PUT | `/api/operations/{id}/` | Update operation (file upload) |
| `operations_form.vue` | POST | `/api/operations/` | Create operation (file upload) |
| `operations_table.vue` | DELETE | `/api/operations/{id}/` | Delete operation |

---

## Report

| File | Method | Endpoint | Action |
|---|---|---|---|
| `report_generator.vue` | POST | `/api/reports/{id}/execute/` | Execute report |

---

## Generic File Upload

| File | Method | Endpoint | Action |
|---|---|---|---|
| `filefield_immediate.vue` | POST | `/api/temporary_document/` | Upload temp document |
| `filefield_immediate.vue` | POST | `/api/temporary_document/` | Create document collection |
| `filefield_immediate.vue` | POST | `/api/temporary_document/{id}/process_temp_document/` | Process temp document |

---

## Summary by Entity

| Entity | POST (Create) | PUT/PATCH (Update) | DELETE |
|---|---|---|---|
| Proposal | 8 | 2 | 1 |
| Cohort | 0 | 2 | 0 |
| Treatment | 1 | 1 | 1 |
| Prescription | 1 | 1 | 0 |
| Treatment Extra | 0 | 0 | 1 |
| Silviculturist Comment | 1 | 1 | 1 |
| Survey Assessment Document | 1 | 3 | 1 |
| Operation | 1 | 1 | 1 |
| Report | 1 | 0 | 0 |
| Temporary Document | 3 | 0 | 0 |
