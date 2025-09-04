# Django S3 File Manager

Uma aplicação web completa em Python/Django para gerenciar arquivos em um bucket Amazon S3, com suporte a versionamento, uploads, downloads via URLs pré-assinadas e autenticação.

## Funcionalidades

-   **Autenticação**: Usa o sistema de admin e sessões do Django.
-   **Listagem de Arquivos**: Exibe uma lista paginada de arquivos de um bucket S3.
-   **Upload**: Permite enviar arquivos para o bucket através de um formulário.
-   **Download Seguro**: Gera links de download (presigned URLs) com tempo de expiração.
-   **Versionamento**: Lista todas as versões de um arquivo e permite o download de versões específicas.
-   **Exclusão de Versão**: Permite que usuários `staff` apaguem versões específicas de um arquivo permanentemente.
-   **UI Simples**: Interface limpa e funcional usando Django Templates e Bootstrap 5.

## Stack

-   Python 3.11+
-   Django 5.x
-   boto3
-   python-dotenv
-   gunicorn (para produção)

---

## Setup e Execução

### 1. Pré-requisitos

-   Python 3.11 ou superior
-   Conta na AWS com credenciais de acesso (Access Key ID e Secret Access Key)
-   (Opcional) Docker e Docker Compose

### 2. Configuração do Ambiente Local

**a. Clone o repositório:**

```bash
git clone <url-do-seu-repositorio>
cd s3-file-manager
