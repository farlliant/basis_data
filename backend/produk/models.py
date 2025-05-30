from django.db import models

class Produk(models.Model):
    kode_barang = models.CharField(primary_key=True, max_length=20)
    nama_barang = models.CharField(max_length=100)
    satuan = models.CharField(max_length=20)
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=2)

class Transaksi(models.Model):
    id_transaksi = models.AutoField(primary_key=True)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    jumlah = models.PositiveIntegerField()