from django.db import models

class Facility(models.Model):
    facility_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100)
    target_state = models.CharField(max_length=2)
    address = models.ForeignKey('residents.Address', on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'facilities'

class Room(models.Model):
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=50)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    base_rate = models.DecimalField(max_digits=18, decimal_places=2, default=140.00)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'rooms'

class Bed(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        OCCUPIED = 'OCCUPIED', 'Occupied'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'

    bed_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        db_table = 'beds'

class InventoryCategory(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_categories'

class DurableMedicalEquipment(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        IN_SERVICE = 'IN_SERVICE', 'In Service'
        UNDER_MAINTENANCE = 'UNDER_MAINTENANCE', 'Under Maintenance'
        RETIRED = 'RETIRED', 'Retired'

    item_name = models.CharField(max_length=200)
    category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT)
    asset_tag = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.AVAILABLE)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    assigned_to_user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to_resident = models.ForeignKey('residents.Resident', on_delete=models.SET_NULL, null=True, blank=True)
    unit_value = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'durable_medical_equipment'

class ConsumableSupply(models.Model):
    class Status(models.TextChoices):
        OK = 'OK', 'OK'
        LOW_STOCK = 'LOW_STOCK', 'Low Stock'
        OUT_OF_STOCK = 'OUT_OF_STOCK', 'Out of Stock'

    item_name = models.CharField(max_length=200)
    category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE)
    stock_on_hand = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    private_pay_rate = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OK)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consumable_supplies'