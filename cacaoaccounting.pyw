# -*- coding: utf-8 -*-
# Copyright 2024 BMO Soluciones
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os import environ

# ---------------------------------------------------------------------------------------
# Modo de Escritorio
# ---------------------------------------------------------------------------------------
environ["CACAO_ACCOUNTING_DESKTOP"] = "ok"


if __name__ == "__main__":
    assert environ.get("CACAO_ACCOUNTING_DESKTOP") == "ok"
    from cacao_accounting_desktop import init_app

    init_app()
