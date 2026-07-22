import logging
import secrets
from django.conf import settings
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils import timezone

logger = logging.getLogger(__name__)

SC003_VERIFICATION_SALT = 'sc003-2step-verification'
SC002_ACTIVATION_SALT = 'sc002-account-activation'

def generate_verification_token(user_id, otp_id):
    signer = TimestampSigner(salt=SC003_VERIFICATION_SALT)
    return signer.sign_object({
        'user_id': user_id,
        'otp_id': otp_id,
        'purpose': 'otp_verification'
    })

def validate_verification_token(token):
    signer = TimestampSigner(salt=SC003_VERIFICATION_SALT)
    try:
        payload = signer.unsign_object(token, max_age=300)
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None

    if 'user_id' not in payload or 'otp_id' not in payload or 'purpose' not in payload:
        return None

    if type(payload['user_id']) is not int or type(payload['otp_id']) is not int:
        return None

    if payload['purpose'] != 'otp_verification':
        return None

    return payload

def generate_otp():
    """Generates a cryptographically secure 6-digit OTP string."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def send_otp(phone_number, otp_code):
    """Local mock delivery using logging."""
    masked = mask_phone_number(phone_number)
    if getattr(settings, 'DEBUG', False):
        logger.warning("[MOCK SMS] To: %s | Code: %s", masked, otp_code)
    else:
        logger.info("[MOCK SMS] OTP sent to: %s", masked)

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
