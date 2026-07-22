from django.urls import path, include
from . import views
from apps.medical.views import (
    CareLevelListCreateView,
    CareLevelDetailView,
    CarePlanListCreateView,
    CarePlanDetailView,
    CareGoalListCreateView,
    CareGoalDetailView,
)



app_name = "medical"

urlpatterns = [
    # SC032
    path('daily-tasks/', views.daily_tasks, name='daily_tasks'),
    path('api/update-task/', views.update_task_status, name='update_task_status'),

    # SC033
    path('bedside-vitals/', views.bedside_vitals, name='bedside_vitals'),
    path('api/save-vitals/', views.save_bedside_vitals, name='save_bedside_vitals'),

    # SC034
    path('reassessments/', views.reassessments, name='reassessments'),
    path('api/start-reassessment/', views.start_reassessment, name='start_reassessment'),
    

    # SC027 LOC Classification
    path(
        "assessments/<int:assessment_id>/loc/",
        views.loc_classification_detail,
        name="loc_detail",
    ),
    path(
        "assessments/<int:assessment_id>/loc/confirm/",
        views.loc_classification_confirm,
        name="loc_confirm",
    ),
    path(
        "assessments/<int:assessment_id>/loc/override/",
        views.loc_classification_override,
        name="loc_override",
    ),
    path(
        "residents/<int:resident_id>/loc-history/",
        views.loc_history_view,
        name="loc-history",
    ),

    path(
        "screenings/create/<int:resident_id>/",
        views.ScreeningCreate.as_view(),
        name="screening-create",
    ),
    path(
        "admission-form/<int:resident_id>/",
        views.AdmissionFormView.as_view(),
        name="admission-form",
    ),



    # ==========================
    # API endpoints
    # ==========================
    path("api/", include("apps.medical.api.urls")),

    # Care Level API
    path(
        "api/care-levels/",
        CareLevelListCreateView.as_view(),
        name="carelevel-list",
    ),
    path(
        "api/care-levels/<int:pk>/",
        CareLevelDetailView.as_view(),
        name="carelevel-detail",
    ),

    # Care Plan API
    path(
        "api/care-plans/",
        CarePlanListCreateView.as_view(),
        name="careplan-list",
    ),
    path(
        "api/care-plans/<int:pk>/",
        CarePlanDetailView.as_view(),
        name="careplan-detail",
    ),

    # Care Goal API
    path(
        "api/care-goals/",
        CareGoalListCreateView.as_view(),
        name="caregoal-list",
    ),
    path(
        "api/care-goals/<int:pk>/",
        CareGoalDetailView.as_view(),
        name="caregoal-detail",
    ),

    path(
        'initial-assessment/<int:pk>/',
        views.initial_assessment,
        name='initial_assessment',
    ),
    path(
        'initial-assessment/<int:pk>/<int:assessment_id>/',
        views.initial_assessment,
        name='initial_assessment',
    ),
    path(
        'api/assessment/<int:assessment_id>/diagnosis/add/',
        views.api_add_diagnosis,
        name='api_add_diagnosis',
    ),
    path(
        'api/assessment/<int:assessment_id>/diagnosis/<int:diagnosis_id>/remove/',
        views.api_remove_diagnosis,
        name='api_remove_diagnosis',
    ),
]