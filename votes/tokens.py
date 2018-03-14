from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac
from base64 import urlsafe_b64encode, urlsafe_b64decode


class MailTokenGenerator:
    key_salt = "votes.fe_crypto.MailTokenGenerator"
    secret = settings.SECRET_KEY
    separator = '.'

    def make_token(self, email):
        return self._make_token(self._encode_email(email))

    def _encode_email(self, email):
        return urlsafe_b64encode(email.encode('utf8')).decode('ascii').rstrip('=')

    def _decode_email(self, encoded_email):
        missing_equals = (4 -len(encoded_email) % 4) % 4
        return urlsafe_b64decode((encoded_email + '=' * missing_equals).encode('ascii')).decode('utf8')

    def _make_token(self, encoded_email):
        hash = salted_hmac(
            self.key_salt,
            encoded_email,
            secret=self.secret
        ).hexdigest()[::2]

        return f"{encoded_email}{self.separator}{hash}"

    def check_token(self, token):
        try:
            encoded_email, hash = token.split(self.separator)
        except ValueError:
            return None

        if not constant_time_compare(self._make_token(encoded_email), token):
            return None

        try:
            return self._decode_email(encoded_email)
        except ValueError:
            return None

mail_token_generator = MailTokenGenerator()
