from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PenggunaViewSet, LoginView, logout_view

router = DefaultRouter()
# 'pengguna' handles GET (list, retrieve), POST (create/register), PUT, DELETE for users
router.register('pengguna', PenggunaViewSet, basename='pengguna')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', logout_view, name='user-logout'),
]