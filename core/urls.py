from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("files/", include("storage_app.urls", namespace="storage_app")),
    path("", RedirectView.as_view(pattern_name="storage_app:files_list", permanent=False)),
]
