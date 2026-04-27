from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QCloseEvent, QIcon, QPixmap
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
    get_secret_key,
    list_database_files,
    restore_database,
    set_backup_directory,
    set_database_directory,
)
from .server import WaitressServerController

APP_DIRECTORY = Path(__file__).resolve().parent
ASSETS_DIRECTORY = APP_DIRECTORY / "assets"


class CreateDatabaseWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, file_name: str, admin_user: str, admin_password: str):
        super().__init__()
        self.file_name = file_name
        self.admin_user = admin_user
        self.admin_password = admin_password

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
            self.failed.emit(f"No fue posible crear la base de datos: {error}")
            return

        self.finished.emit(created_path.name)


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cacao Accounting")
        self.resize(1200, 800)
        self.setWindowIcon(_load_icon("icon.ico"))

        self.web_view = QWebEngineView(self)
        self.setCentralWidget(self.web_view)

    def open_url(self, url: str) -> None:
        self.web_view.setUrl(QUrl(url))
        self.show()
        self.raise_()
        self.activateWindow()


class CreateDatabaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear nueva base de datos")
        self.setModal(True)

        self.database_name = QLineEdit(self)
        self.database_name.setPlaceholderText("empresa.db")

        self.admin_user = QLineEdit(self)
        self.admin_user.setPlaceholderText("Administrador")

        self.admin_password = QLineEdit(self)
        self.admin_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_password.setPlaceholderText("Clave de acceso")

        form_layout = QFormLayout()
        form_layout.addRow("Base de datos", self.database_name)
        form_layout.addRow("Usuario administrador", self.admin_user)
        form_layout.addRow("Clave", self.admin_password)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(form_layout)
        root_layout.addWidget(buttons)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_directories(DEFAULT_PATHS)

        self.server_controller = WaitressServerController()
        self.browser_window = BrowserWindow()
        self.current_database_uri = ""
        self.create_database_thread: QThread | None = None
        self.create_database_worker: CreateDatabaseWorker | None = None

        self.setWindowTitle("Cacao Accounting Desktop")
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
            "Selecciona una base de datos existente o crea una nueva desde esta ventana.",
            error=False,
        )

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
        group = QGroupBox("Directorios", self)
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(14)

        self.database_directory_value = QLabel(group)
        self.database_directory_value.setObjectName("directoryValue")
        self.database_directory_value.setWordWrap(True)
        self.database_directory_caption = QLabel("Bases SQLite", group)
        self.database_directory_caption.setObjectName("directoryCaption")
        select_database_directory_button = QPushButton("Seleccionar carpeta de bases", group)
        select_database_directory_button.clicked.connect(self.choose_database_directory)

        self.backup_directory_value = QLabel(group)
        self.backup_directory_value.setObjectName("directoryValue")
        self.backup_directory_value.setWordWrap(True)
        self.backup_directory_caption = QLabel("Respaldos", group)
        self.backup_directory_caption.setObjectName("directoryCaption")
        select_backup_directory_button = QPushButton("Configurar carpeta de respaldo", group)
        select_backup_directory_button.clicked.connect(self.choose_backup_directory)

        database_info = self._build_directory_summary(
            self.database_directory_caption,
            self.database_directory_value,
            "Carpeta donde se listan y crean las bases SQLite.",
        )
        backup_info = self._build_directory_summary(
            self.backup_directory_caption,
            self.backup_directory_value,
            "Carpeta usada para respaldos y restauraciones.",
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
        group = QGroupBox("Bases de datos", self)
        layout = QGridLayout(group)

        self.database_combo = QComboBox(group)
        self.database_combo.currentIndexChanged.connect(self.update_database_uri)

        refresh_button = QPushButton("Refrescar lista", group)
        refresh_button.clicked.connect(self.refresh_database_list)

        layout.addWidget(QLabel("Base activa"), 0, 0)
        layout.addWidget(self.database_combo, 0, 1)
        layout.addWidget(refresh_button, 0, 2)
        return group

    def _build_actions_group(self) -> QGroupBox:
        group = QGroupBox("Acciones", self)
        layout = QGridLayout(group)

        self.create_button = QPushButton("Crear nueva base", group)
        self.create_button.clicked.connect(self.open_create_database_dialog)

        restore_button = QPushButton("Restaurar base", group)
        restore_button.clicked.connect(self.restore_database_from_file)

        self.backup_button = QPushButton("Respaldar base seleccionada", group)
        self.backup_button.clicked.connect(self.backup_selected_database)

        self.start_button = QPushButton("Iniciar Cacao Accounting", group)
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
            self.database_combo.addItem("No se encontraron bases de datos")
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
            "Seleccione el directorio para almacenar bases SQLite",
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
        self._show_message("Directorio de bases de datos actualizado.", error=False)

    def choose_backup_directory(self) -> None:
        current_directory = str(get_backup_directory(DEFAULT_PATHS))
        selected_directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccione el directorio para respaldos",
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
        self._show_message("Directorio de respaldos actualizado.", error=False)

    def open_create_database_dialog(self) -> None:
        if self.create_database_thread is not None and self.create_database_thread.isRunning():
            self._show_message("Ya hay una creación de base en curso.", error=True)
            return

        dialog = CreateDatabaseDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._start_create_database(
            dialog.database_name.text(),
            dialog.admin_user.text(),
            dialog.admin_password.text(),
        )

    def _start_create_database(self, file_name: str, admin_user: str, admin_password: str) -> None:
        self._set_database_creation_busy(True)
        self._show_message("Creando base de datos, por favor espera...", error=False)

        self.create_database_thread = QThread(self)
        self.create_database_worker = CreateDatabaseWorker(file_name, admin_user, admin_password)
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
        success_message = f"Base de datos creada correctamente: {database_name}"
        self._show_message(success_message, error=False)
        QMessageBox.information(self, "Cacao Accounting Desktop", success_message)

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
            "Seleccione la base de datos a restaurar",
            str(get_backup_directory(DEFAULT_PATHS)),
            "SQLite (*.db);;Todos los archivos (*)",
        )
        if not source_path:
            return

        suggested_name = Path(source_path).name
        target_name, accepted = QInputDialog.getText(
            self,
            "Nombre de la base restaurada",
            "Nombre del archivo .db",
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
        self._show_message("Base de datos restaurada correctamente.", error=False)

    def backup_selected_database(self) -> None:
        selected_name = self._selected_database_name()
        if not selected_name:
            self._show_message("Selecciona primero una base de datos.", error=True)
            return

        try:
            backup_path = create_backup(selected_name, paths=DEFAULT_PATHS)
        except DesktopError as error:
            self._show_message(str(error), error=True)
            return

        self._show_message(f"Respaldo generado en: {backup_path}", error=False)

    def start_accounting(self) -> None:
        selected_name = self._selected_database_name()
        if not selected_name:
            self._show_message("Selecciona una base de datos antes de iniciar la aplicacion.", error=True)
            return

        try:
            database_uri = build_sqlite_uri(selected_name, DEFAULT_PATHS)
            create_backup(selected_name, paths=DEFAULT_PATHS)
            if self.current_database_uri and self.current_database_uri != database_uri:
                self.server_controller.stop()
            address = self.server_controller.start(database_uri=database_uri, secret_key=get_secret_key(DEFAULT_PATHS))
        except DesktopError as error:
            self._show_message(str(error), error=True)
            return
        except Exception as error:
            self._show_message(f"No fue posible iniciar el servidor: {error}", error=True)
            return

        self.current_database_uri = database_uri
        self.browser_window.open_url(address)
        self.hide()
        self._show_message("Servidor local iniciado correctamente.", error=False)

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
        self.status_label.setText(message)
        if not error:
            return

        QMessageBox.critical(self, "Cacao Accounting Desktop", message)

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
    window = MainWindow()
    window.show()
    return app.exec()
