#!/usr/bin/env python3
"""kappa_por_area.py — a concordância do juiz aberta por área do direito e por tarefa.

O artigo do benchmark reportava a régua num número por gênero. Um benchmark, porém, é
consultado por quem quer saber onde o instrumento é confiável, e "onde" aqui tem duas
dimensões: a tarefa e a matéria. Um juiz pode concordar com o humano em Direito Penal e
divergir em Tributário sem que a média denuncie.

Três tarefas, porque a peça nunca se reporta num número só: discursiva, peça formal e peça
de mérito. Sete áreas com quinze questões cada, de modo que nenhuma domina a média.

Uso:  juridico-env/bin/python avaliacao/kappa_por_area.py
Saída: /tmp/kappa_area.json, ou o caminho em KAPPA_AREA
"""
from __future__ import annotations

import collections, json, os, sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

RAIZ = Path(__file__).resolve().parent.parent
# Onde fica o kappa por área. Padrão em /tmp para não sujar a árvore de trabalho;
# KAPPA_AREA aponta para outro lugar quando /tmp não serve.
ARQ_KAPPA = Path(os.environ.get("KAPPA_AREA", "/tmp/kappa_area.json"))

sys.path.insert(0, str(RAIZ / "rabula/consolidado/src"))
sys.path.insert(0, str(RAIZ / "avaliacao"))
from alignment import carregar_anotacoes_humanas                      # noqa: E402
from judge_llm import voto_majoritario                                # noqa: E402
from analisa_kappa_v4 import (V4, ANNOT, chave_disc, chave_pratica,    # noqa: E402
                              carrega_df, juizes_disponiveis, reps_disponiveis)
from kappa_por_classe import mapa_classe, classe_por_chave            # noqa: E402

AREAS = ["administrativo", "civil", "constitucional", "empresarial", "penal",
         "trabalhista", "tributário"]
MIN_COBERTURA = 0.85


def area_por_chave(df: pd.DataFrame, genero: str) -> dict[str, str]:
    fora = {}
    for _, row in df.iterrows():
        for c in (row["formated_criteria"] or []):
            k = (chave_disc(row["exam"], row["area"], row["number"], c.get("letra"),
                            c.get("parte")) if genero == "discursive"
                 else chave_pratica(row["exam"], row["area"], c.get("numero"), c.get("parte")))
            fora[k] = row["area"]
    return fora


def vereditos(rep: int, juiz: str, genero: str, df: pd.DataFrame) -> pd.DataFrame:
    d = V4 / f"rep{rep}" / f"alignment-{juiz}" / genero
    linhas = []
    for _, row in df.iterrows():
        runs = []
        for a in sorted(d.glob(f"q{int(row['id'])}_run*.json")):
            try:
                runs.append(json.loads(a.read_text("utf-8")).get("resultado") or [])
            except Exception:
                pass
        if not runs:
            continue
        for it in voto_majoritario(runs):
            k = (chave_disc(row["exam"], row["area"], row["number"], it.get("letra"),
                            it.get("parte")) if genero == "discursive"
                 else chave_pratica(row["exam"], row["area"], it.get("numero"), it.get("parte")))
            linhas.append({"chave": k, "acerto": int(it.get("acerto") or 0)})
    return pd.DataFrame(linhas)


def main() -> None:
    dfp, dfd = carrega_df("document_writing"), carrega_df("discursive")
    hp = carregar_anotacoes_humanas(ANNOT, tipo="praticas")
    hd = carregar_anotacoes_humanas(ANNOT, tipo="discursivas")
    hp = hp.assign(classe=hp["chave"].map(classe_por_chave(dfp, mapa_classe())),
                   area=hp["chave"].map(area_por_chave(dfp, "document_writing")))
    hd = hd.assign(classe="merito", area=hd["chave"].map(area_por_chave(dfd, "discursive")))

    TAREFAS = [("discursiva", hd, dfd, "discursive", None),
               ("peca_formal", hp, dfp, "document_writing", "formal"),
               ("peca_merito", hp, dfp, "document_writing", "merito")]

    saida: dict = {}
    for juiz in juizes_disponiveis():
        for tk, hum, df, genero, classe in TAREFAS:
            por_area: dict = collections.defaultdict(lambda: ([], []))
            reps = 0
            for rep in reps_disponiveis():
                v = vereditos(rep, juiz, genero, df)
                if v.empty:
                    continue
                m = v.merge(hum, on="chave", how="inner")
                if len(m) / len(hum) < MIN_COBERTURA:
                    continue
                reps += 1
                if classe:
                    m = m[m.classe == classe]
                for a, g in m.groupby("area"):
                    por_area[a][0].extend(g["golden"].tolist())
                    por_area[a][1].extend(g["acerto"].tolist())
            if not reps:
                continue
            cel = {}
            for a, (gold, pred) in por_area.items():
                cel[a] = (float(cohen_kappa_score(gold, pred))
                          if len(set(gold)) > 1 and len(set(pred)) > 1 else None)
            todos = [x for par in por_area.values() for x in par[0]], \
                    [x for par in por_area.values() for x in par[1]]
            cel["_geral"] = (float(cohen_kappa_score(*todos))
                             if len(set(todos[0])) > 1 else None)
            cel["_reps"] = reps
            saida.setdefault(juiz, {})[tk] = cel

    ARQ_KAPPA.parent.mkdir(parents=True, exist_ok=True)
    json.dump(saida, open(ARQ_KAPPA, "w"), ensure_ascii=False, indent=1)
    print(f"{len(saida)} juízes · {ARQ_KAPPA}\n")
    ordem = sorted(saida, key=lambda j: -(saida[j].get("peca_merito", {}).get("_geral") or -1))
    print(f"{'juiz':22s} " + " ".join(f"{a[:6]:>6s}" for a in AREAS) + "  geral")
    for j in ordem[:8]:
        c = saida[j].get("peca_merito", {})
        print(f"{j:22s} " + " ".join(
            f"{c.get(a):6.3f}" if c.get(a) is not None else "     —" for a in AREAS)
            + f"  {c.get('_geral') or float('nan'):.3f}")


if __name__ == "__main__":
    main()
