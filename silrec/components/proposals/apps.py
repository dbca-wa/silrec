from django.apps import AppConfig

class ProposalsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'silrec.components.proposals'
    verbose_name = 'Proposals'

    def ready(self):
        # Import admin.py to ensure admin registrations happen
        import silrec.components.proposals.admin
