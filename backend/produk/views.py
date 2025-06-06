# produk/views.py

from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from .models import Produk, Transaksi
from .serializers import ProdukSerializer, TransaksiSerializer
from django.db import transaction
class ProdukViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan produk untuk dilihat atau diedit.
    Mendukung pembuatan satu per satu atau secara massal (bulk).
    """
    queryset = Produk.objects.all().order_by('nama_barang')
    serializer_class = ProdukSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Memeriksa apakah data yang masuk adalah list (untuk bulk create)
        is_many = isinstance(request.data, list)

        if not is_many:
            # Jika bukan list, proses seperti biasa (membuat satu produk)
            return super().create(request, *args, **kwargs)
        else:
            # Jika ini adalah list, gunakan serializer dengan `many=True`
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# ====================================================================

# ViewSet untuk Transaksi (CRUD operations)
class TransaksiViewSet(viewsets.ModelViewSet):
    """
    API endpoint yang memungkinkan transaksi untuk dilihat atau dibuat.
    """
    queryset = Transaksi.objects.all().order_by('-waktu_transaksi')
    serializer_class = TransaksiSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        produk = serializer.validated_data['produk']
        jumlah = serializer.validated_data['jumlah']
        
        # Hitung total harga
        total_harga = produk.harga * jumlah
        
        # Periksa stok
        if produk.stok < jumlah:
            return Response(
                {"error": f"Stok untuk {produk.nama_barang} tidak cukup. Tersedia: {produk.stok}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Update stok produk
        produk.stok -= jumlah
        produk.save()

        # Simpan transaksi
        serializer.save(total_harga=total_harga)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class SalesReportView(generics.ListAPIView):
    """
    View untuk menampilkan laporan semua transaksi penjualan.
    View ini bersifat read-only.
    """
    serializer_class = TransaksiSerializer
    queryset = Transaksi.objects.all().order_by('-waktu_transaksi')
    permission_classes = [permissions.IsAdminUser]