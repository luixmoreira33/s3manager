from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

class S3ServiceTests(TestCase):
    @patch('storage_app.services.s3.boto3.client')
    def test_generate_presigned_url(self, mock_boto_client):
        """Testa a geração de URL pré-assinada sem version_id."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = "http://presigned.url"

        from storage_app.services.s3 import generate_presigned_url
        url = generate_presigned_url("test.txt")

        self.assertEqual(url, "http://presigned.url")
        mock_s3.generate_presigned_url.assert_called_once()
        # Verifica se 'VersionId' não está nos parâmetros
        self.assertNotIn('VersionId', mock_s3.generate_presigned_url.call_args[1]['Params'])

    @patch('storage_app.services.s3.boto3.client')
    def test_generate_presigned_url_with_version(self, mock_boto_client):
        """Testa a geração de URL pré-assinada com version_id."""
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.generate_presigned_url.return_value = "http://presigned.url.versioned"

        from storage_app.services.s3 import generate_presigned_url
        url = generate_presigned_url("test.txt", version_id="12345")

        self.assertEqual(url, "http://presigned.url.versioned")
        self.assertEqual(mock_s3.generate_presigned_url.call_args[1]['Params']['VersionId'], '12345')

class StorageAppViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.staff_user = User.objects.create_user(username='staffuser', password='password123', is_staff=True)

    def test_files_list_redirects_if_not_logged_in(self):
        """Verifica se rotas protegidas redirecionam para o login."""
        response = self.client.get(reverse('storage_app:files_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response.url)

    @patch('storage_app.services.s3.list_objects')
    def test_files_list_view_authenticated(self, mock_list_objects):
        """Testa a view de listagem de arquivos para um usuário autenticado."""
        mock_list_objects.return_value = {'Contents': [{'Key': 'file.txt', 'Size': 1024}]}
        self.client.login(username='testuser', password='password123')
        
        response = self.client.get(reverse('storage_app:files_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'file.txt')
        mock_list_objects.assert_called_once()

    @patch('storage_app.services.s3.upload_fileobj')
    def test_file_upload_view(self, mock_upload):
        """Testa o upload de um arquivo."""
        mock_upload.return_value = True
        self.client.login(username='testuser', password='password123')
        
        # Cria um arquivo em memória
        dummy_file = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
        
        response = self.client.post(reverse('storage_app:file_upload'), {'file': dummy_file, 'key': 'test.txt'})
        
        self.assertEqual(response.status_code, 302) # Redirect on success
        self.assertRedirects(response, reverse('storage_app:files_list'))
        mock_upload.assert_called_once()

    @patch('storage_app.services.s3.delete_object_version')
    def test_delete_version_only_for_staff(self, mock_delete):
        """Garante que apenas usuários staff possam deletar versões."""
        # Tenta com usuário comum
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('storage_app:delete_version'), {'key': 'file.txt', 'version_id': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin:login'), response.url) # Redirecionado para o login
        mock_delete.assert_not_called()

        # Tenta com usuário staff
        self.client.login(username='staffuser', password='password123')
        mock_delete.return_value = True
        response = self.client.post(reverse('storage_app:delete_version'), {'key': 'file.txt', 'version_id': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('storage_app:versions_list', kwargs={'key': 'file.txt'}))
        mock_delete.assert_called_once()
