![Logo](https://raw.githubusercontent.com/cacao-accounting/cacao-accounting-desktop/main/assets/CacaoAccounting.png)

# Cacao Accounting Desktop

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

Please note thar this is not a native windows app, this mean a app compiled to run as windows executable,
[Cacao Accounting](https://github.com/cacao-accounting/cacao-accounting) is a python wsgi app based is the
[Flask Python Microframework](https://flask.palletsprojects.com/en/3.0.x/), but we use a simple hack thanks
to the [Flask Web Gui](https://github.com/ClimenteA/flaskwebgui) project to start a local wsgi server and
open a browers windows so the user can interact with the app, this way we can simulate a local install of
the app so accountans can use the app localy with out knowing how to set up a server.

Note than been usable as standalone Windows app is one of the main reason beging the development of the Cacao
Accounting project.

### Create a Windows executable

Several steps are necessary to create a windows executable:

1. Install pyvan to generate a Windows executable:

```
pip install pyvan
```

2. Create a Windows executable with:

```
python van.py
```

Doble click on the executable to verify it works.

3. Create a Windows installer with [nsis](https://nsis.sourceforge.io/Main_Page) using the `setup.nsi`, this will create a installer that can be shared to final users.

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
