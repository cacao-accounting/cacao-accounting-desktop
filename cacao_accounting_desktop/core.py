from __future__ import annotations

import os
import inspect
from importlib import import_module
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile
from uuid import uuid4

from appdirs import AppDirs

APP_DIRS = AppDirs("Cacao Accounting Desktop", "BMO Soluciones")
APP_HOME_DIR = Path(os.path.expanduser("~/Cacao Accounting"))


@dataclass(frozen=True)
class DesktopPaths:
    config_dir: Path
    default_data_dir: Path
    default_backup_dir: Path
    secret_key_file: Path
    backup_path_file: Path
    database_path_file: Path


DEFAULT_PATHS = DesktopPaths(
    config_dir=Path(APP_DIRS.user_config_dir),
    default_data_dir=Path(APP_DIRS.user_data_dir),
    default_backup_dir=APP_HOME_DIR / "Backups",
    secret_key_file=Path(APP_DIRS.user_config_dir) / "secret.key",
    backup_path_file=Path(APP_DIRS.user_config_dir) / "backup.path",
    database_path_file=Path(APP_DIRS.user_config_dir) / "database.path",
)


class DesktopError(Exception):
    """Base exception for desktop wrapper errors."""


class ValidationError(DesktopError):
    """Raised when user input cannot be processed."""


class ExternalDependencyError(DesktopError):
    """Raised when runtime dependencies are missing."""


def ensure_directories(paths: DesktopPaths = DEFAULT_PATHS) -> None:
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    paths.default_data_dir.mkdir(parents=True, exist_ok=True)
    paths.default_backup_dir.mkdir(parents=True, exist_ok=True)
    get_database_directory(paths).mkdir(parents=True, exist_ok=True)
    get_backup_directory(paths).mkdir(parents=True, exist_ok=True)


def _read_configured_directory(config_file: Path, fallback: Path) -> Path:
    if not config_file.exists():
        return fallback.resolve()

    raw_value = config_file.read_text(encoding="utf-8").strip()
    if not raw_value:
        return fallback.resolve()

    return Path(raw_value).expanduser().resolve()


def _write_configured_directory(config_file: Path, directory: Path) -> Path:
    resolved_directory = directory.expanduser().resolve()
    resolved_directory.mkdir(parents=True, exist_ok=True)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(str(resolved_directory), encoding="utf-8")
    return resolved_directory


def get_database_directory(paths: DesktopPaths = DEFAULT_PATHS) -> Path:
    return _read_configured_directory(paths.database_path_file, paths.default_data_dir)


def set_database_directory(directory: str | Path, paths: DesktopPaths = DEFAULT_PATHS) -> Path:
    return _write_configured_directory(paths.database_path_file, Path(directory))


def get_backup_directory(paths: DesktopPaths = DEFAULT_PATHS) -> Path:
    return _read_configured_directory(paths.backup_path_file, paths.default_backup_dir)


def set_backup_directory(directory: str | Path, paths: DesktopPaths = DEFAULT_PATHS) -> Path:
    return _write_configured_directory(paths.backup_path_file, Path(directory))


def list_database_files(paths: DesktopPaths = DEFAULT_PATHS) -> list[str]:
    ensure_directories(paths)
    database_directory = get_database_directory(paths)
    return sorted(file.name for file in database_directory.iterdir() if file.is_file() and file.suffix == ".db")


def validate_database_name(file_name: str) -> str:
    normalized_name = file_name.strip()
    if not normalized_name:
        raise ValidationError("Debe indicar un nombre para la base de datos.")
    if Path(normalized_name).name != normalized_name:
        raise ValidationError("El nombre de la base de datos no puede incluir directorios.")
    if not normalized_name.endswith(".db"):
        raise ValidationError("El nombre de la base de datos debe terminar en .db.")
    return normalized_name


def build_database_path(file_name: str, paths: DesktopPaths = DEFAULT_PATHS) -> Path:
    ensure_directories(paths)
    valid_name = validate_database_name(file_name)
    return get_database_directory(paths) / valid_name


def build_sqlite_uri(file_name: str, paths: DesktopPaths = DEFAULT_PATHS) -> str:
    return f"sqlite:///{build_database_path(file_name, paths).resolve().as_posix()}"


def get_secret_key(paths: DesktopPaths = DEFAULT_PATHS) -> str:
    ensure_directories(paths)
    if paths.secret_key_file.exists():
        current_key = paths.secret_key_file.read_text(encoding="utf-8").strip()
        if current_key:
            return current_key

    secret_key = str(uuid4())
    paths.secret_key_file.write_text(secret_key, encoding="utf-8")
    return secret_key


def create_database(
    file_name: str,
    admin_user: str,
    admin_password: str,
    paths: DesktopPaths = DEFAULT_PATHS,
    app_factory=None,
    initializer=None,
) -> Path:
    valid_name = validate_database_name(file_name)
    trimmed_user = admin_user.strip()
    if not trimmed_user:
        raise ValidationError("Debe indicar un usuario administrador.")
    if not admin_password:
        raise ValidationError("Debe indicar una clave de administrador.")

    database_path = build_database_path(valid_name, paths)
    if database_path.exists():
        raise ValidationError("La base de datos indicada ya existe.")

    active_app_factory = app_factory
    active_initializer = initializer

    try:
        if active_app_factory is None:
            active_app_factory = import_module("cacao_accounting").create_app
        if active_initializer is None:
            active_initializer = import_module("cacao_accounting.database.helpers").inicia_base_de_datos
    except ImportError as error:
        raise ExternalDependencyError(
            "No fue posible importar cacao-accounting. Instala las dependencias actualizadas."
        ) from error

    app = active_app_factory(
        {
            "SECRET_KEY": get_secret_key(paths),
            "SQLALCHEMY_DATABASE_URI": build_sqlite_uri(valid_name, paths),
        }
    )

    initializer_kwargs = {
        "app": app,
        "user": trimmed_user,
        "passwd": admin_password,
    }
    if "with_examples" in inspect.signature(active_initializer).parameters:
        initializer_kwargs["with_examples"] = False

    try:
        if hasattr(app, "app_context"):
            with app.app_context():
                active_initializer(**initializer_kwargs)
                _cleanup_sqlalchemy_extension(app)
        else:
            active_initializer(**initializer_kwargs)
    except Exception as error:
        raise DesktopError(f"No fue posible crear la base de datos: {error}") from error

    return database_path


def _cleanup_sqlalchemy_extension(app) -> None:
    sqlalchemy_extension = getattr(app, "extensions", {}).get("sqlalchemy")
    if sqlalchemy_extension is None:
        return

    if hasattr(sqlalchemy_extension, "session"):
        sqlalchemy_extension.session.remove()

    if hasattr(sqlalchemy_extension, "engines"):
        for engine in sqlalchemy_extension.engines.values():
            engine.dispose()


def create_backup(
    file_name: str,
    paths: DesktopPaths = DEFAULT_PATHS,
    backup_directory: str | Path | None = None,
    timestamp: datetime | None = None,
) -> Path:
    database_path = build_database_path(file_name, paths)
    if not database_path.exists():
        raise ValidationError("La base de datos seleccionada no existe.")

    effective_backup_directory = (
        Path(backup_directory).expanduser().resolve() if backup_directory else get_backup_directory(paths)
    )
    effective_backup_directory.mkdir(parents=True, exist_ok=True)

    snapshot_time = timestamp or datetime.now(timezone.utc).astimezone()
    backup_name = f"{snapshot_time:%Y-%m-%d}-cacao_accounting_backup-{database_path.name}"
    backup_path = effective_backup_directory / backup_name

    if not backup_path.exists():
        copyfile(database_path, backup_path)

    return backup_path


def restore_database(
    source_file: str | Path,
    target_name: str | None = None,
    paths: DesktopPaths = DEFAULT_PATHS,
    overwrite: bool = False,
) -> Path:
    source_path = Path(source_file).expanduser().resolve()
    if not source_path.exists() or not source_path.is_file():
        raise ValidationError("El archivo indicado para restaurar no existe.")

    destination_name = validate_database_name(target_name or source_path.name)
    destination_path = build_database_path(destination_name, paths)
    if destination_path.exists() and not overwrite:
        raise ValidationError("La base de datos de destino ya existe.")

    copyfile(source_path, destination_path)
    return destination_path
