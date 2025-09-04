from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


admin.site.site_header = "S3 File Manager"
admin.site.site_title = "Painel S3 Manager"
admin.site.index_title = "Bem-vindo ao Gerenciador de Arquivos"



urlpatterns = [
    path("admin/", admin.site.urls),
    path("files/", include("storage_app.urls", namespace="storage_app")),
    path("", RedirectView.as_view(pattern_name="storage_app:files_list", permanent=False)),
]
