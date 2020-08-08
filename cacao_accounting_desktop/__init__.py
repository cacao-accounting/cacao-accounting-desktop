# Copyright 2020 William José Moreno Reyes
# This file is part of Cacao Accounting Desktop.
#
#  Cacao Accounting Desktop is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Cacao Accounting Desktop is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Cacao Accounting Desktop.  If not, see <https://www.gnu.org/licenses/>.
#
#  Contributors:
#   - William Moreno Reyes

"""
Cacao Accountins as a desktop app.

Based on pyqt5webengine as cliente and waitress as WSGI server.
"""

import subprocess
import time
from sys import argv, executable
from PyQt5.QtWidgets import QApplication
from cacao_accounting import create_app
from cacao_accounting.conf import configuracion
from cacao_accounting.metadata import DEVELOPMENT
from open_marquesote import MainWindow
from waitress import serve


def server():
    app = create_app(configuracion)
    if DEVELOPMENT:
        app.config["ENV"] = "development"
        app.config["DEBUG"] = True
        app.config[" TEMPLATES_AUTO_RELOAD¶"] = True
        app.config[" EXPLAIN_TEMPLATE_LOADING¶"] = True
    try:
        serve(app, threads=2)
    except OSError:
        # If the server was started before and is still running there will be a OSError: [Errno 98] Address already in use
        # Since the server is already up and running we pass this error.
        pass


def browser():
    time.sleep(5)  # Give 5 seconds to the WSGI server to start.
    browser = QApplication(argv)
    window = MainWindow(url="http://127.0.0.1:8080/app", appname="Cacao Accounting Desktop")
    browser.exec_()


def run():
    subprocess.Popen(
        [executable, "-c", "import cacao_accounting_desktop; cacao_accounting_desktop.server()"],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    subprocess.Popen([executable, "-c", "import cacao_accounting_desktop; cacao_accounting_desktop.browser()"])


if __name__ == "__main__":
    run()
