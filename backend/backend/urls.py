from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# --- Import untuk dokumentasi ---
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="API Laris Amanah",
      default_version='v1',
      description="Dokumentasi API.",
      contact=openapi.Contact(email="larisamanah@basisdata.com"),
      license=openapi.License(name="bapakkuprogrammer"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('produk.urls')),
    path('user/', include('user.urls')),
    path('', lambda request: HttpResponse("Welcome to the API!")),
    # URL untuk dokumentasi API
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]