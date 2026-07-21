import calendar
from datetime import date
from django.shortcuts import render
from apps.billing.models import LOCRate
from apps.medical.models import Holiday

def billing_panel(request):
    """
    SC035 - Cost / Billing Panel
    Connected to DB for Holiday and LOC Rate
    """
    # Base daily rates
    loc_rate_obj = LOCRate.objects.first()
    loc_daily_rate = float(loc_rate_obj.daily_rate) if loc_rate_obj else 285.00
    room_rate = 140.00  # Hardcoded as Room model doesn't have a rate yet
    medication_est = 45.00
    subtotal_per_day = loc_daily_rate + room_rate + medication_est
    
    # CR Holidays Logic
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    # Count holidays in this month
    holiday_days = Holiday.objects.filter(
        holiday_date__year=today.year, 
        holiday_date__month=today.month
    ).count()
    
    standard_days = days_in_month - holiday_days

    # Holiday Surcharge (assumed $100 per holiday)
    holiday_surcharge_per_day = 100.00
    total_holiday_surcharge = holiday_days * holiday_surcharge_per_day

    # Monthly calculation
    estimated_monthly = (standard_days * subtotal_per_day) + (holiday_days * (subtotal_per_day + holiday_surcharge_per_day))

    context = {
        'active_menu': 'care_planning',
        
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
    }
    
    return render(request, 'medical/billing_panel.html', context)
