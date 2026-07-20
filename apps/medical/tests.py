from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from apps.residents.models import Resident
from apps.medical.models import Assessment

class AssessmentHistoryTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nurse', password='password123')
        # Assign permission
        view_perm = Permission.objects.get(codename='view_assessment')
        add_perm = Permission.objects.get(codename='add_assessment')
        self.user.user_permissions.add(view_perm, add_perm)
        
        self.resident = Resident.objects.create(
            resident_id='RES001',
            full_name='Robert Hayes',
            room_number='101A',
            date_of_birth='1950-01-01',
            admission_date='2025-01-01'
        )

        self.assessment_v1 = Assessment.objects.create(
            resident=self.resident,
            version=1,
            assessment_type='initial',
            author=self.user,
            total_adl_score=14,
            loc_tier='Level 2',
            is_locked=True
        )

    def test_assessment_history_view(self):
        self.client.login(username='nurse', password='password123')
        response = self.client.get(reverse('medical:assessment_history', args=[self.resident.resident_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Assessment History — Robert Hayes')
        self.assertContains(response, 'v1')
        self.assertContains(response, 'Initial')

    def test_create_reassessment_api(self):
        self.client.login(username='nurse', password='password123')
        response = self.client.post(reverse('medical:create_reassessment', args=[self.resident.resident_id]))
        # Should redirect back to history
        self.assertEqual(response.status_code, 302)
        
        # Verify new assessment was created
        new_assessment = Assessment.objects.filter(resident=self.resident).order_by('-version').first()
        self.assertEqual(new_assessment.version, 2)
        self.assertEqual(new_assessment.assessment_type, 'reassessment')
        self.assertEqual(new_assessment.total_adl_score, 14) # Copied from v1
        self.assertFalse(new_assessment.is_locked) # New draft is unlocked
