# Reproducing the paper

*[Versão em português: `REPRODUZIR.md`](REPRODUZIR.md)*

Scripts carry Portuguese names and Portuguese comments; that is the working language of the
project. This file and the other documents are in both languages.

Three stages. The first two need network access and paid API keys. The third needs neither,
and it is the one that produces **every number, table and figure in the paper** from the
deposited verdicts. If you want to check the results rather than rebuild the experiment, go
straight to stage 3.

```
pip install numpy pandas scipy scikit-learn matplotlib
```

---

## Stage 3 · Analysis, from the deposited verdicts

**Needs:** Python 3.11 and the packages above. No GPU, no API key.

**Input:** the deposit at [10.5281/zenodo.22739161](https://doi.org/10.5281/zenodo.22739161),
unpacked into this repository so that three directories exist:

```
rabula/consolidado/data/evaluations_v4/     ← from the deposit's vereditos/
rabula/consolidado/data/annotations/        ← from the deposit's golden/
rabula/Reconstrucao/LLM-as-judge-in-BR-legal-domain/data/dfs/human_alignment_experiment/
                                            ← from the deposit's questoes/
```

The third holds the 105 questions with their 940 criteria, as two pandas frames, one per
genre. The verdict files identify a criterion by position, so without it the verdicts cannot
be read.

```bash
python dataset/congela.py --conferir          # the files are the ones the manifest describes
python avaliacao/kappa_por_area.py            # agreement by area of law × task → kappa_area.json
python avaliacao/kappa_por_classe.py          # agreement split into form and substance
python publicacao/artigo2_en/tabelas.py       # recomputes Tables 2 to 5
python publicacao/artigo2_en/figura_papeis.py # recomputes Figure 1
```

`kappa_por_area.py` writes to `/tmp/kappa_area.json`; the two scripts after it read from
there. Set `KAPPA_AREA` to another path if `/tmp` does not suit you, and the three agree.

`avaliacao/nota.py` is the single scoring function. It weights each criterion by the points
the examining board assigns to it, and it never aggregates the two task genres. Every table
in the paper comes from it; none is transcribed by hand.
`avaliacao/statistical_tests.py` holds the paired tests, the resampling intervals and
Steiger's test for dependent correlations, which Section 4.4 reports.

`explorador/` puts each verdict beside the answer that produced it, which is the fastest way
to see what a given κ actually consists of. Run `python explorador/app.py` and open the
address it prints.

---

## Stage 1 · Building the evaluation set

**Needs:** network access and the Bar Exam PDFs.

`pipeline/parse_oab_pdfs.py` turns the examinations and their official rubrics into
structured records. `pipeline/monta_benchmark_v2.py` assembles the 105 questions and the 940
criteria, and is also **where the form/substance grouping of document-drafting criteria is
defined**: the titles come from the examining board, the grouping of those titles into two
families is ours, and it lives in that file.
`pipeline/prompt_padrao.py` is the formulation given to every respondent.

## Stage 2 · Running the benchmark

**Needs:** API keys for the candidate models and for the judges.

```bash
python rabula/consolidado/scripts/1_make_candidate_answers.py   # each model answers the 105 questions
python rabula/consolidado/scripts/2_run_judges.py               # each candidate judge issues verdicts
python rabula/consolidado/scripts/3_alignment_humano.py         # aligns verdicts with the 3 annotators
python rabula/consolidado/scripts/4_scoreboard_final.py         # the scoreboard of respondents
python rabula/consolidado/scripts/5_juizes_kappa.py             # Cohen's agreement per candidate judge
```

`src/judge_llm.py` holds the judging client and the majority vote, `src/prompts.py` the
formulation given to every judge, `src/alignment.py` the loading of the human annotations,
`src/candidate_runner.py` the generation of answers and `src/scoreboard.py` the scoring.
`avaliacao/julga_rabula.py` is the variant used in production, with `judge.py` as the client
and `benchmark_schema.py` as the contract of the expected response.

The protocol repeats the whole thing up to 5 times per candidate with the code frozen. That
repetition is what makes the noise floor of Section 4.2 measurable, and it is the reason the
deposit carries five directories of verdicts instead of one.

---

## The manuscript

`tabelas.py` recomputes the tables from the data, `figura_papeis.py` the figure,
`monta_artigo.py` assembles the HTML, and a converter in `publicacao/jurix/` produces the
IOS Press format the conference requires.

| language | sources | converter |
|---|---|---|
| English | `publicacao/artigo2_en/` | `publicacao/jurix/para_tex_2en.py` |
| Portuguese | `publicacao/artigo2/` | `publicacao/jurix/para_tex_2.py` |

The English tables and figure import the Portuguese modules and replace only the labels, so
the two versions cannot diverge in their numbers.

## What is deliberately absent

The interface used to collect the human annotations, which belongs to the Rabula study, and
the working archive of superseded scripts. `publicacao/monta_repo_benchmark.py` is what
assembles this repository: it refuses to include a file whose name or content matches a
credential pattern, and it refuses to finish if any included script imports a module that was
left out.
