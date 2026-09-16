from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QCloseEvent, QIcon, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter, QPrinterInfo
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .core import (
    DEFAULT_PATHS,
    DesktopError,
    build_sqlite_uri,
    create_backup,
    create_database,
    ensure_directories,
    get_backup_directory,
    get_database_directory,
    get_language,
    get_secret_key,
    list_database_files,
    restore_database,
    set_language,
    set_backup_directory,
    set_database_directory,
)
from .i18n import localize_error, text
from .server import WaitressServerController

APP_DIRECTORY = Path(__file__).resolve().parent
ASSETS_DIRECTORY = APP_DIRECTORY / "assets"


def _url_origin(url: QUrl) -> tuple[str, str, int]:
    scheme = url.scheme().lower()
    port = url.port()
    if port < 0:
        port = {"http": 80, "https": 443}.get(scheme, -1)
    return scheme, url.host().lower(), port


class CreateDatabaseWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, file_name: str, admin_user: str, admin_password: str, language: str = "es"):
        super().__init__()
        self.file_name = file_name
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.language = language

    @Slot()
    def run(self) -> None:
        try:
            created_path = create_database(
                self.file_name,
                self.admin_user,
                self.admin_password,
                paths=DEFAULT_PATHS,
            )
        except DesktopError as error:
            self.failed.emit(str(error))
            return
        except Exception as error:
            self.failed.emit(text(self.language, "database_creation_error", error=error))
            return

        self.finished.emit(created_path.name)


class BrowserPage(QWebEnginePage):
    """Keep web links opened with target=_blank inside the desktop window."""

    def createWindow(self, _window_type):  # noqa: N802 - Qt override
        return self


class BrowserWindow(QMainWindow):
    def __init__(self, language: str = "es"):
        super().__init__()
        self.language = language
        self.setWindowTitle("Cacao Accounting")
        self.resize(1200, 800)
        self.setWindowIcon(_load_icon("icon.ico"))

        self.web_view = QWebEngineView(self)
        self.web_view.setPage(BrowserPage(self.web_view))
        self.web_view.page().printRequested.connect(self._print_current_page)
        self.web_view.printFinished.connect(self._print_finished)
        self._trusted_origin: tuple[str, str, int] | None = None
        self._active_printer: QPrinter | None = None
        self._printing_in_progress = False
        self.setCentralWidget(self.web_view)

    def open_url(self, url: str) -> None:
        target_url = QUrl(url)
        self._trusted_origin = _url_origin(target_url)
        self.web_view.setUrl(target_url)
        self.show()
        self.raise_()
        self.activateWindow()

    @Slot()
    def _print_current_page(self) -> None:
        """Open the system print dialog and print the current web page."""
        if self._printing_in_progress:
            return

        if self._trusted_origin is None or _url_origin(self.web_view.url()) != self._trusted_origin:
            QMessageBox.warning(self, self._text("print"), self._text("print_external_page"))
            return

        if not QPrinterInfo.availablePrinters():
            QMessageBox.warning(self, self._text("print"), self._text("no_printers"))
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.NativeFormat)
        printer.setDocName(self.web_view.title().strip() or "Cacao Accounting")
        if not printer.isValid():
            QMessageBox.critical(self, self._text("print"), self._text("printer_init_error"))
            return

        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle(self._text("print_title"))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._active_printer = printer
        self._printing_in_progress = True
        try:
            self.web_view.print(printer)
        except RuntimeError as error:
            self._active_printer = None
            self._printing_in_progress = False
            QMessageBox.critical(self, self._text("print"), self._text("print_start_error", error=error))

    @Slot(bool)
    def _print_finished(self, success: bool) -> None:
        self._active_printer = None
        self._printing_in_progress = False
        if not success:
            QMessageBox.critical(self, self._text("print"), self._text("print_error"))

    def _text(self, key: str, **values: object) -> str:
        return text(self.language, key, **values)


class CreateDatabaseDialog(QDialog):
    def __init__(self, parent=None, language: str = "es"):
        super().__init__(parent)
        self.language = language
        self.setWindowTitle(self._text("create_database_title"))
        self.setModal(True)

        self.database_name = QLineEdit(self)
        self.database_name.setPlaceholderText("empresa.db")

        self.admin_user = QLineEdit(self)
        self.admin_user.setPlaceholderText(self._text("administrator"))

        self.admin_password = QLineEdit(self)
        self.admin_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_password.setPlaceholderText(self._text("access_key"))

        form_layout = QFormLayout()
        form_layout.addRow(self._text("database"), self.database_name)
        form_layout.addRow(self._text("administrator_user"), self.admin_user)
        form_layout.addRow(self._text("key"), self.admin_password)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self._text("accept"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self._text("cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(form_layout)
        root_layout.addWidget(buttons)

    def _text(self, key: str, **values: object) -> str:
        return text(self.language, key, **values)


class LanguageSelectionDialog(QDialog):
    """Ask for the wrapper language before the main window is created."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(text("es", "language_dialog_title") + " / " + text("en", "language_dialog_title"))
        self.setModal(True)

        language_label = QLabel(
            text("es", "language_dialog_label") + "\n" + text("en", "language_dialog_label"),
            self,
        )
        self.language_combo = QComboBox(self)
        self.language_combo.addItem("Español", "es")
        self.language_combo.addItem("English", "en")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok, parent=self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(
            text("es", "continue") + " / " + text("en", "continue")
        )
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(language_label)
        layout.addWidget(self.language_combo)
        layout.addWidget(buttons)

    @property
    def language(self) -> str:
        return str(self.language_combo.currentData())


class MainWindow(QMainWindow):
    def __init__(self, language: str = "es"):
        super().__init__()
        self.language = language
        ensure_directories(DEFAULT_PATHS)

        self.server_controller = WaitressServerController()
        self.browser_window = BrowserWindow(language)
        self.current_database_uri = ""
        self.create_database_thread: QThread | None = None
        self.create_database_worker: CreateDatabaseWorker | None = None

        self.setWindowTitle(self._text("desktop_title"))
        self.setMinimumSize(900, 620)
        self.setWindowIcon(_load_icon("icon.ico"))
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f1e8;
            }
            QGroupBox {
                border: 1px solid #d8cfbf;
                border-radius: 14px;
                margin-top: 12px;
                padding-top: 14px;
                background: #fffaf1;
                font-weight: 600;
                color: #3b3126;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
            }
            QPushButton {
                background: #2f6f5f;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #255a4d;
            }
            QPushButton:disabled {
                background: #9eb7af;
                color: #eff5f3;
            }
            QComboBox, QLineEdit {
                border: 1px solid #d7cfbf;
                border-radius: 10px;
                padding: 8px 10px;
                background: white;
                color: #32281f;
            }
            QLabel#directoryCaption {
                color: #7a6d5c;
                font-size: 12px;
                letter-spacing: 0.03em;
                text-transform: uppercase;
            }
            QLabel#directoryValue {
                color: #2e261e;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel#statusLabel {
                color: #4d4337;
                background: #efe7d6;
                border: 1px solid #ddd0bb;
                border-radius: 12px;
                padding: 12px 14px;
            }
            """)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_paths_group())
        layout.addWidget(self._build_database_group())
        layout.addWidget(self._build_actions_group())

        self.status_label = QLabel(self)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.refresh_database_list()
        self._show_message(
            self._text("initial_message"),
            error=False,
        )

    def _text(self, key: str, **values: object) -> str:
        return text(self.language, key, **values)

    def _build_header(self) -> QWidget:
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel(container)
        logo_label.setPixmap(_load_pixmap("CacaoAccounting.png", 420))
        logo_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        bmo_label = QLabel(container)
        bmo_label.setPixmap(_load_pixmap("bmosoluciones.png", 140))
        bmo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(logo_label, stretch=1)
        layout.addWidget(bmo_label)
        return container

    def _build_paths_group(self) -> QGroupBox:
        group = QGroupBox(self._text("directories"), self)
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(14)

        self.database_directory_value = QLabel(group)
        self.database_directory_value.setObjectName("directoryValue")
        self.database_directory_value.setWordWrap(True)
        self.database_directory_caption = QLabel(self._text("sqlite_databases"), group)
        self.database_directory_caption.setObjectName("directoryCaption")
        select_database_directory_button = QPushButton(self._text("select_database_folder"), group)
        select_database_directory_button.clicked.connect(self.choose_database_directory)

        self.backup_directory_value = QLabel(group)
        self.backup_directory_value.setObjectName("directoryValue")
        self.backup_directory_value.setWordWrap(True)
        self.backup_directory_caption = QLabel(self._text("backups"), group)
        self.backup_directory_caption.setObjectName("directoryCaption")
        select_backup_directory_button = QPushButton(self._text("configure_backup_folder"), group)
        select_backup_directory_button.clicked.connect(self.choose_backup_directory)

        database_info = self._build_directory_summary(
            self.database_directory_caption,
            self.database_directory_value,
            self._text("database_folder_help"),
        )
        backup_info = self._build_directory_summary(
            self.backup_directory_caption,
            self.backup_directory_value,
            self._text("backup_folder_help"),
        )

        layout.addWidget(database_info, 0, 0, 1, 2)
        layout.addWidget(select_database_directory_button, 0, 2)
        layout.addWidget(backup_info, 1, 0, 1, 2)
        layout.addWidget(select_backup_directory_button, 1, 2)
        return group

    def _build_directory_summary(self, caption: QLabel, value: QLabel, helper_text: str) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        helper = QLabel(helper_text, container)
        helper.setWordWrap(True)
        helper.setStyleSheet("color: #6c604f;")

        layout.addWidget(caption)
        layout.addWidget(value)
        layout.addWidget(helper)
        return container

    def _build_database_group(self) -> QGroupBox:
        group = QGroupBox(self._text("databases"), self)
        layout = QGridLayout(group)

        self.database_combo = QComboBox(group)
        self.database_combo.currentIndexChanged.connect(self.update_database_uri)

        refresh_button = QPushButton(self._text("refresh_list"), group)
        refresh_button.clicked.connect(self.refresh_database_list)

        layout.addWidget(QLabel(self._text("active_database")), 0, 0)
        layout.addWidget(self.database_combo, 0, 1)
        layout.addWidget(refresh_button, 0, 2)
        return group

    def _build_actions_group(self) -> QGroupBox:
        group = QGroupBox(self._text("actions"), self)
        layout = QGridLayout(group)

        self.create_button = QPushButton(self._text("create_database"), group)
        self.create_button.clicked.connect(self.open_create_database_dialog)

        restore_button = QPushButton(self._text("restore_database"), group)
        restore_button.clicked.connect(self.restore_database_from_file)

        self.backup_button = QPushButton(self._text("backup_selected"), group)
        self.backup_button.clicked.connect(self.backup_selected_database)

        self.start_button = QPushButton(self._text("start_accounting"), group)
        self.start_button.clicked.connect(self.start_accounting)

        layout.addWidget(self.create_button, 0, 0)
        layout.addWidget(restore_button, 0, 1)
        layout.addWidget(self.backup_button, 1, 0)
        layout.addWidget(self.start_button, 1, 1)
        return group

    def refresh_database_list(self) -> None:
        current_name = self._selected_database_name()
        databases = list_database_files(DEFAULT_PATHS)

        self._set_directory_summary(self.database_directory_value, get_database_directory(DEFAULT_PATHS))
        self._set_directory_summary(self.backup_directory_value, get_backup_directory(DEFAULT_PATHS))

        self.database_combo.blockSignals(True)
        self.database_combo.clear()
        if databases:
            self.database_combo.addItems(databases)
            index = self.database_combo.findText(current_name) if current_name else 0
            self.database_combo.setCurrentIndex(index if index >= 0 else 0)
            self.database_combo.setEnabled(True)
        else:
            self.database_combo.addItem(self._text("no_databases"))
            self.database_combo.setEnabled(False)
        self.database_combo.blockSignals(False)

        self.update_database_uri()

    def update_database_uri(self) -> None:
        selected_name = self._selected_database_name()
        if selected_name:
            self.start_button.setEnabled(True)
            self.backup_button.setEnabled(True)
            return

        self.start_button.setEnabled(False)
        self.backup_button.setEnabled(False)

    def choose_database_directory(self) -> None:
        current_directory = str(get_database_directory(DEFAULT_PATHS))
        selected_directory = QFileDialog.getExistingDirectory(
            self,
            self._text("select_database_folder_dialog"),
            current_directory,
        )
        if not selected_directory:
            return

        try:
            set_database_directory(selected_directory, DEFAULT_PATHS)
        except DesktopError as error:
            self._show_message(str(error), error=True)
            return

        self.refresh_database_list()
        self._show_message(self._text("database_folder_updated"), error=False)

    def choose_backup_directory(self) -> None:
        current_directory = str(get_backup_directory(DEFAULT_PATHS))
        selected_directory = QFileDialog.getExistingDirectory(
            self,
            self._text("select_backup_folder_dialog"),
            current_directory,
        )
        if not selected_directory:
            return

        try:
            set_backup_directory(selected_directory, DEFAULT_PATHS)
        except DesktopError as error:
            self._show_message(str(error), error=True)
            return

        self._set_directory_summary(self.backup_directory_value, get_backup_directory(DEFAULT_PATHS))
        self._show_message(self._text("backup_folder_updated"), error=False)

    def open_create_database_dialog(self) -> None:
        if self.create_database_thread is not None and self.create_database_thread.isRunning():
            self._show_message(self._text("creation_in_progress"), error=True)
            return

        dialog = CreateDatabaseDialog(self, self.language)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._start_create_database(
            dialog.database_name.text(),
            dialog.admin_user.text(),
            dialog.admin_password.text(),
        )

    def _start_create_database(self, file_name: str, admin_user: str, admin_password: str) -> None:
        self._set_database_creation_busy(True)
        self._show_message(self._text("creating_database"), error=False)

        self.create_database_thread = QThread(self)
        self.create_database_worker = CreateDatabaseWorker(file_name, admin_user, admin_password, self.language)
        self.create_database_worker.moveToThread(self.create_database_thread)

        self.create_database_thread.started.connect(self.create_database_worker.run)
        self.create_database_worker.finished.connect(self._on_create_database_success)
        self.create_database_worker.failed.connect(self._on_create_database_error)

        self.create_database_worker.finished.connect(self.create_database_thread.quit)
        self.create_database_worker.failed.connect(self.create_database_thread.quit)
        self.create_database_worker.finished.connect(self.create_database_worker.deleteLater)
        self.create_database_worker.failed.connect(self.create_database_worker.deleteLater)
        self.create_database_thread.finished.connect(self.create_database_thread.deleteLater)
        self.create_database_thread.finished.connect(self._on_create_database_finished)

        self.create_database_thread.start()

    def _on_create_database_success(self, database_name: str) -> None:
        self.refresh_database_list()
        self.database_combo.setCurrentText(database_name)
        success_message = self._text("database_created", database_name=database_name)
        self._show_message(success_message, error=False)
        QMessageBox.information(self, self._text("desktop_title"), success_message)

    def _on_create_database_error(self, message: str) -> None:
        self._show_message(message, error=True)

    def _on_create_database_finished(self) -> None:
        self.create_database_worker = None
        self.create_database_thread = None
        self._set_database_creation_busy(False)

    def _set_database_creation_busy(self, busy: bool) -> None:
        self.create_button.setEnabled(not busy)
        self.start_button.setEnabled((not busy) and (self._selected_database_name() is not None))
        self.backup_button.setEnabled((not busy) and (self._selected_database_name() is not None))

    def restore_database_from_file(self) -> None:
        source_path, _ = QFileDialog.getOpenFileName(
            self,
            self._text("select_database_file"),
            str(get_backup_directory(DEFAULT_PATHS)),
            self._text("sqlite_files"),
        )
        if not source_path:
            return

        suggested_name = Path(source_path).name
        target_name, accepted = QInputDialog.getText(
            self,
            self._text("restored_database_name"),
            self._text("database_file_name"),
            text=suggested_name,
        )
        if not accepted:
            return

        try:
            restored_path = restore_database(source_path, target_name, paths=DEFAULT_PATHS)
        except DesktopError as error:
            self._show_message(str(error), error=True)
            return

        self.refresh_database_list()
        self.database_combo.setCurrentText(restored_path.name)
        self._show_message(self._text("database_restored"), error=False)

    def backup_selected_database(self) -> None:
        selected_name = self._selected_database_name()
        if not selected_name:
            self._show_message(self._text("select_database_first"), error=True)
            return

        try:
            backup_path = create_backup(selected_name, paths=DEFAULT_PATHS)
        except DesktopError as error:
            self._show_message(str(error), error=True)
            return

        self._show_message(self._text("backup_created", backup_path=backup_path), error=False)

    def start_accounting(self) -> None:
        selected_name = self._selected_database_name()
        if not selected_name:
            self._show_message(self._text("select_database_to_start"), error=True)
            return

        try:
            database_uri = build_sqlite_uri(selected_name, DEFAULT_PATHS)
            create_backup(selected_name, paths=DEFAULT_PATHS)
            if self.current_database_uri and self.current_database_uri != database_uri:
                self.server_controller.stop()
            address = self.server_controller.start(
                database_uri=database_uri,
                secret_key=get_secret_key(DEFAULT_PATHS),
                language=self.language,
            )
        except DesktopError as error:
            self._show_message(str(error), error=True)
            return
        except Exception as error:
            self._show_message(self._text("server_start_error", error=error), error=True)
            return

        self.current_database_uri = database_uri
        self.browser_window.open_url(address)
        self.hide()
        self._show_message(self._text("server_started"), error=False)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.server_controller.stop()
        self.browser_window.close()
        event.accept()

    def _selected_database_name(self) -> str | None:
        if not self.database_combo.isEnabled():
            return None
        current_text = self.database_combo.currentText().strip()
        return current_text or None

    def _show_message(self, message: str, error: bool) -> None:
        message = localize_error(self.language, message)
        self.status_label.setText(message)
        if not error:
            return

        QMessageBox.critical(self, self._text("desktop_title"), message)

    def _set_directory_summary(self, label: QLabel, path: Path) -> None:
        folder_name = path.name or str(path)
        label.setText(folder_name)
        label.setToolTip(str(path))
        label.setWhatsThis(str(path))


def _load_icon(file_name: str) -> QIcon:
    icon_path = ASSETS_DIRECTORY / file_name
    return QIcon(str(icon_path)) if icon_path.exists() else QIcon()


def _load_pixmap(file_name: str, width: int) -> QPixmap:
    image_path = ASSETS_DIRECTORY / file_name
    if not image_path.exists():
        return QPixmap()
    return QPixmap(str(image_path)).scaledToWidth(width, Qt.TransformationMode.SmoothTransformation)


def init_app() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    language = get_language(DEFAULT_PATHS)
    if language is None:
        language_dialog = LanguageSelectionDialog()
        if language_dialog.exec() != QDialog.DialogCode.Accepted:
            return 0
        language = set_language(language_dialog.language, DEFAULT_PATHS)

    window = MainWindow(language)
    window.show()
    return app.exec()
