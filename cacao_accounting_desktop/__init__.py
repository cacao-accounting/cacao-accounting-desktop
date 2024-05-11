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
APP_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIRECTORY = os.path.join(APP_DIRECTORY, "assets")


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


from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label


class MyApp(App):

    Window.size = (300, 400)
    title = "Cacao Accounting Desktop"

    def build(self):
        window = GridLayout()
        window.cols = 1

        window.add_widget(Image(source=str(os.path.join(ASSETS_DIRECTORY, "CacaoAccounting.png"))))

        new_db_button = Button(text="Crear una nueva base de datos")
        window.add_widget(new_db_button)

        box = BoxLayout(orientation="vertical")

        db_select = DropDown()
        for file in get_database_file_list():
            label = Button(text=file, size_hint_y=None, height=30)
            db_select.add_widget(label)

        select_db_button = Button(text="Seleccionar base de datos")
        select_db_button.add_widget(db_select)
        select_db_button.bind(on_press=db_select.open)

        box.add_widget(select_db_button)

        window.add_widget(box)

        init_server = Button(text="Iniciar Cacao Accounting")
        window.add_widget(init_server)

        db_restore = Button(text="Restaurar respaldo")
        window.add_widget(db_restore)

        set_restore_path = Button(text="Configurar carpeta de respaldo")
        window.add_widget(set_restore_path)

        return window


def init_app():
    MyApp().run()
