from django.urls import path
from .views import CostBillingAPIView

app_name = 'billing_api'

urlpatterns = [
    path('cost-billing/', CostBillingAPIView.as_view(), name='api-cost-billing'),
]