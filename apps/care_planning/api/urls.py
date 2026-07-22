from django.urls import path
from .views import CarePlanAckAPIView

app_name = 'care_planning_api'

urlpatterns = [
    path('ack/', CarePlanAckAPIView.as_view(), name='api-care-plan-ack'),
]
