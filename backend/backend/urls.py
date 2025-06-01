#Include Routes
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('produk.urls')),
    path('user/', include('user.urls')),
    path('', lambda request: HttpResponse("Welcome to the API!")),
]