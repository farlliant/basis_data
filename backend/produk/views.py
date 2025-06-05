from rest_framework import viewsets, filters, generics, status
from rest_framework.response import Response
from django.db import transaction # Import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import Produk, Transaksi
from .serializers import ProdukSerializer, TransaksiSerializer

# === VIEWSET UNTUK CRUD + SEARCH PRODUK ===
class ProdukViewSet(viewsets.ModelViewSet):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['kode_barang', 'nama_barang']

# === JIKA BUTUH VIEW BERBASIS GENERICS UNTUK DETAIL PRODUK ===
class ProdukRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer

# === VIEWSET UNTUK CRUD + SEARCH TRANSAKSI ===
class TransaksiViewSet(viewsets.ModelViewSet):
    queryset = Transaksi.objects.all().order_by('-waktu_transaksi') # Show newest first
    serializer_class = TransaksiSerializer
    filter_backends = [filters.SearchFilter]
    # Ensure related fields are accessible for search
    search_fields = ['id_transaksi', 'produk__kode_barang', 'produk__nama_barang', 'customer__name', 'customer__email']

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        produk = validated_data['produk']
        customer = validated_data['customer'] # This is a User instance
        jumlah = validated_data['jumlah']

        # Calculate total_harga
        total_harga = produk.harga_satuan * jumlah

        try:
            with transaction.atomic(): # Ensures atomicity
                # 1. Check stock
                if produk.stok < jumlah:
                    raise serializer.ValidationError(f"Not enough stock for {produk.nama_barang}. Available: {produk.stok}")
                
                # 2. Check customer balance
                if customer.balance < total_harga:
                    raise serializer.ValidationError(f"Not enough balance for customer {customer.name}. Required: {total_harga}, Available: {customer.balance}")

                # 3. Reduce product stock
                produk.stok -= jumlah
                produk.save()

                # 4. Reduce customer balance
                customer.balance -= total_harga
                customer.save()
                
                # 5. Save the transaction with the calculated total_harga
                serializer.save(total_harga=total_harga)

        except serializer.ValidationError as e:
            # Re-raise validation errors to be sent as 400 Bad Request
            raise e
        except Exception as e:
            # Handle other potential errors
            raise serializer.ValidationError(str(e))


# === JIKA BUTUH VIEW BERBASIS GENERICS UNTUK DETAIL TRANSAKSI ===
class TransaksiRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaksi.objects.all()
    serializer_class = TransaksiSerializer


# === VIEW UNTUK SALES REPORT ===
class SalesReportView(generics.GenericAPIView):
    # permission_classes = [IsAuthenticated] # Uncomment if report requires login

    def get(self, request, *args, **kwargs):
        total_pendapatan_data = Transaksi.objects.aggregate(total=Sum('total_harga'))
        total_pendapatan = total_pendapatan_data['total'] if total_pendapatan_data['total'] else 0.00

        today_min = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_max = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        penjualan_hari_ini_data = Transaksi.objects.filter(waktu_transaksi__range=(today_min, today_max)).aggregate(total=Sum('total_harga'))
        penjualan_hari_ini = penjualan_hari_ini_data['total'] if penjualan_hari_ini_data['total'] else 0.00
        
        # Laba / Profit Percentage:
        # To calculate profit, you need the cost of goods sold (COGS).
        # If 'harga_satuan' is selling price, you need another field in 'Produk' for cost price.
        # Example: laba_persentase = ((total_pendapatan - total_cogs) / total_cogs) * 100 if total_cogs > 0 else 0
        # For now, we'll put a placeholder.
        persentase_laba = "15.5%" # Placeholder, as per screenshot. Calculation requires cost price data.

        transaksi_terkini = Transaksi.objects.order_by('-waktu_transaksi')[:5] # Get last 5 transactions
        transaksi_terkini_serializer = TransaksiSerializer(transaksi_terkini, many=True)

        report_data = {
            "total_pendapatan": f"Rp {total_pendapatan:,.0f}".replace(",", "."), # Formatted as in screenshot
            "penjualan_hari_ini": f"Rp {penjualan_hari_ini:,.0f}".replace(",", "."), # Formatted
            "persentase_laba": persentase_laba,
            "transaksi_terkini": transaksi_terkini_serializer.data
        }
        return Response(report_data, status=status.HTTP_200_OK)