from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass
from importlib import import_module
from typing import Protocol

from .core import ExternalDependencyError


class ServerLike(Protocol):
    def run(self) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 9871
    threads: int = 4
    readiness_timeout: float = 10.0

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class WaitressServerController:
    def __init__(self, config: ServerConfig | None = None, app_factory=None, server_factory=None):
        self.config = config or ServerConfig()
        self._app_factory = app_factory
        self._server_factory = server_factory
        self._server: ServerLike | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, database_uri: str, secret_key: str) -> str:
        with self._lock:
            if self.is_running:
                return self.config.base_url

            app_factory = self._app_factory or self._import_app_factory()
            server_factory = self._server_factory or self._import_server_factory()
            app = app_factory(
                {
                    "SECRET_KEY": secret_key,
                    "SQLALCHEMY_DATABASE_URI": database_uri,
                }
            )
            server = server_factory(app)
            self._server = server
            self._thread = threading.Thread(target=server.run, name="cacao-accounting-wsgi", daemon=True)
            self._thread.start()

        self.wait_until_ready()
        return self.config.base_url

    def stop(self, timeout: float = 5.0) -> None:
        with self._lock:
            server = self._server
            thread = self._thread
            self._server = None
            self._thread = None

        if server is not None and hasattr(server, "close"):
            server.close()

        if thread is not None:
            thread.join(timeout=timeout)

    def wait_until_ready(self) -> None:
        deadline = time.monotonic() + self.config.readiness_timeout
        last_error = None

        while time.monotonic() < deadline:
            try:
                with socket.create_connection((self.config.host, self.config.port), timeout=0.5):
                    return
            except OSError as error:
                last_error = error
                if self._thread is not None and not self._thread.is_alive():
                    break
                time.sleep(0.1)

        raise RuntimeError(f"El servidor no estuvo disponible a tiempo: {last_error}")

    def _import_app_factory(self):
        try:
            return import_module("cacao_accounting").create_app
        except ImportError as error:
            raise ExternalDependencyError(
                "No fue posible importar cacao-accounting. Instala las dependencias actualizadas."
            ) from error

    def _import_server_factory(self):
        try:
            create_server = import_module("waitress.server").create_server
        except ImportError as error:
            raise ExternalDependencyError("No fue posible importar waitress.") from error

        def factory(app):
            return create_server(
                app,
                host=self.config.host,
                port=self.config.port,
                threads=self.config.threads,
            )

        return factory
