#!/usr/bin/env python3
"""figura_papeis.py — julgar contra responder, um painel por tarefa.

Três painéis, e é a comparação entre eles que carrega o argumento: a associação entre
saber fazer a tarefa e saber julgá-la cai conforme a tarefa passa de forma para mérito.
Com um painel só isso não aparece.

Uma cor só e rótulo seletivo. Com quase trinta modelos, nenhuma paleta categórica sobrevive
aos limiares de separação para daltonismo; a posição carrega tudo, e o nome aparece apenas
nos pontos que sustentam o argumento.

Os rótulos ficam em `TEXTO` para que a versão em inglês troque o idioma sem tocar no
desenho nem nos dados. O separador decimal acompanha o idioma.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "avaliacao"))
from nota import nota                                               # noqa: E402

# O HTML do artigo e do app de revisão precisa de um formato que o navegador desenhe; o
# LaTeX prefere o vetorial. Gravamos os dois do mesmo desenho.
SAI = Path(__file__).resolve().parent / "papeis.pdf"
import os
# Escrito por avaliacao/kappa_por_area.py. KAPPA_AREA muda o caminho nos dois lados.
ARQ_KAPPA = os.environ.get("KAPPA_AREA", "/tmp/kappa_area.json")
if not os.path.exists(ARQ_KAPPA):
    raise SystemExit(f"falta {ARQ_KAPPA}; rode avaliacao/kappa_por_area.py antes")
KAPPA = json.load(open(ARQ_KAPPA))

TAREFAS = [("discursiva", "discursiva"), ("peca_formal", "peca_formal"),
           ("peca_merito", "peca_material")]
TEXTO = {
    "paineis": ["questão discursiva", "peça · critérios formais", "peça · critérios de mérito"],
    "x": "nota como respondente (%)",
    "y": "concordância como juiz ($\\kappa$)",
    "decimal": ",",
}

# Cinza-azulado sobre papel quase branco: o artigo é impresso em preto e branco com
# frequência, e a figura precisa sobreviver a isso.
PONTO, TINTA, SUAVE, GRADE = "#2E4272", "#16181D", "#6A6E77", "#DCDBD6"
DESTAQUE = {"kimi-k2-thinking", "mistral-l3-675b", "nova-lite"}


def dados(tk_kappa: str, tk_nota: str):
    xs, ys, ns = [], [], []
    for j, c in KAPPA.items():
        k = c.get(tk_kappa, {}).get("_geral")
        n = nota(f"resp_{j}", tk_nota)
        if k is not None and n is not None:
            xs.append(n); ys.append(k); ns.append(j)
    return xs, ys, ns


def desenha() -> None:
    dec = TEXTO["decimal"]
    fig, eixos = plt.subplots(1, 3, figsize=(9.6, 3.4), sharey=True)
    for ax, (tkk, tkn), rot in zip(eixos, TAREFAS, TEXTO["paineis"]):
        xs, ys, ns = dados(tkk, tkn)
        r = spearmanr(xs, ys)
        mx, my = sorted(xs)[len(xs) // 2], sorted(ys)[len(ys) // 2]
        ax.axvline(mx, color=GRADE, lw=.9, zorder=0)
        ax.axhline(my, color=GRADE, lw=.9, zorder=0)
        ax.scatter(xs, ys, s=26, color=PONTO, alpha=.85,
                   edgecolor="white", linewidth=.6, zorder=3)
        for x, y, n in zip(xs, ys, ns):
            if n in DESTAQUE:
                ax.annotate(n, (x, y), textcoords="offset points", xytext=(5, 4),
                            fontsize=6.4, color=SUAVE)
        ax.set_title(f"{rot}\n" + r"$\rho$ = " + f"{r.statistic:+.2f}".replace(".", dec)
                     + f"   p = {r.pvalue:.3f}".replace(".", dec),
                     fontsize=8.5, color=TINTA, pad=7)
        ax.set_xlabel(TEXTO["x"], fontsize=7.5, color=SUAVE)
        ax.tick_params(labelsize=7, colors=SUAVE)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(GRADE)
    eixos[0].set_ylabel(TEXTO["y"], fontsize=7.5, color=SUAVE)
    fig.tight_layout()
    fig.savefig(SAI, bbox_inches="tight")
    fig.savefig(SAI.with_suffix(".png"), bbox_inches="tight", dpi=220)
    print(f"{SAI.parent.name}/{SAI.name} · três painéis")
    for (tkk, tkn), rot in zip(TAREFAS, TEXTO["paineis"]):
        xs, ys, _ = dados(tkk, tkn)
        r = spearmanr(xs, ys)
        print(f"  {rot:28s} n={len(xs):3d}  rho={r.statistic:+.3f}  p={r.pvalue:.4f}")


if __name__ == "__main__":
    desenha()
