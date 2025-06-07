import datetime
from rest_framework import viewsets, filters, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
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
    queryset = Transaksi.objects.all().order_by('-waktu_transaksi')
    serializer_class = TransaksiSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_transaksi', 'produk__nama_barang', 'customer']

    def get_serializer(self, *args, **kwargs):
        if self.action == 'create' and isinstance(self.request.data, list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        # For a single transaction request
        if not serializer.many:
            validated_data = serializer.validated_data
            produk = validated_data['produk']
            jumlah = validated_data['jumlah']
            
            # Calculate the total price for the transaction.
            total_harga = produk.harga_satuan * jumlah

            try:
                # Use a database transaction to ensure data integrity.
                with transaction.atomic():
                    # Lock the product row to prevent race conditions during stock update.
                    produk_locked = Produk.objects.select_for_update().get(pk=produk.pk)
                    
                    if float(produk_locked.stok) < float(jumlah):
                        raise serializers.ValidationError(f"Stok tidak cukup untuk {produk_locked.nama_barang}. Tersedia: {produk_locked.stok}")
                    
                    produk_locked.stok = F('stok') - jumlah
                    produk_locked.save()
                    
                    # Save the transaction with the calculated total price.
                    serializer.save(total_harga=total_harga)
            except Exception as e:
                raise serializers.ValidationError(str(e))
        else:
            # For a bulk transaction request (list of transactions)
            instances = []
            try:
                with transaction.atomic():
                    for item_data in serializer.validated_data:
                        produk = item_data['produk']
                        jumlah = item_data['jumlah']
                        customer_name = item_data['customer']
                        
                        total_harga = produk.harga_satuan * jumlah
                        
                        produk_locked = Produk.objects.select_for_update().get(pk=produk.pk)
                        
                        if float(produk_locked.stok) < float(jumlah):
                            raise serializers.ValidationError(f"Stok tidak cukup untuk {produk_locked.nama_barang}. Tersedia: {produk_locked.stok} (for item {produk.nama_barang})")
                        
                        produk_locked.stok = F('stok') - jumlah
                        produk_locked.save()

                        instance = Transaksi.objects.create(
                            produk=produk,
                            customer=customer_name,
                            jumlah=jumlah,
                            waktu_transaksi=item_data.get('waktu_transaksi', timezone.now()),
                            total_harga=total_harga
                        )
                        instances.append(instance)
            except Exception as e:
                raise serializers.ValidationError(f"Terjadi kesalahan saat memproses transaksi bulk: {str(e)}")

class TransaksiRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaksi.objects.all()
    serializer_class = TransaksiSerializer

class SalesReportView(generics.GenericAPIView):

    def get(self, request, *args, **kwargs):
        # Correctly get the date string from query params
        date_str = request.query_params.get('date', None)

        if not date_str:
            # Default to today if no date is provided
            target_date = timezone.now().date()
        else:
            try:
                # Correctly parse the date string into a date object
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Count the number of transactions for the chosen day
        transaksi_count_target_date = Transaksi.objects.filter(waktu_transaksi__date=target_date).count()
        
        # Calculate sales for the chosen day
        penjualan_target_date_data = Transaksi.objects.filter(waktu_transaksi__date=target_date).aggregate(total=Sum('total_harga'))
        penjualan_target_date = penjualan_target_date_data['total'] or 0

        # Calculate sales for the yesterday of chosen day
        penjualan_yesterday_target_date_data = Transaksi.objects.filter(waktu_transaksi__date=target_date - datetime.timedelta(days=1)).aggregate(total=Sum('total_harga'))
        penjualan_yesterday_target_date = penjualan_yesterday_target_date_data['total'] or 0 

        # Note: Accurate profit calculation requires a 'cost_price' field on the Produk model.
        modal_target_date = Transaksi.objects.filter(waktu_transaksi__date=target_date).aggregate(total=Sum('produk__harga_satuan * jumlah'))
        persentase_laba_target_date = penjualan_target_date / modal_target_date['total'] * 100 / 100.0 # Placeholder, as per screenshot. Calculation requires cost price data.

        # Calculates the difference between today and yesterday's sales
        persentase_penjualan_target_date = (penjualan_target_date - penjualan_yesterday_target_date) / penjualan_yesterday_target_date * 100

        # Correctly filter transactions for the chosen day
        transaksi_target_date = Transaksi.objects.filter(waktu_transaksi__date=target_date).order_by('-waktu_transaksi')
        transaksi_serializer = TransaksiSerializer(transaksi_target_date, many=True)

        report_data = {
            "tanggal_laporan": target_date.strftime('%Y-%m-%d'),
            "penjualan_target_date": f"Rp {penjualan_target_date:,.0f}".replace(",", "."),
            "persentase_laba_target_date": persentase_laba_target_date,
            "transaksi_target_date": transaksi_serializer.data,
            "transaksi_count_target_date": transaksi_count_target_date,
            "persentase_penjualan_target_date": persentase_penjualan_target_date
        }
        return Response(report_data, status=status.HTTP_200_OK)
    
    