from django import template

register = template.Library()

@register.filter
def filesizeformat(value):
    """Converte um valor em bytes para um formato legível (KB, MB, GB)."""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return "0 Bytes"

    if value < 1024:
        return f"{value} Bytes"
    elif value < 1024**2:
        return f"{value/1024:.2f} KB"
    elif value < 1024**3:
        return f"{value/1024**2:.2f} MB"
    else:
        return f"{value/1024**3:.2f} GB"
