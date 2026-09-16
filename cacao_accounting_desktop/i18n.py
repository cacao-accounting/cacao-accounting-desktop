"""Translations for the PySide6 desktop wrapper."""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "es": {
        "language_dialog_title": "Idioma de la interfaz",
        "language_dialog_label": "Seleccione el idioma de la interfaz:",
        "continue": "Continuar",
        "cancel": "Cancelar",
        "accept": "Aceptar",
        "print": "Impresión",
        "print_external_page": "Solo se puede imprimir contenido servido por Cacao Accounting.",
        "no_printers": "No hay impresoras configuradas en el sistema.",
        "printer_init_error": "No fue posible inicializar la impresora seleccionada.",
        "print_title": "Imprimir comprobante",
        "print_start_error": "No fue posible iniciar la impresión: {error}",
        "print_error": "No fue posible enviar el comprobante a la impresora.",
        "create_database_title": "Crear nueva base de datos",
        "administrator": "Administrador",
        "access_key": "Clave de acceso",
        "database": "Base de datos",
        "administrator_user": "Usuario administrador",
        "key": "Clave",
        "desktop_title": "Cacao Accounting Desktop",
        "directories": "Directorios",
        "sqlite_databases": "Bases SQLite",
        "select_database_folder": "Seleccionar carpeta de bases",
        "backups": "Respaldos",
        "configure_backup_folder": "Configurar carpeta de respaldo",
        "database_folder_help": "Carpeta donde se listan y crean las bases SQLite.",
        "backup_folder_help": "Carpeta usada para respaldos y restauraciones.",
        "databases": "Bases de datos",
        "refresh_list": "Refrescar lista",
        "active_database": "Base activa",
        "actions": "Acciones",
        "create_database": "Crear nueva base",
        "restore_database": "Restaurar base",
        "backup_selected": "Respaldar base seleccionada",
        "start_accounting": "Iniciar Cacao Accounting",
        "no_databases": "No se encontraron bases de datos",
        "initial_message": "Selecciona una base de datos existente o crea una nueva desde esta ventana.",
        "select_database_folder_dialog": "Seleccione el directorio para almacenar bases SQLite",
        "select_backup_folder_dialog": "Seleccione el directorio para respaldos",
        "database_folder_updated": "Directorio de bases de datos actualizado.",
        "backup_folder_updated": "Directorio de respaldos actualizado.",
        "creation_in_progress": "Ya hay una creación de base en curso.",
        "creating_database": "Creando base de datos, por favor espera...",
        "database_creation_error": "No fue posible crear la base de datos: {error}",
        "database_created": "Base de datos creada correctamente: {database_name}",
        "select_database_file": "Seleccione la base de datos a restaurar",
        "sqlite_files": "SQLite (*.db);;Todos los archivos (*)",
        "restored_database_name": "Nombre de la base restaurada",
        "database_file_name": "Nombre del archivo .db",
        "database_restored": "Base de datos restaurada correctamente.",
        "select_database_first": "Selecciona primero una base de datos.",
        "backup_created": "Respaldo generado en: {backup_path}",
        "select_database_to_start": "Selecciona una base de datos antes de iniciar la aplicación.",
        "server_start_error": "No fue posible iniciar el servidor: {error}",
        "server_started": "Servidor local iniciado correctamente.",
    },
    "en": {
        "language_dialog_title": "Interface language",
        "language_dialog_label": "Select the interface language:",
        "continue": "Continue",
        "cancel": "Cancel",
        "accept": "OK",
        "print": "Printing",
        "print_external_page": "Only content served by Cacao Accounting can be printed.",
        "no_printers": "There are no printers configured on the system.",
        "printer_init_error": "The selected printer could not be initialized.",
        "print_title": "Print voucher",
        "print_start_error": "Printing could not be started: {error}",
        "print_error": "The voucher could not be sent to the printer.",
        "create_database_title": "Create new database",
        "administrator": "Administrator",
        "access_key": "Access password",
        "database": "Database",
        "administrator_user": "Administrator user",
        "key": "Password",
        "desktop_title": "Cacao Accounting Desktop",
        "directories": "Directories",
        "sqlite_databases": "SQLite databases",
        "select_database_folder": "Select database folder",
        "backups": "Backups",
        "configure_backup_folder": "Configure backup folder",
        "database_folder_help": "Folder where SQLite databases are listed and created.",
        "backup_folder_help": "Folder used for backups and restores.",
        "databases": "Databases",
        "refresh_list": "Refresh list",
        "active_database": "Active database",
        "actions": "Actions",
        "create_database": "Create new database",
        "restore_database": "Restore database",
        "backup_selected": "Back up selected database",
        "start_accounting": "Start Cacao Accounting",
        "no_databases": "No databases found",
        "initial_message": "Select an existing database or create a new one from this window.",
        "select_database_folder_dialog": "Select the folder for SQLite databases",
        "select_backup_folder_dialog": "Select the folder for backups",
        "database_folder_updated": "Database folder updated.",
        "backup_folder_updated": "Backup folder updated.",
        "creation_in_progress": "A database creation is already in progress.",
        "creating_database": "Creating database, please wait...",
        "database_creation_error": "The database could not be created: {error}",
        "database_created": "Database created successfully: {database_name}",
        "select_database_file": "Select the database to restore",
        "sqlite_files": "SQLite (*.db);;All files (*)",
        "restored_database_name": "Restored database name",
        "database_file_name": ".db file name",
        "database_restored": "Database restored successfully.",
        "select_database_first": "Select a database first.",
        "backup_created": "Backup created at: {backup_path}",
        "select_database_to_start": "Select a database before starting the application.",
        "server_start_error": "The server could not be started: {error}",
        "server_started": "Local server started successfully.",
    },
}

ERROR_TRANSLATIONS = {
    "en": {
        "El idioma seleccionado no está disponible.": "The selected language is not available.",
        "Debe indicar un nombre para la base de datos.": "Enter a database name.",
        "El nombre de la base de datos no puede incluir directorios.": "The database name cannot include directories.",
        "El nombre de la base de datos debe terminar en .db.": "The database name must end with .db.",
        "Debe indicar un usuario administrador.": "Enter an administrator user.",
        "Debe indicar una clave de administrador.": "Enter an administrator password.",
        "La base de datos indicada ya existe.": "The selected database already exists.",
        "La base de datos seleccionada no existe.": "The selected database does not exist.",
        "El archivo indicado para restaurar no existe.": "The file selected for restore does not exist.",
        "La base de datos de destino ya existe.": "The destination database already exists.",
        "No fue posible importar cacao-accounting. Instala las dependencias actualizadas.": (
            "Cacao Accounting could not be imported. Install the updated dependencies."
        ),
        "La versión instalada de cacao-accounting no permite configurar el idioma.": (
            "The installed version of cacao-accounting does not support language configuration."
        ),
        "No fue posible importar waitress.": "Waitress could not be imported.",
    }
}


def text(language: str, key: str, **values: object) -> str:
    """Return a translated wrapper string."""
    language_translations = TRANSLATIONS.get(language, TRANSLATIONS["es"])
    translated = language_translations.get(key, TRANSLATIONS["es"].get(key, key))
    return translated.format(**values) if values else translated


def localize_error(language: str, message: str) -> str:
    """Translate known errors raised by the desktop wrapper."""
    if language == "es":
        return message

    translated = ERROR_TRANSLATIONS.get(language, {}).get(message)
    if translated:
        return translated

    prefixes = {
        "No fue posible crear la base de datos: ": "The database could not be created: ",
        "No fue posible iniciar el servidor: ": "The server could not be started: ",
        "El servidor no estuvo disponible a tiempo: ": "The server was not available in time: ",
        "Idioma no soportado: ": "Unsupported language: ",
    }
    for source, target in prefixes.items():
        if message.startswith(source):
            return target + message[len(source) :]  # noqa: E203
    return message
