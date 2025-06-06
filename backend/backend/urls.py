# backend/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# --- Import yang diperlukan untuk dokumentasi ---
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# ----------------------------------------------

# --- Konfigurasi untuk halaman dokumentasi ---
schema_view = get_schema_view(
   openapi.Info(
      title="API Toko Sederhana",
      default_version='v1',
      description="Dokumentasi API untuk proyek Toko Sederhana.",
      contact=openapi.Contact(email="kontak@proyek.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
# --------------------------------------------

urlpatterns = [
    # URL Asli Kamu
    path('admin/', admin.site.urls),
    path('api/', include('produk.urls')),
    path('user/', include('user.urls')),
    path('', lambda request: HttpResponse("Welcome to the API!")),

    # === URL UNTUK DOKUMENTASI API ===
    # Ini akan membuat halaman Swagger UI yang interaktif
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    # (Opsional) Ini membuat halaman dokumentasi alternatif (ReDoc)
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]