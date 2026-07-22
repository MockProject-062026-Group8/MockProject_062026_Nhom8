from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),


    path('billing/', include('apps.billing.urls')),
    path('medical/', include('apps.medical.urls')),
    path('residents/', include('apps.residents.urls')),
    path('rooms/', include('apps.rooms.urls')),
    path('staff/', include('apps.staff.urls')),

    path('care-planning/', include('apps.care_planning.urls')),

    # path('incidents/', include('apps.incidents.urls')),
    path('api/v1/residents/', include('apps.residents.api.urls')),

    path('api/v1/medical/', include('apps.medical.api.urls')),

    
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

