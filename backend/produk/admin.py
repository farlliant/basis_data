# produk/admin.py
from django.contrib import admin
from .models import Produk, Transaksi

admin.site.register(Produk)
admin.site.register(Transaksi)
from django.contrib import admin
from .models import Produk, Transaksi


@admin.register(Produk) # Using decorator for registration
class ProdukAdmin(admin.ModelAdmin):
    list_display = ('kode_barang', 'nama_barang', 'stok', 'harga_satuan', 'satuan')
    search_fields = ('kode_barang', 'nama_barang')
    list_filter = ('stok',) # Allows filtering by stock ranges in the admin sidebar
    ordering = ('stok', 'kode_barang') # Order by stock (e.g., low stock first) then by kode_barang

@admin.register(Transaksi) # Using decorator for registration
class TransaksiAdmin(admin.ModelAdmin):
    list_display = ('id_transaksi', 'customer_name_display', 'produk_name_display', 'jumlah', 'total_harga', 'waktu_transaksi')
    search_fields = ('id_transaksi', 'customer__name', 'produk__nama_barang') # Use __ to search related fields
    list_filter = ('waktu_transaksi', 'produk__nama_barang')
    readonly_fields = ('total_harga', 'waktu_transaksi')
    date_hierarchy = 'waktu_transaksi'

    def customer_name_display(self, obj):
        return obj.customer.name if obj.customer else None
    customer_name_display.short_description = 'Customer Name'

    def produk_name_display(self, obj):
        return obj.produk.nama_barang if obj.produk else None
    produk_name_display.short_description = 'Product Name'

# If you previously had admin.site.register(Produk) without a class,
# the @admin.register(Produk) decorator replaces that. Same for Transaksi.