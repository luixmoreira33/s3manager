from django.urls import path
from . import views

app_name = "storage_app"

urlpatterns = [
    path("", views.files_list, name="files_list"),
    path("upload/", views.FileUploadView.as_view(), name="file_upload"),
    path("download/", views.download_file, name="download_file"),
    path("versions/<path:key>/", views.versions_list, name="versions_list"),
    path("download-version/", views.download_version, name="download_version"),
    path("delete-version/", views.delete_version, name="delete_version"),
    path("download-folder/", views.download_folder, name="download_folder"),
]
