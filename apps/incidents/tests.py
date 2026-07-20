from django.test import TestCase
from .models import SeverityLevel


class SeverityLevelModelTest(TestCase):
    def test_str(self):
        level = SeverityLevel(name='Minor')
        self.assertEqual(str(level), 'Minor')
