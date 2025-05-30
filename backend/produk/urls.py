# Add Routes
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProdukViewSet, TransaksiViewSet

router = DefaultRouter()
router.register('produk', ProdukViewSet)
router.register('transaksi', TransaksiViewSet)

urlpatterns = [
    path('', include(router.urls)),
]