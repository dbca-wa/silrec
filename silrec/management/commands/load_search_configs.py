from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from silrec.components.proposals.models import (
    TextSearchModelConfig,
    TextSearchFieldDisplay
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Load initial text search configuration data'

    def handle(self, *args, **options):
        # Get or create admin user
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.filter(is_staff=True).first()
        except:
            admin_user = None

        # Default model configurations
        model_configs = [
            {
                'key': 'proposal',
                'model_name': 'silrec.Proposal',
                'display_name': 'Proposals',
                'search_fields': 'processing_status,title',
                'date_field': 'created_date',
                'id_field': 'id',
                'detail_fields': ['title'],
                'url_pattern': '/internal/proposal/{id}/',
                'is_active': True,
                'order': 1
            },
            {
                'key': 'polygon',
                'model_name': 'silrec.Polygon',
                'display_name': 'Polygons',
                'search_fields': 'name',
                'date_field': 'created_on',
                'id_field': 'polygon_id',
                'detail_fields': ['compartment', 'polygon_name'],
                'url_pattern': '/internal/polygon/{id}/',
                'is_active': True,
                'order': 2
            },
            {
                'key': 'cohort',
                'model_name': 'silrec.Cohort',
                'display_name': 'Cohorts',
                'search_fields': 'comments,obj_code,species',
                'date_field': 'created_on',
                'id_field': 'cohort_id',
                'detail_fields': [],
                'url_pattern': '/internal/cohort/{id}/',
                'is_active': True,
                'order': 3
            },
            {
                'key': 'treatment',
                'model_name': 'silrec.Treatment',
                'display_name': 'Treatments',
                'search_fields': 'results,reference',
                'date_field': 'created_on',
                'id_field': 'treatment_id',
                'detail_fields': ['task_name'],
                'url_pattern': '/internal/treatment/{id}/',
                'is_active': True,
                'order': 4
            },
            {
                'key': 'treatment_xtra',
                'model_name': 'silrec.Treatmentxtra',
                'display_name': 'Treatment Extras',
                'search_fields': 'zresult_standard',
                'date_field': 'treatment__created_on',
                'id_field': 'treatment_xtra_id',
                'detail_fields': [],
                'url_pattern': '/internal/treatment-extra/{id}/',
                'is_active': True,
                'order': 5
            },
            {
                'key': 'survey_assessment_document',
                'model_name': 'silrec.SurveyAssessmentDocument',
                'display_name': 'Survey Documents',
                'search_fields': 'description,title',
                'date_field': 'created_on',
                'id_field': 'document_id',
                'detail_fields': [],
                'url_pattern': '/internal/survey-document/{id}/',
                'is_active': True,
                'order': 6
            },
            {
                'key': 'silviculturist_comment',
                'model_name': 'silrec.SilviculturistComment',
                'display_name': 'Silviculturist Comments',
                'search_fields': 'comment',
                'date_field': 'created_on',
                'id_field': 's_comment_id',
                'detail_fields': [],
                'url_pattern': '/internal/silviculturist-comment/{id}/',
                'is_active': True,
                'order': 7
            },
            {
                'key': 'prescription',
                'model_name': 'silrec.Prescription',
                'display_name': 'Prescriptions',
                'search_fields': 'comment',
                'date_field': 'task__created_on',
                'id_field': 'prescription_id',
                'detail_fields': [],
                'url_pattern': '/internal/prescription/{id}/',
                'is_active': True,
                'order': 8
            }
        ]

        # Default field display configurations
        field_displays = [
            {'field_name': 'comment', 'display_name': 'Comments', 'order': 1},
            {'field_name': 'comments', 'display_name': 'Comments', 'order': 2},
            {'field_name': 'description', 'display_name': 'Description', 'order': 3},
            {'field_name': 'title', 'display_name': 'Title', 'order': 4},
            {'field_name': 'name', 'display_name': 'Name', 'order': 5},
            {'field_name': 'results', 'display_name': 'Results', 'order': 6},
            {'field_name': 'reference', 'display_name': 'Reference', 'order': 7},
            {'field_name': 'extra_info', 'display_name': 'Extra Info', 'order': 8},
            {'field_name': 'herbicide_app_spec', 'display_name': 'Herbicide Spec', 'order': 9},
            {'field_name': 'obj_code', 'display_name': 'Obj Code', 'order': 10},
            {'field_name': 'species', 'display_name': 'Species', 'order': 11},
            {'field_name': 'task_description', 'display_name': 'Task Description', 'order': 12},
            {'field_name': 'processing_status', 'display_name': 'Processing Status', 'order': 13},
            {'field_name': 'zresult_standard', 'display_name': 'Z Result Standard', 'order': 14},
        ]

        # Load model configs
        for config_data in model_configs:
            obj, created = TextSearchModelConfig.objects.update_or_create(
                key=config_data['key'],
                defaults={
                    'model_name': config_data['model_name'],
                    'display_name': config_data['display_name'],
                    'search_fields': config_data['search_fields'],
                    'date_field': config_data['date_field'],
                    'id_field': config_data['id_field'],
                    'detail_fields': config_data['detail_fields'],
                    'url_pattern': config_data['url_pattern'],
                    'is_active': config_data['is_active'],
                    'order': config_data['order'],
                    'created_by': admin_user
                }
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{status} model config: {config_data["key"]}')
            )

        # Load field displays
        for field_data in field_displays:
            obj, created = TextSearchFieldDisplay.objects.update_or_create(
                field_name=field_data['field_name'],
                defaults={
                    'display_name': field_data['display_name'],
                    'is_active': True,
                    'order': field_data['order'],
                    'created_by': admin_user
                }
            )
            status = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f'{status} field display: {field_data["field_name"]}')
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded initial search configurations!')
        )

