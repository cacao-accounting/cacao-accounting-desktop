# Copyright 2020 William José Moreno Reyes
# This file is part of open-marquesote.
#
#  Foobar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Foobar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Foobar.  If not, see <https://www.gnu.org/licenses/>.
#
#  Contributors:
#   - William Moreno Reyes

"""
Cacao Accountins as a desktop app.

Based on pyqt5webengine as cliente and waitress as WSGI server.
"""

import subprocess
from sys import argv, executable
from PyQt5.QtWidgets import QApplication
from cacao_accounting import create_app
from cacao_accounting.conf import configuracion
from open_marquesote import MainWindow
from waitress import serve


def server():
    app = create_app(configuracion)
    serve(app)


def browser():
    browser = QApplication(argv)
    window = MainWindow(
        url="http://127.0.0.1:8080/app",
        appname="Cacao Accounting Desktop"
        )
    browser.exec_()


if __name__ == "__main__":
    subprocess.Popen([executable, "-c", "import cacao_desktop; cacao_desktop.server()"])
    browser()
