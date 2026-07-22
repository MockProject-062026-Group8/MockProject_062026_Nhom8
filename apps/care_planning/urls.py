from django.urls import path
from .views import CarePlanListView
from .views import care_plan_create_page, care_plan_locked_page, care_plan_detail_page, care_plan_review_page, approve_care_plan, reject_care_plan, care_plan_ack

app_name = 'care_planning'

urlpatterns = [
    path('care-plans/create/', care_plan_create_page, name='care_plan_create'),
    path('care-plans/locked/', care_plan_locked_page, name='care_plan_locked'),
    path('care-plans/detail/', care_plan_detail_page, name='care_plan_detail'),
    path('care-plans/<int:pk>/review/', care_plan_review_page, name='care_plan_review'),
    path('api/care-plans/<int:pk>/approve/', approve_care_plan, name='approve_care_plan'),
    path('api/care-plans/<int:pk>/reject/', reject_care_plan, name='reject_care_plan'),
    path('acknowledgment/', care_plan_ack, name='care_plan_ack'),
    path('care-plans/', CarePlanListView.as_view(), name='care_plan_list'),
]
