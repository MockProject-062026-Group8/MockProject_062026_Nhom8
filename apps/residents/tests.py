from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from apps.residents.models import Resident
from apps.rooms.models import Room, Bed, Facility

class ResidentListAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.facility = Facility.objects.create(facility_code='F01', name='Fac 1')
        cls.room = Room.objects.create(room_number='101A', facility=cls.facility)
        cls.bed = Bed.objects.create(room=cls.room, bed_number='1')

        cls.r1 = Resident.objects.create(
            resident_id='RES-001', first_name='John', last_name='Doe',
            date_of_birth='1950-01-01', status=Resident.Status.ACTIVE,
            payer_source='Medicare', referral_source='Hospital A',
            bed=cls.bed
        )
        cls.r2 = Resident.objects.create(
            resident_id='RES-002', first_name='Jane', last_name='Smith',
            date_of_birth='1960-02-02', status=Resident.Status.PENDING,
            payer_source='Medicaid', referral_source='hospital b'
        )
        cls.r3 = Resident.objects.create(
            resident_id='RES-003', first_name='Alice', last_name='Johnson',
            date_of_birth='1970-03-03', status=Resident.Status.DISCHARGED,
            payer_source='Private', referral_source='Clinic C'
        )
        cls.r4 = Resident.objects.create(
            resident_id='RES-004', first_name='Bob', last_name='Williams',
            date_of_birth='1980-04-04', status=Resident.Status.DECEASED,
            payer_source='Medicare', referral_source='Hospital A'
        )

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('sc017-resident-list-api')

    def test_01_empty_database(self):
        Resident.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['summary']['total'], 0)
        self.assertEqual(response.data['summary']['active'], 0)
        self.assertEqual(response.data['summary']['pending'], 0)
        self.assertEqual(response.data['summary']['discharged'], 0)
        self.assertEqual(response.data['results'], [])

    def test_02_exact_response_fields(self):
        response = self.client.get(self.url)
        item = response.data['results'][-1] # r1 (oldest)
        expected_keys = {
            'id', 'resident_id', 'first_name', 'last_name',
            'room_number', 'status', 'date_of_birth',
            'payer_source', 'referral_source'
        }
        self.assertEqual(set(item.keys()), expected_keys)
        self.assertEqual(item['room_number'], '101A')

    def test_03_default_pagination(self):
        # Create 30 more residents
        for i in range(30):
            Resident.objects.create(
                resident_id=f'RES-9{i:02}', first_name=f'F{i}', last_name=f'L{i}',
                status=Resident.Status.ACTIVE, date_of_birth='1950-01-01'
            )
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 34)
        self.assertEqual(len(response.data['results']), 25)

    def test_04_page_size_query_param(self):
        response = self.client.get(self.url, {'page_size': 2})
        self.assertEqual(len(response.data['results']), 2)

    def test_05_max_page_size(self):
        for i in range(105):
            Resident.objects.create(
                resident_id=f'RES-8{i:03}', first_name=f'F{i}', last_name=f'L{i}',
                status=Resident.Status.ACTIVE, date_of_birth='1950-01-01'
            )
        response = self.client.get(self.url, {'page_size': 150})
        self.assertEqual(len(response.data['results']), 100)

    def test_06_search_by_resident_id(self):
        response = self.client.get(self.url, {'search': 'RES-002'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['first_name'], 'Jane')

    def test_07_search_by_first_name(self):
        response = self.client.get(self.url, {'search': 'alice'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['resident_id'], 'RES-003')

    def test_08_search_by_last_name(self):
        response = self.client.get(self.url, {'search': 'smith'})
        self.assertEqual(response.data['count'], 1)

    def test_09_search_by_full_name(self):
        response = self.client.get(self.url, {'search': 'john doe'})
        self.assertEqual(response.data['count'], 1)

    def test_10_search_by_room_number(self):
        response = self.client.get(self.url, {'search': '101A'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['first_name'], 'John')

    def test_11_whitespace_search_ignored(self):
        response = self.client.get(self.url, {'search': '   '})
        self.assertEqual(response.data['count'], 4)

    def test_12_filter_status_active(self):
        response = self.client.get(self.url, {'status': 'ACTIVE'})
        self.assertEqual(response.data['count'], 1)

    def test_13_filter_status_pending(self):
        response = self.client.get(self.url, {'status': 'PENDING'})
        self.assertEqual(response.data['count'], 1)

    def test_14_filter_status_discharged(self):
        response = self.client.get(self.url, {'status': 'discharged'})
        self.assertEqual(response.data['count'], 1)

    def test_15_filter_status_deceased(self):
        response = self.client.get(self.url, {'status': 'DECEASED'})
        self.assertEqual(response.data['count'], 1)

    def test_16_filter_invalid_status(self):
        response = self.client.get(self.url, {'status': 'INVALID_STATUS'})
        self.assertEqual(response.status_code, 400)

    def test_17_referral_exact_case_insensitive(self):
        response = self.client.get(self.url, {'referral_source': 'HOSPITAL B'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['first_name'], 'Jane')

    def test_18_default_ordering(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['results'][0]['first_name'], 'Bob')
        self.assertEqual(response.data['results'][-1]['first_name'], 'John')

    def test_19_custom_ordering(self):
        response = self.client.get(self.url, {'ordering': 'first_name'})
        self.assertEqual(response.data['results'][0]['first_name'], 'Alice')
        self.assertEqual(response.data['results'][1]['first_name'], 'Bob')

    def test_20_invalid_ordering_fallback(self):
        response = self.client.get(self.url, {'ordering': 'invalid_col'})
        self.assertEqual(response.data['results'][0]['first_name'], 'Bob')

    def test_21_summary_without_filters(self):
        response = self.client.get(self.url)
        summary = response.data['summary']
        self.assertEqual(summary['total'], 4)
        self.assertEqual(summary['active'], 1)
        self.assertEqual(summary['pending'], 1)
        self.assertEqual(summary['discharged'], 1)

    def test_22_summary_respects_search(self):
        response = self.client.get(self.url, {'search': 'John'})
        summary = response.data['summary']
        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['active'], 1)
        self.assertEqual(summary['discharged'], 1)

    def test_23_summary_respects_referral(self):
        response = self.client.get(self.url, {'referral_source': 'Hospital A'})
        summary = response.data['summary']
        self.assertEqual(summary['total'], 2)
        self.assertEqual(summary['active'], 1)

    def test_24_summary_before_status(self):
        response = self.client.get(self.url, {'status': 'ACTIVE'})
        summary = response.data['summary']
        self.assertEqual(summary['total'], 4)
        self.assertEqual(summary['active'], 1)
        self.assertEqual(summary['pending'], 1)
        self.assertEqual(summary['discharged'], 1)

    def test_25_no_bed_room_fallback(self):
        response = self.client.get(self.url)
        item = [r for r in response.data['results'] if r['first_name'] == 'Jane'][0]
        self.assertEqual(item['room_number'], 'N/A')

    def test_26_html_route_resolves(self):
        from django.urls import resolve
        url = reverse('residents:list')
        resolver_match = resolve(url)
        self.assertEqual(resolver_match.view_name, 'residents:list')

    def test_27_api_route_resolves(self):
        from django.urls import resolve
        resolver_match = resolve('/api/v1/residents/')
        self.assertEqual(resolver_match.view_name, 'sc017-resident-list-api')

    def test_28_imports_succeed(self):
        try:
            from apps.residents.api.list_serializers import ResidentListSerializer
            from apps.residents.api.list_views import ResidentListAPIView
        except ImportError as e:
            self.fail(f"Import failed: {e}")

    def test_29_route_resolution(self):
        from django.urls import resolve
        from apps.residents.api.list_views import ResidentListAPIView
        match = resolve('/api/v1/residents/')
        self.assertEqual(match.func.view_class, ResidentListAPIView)
        self.assertEqual(match.view_name, 'sc017-resident-list-api')

    def test_30_serializer_fields(self):
        from apps.residents.api.list_serializers import ResidentListSerializer
        serializer = ResidentListSerializer()
        expected_fields = {
            'id', 'resident_id', 'first_name', 'last_name',
            'room_number', 'status', 'date_of_birth',
            'payer_source', 'referral_source'
        }
        self.assertEqual(set(serializer.fields.keys()), expected_fields)
