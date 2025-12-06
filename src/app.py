from typing import Any, cast
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from yt_dlp import YoutubeDL
import os
import asyncio
import re

app = FastAPI(title="FP Video Downloader")

# Diretório dos templates
templates = Jinja2Templates(directory="src/templates")

# Cria o diretório para os downloads temporários, caso não exista.
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Carrega oa arquivos estáticos.
app.mount("/static", StaticFiles(directory=os.path.join("src", "static")), name="static")

# Arquivo HTML página principal.
html_template_file = "index.html"



# SANITIZAÇÃO DO NOME DO ARQUIVO
#__________________________________________________________________

def sanitize_filename(name: str) -> str:
    """
    Remove caracteres inválidos de nomes de arquivo.

    :param name: Nome original do arquivo.
    :return: Nome sanitizado do arquivo.
    """
    name = name.strip()
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name


# ROTA PRINCIPAL (FORMULÁRIO)
#__________________________________________________________________
@app.get("/", response_class=HTMLResponse)
async def formulario(request: Request) -> HTMLResponse:
    """
    Rota principal que exibe o formulário para o usuário inserir a URL do vídeo.
    
    :param request: Objeto Request do FastAPI.
    :return: TemplateResponse com o formulário HTML.
    """
    return templates.TemplateResponse(html_template_file, {"request": request})


# ROTA PARA BAIXAR VÍDEO/ÁUDIO
#__________________________________________________________________
@app.post("/baixar")
async def baixar(request: Request, url: str = Form(...), tipo: str = Form("mp4")) -> HTMLResponse:
    """
    Rota para processar o download do vídeo/áudio a partir da URL fornecida.

    :param request: Objeto Request do FastAPI.
    :param url: URL do vídeo a ser baixado.
    :param tipo: Tipo de download ("mp4" para vídeo, "mp3" para áudio).
    :return: TemplateResponse com o link de download ou mensagem de erro.
    """
    try:
        # Primeiro: obter nome real do vídeo
        with YoutubeDL({"quiet": True}) as ydl:
            # Obtém o nome do vídeo sem baixar ele.
            info = ydl.extract_info(url, download=False)

        titulo_original = info.get("title", "arquivo")
        titulo_limpo = sanitize_filename(str(titulo_original))

        # Define o template de saída sem usar extensão fixa
        #(será atribuída depois de acordo com o tipo escolhido MP4 ou MP3)
        outtmpl = os.path.join(DOWNLOAD_DIR, f"{titulo_limpo}.%(ext)s")

        # Configurações da lib yt_dlp para o tipo de download.
        ydl_opts: dict[str, Any] = {
            "outtmpl": outtmpl,
            "quiet": True,
            "ignoreerrors": True,
            "extract_flat": False,
            "no_warnings": True
        }

        # Caso escolha MP4 (vídeo) (Este já é o padrão)
        if tipo == "mp4":
            ydl_opts.update({
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4"
            })

        # Caso escolha MP3 (áudio)
        elif tipo == "mp3":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            })

        # Cria o objeto FileDownload
        with YoutubeDL(cast(Any, ydl_opts)) as ydl:
            info = ydl.extract_info(url, download=True)
            arquivo_final = ydl.prepare_filename(info)

        # Quando é MP3, a extensão real vai mudar após o postprocess.
        if tipo == "mp3":
            arquivo_final = os.path.splitext(arquivo_final)[0] + ".mp3"

        # Preparo a URL indicando onde vai acontecer o download do arquivo para um postprocess.
        download_url = f"/download/{os.path.basename(arquivo_final)}"

        # Responde a requisição com o link de download e o título da mídia.
        return templates.TemplateResponse(
            html_template_file,
            {
                "request": request,
                "mensagem": f"Arquivo pronto para download!\n( {titulo_limpo} )",
                "download_url": download_url,
            }
        )

    except Exception as e:
        print("ERRO:", e)
        # Responde a requisição com a mensagem de erro caso não consiga obter.
        return templates.TemplateResponse(
            html_template_file,
            {
                "request": request,
                "erro": f"Erro ao tentar baixar: {str(e)}"
            }
        )


# ROTA DE DOWNLOAD VÍDEO/ÁUDIO
#__________________________________________________________________

@app.get("/download/{nome_arquivo}") 
async def download(nome_arquivo: str)-> FileResponse:
    """
    Rota para baixar o arquivo de vídeo/áudio já processado.

    :param nome_arquivo: Nome do arquivo a ser baixado.
    :return: FileResponse para download do arquivo.
    """
    
    # Caminho completo até o arquivo no PC (pasta de downloads)
    caminho = os.path.join(DOWNLOAD_DIR, nome_arquivo)

    # Verifica se o arquivo existe
    if not os.path.exists(caminho):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    
    # Agendar a exclusão do arquivo temporário após iniciar o download.
    if not hasattr(app.state, "background_tasks"):
        app.state.background_tasks = [] 

    # Agendar a tarefa de exclusão do arquivo após 10 segundos.
    task = asyncio.create_task(apagar_arquivo_temporario(caminho, delay=10)) 
    
    # Adiciono a tarefa à lista de tarefas em segundo plano do aplicativo.
    app.state.background_tasks.append(task) 

    # Retornará o arquivo concluído para download no PC.
    return FileResponse(caminho, filename=nome_arquivo)


# DELETAR O ARQUIVO ORIGINAL(TEMPORÁRIO) APÓS INICIAR O DOWNLOAD
#__________________________________________________________________
async def apagar_arquivo_temporario(caminho: str, delay: int = 10) -> None:
    """
    Apagar o arquivo temporário após um atraso especificado para começar o download.

    :param caminho: Caminho completo do arquivo a ser apagado na pasta de temporários.
    :param delay: Tempo(10 por padrão) em segundos para aguardar antes de apagar o arquivo.
    """
    await asyncio.sleep(delay)
    if os.path.exists(caminho):
        os.remove(caminho)
        print(f"[INFO]: Arquivo temporário removido: {caminho}")
