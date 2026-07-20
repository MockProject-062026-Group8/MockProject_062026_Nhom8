from django.urls import path
from . import views

app_name = 'incidents'

urlpatterns = [
    path('', views.severity_list, name='list'),
]
