# ---------------------------------------------------------------------------------------
# Libreria estandar
# ---------------------------------------------------------------------------------------
import os
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------------------
# Librerias de terceros
# ---------------------------------------------------------------------------------------
from appdirs import AppDirs
from cacao_accounting import create_app
from flaskwebgui import FlaskUI
from PIL import Image
import wx

if TYPE_CHECKING:
    from flask import Flask


# ---------------------------------------------------------------------------------------
# Principales constantes
# ---------------------------------------------------------------------------------------
APP_DIRS: AppDirs = AppDirs("Cacao Accounting Desktop", "BMO Soluciones")
APP_CONFIG_DIR = Path(os.path.join(APP_DIRS.user_config_dir))
APP_DATA_DIR = Path(os.path.join(APP_DIRS.user_data_dir))
APP_HOME_DIR = os.path.expanduser("~/Cacao Accounting")
APP_BACKUP_DIR = Path(os.path.join(APP_HOME_DIR, "Backups"))
SECURE_KEY_FILE = Path(os.path.join(APP_CONFIG_DIR, "secret.key"))
BACKUP_PATH_FILE = Path(os.path.join(APP_CONFIG_DIR, "backup.path"))


# ---------------------------------------------------------------------------------------
# Asegura que los directorios utilizados por la aplicación existen
# ---------------------------------------------------------------------------------------
APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
APP_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
FILE_LIST = os.listdir(APP_DATA_DIR)


def get_database_file_list():
    DB_FILES = []
    for file in FILE_LIST:
        if file.endswith(".db"):
            DB_FILES.append(file)
    if len(DB_FILES) == 0:
        DB_FILES.append("No se encontraron bases de datos.")
    return DB_FILES


def get_secret_key():
    """
    Populate the SECRET_KEY config.

    Is SECURE_KEY_FILE exist will read the content of the file a return it,
    if not will generate a ramond string a save the value for future use.
    """
    if Path.exists(SECURE_KEY_FILE):
        with open(SECURE_KEY_FILE) as f:
            return f.readline()
    else:
        from uuid import uuid4

        UUID = uuid4()
        SECURE_KEY = str(UUID)
        with open(SECURE_KEY_FILE, "x") as f:
            f.write(SECURE_KEY)
        return SECURE_KEY


def get_backup_path():
    if Path.exists(BACKUP_PATH_FILE):
        with open(BACKUP_PATH_FILE) as f:
            return Path(f.readline())
    else:
        return APP_BACKUP_DIR


class HelloFrame(wx.Frame):

    def __init__(self, *args, **kw):
        super(HelloFrame, self).__init__(*args, **kw)

        panel = wx.Panel(self)

        st = wx.StaticText(panel, label="Cacao Accounting Desktop")
        font = st.GetFont()
        font.PointSize += 10
        font = font.Bold()
        st.SetFont(font)


def init_app():
    app = wx.App()
    frm = HelloFrame(None, title="Cacao Accounting")
    frm.Show()
    app.MainLoop()
