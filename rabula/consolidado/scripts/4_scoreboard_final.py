#!/usr/bin/env python3
"""
Gera scoreboard final agregando os juízes sobre M1..M6 (ou modelos passados via CLI).

Saída:
    data/scoreboard_final.csv
    data/scoreboard_final.pkl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scoreboard import scoreboard_modelo  # noqa: E402

DATA_BASE = ROOT / "data" / "base"
DATA_EVAL = ROOT / "data" / "evaluations"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelos", default="M1,M2,M3,M4,M5,M6")
    ap.add_argument("--by-area", action="store_true", default=True)
    args = ap.parse_args()

    df_disc = pd.read_pickle(DATA_BASE / "df_discursive.pkl")
    df_prac = pd.read_pickle(DATA_BASE / "df_practical.pkl")

    out = []
    for label in args.modelos.split(","):
        avd = DATA_EVAL / label
        if not avd.exists():
            print(f"[skip] sem avaliações em {avd}")
            continue
        sb = scoreboard_modelo(label, avd, df_disc, df_prac, by_area=args.by_area)
        out.append(sb)

    if not out:
        sys.exit("Nenhum modelo avaliado — rode antes scripts/2_run_judges.py")

    final = pd.concat(out, ignore_index=True)
    final["id"] = range(1, len(final) + 1)
    print(final.to_string(index=False))

    out_csv = ROOT / "data" / "scoreboard_final.csv"
    out_pkl = ROOT / "data" / "scoreboard_final.pkl"
    final.to_csv(out_csv, index=False)
    final.to_pickle(out_pkl)
    print(f"\n→ {out_csv}")
    print(f"→ {out_pkl}")


if __name__ == "__main__":
    main()
