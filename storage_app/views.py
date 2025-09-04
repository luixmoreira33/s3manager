from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404, HttpResponseBadRequest
from urllib.parse import unquote

from .forms import UploadFileForm
from .services import s3

@login_required
def files_list(request):
    prefix = request.GET.get("prefix", "")
    token = request.GET.get("token")
    
    response = s3.list_objects(prefix=prefix, continuation_token=token)

    if response is None:
        messages.error(request, "Não foi possível listar os arquivos do S3. Verifique a configuração.")
        context = {"files": [], "prefix": prefix}
    else:
        context = {
            "files": response.get("Contents", []),
            "prefix": prefix,
            "next_token": response.get("NextContinuationToken"),
        }
    return render(request, "storage_app/files_list.html", context)

class FileUploadView(LoginRequiredMixin, View):
    def get(self, request):
        form = UploadFileForm()
        return render(request, "storage_app/upload_form.html", {"form": form})

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            key = form.cleaned_data.get("key") or uploaded_file.name

            success = s3.upload_fileobj(
                uploaded_file, 
                key, 
                uploaded_file.content_type
            )
            
            if success:
                messages.success(request, f"Arquivo '{key}' enviado com sucesso!")
                return redirect("storage_app:files_list")
            else:
                messages.error(request, "Ocorreu um erro durante o upload.")
        
        return render(request, "storage_app/upload_form.html", {"form": form})

@login_required
def download_file(request):
    key = request.GET.get("key")
    if not key:
        return HttpResponseBadRequest("Parâmetro 'key' é obrigatório.")
    
    url = s3.generate_presigned_url(key)
    
    if url:
        return redirect(url)
    else:
        messages.error(request, "Não foi possível gerar o link de download.")
        return redirect("storage_app:files_list")

@login_required
def versions_list(request, key):
    # O key da URL vem com encoding, então decodificamos
    decoded_key = unquote(key)
    versions = s3.list_object_versions(decoded_key)
    
    if versions is None:
        messages.error(request, "Não foi possível listar as versões do arquivo.")
        return redirect("storage_app:files_list")
        
    context = {"key": decoded_key, "versions": versions}
    return render(request, "storage_app/versions_list.html", context)


@login_required
def download_version(request):
    key = request.GET.get("key")
    version_id = request.GET.get("version_id")

    if not key or not version_id:
        return HttpResponseBadRequest("Parâmetros 'key' e 'version_id' são obrigatórios.")

    url = s3.generate_presigned_url(key, version_id=version_id)

    if url:
        return redirect(url)
    else:
        messages.error(request, "Não foi possível gerar o link de download para esta versão.")
        return redirect("storage_app:versions_list", key=key)

@staff_member_required
def delete_version(request):
    if request.method == "POST":
        key = request.POST.get("key")
        version_id = request.POST.get("version_id")

        if not key or not version_id:
            return HttpResponseBadRequest("Parâmetros 'key' e 'version_id' são obrigatórios.")
        
        success = s3.delete_object_version(key, version_id)
        
        if success:
            messages.success(request, f"Versão '{version_id.split('.')[0]}...' do arquivo '{key}' apagada permanentemente.")
        else:
            messages.error(request, "Erro ao apagar a versão do arquivo.")
        
        return redirect("storage_app:versions_list", key=key)
    
    return redirect("storage_app:files_list")
