from django.urls import path
from .views import ResidentDetailAPIView, ResidentCreateUpdateAPIView
from .list_views import ResidentListAPIView

urlpatterns = [
    path('', ResidentListAPIView.as_view(), name='sc017-resident-list-api'),
    path('<int:pk>/', ResidentDetailAPIView.as_view(), name='resident-detail'),
    path('create/', ResidentCreateUpdateAPIView.as_view(), name='resident-create'),
    path('edit/<int:pk>/', ResidentCreateUpdateAPIView.as_view(), name='resident-edit'),
]
