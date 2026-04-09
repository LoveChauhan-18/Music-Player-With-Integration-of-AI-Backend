from django.contrib import admin 
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
]


def home(request):
    return HttpResponse("Backend is running 🚀")

urlpatterns = [
    path('', home),
]
