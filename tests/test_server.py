from __future__ import annotations

import socket
import threading

from cacao_accounting_desktop.server import ServerConfig, WaitressServerController


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class FakeServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._stop_event = threading.Event()

    def run(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            server_socket.settimeout(0.1)
            while not self._stop_event.is_set():
                try:
                    connection, _ = server_socket.accept()
                except socket.timeout:
                    continue
                with connection:
                    connection.sendall(b"ok")

    def close(self) -> None:
        self._stop_event.set()
        try:
            with socket.create_connection((self.host, self.port), timeout=0.2):
                pass
        except OSError:
            pass


def test_waitress_server_controller_starts_and_stops() -> None:
    port = _free_port()
    config = ServerConfig(port=port, readiness_timeout=2.0)
    captured = {}

    def fake_app_factory(settings):
        captured["settings"] = settings
        return settings

    def fake_server_factory(app):
        captured["app"] = app
        return FakeServer(config.host, config.port)

    controller = WaitressServerController(config=config, app_factory=fake_app_factory, server_factory=fake_server_factory)

    url = controller.start(database_uri="sqlite:///tmp/demo.db", secret_key="secret")

    assert url == config.base_url
    assert controller.is_running
    assert captured["settings"]["SQLALCHEMY_DATABASE_URI"] == "sqlite:///tmp/demo.db"

    controller.stop()

    assert not controller.is_running


def test_waitress_server_controller_reuses_running_instance() -> None:
    port = _free_port()
    config = ServerConfig(port=port, readiness_timeout=2.0)
    calls = {"server_factory": 0}

    def fake_server_factory(app):
        calls["server_factory"] += 1
        return FakeServer(config.host, config.port)

    controller = WaitressServerController(
        config=config,
        app_factory=lambda settings: settings,
        server_factory=fake_server_factory,
    )

    controller.start(database_uri="sqlite:///tmp/one.db", secret_key="secret")
    controller.start(database_uri="sqlite:///tmp/two.db", secret_key="secret")
    controller.stop()

    assert calls["server_factory"] == 1