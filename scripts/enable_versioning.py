import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env na raiz do projeto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL") # Opcional

def get_s3_client():
    """Cria um cliente S3 configurado."""
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        endpoint_url=AWS_S3_ENDPOINT_URL,
    )

def setup_bucket():
    """Garante que o bucket exista e tenha o versionamento ativado."""
    if not AWS_S3_BUCKET_NAME:
        print("Erro: A variável de ambiente AWS_S3_BUCKET_NAME não está definida.")
        return

    s3 = get_s3_client()
    print(f"Verificando bucket '{AWS_S3_BUCKET_NAME}' na região '{AWS_REGION}'...")

    try:
        s3.head_bucket(Bucket=AWS_S3_BUCKET_NAME)
        print("Bucket já existe.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print("Bucket não encontrado. Criando...")
            try:
                # O LocationConstraint é necessário para regiões diferentes de us-east-1
                if AWS_REGION != "us-east-1":
                    s3.create_bucket(
                        Bucket=AWS_S3_BUCKET_NAME,
                        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
                    )
                else:
                    s3.create_bucket(Bucket=AWS_S3_BUCKET_NAME)
                print(f"Bucket '{AWS_S3_BUCKET_NAME}' criado com sucesso.")
            except ClientError as create_error:
                print(f"Erro ao criar o bucket: {create_error}")
                return
        else:
            print(f"Erro ao verificar o bucket: {e}")
            return

    # Habilitar versionamento
    try:
        versioning_status = s3.get_bucket_versioning(Bucket=AWS_S3_BUCKET_NAME)
        status = versioning_status.get("Status", "Not Enabled")
        
        if status == "Enabled":
            print("O versionamento já está ativado.")
        else:
            print("Habilitando versionamento...")
            s3.put_bucket_versioning(
                Bucket=AWS_S3_BUCKET_NAME,
                VersioningConfiguration={"Status": "Enabled"},
            )
            print("Versionamento ativado com sucesso!")
    except ClientError as e:
        print(f"Erro ao configurar o versionamento: {e}")

if __name__ == "__main__":
    setup_bucket()
