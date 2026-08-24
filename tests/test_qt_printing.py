from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog, QWidget  # noqa: E402

from cacao_accounting_desktop import qt_app  # noqa: E402


class FakeSignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback


class FakePage:
    def __init__(self, _parent=None):
        self.printRequested = FakeSignal()


class FakeWebView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.printFinished = FakeSignal()
        self._page = FakePage()
        self._url = QUrl()
        self.print_calls = []

    def setPage(self, page) -> None:
        self._page = page

    def page(self):
        return self._page

    def setUrl(self, url: QUrl) -> None:
        self._url = url

    def url(self) -> QUrl:
        return self._url

    def title(self) -> str:
        return "Comprobante 42"

    def print(self, printer) -> None:
        self.print_calls.append(printer)


class FakePrinter:
    class PrinterMode:
        HighResolution = object()

    class OutputFormat:
        NativeFormat = object()

    def __init__(self, mode):
        self.mode = mode
        self.output_format = None
        self.document_name = None

    def setOutputFormat(self, output_format) -> None:
        self.output_format = output_format

    def setDocName(self, document_name: str) -> None:
        self.document_name = document_name

    def isValid(self) -> bool:
        return True


class FakePrinterInfo:
    printers = [object()]

    @classmethod
    def availablePrinters(cls):
        return cls.printers


class FakePrintDialog:
    result = QDialog.DialogCode.Accepted

    def __init__(self, printer, parent):
        self.printer = printer
        self.parent = parent
        self.title = ""

    def setWindowTitle(self, title: str) -> None:
        self.title = title

    def exec(self):
        return self.result


class FakeMessageBox:
    warnings = []
    critical_errors = []

    @classmethod
    def warning(cls, _parent, title: str, message: str) -> None:
        cls.warnings.append((title, message))

    @classmethod
    def critical(cls, _parent, title: str, message: str) -> None:
        cls.critical_errors.append((title, message))


@pytest.fixture(scope="module", autouse=True)
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def browser_window(monkeypatch):
    FakePrintDialog.result = QDialog.DialogCode.Accepted
    FakePrinterInfo.printers = [object()]
    FakeMessageBox.warnings = []
    FakeMessageBox.critical_errors = []
    monkeypatch.setattr(qt_app, "QWebEngineView", FakeWebView)
    monkeypatch.setattr(qt_app, "BrowserPage", FakePage)
    monkeypatch.setattr(qt_app, "QPrinter", FakePrinter)
    monkeypatch.setattr(qt_app, "QPrinterInfo", FakePrinterInfo)
    monkeypatch.setattr(qt_app, "QPrintDialog", FakePrintDialog)
    monkeypatch.setattr(qt_app, "QMessageBox", FakeMessageBox)
    window = qt_app.BrowserWindow()
    window.open_url("http://127.0.0.1:9871/printing/preview/42")
    return window


def test_url_origin_normalizes_default_ports() -> None:
    assert qt_app._url_origin(QUrl("http://example.test/path")) == ("http", "example.test", 80)
    assert qt_app._url_origin(QUrl("https://EXAMPLE.test/path")) == ("https", "example.test", 443)


def test_native_print_keeps_printer_until_async_completion(browser_window) -> None:
    browser_window._print_current_page()

    assert len(browser_window.web_view.print_calls) == 1
    assert browser_window._printing_in_progress
    assert browser_window._active_printer is browser_window.web_view.print_calls[0]
    assert browser_window._active_printer.document_name == "Comprobante 42"
    assert browser_window._active_printer.output_format is FakePrinter.OutputFormat.NativeFormat

    browser_window._print_current_page()
    assert len(browser_window.web_view.print_calls) == 1

    browser_window._print_finished(True)
    assert not browser_window._printing_in_progress
    assert browser_window._active_printer is None


def test_cancelled_dialog_does_not_print(browser_window) -> None:
    FakePrintDialog.result = QDialog.DialogCode.Rejected

    browser_window._print_current_page()

    assert browser_window.web_view.print_calls == []
    assert not browser_window._printing_in_progress


def test_external_page_cannot_request_printing(browser_window) -> None:
    browser_window.web_view.setUrl(QUrl("https://example.test/document"))

    browser_window._print_current_page()

    assert browser_window.web_view.print_calls == []
    assert FakeMessageBox.warnings == [("Impresión", "Solo se puede imprimir contenido servido por Cacao Accounting.")]


def test_missing_printer_and_failed_job_show_messages(browser_window) -> None:
    FakePrinterInfo.printers = []
    browser_window._print_current_page()
    assert FakeMessageBox.warnings == [("Impresión", "No hay impresoras configuradas en el sistema.")]

    browser_window._printing_in_progress = True
    browser_window._active_printer = FakePrinter(FakePrinter.PrinterMode.HighResolution)
    browser_window._print_finished(False)

    assert FakeMessageBox.critical_errors == [("Impresión", "No fue posible enviar el comprobante a la impresora.")]
