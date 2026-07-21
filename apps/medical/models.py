
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from apps.residents.models import Resident


# ==========================================
# 1. CARE LEVEL MODELS
# ==========================================
class CareLevel(models.Model):
    class LevelCode(models.TextChoices):
        INDEPENDENT_LIVING = 'INDEPENDENT_LIVING', 'Independent Living'
        ASSISTED_LIVING = 'ASSISTED_LIVING', 'Assisted Living'
        MEMORY_CARE = 'MEMORY_CARE', 'Memory Care'
        SKILLED_NURSING = 'SKILLED_NURSING', 'Skilled Nursing'
        HOSPICE = 'HOSPICE', 'Hospice'

    level_code = models.CharField(max_length=30, unique=True, choices=LevelCode.choices)
    level_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    min_adl_ratio = models.FloatField(null=True, blank=True)
    max_adl_ratio = models.FloatField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'care_levels'
        ordering = ['sort_order']
        verbose_name = 'Care Level'
        verbose_name_plural = 'Care Levels'

    def __str__(self):
        return self.level_name


class CareLevelRate(models.Model):
    care_level = models.ForeignKey(CareLevel, on_delete=models.CASCADE)
    facility = models.ForeignKey('rooms.Facility', on_delete=models.CASCADE)
    daily_rate = models.DecimalField(max_digits=18, decimal_places=2)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'care_level_rates'


class ResidentCareLevelHistory(models.Model):
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE)
    care_level = models.ForeignKey(CareLevel, on_delete=models.CASCADE)

    class Meta:
        db_table = 'resident_care_level_history'


# ==========================================
# 2. SCREENING & CLINICAL RECORDS
# ==========================================
class PreAdmissionScreening(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        COMPLETED = 'COMPLETED', 'Completed'
        REJECTED = 'REJECTED', 'Rejected'
        
    class AcuityLevel(models.TextChoices):
        LOW = 'LOW', 'Low'
        MODERATE = 'MODERATE', 'Moderate'
        HIGH = 'HIGH', 'High'

    status = models.CharField(max_length=20, choices=Status.choices)
    acuity_level = models.CharField(max_length=20, choices=AcuityLevel.choices, null=True, blank=True)
    estimated_care_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    clinical_needs = models.JSONField(default=list, blank=True)
    special_requirements = models.TextField(null=True, blank=True)
    compliance_flagged = models.BooleanField(default=False)
    override_reason = models.TextField(null=True, blank=True)
    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE)
    screened_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, db_column='screened_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pre_admission_screenings'


class ClinicalRecord(models.Model):
    class RecordType(models.TextChoices):
        PROGRESS_NOTE = 'PROGRESS_NOTE', 'Progress Note'
        DIAGNOSIS = 'DIAGNOSIS', 'Diagnosis'
        LAB_RESULT = 'LAB_RESULT', 'Lab Result'
        ALLERGY = 'ALLERGY', 'Allergy'

    record_type = models.CharField(max_length=50, choices=RecordType.choices)
    description = models.TextField()
    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, db_column='recorded_by')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clinical_records'


# ==========================================
# 3. ASSESSMENT & SCORING MODELS (SC-022 & DEV)
# ==========================================
class AssessmentMetric(models.Model):
    class Category(models.TextChoices):
        ADL = 'ADL', 'ADL'
        IADL = 'IADL', 'IADL'
        BRADEN = 'BRADEN', 'Braden'
        MORSE = 'MORSE', 'Morse'

    category = models.CharField(max_length=50, choices=Category.choices)
    metric_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'assessment_metrics'


class Assessment(models.Model):
    ASSESSMENT_TYPE_CHOICES = [
        ('initial', 'Initial Assessment'),
        ('periodic', 'Periodic Assessment'),
        ('quarterly', 'Quarterly Assessment'),
        ('annual', 'Annual Assessment'),
        ('change_of_condition', 'Change of Condition'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
    ]

    COGNITIVE_STATUS_CHOICES = [
        ('alert_oriented', 'Alert & Oriented'),
        ('alert_oriented_x1', 'Alert & Oriented x1'),
        ('alert_oriented_x2', 'Alert & Oriented x2'),
        ('alert_oriented_x3', 'Alert & Oriented x3'),
        ('confused', 'Confused'),
        ('lethargic', 'Lethargic'),
        ('obtunded', 'Obtunded'),
        ('stupor', 'Stupor'),
        ('coma', 'Coma'),
    ]

    CARE_LEVEL_CHOICES = [
        ('independent', 'Independent'),
        ('minimal_assist', 'Minimal Assist'),
        ('moderate_assist', 'Moderate Assist'),
        ('maximum_assist', 'Maximum Assist'),
        ('total_care', 'Total Care'),
    ]

    # --- Liên kết cư dân & người đánh giá ---
    resident = models.ForeignKey(
        'residents.Resident',
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name='Resident',
    )
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assessments_performed',
        db_column='assessed_by',
        verbose_name='Assessed By',
    )

    # --- Thông tin trạng thái & phiên bản ---
    version = models.IntegerField(default=1)
    assessment_type = models.CharField(max_length=30, choices=ASSESSMENT_TYPE_CHOICES, default='initial')
    assessment_date = models.DateTimeField(verbose_name='Assessment Date', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_locked = models.BooleanField(default=False)
    is_overridden = models.BooleanField(default=False)

    # --- Đánh giá lâm sàng ---
    cognitive_status = models.CharField(max_length=30, choices=COGNITIVE_STATUS_CHOICES, blank=True, default='')
    care_level = models.CharField(max_length=20, choices=CARE_LEVEL_CHOICES, blank=True, default='')
    suggested_care_level = models.ForeignKey(CareLevel, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    confirmed_care_level = models.ForeignKey(CareLevel, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    
    allergies = models.TextField(blank=True, default='')
    clinical_notes = models.TextField(blank=True, default='')
    
    # --- Điểm số ADL & IADL ---
    total_adl_score = models.IntegerField(default=0)
    max_adl_score = models.IntegerField(default=32)
    total_iadl_score = models.IntegerField(default=0)
    max_iadl_score = models.IntegerField(default=8)
    adl_total_score = models.IntegerField(default=0)  # Giữ lại để tương thích với code cũ của dev

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assessments'
        ordering = ['-created_at']
        verbose_name = 'Assessment'
        verbose_name_plural = 'Assessments'

    def __str__(self):
        return f"Assessment v{self.version} ({self.get_assessment_type_display()}) - {self.resident}"

    def recalculate_scores(self):
        adl_items = self.details.filter(category='adl')
        self.total_adl_score = sum(item.score or 0 for item in adl_items)
        self.adl_total_score = self.total_adl_score
        self.max_adl_score = sum(item.max_score or 0 for item in adl_items)
        
        iadl_items = self.details.filter(category='iadl')
        self.total_iadl_score = sum(item.score or 0 for item in iadl_items)
        self.max_iadl_score = sum(item.max_score or 0 for item in iadl_items)
        
        if self.max_adl_score > 0:
            ratio = self.total_adl_score / self.max_adl_score
            if ratio >= 0.9:
                self.care_level = 'independent'
            elif ratio >= 0.7:
                self.care_level = 'minimal_assist'
            elif ratio >= 0.5:
                self.care_level = 'moderate_assist'
            elif ratio >= 0.25:
                self.care_level = 'maximum_assist'
            else:
                self.care_level = 'total_care'
                
        self.save(update_fields=[
            'total_adl_score', 'adl_total_score', 'max_adl_score',
            'total_iadl_score', 'max_iadl_score',
            'care_level', 'updated_at',
        ])


class AssessmentDetail(models.Model):
    CATEGORY_CHOICES = [
        ('adl', 'Activities of Daily Living'),
        ('iadl', 'Instrumental ADL'),
        ('vital_sign', 'Vital Sign'),
    ]

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='details')
    metric = models.ForeignKey(AssessmentMetric, on_delete=models.PROTECT, null=True, blank=True)
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    item_key = models.CharField(max_length=30, null=True, blank=True)
    item_name = models.CharField(max_length=50, null=True, blank=True)
    
    score = models.IntegerField(null=True, blank=True)
    max_score = models.IntegerField(null=True, blank=True)
    value = models.CharField(max_length=50, null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'assessment_details'
        verbose_name = 'Assessment Detail'
        verbose_name_plural = 'Assessment Details'

    def __str__(self):
        display = self.score if self.score is not None else self.value
        return f"{self.assessment.id} - {self.item_name or self.metric}: {display}"


class AssessmentDiagnosis(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_name = models.CharField(max_length=255)
    diagnosis_code = models.CharField(max_length=20, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'assessment_diagnoses'
        ordering = ['-is_primary', 'diagnosis_name']
        verbose_name = 'Assessment Diagnosis'
        verbose_name_plural = 'Assessment Diagnoses'

    def __str__(self):
        code = f" ({self.diagnosis_code})" if self.diagnosis_code else ""
        return f"{self.diagnosis_name}{code}"


# ==========================================
# 4. LOC CLASSIFICATION (WORKFLOW)
# ==========================================
class LOCClassification(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'

    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='loc_classification')
    calculated_score = models.IntegerField()
    suggested_loc = models.CharField(max_length=50)
    final_loc = models.CharField(max_length=50, null=True, blank=True)
    is_overridden = models.BooleanField(default=False)
    override_reason = models.TextField(null=True, blank=True)
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        db_table = 'loc_classifications'

    def __str__(self):
        return f"LOC for {self.assessment.resident} - {self.status}"


class LOCClassificationHistory(models.Model):
    loc_classification = models.ForeignKey(LOCClassification, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_at = models.DateTimeField(auto_now_add=True)
    details = models.TextField()

    class Meta:
        db_table = 'loc_classification_history'

    def __str__(self):
        return f"{self.action} on {self.action_at}"


# ==========================================
# 5. VITAL SIGNS
# ==========================================
class VitalSign(models.Model):
    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, db_column='recorded_by')
    blood_pressure_systolic = models.SmallIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.SmallIntegerField(null=True, blank=True)
    heart_rate_bpm = models.SmallIntegerField(null=True, blank=True)
    respiratory_rate = models.SmallIntegerField(null=True, blank=True)
    temperature_fahrenheit = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    spo2_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    pain_scale = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.CharField(max_length=500, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vital_signs'


# ==========================================
# 6. CARE PLAN & TASKS
# ==========================================
class CarePlan(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        ACTIVE = 'active', 'Active'
        REVIEW_DUE = 'review_due', 'Review Due'
        NEEDS_UPDATE = 'needs_update', 'Needs Update'
        RESOLVED = 'resolved', 'Resolved'
        DISCONTINUED = 'discontinued', 'Discontinued'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    significant_change_flag = models.BooleanField(default=False)
    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE, related_name='medical_care_plans')
    is_deleted = models.BooleanField(default=False)
    last_review_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_care_plans')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'care_plans'

    def __str__(self):
        return f"Care Plan #{self.id}"


class CareGoal(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        ACHIEVED = 'ACHIEVED', 'Achieved'
        NOT_MET = 'NOT_MET', 'Not Met'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    care_plan = models.ForeignKey(CarePlan, on_delete=models.CASCADE, related_name='goals', db_column="care_plan_id")
    goal = models.TextField(null=True, blank=True)
    measure = models.TextField(null=True, blank=True)
    task = models.TextField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'care_goals'

    def __str__(self):
        return f"Care Goal #{self.id}"


class CareIntervention(models.Model):
    assigned_role = models.CharField(max_length=50)
    care_plan = models.ForeignKey(CarePlan, on_delete=models.CASCADE)

    class Meta:
        db_table = 'care_interventions'


class CareTask(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        MISSED = 'MISSED', 'Missed'

    task_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    is_abnormal_flagged = models.BooleanField(default=False)
    care_intervention = models.ForeignKey(CareIntervention, on_delete=models.CASCADE)
    assigned_cna = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_time = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'care_tasks'


# ==========================================
# 7. MEDICATION ORDERS & LOGS
# ==========================================
class MedicationOrder(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        DISCONTINUED = 'DISCONTINUED', 'Discontinued'
        ON_HOLD = 'ON_HOLD', 'On Hold'

    drug_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    route = models.CharField(max_length=30)
    frequency = models.CharField(max_length=100)
    is_controlled_substance = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices)
    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE)
    prescribed_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, db_column='prescribed_by')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medication_orders'


class MedicationSchedule(models.Model):
    order = models.ForeignKey(MedicationOrder, on_delete=models.CASCADE)
    scheduled_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'medication_schedules'


class MedicationLog(models.Model):
    class Status(models.TextChoices):
        ADMINISTERED = 'ADMINISTERED', 'Administered'
        REFUSED = 'REFUSED', 'Refused'
        HELD = 'HELD', 'Held'
        NOT_AVAILABLE = 'NOT_AVAILABLE', 'Not Available'

    status = models.CharField(max_length=20, choices=Status.choices)
    is_clinically_justified = models.BooleanField(default=False)
    override_reason = models.CharField(max_length=500, null=True, blank=True)
    order = models.ForeignKey(MedicationOrder, on_delete=models.CASCADE)
    administered_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='administered_meds', db_column='administered_by')
    witnessed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='witnessed_meds', db_column='witnessed_by')
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medication_logs'


# ==========================================
# 8. INCIDENTS & SLA
# ==========================================
class IncidentSeverity(models.Model):
    level_name = models.CharField(max_length=50)
    chart_lock_trigger = models.BooleanField(default=False)

    class Meta:
        db_table = 'incident_severities'


class SlaConfig(models.Model):
    sla_window_hrs = models.IntegerField()
    severity = models.ForeignKey(IncidentSeverity, on_delete=models.CASCADE)

    class Meta:
        db_table = 'sla_configs'


class Incident(models.Model):
    class IncidentType(models.TextChoices):
        FALL = 'FALL', 'Fall'
        MEDICATION_ERROR = 'MEDICATION_ERROR', 'Medication Error'
        ALTERCATION = 'ALTERCATION', 'Altercation'
        SKIN_TEAR = 'SKIN_TEAR', 'Skin Tear'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        UNDER_INVESTIGATION = 'UNDER_INVESTIGATION', 'Under Investigation'
        CLOSED = 'CLOSED', 'Closed'

    incident_type = models.CharField(max_length=50, choices=IncidentType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    description = models.TextField(null=True, blank=True)
    sla_deadline = models.DateTimeField()
    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE)
    severity = models.ForeignKey(IncidentSeverity, on_delete=models.PROTECT)
    reported_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, db_column='reported_by')
    reported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'incidents'


class IncidentTimeline(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    action = models.TextField(null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    actor = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'incident_timelines'


class ChartLockEvent(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    unlocked_by = models.ForeignKey('accounts.User', on_delete=models.PROTECT, db_column='unlocked_by', null=True, blank=True)
    locked_by_system = models.BooleanField(default=True)
    unlock_reason = models.TextField(null=True, blank=True)
    event_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chart_lock_events'


# ==========================================
# 9. HOLIDAY MODEL (SQL Server SSMS)
# ==========================================
class Holiday(models.Model):
    holiday_id = models.AutoField(primary_key=True, db_column='HolidayID')
    holiday_date = models.DateField(unique=True, db_column='HolidayDate')
    holiday_name = models.CharField(max_length=250, db_column='HolidayName')
    is_national_holiday = models.BooleanField(default=True, db_column='IsNationalHoliday')
    description = models.CharField(max_length=500, blank=True, null=True, db_column='Description')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')

    class Meta:
        db_table = 'Holidays'

    def __str__(self):
        return f"{self.holiday_name} ({self.holiday_date})"