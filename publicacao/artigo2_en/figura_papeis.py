#!/usr/bin/env python3
"""figura_papeis.py — the figure of the English version.

Importa o módulo da versão em português e troca só os rótulos e o separador decimal. Os
dados e o desenho vêm do mesmo código, então as duas figuras não têm como divergir.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "artigo2"))
import figura_papeis as F                                           # noqa: E402

F.SAI = AQUI / "papeis.pdf"
F.TEXTO = {
    "paineis": ["discursive question", "document · formal criteria",
                "document · substantive criteria"],
    "x": "score as respondent (%)",
    "y": "agreement as judge ($\\kappa$)",
    "decimal": ".",
}

if __name__ == "__main__":
    F.desenha()
