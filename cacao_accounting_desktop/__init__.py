"""Cacao Accounting Desktop package."""


def init_app() -> int:
    from .qt_app import init_app as run_qt_app

    return run_qt_app()


__all__ = ["init_app"]
