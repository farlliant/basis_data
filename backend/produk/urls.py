from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProdukViewSet, TransaksiViewSet, SalesReportView # Added SalesReportView

router = DefaultRouter()
router.register('produk', ProdukViewSet, basename='produk')
router.register('transaksi', TransaksiViewSet, basename='transaksi')

urlpatterns = [
    path('', include(router.urls)),
    path('report/', SalesReportView.as_view(), name='sales-report'), # <-- Added report URL
]