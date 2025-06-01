from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import userViewSet, LoginView, logout_view

router = DefaultRouter()
# 'user' handles GET (list, retrieve), POST (create/register), PUT, DELETE for users
router.register('register', userViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='user-login'),
    path('logout/', logout_view, name='user-logout'),
]