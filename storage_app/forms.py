from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Selecione um arquivo",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    key = forms.CharField(
        label="Nome/Caminho do arquivo no S3 (opcional)",
        required=False,
        help_text="Ex: pasta/subpasta/meu-arquivo.txt. Se vazio, usa o nome original.",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'caminho/para/o/arquivo.ext'})
    )
