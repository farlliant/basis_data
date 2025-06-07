import datetime
from rest_framework import viewsets, filters, generics, status
from rest_framework.response import Response
from rest_framework.decorators import action # Import action for custom methods
from rest_framework import serializers # Corrected import for serializers
from django.db import transaction # Import transaction
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .models import Produk, Transaksi
from user.models import User # Asumsi User model ada di user.models
from .serializers import ProdukSerializer, TransaksiSerializer

# === VIEWSET UNTUK CRUD + SEARCH PRODUK ===
class ProdukViewSet(viewsets.ModelViewSet):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['kode_barang', 'nama_barang']

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        If the request is a POST and the data is a list, set many=True for bulk creation.
        """
        if self.action == 'create' and isinstance(self.request.data, list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        """
        Allows bulk updating of multiple Produk instances.
        Expects a list of dictionaries, where each dictionary contains 'kode_barang'
        and the fields to be updated.
        Example: [{"kode_barang": "PROD001", "stok": 500}, {"kode_barang": "PROD002", "harga_satuan": "25000.00"}]
        """
        data = request.data
        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a list of items for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_count = 0
        errors = []

        with transaction.atomic(): # Ensure atomicity for the bulk operation
            for item in data:
                # Menggunakan 'kode_barang' sebagai identifier unik
                item_kode_barang = item.get('kode_barang')
                if not item_kode_barang:
                    errors.append({"error": "Each item must have a 'kode_barang' for bulk update.", "item": item})
                    continue

                try:
                    # Mencari produk berdasarkan kode_barang
                    produk = Produk.objects.get(kode_barang=item_kode_barang)
                    
                    # Membuat salinan data untuk diupdate dan menghapus 'kode_barang' dari payload
                    # agar tidak mencoba mengupdate primary key itu sendiri
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
            # If there are errors, return 207 Multi-Status to indicate partial success/failure
            return Response(
                {"message": f"Successfully updated {updated_count} produk(s) with errors.", "errors": errors},
                status=status.HTTP_207_MULTI_STATUS
            )
        # If no errors, return 200 OK
        return Response(
            {"message": f"Successfully updated {updated_count} produk(s)."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Allows bulk deletion of multiple Produk instances.
        Expects a list of kode_barang in the request body.
        Example: {"kode_barang_list": ["PROD001", "PROD002", "PROD003"]}
        """
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
        with transaction.atomic(): # Ensure atomicity for the bulk deletion
            # Filter objects that exist and delete them based on kode_barang
            queryset_to_delete = Produk.objects.filter(kode_barang__in=kode_barang_list)
            deleted_count, _ = queryset_to_delete.delete() # _ captures a dictionary of deleted object counts by type

        # 204 No Content is typically used for successful DELETE requests
        return Response(
            {"message": f"Successfully deleted {deleted_count} produk(s)."},
            status=status.HTTP_204_NO_CONTENT
        )

# === JIKA BUTUH VIEW BERBASIS GENERICS UNTUK DETAIL PRODUK ===
class ProdukRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Produk.objects.all()
    serializer_class = ProdukSerializer
    lookup_field = 'kode_barang' # Menggunakan kode_barang sebagai lookup field untuk detail view

# === VIEWSET UNTUK CRUD + SEARCH TRANSAKSI ===
class TransaksiViewSet(viewsets.ModelViewSet):
    queryset = Transaksi.objects.all().order_by('-waktu_transaksi')
    serializer_class = TransaksiSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_transaksi', 'produk__nama_barang', 'customer__name'] # Asumsi customer adalah field di Transaksi

    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        produk = validated_data['produk']
        customer = validated_data['customer'] # Mengasumsikan customer adalah instance User atau field yang benar
        jumlah = validated_data['jumlah']
        
        # Pastikan produk.harga_satuan adalah tipe numerik yang benar sebelum perkalian
        total_harga = produk.harga_satuan * jumlah

        try:
            with transaction.atomic(): # Ensures atomicity
                # Use select_for_update to lock rows and prevent race conditions
                produk_locked = Produk.objects.select_for_update().get(pk=produk.pk)
                # Customer mungkin tidak memiliki PK, jika 'customer' adalah CharField
                # jika customer adalah ForeignKey ke User, ini akan bekerja.
                # Asumsi 'customer' di model Transaksi adalah ForeignKey ke User:
                # customer_locked = User.objects.select_for_update().get(pk=customer.pk) 
                
                # 1. Check stock
                if produk_locked.stok < jumlah:
                    raise serializers.ValidationError(f"Not enough stock for {produk_locked.nama_barang}. Available: {produk_locked.stok}")
                
                # 2. Check customer balance (hanya jika customer adalah ForeignKey ke User)
                # if hasattr(customer, 'balance') and customer_locked.balance < total_harga:
                #     raise serializers.ValidationError(f"Not enough balance for customer {customer_locked.name}. Required: {total_harga}, Available: {customer_locked.balance}")

                # 3. Reduce product stock
                produk_locked.stok -= jumlah
                produk_locked.save()

                # 4. Reduce customer balance (hanya jika customer adalah ForeignKey ke User)
                # if hasattr(customer, 'balance'):
                #     customer_locked.balance -= total_harga
                #     customer_locked.save()
                
                # 5. Save the transaction with the calculated total_harga
                serializer.save(total_harga=total_harga)
                
        except serializers.ValidationError as e:
            # Re-raise validation errors to be sent as 400 Bad Request
            raise e
        except Exception as e:
            # Handle other potential errors, convert to ValidationError
            raise serializers.ValidationError(str(e))

    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        """
        Allows bulk updating of multiple Transaksi instances.
        Expects a list of dictionaries, where each dictionary contains 'id_transaksi'
        and the fields to be updated.
        Example: [{"id_transaksi": 101, "jumlah": 5}, {"id_transaksi": 102, "waktu_transaksi": "2023-01-15T10:30:00Z"}]
        """
        data = request.data
        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a list of items for bulk update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_count = 0
        errors = []

        with transaction.atomic(): # Ensure atomicity for the bulk operation
            for item in data:
                # Menggunakan 'id_transaksi' sebagai identifier unik
                item_id_transaksi = item.get('id_transaksi')
                if not item_id_transaksi:
                    errors.append({"error": "Each item must have an 'id_transaksi' for bulk update.", "item": item})
                    continue

                try:
                    # Mencari transaksi berdasarkan id_transaksi (primary key)
                    transaksi = Transaksi.objects.get(pk=item_id_transaksi) # id_transaksi adalah primary key, jadi bisa pakai pk
                    
                    # Membuat salinan data untuk diupdate dan menghapus 'id_transaksi' dari payload
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
            # If there are errors, return 207 Multi-Status to indicate partial success/failure
            return Response(
                {"message": f"Successfully updated {updated_count} transaksi(s) with errors.", "errors": errors},
                status=status.HTTP_207_MULTI_STATUS
            )
        # If no errors, return 200 OK
        return Response(
            {"message": f"Successfully updated {updated_count} transaksi(s)."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Allows bulk deletion of multiple Transaksi instances.
        Expects a list of id_transaksi in the request body.
        Example: {"id_transaksi_list": [101, 102, 103]}
        """
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
        with transaction.atomic(): # Ensure atomicity for the bulk deletion
            # Filter objects that exist and delete them based on id_transaksi (primary key)
            queryset_to_delete = Transaksi.objects.filter(pk__in=id_transaksi_list)
            deleted_count, _ = queryset_to_delete.delete()

        # 204 No Content is typically used for successful DELETE requests
        return Response(
            {"message": f"Successfully deleted {deleted_count} transaksi(s)."},
            status=status.HTTP_204_NO_CONTENT
        )


class TransaksiRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaksi.objects.all()
    serializer_class = TransaksiSerializer
    lookup_field = 'id_transaksi' # Menggunakan id_transaksi sebagai lookup field untuk detail view

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
                target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() # Use datetime.datetime
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Count the number of transactions for the chosen day
        transaksi_count_target_date = Transaksi.objects.filter(waktu_transaksi__date=target_date).count()
        
        # Calculate sales (total_harga) for the chosen day
        penjualan_target_date_data = Transaksi.objects.filter(waktu_transaksi__date=target_date).aggregate(total=Sum('total_harga'))
        penjualan_target_date = penjualan_target_date_data['total'] or 0

        # Calculate sales (total_harga) for the yesterday of chosen day
        penjualan_yesterday_target_date_data = Transaksi.objects.filter(waktu_transaksi__date=target_date - datetime.timedelta(days=1)).aggregate(total=Sum('total_harga'))
        penjualan_yesterday_target_date = penjualan_yesterday_target_date_data['total'] or 0 

        # Calculate modal (cost price * quantity) for the chosen day
        # Assuming 'produk__harga_satuan' represents the cost price for profit calculation
        modal_transactions = Transaksi.objects.filter(waktu_transaksi__date=target_date).annotate(
            item_modal=ExpressionWrapper(
                F('produk__harga_satuan') * F('jumlah'), 
                output_field=DecimalField() # Specify output_field type for accuracy
            )
        )
        modal_target_date_sum = modal_transactions.aggregate(total=Sum('item_modal'))['total'] or 0

        # Calculate profit percentage
        persentase_laba_target_date = 0
        if modal_target_date_sum > 0:
            persentase_laba_target_date = ((penjualan_target_date - modal_target_date_sum) / modal_target_date_sum) * 100
        
        # Calculates the sales growth percentage between today and yesterday
        persentase_penjualan_target_date = 0
        if penjualan_yesterday_target_date > 0:
            persentase_penjualan_target_date = ((penjualan_target_date - penjualan_yesterday_target_date) / penjualan_yesterday_target_date) * 100
        elif penjualan_target_date > 0: # If yesterday's sales were zero but today has sales
            persentase_penjualan_target_date = 100.0 # Indicate 100% growth (or start from zero)
        
        # Correctly filter transactions for the chosen day
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
