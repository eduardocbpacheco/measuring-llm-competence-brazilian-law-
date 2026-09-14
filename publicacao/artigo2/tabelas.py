#!/usr/bin/env python3
"""tabelas.py — as tabelas do artigo do benchmark, recomputadas dos julgamentos.

Desenho pedido na revisão: primeiro a concordância com o humano, depois as notas; uma
tabela por tarefa, modelos nas linhas e áreas do direito nas colunas. É o que se espera
encontrar num benchmark e o que a versão anterior deste artigo não trazia.

A peça aparece sempre nas duas classes que a banca rotula, e nunca num número só.
"""
from __future__ import annotations

import json, sys, statistics as st
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "avaliacao"))
from nota import AREAS, nota                                        # noqa: E402

SAI = Path(__file__).resolve().parent
import os
# Escrito por avaliacao/kappa_por_area.py. KAPPA_AREA muda o caminho nos dois lados.
ARQ_KAPPA = os.environ.get("KAPPA_AREA", "/tmp/kappa_area.json")
if not os.path.exists(ARQ_KAPPA):
    raise SystemExit(f"falta {ARQ_KAPPA}; rode avaliacao/kappa_por_area.py antes")
KAPPA = json.load(open(ARQ_KAPPA))

TAREFAS = [("discursiva", "peca_formal", "peca_merito"),
           ("questão discursiva", "peça, critérios formais", "peça, critérios de mérito")]
# nota.py usa `peca_material`; o kappa usa `peca_merito`. Mesma classe, nomes herdados.
TAREFA_NOTA = {"discursiva": "discursiva", "peca_formal": "peca_formal",
               "peca_merito": "peca_material"}
ABREV = {"administrativo": "Adm.", "civil": "Civ.", "constitucional": "Const.",
         "empresarial": "Empr.", "penal": "Pen.", "trabalhista": "Trab.",
         "tributário": "Trib."}
USADOS = {"gpt-oss-120b", "kimi-k2-5"}

TEXTO = {
    "juiz": "Juiz", "modelo": "Modelo", "geral": "geral", "ampl": "ampl.",
    "decimal": ",",
    "kappa": ("Concordância de Cohen com o padrão-ouro humano na <b>{rot}</b>, por área do "
              "direito. Valores &times;100. A coluna <b>ampl.</b> é a distância entre a "
              "melhor e a pior área do mesmo juiz."),
    "kappa_peca": ("Concordância de Cohen com o padrão-ouro humano na <b>redação de peça</b>, "
                   "por área do direito. Cada célula traz dois valores, "
                   "<b>formal</b>&#8202;|&#8202;mérito, nas duas classes de critério que a "
                   "banca rotula. Valores &times;100. A coluna <b>ampl.</b> é a distância "
                   "entre a melhor e a pior área do mesmo juiz."),
    "nota": ("Nota dos mesmos modelos como <b>respondentes</b> na {rot}, por área do direito."),
    "nota_peca": ("Nota dos mesmos modelos como <b>respondentes</b> na redação de peça, em "
                  "percentual dos pontos da banca. Mesma leitura das células: "
                  "<b>formal</b>&#8202;|&#8202;mérito."),
    "discursiva": "questão discursiva",
    "rotulo": "Tabela",
}
marca = lambda j: j
def pt(x) -> str:
    """Kappa em centesimos inteiros: 0,891 vira 89.

    Duas decisoes numa. A primeira e a precisao: cada area tem cerca de cem itens
    julgados e o erro padrao de um kappa desse tamanho e da ordem de 0,03, maior que a
    casa que o terceiro decimal anuncia. Duas casas e o que o dado sustenta.

    A segunda e de leitura. Na tabela da peca cada celula traz dois valores separados por
    barra, e `,89|,76` nao se le: a barra encosta na virgula do segundo numero e os dois
    viram um borrao. Sem virgula e sem zero a esquerda, `89|76` se le de relance e ainda
    devolve quatro caracteres por celula, que e o que permite manter a coluna folgada.
    A legenda avisa que os valores estao multiplicados por cem.
    """
    return "—" if x is None else f"{round(x * 100):d}"


# Quantos juízes entram nas tabelas do artigo. Medido: 22 e o maior numero que mantem o
# corpo dentro da pagina 10 nas DUAS versoes. Com 23 a inglesa invade a pagina 11, e com
# 24 as duas invadem. Quem manda e a inglesa, que e a de submissao.
# Os 26 com cobertura completa ficam no deposito; o artigo mostra o topo, que e onde a
# decisao de escolha acontece.
N_TABELA = 22


def completos(limite: int | None = N_TABELA) -> list[str]:
    """Juízes com as três tarefas medidas, ordenados pela concordância em mérito."""
    ok = [j for j, d in KAPPA.items() if all(t in d for t in TAREFAS[0])]
    ok = sorted(ok, key=lambda j: -(KAPPA[j]["peca_merito"]["_geral"] or -1))
    return ok[:limite] if limite else ok


def tab(n, cap, cabs, linhas, pe=""):
    rotulo = TEXTO["rotulo"]
    th = "".join("<th" + (' class="n"' if c[0] == "#" else "") + ">" + c.lstrip("#") + "</th>"
                 for c in cabs)
    return (f'<figure class="tab" id="tab-{n}">\n<figcaption><b>{rotulo} {n}.</b> {cap}</figcaption>\n'
            f'<div class="rol"><table>\n<thead><tr>{th}</tr></thead>\n<tbody>\n'
            + "".join(linhas) + "</tbody></table></div>\n"
            + (f'<p class="tnota">{pe}</p>' if pe else "") + "</figure>\n")


def tabela_kappa_peca(n: int, juizes: list[str]) -> str:
    """As duas classes da peça lado a lado na mesma célula: formal | mérito.

    Duas colunas por área dariam catorze colunas, largura que não cabe em retrato. Empilhar
    o par na célula custa altura de linha e devolve uma tabela inteira.
    """
    cab = [TEXTO["juiz"]] + [f"#{ABREV[a]}" for a in AREAS] + [f"#{TEXTO['geral']}", f"#{TEXTO['ampl']}"]
    L = []
    for j in juizes:
        cf, cm = KAPPA[j].get("peca_formal", {}), KAPPA[j].get("peca_merito", {})
        cs = [f'<td><code>{marca(j)}</code></td>']
        for a in AREAS:
            cs.append(f'<td class="n"><b>{pt(cf.get(a))}</b>'
                      f'<span class="g">|</span>{pt(cm.get(a))}</td>')
        cs.append(f'<td class="n z"><b>{pt(cf.get("_geral"))}</b>'
                  f'<span class="g">|</span>{pt(cm.get("_geral"))}</td>')
        amp = lambda c: (lambda v: max(v) - min(v) if len(v) > 1 else None)(
            [c[a] for a in AREAS if c.get(a) is not None])
        cs.append(f'<td class="n"><b>{pt(amp(cf))}</b>'
                  f'<span class="g">|</span>{pt(amp(cm))}</td>')
        L.append(("<tr class='hl'>" if j in USADOS else "<tr>") + "".join(cs) + "</tr>\n")
    return tab(n, TEXTO["kappa_peca"], cab, L)


def tabela_nota_peca(n: int, modelos: list[str]) -> str:
    cab = [TEXTO["modelo"]] + [f"#{ABREV[a]}" for a in AREAS] + [f"#{TEXTO['geral']}"]
    L = []
    fmt = lambda x: "—" if x is None else f"{x:.1f}".replace(".", TEXTO["decimal"])
    for m in modelos:
        cond = f"resp_{m}"
        gf, gm = nota(cond, "peca_formal"), nota(cond, "peca_material")
        if gf is None and gm is None:
            continue
        cs = [f'<td><code>{m}</code></td>']
        for a in AREAS:
            cs.append(f'<td class="n"><b>{fmt(nota(cond, "peca_formal", area=a))}</b>'
                      f'<span class="g">|</span>{fmt(nota(cond, "peca_material", area=a))}</td>')
        cs.append(f'<td class="n z"><b>{fmt(gf)}</b>'
                  f'<span class="g">|</span>{fmt(gm)}</td>')
        L.append("<tr>" + "".join(cs) + "</tr>\n")
    return tab(n, TEXTO["nota_peca"], cab, L)


def tabela_kappa(n: int, tk: str, rot: str, juizes: list[str]) -> str:
    cab = [TEXTO["juiz"]] + [f"#{ABREV[a]}" for a in AREAS] + [f"#{TEXTO['geral']}", f"#{TEXTO['ampl']}"]
    L = []
    for j in juizes:
        c = KAPPA[j].get(tk, {})
        v = [c.get(a) for a in AREAS]
        bons = [x for x in v if x is not None]
        amp = max(bons) - min(bons) if len(bons) > 1 else None
        cs = [f'<td><code>{marca(j)}</code></td>']
        for a, x in zip(AREAS, v):
            destaque = ' class="n melhor"' if x is not None and bons and x == max(bons) else ' class="n"'
            cs.append(f"<td{destaque}>{pt(x)}</td>")
        cs.append(f'<td class="n z">{pt(c.get("_geral"))}</td>')
        cs.append(f'<td class="n">{pt(amp)}</td>')
        L.append(("<tr class='hl'>" if j in USADOS else "<tr>") + "".join(cs) + "</tr>\n")
    return tab(n, TEXTO["kappa"].format(rot=rot), cab, L)


def tabela_nota(n: int, tk: str, rot: str, modelos: list[str]) -> str:
    cab = [TEXTO["modelo"]] + [f"#{ABREV[a]}" for a in AREAS] + [f"#{TEXTO['geral']}"]
    L = []
    for m in modelos:
        cond = f"resp_{m}"
        v = [nota(cond, TAREFA_NOTA[tk], area=a) for a in AREAS]
        g = nota(cond, TAREFA_NOTA[tk])
        if g is None:
            continue
        cs = [f'<td><code>{m}</code></td>']
        bons = [x for x in v if x is not None]
        for x in v:
            d = ' class="n melhor"' if x is not None and bons and x == max(bons) else ' class="n"'
            v1 = "—" if x is None else f"{x:.1f}".replace(".", TEXTO["decimal"])
            cs.append(f"<td{d}>{v1}</td>")
        cs.append(f'<td class="n z">{f"{g:.1f}".replace(".", TEXTO["decimal"])}</td>')
        L.append("<tr>" + "".join(cs) + "</tr>\n")
    return tab(n, TEXTO["nota"].format(rot=rot), cab, L)


def main() -> None:
    js = completos()
    print(f"juízes nas tabelas: {len(js)} de {len(completos(None))} com cobertura completa")
    # Comecam em 2: a Tabela 1 e a da composicao do conjunto, escrita a mao na Secao 3.1,
    # porque ela descreve o material e nao e recomputada dos julgamentos.
    partes = [tabela_kappa(2, "discursiva", TEXTO["discursiva"], js),
              tabela_kappa_peca(3, js),
              tabela_nota(4, "discursiva", TEXTO["discursiva"], js),
              tabela_nota_peca(5, js)]
    (SAI / "tabelas.html").write_text("\n".join(partes), "utf-8")
    linhas = sum(p.count("<tr>") + p.count("<tr class") for p in partes)
    print(f"{len(partes)} tabelas · {linhas} linhas de dados · "
          f"{(SAI / 'tabelas.html').stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
