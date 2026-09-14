#!/usr/bin/env python3
"""
Roda alinhamento para múltiplos juízes (Bedrock + Azure + Groq já testados).
Compila DataFrame final com κ Cohen vs golden humano (discursivas + peças).

Saída: dashboard/kappa_juizes.pkl + .csv
"""
from __future__ import annotations
import argparse, json, os, threading, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alignment import carregar_anotacoes_humanas, relatorio_alinhamento  # noqa: E402
from judge_llm import avaliar_questao, voto_majoritario  # noqa: E402

DATA = ROOT / "data"
ANNOT = DATA / "annotations"
HUMAN_EXP = ROOT.parent / "Reconstrucao" / "LLM-as-judge-in-BR-legal-domain" / "data" / "dfs" / "human_alignment_experiment"
EVAL_OUT_BASE = Path(os.environ.get("EVAL_OUT_BASE", DATA / "evaluations"))


def chave_disc(exame, area, numero, letra, parte):
    return f"exame_{exame}_area_{area}_questao_numero_{numero}_letra_{letra}_parte_{parte}"


def chave_pratica(exame, area, numero, parte):
    return f"exame_{exame}_area_{area}_questao_numero_{numero}_parte_{parte}"


def _rodar_juiz(df, tipo, out_dir, n_runs, backend, judge_model, workers=8):
    """Roda as (questão × run) do juiz em paralelo.

    Era sequencial com sleep(0.2): 315 chamadas de ~20s em fila dão ~1,7h POR JUIZ, e
    com 26 juízes isso é uma semana. O teto real não é a serialização e sim o RPM do
    modelo (100 na maioria, 5-10 nos Claude), e cada modelo tem cota própria — então
    paralelizar dentro do juiz é o que estava sobrando na mesa.

    Um arquivo por (questão, run) mantém o resume intacto: relançar só refaz o que falta.
    Quem estoura RPM cai no backoff com jitter do judge_llm, que agora tenta 6 vezes.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    tarefas = []
    for _, row in df.iterrows():
        qid = int(row["id"])
        for r in range(n_runs):
            alvo = out_dir / f"q{qid}_run{r}.json"
            if not alvo.exists():
                tarefas.append((qid, r, alvo, row))
    if not tarefas:
        print(f"  [{tipo}] nada pendente")
        return

    ok = falha = 0
    lock = threading.Lock()
    t0 = time.time()

    def uma(t):
        qid, r, alvo, row = t
        res = avaliar_questao(
            tipo=tipo,
            resposta_candidato=row.get("model_answer") or "",
            gabarito=row.get("answer") or "",
            criterios=row.get("formated_criteria") or [],
            backend=backend, judge_model=judge_model,
        )
        alvo.write_text(json.dumps(res, ensure_ascii=False, indent=2), "utf-8")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(uma, t): t for t in tarefas}
        for fut in as_completed(futs):
            qid, r, _, _ = futs[fut]
            try:
                fut.result()
                with lock:
                    ok += 1
            except Exception as e:
                with lock:
                    falha += 1
                    print(f"  [{tipo}] q{qid} run{r} ERRO: {type(e).__name__}: {str(e)[:100]}",
                          flush=True)
            if (ok + falha) % 25 == 0:
                dt = time.time() - t0
                print(f"  [{tipo}] {ok+falha}/{len(tarefas)} · {dt/60:.0f}min · "
                      f"falhas {falha}", flush=True)
    print(f"  [{tipo}] {ok} ok · {falha} falhas · {(time.time()-t0)/60:.0f}min", flush=True)


def _juiz_chaves(df, eval_dir, tipo):
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
                k = chave_disc(row["exam"], row["area"], row["number"], item.get("letra"), item.get("parte"))
            else:
                k = chave_pratica(row["exam"], row["area"], item.get("numero"), item.get("parte"))
            linhas.append({"chave": k, "acerto": int(item.get("acerto") or 0)})
    return pd.DataFrame(linhas)


def _carimbo(destino: Path, judge_label: str, backend: str, model_id: str, runs: int) -> None:
    """Grava a proveniência da medição junto com ela.

    Sem isto não há como, semanas depois, distinguir uma diferença de κ causada por
    mudança no nosso código de uma causada por mudança do modelo. Foi exatamente o que
    aconteceu entre junho e agosto de 2026: o κ se moveu e as duas explicações ficaram
    confundidas, o que inutilizou a comparação.

    O que NÃO dá para carimbar: a versão dos pesos. O Bedrock serve `moonshotai.kimi-k2.5`
    sob um ID estável e não expõe versão, então deriva silenciosa do provedor permanece
    inobservável. Isso é limitação da plataforma e vai declarada no artigo.
    """
    import hashlib, datetime
    def h(caminho: Path) -> str:
        return hashlib.sha256(caminho.read_bytes()).hexdigest()[:16]
    src = ROOT / "src"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "_proveniencia.json").write_text(json.dumps({
        "juiz": judge_label, "backend": backend, "model_id": model_id, "runs": runs,
        "quando": datetime.datetime.now().isoformat(timespec="seconds"),
        "sha_judge_llm": h(src / "judge_llm.py"),
        "sha_prompts": h(src / "prompts.py"),
        "sha_script": h(Path(__file__)),
        "aviso": "o provedor nao expoe versao dos pesos; deriva silenciosa e inobservavel",
    }, indent=2, ensure_ascii=False), "utf-8")


def aval_juiz(judge_label, backend, model_id, runs=3, workers=8):
    df_disc = pd.read_pickle(HUMAN_EXP / "df_discursive_answers_4o_mini.pkl")
    df_prac = pd.read_pickle(HUMAN_EXP / "df_legal_document_writing_4o_mini.pkl")

    out_dir = EVAL_OUT_BASE / f"alignment-{judge_label}"
    out_disc = out_dir / "discursive"
    out_prac = out_dir / "document_writing"

    print(f"\n=== {judge_label} ({backend}/{model_id}) ===")
    print(f"output: {out_dir}")
    _carimbo(out_dir, judge_label, backend, model_id, runs)

    _rodar_juiz(df_disc, "discursive", out_disc, runs, backend, model_id, workers)
    _rodar_juiz(df_prac, "document_writing", out_prac, runs, backend, model_id, workers)

    h_disc = carregar_anotacoes_humanas(ANNOT, tipo="discursivas")
    h_prac = carregar_anotacoes_humanas(ANNOT, tipo="praticas")

    j_disc = _juiz_chaves(df_disc, out_disc, "discursive")
    j_prac = _juiz_chaves(df_prac, out_prac, "document_writing")

    rep_disc = relatorio_alinhamento(j_disc, h_disc) if not j_disc.empty else {}
    rep_prac = relatorio_alinhamento(j_prac, h_prac) if not j_prac.empty else {}

    return {
        "judge": judge_label,
        "backend": backend,
        "model_id": model_id,
        "disc_n_itens": rep_disc.get("n_itens"),
        "disc_acuracia": rep_disc.get("acuracia_vs_golden"),
        "disc_kappa": rep_disc.get("kappa_juiz_vs_golden"),
        "pec_n_itens": rep_prac.get("n_itens"),
        "pec_acuracia": rep_prac.get("acuracia_vs_golden"),
        "pec_kappa": rep_prac.get("kappa_juiz_vs_golden"),
        "humanos_fleiss": rep_disc.get("kappa_humanos_fleiss"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--only", default=None, help="só rodar estes labels (comma-separated)")
    ap.add_argument("--workers", type=int, default=8,
                    help="chamadas em paralelo por juiz. Cada modelo tem RPM próprio, "
                         "então paralelizar aqui não rouba cota de outro juiz")
    args = ap.parse_args()

    juizes = [
        # Bedrock
        ("nova-pro",       "bedrock", "amazon.nova-pro-v1:0"),
        ("nova-lite",      "bedrock", "amazon.nova-lite-v1:0"),
        ("nova-micro",     "bedrock", "amazon.nova-micro-v1:0"),
        ("llama3-70b",     "bedrock", "meta.llama3-70b-instruct-v1:0"),
        ("llama3-8b",      "bedrock", "meta.llama3-8b-instruct-v1:0"),
        ("mistral-large",  "bedrock", "mistral.mistral-large-2402-v1:0"),
        ("mistral-l3-675b","bedrock", "mistral.mistral-large-3-675b-instruct"),
        ("mistral-small",  "bedrock", "mistral.mistral-small-2402-v1:0"),
        # Inference profiles (cross-region) — Llama 3.2 90B bloqueado (Legacy), substituído por 3.3 e Llama 4
        ("llama4-scout",   "bedrock", "us.meta.llama4-scout-17b-instruct-v1:0"),
        ("llama3-3-70b",   "bedrock", "us.meta.llama3-3-70b-instruct-v1:0"),
        ("llama4-maverick","bedrock", "us.meta.llama4-maverick-17b-instruct-v1:0"),
        # Novos candidatos a juiz (também são geradores Apache 2.0/MIT)
        ("deepseek-v3",    "bedrock", "deepseek.v3.2"),
        ("qwen3-235b-vl",  "bedrock", "qwen.qwen3-vl-235b-a22b"),
        ("qwen3-32b",      "bedrock", "qwen.qwen3-32b-v1:0"),
        ("qwen3-80b-a3b",  "bedrock", "qwen.qwen3-next-80b-a3b"),
        ("mixtral-8x7b",   "bedrock", "mistral.mixtral-8x7b-instruct-v0:1"),
        # Wave 2 — 2026-06-12
        ("gpt-oss-120b",   "bedrock", "openai.gpt-oss-120b-1:0"),
        ("glm-5",          "bedrock", "zai.glm-5"),
        ("kimi-k2-5",      "bedrock", "moonshotai.kimi-k2.5"),
        ("magistral-small","bedrock", "mistral.magistral-small-2509"),
        # Wave 3 — 2026-08-21. A limitação nº 5 do estudo de junho era "sem Claude
        # testado, Anthropic bloqueado em Bedrock para esta conta". Deixou de ser: Opus
        # 4.5 e 4.6 respondem por perfil cross-region (testado em 21/08). Opus 5,
        # Sonnet 5 e Fable 5 aparecem na listagem mas dão AccessDenied, e Sonnet 4.5/4.6
        # dão ResourceNotFound — ficam de fora até serem liberados.
        # Cota dos Claude é de 5-10 RPM cross-region, então cada um leva ~1h aqui. É
        # aceitável: são 315 chamadas, uma vez.
        ("claude-opus-4-6","bedrock", "us.anthropic.claude-opus-4-6-v1"),
        ("claude-opus-4-5","bedrock", "us.anthropic.claude-opus-4-5-20251101-v1:0"),
        # Liberados às 20h45 de 21/08, depois que o formulário de use case da Anthropic
        # foi registrado na conta. Antes disso os cinco davam ResourceNotFound.
        # Seguem FORA por indisponibilidade na conta ("not available for this account",
        # que pede contato com o AWS Sales): Fable 5, Opus 5, Opus 4.7, Opus 4.8,
        # Sonnet 5, Grok 4.6 e a família GPT-5.6.
        ("claude-sonnet-4-6","bedrock", "us.anthropic.claude-sonnet-4-6"),
        ("claude-sonnet-4-5","bedrock", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
        ("claude-haiku-4-5","bedrock", "us.anthropic.claude-haiku-4-5-20251001-v1:0"),
        # Maritaca — os únicos treinados PARA português no elenco. Todos os outros 22 são
        # multilíngues de propósito geral, então esta é a única linha da tabela que
        # responde se especialização em idioma compra alinhamento com anotador brasileiro.
        # (Sabiá-4 Thinking fica para depois: cobra o raciocínio como saída.)
        ("sabia-4",        "maritaca", "sabia-4"),
        ("sabiazinho-4",   "maritaca", "sabiazinho-4"),
        # O gargalo do estudo de junho é PEÇA (Δ disc→peças = -0,18 κ). Estes entram
        # sobretudo para atacar esse lado: contexto longo e muitos critérios.
        ("kimi-k2-thinking","bedrock","moonshot.kimi-k2-thinking"),
        ("glm-4-7",        "bedrock", "zai.glm-4.7"),
        ("minimax-m2-5",   "bedrock", "minimax.minimax-m2.5"),
        ("nemotron-s3-120b","bedrock","nvidia.nemotron-super-3-120b"),
    ]
    # Para alinhar: gpt-4o e gpt-4o-mini já temos dados (alignment-gpt-4o, alignment-gpt-4o-mini implicit)

    only_set = set(args.only.split(",")) if args.only else None
    resultados = []
    for label, backend, mid in juizes:
        if only_set and label not in only_set:
            continue
        try:
            r = aval_juiz(label, backend, mid, args.runs, args.workers)
            resultados.append(r)
        except Exception as e:
            print(f"  ❌ {label}: {e}")

    # Adicionar gpt-4o e gpt-4o-mini se existirem
    for label_existe, backend_aux, mid_aux in [
        ("gpt-4o", "azure", "gpt-4o-qa-hml"),
        ("gpt-4o-mini", "azure", "gpt-4o-mini-qa-hml"),
        ("llama-3.3-70b", "groq", "llama-3.3-70b-versatile"),
    ]:
        d = EVAL_OUT_BASE / f"alignment-{label_existe}"
        if not (d / "discursive").exists():
            continue
        # Re-compila kappa para uniformidade
        df_disc = pd.read_pickle(HUMAN_EXP / "df_discursive_answers_4o_mini.pkl")
        df_prac = pd.read_pickle(HUMAN_EXP / "df_legal_document_writing_4o_mini.pkl")
        h_disc = carregar_anotacoes_humanas(ANNOT, tipo="discursivas")
        h_prac = carregar_anotacoes_humanas(ANNOT, tipo="praticas")
        j_disc = _juiz_chaves(df_disc, d / "discursive", "discursive")
        j_prac = _juiz_chaves(df_prac, d / "document_writing", "document_writing")
        rd = relatorio_alinhamento(j_disc, h_disc) if not j_disc.empty else {}
        rp = relatorio_alinhamento(j_prac, h_prac) if not j_prac.empty else {}
        resultados.append({
            "judge": label_existe, "backend": backend_aux, "model_id": mid_aux,
            "disc_n_itens": rd.get("n_itens"), "disc_acuracia": rd.get("acuracia_vs_golden"),
            "disc_kappa": rd.get("kappa_juiz_vs_golden"),
            "pec_n_itens": rp.get("n_itens"), "pec_acuracia": rp.get("acuracia_vs_golden"),
            "pec_kappa": rp.get("kappa_juiz_vs_golden"),
            "humanos_fleiss": rd.get("kappa_humanos_fleiss"),
        })

    df = pd.DataFrame(resultados)
    if not df.empty:
        # ordenação por média dos kappas
        df["kappa_media"] = df[["disc_kappa", "pec_kappa"]].mean(axis=1)
        df = df.sort_values("kappa_media", ascending=False).reset_index(drop=True)

    out_pkl = ROOT.parent.parent / "dashboard" / "kappa_juizes.pkl"
    out_csv = ROOT.parent.parent / "dashboard" / "kappa_juizes.csv"
    out_pkl.parent.mkdir(exist_ok=True)
    df.to_pickle(out_pkl)
    df.to_csv(out_csv, index=False)
    print(f"\n✅ Salvo: {out_pkl}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
