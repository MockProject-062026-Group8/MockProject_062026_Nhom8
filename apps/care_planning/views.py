from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Count, Q
from apps.medical.models import CarePlan

class CarePlanListView(ListView):
    model = CarePlan
    template_name = 'care_planning/care_plan_list.html'
    context_object_name = 'care_plans'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('resident', 'assigned_to')
        
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(resident__first_name__icontains=search) | 
                Q(resident__last_name__icontains=search) | 
                Q(resident__resident_id__icontains=search)
            )

        status_filter = self.request.GET.get('status', 'all')
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter.upper())
            
        review_filter = self.request.GET.get('review', 'all')
        if review_filter == 'due':
            queryset = queryset.filter(status=CarePlan.Status.REVIEW_DUE)

        return queryset.order_by('next_review_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        total_plans = CarePlan.objects.count()
        draft_plans = CarePlan.objects.filter(status=CarePlan.Status.DRAFT).count()
        pending_plans = CarePlan.objects.filter(status=CarePlan.Status.PENDING_REVIEW).count()
        review_due_plans = CarePlan.objects.filter(status=CarePlan.Status.REVIEW_DUE).count()

        context['summary'] = {
            'total': total_plans,
            'draft': draft_plans,
            'pending': pending_plans,
            'review_due': review_due_plans
        }
        
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', 'all')
        context['current_review'] = self.request.GET.get('review', 'all')
        context['active_menu'] = 'care_planning'
        
        return context


from datetime import date, datetime
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from apps.medical.models import CareGoal, Holiday

def care_plan_create_page(request):

    # =====================
    # SUBMIT FORM (POST)
    # =====================
    if request.method == "POST":
        resident_id = request.POST.get("resident_id", 1)
        action = request.POST.get("action", "save_draft")

        status = CarePlan.Status.DRAFT if action == "save_draft" else CarePlan.Status.PENDING_REVIEW

        care_plan = CarePlan.objects.create(
            resident_id=resident_id,
            status=status,
            significant_change_flag=False
        )

        # 2. Tạo Care Goal đi kèm
        goal_text = request.POST.get("goal")
        if goal_text:
            CareGoal.objects.create(
                care_plan=care_plan,
                goal=goal_text,
                measure=request.POST.get("measure", ""),
                task=request.POST.get("task", ""),
                status="IN_PROGRESS"  # Khớp với STATUS_CHOICES trong CareGoal model
            )

        messages.success(request, f"Care Plan created successfully with status: {status}")
        return redirect("care_planning:care_plan_create")

    # =====================
    # DISPLAY PAGE (GET) & HOLIDAY CHECK LOGIC
    # =====================
    review_date_input = request.GET.get("review_date", "2026-09-02")
    try:
        target_date = datetime.strptime(review_date_input, "%Y-%m-%d").date()
    except ValueError:
        target_date = date(2026, 9, 2)

    # Đã map db_column='HolidayDate' chuẩn trong model -> Query trực tiếp cực ngắn gọn
    # Query kiểm tra trùng ngày lễ từ SQL Server
    is_holiday_conflict = Holiday.objects.filter(holiday_date=target_date).exists()

    care_areas = [
        {
            "name": "Mobility",
            "suggested": True,
            "goal": "Resident will ambulate 50 ft with walker x2/day by 2026-07-30.",
            "measure": "Distance log",
            "target": "2026-07-30",
            "task": "Assist ambulation with front-wheel walker, twice daily."
        },
        {
            "name": "Skin Integrity",
            "suggested": True,
            "goal": "Maintain skin integrity.",
            "measure": "Braden score",
            "target": "2026-10-07",
            "task": "Reposition every 2 hours."
        },
        {
            "name": "Nutrition",
            "suggested": False,
            "goal": "Maintain hydration ≥1500 ml/day.",
            "measure": "I/O log",
            "target": "Ongoing",
            "task": "Monitor daily fluid intake."
        }
    ]

    context = {
        "resident_id": 1,
        "resident_name": "Robert Hayes",
        "room": "204B",
        "loc_tier": "LOC Tier 3",
        "loc_rate": 248.00,
        "room_rate": 185.00,
        "estimated_daily": 433.00,
        "estimated_monthly": 13163.00,
        "is_holiday_conflict": is_holiday_conflict,
        "care_areas": care_areas
    }

    return render(
        request,
        "medical/care_plan_create.html",
        context
    )


# ==========================
# SC028 UI Page View (Care Plan Locked Page)
# ==========================

def care_plan_locked_page(request):
    target_date = date(2026, 9, 2)
    
    # Query trực tiếp sạch đẹp
    is_holiday_conflict = Holiday.objects.filter(holiday_date=target_date).exists()

    context = {
        "resident_name": "Elena Ramos",
        "room": "Room 106A",
        "loc_tier": "LOC: Suggested (Tier 1)",
        "is_holiday_conflict": is_holiday_conflict,
    }

    return render(
        request,
        "medical/care_plan_locked.html",
        context
    )


# ==========================
# Care Level API
# ==========================

def care_plan_detail_page(request):
    # Ngày review tiếp theo của kế hoạch
    next_review_due = date(2026, 7, 4)  # Mẫu ngày 04/07/2026 (Federal Holiday)

    # Truy vấn tên ngày lễ từ SQL Server DB
    next_review_due = date(2026, 7, 4)

    holiday_info = Holiday.objects.filter(holiday_date=next_review_due).first()
    
    holiday_notice = None
    if holiday_info:
        # Định dạng chuỗi thông báo: "Scheduled on: July 4 - Federal Holiday"
        formatted_date = next_review_due.strftime("%B %d").replace(" 0", " ")
        holiday_notice = f"Scheduled on: {formatted_date} - {holiday_info.holiday_name}"

    context = {
        "resident_name": "Robert Hayes",
        "room": "Room 204B",
        "loc_tier": "LOC Tier 3",
        "next_review": next_review_due.strftime("%Y-%m-%d"),
        "last_reviewed": "2026-04-08",
        "cycle_days": "90 days",
        "loc_rate": 248.00,
        "room_rate": 185.00,
        "estimated_daily": 433.00,
        "estimated_monthly": 13163.00,
        "holiday_notice": holiday_notice,  # Biến truyền ra giao diện
        "holiday_notice": holiday_notice,
    }

    return render(
        request,
        "medical/care_plan_detail.html",
        context
    )

# ==========================
# SC030 UI Page View (Review Care Plan)
# ==========================

def care_plan_review_page(request, pk=None):
    care_plan = CarePlan.objects.filter(pk=pk).first() if pk else None

    # Dynamic check trùng ngày lễ cho banner warning
    holiday_warning = None
    holiday_check = Holiday.objects.filter(holiday_date=date(2026, 7, 30)).first()
    if holiday_check:
        holiday_warning = f"The plan includes a date that coincides with a public holiday ({holiday_check.holiday_name})."
    else:
        holiday_warning = "The plan includes a date that coincides with a public holiday (July 30th)."

    context = {
        "care_plan": care_plan,
        "resident_name": care_plan.resident.full_name if care_plan and hasattr(care_plan, 'resident') else "Robert Hayes",
        "room": getattr(care_plan, 'room', "Room 204B"),
        "loc_tier": getattr(care_plan, 'loc_tier', "LOC Tier 3"),
        "submitted_by": getattr(care_plan, 'submitted_by', "Anna Lee, RN"),
        "submitted_date": care_plan.created_at.strftime("%Y-%m-%d") if care_plan and hasattr(care_plan, 'created_at') else "2026-07-02",
        "status": getattr(care_plan, 'status', "Pending Review"),
        
        # Author info
        "author_name": "Anna Lee, RN",
        "license_no": "RN-482913 (CA)",
        "prepared_date": "2026-07-02 16:40",
        
        # IDT Acknowledgment
        "physician_name": "Dr. Alan Cho, MD",
        "physician_signed_at": "2026-07-02 14:10",
        "dietary_name": "Grace Liu, RD",
        "dietary_signed_at": "2026-07-02 15:30",

        # Holiday warning
        "holiday_warning": holiday_warning,
    }
    return render(request, "medical/care_plan_review.html", context)


# ==========================
# SC030 / SC031 API: Approve & e-Sign (With Password Check)
# ==========================

@csrf_exempt
@require_POST
def approve_care_plan(request, pk=None):
    try:
        password = request.POST.get("password", "").strip()

        # Xác thực mật khẩu chữ ký điện tử nếu user đã đăng nhập
        if request.user.is_authenticated and password:
            if not request.user.check_password(password):
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid re-authentication password. Please try again."
                }, status=400)

        # Xử lý cập nhật DB
        if pk:
            care_plan = CarePlan.objects.filter(pk=pk).first()
            if care_plan:
                care_plan.status = CarePlan.Status.ACTIVE
                care_plan.approved_at = timezone.now()
                if hasattr(care_plan, 'approved_by'):
                    care_plan.approved_by = request.user if request.user.is_authenticated else None
                care_plan.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Care Plan approved and e-signed successfully!"
                })

        return JsonResponse({
            "status": "success",
            "message": "Care Plan approved and e-signed (Simulated)!"
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Server Error: {str(e)}"}, status=500)


# ==========================
# SC030 API: Reject & Return
# ==========================

@csrf_exempt
@require_POST
def reject_care_plan(request, pk=None):
    try:
        reason = request.POST.get("rejection_reason", "").strip()

        if not reason:
            return JsonResponse(
                {"status": "error", "message": "Rejection reason is required when returning a plan to Draft."},
                status=400
            )

        if pk:
            care_plan = CarePlan.objects.filter(pk=pk).first()
            if care_plan:
                care_plan.status = CarePlan.Status.DRAFT
                care_plan.rejection_reason = reason
                care_plan.save()
                return JsonResponse({"status": "success", "message": "Care Plan rejected and returned to Draft!"})

        return JsonResponse({"status": "success", "message": "Care Plan rejected and returned as Draft (Simulated)!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"Server Error: {str(e)}"}, status=500)


# ==========================
# Care Level API (DRF Views)
# ==========================

def care_plan_ack(request):
    """
    SC036 - Care Plan Acknowledgment
    Dummy data based on Figma mockup
    """
    context = {
        'active_menu': 'pending_ack',
        
        # Patient & Form info
        'patient_name': 'Robert Hayes',
        'submitted_by': 'Anna Lee, RN',
        'status': 'Pending Review',
        'submit_date': '2026-07-02',
        
        # Goals List
        'goals': [
            {
                'title': 'Mobility',
                'description': 'Goal: Ambulate 50 ft with walker x2/day.',
                'task': 'Assist ambulation w/ walker, 2x daily.',
                'status_badge': 'On Track',
                'status_class': 'badge-success-outline'
            },
            {
                'title': 'Skin Integrity',
                'description': 'Goal: Maintain skin integrity (no stage-2 injury).',
                'task': 'Reposition q2h; skin check each shift.',
                'status_badge': 'At Risk',
                'status_class': 'badge-warning-outline'
            },
            {
                'title': 'Nutrition',
                'description': 'Goal: Maintain fluid intake ≥ 1500 mL/day.',
                'task': 'Monitor fluid intake; document I/O.',
                'status_badge': 'On Track',
                'status_class': 'badge-success-outline'
            }
        ],
        
        # Role Info
        'physician_name': 'Dr. Alan Cho, MD',
        'license': 'CA-MD-88231',
        'npi': '1720493857',
        
        # IDT Acknowledgment Info
        'dietary_name': 'Grace Liu, RD',
        'dietary_status': 'Signed',
        'dietary_date': '2026-07-02 15:30'
    }
    
    return render(request, 'medical/care_plan_ack.html', context)



