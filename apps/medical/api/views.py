import csv
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from apps.residents.models import Resident
from apps.medical.models import ResidentCareLevelHistory
from .serializers import ResidentCareLevelHistorySerializer

from rest_framework import viewsets

from apps.medical.models import CareLevel, CarePlan, CareGoal
from .serializers import (
    CareLevelSerializer,
    CarePlanSerializer,
    CareGoalSerializer,
)

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.medical.models import PreAdmissionScreening
from apps.medical.api.serializers import PreAdmissionScreeningSerializer

from apps.residents.models import Admission
from apps.medical.api.serializers import AdmissionCreateSerializer



from apps.medical.models import LOCClassificationHistory
from apps.medical.api.serializers import ResidentCareLevelHistorySerializer
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import csv

class ResidentCareLevelHistoryListView(generics.ListAPIView):
    serializer_class = ResidentCareLevelHistorySerializer

    def get_queryset(self):
        resident_id = self.kwargs.get('resident_id')
        return LOCClassificationHistory.objects.filter(
            loc_classification__assessment__resident_id=resident_id
        ).order_by('-action_at')

class ResidentCareLevelHistoryExportView(APIView):
    def get(self, request, resident_id):
        resident = get_object_or_404(Resident, id=resident_id)
        queryset = LOCClassificationHistory.objects.filter(
            loc_classification__assessment__resident_id=resident_id
        ).order_by('-action_at')
        
        # Always return CSV for simplicity in this implementation
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="loc_history_{resident_id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Action', 'New Tier', 'Actor', 'Note'])
        
        for history in queryset:
            actor_name = history.action_by.get_full_name() if history.action_by else "System"
            date_str = history.action_at.strftime("%m/%d/%Y %H:%M")
            writer.writerow([
                date_str,
                history.action,
                history.loc_classification.final_loc or "",
                actor_name,
                history.details or ""
            ])
            
        return response



class PreAdmissionScreeningCreateUpdateAPIView(generics.CreateAPIView, generics.UpdateAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = PreAdmissionScreening.objects.all()
    serializer_class = PreAdmissionScreeningSerializer

    def perform_create(self, serializer):
        from apps.accounts.models import User, Role
        from django.contrib.auth.hashers import make_password
        user = None
        if hasattr(self.request.user, 'employee_code'):
            user = self.request.user
            
        if not user:
            user = User.objects.first()
            if not user:
                role, _ = Role.objects.get_or_create(role_name='Doctor', defaults={'description': 'Doctor'})
                user = User.objects.create(
                    employee_code='TEST01',
                    email='test@test.com',
                    password_hash=make_password('temp_password_123!'),
                    first_name='Test',
                    last_name='User',
                    role=role
                )
        serializer.save(screened_by=user)

class PreAdmissionScreeningDetailAPIView(generics.RetrieveAPIView):
    queryset = PreAdmissionScreening.objects.all()
    serializer_class = PreAdmissionScreeningSerializer

class ComplianceCheckAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        Simulate a compliance check (BR-06).
        Checks if the provided clinical needs and acuity level can be supported by the facility.
        """
        acuity_level = request.data.get('acuity_level', '')
        if acuity_level:
            acuity_level = acuity_level.upper()
        clinical_needs = request.data.get('clinical_needs', [])
        
        # Hardcoded capacity simulation
        is_flagged = False
        message = "Facility capability check: all selected needs are supported."
        
        if acuity_level in [PreAdmissionScreening.AcuityLevel.MODERATE, PreAdmissionScreening.AcuityLevel.HIGH]:
            is_flagged = True
            message = f"FLAGGED — Clinical review required before admission. Facility acuity capacity for {acuity_level} tier is at 90% — needs DON sign-off."
            
        return Response({
            'is_flagged': is_flagged,
            'message': message,
            'needs_checked': len(clinical_needs)
        }, status=status.HTTP_200_OK)



class AdmissionCreateAPIView(generics.CreateAPIView):
    authentication_classes = []
    permission_classes = []
    queryset = Admission.objects.all()
    serializer_class = AdmissionCreateSerializer


class CareLevelViewSet(viewsets.ModelViewSet):
    queryset = CareLevel.objects.all()
    serializer_class = CareLevelSerializer


class CarePlanViewSet(viewsets.ModelViewSet):
    queryset = CarePlan.objects.all()
    serializer_class = CarePlanSerializer


class CareGoalViewSet(viewsets.ModelViewSet):
    queryset = CareGoal.objects.all()
    serializer_class = CareGoalSerializer