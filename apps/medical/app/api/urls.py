"""
apps/api/urls.py
SC-022 Initial Assessment - API URL patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'assessments', views.AssessmentViewSet, basename='assessment')

urlpatterns = [
    # Router URLs (CRUD assessments)
    path('', include(router.urls)),

    # Nested: Diagnoses dưới Assessment
    path(
        'assessments/<int:assessment_id>/diagnoses/',
        views.AssessmentDiagnosisListCreateView.as_view(),
        name='assessment-diagnoses-list',
    ),
    path(
        'assessments/<int:assessment_id>/diagnoses/<int:pk>/',
        views.AssessmentDiagnosisDetailView.as_view(),
        name='assessment-diagnosis-detail',
    ),
]