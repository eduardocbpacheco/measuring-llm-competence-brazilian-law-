"""
Gera respostas do nosso modelo (MLX local — Tucano-OAB ou adaptadores)
para as 84 questões discursivas e 21 práticas do benchmark Rabula.

Saída: data/candidates/{M_label}/df_{discursive,document_writing}_answers.pkl
com colunas extras ['model_answer', 'reasoning'].
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

_ROOT = Path(__file__).resolve().parents[3]
DATA_BASE = Path(__file__).resolve().parents[1] / "data" / "base"
DATA_CAND = Path(__file__).resolve().parents[1] / "data" / "candidates"


# Prompt vem da FONTE ÚNICA (pipeline/prompt_padrao.py): estas constantes locais eram
# a 12ª e a 13ª variante do mesmo prompt no repositório, e prompt local é como a
# divergência treino/avaliação nasceu.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[3] / "pipeline"))
from prompt_padrao import system_de as _system_de

SYSTEM_DISCURSIVA = _system_de("discursiva")
SYSTEM_PECA = _system_de("peca")


def _carregar_mlx(model_dir: str, adapter_dir: str | None = None, adapter_file: str | None = None):
    """Se `adapter_file` for passado, copia-o temporariamente para adapters.safetensors
    no diretório do adapter (MLX-LM sempre lê esse nome). Usado para selecionar
    checkpoint específico (ex: iter 100 em vez do final overfittado)."""
    from mlx_lm import load
    import shutil

    if adapter_dir and adapter_file:
        src = Path(adapter_file)
        if not src.is_absolute():
            src = Path(adapter_dir) / src.name
        dst = Path(adapter_dir) / "adapters.safetensors"
        if not src.exists():
            raise FileNotFoundError(f"adapter_file não encontrado: {src}")
        # backup do adapters.safetensors atual (uma única vez)
        bk = dst.with_suffix(".safetensors.runner_backup")
        if dst.exists() and not bk.exists():
            shutil.copy2(dst, bk)
        if src.resolve() != dst.resolve():
            shutil.copy2(src, dst)
            log.info(f"Adapter pinned: {src.name} → adapters.safetensors")

    log.info(f"Carregando MLX: {model_dir}{' + adapter ' + adapter_dir if adapter_dir else ''}")
    if adapter_dir:
        model, tok = load(model_dir, adapter_path=adapter_dir)
    else:
        model, tok = load(model_dir)
    return model, tok


def _gerar_mlx(model, tok, system: str, user: str, max_tokens: int = 1500) -> str:
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_sampler

    if hasattr(tok, "apply_chat_template") and tok.chat_template:
        msgs = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    else:
        prompt = f"{system}\n\n{user}\n\nResposta:"

    sampler = make_sampler(temp=0.7, top_p=0.9)
    return generate(model, tok, prompt=prompt, max_tokens=max_tokens, sampler=sampler, verbose=False).strip()


def gerar_respostas(
    df: pd.DataFrame,
    tipo: str,
    model,
    tok,
    out_path: Path,
    resume: bool = True,
) -> pd.DataFrame:
    system = SYSTEM_DISCURSIVA if tipo == "discursive" else SYSTEM_PECA
    max_tok = 1500 if tipo == "discursive" else 3000

    if resume and out_path.exists():
        out_df = pd.read_pickle(out_path)
    else:
        out_df = df.copy()
        out_df["model_answer"] = pd.NA
        out_df["reasoning"] = pd.NA

    for ix, row in out_df.iterrows():
        if pd.notna(out_df.at[ix, "model_answer"]):
            continue
        try:
            resp = _gerar_mlx(model, tok, system, row["question"], max_tokens=max_tok)
            out_df.at[ix, "model_answer"] = resp
            log.info(f"[{tipo}] {ix + 1}/{len(out_df)} ok ({len(resp)} chars)")
        except Exception as e:
            log.error(f"[{tipo}] erro ix={ix}: {e}")
            out_df.at[ix, "model_answer"] = ""
        if (ix + 1) % 10 == 0:
            out_df.to_pickle(out_path)
    out_df.to_pickle(out_path)
    return out_df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="ex: M2_cpt-v1")
    ap.add_argument("--base-model", required=True, help="caminho ou repo HF do modelo base")
    ap.add_argument("--adapter", default=None, help="caminho do adapter LoRA (opcional)")
    ap.add_argument("--adapter-file", default=None, help="checkpoint específico .safetensors (opcional)")
    ap.add_argument("--tipos", default="discursive,document_writing",
                    help="discursive,document_writing")
    args = ap.parse_args()

    out_dir = DATA_CAND / args.label
    out_dir.mkdir(parents=True, exist_ok=True)

    model, tok = _carregar_mlx(args.base_model, args.adapter, args.adapter_file)

    tipos = args.tipos.split(",")
    if "discursive" in tipos:
        df_d = pd.read_pickle(DATA_BASE / "df_discursive.pkl")
        gerar_respostas(df_d, "discursive", model, tok, out_dir / "df_discursive_answers.pkl")
    if "document_writing" in tipos:
        df_p = pd.read_pickle(DATA_BASE / "df_practical.pkl")
        gerar_respostas(df_p, "document_writing", model, tok, out_dir / "df_document_writing_answers.pkl")

    log.info(f"Done. Saída em {out_dir}")


if __name__ == "__main__":
    main()
