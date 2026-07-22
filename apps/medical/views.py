import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.residents.models import Resident
from .models import Assessment, AssessmentDetail, AssessmentDiagnosis
from .fomrs import (
    AssessmentForm,
    ADL_ITEMS,
    IADL_ITEMS,
    VITAL_SIGN_ITEMS,
    ADL_SCORE_CHOICES,
    IADL_SCORE_CHOICES,
)


# @login_required
def initial_assessment(request, pk, assessment_id=None):
    """
    SC-022: pk = Resident.id (Django auto id)
    """
    resident = get_object_or_404(Resident, pk=pk)

    assessment = None
    existing_details = {}
    existing_diagnoses = []

    if assessment_id:
        assessment = get_object_or_404(Assessment, id=assessment_id, resident=resident)
        for d in assessment.details.all():
            existing_details[(d.category, d.item_key)] = d
        existing_diagnoses = list(assessment.diagnoses.all())

    if request.method == 'POST':
        form = AssessmentForm(request.POST, instance=assessment)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.resident = resident
            if request.user.is_authenticated:
                obj.assessed_by = request.user
            else:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                obj.assessed_by = User.objects.first()
            if not obj.assessment_date:
                obj.assessment_date = timezone.now()
            obj.save()

            for item_key, item_name in ADL_ITEMS:
                score = int(request.POST.get(f'adl_{item_key}', 0))
                AssessmentDetail.objects.update_or_create(
                    assessment=obj, category='adl', item_key=item_key,
                    defaults={'item_name': item_name, 'score': score, 'max_score': 4},
                )
            obj.details.filter(category='adl').exclude(
                item_key__in=[k for k, _ in ADL_ITEMS]
            ).delete()

            for item_key, item_name in IADL_ITEMS:
                score = int(request.POST.get(f'iadl_{item_key}', 0))
                AssessmentDetail.objects.update_or_create(
                    assessment=obj, category='iadl', item_key=item_key,
                    defaults={'item_name': item_name, 'score': score, 'max_score': 1},
                )
            obj.details.filter(category='iadl').exclude(
                item_key__in=[k for k, _ in IADL_ITEMS]
            ).delete()

            for item_key, item_name, unit in VITAL_SIGN_ITEMS:
                value = request.POST.get(f'vs_{item_key}', '').strip()
                AssessmentDetail.objects.update_or_create(
                    assessment=obj, category='vital_sign', item_key=item_key,
                    defaults={'item_name': item_name, 'value': value, 'unit': unit, 'score': None, 'max_score': None},
                )
            obj.details.filter(category='vital_sign').exclude(
                item_key__in=[k for k, _, _ in VITAL_SIGN_ITEMS]
            ).delete()

            diagnoses_json = request.POST.get('diagnoses_json', '[]')
            try:
                diagnoses_data = json.loads(diagnoses_json)
            except json.JSONDecodeError:
                diagnoses_data = []

            obj.diagnoses.all().delete()
            for diag in diagnoses_data:
                if diag.get('name', '').strip():
                    AssessmentDiagnosis.objects.create(
                        assessment=obj,
                        diagnosis_name=diag['name'].strip(),
                        diagnosis_code=diag.get('code', '').strip() or None,
                        is_primary=diag.get('is_primary', False),
                        notes=diag.get('notes', '').strip(),
                    )

            obj.recalculate_scores()
            messages.success(request, 'Initial Assessment saved successfully.')
            return redirect('medical:initial_assessment', pk=resident.pk, assessment_id=obj.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial_data = {}
        if assessment:
            initial_data = {
                'assessment_type': assessment.assessment_type,
                'assessment_date': assessment.assessment_date.strftime('%Y-%m-%dT%H:%M')
                if assessment.assessment_date
                else timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'cognitive_status': assessment.cognitive_status,
                'allergies': assessment.allergies,
                'clinical_notes': assessment.clinical_notes,
            }
        form = AssessmentForm(initial=initial_data)

    adl_rows = []
    for item_key, item_name in ADL_ITEMS:
        detail = existing_details.get(('adl', item_key))
        adl_rows.append({
            'key': item_key, 'name': item_name,
            'score': detail.score if detail else 0, 'max_score': 4,
            'choices': ADL_SCORE_CHOICES,
        })

    iadl_rows = []
    for item_key, item_name in IADL_ITEMS:
        detail = existing_details.get(('iadl', item_key))
        iadl_rows.append({
            'key': item_key, 'name': item_name,
            'score': detail.score if detail else 0, 'max_score': 1,
            'choices': IADL_SCORE_CHOICES,
        })

    vs_rows = []
    for item_key, item_name, unit in VITAL_SIGN_ITEMS:
        detail = existing_details.get(('vital_sign', item_key))
        vs_rows.append({
            'key': item_key, 'name': item_name,
            'value': detail.value if detail else '', 'unit': unit,
        })

    diagnoses_list = [
        {'id': d.id, 'name': d.diagnosis_name, 'code': d.diagnosis_code or '',
         'is_primary': d.is_primary, 'notes': d.notes}
        for d in existing_diagnoses
    ]

    # Tạo initials từ full_name
    name_parts = resident.full_name.split()
    initials = ''.join(p[0].upper() for p in name_parts[:2]) if name_parts else '?'

    context = {
        'resident': resident,
        'initials': initials,
        'form': form,
        'assessment': assessment,
        'adl_rows': adl_rows,
        'iadl_rows': iadl_rows,
        'vs_rows': vs_rows,
        'diagnoses_list_json': json.dumps(diagnoses_list),
        'total_adl': assessment.total_adl_score if assessment else 0,
        'max_adl': assessment.max_adl_score if assessment else 32,
        'total_iadl': assessment.total_iadl_score if assessment else 0,
        'max_iadl': assessment.max_iadl_score if assessment else 8,
        'active_menu': 'medical',
    }
    return render(request, 'medical/sc_022.html', context)


# @login_required
# @require_POST
def api_add_diagnosis(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Diagnosis name is required'}, status=400)
    if data.get('is_primary', False):
        assessment.diagnoses.all().update(is_primary=False)
    diag = AssessmentDiagnosis.objects.create(
        assessment=assessment,
        diagnosis_name=name,
        diagnosis_code=data.get('code', '').strip() or None,
        is_primary=data.get('is_primary', False),
        notes=data.get('notes', '').strip(),
    )
    return JsonResponse({
        'id': diag.id, 'name': diag.diagnosis_name,
        'code': diag.diagnosis_code or '', 'is_primary': diag.is_primary,
        'notes': diag.notes,
    })


# @login_required
# @require_POST
def api_remove_diagnosis(request, assessment_id, diagnosis_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    diag = get_object_or_404(AssessmentDiagnosis, id=diagnosis_id, assessment=assessment)
    diag.delete()
    return JsonResponse({'success': True})


# Create your views here.
def reassessments(request):
    """
    SC034 - Reassessments connected to DB
    """
    from datetime import timedelta
    now = timezone.now().date()
    
    from apps.residents.models import Resident
    from apps.medical.models import Assessment
    
    residents = Resident.objects.all()
    
    reassessments_list = []
    total_reassessments = 0
    total_overdue = 0
    
    for resident in residents:
        latest_assessment = Assessment.objects.filter(resident=resident).order_by('-assessment_date').first()
        
        if latest_assessment:
            last_date = latest_assessment.assessment_date
        else:
            # If no assessment, fallback to admission date or resident creation date
            admission = resident.admission_set.first()
            last_date = admission.admission_date if admission else resident.created_at
            
        if hasattr(last_date, 'date'):
            last_date = last_date.date()
            
        days_since = (now - last_date).days
        next_due = last_date + timedelta(days=90)
        
        # We classify as Overdue if > 90 days, Upcoming if 75-90 days
        is_overdue = days_since > 90
        is_upcoming = 75 <= days_since <= 90
        
        if is_overdue or is_upcoming:
            total_reassessments += 1
            if is_overdue:
                total_overdue += 1
                
            trigger = '90-day cycle'
            action = 'Start'
            
            room_name = resident.room_number
            
            due_date_str = next_due.strftime('%Y-%m-%d')
            overdue_str = f'{days_since - 90} days' if is_overdue else '-'
            
            reassessments_list.append({
                'id': resident.id,
                'resident': resident.full_name,
                'room': room_name,
                'trigger': trigger,
                'due_date': due_date_str,
                'overdue': overdue_str,
                'status': 'Overdue' if is_overdue else 'Upcoming',
                'action': action,
                'is_escalated': is_overdue and (days_since - 90) > 3,
            })

    reassessments_list.sort(key=lambda x: (x['status'] == 'Upcoming', not x['is_escalated']))
    
    context = {
        'active_menu': 'care_planning',
        'reassessments_list': reassessments_list,
        'total_reassessments': total_reassessments,
        'total_overdue': total_overdue,
    }
    return render(request, 'medical/reassessments.html', context)

@require_POST
def start_reassessment(request):
    try:
        data = json.loads(request.body)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Reassessment started successfully'
        })
    except CarePlan.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Care Plan not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from .models import Assessment, LOCClassification, LOCClassificationHistory
from apps.billing.models import LOCRate
from django.utils import timezone

def loc_classification_detail(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    
    loc, created = LOCClassification.objects.get_or_create(
        assessment=assessment,
        defaults={
            'calculated_score': assessment.total_adl_score,
            'suggested_loc': _calculate_loc(assessment.total_adl_score)
        }
    )
    
    loc_rate = None
    display_loc = loc.final_loc if loc.final_loc else loc.suggested_loc
    try:
        loc_rate = LOCRate.objects.get(loc_level=display_loc)
    except LOCRate.DoesNotExist:
        pass
        
    history = loc.history.all().order_by('-action_at')
    
    context = {
        'assessment': assessment,
        'loc': loc,
        'loc_rate': loc_rate,
        'history': history,
    }
    return render(request, 'medical/loc_classification.html', context)

def _calculate_loc(score):
    if score <= 8:
        return 'Level 1'
    elif score <= 16:
        return 'Level 2'
    elif score <= 24:
        return 'Level 3'
    else:
        return 'Level 4'

def loc_classification_confirm(request, assessment_id):
    if request.method == 'POST':
        assessment = get_object_or_404(Assessment, id=assessment_id)
        loc = get_object_or_404(LOCClassification, assessment=assessment)
        
        if loc.status == 'Confirmed':
            return HttpResponseBadRequest("Already confirmed")
            
        loc.final_loc = loc.suggested_loc
        loc.status = 'Confirmed'
        loc.confirmed_by = request.user if request.user.is_authenticated else None
        loc.confirmed_at = timezone.now()
        loc.save()
        
        LOCClassificationHistory.objects.create(
            loc_classification=loc,
            action="LOC Confirmed",
            action_by=request.user if request.user.is_authenticated else None,
            details=f"Confirmed {loc.final_loc}"
        )
        return redirect('medical:loc_detail', assessment_id=assessment.id)
    return HttpResponseBadRequest("Invalid request")

def loc_classification_override(request, assessment_id):
    if request.method == 'POST':
        assessment = get_object_or_404(Assessment, id=assessment_id)
        loc = get_object_or_404(LOCClassification, assessment=assessment)
        
        if loc.status == 'Confirmed':
            return HttpResponseBadRequest("Already confirmed")
            
        override_loc = request.POST.get('override_loc')
        override_reason = request.POST.get('override_reason')
        
        if not override_loc or not override_reason:
            return HttpResponseBadRequest("Missing fields")
            
        loc.final_loc = override_loc
        loc.status = 'Confirmed'
        loc.is_overridden = True
        loc.override_reason = override_reason
        loc.confirmed_by = request.user if request.user.is_authenticated else None
        loc.confirmed_at = timezone.now()
        loc.save()
        
        LOCClassificationHistory.objects.create(
            loc_classification=loc,
            action="LOC Overridden",
            action_by=request.user if request.user.is_authenticated else None,
            details=f"Overridden to {loc.final_loc}. Reason: {override_reason}"
        )
        return redirect('medical:loc_detail', assessment_id=assessment.id)
    return HttpResponseBadRequest("Invalid request")

from django.shortcuts import render, get_object_or_404

from apps.residents.models import Resident

def loc_history_view(request, resident_id):
    resident = get_object_or_404(Resident, id=resident_id)
    return render(request, "medical/loc_history.html", {"resident": resident})

from django.views import View
from .models import PreAdmissionScreening
from apps.residents.models import Resident

class ScreeningCreate(View):
    def get(self, request, resident_id):
        resident = get_object_or_404(Resident, pk=resident_id)
        return render(request, 'medical/screening_form.html', {'resident': resident})

class AdmissionFormView(View):
    def get(self, request, resident_id):
        from apps.rooms.models import Bed
        resident = get_object_or_404(Resident, pk=resident_id)
        beds = Bed.objects.filter(status='AVAILABLE')
        return render(request, 'medical/admission_form.html', {'resident': resident, 'beds': beds})



from datetime import date, datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics

from apps.medical.models import (
    CareLevel,
    CarePlan,
    CareGoal,
    Holiday
)

from apps.medical.api.serializers import (
    CareLevelSerializer,
    CarePlanSerializer,
    CareGoalSerializer
)


# ==========================
# SC027 UI Page View (Create Care Plan + Holiday Check)
# ==========================

class CareLevelListCreateView(generics.ListCreateAPIView):
    queryset = CareLevel.objects.filter(is_deleted=False)
    serializer_class = CareLevelSerializer


class CareLevelDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CareLevel.objects.all()
    serializer_class = CareLevelSerializer


# ==========================
# Care Plan API (DRF Views)
# ==========================

class CarePlanListCreateView(generics.ListCreateAPIView):
    queryset = CarePlan.objects.filter(is_deleted=False)
    serializer_class = CarePlanSerializer


class CarePlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CarePlan.objects.all()
    serializer_class = CarePlanSerializer


# ==========================
# Care Goal API (DRF Views)
# ==========================

class CareGoalListCreateView(generics.ListCreateAPIView):
    queryset = CareGoal.objects.all()
    serializer_class = CareGoalSerializer


class CareGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CareGoal.objects.all()
    serializer_class = CareGoalSerializer



# ==========================
# SC029 UI Page View (Care Plan Detail with Holiday Notice)
# ==========================

class CareLevelListCreateView(generics.ListCreateAPIView):
    queryset = CareLevel.objects.filter(is_deleted=False)
    serializer_class = CareLevelSerializer


class CareLevelDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CareLevel.objects.all()
    serializer_class = CareLevelSerializer


# ==========================
# Care Plan API (DRF Views)
# ==========================

class CarePlanListCreateView(generics.ListCreateAPIView):
    queryset = CarePlan.objects.filter(is_deleted=False)
    serializer_class = CarePlanSerializer


class CarePlanDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CarePlan.objects.all()
    serializer_class = CarePlanSerializer


# ==========================
# Care Goal API (DRF Views)
# ==========================

class CareGoalListCreateView(generics.ListCreateAPIView):
    queryset = CareGoal.objects.all()
    serializer_class = CareGoalSerializer

    

class CareGoalDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CareGoal.objects.all()
    serializer_class = CareGoalSerializer

def bedside_vitals(request):
    """
    SC033 - Bedside Vitals (Ghi nhận Sinh hiệu tại giường)
    """
    resident_id = request.GET.get('resident_id', 1)
    from django.shortcuts import get_object_or_404
    resident = get_object_or_404(Resident, pk=resident_id)
    
    task_id = request.GET.get('task_id')
    task = CareTask.objects.filter(pk=task_id).first() if task_id else None
    now = timezone.now()
    
    context = {
        'active_menu': 'care_planning',
        'resident_name': resident.full_name,
        'room_number': resident.room_number,
        'task_name': task.task_type if task else 'Vitals check',
        'due_time': f"due {task.scheduled_time.strftime('%H:%M')}" if task and task.scheduled_time else f"due {now.strftime('%H:%M')}",
        'recorder_name': request.user.get_full_name() if request.user.is_authenticated else 'System',
        'recorder_time': now.strftime('%Y-%m-%d %H:%M'),
        'resident_id': resident.id
    }
    return render(request, 'medical/bedside_vitals.html', context)

from django.utils import timezone
from apps.residents.models import Resident
from apps.medical.models import CareTask

def daily_tasks(request):
    residents = Resident.objects.prefetch_related(
        'medical_care_plans', 
        'medical_care_plans__careintervention_set__caretask_set',
        'bed__room'
    )
    
    tasks_data = []
    completed_tasks = 0
    total_tasks = 0
    now = timezone.now()
    
    for resident in residents:
        active_plan = resident.medical_care_plans.filter(status=CarePlan.Status.ACTIVE).first()
        draft_plan = resident.medical_care_plans.filter(status=CarePlan.Status.DRAFT).first()
        
        status_text = 'Active' if active_plan else ('Draft' if draft_plan else 'No Plan')
        
        resident_tasks = []
        if active_plan:
            # 1. Fetch today's tasks
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            from apps.medical.models import CareIntervention
            interventions = list(active_plan.careintervention_set.all())
            if not interventions:
                intervention = CareIntervention.objects.create(assigned_role='CNA', care_plan=active_plan)
                interventions.append(intervention)
                
            tasks = CareTask.objects.filter(care_intervention__in=interventions, scheduled_time__range=(today_start, today_end))
            
            if not tasks.exists():
                goals = active_plan.goals.all()
                if not goals:
                    CareTask.objects.create(
                        task_type="Daily Check", 
                        care_intervention=interventions[0], 
                        scheduled_time=now.replace(hour=10, minute=0, second=0)
                    )
                else:
                    for idx, goal in enumerate(goals):
                        hour = 8 + (idx * 2) % 10
                        task_name = goal.task or goal.goal or "Care Task"
                        if len(task_name) > 50:
                            task_name = task_name[:47] + '...'
                        CareTask.objects.create(
                            task_type=task_name,
                            care_intervention=interventions[0],
                            scheduled_time=now.replace(hour=hour, minute=0, second=0)
                        )
                tasks = CareTask.objects.filter(care_intervention__in=interventions, scheduled_time__range=(today_start, today_end))

            for task in tasks:
                overdue = task.status == 'PENDING' and task.scheduled_time < now
                
                state = 'Pending'
                if task.status == 'COMPLETED':
                    state = 'Done'
                elif task.status == 'MISSED':
                    state = 'Refused'
                    
                resident_tasks.append({
                    'id': task.id,
                    'name': task.task_type,
                    'due': task.scheduled_time.strftime('%H:%M') if task.scheduled_time else '',
                    'overdue': overdue,
                    'state': state
                })
                total_tasks += 1
                if state == 'Done':
                    completed_tasks += 1
                        
        if resident_tasks or active_plan or draft_plan:
            room_name = resident.room_number
            tasks_data.append({
                'resident_name': resident.full_name,
                'room': room_name,
                'status': status_text,
                'has_active_plan': bool(active_plan),
                'tasks': sorted(resident_tasks, key=lambda x: x['due'])
            })
            
    context = {
        'active_menu': 'care_planning',
        'residents_tasks': tasks_data,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
    }
    return render(request, 'medical/daily_tasks.html', context)

@require_POST
def update_task_status(request):
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_state = data.get('state')
        
        task = CareTask.objects.get(id=task_id)
        if new_state == 'Done':
            task.status = 'COMPLETED'
            task.completed_at = timezone.now()
        elif new_state == 'Refused':
            task.status = 'MISSED'
        else:
            task.status = 'PENDING'
            
        task.save()
        
        return JsonResponse({
            'status': 'success', 
            'task_id': task_id, 
            'new_state': new_state,
            'message': f'Task {task_id} updated to {new_state} successfully.'
        })
    except CareTask.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_POST
def save_bedside_vitals(request):
    try:
        data = json.loads(request.body)
        
        from apps.accounts.models import User
        recorded_by = request.user if request.user.is_authenticated else None
        
        valid_user = None
        if recorded_by and hasattr(recorded_by, 'id'):
            valid_user = User.objects.filter(id=recorded_by.id).first()
            
        if not valid_user:
            valid_user = User.objects.first()
            
        recorded_by_id = valid_user.id if valid_user else None
            
        resident_id = data.get('resident_id', 1)
        
        bp_sys = data.get('bp_sys') or None
        bp_dia = data.get('bp_dia') or None
        hr = data.get('hr') or None
        resp = data.get('resp') or None
        temp = data.get('temp') or None
        spo2 = data.get('spo2') or None
        pain = data.get('pain') or None
        
        bp_sys_val = float(bp_sys) if bp_sys else None
        hr_val = float(hr) if hr else None
        spo2_val = float(spo2) if spo2 else None
        
        is_abnormal = False
        if bp_sys_val and (bp_sys_val > 140 or bp_sys_val < 90): is_abnormal = True
        if hr_val and (hr_val > 100 or hr_val < 60): is_abnormal = True
        if spo2_val and (spo2_val < 92): is_abnormal = True
        
        from apps.medical.models import VitalSign
            
        VitalSign.objects.create(
            resident_id=resident_id,
            recorded_by_id=recorded_by_id,
            blood_pressure_systolic=bp_sys,
            blood_pressure_diastolic=bp_dia,
            heart_rate_bpm=hr,
            respiratory_rate=resp,
            temperature_fahrenheit=temp,
            spo2_percentage=spo2,
            pain_scale=pain,
            notes=data.get('notes', '')
        )
        
        message = 'Vitals saved successfully'
        if is_abnormal:
            message += ' - WARNING: Abnormal vitals detected!'
            
        return JsonResponse({
            'status': 'success',
            'message': message,
            'is_abnormal': is_abnormal
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


