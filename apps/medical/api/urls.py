from django.urls import path

from . import views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CareLevelViewSet,
    CarePlanViewSet,
    CareGoalViewSet,
)

from .views import (
    PreAdmissionScreeningDetailAPIView, 
    PreAdmissionScreeningCreateUpdateAPIView, 
    ComplianceCheckAPIView,
    AdmissionCreateAPIView
)


urlpatterns = [
    path('residents/<int:resident_id>/loc-history/', views.ResidentCareLevelHistoryListView.as_view(), name='loc-history-list'),
    path('residents/<int:resident_id>/loc-history/export/', views.ResidentCareLevelHistoryExportView.as_view(), name='loc-history-export'),
]



app_name = 'medical_api'

urlpatterns = [
    path('screenings/<int:pk>/', PreAdmissionScreeningDetailAPIView.as_view(), name='screening-detail'),
    path('screenings/create/', PreAdmissionScreeningCreateUpdateAPIView.as_view(), name='screening-create'),
    path('screenings/edit/<int:pk>/', PreAdmissionScreeningCreateUpdateAPIView.as_view(), name='screening-edit'),
    path('screenings/compliance-check/', ComplianceCheckAPIView.as_view(), name='screening-compliance-check'),
    path('admissions/create/', AdmissionCreateAPIView.as_view(), name='admission-create'),
]




router = DefaultRouter()
router.register(r"care-levels", CareLevelViewSet)
router.register(r"care-plans", CarePlanViewSet)
router.register(r"care-goals", CareGoalViewSet)

urlpatterns = [
    path("", include(router.urls)),
]