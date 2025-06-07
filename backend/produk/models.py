from django.db import models
from user.models import User
from django.utils import timezone

def get_default_customer_pk():
    user, created = User.objects.get_or_create(name="Default Internal Customer")
    return user.pk

def get_default_produk_pk():
    produk, created = Produk.objects.get_or_create(Produk.kode_barang)
    return produk.pk

class Produk(models.Model):
    kode_barang = models.CharField(primary_key=True, max_length=20)
    nama_barang = models.CharField(max_length=100)
    stok = models.PositiveIntegerField(default=0)
    satuan = models.CharField(max_length=20)
    harga_satuan = models.PositiveBigIntegerField(default=0) # Price per unit in the smallest currency unit (e.g., cents)

class Transaksi(models.Model):
    id_transaksi  = models.IntegerField(primary_key=True)
    # Option 1: Link to the Customer model defined above
    customer = models.CharField(max_length=100, blank=True, null=True)
    produk = models.ForeignKey(Produk, 
                               on_delete=models.PROTECT, 
                               related_name='transaksi',
    )
    jumlah = models.PositiveIntegerField() # Quantity of the product purchased
    total_harga = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True) # Corresponds to 'Total Belanja (Rp)'
    waktu_transaksi = models.DateTimeField(null=True, blank=True) # Timestamp of the transaction
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    def __str__(self):
        # Determine if customer or user is used
        user_name = self.user.get_full_name() or self.user.username if hasattr(self, 'customer') and self.customer else "N/A"
        # If using Option 2 (user):
        # customer_name = self.user.get_full_name() or self.user.username if hasattr(self, 'user') and self.user else "N/A"
        return f"Transaksi {self.id} by {user_name} for {self.produk.nama_barang}"