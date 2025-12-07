import os
import asyncio
from yt_dlp import YoutubeDL
from apps.utils import sanitize_filename
from flask import current_app


def baixar_midias(url: str, tipo: str) -> tuple[str, str]:
    """
    Baixa vídeo ou áudio e retorna (titulo_limpo, caminho_arquivo_final).
    """

    download_dir = current_app.config["DOWNLOAD_DIR"]
    os.makedirs(download_dir, exist_ok=True)

    # Obtém somente informações do vídeo
    with YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    titulo_original = info.get("title", "arquivo")
    titulo_limpo = sanitize_filename(str(titulo_original))

    outtmpl = os.path.join(download_dir, f"{titulo_limpo}.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "ignoreerrors": True,
        "extract_flat": False,
        "no_warnings": True,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        }
    }
    if tipo == "mp4":
        ydl_opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4"
        })

    elif tipo == "mp3":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        })

    # Download
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        arquivo_final = ydl.prepare_filename(info)

    if tipo == "mp3":
        arquivo_final = os.path.splitext(arquivo_final)[0] + ".mp3"

    return titulo_limpo, arquivo_final


async def apagar_arquivo_temporario(caminho: str, delay: int = 10):
    """
    Apaga o arquivo temporário após atraso.
    """
    await asyncio.sleep(delay)
    if os.path.exists(caminho):
        os.remove(caminho)
        print(f"[INFO] Arquivo removido: {caminho}")
