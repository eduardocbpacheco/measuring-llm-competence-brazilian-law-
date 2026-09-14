#!/usr/bin/env python3
"""monta_repo_benchmark.py — a pasta pública do artigo do benchmark.

Repositório separado do artigo do corpus, por decisão de projeto: são dois artigos com
públicos e ciclos distintos, e misturar o código dos dois obriga o leitor de um a atravessar
o do outro. O preço é que o núcleo compartilhado aparece nos dois repositórios; é
duplicação, e é consciente.

Reaproveita a varredura de segredo e o fecho de imports de `monta_repo.py`, que são o que
torna a publicação segura; troca apenas a lista de conteúdo e o destino.

    python publicacao/monta_repo_benchmark.py
    python publicacao/monta_repo_benchmark.py --so-varrer
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import monta_repo as M

RAIZ = M.RAIZ
M.DESTINO = RAIZ.parent / "benchmark-juridico-publicacao"
M.PASTA_RAIZ = RAIZ / "publicacao/repo_benchmark"

M.CONTEUDO = [
    # ── 1 · o conjunto de avaliação
    ("pipeline", "parse_oab_pdfs.py"),       # provas e espelhos a partir dos PDFs
    ("pipeline", "monta_benchmark_v2.py"),   # as 105 questões, os 940 critérios, forma/mérito
    ("pipeline", "prompt_padrao.py"),        # a formulação dada a quem responde

    # ── 2 · rodar o benchmark
    ("rabula/consolidado/src", "__init__.py"),
    ("rabula/consolidado/src", "alignment.py"),      # carrega as anotações dos três juristas
    ("rabula/consolidado/src", "judge_llm.py"),      # cliente de julgamento e voto majoritário
    ("rabula/consolidado/src", "prompts.py"),
    ("rabula/consolidado/src", "candidate_runner.py"),
    ("rabula/consolidado/src", "scoreboard.py"),
    ("rabula/consolidado/scripts", "1_make_candidate_answers.py"),
    ("rabula/consolidado/scripts", "2_run_judges.py"),
    ("rabula/consolidado/scripts", "3_alignment_humano.py"),
    ("rabula/consolidado/scripts", "4_scoreboard_final.py"),
    ("rabula/consolidado/scripts", "5_juizes_kappa.py"),
    ("avaliacao", "julga_rabula.py"), ("avaliacao", "judge.py"),
    ("avaliacao", "benchmark_schema.py"),

    # ── 3 · análise, sem GPU e sem chave
    ("avaliacao", "nota.py"),                # a única função de nota do projeto
    ("avaliacao", "analisa_kappa_v4.py"),    # a calibração contra o padrão-ouro
    ("avaliacao", "kappa_por_area.py"),      # concordância por área do direito
    ("avaliacao", "kappa_por_classe.py"),    # concordância aberta em forma e mérito
    ("avaliacao", "statistical_tests.py"),

    # ── 4 · explorar os resultados
    ("explorador", "*.py"), ("explorador/static", "*"),

    # ── 5 · o manuscrito
    ("publicacao/artigo2", "corpo_*.html"), ("publicacao/artigo2", "tabelas.py"),
    ("publicacao/artigo2", "figura_papeis.py"), ("publicacao/artigo2", "monta_artigo.py"),
    ("publicacao/artigo2", "estilo.css"), ("publicacao/artigo2", "papeis.pdf"),
    ("publicacao/artigo2_en", "corpo_*.html"), ("publicacao/artigo2_en", "tabelas.py"),
    ("publicacao/artigo2_en", "figura_papeis.py"), ("publicacao/artigo2_en", "monta_artigo.py"),
    ("publicacao/artigo2_en", "estilo.css"), ("publicacao/artigo2_en", "papeis.pdf"),
    # `para_tex_2*.py` são casca fina sobre `para_tex*.py`, que por isso vêm junto.
    ("publicacao/jurix", "para_tex.py"), ("publicacao/jurix", "para_tex_en.py"),
    ("publicacao/jurix", "para_tex_2.py"), ("publicacao/jurix", "para_tex_2en.py"),
    ("publicacao/jurix", "artigo2.tex"), ("publicacao/jurix", "artigo2_en.tex"),
    ("publicacao/jurix", "artigo2.pdf"), ("publicacao/jurix", "artigo2_en.pdf"),
    ("publicacao/jurix", "*.cls"), ("publicacao/jurix", "*.bst"),

    # ── ferramentas
    ("dataset", "congela.py"), ("dataset", "depositos.py"), ("dataset", "empacota.py"),
    ("dataset/manifestos", "benchmark-juizes.json"),
    ("publicacao", "monta_repo.py"), ("publicacao", "monta_repo_benchmark.py"),
]

if __name__ == "__main__":
    M.main()
