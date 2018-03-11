import redislite

from django.test import TestCase

from finuke.test_utils import RedisLiteMixin
from finuke.exceptions import RateLimitedException
from phones.models import PhoneNumber, SMS
from phones.sms import send_new_code, is_valid_code


class ModelsTestCase(RedisLiteMixin, TestCase):
    def test_can_send_limited_codes(self):
        with self.settings(SMS_BUCKET_MAX=3, SMS_BUCKET_INTERVAL=600, OVH_SMS_DISABLE=True):
            phone_number = PhoneNumber.objects.create(phone_number='+33600000000')
            send_new_code(phone_number, ip='random')
            with self.assertRaises(RateLimitedException):
                send_new_code(phone_number, ip='random')

            # test for ip limiting
            for i in range(1, 31):
                send_new_code(PhoneNumber.objects.create(phone_number='+336000000{}'.format(str(i).zfill(2))), ip='127.0.0.1')

            with self.assertRaises(RateLimitedException):
                send_new_code(PhoneNumber.objects.create(phone_number='+33600000031'), ip='127.0.0.1')

    def test_sms_had_random_8_digit_code(self):
        phone_number = PhoneNumber.objects.create(phone_number='+33600000000')
        sms = SMS(phone_number=phone_number)

        self.assertRegex(sms.code, '[0-9]{8}')

    def test_sms_code(self):
        phone_number = PhoneNumber.objects.create(phone_number='+33600000000')

        with self.settings(OVH_SMS_DISABLE=True):
            code = send_new_code(phone_number, ip='random')

        self.assertTrue(is_valid_code(phone_number, code))
        self.assertFalse(is_valid_code(phone_number, '0'))

