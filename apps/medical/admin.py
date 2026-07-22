"""
apps/medical/admin.py
SC-022 Initial Assessment - Admin Registration
"""
from django.contrib import admin
from .models import Assessment, AssessmentDetail, AssessmentDiagnosis, CareLevel


class AssessmentDetailInline(admin.TabularInline):
    model = AssessmentDetail
    extra = 0
    readonly_fields = ['item_name', 'category', 'item_key']
    fields = ['category', 'item_key', 'item_name', 'score', 'max_score', 'value', 'unit']


class AssessmentDiagnosisInline(admin.TabularInline):
    model = AssessmentDiagnosis
    extra = 0
    fields = ['diagnosis_name', 'diagnosis_code', 'is_primary', 'notes']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'resident', 'assessment_type', 'assessment_date',
        'status', 'total_adl_score', 'max_adl_score',
        'total_iadl_score', 'max_iadl_score',
        'care_level', 'assessed_by', 'created_at',
    ]
    list_filter = ['assessment_type', 'status', 'care_level', 'assessment_date']
    search_fields = [
        'resident__first_name', 'resident__last_name',
        'clinical_notes', 'allergies',
    ]
    inlines = [AssessmentDetailInline, AssessmentDiagnosisInline]
    readonly_fields = [
        'total_adl_score', 'max_adl_score',
        'total_iadl_score', 'max_iadl_score',
        'care_level', 'created_at', 'updated_at',
    ]
    date_hierarchy = 'assessment_date'


@admin.register(CareLevel)
class CareLevelAdmin(admin.ModelAdmin):
    list_display = ['level_code', 'level_name', 'sort_order', 'min_adl_ratio', 'max_adl_ratio']
    ordering = ['sort_order']