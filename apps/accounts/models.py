from django.db import models
from django.utils import timezone

class Role(models.Model):
    role_name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roles'

class Permission(models.Model):
    action_code = models.CharField(max_length=100, unique=True)
    is_phi_sensitive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'permissions'

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = 'role_permissions'
        unique_together = (('role', 'permission'),)

class User(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        LOCKED = 'LOCKED', 'Locked'

    employee_code = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password_hash = models.CharField(max_length=300)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=100, null=True, blank=True)
    npi = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    mfa_enabled = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

class UserFacility(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    facility = models.ForeignKey('rooms.Facility', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_facilities'
        unique_together = (('user', 'facility'),)

class AuditLog(models.Model):
    class Action(models.TextChoices):
        INSERT = 'INSERT', 'Insert'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'

    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=Action.choices)
    old_data = models.TextField(null=True, blank=True)
    new_data = models.TextField(null=True, blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    performed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        db_table = 'audit_logs'

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    is_consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otps'

class PhiAccessLog(models.Model):
    class AccessType(models.TextChoices):
        VIEW = 'VIEW', 'View'
        PRINT = 'PRINT', 'Print'
        EXPORT = 'EXPORT', 'Export'
        DOWNLOAD = 'DOWNLOAD', 'Download'

    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100)
    accessed_by = models.ForeignKey(User, on_delete=models.PROTECT)
    access_type = models.CharField(max_length=20, choices=AccessType.choices)
    access_reason = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'phi_access_logs'

class Notification(models.Model):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=50)
    is_read = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'