"""
apps/api/views.py
SC-022 Initial Assessment - Django REST Framework Views
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from apps.medical.models import Assessment, AssessmentDetail, AssessmentDiagnosis
from .serializers import (
    AssessmentListSerializer,
    AssessmentDetailSerializer as AssessmentFullSerializer,
    AssessmentCreateUpdateSerializer,
    AssessmentDetailSerializer as DetailSerializer,
    AssessmentDiagnosisSerializer,
)


class AssessmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint cho Assessments
    GET    /api/assessments/              - Danh sách assessments
    POST   /api/assessments/              - Tạo assessment mới
    GET    /api/assessments/{id}/         - Chi tiết assessment
    PUT    /api/assessments/{id}/         - Cập nhật assessment
    PATCH  /api/assessments/{id}/         - Cập nhật một phần
    DELETE /api/assessments/{id}/         - Xóa assessment
    GET    /api/assessments/{id}/scores/  - Xem điểm ADL/IADL
    """
    queryset = Assessment.objects.select_related('resident', 'assessed_by').prefetch_related(
        'details', 'diagnoses'
    )
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return AssessmentCreateUpdateSerializer
        return AssessmentFullSerializer

    def get_queryset(self):
        """Filter theo resident_id nếu có query param"""
        queryset = super().get_queryset()
        resident_id = self.request.query_params.get('resident_id')
        if resident_id:
            queryset = queryset.filter(resident_id=resident_id)
        assessment_type = self.request.query_params.get('type')
        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)
        return queryset

    @action(detail=True, methods=['get'])
    def scores(self, request, pk=None):
        """Lấy thông tin điểm số ADL/IADL của assessment"""
        assessment = self.get_object()
        adl_items = assessment.details.filter(category='adl').values('item_key', 'item_name', 'score', 'max_score')
        iadl_items = assessment.details.filter(category='iadl').values('item_key', 'item_name', 'score', 'max_score')
        vital_signs = assessment.details.filter(category='vital_sign').values('item_key', 'item_name', 'value', 'unit')

        return Response({
            'assessment_id': assessment.id,
            'adl': list(adl_items),
            'iadl': list(iadl_items),
            'vital_signs': list(vital_signs),
            'totals': {
                'adl_score': assessment.total_adl_score,
                'adl_max': assessment.max_adl_score,
                'iadl_score': assessment.total_iadl_score,
                'iadl_max': assessment.max_iadl_score,
            },
            'care_level': assessment.care_level,
        })


class AssessmentDiagnosisListCreateView(ListCreateAPIView):
    """
    API endpoint cho Diagnoses của 1 Assessment
    GET  /api/assessments/{assessment_id}/diagnoses/
    POST /api/assessments/{assessment_id}/diagnoses/
    """
    serializer_class = AssessmentDiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        assessment_id = self.kwargs['assessment_id']
        return AssessmentDiagnosis.objects.filter(assessment_id=assessment_id)

    def perform_create(self, serializer):
        assessment_id = self.kwargs['assessment_id']
        assessment = Assessment.objects.get(id=assessment_id)
        serializer.save(assessment=assessment)


class AssessmentDiagnosisDetailView(RetrieveUpdateDestroyAPIView):
    """
    API endpoint cho 1 Diagnosis cụ thể
    GET    /api/assessments/{assessment_id}/diagnoses/{pk}/
    PUT    /api/assessments/{assessment_id}/diagnoses/{pk}/
    DELETE /api/assessments/{assessment_id}/diagnoses/{pk}/
    """
    serializer_class = AssessmentDiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        assessment_id = self.kwargs['assessment_id']
        return AssessmentDiagnosis.objects.filter(assessment_id=assessment_id)