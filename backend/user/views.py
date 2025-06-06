# user/views.py

from rest_framework import viewsets, filters, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer, LoginSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint untuk User.
    - GET list: Melihat daftar user (siapa saja boleh).
    - POST: Membuat user baru/registrasi (siapa saja boleh).
    - GET detail, PUT, PATCH, DELETE: Harus login.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'full_name']

    def get_permissions(self):
        # === PERUBAHAN DI SINI ===
        # Sekarang, siapa saja boleh melihat daftar user (list) dan membuat user (create).
        if self.action == 'list' or self.action == 'create':
            self.permission_classes = [AllowAny]
        # Untuk aksi lainnya (melihat detail, mengubah, menghapus), harus sudah login.
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        # Memeriksa apakah data yang masuk adalah list
        is_many = isinstance(request.data, list)

        if not is_many:
            # Jika bukan list, proses seperti biasa
            return super().create(request, *args, **kwargs)
        else:
            # Jika list, gunakan serializer dengan `many=True`
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class LoginView(generics.GenericAPIView):
    """
    API endpoint untuk proses login.
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(request, email=email, password=password)
        if user and user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login berhasil",
                "token": token.key,
                "user_id": user.pk,
                "email": user.email,
                "name": user.name
            }, status=status.HTTP_200_OK)
        
        return Response({"error": "Email atau password salah."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    API endpoint untuk proses logout.
    """
    try:
        request.user.auth_token.delete()
        return Response({"message": "Logout berhasil."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)