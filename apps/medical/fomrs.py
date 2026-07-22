"""
apps/medical/fomrs.py
SC-022 Initial Assessment - Forms
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Assessment, AssessmentDiagnosis, AssessmentDetail


# ─── Hằng số dùng chung ───
ADL_ITEMS = [
    ('bathing', 'Bathing'),
    ('dressing', 'Dressing'),
    ('toileting', 'Toileting'),
    ('transferring', 'Transferring'),
    ('continence', 'Continence'),
    ('feeding', 'Feeding'),
    ('mobility', 'Mobility'),
]

IADL_ITEMS = [
    ('phone', 'Using Telephone'),
    ('shopping', 'Shopping'),
    ('food_prep', 'Food Preparation'),
    ('housekeeping', 'Housekeeping'),
    ('laundry', 'Laundry'),
    ('transportation', 'Transportation'),
    ('medications', 'Medications'),
    ('finances', 'Finances'),
]

VITAL_SIGN_ITEMS = [
    ('blood_pressure', 'Blood Pressure', 'mmHg'),
    ('heart_rate', 'Heart Rate', 'bpm'),
    ('temperature', 'Temperature', '°F'),
    ('respiratory_rate', 'Respiratory Rate', 'bpm'),
    ('oxygen_saturation', 'Oxygen Saturation', '%'),
]

ADL_SCORE_CHOICES = [
    (0, '0 – Total Dependence'),
    (1, '1 – Maximum Assistance'),
    (2, '2 – Moderate Assistance'),
    (3, '3 – Minimal Assistance'),
    (4, '4 – Complete Independence'),
]

IADL_SCORE_CHOICES = [
    (0, '0 – Dependent'),
    (1, '1 – Independent'),
]

COGNITIVE_CHOICES = Assessment.COGNITIVE_STATUS_CHOICES


# ─── Form chính ───
class AssessmentForm(forms.ModelForm):
    """Form cho phần thông tin tổng quan của Assessment"""

    class Meta:
        model = Assessment
        fields = [
            'assessment_type',
            'assessment_date',
            'cognitive_status',
            'allergies',
            'clinical_notes',
        ]
        widgets = {
            'assessment_type': forms.Select(
                attrs={'class': 'form-control', 'id': 'assessment_type'}
            ),
            'assessment_date': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'id': 'assessment_date',
                    'type': 'datetime-local',
                }
            ),
            'cognitive_status': forms.Select(
                attrs={'class': 'form-control', 'id': 'cognitive_status'}
            ),
            'allergies': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'id': 'allergies',
                    'placeholder': 'e.g., NKDA, Penicillin – rash',
                }
            ),
            'clinical_notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'id': 'clinical_notes',
                    'rows': 4,
                    'placeholder': 'Enter clinical notes and recommendations...',
                }
            ),
        }


class DiagnosisForm(forms.ModelForm):
    """Form thêm chẩn đoán (dùng cho inline / AJAX)"""

    class Meta:
        model = AssessmentDiagnosis
        fields = ['diagnosis_name', 'diagnosis_code', 'is_primary', 'notes']
        widgets = {
            'diagnosis_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g., Osteoarthritis – bilateral knees',
                    'id': 'diag_name',
                }
            ),
            'diagnosis_code': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'ICD-10 (optional)',
                    'id': 'diag_code',
                }
            ),
            'is_primary': forms.CheckboxInput(
                attrs={'class': 'form-check-input', 'id': 'diag_primary'}
            ),
            'notes': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Notes (optional)',
                    'id': 'diag_notes',
                }
            ),
        }

    def clean_diagnosis_name(self):
        name = self.cleaned_data.get('diagnosis_name', '').strip()
        if not name:
            raise ValidationError('Diagnosis name is required.')
        return name