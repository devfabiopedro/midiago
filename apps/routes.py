import asyncio
import os
from flask import Blueprint, render_template, request, send_file, abort, current_app
from apps.downloader import baixar_midias, apagar_arquivo_temporario

bp = Blueprint("main", __name__)
template_page = "index.html"

@bp.get("/")
def home():
    return render_template(template_page)


@bp.post("/baixar")
def baixar():
    url = request.form.get("url")
    tipo = request.form.get("tipo", "mp4")

    if not url:
        return render_template(template_page, erro="URL inválida ou vazia.")

    try:
        titulo, caminho_arquivo = baixar_midias(url, tipo)
        download_url = f"/download/{os.path.basename(caminho_arquivo)}"

        return render_template(
            template_page,
            mensagem=f"Arquivo pronto: {titulo}",
            download_url=download_url
        )
    except Exception as e:
        print("ERRO:", e)
        msg_error = """Erro ao tentar baixar mídia, 
        pode ser um problema temporário com o serviço de onde você está tentando baixar essa mídia."""
        return render_template(template_page, erro=msg_error)


@bp.get("/download/<nome_arquivo>")
def download(nome_arquivo):
    caminho = os.path.join(current_app.config["DOWNLOAD_DIR"], nome_arquivo)

    if not os.path.exists(caminho):
        abort(404, "Arquivo não encontrado.")

    # agendar exclusão async
    asyncio.create_task(apagar_arquivo_temporario(caminho))

    return send_file(caminho, as_attachment=True)
