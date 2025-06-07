from rest_framework import serializers
from .models import Produk, Transaksi # Import model Produk dan Transaksi
from user.models import User # Import User model

class ProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produk
        fields = '__all__'

class TransaksiSerializer(serializers.ModelSerializer):
    """
    Serializer for the Transaksi model.
    Accepts 'customer' as a string (name) and 'produk' by its 'kode_barang'.
    """
    # This field now accepts the customer's name as a string, matching your model.
    customer = serializers.CharField(max_length=100)

    # This correctly uses the product's 'kode_barang' for input.
    produk = serializers.SlugRelatedField(
        queryset=Produk.objects.all(),
        slug_field='kode_barang'
    )

    # These are read-only fields for providing detailed output in the API response.
    total_harga = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    produk_name = serializers.CharField(source='produk.nama_barang', read_only=True)
    kode_barang = serializers.CharField(source='produk.kode_barang', read_only=True)

    class Meta:
        model = Transaksi
        fields = [
            'id_transaksi',
            'customer', # This now directly holds the customer name string.
            'produk',
            'produk_name',
            'jumlah',
            'total_harga',
            'waktu_transaksi',
            'kode_barang'
        ]
        read_only_fields = ['id_transaksi', 'total_harga', 'produk_name', 'kode_barang']

    def validate(self, data):
        """
        Validates that product stock is sufficient for the transaction.
        """
        produk = data['produk']
        jumlah = data['jumlah']

        if float(produk.stok) < float(jumlah):
            raise serializers.ValidationError(f"Stok tidak cukup untuk {produk.nama_barang}. Tersedia: {produk.stok}")

        return data