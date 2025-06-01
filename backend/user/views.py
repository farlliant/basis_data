from rest_framework import viewsets, filters, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token # For token generation
from .models import Pengguna
from .serializers import PenggunaSerializer, LoginSerializer

class PenggunaViewSet(viewsets.ModelViewSet):
    queryset = Pengguna.objects.all();
    serializer_class = PenggunaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['nama_pengguna', 'email', 'nama_lengkap']

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny,]
        else:
            self.permission_classes = [IsAuthenticated,] 
        return super().get_permissions()


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            pengguna = Pengguna.objects.get(email=email)
        except Pengguna.DoesNotExist:
            return Response({"error": "Account not found"}, status=status.HTTP_404_NOT_FOUND)

        if not pengguna.is_active:
            return Response({"error": "Account is inactive"}, status=status.HTTP_403_FORBIDDEN)

        if pengguna.check_password(password):
            return Response({
                'token': str(pengguna.id_pengguna),
                'id_pengguna': pengguna.id_pengguna,
                'email': pengguna.email,
                'nama_pengguna': pengguna.nama_pengguna
            }, status=status.HTTP_200_OK)
        
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Get the token from the request (DRF's TokenAuthentication adds it to request.auth)
        token_obj = request.auth
        if token_obj:
            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        return Response({"error": "Token not found!"}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)