#!/usr/bin/env python3
"""
Valida o juiz LLM contra anotações humanas.

Roda o juiz nas RESPOSTAS DO gpt-4o-mini (subconjunto human_alignment_experiment)
e mede κ Cohen, MAE etc. contra voto majoritário dos 3 humanos.

Pré-requisito: ter rodado o juiz em ../data/evaluations/gpt-4o-mini-baseline/
ou usar --recompute para chamar a API agora.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alignment import carregar_anotacoes_humanas, relatorio_alinhamento  # noqa: E402
from judge_llm import avaliar_questao, voto_majoritario  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("align")

DATA = ROOT / "data"
ANNOT = DATA / "annotations"
HUMAN_EXP = (
    ROOT.parent  # rabula/
    / "Reconstrucao" / "LLM-as-judge-in-BR-legal-domain" / "data" / "dfs"
    / "human_alignment_experiment"
)
EVAL_OUT = DATA / "evaluations" / "gpt-4o-mini-baseline"


def chave(exame, area, numero, letra, parte) -> str:
    return f"exame_{exame}_area_{area}_questao_numero_{numero}_letra_{letra}_parte_{parte}"


def chave_pratica(exame, area, numero, parte) -> str:
    return f"exame_{exame}_area_{area}_questao_numero_{numero}_parte_{parte}"


def _rodar_juiz(df: pd.DataFrame, tipo: str, out_dir: Path, n_runs: int, judge_model: str, backend: str = "azure") -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for _, row in df.iterrows():
        qid = int(row["id"])
        for r in range(n_runs):
            p = out_dir / f"q{qid}_run{r}.json"
            if p.exists():
                continue
            try:
                res = avaliar_questao(
                    tipo=tipo,
                    resposta_candidato=row["model_answer"] or "",
                    gabarito=row["answer"] or "",
                    criterios=row["formated_criteria"] or [],
                    backend=backend,
                    judge_model=judge_model,
                )
                p.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")
                log.info(f"q{qid} run{r} ok")
            except Exception as e:
                log.error(f"q{qid} run{r} erro: {e}")
            time.sleep(0.2)


def _juiz_chaves(df: pd.DataFrame, eval_dir: Path, tipo: str) -> pd.DataFrame:
    """Devolve dataframe long com [chave, acerto] consolidado via voto majoritário."""
    linhas = []
    for _, row in df.iterrows():
        qid = int(row["id"])
        runs_paths = sorted(eval_dir.glob(f"q{qid}_run*.json"))
        if not runs_paths:
            continue
        runs = [json.loads(p.read_text("utf-8")).get("resultado") or [] for p in runs_paths]
        consol = voto_majoritario(runs)
        for item in consol:
            if tipo == "discursive":
                k = chave(row["exam"], row["area"], row["number"], item.get("letra"), item.get("parte"))
            else:
                # Peças: 'numero' é o índice do critério dentro da rubrica, não a questão
                k = chave_pratica(row["exam"], row["area"], item.get("numero"), item.get("parte"))
            linhas.append({"chave": k, "acerto": int(item.get("acerto") or 0)})
    return pd.DataFrame(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="gpt-4o-mini")
    ap.add_argument("--backend", default="azure", choices=["azure", "groq"])
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--label", default=None, help="subdiretório para salvar (default: derivado de judge)")
    ap.add_argument("--recompute", action="store_true",
                    help="re-roda o juiz mesmo se já houver outputs")
    args = ap.parse_args()

    df_disc = pd.read_pickle(HUMAN_EXP / "df_discursive_answers_4o_mini.pkl")
    df_prac = pd.read_pickle(HUMAN_EXP / "df_legal_document_writing_4o_mini.pkl")

    label = args.label or args.judge.replace("/", "_").replace(":", "_")
    eval_out = EVAL_OUT.parent / f"alignment-{label}"
    out_disc = eval_out / "discursive"
    out_prac = eval_out / "document_writing"

    if args.recompute:
        for d in (out_disc, out_prac):
            if d.exists():
                for f in d.glob("*.json"):
                    f.unlink()

    print(f"[align] backend={args.backend} judge={args.judge} runs={args.runs}")
    print(f"[align] output: {eval_out}")
    _rodar_juiz(df_disc, "discursive", out_disc, args.runs, args.judge, args.backend)
    _rodar_juiz(df_prac, "document_writing", out_prac, args.runs, args.judge, args.backend)

    h_disc = carregar_anotacoes_humanas(ANNOT, tipo="discursivas")
    h_prac = carregar_anotacoes_humanas(ANNOT, tipo="praticas")

    j_disc = _juiz_chaves(df_disc, out_disc, "discursive")
    j_prac = _juiz_chaves(df_prac, out_prac, "document_writing")

    print("\n=== Alinhamento — DISCURSIVAS ===")
    print(json.dumps(relatorio_alinhamento(j_disc, h_disc), ensure_ascii=False, indent=2))
    print("\n=== Alinhamento — PEÇAS ===")
    print(json.dumps(relatorio_alinhamento(j_prac, h_prac), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
