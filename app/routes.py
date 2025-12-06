import asyncio
import os
from flask import Blueprint, render_template, request, send_file, abort, current_app
from .downloader import baixar_midias, apagar_arquivo_temporario

bp = Blueprint("main", __name__)


@bp.get("/")
def home():
    return render_template("index.html")


@bp.post("/baixar")
def baixar():
    url = request.form.get("url")
    tipo = request.form.get("tipo", "mp4")

    if not url:
        return render_template("index.html", erro="URL inválida ou vazia.")

    try:
        titulo, caminho_arquivo = baixar_midias(url, tipo)
        download_url = f"/download/{os.path.basename(caminho_arquivo)}"

        return render_template(
            "index.html",
            mensagem=f"Arquivo pronto: {titulo}",
            download_url=download_url
        )
    except Exception as e:
        print("ERRO:", e)
        return render_template("index.html", erro=f"Erro ao tentar baixar: {e}")


@bp.get("/download/<nome_arquivo>")
def download(nome_arquivo):
    caminho = os.path.join(current_app.config["DOWNLOAD_DIR"], nome_arquivo)

    if not os.path.exists(caminho):
        abort(404, "Arquivo não encontrado.")

    # agendar exclusão async
    asyncio.create_task(apagar_arquivo_temporario(caminho))

    return send_file(caminho, as_attachment=True)
