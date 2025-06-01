from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User
import uuid

class SimpleTokenAuthentication(BaseAuthentication):
    keyword = 'Bearer'
    custom_header = 'HTTP_X_API_TOKEN'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        token_str = None

        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == self.keyword:
                token_str = parts[1]
        
        if not token_str:
            token_str = request.META.get(self.custom_header)

        if not token_str:
            return None

        try:
            # Validate if the token_str is a valid UUID before querying
            token_uuid = uuid.UUID(token_str) 
            user = User.objects.get(id=token_uuid, is_active=True)
        except ValueError:
            raise AuthenticationFailed('Invalid Token.')
        except User.DoesNotExist:
            raise AuthenticationFailed('User doesn\'t exist.')
        
        return (user, token_uuid) 

    def authenticate_header(self, request):
        return f'{self.keyword} realm="api"'