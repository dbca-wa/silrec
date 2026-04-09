import os
import sys
import django
proj_path='/var/www/silrec'
sys.path.append(proj_path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "silrec.settings")
django.setup()


from silrec.components.proposals.models import Proposal

p=Proposal.objects.last()

print(p.__dict__)

