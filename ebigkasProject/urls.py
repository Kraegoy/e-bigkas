# urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),    
    path('', include('ebigkasAPP.urls')),
    path('', include('ebigkasAdminAPP.urls')),
    path('', include('ebigkasLearnings.urls')),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


