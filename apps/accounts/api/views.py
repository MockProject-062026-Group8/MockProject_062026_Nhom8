from datetime import datetime, timedelta, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.db import transaction
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.hashers import check_password, make_password

from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import User, OTP
from apps.accounts.utils import (
    generate_verification_token,
    mask_phone_number,
    SC002_ACTIVATION_SALT,
    generate_otp,
    send_otp,
    validate_verification_token
)
from .serializers import (
    LoginSerializer,
    ActivationSerializer,
    OTPVerifySerializer,
    OTPResendSerializer
)

class LoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Identifier and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        identifier = serializer.validated_data.get('identifier')
        raw_password = serializer.validated_data.get('password')

        user = User.objects.filter(
            Q(email__iexact=identifier) | Q(phone_number=identifier)
        ).first()

        if not user:
            return Response(
                {"detail": "Invalid email/phone or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(raw_password, user.password_hash):
            return Response(
                {"detail": "Invalid email/phone or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if user.status != User.Status.ACTIVE:
            return Response(
                {"detail": "Invalid email/phone or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        masked_phone = mask_phone_number(user.phone_number)
        if not masked_phone:
            return Response(
                {"detail": "Invalid email/phone or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Success (ACTIVE)
        with transaction.atomic():
            user = User.objects.select_for_update().get(id=user.id)
            OTP.objects.filter(user=user, is_consumed=False).update(is_consumed=True)

            otp_code = generate_otp()
            otp = OTP.objects.create(
                user=user,
                otp_hash=make_password(otp_code),
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=300)
            )

            verification_token = generate_verification_token(user.id, otp.id)

            transaction.on_commit(lambda: send_otp(user.phone_number, otp_code))

        return Response({
            "verification_token": verification_token,
            "phone_number": masked_phone,
            "mfa_required": True
        }, status=status.HTTP_200_OK)

class ActivationAPIView(APIView):
    def _validate_token_and_get_user(self, token):
        signer = TimestampSigner(salt=SC002_ACTIVATION_SALT)
        try:
            payload = signer.unsign_object(token, max_age=72*60*60)
        except (BadSignature, SignatureExpired):
            return None, None

        if not isinstance(payload, dict):
            return None, None

        if 'user_id' not in payload or 'purpose' not in payload or 'issued_at' not in payload:
            return None, None

        if not isinstance(payload['user_id'], int):
            return None, None

        if payload['purpose'] != 'account_activation':
            return None, None

        try:
            issued_at = datetime.fromisoformat(payload['issued_at'])
            if issued_at.tzinfo is None:
                return None, None
            payload['issued_at_dt'] = issued_at.astimezone(timezone.utc)
        except (ValueError, TypeError):
            return None, None

        user = User.objects.filter(id=payload['user_id'], status=User.Status.INACTIVE).first()
        return user, payload

    def get(self, request, token, *args, **kwargs):
        user, payload = self._validate_token_and_get_user(token)
        if not user:
            return Response(
                {"detail": "Activation link is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        issued_at = payload['issued_at_dt']
        expires_at = issued_at + timedelta(hours=72)

        return Response({
            "email": user.email,
            "phone_number": user.phone_number,
            "status": user.status,
            "expires_at": expires_at.isoformat().replace('+00:00', 'Z')
        }, status=status.HTTP_200_OK)

    def post(self, request, token, *args, **kwargs):
        user, _ = self._validate_token_and_get_user(token)
        if not user:
            return Response(
                {"detail": "Activation link is invalid or expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ActivationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Reload user with select_for_update to prevent concurrent activation
            locked_user = User.objects.select_for_update().filter(id=user.id, status=User.Status.INACTIVE).first()
            if not locked_user:
                return Response(
                    {"detail": "Activation link is invalid or expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            locked_user.password_hash = make_password(serializer.validated_data['password'])
            locked_user.phone_number = serializer.validated_data['phone_number']
            locked_user.status = User.Status.ACTIVE
            locked_user.mfa_enabled = True
            locked_user.save(update_fields=['password_hash', 'phone_number', 'status', 'mfa_enabled', 'updated_at'])

        return Response({
            "id": locked_user.id,
            "email": locked_user.email,
            "phone_number": locked_user.phone_number,
            "status": locked_user.status,
            "mfa_enabled": True
        }, status=status.HTTP_200_OK)

class OTPVerifyAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = OTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['verification_token']
        otp_code = serializer.validated_data['otp_code']

        payload = validate_verification_token(token)
        if not payload:
            return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(id=payload['user_id'])
                otp = OTP.objects.select_for_update().get(id=payload['otp_id'], user=user)
            except (User.DoesNotExist, OTP.DoesNotExist):
                return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            if user.status != User.Status.ACTIVE:
                return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            if otp.is_consumed or otp.expires_at <= datetime.now(timezone.utc):
                return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            if not check_password(otp_code, otp.otp_hash):
                return Response({"detail": "The verification code is invalid."}, status=status.HTTP_400_BAD_REQUEST)

            otp.is_consumed = True
            otp.save(update_fields=['is_consumed'])

            user.last_login_at = datetime.now(timezone.utc)
            user.save(update_fields=['last_login_at'])

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.role_name if user.role else ""
            }
        }, status=status.HTTP_200_OK)

class OTPResendAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = OTPResendSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['verification_token']
        payload = validate_verification_token(token)
        if not payload:
            return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(id=payload['user_id'])
                old_otp = OTP.objects.select_for_update().get(id=payload['otp_id'], user=user)
            except (User.DoesNotExist, OTP.DoesNotExist):
                return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            if user.status != User.Status.ACTIVE:
                return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            if old_otp.is_consumed:
                return Response({"detail": "The verification code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

            old_otp.is_consumed = True
            old_otp.save(update_fields=['is_consumed'])

            new_otp_code = generate_otp()
            new_otp = OTP.objects.create(
                user=user,
                otp_hash=make_password(new_otp_code),
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=300)
            )

            new_token = generate_verification_token(user.id, new_otp.id)

            transaction.on_commit(lambda: send_otp(user.phone_number, new_otp_code))

        return Response({
            "verification_token": new_token,
            "phone_number": mask_phone_number(user.phone_number),
            "expires_in": 300
        }, status=status.HTTP_200_OK)
