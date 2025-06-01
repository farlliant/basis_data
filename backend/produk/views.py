from rest_framework import viewsets, filters, generics
from .models import Produk, Transaksi
from .serializers import ProdukSerializer, TransaksiSerializer

# === VIEWSET UNTUK CRUD + SEARCH PRODUK ===
class ProdukViewSet(viewsets.ModelViewSet):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['kode_barang', 'nama_barang']  # pastikan field ini ada di model Produk

# === JIKA BUTUH VIEW BERBASIS GENERICS UNTUK DETAIL PRODUK ===
class ProdukRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer

# === VIEWSET UNTUK CRUD + SEARCH TRANSAKSI ===
class TransaksiViewSet(viewsets.ModelViewSet):
    queryset = Transaksi.objects.all()
    serializer_class = TransaksiSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['produk__kode_barang', 'produk__nama_barang', 'jumlah']  # lookup ke foreign key

# === JIKA BUTUH VIEW BERBASIS GENERICS UNTUK DETAIL TRANSAKSI ===
class TransaksiRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaksi.objects.all()
    serializer_class = TransaksiSerializer
