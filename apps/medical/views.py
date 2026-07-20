from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from apps.residents.models import Resident
from .models import Assessment

@login_required
@permission_required('medical.view_assessment', raise_exception=True)
def assessment_history_view(request, resident_id):
    resident = get_object_or_404(Resident, resident_id=resident_id)
    assessments = Assessment.objects.filter(resident=resident).order_by('-assessment_date', '-version')
    
    context = {
        'resident': resident,
        'assessments': assessments,
    }
    return render(request, 'medical/sc_023_history.html', context)

@login_required
@permission_required('medical.add_assessment', raise_exception=True)
@require_POST
def create_reassessment_api(request, resident_id):
    resident = get_object_or_404(Resident, resident_id=resident_id)
    latest_assessment = Assessment.objects.filter(resident=resident).order_by('-version').first()
    
    new_version = (latest_assessment.version + 1) if latest_assessment else 1
    
    new_assessment = Assessment.objects.create(
        resident=resident,
        version=new_version,
        assessment_type='reassessment',
        author=request.user,
        total_adl_score=latest_assessment.total_adl_score if latest_assessment else 0,
        loc_tier=latest_assessment.loc_tier if latest_assessment else '',
        is_locked=False
    )
    
    # Normally we would redirect to the Initial Assessment form to edit the draft.
    # For now, we redirect back to history.
    return redirect('medical:assessment_history', resident_id=resident.resident_id)
