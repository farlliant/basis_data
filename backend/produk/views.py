from rest_framework import viewsets, filters
from .models import Produk, Transaksi
from .serializers import ProdukSerializer, TransaksiSerializer

class ProdukViewSet(viewsets.ModelViewSet):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['kode_barang', 'nama_barang']

class TransaksiViewSet(viewsets.ModelViewSet):
    queryset = Transaksi.objects.all()
    serializer_class = TransaksiSerializer