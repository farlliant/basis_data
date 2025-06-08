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

    def get_serializer(self, *args, **kwargs):
        if self.action == 'create' and isinstance(self.request.data, list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        data = request.data
        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a list of items for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_count = 0
        errors = []

        with transaction.atomic():
            for item in data:
                item_kode_barang = item.get('kode_barang')
                if not item_kode_barang:
                    errors.append({"error": "Each item must have a 'kode_barang' for bulk update.", "item": item})
                    continue

                try:
                    produk = Produk.objects.get(kode_barang=item_kode_barang)
                    
                    update_data = item.copy()
                    update_data.pop('kode_barang', None) 

                    serializer = self.get_serializer(produk, data=update_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    updated_count += 1
                except Produk.DoesNotExist:
                    errors.append({"error": f"Produk with kode_barang '{item_kode_barang}' not found.", "item": item})
                except serializers.ValidationError as e:
                    errors.append({"error": e.detail, "item": item})
                except Exception as e:
                    errors.append({"error": str(e), "item": item})

        if errors:
            return Response(
                {"message": f"Successfully updated {updated_count} produk(s) with errors.", "errors": errors},
                status=status.HTTP_207_MULTI_STATUS
            )
        return Response(
            {"message": f"Successfully updated {updated_count} produk(s)."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        kode_barang_list = request.data.get('kode_barang_list', [])
        if not isinstance(kode_barang_list, list):
            return Response(
                {"detail": "Expected a dictionary with a 'kode_barang_list' list for bulk delete."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not kode_barang_list:
            return Response(
                {"detail": "No kode_barang provided for bulk deletion."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count = 0
        with transaction.atomic():
            queryset_to_delete = Produk.objects.filter(kode_barang__in=kode_barang_list)
            deleted_count, _ = queryset_to_delete.delete()

        return Response(
            {"message": f"Successfully deleted {deleted_count} produk(s)."},
            status=status.HTTP_204_NO_CONTENT
        )

class ProdukRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer
    lookup_field = 'kode_barang'

class TransaksiViewSet(viewsets.ModelViewSet):
    queryset = Transaksi.objects.all().order_by('-waktu_transaksi')
    serializer_class = TransaksiSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_transaksi', 'produk__nama_barang', 'customer__name']

    def get_serializer(self, *args, **kwargs):
        if self.action == 'create' and isinstance(self.request.data, list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

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
        if getattr(serializer, 'many', False):
            # For bulk transaction requests (a list of items)
            instances = []
            with transaction.atomic():
                for item_data in serializer.validated_data:
                    produk = item_data['produk']
                    customer_name = item_data['customer']
                    jumlah = item_data['jumlah']
                    total_harga = produk.harga_satuan * jumlah

                    try:
                        produk_locked = Produk.objects.select_for_update().get(pk=produk.pk)
                        
                        if float(produk_locked.stok) < float(jumlah):
                            raise serializers.ValidationError(f"Stok tidak cukup untuk {produk_locked.nama_barang}. Tersedia: {produk_locked.stok}")
                        
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

                    except Produk.DoesNotExist:
                        raise serializers.ValidationError(f"Produk dengan ID {produk.pk} tidak ditemukan.")
                    except serializers.ValidationError:
                        raise
                    except Exception as e:
                        raise serializers.ValidationError(f"Terjadi kesalahan saat memproses transaksi: {str(e)}")
        # For a single transaction request
        else:
            validated_data = serializer.validated_data
            produk = validated_data['produk']
            jumlah = validated_data['jumlah']
            total_harga = produk.harga_satuan * jumlah

            try:
                with transaction.atomic():
                    produk_locked = Produk.objects.select_for_update().get(pk=produk.pk)
                    
                    if float(produk_locked.stok) < float(jumlah):
                        raise serializers.ValidationError(f"Stok tidak cukup untuk {produk_locked.nama_barang}. Tersedia: {produk_locked.stok}")
                    
                    produk_locked.stok = F('stok') - jumlah
                    produk_locked.save()
                    
                    serializer.save(total_harga=total_harga)
                    
            except serializers.ValidationError as e:
                raise e
            except Exception as e:
                raise serializers.ValidationError(str(e))

    # No changes are needed for your existing bulk_update and bulk_delete methods.
    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        # ... (Your existing code here)
        pass

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        # ... (Your existing code here)
        pass

    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        data = request.data
        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a list of items for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_count = 0
        errors = []

        with transaction.atomic():
            for item in data:
                item_id_transaksi = item.get('id_transaksi')
                if not item_id_transaksi:
                    errors.append({"error": "Each item must have an 'id_transaksi' for bulk update.", "item": item})
                    continue

                try:
                    transaksi = Transaksi.objects.get(pk=item_id_transaksi)
                    
                    update_data = item.copy()
                    update_data.pop('id_transaksi', None)

                    serializer = self.get_serializer(transaksi, data=update_data, partial=True)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    updated_count += 1
                except Transaksi.DoesNotExist:
                    errors.append({"error": f"Transaksi with id_transaksi {item_id_transaksi} not found.", "item": item})
                except serializers.ValidationError as e:
                    errors.append({"error": e.detail, "item": item})
                except Exception as e:
                    errors.append({"error": str(e), "item": item})

        if errors:
            return Response(
                {"message": f"Successfully updated {updated_count} transaksi(s) with errors.", "errors": errors},
                status=status.HTTP_207_MULTI_STATUS
            )
        return Response(
            {"message": f"Successfully updated {updated_count} transaksi(s)."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        id_transaksi_list = request.data.get('id_transaksi_list', [])
        if not isinstance(id_transaksi_list, list):
            return Response(
                {"detail": "Expected a dictionary with an 'id_transaksi_list' list for bulk delete."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not id_transaksi_list:
            return Response(
                {"detail": "No id_transaksi provided for bulk deletion."},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count = 0
        with transaction.atomic():
            queryset_to_delete = Transaksi.objects.filter(pk__in=id_transaksi_list)
            deleted_count, _ = queryset_to_delete.delete()

        return Response(
            {"message": f"Successfully deleted {deleted_count} transaksi(s)."},
            status=status.HTTP_204_NO_CONTENT
        )

class TransaksiRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaksi.objects.all()
    serializer_class = TransaksiSerializer
    lookup_field = 'id_transaksi'

class SalesReportView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        month_str = request.query_params.get('month', None)
        year_str = request.query_params.get('year', None)

        if not month_str or not year_str:
            # Default to current month and year if not provided
            target_date = timezone.now().date()
            target_month = target_date.month
            target_year = target_date.year
        else:
            try:
                target_month = int(month_str)
                target_year = int(year_str)
                # Validate month and year
                if not (1 <= target_month <= 12) or not (1900 <= target_year <= 2100): # Adjust year range as needed
                    return Response({"error": "Invalid month or year. Month must be 1-12, Year must be valid."}, status=status.HTTP_400_BAD_REQUEST)
                
                target_date = datetime.date(target_year, target_month, 1) # Set to the first day of the target month
            except ValueError:
                return Response({"error": "Invalid month or year format. Use numbers for month and year."}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate the start and end dates for the target month
        start_of_month = datetime.date(target_year, target_month, 1)
        # Get the last day of the month
        if target_month == 12:
            end_of_month = datetime.date(target_year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            end_of_month = datetime.date(target_year, target_month + 1, 1) - datetime.timedelta(days=1)

        # Calculate the start and end dates for the previous month
        first_day_prev_month = start_of_month - datetime.timedelta(days=1)
        prev_month = first_day_prev_month.month
        prev_year = first_day_prev_month.year
        start_of_prev_month = datetime.date(prev_year, prev_month, 1)
        end_of_prev_month = start_of_month - datetime.timedelta(days=1)

        # --- Data for the target month ---
        transaksi_count_target_month = Transaksi.objects.filter(
            waktu_transaksi__date__gte=start_of_month,
            waktu_transaksi__date__lte=end_of_month
        ).count()
        
        penjualan_target_month_data = Transaksi.objects.filter(
            waktu_transaksi__date__gte=start_of_month,
            waktu_transaksi__date__lte=end_of_month
        ).aggregate(total=Sum('total_harga'))
        penjualan_target_month = penjualan_target_month_data['total'] or 0

        modal_transactions_target_month = Transaksi.objects.filter(
            waktu_transaksi__date__gte=start_of_month,
            waktu_transaksi__date__lte=end_of_month
        ).annotate(
            item_modal=ExpressionWrapper(
                F('produk__harga_satuan') * F('jumlah'), 
                output_field=DecimalField()
            )
        )
        modal_target_month_sum = modal_transactions_target_month.aggregate(total=Sum('item_modal'))['total'] or 0

        # --- Data for the previous month (for comparison) ---
        penjualan_prev_month_data = Transaksi.objects.filter(
            waktu_transaksi__date__gte=start_of_prev_month,
            waktu_transaksi__date__lte=end_of_prev_month
        ).aggregate(total=Sum('total_harga'))
        penjualan_prev_month = penjualan_prev_month_data['total'] or 0 

        # --- Data for the target year (annual sales) ---
        start_of_target_year = datetime.date(target_year, 1, 1)
        end_of_target_year = datetime.date(target_year, 12, 31)
        penjualan_target_year_data = Transaksi.objects.filter(
            waktu_transaksi__date__gte=start_of_target_year,
            waktu_transaksi__date__lte=end_of_target_year
        ).aggregate(total=Sum('total_harga'))
        penjualan_target_year = penjualan_target_year_data['total'] or 0

        # --- Data for the previous year (for comparison) ---
        prev_year_for_annual = target_year - 1
        start_of_prev_year_annual = datetime.date(prev_year_for_annual, 1, 1)
        end_of_prev_year_annual = datetime.date(prev_year_for_annual, 12, 31)
        penjualan_prev_year_annual_data = Transaksi.objects.filter(
            waktu_transaksi__date__gte=start_of_prev_year_annual,
            waktu_transaksi__date__lte=end_of_prev_year_annual
        ).aggregate(total=Sum('total_harga'))
        penjualan_prev_year_annual = penjualan_prev_year_annual_data['total'] or 0


        # --- Calculations ---
        persentase_laba_target_month = 0
        if modal_target_month_sum > 0:
            persentase_laba_target_month = ((penjualan_target_month - modal_target_month_sum) / modal_target_month_sum) * 100
        
        persentase_penjualan_target_month = 0
        if penjualan_prev_month > 0:
            persentase_penjualan_target_month = ((penjualan_target_month - penjualan_prev_month) / penjualan_prev_month) * 100
        elif penjualan_target_month > 0:
            persentase_penjualan_target_month = 100.0 # If previous month had no sales, but current does, it's 100% growth

        # Calculate percentage change for annual sales
        persentase_penjualan_dibanding_tahun_lalu = 0
        if penjualan_prev_year_annual > 0:
            persentase_penjualan_dibanding_tahun_lalu = ((penjualan_target_year - penjualan_prev_year_annual) / penjualan_prev_year_annual) * 100
        elif penjualan_target_year > 0:
            persentase_penjualan_dibanding_tahun_lalu = 100.0 # If previous year had no sales, but current does, it's 100% growth


        transaksi_target_month = Transaksi.objects.filter(
            waktu_transaksi__date__gte=start_of_month,
            waktu_transaksi__date__lte=end_of_month
        ).order_by('-waktu_transaksi')
        transaksi_serializer = TransaksiSerializer(transaksi_target_month, many=True)

        report_data = {
            "bulan_laporan": target_date.strftime('%Y-%m'),
            "penjualan_bulan_ini": f"Rp {penjualan_target_month:,.0f}".replace(",", "."),
            "persentase_laba_bulan_ini": f"{persentase_laba_target_month:.2f}%",
            "transaksi_bulan_ini": transaksi_serializer.data,
            "jumlah_transaksi_bulan_ini": transaksi_count_target_month,
            "persentase_penjualan_dibanding_bulan_lalu": f"{persentase_penjualan_target_month:.2f}%",
            # New additions
            "penjualan_tahun_ini": f"Rp {penjualan_target_year:,.0f}".replace(",", "."),
            "persentase_penjualan_dibanding_tahun_lalu": f"{persentase_penjualan_dibanding_tahun_lalu:.2f}%"
        }
        return Response(report_data, status=status.HTTP_200_OK)