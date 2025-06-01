from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import uuid

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128) # Stores the hashed password
    full_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True) # Important for authentication
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.name

    # Override the default save method to hash the password
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith(('pbkdf2_sha256$', 'argon2$', 'bcrypt_sha256$')):
             self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        # self.save(update_fields=['password'])

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # Required for Django admin and some auth parts if you were to use it more deeply
    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True