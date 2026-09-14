#!/usr/bin/env python3
"""para_tex_2.py — o artigo do benchmark no estilo IOS Press.

Mesma conversão do artigo da ablação, com três diferenças que são do artigo e não do
conversor: a origem, o destino, a folga entre colunas e a separação de parágrafos. As duas tabelas de peça deste
artigo trazem dois valores por célula, e com 4pt elas estouram a largura do texto.

    python publicacao/jurix/para_tex_2.py
"""
from __future__ import annotations

from pathlib import Path

import para_tex as C

AQUI = Path(__file__).resolve().parent
C.ART = AQUI.parent / "artigo2/artigo.html"
C.SAIDA = AQUI / "artigo2.tex"
C.TABCOLSEP = 2
C.SEPARA_PARAGRAFOS = True

if __name__ == "__main__":
    C.main()
