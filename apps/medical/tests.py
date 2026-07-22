from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Assessment, LOCClassification
from apps.residents.models import Resident
from apps.billing.models import LOCRate

class LOCClassificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='nurse', password='password')
        self.resident = Resident.objects.create(
            resident_id='RES_TEST',
            first_name='Test',
            last_name='Resident',
            date_of_birth='1950-01-01'
        )
        self.assessment = Assessment.objects.create(
            resident=self.resident,
            total_adl_score=20
        )
        LOCRate.objects.create(loc_level='Level 3', daily_rate='248.00')

    def test_loc_detail_view(self):
        self.client.login(username='nurse', password='password')
        response = self.client.get(reverse('medical:loc_detail', args=[self.assessment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '20 / 32')
        self.assertContains(response, 'Level 3')

    def test_loc_confirm(self):
        self.client.login(username='nurse', password='password')
        self.client.get(reverse('medical:loc_detail', args=[self.assessment.id])) # Trigger get_or_create
        response = self.client.post(reverse('medical:loc_confirm', args=[self.assessment.id]))
        self.assertEqual(response.status_code, 302)
        
        loc = LOCClassification.objects.get(assessment=self.assessment)
        self.assertEqual(loc.status, 'Confirmed')
        self.assertEqual(loc.final_loc, 'Level 3')

    def test_loc_override(self):
        self.client.login(username='nurse', password='password')
        self.client.get(reverse('medical:loc_detail', args=[self.assessment.id])) # Trigger get_or_create
        response = self.client.post(reverse('medical:loc_override', args=[self.assessment.id]), {
            'override_loc': 'Level 4',
            'override_reason': 'Needs more help'
        })
        self.assertEqual(response.status_code, 302)
        
        loc = LOCClassification.objects.get(assessment=self.assessment)
        self.assertEqual(loc.status, 'Confirmed')
        self.assertTrue(loc.is_overridden)
        self.assertEqual(loc.final_loc, 'Level 4')

    def test_loc_chart_lock(self):
        LOCClassification.objects.create(
            assessment=self.assessment,
            calculated_score=20,
            suggested_loc='Level 3',
            final_loc='Level 3',
            status='Confirmed'
        )
        
        self.client.login(username='nurse', password='password')
        response = self.client.post(reverse('medical:loc_confirm', args=[self.assessment.id]))
        self.assertEqual(response.status_code, 400) 

        response = self.client.post(reverse('medical:loc_override', args=[self.assessment.id]), {
            'override_loc': 'Level 4',
            'override_reason': 'test'
        })
        self.assertEqual(response.status_code, 400)
