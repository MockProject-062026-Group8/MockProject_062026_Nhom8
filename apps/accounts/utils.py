from django.core.signing import TimestampSigner
from django.utils import timezone

SC003_VERIFICATION_SALT = 'sc003-2step-verification'
SC002_ACTIVATION_SALT = 'sc002-account-activation'

def generate_verification_token(user_id):
    signer = TimestampSigner(salt=SC003_VERIFICATION_SALT)
    return signer.sign_object({
        'user_id': user_id,
        'purpose': 'otp_verification'
    })

def generate_activation_token(user):
    signer = TimestampSigner(salt=SC002_ACTIVATION_SALT)
    return signer.sign_object({
        'user_id': user.id,
        'purpose': 'account_activation',
        'issued_at': timezone.now().isoformat()
    })

def mask_phone_number(phone_number):
    if not phone_number or len(phone_number) < 4:
        return None
    return "******" + phone_number[-4:]
