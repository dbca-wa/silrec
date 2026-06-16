from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

USERS = {
    'Reviewer': [
        ('Jodie', 'Miller', 'jodie.miller@dbca.wa.gov.au'),
        ('Matt', 'Seymour', 'matthew.seymour@dbca.wa.gov.au'),
        ('Lisa', 'Smith', 'lisa.smith@dbca.wa.gov.au'),
        ('Mel', 'Dybala', 'melanie.dybala@dbca.wa.gov.au'),
        ('Martin', 'Van Rooyen', 'martin.vanrooyen@dbca.wa.gov.au'),
        ('Clarissa', 'Swarts', 'clarissa.swarts@dbca.wa.gov.au'),
        ('Thu', 'Nguyen', 'thu.nguyen@dbca.wa.gov.au'),
    ],
    'Operator': [
        ('Shelley', 'Phillips', 'shelley.phillips@dbca.wa.gov.au'),
        ('John', 'Mosaj', 'john.mosaj@dbca.wa.gov.au'),
    ],
    'Silrec Admin': [
        ('Derek', 'Winters', 'derek.winters@dbca.wa.gov.au'),
        ('Zianfeng', 'Su', 'xianfeng.su@dbca.wa.gov.au'),
        ('Jawaid', 'Mushtaq', 'jawaid.mushtaq@dbca.wa.gov.au'),
        ('Sonia', 'Gillespie', 'sonia.gillespie@dbca.wa.gov.au'),
    ],
}


class Command(BaseCommand):
    help = 'Create or remove users defined in USERS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove users defined in USERS instead of creating them',
        )

    def handle(self, *args, **options):
        if options['remove']:
            self._remove_users()
        else:
            self._create_users()

    def _create_users(self):
        for group_name, people in USERS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            for first_name, last_name, email in people:
                username = email
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_staff': True,
                        'is_active': True,
                    },
                )
                if created:
                    user.set_unusable_password()
                    user.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'Created user {first_name} {last_name} ({email})'
                    ))

                    user.groups.add(group)
                    self.stdout.write(f'  → added to group "{group_name}"')

    def _remove_users(self):
        for group_name, people in USERS.items():
            for first_name, last_name, email in people:
                try:
                    user = User.objects.get(username=email)
                    user.delete()
                    self.stdout.write(self.style.SUCCESS(
                        f'Removed user {first_name} {last_name} ({email})'
                    ))
                except User.DoesNotExist:
                    self.stdout.write(
                        f'Skipped {first_name} {last_name} ({email}) — not found'
                    )
