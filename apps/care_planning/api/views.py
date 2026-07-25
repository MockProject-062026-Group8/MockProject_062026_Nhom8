from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.medical.models import CarePlan
from apps.accounts.models import User

class CarePlanAckAPIView(APIView):
    """
    API Endpoint for SC036 - Care Plan Acknowledgment
    """
    def get(self, request, *args, **kwargs):
        plan_id = request.GET.get('plan_id')
        
        if plan_id:
            plan = get_object_or_404(CarePlan, pk=plan_id)
        else:
            plan = CarePlan.objects.filter(status=CarePlan.Status.PENDING_REVIEW).first()
            if not plan:
                plan = CarePlan.objects.first()
                
        goals_data = []
        if plan:
            for goal in plan.goals.all():
                status_badge = 'On Track'
                status_class = 'badge-success-outline'
                if goal.status == 'NOT_MET':
                    status_badge = 'At Risk'
                    status_class = 'badge-warning-outline'
                elif goal.status == 'IN_PROGRESS':
                    status_badge = 'In Progress'
                    status_class = 'badge-primary-outline'
                    
                goals_data.append({
                    'title': goal.goal[:20] + '...' if goal.goal and len(goal.goal) > 20 else (goal.goal or 'Goal'),
                    'description': f"Goal: {goal.goal}",
                    'task': goal.task,
                    'status_badge': status_badge,
                    'status_class': status_class
                })
                
        physician_name = 'Not Assigned'
        physician_license = 'N/A'
        physician_npi = 'N/A'
        
        if plan and hasattr(plan.resident, 'admission_set'):
            admission = plan.resident.admission_set.first()
            if admission and admission.admitting_physician:
                physician_name = f"Dr. {admission.admitting_physician.first_name} {admission.admitting_physician.last_name}, MD"
                physician_license = admission.admitting_physician.license_number or 'N/A'
                physician_npi = admission.admitting_physician.npi or 'N/A'
                
        dietary_name = 'Not Assigned'
        dietary_user = User.objects.filter(role__role_name__icontains='Dietary').first()
        if not dietary_user:
            # Fallback to a Nurse or DON if Dietary role doesn't exist in DB
            dietary_user = User.objects.filter(role__role_name__icontains='DON').first()
            if not dietary_user:
                dietary_user = User.objects.filter(role__role_name__icontains='Nurse').first()
                
        if dietary_user:
            role_suffix = dietary_user.role.role_name.split(' ')[0] if dietary_user.role else 'RD'
            dietary_name = f"{dietary_user.first_name} {dietary_user.last_name}, {role_suffix}"
            
        data = {
            # Patient & Form info
            'patient_name': plan.resident.full_name if plan else 'Unknown',
            'submitted_by': f"{plan.assigned_to.first_name} {plan.assigned_to.last_name}" if plan and getattr(plan, 'assigned_to', None) else 'System User',
            'status': plan.get_status_display() if plan else 'Unknown',
            'submit_date': getattr(plan, 'created_at', timezone.now()).strftime('%Y-%m-%d') if plan else 'Unknown',
            
            # Goals List
            'goals': goals_data or [],
            
            # Role Info
            'physician_name': physician_name,
            'license': physician_license,
            'npi': physician_npi,
            
            # IDT Acknowledgment Info
            'dietary_name': dietary_name,
            'dietary_status': 'Signed',
            'dietary_date': getattr(plan, 'created_at', timezone.now()).strftime('%Y-%m-%d %H:%M') if plan else 'Unknown'
        }
        
        return Response(data)
