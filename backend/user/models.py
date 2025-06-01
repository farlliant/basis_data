from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
import uuid

class Pengguna(models.Model):
    id_pengguna = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_pengguna = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    kata_sandi = models.CharField(max_length=128) # Stores the hashed password
    nama_lengkap = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True) # Important for authentication
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return self.nama_pengguna

    # Override the default save method to hash the password
    def save(self, *args, **kwargs):
        if self.kata_sandi and not self.kata_sandi.startswith(('pbkdf2_sha256$', 'argon2$', 'bcrypt_sha256$')):
             self.kata_sandi = make_password(self.kata_sandi)
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.kata_sandi = make_password(raw_password)
        # self.save(update_fields=['kata_sandi'])

    def check_password(self, raw_password):
        return check_password(raw_password, self.kata_sandi)

    # Required for Django admin and some auth parts if you were to use it more deeply
    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True