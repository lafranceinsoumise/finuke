import redislite

from django.test import TestCase

from finuke.test_utils import RedisLiteMixin

from phones.models import PhoneNumber, SMS
from phones.sms import send_new_code, is_valid_code, SMSCodeException



class ModelsTestCase(RedisLiteMixin, TestCase):

    def test_can_send_limited_codes(self):
        with self.settings(SMS_BUCKET_MAX=3, SMS_BUCKET_INTERVAL=600, OVH_SMS_DISABLE=True):
            phone_number = PhoneNumber.objects.create(phone_number='+33600000000')
            send_new_code(phone_number)
            send_new_code(phone_number)
            send_new_code(phone_number)

            with self.assertRaises(SMSCodeException):
                send_new_code(phone_number)


    def test_sms_had_random_8_digit_code(self):
        phone_number = PhoneNumber.objects.create(phone_number='+33600000000')
        sms = SMS(phone_number=phone_number)

        self.assertRegex(sms.code, '[0-9]{8}')

    def test_sms_code(self):
        phone_number = PhoneNumber.objects.create(phone_number='+33600000000')

        with self.settings(OVH_SMS_DISABLE=True):
            code = send_new_code(phone_number)

        self.assertTrue(is_valid_code(phone_number, code))
        self.assertFalse(is_valid_code(phone_number, '0'))

