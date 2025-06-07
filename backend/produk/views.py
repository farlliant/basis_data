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
        date_str = request.query_params.get('date', None)

        if not date_str:
            target_date = timezone.now().date()
        else:
            try:
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        
        transaksi_count_target_date = Transaksi.objects.filter(waktu_transaksi__date=target_date).count()
        
        penjualan_target_date_data = Transaksi.objects.filter(waktu_transaksi__date=target_date).aggregate(total=Sum('total_harga'))
        penjualan_target_date = penjualan_target_date_data['total'] or 0

        penjualan_yesterday_target_date_data = Transaksi.objects.filter(waktu_transaksi__date=target_date - datetime.timedelta(days=1)).aggregate(total=Sum('total_harga'))
        penjualan_yesterday_target_date = penjualan_yesterday_target_date_data['total'] or 0 

        modal_transactions = Transaksi.objects.filter(waktu_transaksi__date=target_date).annotate(
            item_modal=ExpressionWrapper(
                F('produk__harga_satuan') * F('jumlah'), 
                output_field=DecimalField()
            )
        )
        modal_target_date_sum = modal_transactions.aggregate(total=Sum('item_modal'))['total'] or 0

        persentase_laba_target_date = 0
        if modal_target_date_sum > 0:
            persentase_laba_target_date = ((penjualan_target_date - modal_target_date_sum) / modal_target_date_sum) * 100
        
        persentase_penjualan_target_date = 0
        if penjualan_yesterday_target_date > 0:
            persentase_penjualan_target_date = ((penjualan_target_date - penjualan_yesterday_target_date) / penjualan_yesterday_target_date) * 100
        elif penjualan_target_date > 0:
            persentase_penjualan_target_date = 100.0
        
        transaksi_target_date = Transaksi.objects.filter(waktu_transaksi__date=target_date).order_by('-waktu_transaksi')
        transaksi_serializer = TransaksiSerializer(transaksi_target_date, many=True)

        report_data = {
            "tanggal_laporan": target_date.strftime('%Y-%m-%d'),
            "penjualan_target_date": f"Rp {penjualan_target_date:,.0f}".replace(",", "."),
            "persentase_laba_target_date": f"{persentase_laba_target_date:.2f}%",
            "transaksi_target_date": transaksi_serializer.data,
            "transaksi_count_target_date": transaksi_count_target_date,
            "persentase_penjualan_target_date": f"{persentase_penjualan_target_date:.2f}%"
        }
        return Response(report_data, status=status.HTTP_200_OK)
    
    