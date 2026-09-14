#!/usr/bin/env python3
"""
Atalho para gerar respostas dos nossos modelos M1..M6.
Internamente chama src/candidate_runner.py.

Uso:
    python scripts/1_make_candidate_answers.py M2
    python scripts/1_make_candidate_answers.py M6 --base-model models/tucano-cpt-v3-fused --adapter adapters/finetune-v4
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT.parents[1]  # raiz do projeto

DEFAULTS = {
    "M1": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": None,                                            "adapter_file": None},
    "M2": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "pretrain-v1"),          "adapter_file": None},
    # M3: checkpoint iter 100 (final overfittou)
    "M3": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v1"),          "adapter_file": "0000100_adapters.safetensors"},
    "M4": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v2"),          "adapter_file": None},
    "M5": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v3"),          "adapter_file": None},
    "M6": {"base": str(PROJ / "models" / "tucano-cpt-v3-fused"), "adapter": str(PROJ / "adapters" / "finetune-v4"),    "adapter_file": None},
    # M7: CPT v4 puro (sem SFT). Usa checkpoint iter 700 (val 0.697, melhor da série).
    "M7": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "pretrain-v4"), "adapter_file": "0000700_adapters.safetensors"},
    # M8: CPT v4 + SFT v5. Usa checkpoint iter 400 do SFT (val 1.099, melhor).
    "M8": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v5"), "adapter_file": "0000400_adapters.safetensors"},
    # M9: CPT v6 (MLP+attn) + SFT v6 (MLP+attn). Adapter HF/PEFT convertido para MLX.
    "M9": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v6-mlp-mlx"), "adapter_file": None},
    # M10: CPT v7 (rank 64, 36 layers) + SFT v7 — retreinando (ckpt v1 corrompeu por falta de disco)
    "M10": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v7-r64-mlx"), "adapter_file": None},
    # M11: CPT v8 (+embed+lm_head) + SFT v8. Adapter HF/PEFT convertido para MLX.
    "M11": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v8-embedlm-mlx"), "adapter_file": None},
    # M12: H14 (val 0.5903 — best CPT) + SFT v9 (receita ótima: MLP + embed + lm_head + max_seq=4096)
    "M12": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v9-h14-mlx"), "adapter_file": None},
    # M13: H7 (val 0.5973) + SFT v9 (receita ótima: MLP + embed + lm_head + max_seq=4096)
    "M13": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v9-h7-mlx"), "adapter_file": None},
    # M14: H11 (CPT v6 estendido) + SFT v9
    "M14": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v9-h11-mlx"), "adapter_file": None},
    # M15: H12 (rank 128) + SFT v9 — best eval (1.060)
    "M15": {"base": "Polygl0t/Tucano2-qwen-3.7B-Instruct", "adapter": str(PROJ / "adapters" / "finetune-v9-h12-mlx"), "adapter_file": None},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modelo", choices=list(DEFAULTS) + ["custom"])
    ap.add_argument("--base-model", default=None)
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--label", default=None)
    ap.add_argument("--tipos", default="discursive,document_writing")
    args = ap.parse_args()

    if args.modelo == "custom":
        if not args.base_model or not args.label:
            sys.exit("custom requires --base-model and --label")
        base = args.base_model
        adapter = args.adapter
        adapter_file = None
        label = args.label
    else:
        cfg = DEFAULTS[args.modelo]
        base = args.base_model or cfg["base"]
        adapter = args.adapter or cfg["adapter"]
        adapter_file = cfg.get("adapter_file")
        label = args.label or args.modelo

    cmd = [
        sys.executable,
        str(ROOT / "src" / "candidate_runner.py"),
        "--label", label,
        "--base-model", base,
        "--tipos", args.tipos,
    ]
    if adapter:
        cmd += ["--adapter", adapter]
    if adapter_file:
        cmd += ["--adapter-file", adapter_file]

    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
