from rest_framework import serializers
from apps.medical.models import ResidentCareLevelHistory, LOCClassificationHistory

from django.db import transaction
from django.contrib.auth.hashers import make_password
from apps.medical.models import PreAdmissionScreening
from apps.residents.models import Admission, Resident
from apps.rooms.models import Bed

from rest_framework import serializers
from apps.medical.models import CareLevel, CarePlan, CareGoal


class ResidentCareLevelHistorySerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source='action_at')
    new_tier = serializers.CharField(source='loc_classification.final_loc')
    previous_tier = serializers.SerializerMethodField()
    note = serializers.CharField(source='details')

    class Meta:
        model = LOCClassificationHistory
        fields = [
            'id', 'date', 'action', 'previous_tier', 
            'new_tier', 'actor_name', 'note'
        ]

    def get_actor_name(self, obj):
        if obj.action_by:
            return obj.action_by.get_full_name() or obj.action_by.username
        return "System"
        
    def get_previous_tier(self, obj):
        return ""



class PreAdmissionScreeningSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreAdmissionScreening
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'screened_by']

    def validate(self, data):
        # Validation for BR-06: Override reason required if flagged
        compliance_flagged = data.get('compliance_flagged', False)
        acuity_level = data.get('acuity_level')
        clinical_needs = data.get('clinical_needs', [])
        
        errors = {}
        if not acuity_level:
            errors['acuity_level'] = 'Acuity Level is required.'
        if not clinical_needs or len(clinical_needs) == 0:
            errors['clinical_needs'] = 'Please select at least one clinical need.'
            
        if errors:
            raise serializers.ValidationError(errors)
        
        # Auto flag if acuity is Moderate or High (simulated compliance check)
        if acuity_level in [PreAdmissionScreening.AcuityLevel.MODERATE, PreAdmissionScreening.AcuityLevel.HIGH]:
            compliance_flagged = True
            data['compliance_flagged'] = True
            
        if compliance_flagged:
            override_reason = data.get('override_reason')
            if not override_reason or len(override_reason.strip()) < 20:
                raise serializers.ValidationError({
                    'override_reason': 'Override reason is required and must be at least 20 characters when compliance check is flagged or acuity level is Moderate/High.'
                })
        
        return data

class AdmissionCreateSerializer(serializers.ModelSerializer):
    bed_id = serializers.IntegerField(write_only=True, required=True)
    
    # Extra fields for Care Team and Payer
    physician_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    physician_npi = serializers.CharField(write_only=True, required=False, allow_blank=True)
    nurse_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    payer_source = serializers.CharField(write_only=True, required=False, allow_blank=True)
    payer_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Admission
        fields = [
            'resident', 'facility', 'admission_date', 
            'verification_method', 'consent_signature', 'consent_file',
            'bed_id', 'order_date',
            'physician_name', 'physician_npi', 'nurse_name',
            'payer_source', 'payer_name'
        ]

    @transaction.atomic
    def create(self, validated_data):
        from apps.accounts.models import User, Role
        from apps.billing.models import InsuranceProvider, ResidentInsurancePolicy
        
        bed_id = validated_data.pop('bed_id', None)
        physician_name = validated_data.pop('physician_name', None)
        physician_npi = validated_data.pop('physician_npi', None)
        nurse_name = validated_data.pop('nurse_name', None)
        payer_source = validated_data.pop('payer_source', None)
        payer_name = validated_data.pop('payer_name', None)
        
        validated_data['admitting_physician'] = self._provision_physician(physician_name, physician_npi, User, Role)
        validated_data['admitting_nurse'] = self._provision_nurse(nurse_name, User, Role)
        self._provision_insurance(validated_data['resident'], payer_name, payer_source, validated_data['admission_date'], InsuranceProvider, ResidentInsurancePolicy)

        
        # Save Admission record
        admission = Admission.objects.create(**validated_data)
        
        # Update Bed Status
        bed = None
        if bed_id:
            bed = Bed.objects.filter(pk=bed_id).first()
            if not bed:
                raise serializers.ValidationError({'bed_id': 'Invalid bed ID provided.'})
            bed.status = 'OCCUPIED'
            bed.save()
            
        # Update Resident Status & Bed
        resident = validated_data['resident']
        resident.status = Resident.Status.ACTIVE
        if bed:
            resident.bed = bed
        resident.save()
            
        return admission

    def _provision_physician(self, physician_name, physician_npi, User, Role):
        if not physician_name:
            return None
        role_doctor, _ = Role.objects.get_or_create(role_name='Doctor')
        physician = User.objects.filter(last_name=physician_name, npi=physician_npi).first()
        if not physician:
            physician = User.objects.create(
                employee_code=f"DOC_{physician_npi or 'TEMP'}",
                email=f"doc_{physician_npi or 'temp'}@test.com",
                password_hash=make_password('temp_password_123!'),
                first_name='',
                last_name=physician_name,
                npi=physician_npi,
                role=role_doctor
            )
        return physician
        
    def _provision_nurse(self, nurse_name, User, Role):
        if not nurse_name:
            return None
        role_nurse, _ = Role.objects.get_or_create(role_name='Nurse')
        nurse = User.objects.filter(last_name=nurse_name).first()
        if not nurse:
            nurse = User.objects.create(
                employee_code=f"NUR_{nurse_name.replace(' ', '')}",
                email=f"nur_{nurse_name.replace(' ', '')}@test.com",
                password_hash=make_password('temp_password_123!'),
                first_name='',
                last_name=nurse_name,
                role=role_nurse
            )
        return nurse
        
    def _provision_insurance(self, resident, payer_name, payer_source, admission_date, InsuranceProvider, ResidentInsurancePolicy):
        if not payer_source and not payer_name:
            return
        provider, _ = InsuranceProvider.objects.get_or_create(
            provider_name=payer_name or payer_source,
            defaults={'provider_type': payer_source or 'OTHER'}
        )
        ResidentInsurancePolicy.objects.get_or_create(
            resident=resident,
            insurance_provider=provider,
            defaults={
                'policy_number_encrypted': 'PENDING_AT_ADMISSION',
                'effective_from': admission_date
            }
        )




class CareLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareLevel
        fields = "__all__"


class CarePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarePlan
        fields = "__all__"


class CareGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareGoal
        fields = "__all__"