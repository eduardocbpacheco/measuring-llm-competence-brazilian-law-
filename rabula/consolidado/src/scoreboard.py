"""
Agrega notas dos juízes em scoreboard estilo `df_oabench_scoreboard.pkl`.

Saída:
   id | model | evaluated_area | discursive | document_writing | overall
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from judge_llm import calcular_pontuacao, voto_majoritario


def consolidar_runs_questao(runs_path: list[Path]) -> list[dict]:
    """Lê N arquivos de runs do juiz e retorna voto majoritário por critério."""
    runs = []
    for p in runs_path:
        obj = json.loads(p.read_text("utf-8"))
        runs.append(obj.get("resultado") or [])
    return voto_majoritario(runs)


def nota_questao(consolidado: list[dict]) -> tuple[float, float, float]:
    """Retorna (obtida, máxima, normalizada_0_100)."""
    obtida, maxima = calcular_pontuacao(consolidado)
    norm = (obtida / maxima * 100) if maxima > 0 else 0.0
    return obtida, maxima, round(norm, 2)


def scoreboard_modelo(
    model_name: str,
    avaliacoes_dir: Path,
    df_discursive: pd.DataFrame,
    df_practical: pd.DataFrame,
    by_area: bool = True,
) -> pd.DataFrame:
    """
    avaliacoes_dir: data/evaluations/{model_name}/
       discursive/q{id}_run{r}.json
       document_writing/q{id}_run{r}.json
    """
    linhas = []

    def juntar(tipo: str, df_base: pd.DataFrame, col_id: str = "id") -> pd.DataFrame:
        base_dir = avaliacoes_dir / tipo
        notas = []
        if not base_dir.exists():
            return pd.DataFrame()
        for _, row in df_base.iterrows():
            qid = int(row[col_id])
            runs = sorted(base_dir.glob(f"q{qid}_run*.json"))
            if not runs:
                continue
            consolidado = consolidar_runs_questao(runs)
            obt, mx, norm = nota_questao(consolidado)
            notas.append({
                "id": qid,
                "exam": row.get("exam"),
                "area": row.get("area"),
                "obtida": obt,
                "maxima": mx,
                "normalizada": norm,
                "n_runs": len(runs),
            })
        return pd.DataFrame(notas)

    disc = juntar("discursive", df_discursive)
    pec = juntar("document_writing", df_practical)

    # row "all"
    linhas.append({
        "id": 1,
        "model": model_name,
        "evaluated_area": "all",
        "discursive": round(float(disc["normalizada"].mean()), 2) if not disc.empty else None,
        "document_writing": round(float(pec["normalizada"].mean()), 2) if not pec.empty else None,
        "n_disc": int(len(disc)),
        "n_pec": int(len(pec)),
    })

    if by_area:
        areas = sorted(set(disc.get("area", pd.Series([], dtype=str)).dropna()) | set(pec.get("area", pd.Series([], dtype=str)).dropna()))
        for i, a in enumerate(areas, start=2):
            d_a = disc[disc["area"] == a] if not disc.empty else pd.DataFrame()
            p_a = pec[pec["area"] == a] if not pec.empty else pd.DataFrame()
            linhas.append({
                "id": i,
                "model": model_name,
                "evaluated_area": a,
                "discursive": round(float(d_a["normalizada"].mean()), 2) if not d_a.empty else None,
                "document_writing": round(float(p_a["normalizada"].mean()), 2) if not p_a.empty else None,
                "n_disc": int(len(d_a)),
                "n_pec": int(len(p_a)),
            })

    return pd.DataFrame(linhas)
