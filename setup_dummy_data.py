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

# Fix missing Holidays table in SQLite
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS "Holidays" (
            "HolidayID" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "HolidayDate" date NOT NULL UNIQUE,
            "HolidayName" varchar(250) NOT NULL,
            "IsNationalHoliday" bool NOT NULL,
            "Description" varchar(500) NULL,
            "CreatedAt" datetime NOT NULL
        )
    ''')

# Seed a dummy holiday for testing
from apps.medical.models import Holiday
from datetime import date
Holiday.objects.get_or_create(
    holiday_date=date(2026, 7, 30),
    defaults={
        'holiday_name': 'Test Holiday',
        'is_national_holiday': True
    }
)

print("Dummy data setup complete.")
