import re

def sanitize_filename(name: str) -> str:
    """
    Remove caracteres inválidos de nomes de arquivos.
    """
    name = name.strip()
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name
