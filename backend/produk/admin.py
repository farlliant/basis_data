# farlliant/basis_data/basis_data-082a188571337ff8a3b1b4193fd9f8a80e851b83/backend/produk/admin.py
from django.contrib import admin
from .models import Produk, Transaksi

@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = ('kode_barang', 'nama_barang', 'stok', 'harga_satuan', 'satuan')
    search_fields = ('kode_barang', 'nama_barang')
    list_filter = ('stok',)
    ordering = ('stok', 'kode_barang')

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    list_display = ('id_transaksi', 'customer_name_display', 'produk_name_display', 'jumlah', 'total_harga', 'waktu_transaksi')
    search_fields = ('id_transaksi', 'customer__name', 'produk__nama_barang')
    list_filter = ('waktu_transaksi', 'produk__nama_barang')
    readonly_fields = ('total_harga', 'waktu_transaksi')
    date_hierarchy = 'waktu_transaksi'

    def customer_name_display(self, obj):
        return obj.customer.name if obj.customer else None
    customer_name_display.short_description = 'Customer Name'

    def produk_name_display(self, obj):
        return obj.produk.nama_barang if obj.produk else None
    produk_name_display.short_description = 'Product Name'