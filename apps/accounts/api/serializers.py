import re
from rest_framework import serializers

class OTPVerifySerializer(serializers.Serializer):
    verification_token = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True)

    def validate_otp_code(self, value):
        if not re.fullmatch(r'^\d{6}$', value):
            raise serializers.ValidationError("OTP code must contain exactly 6 digits.")
        return value

class OTPResendSerializer(serializers.Serializer):
    verification_token = serializers.CharField(required=True)

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True, allow_blank=False, max_length=255)
    password = serializers.CharField(required=True, allow_blank=False, trim_whitespace=False, write_only=True)

class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if not isinstance(data, bool):
            self.fail('invalid')
        return super().to_internal_value(data)

class ActivationSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, allow_blank=False, trim_whitespace=False, write_only=True)
    confirm_password = serializers.CharField(required=True, allow_blank=False, trim_whitespace=False, write_only=True)
    phone_number = serializers.CharField(required=True, allow_blank=False)
    accept_terms = StrictBooleanField(
        required=True,
        error_messages={
            'invalid': 'You must accept the Terms of Use and Privacy Policy.',
            'required': 'You must accept the Terms of Use and Privacy Policy.',
            'null': 'You must accept the Terms of Use and Privacy Policy.'
        }
    )

    def validate_password(self, value):
        if value != value.strip():
            raise serializers.ValidationError("Password must not begin or end with whitespace.")

        if len(value) < 8 or not re.search(r'[A-Z]', value) or not re.search(r'[a-z]', value) or not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must be at least 8 characters and include uppercase, lowercase, and a number.")
        return value

    def validate_phone_number(self, value):
        if not re.fullmatch(r'^\+[1-9]\d{7,14}$', value):
            raise serializers.ValidationError("Enter a valid phone number in E.164 format.")
        return value

    def validate_accept_terms(self, value):
        if value is not True:
            raise serializers.ValidationError("You must accept the Terms of Use and Privacy Policy.")
        return value

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data