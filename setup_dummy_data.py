import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User, Permission
from apps.residents.models import Resident
from apps.medical.models import Assessment
from apps.billing.models import LOCRate

# Create superuser
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
else:
    user = User.objects.get(username='admin')

# Give permissions
try:
    view_perm = Permission.objects.get(codename='view_assessment')
    add_perm = Permission.objects.get(codename='add_assessment')
    user.user_permissions.add(view_perm, add_perm)
except Exception as e:
    print("Permissions issue:", e)

# Create Resident
res, created = Resident.objects.get_or_create(
    resident_id='RES001',
    defaults={
        'first_name': 'Robert',
        'last_name': 'Hayes',
        'date_of_birth': '1950-01-01',
    }
)

# Setup Rates
rates = [
    {'loc_level': 'Level 1', 'daily_rate': '100.00'},
    {'loc_level': 'Level 2', 'daily_rate': '180.00'},
    {'loc_level': 'Level 3', 'daily_rate': '248.00'},
    {'loc_level': 'Level 4', 'daily_rate': '320.00'},
]
for r in rates:
    LOCRate.objects.get_or_create(loc_level=r['loc_level'], defaults={'daily_rate': r['daily_rate']})

# Create Assessment
# if not Assessment.objects.filter(resident=res).exists():
#     Assessment.objects.create(
#         resident=res,
#         version=3,
#         assessment_type='initial',
#         author=user,
#         total_adl_score=20,
#         adl_bed_mobility=2,
#         adl_transfer=3,
#         adl_locomotion=3,
#         adl_dressing=2,
#         adl_eating=1,
#         adl_toilet_use=3,
#         adl_personal_hygiene=3,
#         adl_bathing=3,
#         loc_tier=None,
#         is_locked=False
#     )
print("Dummy data setup complete.")
