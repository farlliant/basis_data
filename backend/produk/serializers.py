from rest_framework import serializers
from .models import Produk, Transaksi
from user.models import User # Import User model

class ProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produk
        fields = '__all__'

class TransaksiSerializer(serializers.ModelSerializer):
    # customer field will now expect a User ID for input
    # and can be configured to show more User details on output if needed.
    customer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    produk = serializers.PrimaryKeyRelatedField(queryset=Produk.objects.all())
    
    # Make total_harga read-only as it's calculated in the view
    total_harga = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    # Include related model string representations for better readability in API responses
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    produk_name = serializers.CharField(source='produk.nama_barang', read_only=True)


    class Meta:
        model = Transaksi
        fields = ['id_transaksi', 'customer', 'customer_name', 'produk', 'produk_name', 'jumlah', 'total_harga', 'waktu_transaksi']
        read_only_fields = ['waktu_transaksi', 'total_harga']


    def validate(self, data):
        """
        Validate stock and customer balance if performing these checks here.
        However, it's often cleaner to do this in the ViewSet's perform_create for atomicity.
        """
        produk = data['produk']
        jumlah = data['jumlah']
        
        if produk.stok < jumlah:
            raise serializers.ValidationError(f"Not enough stock for {produk.nama_barang}. Available: {produk.stok}")
        
        # Balance check will be done in the view for atomicity with saving.
        return data