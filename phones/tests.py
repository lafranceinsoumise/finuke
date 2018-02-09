from django.test import TestCase

from phones.models import PhoneNumber, SMS
from phones.sms import send_new_code, is_valid_code


class ModelsTestCase(TestCase):
    def test_sms_had_random_8_digit_code(self):
        voter = PhoneNumber.objects.create(phonenumber='+33600000000')
        sms = SMS(voter=voter)

        self.assertRegex(sms.code, '[0-9]{8}')

    def test_sms_code(self):
        voter = PhoneNumber.objects.create(phonenumber='+33600000000')
        code = send_new_code(voter)
        self.assertTrue(is_valid_code(voter, code))
        self.assertFalse(is_valid_code(voter, '0'))

