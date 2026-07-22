from django.db import models

class Address(models.Model):
    class AddressType(models.TextChoices):
        HOME = 'HOME', 'Home'
        MAILING = 'MAILING', 'Mailing'
        FACILITY = 'FACILITY', 'Facility'
        BILLING = 'BILLING', 'Billing'

    street_line1 = models.CharField(max_length=200)
    street_line2 = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=10)
    address_type = models.CharField(max_length=20, choices=AddressType.choices, default=AddressType.HOME)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'addresses'

class Resident(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'
        UNDISCLOSED = 'UNDISCLOSED', 'Undisclosed'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACTIVE = 'ACTIVE', 'Active'
        DISCHARGED = 'DISCHARGED', 'Discharged'
        DECEASED = 'DECEASED', 'Deceased'

    # Thêm từ nhánh thành viên: Mức độ chăm sóc (Level of Care)
    class LocTier(models.TextChoices):
        TIER_1 = 'Tier 1', 'Tier 1'
        TIER_2 = 'Tier 2', 'Tier 2'
        TIER_3 = 'Tier 3', 'Tier 3'
        TIER_4 = 'Tier 4', 'Tier 4'

    # --- Định danh và Thông tin cá nhân ---
    resident_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='Resident ID') # Thêm từ thành viên (để null=True tạm thời tránh lỗi migration dữ liệu cũ)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices, null=True, blank=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)
    religion_preference = models.CharField(max_length=100, null=True, blank=True)
    
    # --- Trạng thái & Nghiệp vụ ---
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    loc_tier = models.CharField(max_length=10, choices=LocTier.choices, default=LocTier.TIER_1) # Thêm từ thành viên
    payer_source = models.CharField(max_length=50, null=True, blank=True) # Thêm từ thành viên
    is_chart_locked = models.BooleanField(default=False)
    has_dnr = models.BooleanField(default=False)
    
    # --- Thông tin giới thiệu (Referral) ---
    referral_source = models.CharField(max_length=200, null=True, blank=True)
    referral_facility = models.CharField(max_length=200, null=True, blank=True)
    referred_by = models.CharField(max_length=200, null=True, blank=True)

    # --- Liên kết khóa ngoại ---
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    bed = models.ForeignKey('rooms.Bed', on_delete=models.SET_NULL, null=True, blank=True)
    
    # --- Audit / Soft Delete ---
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def room_number(self):
        if self.bed and hasattr(self.bed, 'room') and self.bed.room:
            return getattr(self.bed.room, 'room_number', 'N/A')
        return 'N/A'

class ResidentSensitiveInfo(models.Model):
    resident = models.OneToOneField(Resident, on_delete=models.CASCADE)
    ssn_encrypted = models.CharField(max_length=512, null=True, blank=True)
    medical_record_number_encrypted = models.CharField(max_length=512, null=True, blank=True)
    primary_insurance_id_encrypted = models.CharField(max_length=512, null=True, blank=True)
    bank_account_encrypted = models.CharField(max_length=512, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'resident_sensitive_info'

class Contact(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    phone_primary = models.CharField(max_length=20)
    phone_secondary = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contacts'

class ResidentContact(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    relationship_type = models.CharField(max_length=50)
    is_guarantor = models.BooleanField(default=False)
    is_emergency_contact = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    financial_responsibility_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resident_contacts'

class Admission(models.Model):
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    discharge_reason = models.CharField(max_length=255, null=True, blank=True)
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    facility = models.ForeignKey('rooms.Facility', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    referral_source = models.CharField(max_length=255, null=True, blank=True)
    
    # Consents Verification
    verification_method = models.CharField(max_length=50, null=True, blank=True, choices=[('esignature', 'e-Signature'), ('upload', 'Upload')])
    consent_signature = models.TextField(null=True, blank=True) # Base64 string of signature
    consent_file = models.FileField(upload_to='consents/', null=True, blank=True)
    
    # Care Team & Orders
    admitting_physician = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='admitted_residents_as_physician')
    admitting_nurse = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='admitted_residents_as_nurse')
    order_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'admissions'