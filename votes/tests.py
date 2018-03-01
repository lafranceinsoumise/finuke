from django.test import TestCase
from django.urls import reverse


class DisplayPageTestCase(TestCase):
    def test_validate_list_display(self):
        response = self.client.get(reverse('validate_list'))
        self.assertEqual(response.status_code, 200)
