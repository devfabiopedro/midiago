import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = "69345f85-7370-832c-85ab-ee94260e500a"
    DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
    TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
    STATIC_DIR = os.path.join(BASE_DIR, "static")
