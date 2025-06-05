# produk/admin.py
from django.contrib import admin
from .models import Produk, Transaksi

admin.site.register(Produk)
admin.site.register(Transaksi)
