from django.test import TestCase

from phones.models import PhoneNumber, SMS
from phones.sms import send_new_code, is_valid_code


class ModelsTestCase(TestCase):
    def test_sms_had_random_8_digit_code(self):
        phone_number = PhoneNumber.objects.create(phone_number='+33600000000')
        sms = SMS(phone_number=phone_number)

        self.assertRegex(sms.code, '[0-9]{8}')

    def test_sms_code(self):
        phone_number = PhoneNumber.objects.create(phone_number='+33600000000')
        code = send_new_code(phone_number)
        self.assertTrue(is_valid_code(phone_number, code))
        self.assertFalse(is_valid_code(phone_number, '0'))

