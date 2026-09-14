#!/usr/bin/env python3
"""tabelas.py — the tables of the English version.

Importa o módulo da versão em português e troca só os rótulos. A alternativa, copiar o
arquivo e traduzir, deixaria dois cálculos vivos que podem divergir sem aviso; aqui os
números vêm do mesmo código e a tradução não tem como alcançá-los.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "artigo2"))
import tabelas as T                                                 # noqa: E402

T.SAI = AQUI
T.ABREV = {"administrativo": "Admin.", "civil": "Civil", "constitucional": "Const.",
           "empresarial": "Corp.", "penal": "Crim.", "trabalhista": "Labour",
           "tributário": "Tax"}
T.TEXTO = {
    "juiz": "Judge", "modelo": "Model", "geral": "overall", "ampl": "range",
    "decimal": ".",
    "kappa": ("Cohen's agreement with the human gold standard on the <b>{rot}</b>, by area "
              "of law. Values &times;100. The <b>range</b> column is the distance between "
              "the best and the worst area of the same judge."),
    "kappa_peca": ("Cohen's agreement with the human gold standard on <b>drafting a legal "
                   "document</b>, by area of law. Each cell carries two values, "
                   "<b>formal</b>&#8202;|&#8202;substantive, for the two classes of "
                   "criterion the examining board labels. Values &times;100. The "
                   "<b>range</b> column is the distance between the best and the worst area "
                   "of the same judge."),
    "nota": ("Score of the same models as <b>respondents</b> on the {rot}, by area of law."),
    "nota_peca": ("Score of the same models as <b>respondents</b> on drafting a legal "
                  "document, as a percentage of the board's points. Cells read as before: "
                  "<b>formal</b>&#8202;|&#8202;substantive."),
    "discursiva": "discursive question",
    "rotulo": "Table",
}

if __name__ == "__main__":
    T.main()
