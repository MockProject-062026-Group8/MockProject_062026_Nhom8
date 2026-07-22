from rest_framework import serializers
from apps.residents.models import Resident

class ResidentListSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(read_only=True)
    class Meta:
        model = Resident
        fields = ['id', 'resident_id', 'first_name', 'last_name', 'room_number', 'status', 'date_of_birth', 'payer_source', 'referral_source']
