from rest_framework import serializers
from .models import Produk, Transaksi # Import model Produk dan Transaksi
from user.models import User # Import User model

class ProdukSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produk
        fields = '__all__'

class TransaksiSerializer(serializers.ModelSerializer):
    # Menggunakan PrimaryKeyRelatedField untuk field customer.
    # Ini akan menerima UUID (primary key) dari User di input
    # dan mengonversinya menjadi instance User. Ini sesuai dengan ForeignKey di models.py.
    customer = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    # Menggunakan SlugRelatedField untuk produk.
    # Ini akan menerima 'kode_barang' produk di input
    # dan mengonversinya menjadi instance Produk.
    produk = serializers.SlugRelatedField(
        queryset=Produk.objects.all(),
        slug_field='kode_barang'
    )
    
    # Field total_harga akan dihitung di ViewSet (perform_create) dan hanya untuk output.
    total_harga = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    # Field tambahan untuk menampilkan nama customer dan produk di output JSON, read-only.
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    produk_name = serializers.CharField(source='produk.nama_barang', read_only=True)
    
    # Menambahkan kode_barang sebagai read-only field di output jika diperlukan,
    # meskipun sudah bisa diakses via 'produk' object jika ingin.
    kode_barang = serializers.CharField(source='produk.kode_barang', read_only=True)

    class Meta:
        model = Transaksi
        fields = [
            'id_transaksi', 
            'customer', 
            'customer_name', # Untuk output
            'produk', 
            'produk_name', # Untuk output
            'jumlah', 
            'total_harga', 
            'waktu_transaksi', 
            'kode_barang' # Untuk output
        ]
        # Menentukan semua field yang bersifat read-only.
        # id_transaksi (AutoField) dan total_harga (dihitung) adalah read-only.
        # customer_name, produk_name, kode_barang juga read-only karena mereka derived fields.
        read_only_fields = ['id_transaksi', 'total_harga', 'customer_name', 'produk_name', 'kode_barang']


    def validate(self, data):
        """
        Melakukan validasi data sebelum disimpan ke database.
        Memastikan stok produk mencukupi untuk jumlah transaksi yang diminta.
        """
        produk = data['produk']
        jumlah = data['jumlah']
        
        # Validasi stok: pastikan stok produk tidak kurang dari jumlah yang diminta.
        if produk.stok < jumlah:
            raise serializers.ValidationError(f"Stok tidak cukup untuk {produk.nama_barang}. Tersedia: {produk.stok}")
        
        # Karena tidak ada konsep saldo, pengecekan saldo telah dihapus dari ViewSet.
        return data