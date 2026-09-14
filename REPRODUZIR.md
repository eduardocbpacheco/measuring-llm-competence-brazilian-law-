# Reproduzir o artigo

*[English version: `REPRODUCING.md`](REPRODUCING.md)*

Os scripts têm nome e comentário em português, que é a língua de trabalho do projeto. Este
arquivo e os demais documentos estão nas duas línguas.

Três etapas. As duas primeiras precisam de acesso à rede e de chaves de API pagas. A terceira
não precisa de nenhuma das duas, e é ela que produz **todos os números, tabelas e figuras do
artigo** a partir dos vereditos depositados. Se o que você quer é conferir os resultados, e
não refazer o experimento, vá direto à etapa 3.

```
pip install numpy pandas scipy scikit-learn matplotlib
```

---

## Etapa 3 · Análise, a partir dos vereditos depositados

**Precisa de:** Python 3.11 e os pacotes acima. Sem GPU, sem chave de API.

**Entrada:** o depósito em [10.5281/zenodo.22739161](https://doi.org/10.5281/zenodo.22739161),
descompactado dentro deste repositório de modo que existam três diretórios:

```
rabula/consolidado/data/evaluations_v4/     ← do vereditos/ do depósito
rabula/consolidado/data/annotations/        ← do golden/ do depósito
rabula/Reconstrucao/LLM-as-judge-in-BR-legal-domain/data/dfs/human_alignment_experiment/
                                            ← do questoes/ do depósito
```

O terceiro guarda as 105 questões com os seus 940 critérios, em duas tabelas pandas, uma por
gênero. Os arquivos de veredito identificam o critério por posição, então sem ele os
vereditos não podem ser lidos.

```bash
python dataset/congela.py --conferir           # os arquivos são os que o manifesto descreve
python avaliacao/kappa_por_area.py             # concordância por área × tarefa → kappa_area.json
python avaliacao/kappa_por_classe.py           # concordância aberta em forma e mérito
python publicacao/artigo2/tabelas.py           # recomputa as Tabelas 2 a 5
python publicacao/artigo2/figura_papeis.py     # recomputa a Figura 1
```

`kappa_por_area.py` grava em `/tmp/kappa_area.json`; os dois scripts seguintes leem de lá.
Aponte `KAPPA_AREA` para outro caminho se `/tmp` não servir, e os três concordam.

`avaliacao/nota.py` é a única função de nota. Ela pondera cada critério pela pontuação que a
banca lhe atribui, e nunca agrega os dois gêneros de tarefa. Toda tabela do artigo sai dela;
nenhuma é transcrita à mão. `avaliacao/statistical_tests.py` guarda os testes pareados, os
intervalos por reamostragem e o teste de Steiger para correlações dependentes, que a Seção
4.4 reporta.

`explorador/` põe cada veredito ao lado da resposta que o gerou, que é o jeito mais rápido de
ver em que um dado κ de fato consiste. Rode `python explorador/app.py` e abra o endereço que
ele imprime.

---

## Etapa 1 · Construir o conjunto de avaliação

**Precisa de:** acesso à rede e os PDFs do Exame de Ordem.

`pipeline/parse_oab_pdfs.py` transforma as provas e os espelhos oficiais em registros
estruturados. `pipeline/monta_benchmark_v2.py` monta as 105 questões e os 940 critérios, e é
também **onde o agrupamento forma/mérito dos critérios de peça está definido**: os títulos vêm
da banca, o agrupamento desses títulos em duas famílias é nosso, e mora nesse arquivo.
`pipeline/prompt_padrao.py` é a formulação dada a todos os respondentes.

## Etapa 2 · Rodar o benchmark

**Precisa de:** chaves de API dos modelos candidatos e dos juízes.

```bash
python rabula/consolidado/scripts/1_make_candidate_answers.py   # cada modelo responde as 105 questões
python rabula/consolidado/scripts/2_run_judges.py               # cada juiz candidato emite vereditos
python rabula/consolidado/scripts/3_alignment_humano.py         # alinha vereditos com os 3 anotadores
python rabula/consolidado/scripts/4_scoreboard_final.py         # o placar dos respondentes
python rabula/consolidado/scripts/5_juizes_kappa.py             # concordância de Cohen por juiz candidato
```

`src/judge_llm.py` guarda o cliente de julgamento e o voto majoritário, `src/prompts.py` a
formulação dada a todos os juízes, `src/alignment.py` o carregamento das anotações humanas,
`src/candidate_runner.py` a geração das respostas e `src/scoreboard.py` a apuração.
`avaliacao/julga_rabula.py` é a variante usada em produção, com `judge.py` como cliente e
`benchmark_schema.py` como contrato da resposta esperada.

O protocolo repete tudo isso até 5 vezes por candidato com o código congelado. É essa
repetição que torna mensurável o piso de ruído da Seção 4.2, e é a razão de o depósito trazer
cinco diretórios de veredito em vez de um.

---

## O manuscrito

`tabelas.py` recomputa as tabelas a partir dos dados, `figura_papeis.py` a figura,
`monta_artigo.py` monta o HTML, e um conversor em `publicacao/jurix/` produz o formato IOS
Press que a conferência exige.

| língua | fontes | conversor |
|---|---|---|
| inglês | `publicacao/artigo2_en/` | `publicacao/jurix/para_tex_2en.py` |
| português | `publicacao/artigo2/` | `publicacao/jurix/para_tex_2.py` |

As tabelas e a figura em inglês importam os módulos em português e trocam apenas os rótulos,
de modo que as duas versões não têm como divergir nos números.

## O que está deliberadamente ausente

A interface usada para coletar as anotações humanas, que pertence ao estudo Rabula, e o
arquivo de trabalho de scripts superados. `publicacao/monta_repo_benchmark.py` é o que monta
este repositório: ele se recusa a incluir um arquivo cujo nome ou conteúdo case com um padrão
de credencial, e se recusa a terminar se algum script incluído importa um módulo que ficou de
fora.
