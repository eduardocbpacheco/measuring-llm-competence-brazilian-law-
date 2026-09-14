#!/usr/bin/env python3
"""
Roda o juiz Rabula-style sobre as respostas de um modelo-candidato.
Faz N runs por questão e salva cada run separadamente (para análise de variância).

Saída: data/evaluations/{label}/{discursive,document_writing}/q{id}_run{r}.json
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

from judge_llm import avaliar_questao  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("run_judges")

DATA_CAND = ROOT / "data" / "candidates"
DATA_EVAL = ROOT / "data" / "evaluations"


def _run_um_tipo(
    df_answers: pd.DataFrame,
    tipo: str,
    out_dir: Path,
    n_runs: int,
    judge_model: str,
    resume: bool = True,
    sleep: float = 0.2,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(df_answers) * n_runs
    feitos = 0
    inicio = time.time()

    for _, row in df_answers.iterrows():
        qid = int(row["id"])
        resposta = (row.get("model_answer") or "").strip()
        if not resposta:
            log.warning(f"[{tipo}] q{qid} sem model_answer — pulando")
            continue
        gabarito = row.get("answer") or ""
        criterios = row.get("formated_criteria") or []

        for r in range(n_runs):
            out_path = out_dir / f"q{qid}_run{r}.json"
            if resume and out_path.exists():
                feitos += 1
                continue
            try:
                result = avaliar_questao(
                    tipo=tipo,
                    resposta_candidato=resposta,
                    gabarito=gabarito,
                    criterios=criterios,
                    backend="azure",
                    judge_model=judge_model,
                )
                out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
                feitos += 1
                eta = (time.time() - inicio) / max(feitos, 1) * (total - feitos)
                log.info(f"[{tipo}] q{qid} run{r} ok | {feitos}/{total} | ETA {eta/60:.1f}min")
            except Exception as e:
                log.error(f"[{tipo}] q{qid} run{r} erro: {e}")
            time.sleep(sleep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True, help="label do modelo (ex: M2, M6)")
    ap.add_argument("--judge", default="gpt-4o-mini", help="modelo juiz (deployment name)")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--tipos", default="discursive,document_writing")
    args = ap.parse_args()

    cand_dir = DATA_CAND / args.candidate
    eval_dir = DATA_EVAL / args.candidate
    if not cand_dir.exists():
        sys.exit(f"Sem respostas em {cand_dir} — rode antes scripts/1_make_candidate_answers.py")

    tipos = args.tipos.split(",")
    for tipo in tipos:
        ans_path = cand_dir / (
            "df_discursive_answers.pkl" if tipo == "discursive" else "df_document_writing_answers.pkl"
        )
        if not ans_path.exists():
            log.warning(f"sem {ans_path} — pulando {tipo}")
            continue
        df = pd.read_pickle(ans_path)
        log.info(f"=== {tipo} | {len(df)} questões × {args.runs} runs ===")
        _run_um_tipo(df, tipo, eval_dir / tipo, args.runs, judge_model=args.judge)


if __name__ == "__main__":
    main()
