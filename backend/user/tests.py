from django.test import TestCase

# Tests
# from .models import Pengguna
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase

# class PenggunaAPITests(APITestCase):
#     def test_create_pengguna(self):
#         """
#         Ensure we can create a new pengguna object.
#         """
#         url = reverse('pengguna-list') # 'pengguna-list' is the default name given by router for list/create
#         data = {'nama_pengguna': 'testuser', 'email': 'test@example.com', 'kata_sandi': 'testpassword123'}
#         response = self.client.post(url, data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Pengguna.objects.count(), 1)
#         self.assertEqual(Pengguna.objects.get().nama_pengguna, 'testuser')