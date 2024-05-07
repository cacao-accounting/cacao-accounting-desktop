import pyvan

OPTIONS = {
    "main_file_name": "cacaoaccounting.pyw",
    "show_console": False,
    "use_existing_requirements": True,
    "python_version": "3.8.0",
    "use_pipreqs": False,
    "build_dir": "dist",
    "pydist_sub_dir": "pydist",
    "source_sub_dir": "",
    "icon_file": "cacao_accounting_desktop/assets/icon.ico",
}

pyvan.build(**OPTIONS)
