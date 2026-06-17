from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

ROUND1 = {
    'Silrec Admin': [
        ('Jawaid', 'Mushtaq', 'jawaid.mushtaq@dbca.wa.gov.au'),
        ('Derek', 'Winters', 'derek.winters@dbca.wa.gov.au'),
        ('Xianfeng', 'Su', 'xianfeng.su@dbca.wa.gov.au'),
    ],
    'Operator': [
        ('Shelley', 'Phillips', 'shelley.phillips@dbca.wa.gov.au'),
        ('John', 'Mosaj', 'john.mosaj@dbca.wa.gov.au'),
        ('Sonia', 'Gillespie', 'sonia.gillespie@dbca.wa.gov.au'),
        ('Jodie', 'Miller', 'jodie.miller@dbca.wa.gov.au'),
        ('Matt', 'Seymour', 'matthew.seymour@dbca.wa.gov.au'),
        ('Ben', 'Davies', 'benton.davies@dbca.wa.gov.au'),
        ('Cal', 'Burwood', 'callum.burwood@dbca.wa.gov.au'),
    ],
    'Reviewer': [
        ('Melanie', 'Dybala', 'melanie.dybala@dbca.wa.gov.au'),
        ('Jodie', 'Watts', 'jodie.watts@dbca.wa.gov.au'),
        ('Bec', 'Brown', 'rebecca.brown@dbca.wa.gov.au'),
        ('Magda', 'Bustos Hevia', 'magda.bustoshevia@dbca.wa.gov.au'),
        ('Martin', 'Van Rooyen', 'martin.vanrooyen@dbca.wa.gov.au'),
        ('Clarissa', 'Swarts', 'clarissa.swarts@dbca.wa.gov.au'),
    ],
    'User': [
        ('Lisa', 'Smith', 'lisa.smith@dbca.wa.gov.au'),
        ('Prem', 'Neupane', 'prem.neupane@dbca.wa.gov.au'),
        ('Thu', 'Nguyen', 'thu.nguyen@dbca.wa.gov.au'),
    ],
}

ROUND2 = {
    'Silrec Admin': [
        ('Jawaid', 'Mushtaq', 'jawaid.mushtaq@dbca.wa.gov.au'),
    ],
    'Operator': [
        ('Derek', 'Winters', 'derek.winters@dbca.wa.gov.au'),
        ('Clarissa', 'Swarts', 'clarissa.swarts@dbca.wa.gov.au'),
    ],
    'Reviewer': [
        ('Xianfeng', 'Su', 'xianfeng.su@dbca.wa.gov.au'),
        ('Shelley', 'Phillips', 'shelley.phillips@dbca.wa.gov.au'),
        ('John', 'Mosaj', 'john.mosaj@dbca.wa.gov.au'),
        ('Sonia', 'Gillespie', 'sonia.gillespie@dbca.wa.gov.au'),
        ('Jodie', 'Miller', 'jodie.miller@dbca.wa.gov.au'),
        ('Lisa', 'Smith', 'lisa.smith@dbca.wa.gov.au'),
        ('Matt', 'Seymour', 'matthew.seymour@dbca.wa.gov.au'),
        ('Ben', 'Davies', 'benton.davies@dbca.wa.gov.au'),
        ('Cal', 'Burwood', 'callum.burwood@dbca.wa.gov.au'),
        ('Prem', 'Neupane', 'prem.neupane@dbca.wa.gov.au'),
        ('Thu', 'Nguyen', 'thu.nguyen@dbca.wa.gov.au'),
    ],
    'User': [
        ('Melanie', 'Dybala', 'melanie.dybala@dbca.wa.gov.au'),
        ('Jodie', 'Watts', 'jodie.watts@dbca.wa.gov.au'),
        ('Bec', 'Brown', 'rebecca.brown@dbca.wa.gov.au'),
        ('Magda', 'Bustos Hevia', 'magda.bustoshevia@dbca.wa.gov.au'),
        ('Martin', 'Van Rooyen', 'martin.vanrooyen@dbca.wa.gov.au'),
    ],
}

ROUNDS = {'round1': ROUND1, 'round2': ROUND2}


class Command(BaseCommand):
    '''
    # Round 1 (default)                                                                                                                                                                     python manage.py create_users                                                                                                                                                           python manage.py create_users --round round1                                                                                                                                                                                                                                                                                                                                    # Round 2                                                                                                                                                                               python manage.py create_users --round round2                                                                                                                                                                                                                                                                                                                                    # Remove users for a round                                                                                                                                                              python manage.py create_users --remove --round round2

    '''
    help = 'Create or remove users by round'

    def add_arguments(self, parser):
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove users instead of creating them',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all users with groups, staff, active status',
        )
        parser.add_argument(
            '--round',
            type=str,
            choices=['round1', 'round2'],
            default='round1',
            help='Which round of users to create/remove (default: round1)',
        )

    def handle(self, *args, **options):
        self.users = ROUNDS[options['round']]
        self.round = options['round']
        if options['list']:
            self._list_users()
        elif options['remove']:
            self._remove_users()
        else:
            self._create_users()

    def _list_users(self):
        GROUP_ORDER = {'Silrec Admin': 0, 'Reviewer': 1, 'Operator': 2, 'User': 3}

        def sort_key(u):
            groups = list(u.groups.values_list('name', flat=True))
            g = next((g for g in groups if g in GROUP_ORDER), None)
            return (GROUP_ORDER.get(g, 9), g or 'z', u.username)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'{"Username":35} {"Staff":6} {"Active":6} {"Superuser":10} {"Groups"}'
        ))
        self.stdout.write('-' * 120)
        for u in sorted(User.objects.all(), key=sort_key):
            groups = ', '.join(u.groups.values_list('name', flat=True)) or '-'
            self.stdout.write(
                f'{u.username:35} {str(u.is_staff):6} {str(u.is_active):6} '
                f'{str(u.is_superuser):10} {groups}'
            )

    def _create_users(self):
        for group_name, people in self.users.items():
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
        for group_name, people in self.users.items():
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
