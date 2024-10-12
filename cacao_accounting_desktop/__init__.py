# Copyright 2024 William José Moreno Reyes
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Cacao Accounting como aplicación de escritorio."""

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
import customtkinter
from appdirs import AppDirs
from cacao_accounting import create_app
from customtkinter import filedialog
from CTkMessagebox import CTkMessagebox
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


# ---------------------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------------------
def get_database_file_list():
    """Return database files as a list."""
    FILE_LIST = os.listdir(APP_DATA_DIR)
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
    if Path.exists(SECURE_KEY_FILE) and os.access(SECURE_KEY_FILE, os.R_OK):
        with open(SECURE_KEY_FILE) as f:
            return f.readline()
    else:
        from uuid import uuid4
        from ulid import ULID

        UUID = uuid4()  # https://docs.python.org/3/library/uuid.html
        ULID = ULID()  # https://github.com/ulid/spec
        SECURE_KEY = str(ULID) + ":" + str(UUID)  # Possibly a little psycho here
        with open(SECURE_KEY_FILE, "x") as f:
            f.write(SECURE_KEY)
        return SECURE_KEY


def get_backup_path():
    """Devulve la ruta para guardar los respaldos por defecto."""
    if Path.exists(BACKUP_PATH_FILE):
        with open(BACKUP_PATH_FILE) as f:
            return Path(f.readline())
    else:
        return APP_BACKUP_DIR


# ---------------------------------------------------------------------------------------
# Interfaz grafica
# ---------------------------------------------------------------------------------------
class NewDabataseWin(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x300")

        self.label = customtkinter.CTkLabel(self, text="Crear Nueva Base de Datos:")
        self.label.grid(row=0, padx=20, pady=5)

        self.tag = customtkinter.CTkLabel(self, text="Nombre de la Nueva Base de Datos:", fg_color="transparent")
        self.tag.grid(row=1)

        self.dbname = customtkinter.CTkEntry(self, placeholder_text="dbname.db")
        self.dbname.grid(row=2)

        self.user = customtkinter.CTkLabel(self, text="Nombre de Usuario:", fg_color="transparent")
        self.user.grid(row=3)

        self.nuser = customtkinter.CTkEntry(self, placeholder_text="Usuario")
        self.nuser.grid(row=4)

        self.pwd = customtkinter.CTkLabel(self, text="Ingrese Clave de Acceso:", fg_color="transparent")
        self.pwd.grid(row=5)

        self.npswd = customtkinter.CTkEntry(self, placeholder_text="Clave de Acceso", show="*")
        self.npswd.grid(row=6)

        self.npswd2 = customtkinter.CTkEntry(self, placeholder_text="Confirmar Clave", show="*")
        self.npswd2.grid(row=7)

        self.create = customtkinter.CTkButton(
            self,
            corner_radius=20,
            height=40,
            border_spacing=10,
            text="Crear Base de Datos",
            bg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.create_db,
        )
        self.create.grid(row=8)

    def create_db(self):
        self.DATABASE_FILE = Path(os.path.join(APP_DATA_DIR, self.dbname.get()))
        self.DATABASE_URI = "sqlite:///" + str(self.DATABASE_FILE)

        if not os.path.exists(self.DATABASE_FILE):
            open(self.DATABASE_FILE, "w").close()
            self.NEW_DB_FILE = True
        else:
            self.message = CTkMessagebox(
                title="Error",
                icon="cancel",
                message="Ya existe una base de datos con ese nombre.",
            )
            self.NEW_DB_FILE = False

        if self.NEW_DB_FILE:
            self.app = create_app(
                {
                    "SECRET_KEY": get_secret_key(),
                    "SQLALCHEMY_DATABASE_URI": self.DATABASE_URI,
                }
            )

            self.new_user = self.nuser.get()
            self.new_passwd = self.npswd.get()
            self.new_passwd2 = self.npswd2.get()
            self.checkpw = self.new_passwd == self.new_passwd2

            if self.checkpw is not True:
                self.message = CTkMessagebox(
                    title="Error",
                    icon="cancel",
                    message="Las contraseñas no coinciden.",
                )

            else:
                try:
                    from cacao_accounting.database.helpers import inicia_base_de_datos

                    inicia_base_de_datos(app=self.app, user=self.new_user, passwd=self.new_passwd, with_examples=False)
                    self.message = CTkMessagebox(
                        title="Confirmación",
                        icon="check",
                        message="Base de datos creada correctamente.",
                    )
                except:
                    self.message = CTkMessagebox(
                        title="Error",
                        icon="cancel",
                        message="Hubo un error al crear la base de datos.",
                    )

        self.withdraw()


class SetBackupDir(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("250x150")

        self.label = customtkinter.CTkLabel(self, text="Seleccione Carpeta de Respaldos:")
        self.label.grid(row=0, padx=20, pady=5)
        self.set_backup_dir = customtkinter.CTkButton(
            self,
            corner_radius=20,
            height=40,
            border_spacing=10,
            text="Establecer Carpeta de Respaldo.",
            bg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.backup,
        )
        self.set_backup_dir.grid(row=1, padx=20, pady=5)

    def backup(self):
        self.bk_dir = filedialog.askdirectory()
        try:
            with open(BACKUP_PATH_FILE, "x") as f:
                try:
                    f.write(self.bk_dir)
                    self.message = CTkMessagebox(
                        title="Confirmación",
                        icon="check",
                        message="Carpeta de respaldos establecida correctamente.",
                    )
                except:
                    self.message = CTkMessagebox(
                        title="Error",
                        icon="cancel",
                        message="Hubo un error al establecer la carpeta de repaldos.",
                    )
        except FileExistsError:
            self.message = CTkMessagebox(
                title="Error",
                icon="cancel",
                message="Ya ha establecido un directorio de respaldos.",
            )

        self.withdraw()


class RestoreDabataseWin(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x300")

        self.label = customtkinter.CTkLabel(self, text="Seleccione Base de Datos a Restaurar:")
        self.label.grid(row=0, padx=20, pady=5)

        self.tag = customtkinter.CTkLabel(self, text="Defina el Nombre de la Base de Datos:", fg_color="transparent")
        self.tag.grid(row=1)

        self.entry = customtkinter.CTkEntry(self, placeholder_text="Nombre")
        self.entry.grid(row=2)

        self.reminder = customtkinter.CTkLabel(
            self,
            text="Recuerde que el nombre de la base de datos debe terminar en .db",
            fg_color="transparent",
        )
        self.reminder.grid(row=3)

        self.backup = customtkinter.CTkButton(
            self,
            corner_radius=20,
            height=40,
            border_spacing=10,
            text="Restaurar Base de Datos",
            bg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.backup,
        )
        self.backup.grid(row=4)

    def backup(self):
        self.origin = filedialog.askopenfile(mode="r")
        self.dest = Path(os.path.join(get_backup_path(), self.entry.get()))
        with open(self.origin.name) as input:
            try:
                copyfile(input.name, self.dest)
                self.message = CTkMessagebox(
                    title="Confirmación",
                    icon="check",
                    message="Base de datos restaurada correctamente.",
                )
            except:
                self.message = CTkMessagebox(
                    title="Error",
                    icon="cancel",
                    message="Hubo un error al restaurar la base de datos.",
                )

        self.withdraw()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        customtkinter.set_default_color_theme("green")
        customtkinter.set_appearance_mode("system")
        self.title("Cacao Accounting Desktop")
        self.geometry("540x520")
        self.logo = customtkinter.CTkImage(
            Image.open(os.path.join(ASSETS_DIRECTORY, "CacaoAccounting.png")),
            size=(500, 150),
        )
        self.bmo = customtkinter.CTkImage(
            Image.open(os.path.join(ASSETS_DIRECTORY, "bmosoluciones.png")),
            size=(120, 40),
        )

        self.home = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent", bg_color="transparent")
        self.home.grid(row=0, column=0, sticky="nsew")
        self.home.grid_rowconfigure(4, weight=1)
        self.home_logo = customtkinter.CTkLabel(self.home, text="", image=self.logo)
        self.home_logo.grid(row=0, column=0, padx=20, pady=5)

        self.new_db_ico = customtkinter.CTkImage(
            Image.open(os.path.join(ASSETS_DIRECTORY, "plus-circle.png")),
            size=(12, 12),
        )

        self.new_db = customtkinter.CTkButton(
            self.home,
            corner_radius=20,
            height=40,
            border_spacing=10,
            text="Crear Nueva Base de Datos",
            bg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.new_database,
            image=self.new_db_ico,
        )
        self.new_db.grid(row=2, column=0, padx=10, pady=5, sticky="s")

        self.restore_db_ico = customtkinter.CTkImage(
            Image.open(os.path.join(ASSETS_DIRECTORY, "arrow-counterclockwise.png")),
            size=(12, 12),
        )

        self.restore_db = customtkinter.CTkButton(
            self.home,
            corner_radius=20,
            height=40,
            border_spacing=10,
            text="Restaurar base de datos",
            bg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.restore_database,
            image=self.restore_db_ico,
        )
        self.restore_db.grid(row=3, column=0, padx=10, pady=5, sticky="s")

        self.select_db_title = customtkinter.CTkLabel(self.home, text="Seleccionar Base de Datos:")

        self.select_db_title.grid(row=4, column=0, padx=10, pady=5, sticky="s")

        self.select_db = customtkinter.CTkOptionMenu(
            self.home,
            values=get_database_file_list(),
        )
        self.select_db.grid(row=5, column=0, padx=10, pady=5, sticky="s")

        self.select_db_note = customtkinter.CTkLabel(
            self.home,
            text="Si la base de datos no se muestra intente cerrar y volver a abrir el programa.",
        )

        self.select_db_note.grid(row=6, column=0, padx=10, pady=5, sticky="s")

        self.init_server_ico = customtkinter.CTkImage(
            Image.open(os.path.join(ASSETS_DIRECTORY, "play-fill.png")),
            size=(12, 12),
        )

        self.init_server = customtkinter.CTkButton(
            self.home,
            corner_radius=20,
            height=40,
            border_spacing=10,
            text="Iniciar Cacao Accounting",
            bg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.run_wsgi_server,
            image=self.init_server_ico,
        )
        self.init_server.grid(row=7, column=0, padx=10, pady=5, sticky="s")

        self.backup_dir_ico = customtkinter.CTkImage(
            Image.open(os.path.join(ASSETS_DIRECTORY, "sliders.png")),
            size=(12, 12),
        )

        self.backup_dir = customtkinter.CTkButton(
            self.home,
            corner_radius=20,
            height=40,
            border_spacing=10,
            text="Configurar Carpeta de Respaldo",
            bg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            command=self.configurar_respaldo,
            image=self.backup_dir_ico,
        )
        self.backup_dir.grid(row=8, column=0, padx=10, pady=5, sticky="s")

        self.home_bmo_logo = customtkinter.CTkLabel(self.home, text="", image=self.bmo)
        self.home_bmo_logo.grid(row=9, column=0, padx=20, pady=5)

        self.toplevel_window = None

    def create_sqlite_url(self):
        self.DATABASE_FILE = Path(os.path.join(APP_DATA_DIR, self.select_db.get()))
        self.DATABASE_URI = "sqlite:///" + str(self.DATABASE_FILE)

        return self.DATABASE_URI

    def configurar_respaldo(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = SetBackupDir(self)
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()

    def run_wsgi_server(self):
        self.DB_FILE = Path(os.path.join(APP_DATA_DIR, self.select_db.get()))
        self.DB_BACKUP = Path(
            os.path.join(
                get_backup_path(),
                str(datetime.today().strftime("%Y-%m-%d")) + "-cacao_accounting_backup-" + os.path.basename(self.DB_FILE),
            )
        )
        if not Path.exists(self.DB_BACKUP):
            copyfile(self.DB_FILE, self.DB_BACKUP)
        self.withdraw()
        self.app_server = FlaskUI(
            app=create_app(
                {
                    "SECRET_KEY": get_secret_key(),
                    "SQLALCHEMY_DATABASE_URI": self.create_sqlite_url(),
                }
            ),
            server="flask",
            port=9871,
            fullscreen=False,
            profile_dir_prefix="cacao_accounting",
            height=600,
            width=1200,
        )
        self.app_server.run()

    def new_database(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = NewDabataseWin(self)
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()

    def restore_database(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = RestoreDabataseWin(self)
            self.toplevel_window.focus()
        else:
            self.toplevel_window.focus()


# ---------------------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------------------
def init_app():
    start_app = App()
    start_app.mainloop()
