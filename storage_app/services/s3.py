import logging
import os
from django.conf import settings
import boto3
import io
from zipfile import ZipFile
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def get_s3_client():
    """Retorna um cliente boto3 S3 configurado a partir do settings.py."""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL, # None se não estiver definido
    )

def list_objects(prefix="", continuation_token=None):
    """Lista objetos no bucket S3 com paginação."""
    s3 = get_s3_client()
    try:
        params = {
            "Bucket": settings.AWS_S3_BUCKET_NAME,
            "Prefix": prefix
            "Delimiter": "/",
            "MaxKeys": 50,
        }
        if continuation_token:
            params["ContinuationToken"] = continuation_token
        
        response = s3.list_objects_v2(**params)
        return response
    except ClientError as e:
        logger.error(f"Erro ao listar objetos S3: {e}")
        return None

def upload_fileobj(fileobj, key, content_type):
    """Faz upload de um objeto para o S3."""
    s3 = get_s3_client()
    try:
        s3.upload_fileobj(
            fileobj,
            settings.AWS_S3_BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": content_type}
        )
        return True
    except ClientError as e:
        logger.error(f"Erro ao fazer upload para o S3: {e}")
        return False

def generate_presigned_url(key, version_id=None, expires_in=300):
    """Gera uma URL pré-assinada para download."""
    s3 = get_s3_client()

    # Extrai o nome do arquivo da chave completa
    filename = os.path.basename(key)

    params = {
        "Bucket": settings.AWS_S3_BUCKET_NAME,
        "Key": key,
        # A linha mágica que força o download!
        "ResponseContentDisposition": f'attachment; filename="{filename}"'
    }
    if version_id:
        params["VersionId"] = version_id

    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        logger.error(f"Erro ao gerar URL pré-assinada: {e}")
        return None

def list_object_versions(key):
    """Lista todas as versões de um objeto específico."""
    s3 = get_s3_client()
    try:
        response = s3.list_object_versions(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Prefix=key
        )
        # Filtra para garantir que apenas as versões da chave exata sejam retornadas
        versions = [v for v in response.get("Versions", []) if v["Key"] == key]
        delete_markers = [dm for dm in response.get("DeleteMarkers", []) if dm["Key"] == key]
        
        # Combina e ordena por data
        all_versions = sorted(
            versions + delete_markers,
            key=lambda x: x["LastModified"],
            reverse=True
        )
        return all_versions
    except ClientError as e:
        logger.error(f"Erro ao listar versões do objeto: {e}")
        return []

def delete_object_version(key, version_id):
    """Apaga uma versão específica de um objeto."""
    s3 = get_s3_client()
    try:
        s3.delete_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=key,
            VersionId=version_id
        )
        return True
    except ClientError as e:
        logger.error(f"Erro ao deletar versão do objeto: {e}")
        return False
        
def get_all_objects_in_prefix(prefix):
    """Lista TODOS os objetos sob um determinado prefixo, lidando com paginação."""
    s3 = get_s3_client()
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=settings.AWS_S3_BUCKET_NAME, Prefix=prefix)
    
    files = []
    for page in pages:
        if "Contents" in page:
            for obj in page["Contents"]:
                files.append(obj)
    return files

def download_object_to_memory(key):
    """Baixa um único objeto do S3 para um buffer em memória."""
    s3 = get_s3_client()
    try:
        in_memory_file = io.BytesIO()
        s3.download_fileobj(settings.AWS_S3_BUCKET_NAME, key, in_memory_file)
        in_memory_file.seek(0) # Retorna o cursor para o início do arquivo
        return in_memory_file
    except ClientError as e:
        logger.error(f"Erro ao baixar objeto {key} para a memória: {e}")
        return None
