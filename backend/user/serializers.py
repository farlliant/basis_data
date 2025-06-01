from rest_framework import serializers
from .models import Pengguna

class PenggunaSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    nama_pengguna = serializers.CharField(required=True)
    kata_sandi = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    id_pengguna = serializers.UUIDField(read_only=True) 

    class Meta:
        model = Pengguna
        fields = ['id_pengguna', 'nama_pengguna', 'email', 'kata_sandi', 'nama_lengkap', 'is_active']
        read_only_fields = ['is_active', 'date_joined']

    def create(self, validated_data):
        if Pengguna.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError('Email already exists')
        password = validated_data.pop('kata_sandi')
        pengguna_instance = Pengguna(**validated_data)
        pengguna_instance.set_password(password) # Hash the password
        pengguna_instance.save()
        return pengguna_instance

    def update(self, instance, validated_data):
        password = validated_data.pop('kata_sandi', None)
        if password:
            instance.set_password(password) # Hash new password

        instance.nama_pengguna = validated_data.get('nama_pengguna', instance.nama_pengguna)
        instance.email = validated_data.get('email', instance.email)
        instance.nama_lengkap = validated_data.get('nama_lengkap', instance.nama_lengkap)

        instance.save()
        return instance

# Serializer for Login
class LoginSerializer(serializers.Serializer):
    nama_pengguna = serializers.CharField(required=True)
    kata_sandi = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})