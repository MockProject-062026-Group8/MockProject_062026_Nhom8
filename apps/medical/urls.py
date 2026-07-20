from django.urls import path
from . import views

app_name = 'medical'
urlpatterns = [
    path('residents/<str:resident_id>/assessments/', views.assessment_history_view, name='assessment_history'),
    path('residents/<str:resident_id>/assessments/new/', views.create_reassessment_api, name='create_reassessment'),
]