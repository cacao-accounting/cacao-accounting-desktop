![Logo](https://raw.githubusercontent.com/cacao-accounting/cacao-accounting-desktop/main/cacao_accounting_desktop/assets/CacaoAccounting.png)

# Cacao Accounting Desktop

[![Python application](https://github.com/cacao-accounting/cacao-accounting-desktop/actions/workflows/python-app.yml/badge.svg)](https://github.com/cacao-accounting/cacao-accounting-desktop/actions/workflows/python-app.yml)

This is Cacao Accounting software packaged as a windows
executable, so accountans can download the app and use it
in theirs Windows personal computers to run small accounting
projects, once installed you not require a active internet
conection to run the app, but it is recomended to have a
conection to the internet to make backups of the app database.

Please note that if you are a Linux or Mac user you can host
Cacao Accounting for your personal use with a few steps, this
project is focused in Windows system that do not have a default
install of Python.

## Cacao Accounting as stand alone executable for Windows.

Please note that this is not a native windows app, this mean a
app compiled to run as windows executable, [Cacao Accounting](https://github.com/cacao-accounting/cacao-accounting)
is a python wsgi app based is the [Flask Python Microframework](https://flask.palletsprojects.com/en/3.0.x/), but we use a simple hack thanks
to the [Flask Web Gui](https://github.com/ClimenteA/flaskwebgui) project to start a local wsgi server and
open a browers windows so the user can interact with the app, this way we can simulate a local install of
the app so accountans can use the app localy with out knowing how to set up a server.

Note than been usable as standalone Windows app is one of the main reason beging the development of the Cacao
Accounting project.

### Create a Windows executable

Several steps are necessary to create a windows executable:

1. Download [WinPython 3.8.10](https://github.com/winpython/winpython/releases/download/4.3.20210620/Winpython32-3.8.10.0dot.exe), this contain a portable version of python suitable to run Cacao Accounting as a desktop app.

```
Please note that there is no formal requirement on the Python version,
Python 3.8.10 is taken as the base because it is the last stable version
to support Windows 7.

Support for Windows 7 ended on January 14, 2020, however some people may
find it useful to be able to run Cacao Accounting on Windows 7 (it is up
to the user to use a version of their operating system without manufacturer
support, updating the operating system version is highly recommended).

The 32-bit version must be functional but it is recommended to at least
use a Core i3 processor or higher, which are 64-bit processors.

It is possible that future versions of this project will update to a more
recent version of python.
```

3. Uncompress WinPython 3.8.10, this will create a directory name `WPy64-38100` and inside this directory a copy of Python portable named `python-3.8.10.amd64`

4. Copy the content of `python-3.8.10.amd64` to the `pydist` in the same directory that the script `cacaoaccounting.pyw`, your working directory should be like this:

```
work-dir:
 |-assets
 |-cacaoaccounting.pyw
 |-LICENSE
 |-pydist
  |-python.exe
  |-[support files to the python portable enviroment]
 |-README.md
 |-requirements.txt
 |-setup.nsi
```

4. Install requirements inside the python portable enviroment with:

```
pydist\python.exe -m pip install -r requirements.txt
```

5. Ensure the python portable enviroment can run the scritp with:

`pydist\python.exe cacaoaccounting.pyw`

6. Generate a Windows executable with:

```
python -m pip install gen-exe
gen-exe --hide-console cacaoaccounting.exe "{EXE_DIR}\\pydist\\python.exe cacaoaccounting.pyw" --icon-file cacao_accounting_desktop/assets/icon.ico
```

Your working directory now will have a Windows executable:

```
work-dir:
 |-assets
 |-cacaoaccounting.pyw
 |-cacaoaccounting.exe
 |-LICENSE
 |-pydist
  |-python.exe
  |-[support files to the python portable enviroment]
 |-README.md
 |-requirements.txt
 |-setup.nsi
```

Doble click on the executable to verify it works.

7. Create a Windows installer with [nsis](https://nsis.sourceforge.io/Main_Page) using the `setup.nsi`, this will create a installer that can be shared to final users.

```
Please consider that .exe installers, unlike .msi installers, may represent a danger
to your computer by containing malicious software or performing actions not authorized
by the user. For this reason, we recommend only using .exe installers obtained from
reliable sources. Since Cacao Accounting Desktop is distributed free of charge, we
recommend that you always download the application from the official Cacao Accounting
website and do not use installers provided by third parties.

To reduce the risk of damage to your computer, the Cacao Accounting installer does not
require administrator permissions and only makes changes to your user folder without
affecting other users on the computer.
```

# Copyright

Copyright 2024 BMO Soluciones, S.A.

![BMO Logo](https://bmogroup.solutions/wp-content/uploads/2023/11/cropped-Logotipo-BMO-Soluciones-pequeno-1.png)
