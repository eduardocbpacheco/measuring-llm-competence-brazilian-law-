# Medindo a competência de LLMs no direito brasileiro: responder, redigir e julgar

*[English version: `README.md`](README.md)*

Código e material de reprodução do artigo de mesmo nome, que mede 31 modelos de linguagem
nos **três papéis** que o arranjo corrente de avaliação envolve, sobre o mesmo material:
escrever uma peça processual, responder uma questão discursiva e julgar o que os outros
modelos escreveram.

O conjunto de avaliação são 105 questões da segunda fase do Exame de Ordem, decompostas em
940 critérios extraídos do espelho oficial das bancas, com padrão-ouro humano de 940 decisões
binárias tomadas por três juristas. A concordância é reportada por área do direito e, na
redação de peça, aberta nas duas classes de critério que a própria banca rotula.

**Eduardo Pacheco** · Instituto de Ciências Matemáticas e de Computação, Universidade de São
Paulo. Artigo em coautoria com Cibele Maria Russo.

## Comece aqui

**[`REPRODUZIR.md`](REPRODUZIR.md)** percorre as três etapas e nomeia o script exato de cada
uma. A etapa 3 **não precisa de GPU nem de chave de API**: ela recomputa todos os números,
tabelas e figuras do artigo a partir dos vereditos depositados.

## O que há aqui

| diretório | o que guarda |
|---|---|
| `pipeline/` | transformar os PDFs das provas em 105 questões e 940 critérios, e o agrupamento forma/mérito |
| `rabula/consolidado/` | rodar o benchmark: respostas candidatas, julgamento, alinhamento com o padrão-ouro |
| `avaliacao/` | concordância por área e por classe de critério, nota, os testes estatísticos |
| `explorador/` | aplicação local para inspecionar cada veredito ao lado da resposta que o gerou |
| `publicacao/` | as fontes do artigo, em português e inglês, e a conversão para o estilo IOS Press |
| `dataset/` | congelamento, o manifesto com soma de verificação por arquivo, empacotamento |

Isto é uma seleção curada, não o arquivo de trabalho. Só está aqui o caminho que produziu o
que está no artigo.

## Anotação e exploração

`explorador/` é uma aplicação local pequena, HTML, CSS e JavaScript servidos por Flask, sem
etapa de build e sem login. Tem três vistas:

| vista | o que faz | precisa de |
|---|---|---|
| `/regua` | a tabela de concordância de cada juiz por área do direito, e a nota dos mesmos modelos como respondentes, lado a lado e alternável por tarefa | o depósito deste artigo |
| `/anotar` | **anotação binária cega**, para estender o padrão-ouro humano: mostra o caso, a resposta avaliada e um critério, e nada mais | o depósito deste artigo |
| `/condicoes` | compara duas condições treinadas na mesma questão, critério a critério | o depósito do artigo irmão |

Rode `python explorador/app.py` e abra o endereço que ele imprime.

A vista de anotação é cega por construção: ela nunca mostra o item do espelho oficial, nem o
veredito de qualquer juiz, nem a decisão de outro anotador. Mostrar qualquer um dos três
transformaria a anotação numa conferência, que mede outra coisa. As decisões são gravadas uma
por anotador em `explorador/anotacoes/`, com escrita atômica.

O padrão-ouro de 940 decisões que já está no depósito foi **herdado** do benchmark Rabula,
coletado antes deste trabalho; `/anotar` é como ele se estende, não como foi construído. Tudo
o que vem depois dele está aqui: `rabula/consolidado/scripts/3_alignment_humano.py` alinha os
três anotadores com cada juiz candidato, e `avaliacao/kappa_por_area.py` e
`kappa_por_classe.py` abrem essa concordância por área do direito e por classe de critério.

## Os dados

Os vereditos **não** estão neste repositório. São 47.869 arquivos, cerca de 180 MB,
depositados sob identificador persistente:
**[10.5281/zenodo.22739161](https://doi.org/10.5281/zenodo.22739161)**.

O depósito traz os vereditos dos 31 juízes candidatos em até 5 repetições sob código
congelado, as anotações dos três juristas, e as 105 questões com os seus 940 critérios.
`dataset/manifestos/benchmark-juizes.json` dá, para cada arquivo, o caminho, o tamanho, a
contagem de linhas e o SHA-256.

O artigo irmão, sobre o que treinar, e os depósitos de corpus e julgamentos dele estão em
[github.com/eduardocbpacheco/synthetic-corpora-brazilian-law](https://github.com/eduardocbpacheco/synthetic-corpora-brazilian-law).
Os dois repositórios compartilham um núcleo pequeno, `avaliacao/nota.py` entre ele; estão
separados porque os artigos são lidos por pessoas diferentes e por razões diferentes.

## Licença

Código sob MIT (`LICENSE`). Os dados depositados sob CC BY 4.0, com o padrão-ouro herdado do
Rabula nos mesmos termos.
