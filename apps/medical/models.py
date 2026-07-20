from django.db import models
from django.contrib.auth.models import User
from apps.residents.models import Resident

class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('initial', 'Initial'),
        ('reassessment', 'Reassessment'),
    ]
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='assessments')
    version = models.PositiveIntegerField(default=1)
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES, default='initial')
    assessment_date = models.DateField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.RESTRICT)
    total_adl_score = models.IntegerField(default=0)
    loc_tier = models.CharField(max_length=20, blank=True)
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-assessment_date', '-version']

    def __str__(self):
        return f"{self.resident.full_name} - {self.get_assessment_type_display()} v{self.version}"
