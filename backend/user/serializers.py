from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    id = serializers.UUIDField(read_only=True) 

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'full_name', 'is_active']
        read_only_fields = ['is_active', 'date_joined']

    def create(self, validated_data):
        if User.objects.filter(email=validated_data['email']).exists():
            raise serializers.ValidationError('Email already exists')
        password = validated_data.pop('password')
        user_instance = User(**validated_data)
        user_instance.set_password(password) # Hash the password
        user_instance.save()
        return user_instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password) # Hash new password

        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.full_name = validated_data.get('full_name', instance.full_name)

        instance.save()
        return instance

# Serializer for Login
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})