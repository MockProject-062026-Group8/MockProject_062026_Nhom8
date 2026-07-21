from datetime import datetime, timedelta, timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.db import transaction
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth.hashers import check_password, make_password

from apps.accounts.models import User
from apps.accounts.utils import generate_verification_token, mask_phone_number, SC002_ACTIVATION_SALT
from .serializers import LoginSerializer, ActivationSerializer

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
        verification_token = generate_verification_token(user.id)

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