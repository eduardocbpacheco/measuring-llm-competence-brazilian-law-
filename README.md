# Measuring the competence of LLMs in Brazilian law

*[Versão em português: `LEIAME.md`](LEIAME.md)*

Code and reproduction material for the paper of the same name, which measures 31 language
models in the **three roles** the standard evaluation arrangement involves, over the same
material: drafting a legal document, answering a discursive question, and judging what the
other models wrote.

The evaluation set is 105 questions from the second stage of the OAB Bar Exam, decomposed
into 940 criteria taken from the examining boards' official rubric, with a human gold
standard of 940 binary decisions by three legal experts. Agreement is reported by area of
law and, for document drafting, split into the two classes of criterion the board itself
labels.

**Eduardo Pacheco** · Institute of Mathematics and Computer Sciences, University of São
Paulo. Paper co-authored with Cibele Maria Russo.

## Start here

**[`REPRODUCING.md`](REPRODUCING.md)** walks the three stages and names the exact script for
each. Stage 3 needs **no GPU and no API key**: it recomputes every number, table and figure
in the paper from the deposited verdicts.

## What is here

| directory | what it holds |
|---|---|
| `pipeline/` | turning the examination PDFs into 105 questions and 940 criteria, and the form/substance grouping |
| `rabula/consolidado/` | running the benchmark: candidate answers, judging, alignment with the human gold standard |
| `avaliacao/` | agreement by area and by class of criterion, scoring, the statistical tests |
| `explorador/` | a local application to inspect each verdict beside the answer that produced it |
| `publicacao/` | the paper sources, Portuguese and English, and the IOS Press conversion |
| `dataset/` | freezing, the manifest with a checksum per file, packaging |

This is a curated selection, not the working archive. Only the path that produced what is in
the paper is here.

## Annotation and exploration

`explorador/` is a small local application, plain HTML, CSS and JavaScript served by Flask,
with no build step and no login. It has three views:

| view | what it does | needs |
|---|---|---|
| `/regua` | the agreement table of every judge by area of law, and the score of the same models as respondents, side by side and switchable by task | this paper's deposit |
| `/anotar` | **blind binary annotation**, to extend the human gold standard: it shows the case, the answer under evaluation and one criterion, and nothing else | this paper's deposit |
| `/condicoes` | compares two trained conditions on the same question, criterion by criterion | the companion paper's deposit |

Run `python explorador/app.py` and open the address it prints.

The annotation view is blind by construction: it never shows the official rubric item, any
judge's verdict, or another annotator's decision. Showing any of the three would turn
annotation into review, which measures something else. Decisions are written one per
annotator to `explorador/anotacoes/`, appended atomically.

The gold standard of 940 decisions already in the deposit was **inherited** from the Rabula
benchmark, collected before this work; `/anotar` is how it gets extended, not how it was
built. Everything downstream of it is here:
`rabula/consolidado/scripts/3_alignment_humano.py` aligns the three annotators with each
candidate judge, and `avaliacao/kappa_por_area.py` and `kappa_por_classe.py` open that
agreement by area of law and by class of criterion.

## The data

The verdicts are **not** in this repository. They are 47,869 files, about 180 MB, deposited
under a persistent identifier: **[10.5281/zenodo.22739161](https://doi.org/10.5281/zenodo.22739161)**.

The deposit carries the verdicts of the 31 candidate judges in up to 5 repetitions under
frozen code, the annotations of the three legal experts, and the 105 questions with their
940 criteria. `dataset/manifestos/benchmark-juizes.json` gives, for every file, its path,
size, line count and SHA-256.

The companion paper on what to train, and its own corpus and judgment deposits, is at
[github.com/eduardocbpacheco/synthetic-corpora-brazilian-law](https://github.com/eduardocbpacheco/synthetic-corpora-brazilian-law).
The two repositories share a small core, `avaliacao/nota.py` among it; they are separate
because the papers are read by different people for different reasons.

## Licence

Code under MIT (`LICENSE`). The deposited data under CC BY 4.0, with the gold standard
inherited from Rabula under the same terms.
