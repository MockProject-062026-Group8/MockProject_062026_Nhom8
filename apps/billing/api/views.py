import calendar
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.billing.models import LOCRate
from apps.medical.models import Holiday, LOCClassification
from apps.residents.models import Resident

class CostBillingAPIView(APIView):
    """
    API Endpoint for SC035 - Cost / Billing Panel
    """
    def get(self, request, *args, **kwargs):
        # 1. Seed LOCRate if empty
        if not LOCRate.objects.exists():
            LOCRate.objects.create(loc_level="LOC Tier 1", daily_rate=150.00)
            LOCRate.objects.create(loc_level="LOC Tier 2", daily_rate=200.00)
            LOCRate.objects.create(loc_level="LOC Tier 3", daily_rate=250.00)
            LOCRate.objects.create(loc_level="LOC Tier 4", daily_rate=300.00)
        
        # 2. Get Resident
        resident_id = request.GET.get('resident_id', 1)
        resident = get_object_or_404(Resident, pk=resident_id)
        
        # 3. Get LOC Rate
        latest_loc = LOCClassification.objects.filter(assessment__resident=resident, status='CONFIRMED').order_by('-confirmed_at').first()
        
        if latest_loc:
            loc_tier_name = latest_loc.final_loc or latest_loc.suggested_loc or "LOC Tier 1"
        else:
            loc_tier_name = "LOC Tier 1"
            
        if "Level" in loc_tier_name:
            loc_tier_name = loc_tier_name.replace("Level", "LOC Tier")
            
        loc_rate_obj = LOCRate.objects.filter(loc_level=loc_tier_name).first()
        loc_daily_rate = float(loc_rate_obj.daily_rate) if loc_rate_obj else 150.00
        
        # 4. Get Room Rate
        room = resident.bed.room if hasattr(resident, 'bed') and resident.bed else None
        room_rate = float(room.base_rate) if room else 140.00
                
        room_type_display = room.room_type.replace('_', '-').title() if room else "N/A"
                
        medication_est = 45.00
        subtotal_per_day = loc_daily_rate + room_rate + medication_est
        
        # CR Holidays Logic
        today = date.today()
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        
        holiday_days = Holiday.objects.filter(
            holiday_date__year=today.year, 
            holiday_date__month=today.month
        ).count()
        
        standard_days = days_in_month - holiday_days
        holiday_surcharge_per_day = 100.00
        total_holiday_surcharge = holiday_days * holiday_surcharge_per_day

        estimated_monthly = (standard_days * subtotal_per_day) + (holiday_days * (subtotal_per_day + holiday_surcharge_per_day))

        # 5. Medicare days
        admission = resident.admission_set.first()
        if admission:
            days_admitted = (today - admission.admission_date).days
        else:
            # Fallback if no admission date
            days_admitted = (today - resident.created_at.date()).days
            
        # Ensure it's not negative
        days_admitted = max(0, days_admitted)

        data = {
            'resident_name': resident.full_name,
            'loc_tier_name': loc_tier_name,
            'room_number': room.room_number if room else "N/A",
            'room_type': room_type_display,
            
            # Breakdown data
            'loc_daily_rate': f"{loc_daily_rate:.2f}",
            'room_rate': f"{room_rate:.2f}",
            'medication_est': f"{medication_est:.2f}",
            'subtotal_per_day': f"{subtotal_per_day:.2f}",
            
            # Holiday data
            'holiday_days': holiday_days,
            'holiday_surcharge_per_day': f"{holiday_surcharge_per_day:.2f}",
            'total_holiday_surcharge': f"{total_holiday_surcharge:.2f}",
            
            # Top cards data
            'estimated_day': f"{subtotal_per_day:.2f}",
            'estimated_month': f"{estimated_monthly:,.2f}",
            
            # Medicare data
            'days_admitted': days_admitted,
        }
        return Response(data)