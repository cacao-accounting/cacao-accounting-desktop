from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from cacao_accounting_desktop.core import (
    DesktopPaths,
    ValidationError,
    build_database_path,
    build_sqlite_uri,
    create_backup,
    create_database,
    ensure_directories,
    get_database_directory,
    list_database_files,
    restore_database,
    set_database_directory,
)


def make_paths(tmp_path: Path) -> DesktopPaths:
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    backup_dir = tmp_path / "backups"
    return DesktopPaths(
        config_dir=config_dir,
        default_data_dir=data_dir,
        default_backup_dir=backup_dir,
        secret_key_file=config_dir / "secret.key",
        backup_path_file=config_dir / "backup.path",
        database_path_file=config_dir / "database.path",
    )


def test_database_directory_can_be_overridden(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    ensure_directories(paths)

    custom_directory = tmp_path / "custom-dbs"
    set_database_directory(custom_directory, paths)

    assert get_database_directory(paths) == custom_directory.resolve()
    assert custom_directory.exists()


def test_list_database_files_reads_selected_directory(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    selected_directory = tmp_path / "selected-dbs"
    set_database_directory(selected_directory, paths)

    (selected_directory / "zeta.db").write_text("", encoding="utf-8")
    (selected_directory / "alfa.db").write_text("", encoding="utf-8")
    (selected_directory / "ignore.txt").write_text("", encoding="utf-8")

    assert list_database_files(paths) == ["alfa.db", "zeta.db"]


def test_sqlite_uri_uses_selected_database_directory(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    set_database_directory(tmp_path / "db-root", paths)

    sqlite_uri = build_sqlite_uri("empresa.db", paths)

    assert sqlite_uri.startswith("sqlite:///")
    assert sqlite_uri.endswith("empresa.db")


def test_backup_and_restore_copy_sqlite_files(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    ensure_directories(paths)
    original_database = build_database_path("empresa.db", paths)
    original_database.write_text("sqlite-content", encoding="utf-8")

    backup_path = create_backup("empresa.db", paths=paths, timestamp=datetime(2026, 4, 24, 12, 0, 0))
    restored_database = restore_database(backup_path, "restaurada.db", paths=paths)

    assert backup_path.exists()
    assert backup_path.name == "2026-04-24-cacao_accounting_backup-empresa.db"
    assert restored_database.read_text(encoding="utf-8") == "sqlite-content"


def test_create_database_uses_injected_dependencies(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    calls = {}

    def fake_app_factory(settings):
        calls["settings"] = settings
        return object()

    def fake_initializer(app, user, passwd):
        calls["initializer"] = {"app": app, "user": user, "passwd": passwd}

    database_path = create_database(
        "nueva.db",
        "admin",
        "secret",
        paths=paths,
        app_factory=fake_app_factory,
        initializer=fake_initializer,
    )

    assert database_path == build_database_path("nueva.db", paths)
    assert calls["settings"]["SQLALCHEMY_DATABASE_URI"].endswith("nueva.db")
    assert calls["initializer"]["user"] == "admin"


def test_restore_database_rejects_existing_target(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    ensure_directories(paths)
    source_file = tmp_path / "source.db"
    source_file.write_text("payload", encoding="utf-8")
    build_database_path("source.db", paths).write_text("current", encoding="utf-8")

    with pytest.raises(ValidationError):
        restore_database(source_file, "source.db", paths=paths)