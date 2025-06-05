from django.db import models
from user.models import User


def get_default_customer_pk():
    user, created = User.objects.get_or_create(name="Default Internal Customer")
    return user.pk

def get_default_produk_pk():
    produk, created = Produk.objects.get_or_create(kode_barang="0000")
    return produk.pk

class Produk(models.Model):
    kode_barang = models.CharField(primary_key=True, max_length=20)
    nama_barang = models.CharField(max_length=100)
    satuan = models.CharField(max_length=20)
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=2)

class Transaksi(models.Model):
    id_transaksi  = models.AutoField(primary_key=True)
    # Option 1: Link to the Customer model defined above
    customer = models.ForeignKey(
                                User,
                                on_delete=models.PROTECT,
                                related_name='transaksi',
                                default=get_default_customer_pk # <<< Add this if the field can be optional in forms/admin
    )
    
    produk = models.ForeignKey(Produk, 
                               on_delete=models.PROTECT, 
                               related_name='transaksi',
                               default=get_default_produk_pk # <<< Add this if the field can be optional in forms/admin
    )
    jumlah = models.PositiveIntegerField() # Quantity of the product purchased
    total_harga = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True) # Corresponds to 'Total Belanja (Rp)'
    waktu_transaksi = models.DateTimeField(auto_now_add=True, blank=True, null=True) # Timestamp of the transaction

    # You might want to add a method to calculate total_harga if it's always jumlah * produk.harga_satuan
    # Or, ensure it's correctly populated upon creation.
    # For example:
    # def save(self, *args, **kwargs):
    #     if not self.total_harga: # Or if you always want to recalculate
    #         self.total_harga = self.produk.harga_satuan * self.jumlah
    #     super().save(*args, **kwargs)

    def __str__(self):
        # Determine if customer or user is used
        user_name = self.user.get_full_name() or self.user.username if hasattr(self, 'customer') and self.customer else "N/A"
        # If using Option 2 (user):
        # customer_name = self.user.get_full_name() or self.user.username if hasattr(self, 'user') and self.user else "N/A"
        return f"Transaksi {self.id} by {user_name} for {self.produk.nama_barang}"
