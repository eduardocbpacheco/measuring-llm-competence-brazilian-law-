#!/usr/bin/env python3
"""para_tex_2en.py — the benchmark article, English, in the IOS Press style.

Same conversion as the English ablation article, with three differences that belong to the
article and not to the converter: the source, the destination and the column padding. The
two document tables carry two values per cell, and at 4pt they overflow the text width.

    python publicacao/jurix/para_tex_2en.py
"""
from __future__ import annotations

from pathlib import Path

import para_tex_en as C

AQUI = Path(__file__).resolve().parent
C.ART = AQUI.parent / "artigo2_en/artigo.html"
C.SAIDA = AQUI / "artigo2_en.tex"
C.TABCOLSEP = 2
C.SEPARA_PARAGRAFOS = True

if __name__ == "__main__":
    C.main()
