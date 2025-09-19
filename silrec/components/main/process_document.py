import logging
import os

from django.core.files.base import ContentFile

from silrec.components.main.models import upload_protected_files_storage
from silrec.components.main.utils import get_secure_document_url
from silrec.components.proposals.models import ProposalAdditionalDocumentType

logger = logging.getLogger(__name__)


def process_generic_document(request, instance, document_type=None, *args, **kwargs):
    try:
        action = request.data.get("action")
        input_name = request.data.get("input_name")
        comms_log_id = request.data.get("comms_log_id")
        comms_instance = None

        if document_type == "comms_log" and comms_log_id and comms_log_id != "null":
            comms_instance = instance.comms_logs.get(id=comms_log_id)
        elif document_type == "comms_log":
            comms_instance = instance.comms_logs.create()

        if action == "list":
            pass
        elif action == "delete":
            delete_document(
                request, instance, comms_instance, document_type, input_name
            )
        elif action == "cancel":
            deleted = cancel_document(
                request, instance, comms_instance, document_type, input_name
            )
        elif action == "save":
            save_document(request, instance, comms_instance, document_type, input_name)

        #import ipdb; ipdb.set_trace()
        # HTTP Response varies by action and instance type
        if comms_instance and action == "cancel" and deleted:
            return deleted
        elif comms_instance:
            returned_file_data = [
                dict(
                    file=d._file.url,
                    id=d.id,
                    name=d.name,
                )
                for d in comms_instance.documents.all()
                if d._file
            ]
            return {
                "filedata": returned_file_data,
                "comms_instance_id": comms_instance.id,
            }
        # example document_type
        elif input_name:
            if document_type == "deed_poll_document":
                documents_qs = instance.deed_poll_documents
            elif document_type == "supporting_document":
                documents_qs = instance.supporting_documents
            elif document_type == "proposed_approval_document":
                documents_qs = instance.proposed_approval_documents
            elif document_type == "shapefile_document":
                documents_qs = instance.shapefile_documents
            elif document_type == "proposed_decline_document":
                documents_qs = instance.proposed_decline_documents
            elif document_type == "additional_document":
                documents_qs = instance.additional_documents

            # default file attributes
            returned_file_data = [
                dict(
                    secure_url=get_secure_document_url(
                        instance, document_type + "s", d.id
                    ),
                    id=d.id,
                    name=d.name,
                )
                for d in documents_qs.filter(input_name=input_name)
                if d._file
            ]
            return {"filedata": returned_file_data}
        else:
            # not used
            returned_file_data = [
                dict(
                    file=d._file.url,
                    id=d.id,
                    name=d.name,
                )
                for d in instance.documents.all()
                if d._file
            ]
            return {"filedata": returned_file_data}

    except Exception as e:
        logger.exception(e)
        raise e


def delete_document(request, instance, comms_instance, document_type, input_name=None):
    document_id = request.data.get("document_id")
    if "document_id" in request.data:
        if document_type == "deed_poll_document":
            document = instance.deed_poll_documents.get(id=document_id)
        elif document_type == "temp_document":
            document = instance.documents.get(id=document_id)
        elif document_type == "supporting_document":
            document = instance.supporting_documents.get(id=document_id)
        elif document_type == "proposed_approval_document":
            document = instance.proposed_approval_documents.get(id=document_id)
        elif document_type == "exclusive_use_document":
            document = instance.exclusive_use_documents.get(id=document_id)
        elif document_type == "long_term_use_document":
            document = instance.long_term_use_documents.get(id=document_id)
        elif document_type == "consistent_purpose_document":
            document = instance.consistent_purpose_documents.get(id=document_id)
        elif document_type == "consistent_plan_document":
            document = instance.consistent_plan_documents.get(id=document_id)
        elif document_type == "clearing_vegetation_document":
            document = instance.clearing_vegetation_documents.get(id=document_id)
        elif document_type == "ground_disturbing_works_document":
            document = instance.ground_disturbing_works_documents.get(id=document_id)
        elif document_type == "heritage_site_document":
            document = instance.heritage_site_documents.get(id=document_id)
        elif document_type == "environmentally_sensitive_document":
            document = instance.environmentally_sensitive_documents.get(id=document_id)
        elif document_type == "wetlands_impact_document":
            document = instance.wetlands_impact_documents.get(id=document_id)
        elif document_type == "building_required_document":
            document = instance.building_required_documents.get(id=document_id)
        elif document_type == "significant_change_document":
            document = instance.significant_change_documents.get(id=document_id)
        elif document_type == "aboriginal_site_document":
            document = instance.aboriginal_site_documents.get(id=document_id)
        elif document_type == "native_title_consultation_document":
            document = instance.native_title_consultation_documents.get(id=document_id)
        elif document_type == "mining_tenement_document":
            document = instance.mining_tenement_documents.get(id=document_id)
        elif document_type == "profit_and_loss_document":
            document = instance.profit_and_loss_documents.get(id=document_id)
        elif document_type == "cash_flow_document":
            document = instance.cash_flow_documents.get(id=document_id)
        elif document_type == "capital_investment_document":
            document = instance.capital_investment_documents.get(id=document_id)
        elif document_type == "financial_capacity_document":
            document = instance.financial_capacity_documents.get(id=document_id)
        elif document_type == "available_activities_document":
            document = instance.available_activities_documents.get(id=document_id)
        elif document_type == "market_analysis_document":
            document = instance.market_analysis_documents.get(id=document_id)
        elif document_type == "staffing_document":
            document = instance.staffing_documents.get(id=document_id)
        elif document_type == "key_personnel_document":
            document = instance.key_personnel_documents.get(id=document_id)
        elif document_type == "key_milestones_document":
            document = instance.key_milestones_documents.get(id=document_id)
        elif document_type == "risk_factors_document":
            document = instance.risk_factors_documents.get(id=document_id)
        elif document_type == "legislative_requirements_document":
            document = instance.legislative_requirements_documents.get(id=document_id)
        elif document_type == "shapefile_document":
            document = instance.shapefile_documents.get(id=document_id)
        elif document_type == "proposed_decline_document":
            document = instance.proposed_decline_documents.get(id=document_id)
        elif document_type == "lease_licence_approval_document":
            document = instance.lease_licence_approval_documents.get(id=document_id)
        elif document_type == "competitive_process_document":
            document = instance.competitive_process_documents.get(id=document_id)
        elif document_type == "approval_cancellation_document":
            document = instance.approval_cancellation_documents.get(id=document_id)
        elif document_type == "approval_surrender_document":
            document = instance.approval_surrender_documents.get(id=document_id)
        elif document_type == "approval_suspension_document":
            document = instance.approval_suspension_documents.get(id=document_id)
        elif document_type == "additional_document":
            document = instance.additional_documents.get(id=document_id)
        elif document_type == "approval_transfer_supporting_document":
            document = instance.approval_transfer_supporting_documents.get(
                id=document_id
            )

    # comms_log doc store delete
    elif comms_instance and "document_id" in request.data:
        document = comms_instance.documents.get(id=document_id)

    # default doc store delete
    elif "document_id" in request.data:
        document = instance.documents.get(id=document_id)

    if document._file and os.path.isfile(document._file.path):
        os.remove(document._file.path)

    if document:
        document.delete()


def cancel_document(request, instance, comms_instance, document_type, input_name=None):
    if document_type in [
        "deed_poll_document",
        "supporting_document",
        "proposed_approval_document",
        "exclusive_use_document",
        "long_term_use_document",
        "consistent_purpose_document",
        "consistent_plan_document",
        "clearing_vegetation_document",
        "ground_disturbing_works_document",
        "heritage_site_document",
        "environmentally_sensitive_document",
        "wetlands_impact_document",
        "building_required_document",
        "significant_change_document",
        "aboriginal_site_document",
        "native_title_consultation_document",
        "mining_tenement_document",
        # additional form fields for lease_licence
        "profit_and_loss_document",
        "cash_flow_document",
        "capital_investment_document",
        "financial_capacity_document",
        "available_activities_document",
        "market_analysis_document",
        "staffing_document",
        "key_personnel_document",
        "key_milestones_document",
        "risk_factors_document",
        "legislative_requirements_document",
        "lease_licence_approval_document" "proposed_decline_document",
        "competitive_process_document",
    ]:
        pass

    if comms_instance:
        document_list = comms_instance.documents.all()
    else:
        document_list = instance.documents.all()

    for document in document_list:
        if document._file and os.path.isfile(document._file.path):
            os.remove(document._file.path)
        document.delete()

    if comms_instance:
        return comms_instance.delete()


def save_document(request, instance, comms_instance, document_type, input_name=None):
    # example document_type
    if "filename" in request.data and input_name:
        filename = request.data.get("filename")
        _file = request.data.get("_file")

        if document_type == "deed_poll_document":
            document = instance.deed_poll_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/deed_poll_documents/{}"
        elif document_type == "supporting_document":
            document = instance.supporting_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/proposed_approval_documents/{}"
        elif document_type == "proposed_approval_document":
            document = instance.proposed_approval_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/supporting_documents/{}"
        elif document_type == "exclusive_use_document":
            document = instance.exclusive_use_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/exclusive_use_documents/{}"
        elif document_type == "long_term_use_document":
            document = instance.long_term_use_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/long_term_use_documents/{}"
        elif document_type == "consistent_purpose_document":
            document = instance.consistent_purpose_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/consistent_purpose_documents/{}"
        elif document_type == "consistent_plan_document":
            document = instance.consistent_plan_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/consistent_plan_documents/{}"
        elif document_type == "clearing_vegetation_document":
            document = instance.clearing_vegetation_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/clearing_vegetation_documents/{}"
        elif document_type == "ground_disturbing_works_document":
            document = instance.ground_disturbing_works_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/ground_disturbing_works_documents/{}"
        elif document_type == "heritage_site_document":
            document = instance.heritage_site_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/heritage_site_documents/{}"
        elif document_type == "environmentally_sensitive_document":
            document = instance.environmentally_sensitive_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/environmentally_sensitive_documents/{}"
        elif document_type == "wetlands_impact_document":
            document = instance.wetlands_impact_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/wetlands_impact_documents/{}"
        elif document_type == "building_required_document":
            document = instance.building_required_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/building_required_documents/{}"
        elif document_type == "significant_change_document":
            document = instance.significant_change_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/significant_change_documents/{}"
        elif document_type == "aboriginal_site_document":
            document = instance.aboriginal_site_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/aboriginal_site_documents/{}"
        elif document_type == "native_title_consultation_document":
            document = instance.native_title_consultation_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/native_title_consultation_documents/{}"
        elif document_type == "mining_tenement_document":
            document = instance.mining_tenement_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/mining_tenement_documents/{}"
        elif document_type == "profit_and_loss_document":
            document = instance.profit_and_loss_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/profit_and_loss_documents/{}"
        elif document_type == "cash_flow_document":
            document = instance.cash_flow_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/cash_flow_documents/{}"
        elif document_type == "capital_investment_document":
            document = instance.capital_investment_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/capital_investment_documents/{}"
        elif document_type == "financial_capacity_document":
            document = instance.financial_capacity_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/financial_capacity_documents/{}"
        elif document_type == "available_activities_document":
            document = instance.available_activities_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/available_activities_documents/{}"
        elif document_type == "market_analysis_document":
            document = instance.market_analysis_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/market_analysis_documents/{}"
        elif document_type == "staffing_document":
            document = instance.staffing_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/staffing_documents/{}"
        elif document_type == "key_personnel_document":
            document = instance.key_personnel_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/key_personnel_documents/{}"
        elif document_type == "key_milestones_document":
            document = instance.key_milestones_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/key_milestones_documents/{}"
        elif document_type == "risk_factors_document":
            document = instance.risk_factors_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/risk_factors_documents/{}"
        elif document_type == "legislative_requirements_document":
            document = instance.legislative_requirements_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/legislative_requirements_documents/{}"
        elif document_type == "shapefile_document":
            document = instance.shapefile_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/shapefile_documents/{}"
        elif document_type == "proposed_decline_document":
            document = instance.proposed_decline_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "proposals/{}/proposed_decline_documents/{}"
        elif document_type == "additional_document":
            proposal_additional_document_type = (
                ProposalAdditionalDocumentType.objects.get(
                    proposal=instance, additional_document_type__name=input_name
                )
            )
            document = instance.additional_documents.get_or_create(
                input_name=input_name,
                name=filename,
                proposal_additional_document_type=proposal_additional_document_type,
            )[0]
            path_format_string = "proposals/{}/additional_documents/{}"
        elif document_type == "lease_licence_approval_document":
            approval_type = request.data.get("approval_type")
            approval_type_document_type = request.data.get(
                "approval_type_document_type"
            )
            if not approval_type_document_type.isnumeric() or not (
                ApprovalTypeDocumentType.objects.filter(
                    id=approval_type_document_type
                ).exists()
            ):
                approval_type_document_type = ApprovalTypeDocumentType.objects.get(
                    name="Other"
                ).id

            document = instance.lease_licence_approval_documents.get_or_create(
                input_name=input_name,
                name=filename,
                approval_type=ApprovalType.objects.get(id=approval_type),
                approval_type_document_type=ApprovalTypeDocumentType.objects.get(
                    id=approval_type_document_type
                ),
            )[0]
            path_format_string = "proposals/{}/lease_licence_approval_documents/{}"

        # -------------- Approval
        elif document_type == "approval_cancellation_document":
            document = instance.approval_cancellation_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "approvals/{}/cancellation_documents/{}"
        elif document_type == "approval_surrender_document":
            document = instance.approval_surrender_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "approvals/{}/surrender_documents/{}"
        elif document_type == "approval_suspension_document":
            document = instance.approval_suspension_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "approvals/{}/suspension_documents/{}"
        elif document_type == "approval_transfer_supporting_document":
            document = instance.approval_transfer_supporting_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "approval-transfer/{}/supporting-documents/{}"
        # -------------- Competitive Process
        elif document_type == "competitive_process_document":
            document = instance.competitive_process_documents.get_or_create(
                input_name=input_name, name=filename
            )[0]
            path_format_string = "competitive_process/{}/{}"
            # return '{}/competitive_process/{}/{}'.format(
            #     settings.MEDIA_APP_DIR,
            #     instance.competitive_process.id,
            #     filename,
            # )

        path = upload_protected_files_storage.save(
            path_format_string.format(instance.id, filename),
            ContentFile(_file.read()),
        )
        document._file = path
        document.save()

    # comms_log doc store save
    elif comms_instance and "filename" in request.data:
        filename = request.data.get("filename")
        _file = request.data.get("_file")

        document = comms_instance.documents.get_or_create(name=filename)[0]
        path = upload_protected_files_storage.save(
            "{}/{}/communications/{}/documents/{}".format(
                instance._meta.model_name, instance.id, comms_instance.id, filename
            ),
            ContentFile(_file.read()),
        )

        document._file = path
        document.save()

    # default doc store save
    elif "filename" in request.data:
        filename = request.data.get("filename")
        _file = request.data.get("_file")

        document = instance.documents.get_or_create(name=filename)[0]
        path = upload_protected_files_storage.save(
            "{}/{}/documents/{}".format(
                instance._meta.model_name, instance.id, filename
            ),
            ContentFile(_file.read()),
        )

        document._file = path
        document.save()


# For transferring files from temp doc objs to default doc objs
def save_default_document_obj(instance, temp_document):
    document = instance.documents.get_or_create(name=temp_document.name)[0]
    path = upload_protected_files_storage.save(
        "{}/{}/documents/{}".format(
            instance._meta.model_name, instance.id, temp_document.name
        ),
        temp_document._file,
    )

    document._file = path
    document.save()
