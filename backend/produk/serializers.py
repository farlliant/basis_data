from rest_framework import serializers
from .models import Produk, Transaksi
from user.models import User # Import User model

class ProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produk
        fields = '__all__'

class TransaksiSerializer(serializers.ModelSerializer):
    """
    Serializer for the Transaksi model.
    Accepts 'customer' as a string (name) and 'produk' as a string (kode_barang).
    """
    # This field now accepts the customer's name as a string.
    customer = serializers.CharField(max_length=100)

    # This field correctly accepts the product's 'kode_barang' as a string.
    produk = serializers.SlugRelatedField(
        queryset=Produk.objects.all(),
        slug_field='kode_barang'
    )
    
    # These fields are for read-only output to include more details in the API response.
    total_harga = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    produk_name = serializers.CharField(source='produk.nama_barang', read_only=True)
    kode_barang = serializers.CharField(source='produk.kode_barang', read_only=True)

    class Meta:
        model = Transaksi
        fields = [
            'id_transaksi', 
            'customer', 
            'produk', 
            'produk_name',
            'jumlah', 
            'total_harga', 
            'waktu_transaksi', 
            'kode_barang'
        ]
        # These fields are either auto-generated or calculated in the backend.
        read_only_fields = ['id_transaksi', 'total_harga', 'produk_name', 'kode_barang']


    def validate(self, data):
        """
        Performs validation before creating a transaction.
        Ensures that the product stock is sufficient for the requested quantity.
        """
        produk = data['produk']
        jumlah = data['jumlah']
        
        # Validate that the requested quantity does not exceed the available stock.
        if float(produk.stok) < float(jumlah):
            raise serializers.ValidationError(f"Stok tidak cukup untuk {produk.nama_barang}. Tersedia: {produk.stok}")
        
        return data