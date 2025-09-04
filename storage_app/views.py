from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404, HttpResponseBadRequest, HttpResponse
from urllib.parse import unquote
import io
from zipfile import ZipFile
from .forms import UploadFileForm
from .services import s3

@login_required
def files_list(request):
    prefix = request.GET.get("prefix", "")
    token = request.GET.get("token")
    
    response = s3.list_objects(prefix=prefix, continuation_token=token)

    # --- Início da Alteração ---
    # Transforma a string do prefixo em uma lista para o "breadcrumb" (navegação)
    breadcrumb_parts = prefix.strip('/').split('/') if prefix else []
    # --- Fim da Alteração ---

    if response is None:
        messages.error(request, "Não foi possível listar os arquivos do S3. Verifique a configuração.")
        context = {"files": [], "folders": [], "prefix": prefix}
    else:
        context = {
            "files": response.get("Contents", []),
            "folders": response.get("CommonPrefixes", []),
            "prefix": prefix,
            "breadcrumb_parts": breadcrumb_parts, # <-- Passa a nova lista para o template
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

@login_required
def download_folder(request):
    prefix = request.GET.get("prefix")
    if not prefix:
        messages.error(request, "Prefixo da pasta não especificado.")
        return redirect("storage_app:files_list")

    # Lista todos os objetos no prefixo
    objects_to_download = s3.get_all_objects_in_prefix(prefix)
    
    # Prepara o arquivo zip em memória
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, 'w') as zip_file:
        for obj in objects_to_download:
            # Não tentamos zipar a própria "pasta" (objeto de 0 bytes)
            if obj['Size'] > 0:
                file_key = obj['Key']
                
                # Baixa o arquivo do S3 para a memória
                file_content = s3.download_object_to_memory(file_key)
                
                if file_content:
                    # Adiciona o arquivo ao zip, mantendo a estrutura de pastas
                    # Remove o prefixo principal para ter caminhos relativos no zip
                    file_path_in_zip = file_key.replace(prefix, "", 1)
                    zip_file.writestr(file_path_in_zip, file_content.read())

    zip_buffer.seek(0)
    
    # Prepara a resposta HTTP
    folder_name = prefix.strip('/').split('/')[-1]
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{folder_name}.zip"'
    
    return response
