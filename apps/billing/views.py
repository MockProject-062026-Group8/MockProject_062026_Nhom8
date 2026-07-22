from django.shortcuts import render

# Create your views here.
def billing_panel(request):
    """
    SC035 - Cost / Billing Panel
    Dummy data based on Figma mockup + Holiday CR Logic
    """
    # Base daily rates
    loc_daily_rate = 285.00
    room_rate = 140.00
    medication_est = 45.00
    subtotal_per_day = loc_daily_rate + room_rate + medication_est # 470.00

    # CR Holidays Logic
    days_in_month = 30
    holiday_days = 1 # e.g. July 4th
    standard_days = days_in_month - holiday_days # 29

    
    # Holiday Surcharge (assumed $100 per holiday)
    holiday_surcharge_per_day = 100.00
    total_holiday_surcharge = holiday_days * holiday_surcharge_per_day # 100.00

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
