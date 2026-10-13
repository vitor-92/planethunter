# Nível avançado: pensar como quem constrói e publica

<p class="meta">Nível avançado · cerca de 16 semanas · 4 a 6 horas por semana</p>

Você chegou aqui sabendo o que é um trânsito, como se lê um periodograma, por que SNR 7,1 é um limite razoável e o que cada teste do vetting procura. Este nível muda o ponto de vista. Até agora você aprendeu a **usar** e **interpretar** o PlanetHunter. A partir daqui você vai aprender a **questionar** as escolhas dele, ler os artigos que as justificam, medir o efeito de uma mudança e levar um candidato até a comunidade científica.

!!! abstract "Ao final deste nível você vai conseguir"
    - Ler um artigo de método (BLS, TLS, Robovetter, triceratops, ExoMiner) e dizer o que ele faz, o que assume e onde falha.
    - Comparar o vetting do PlanetHunter com o das missões Kepler e TESS e apontar o que falta.
    - Interpretar uma probabilidade de falso positivo (FPP) sem tratá-la como verdade absoluta.
    - Propor uma mudança num limite de `config/thresholds.yaml`, medir antes e depois e escrever o resultado com intervalo de confiança.
    - Montar um pacote de submissão de CTOI completo, com busca de literatura e texto honesto.

## Para quem é este nível

Para quem concluiu o [nível médio](../intermediate/index.md) e a trilha de programação até a aula P3. Você vai rodar comandos, editar um arquivo de configuração e ler código Python. Não precisa saber escrever um pipeline do zero, mas precisa conseguir seguir uma função de 50 linhas e entender o que entra e o que sai.

A matemática sobe um degrau. Aparecem somatórios, qui-quadrado, probabilidade condicional e o teorema de Bayes. Cada fórmula vem com a explicação em palavras e com um exercício numérico resolvido. Se uma equação travar você, leia a frase que vem depois dela, faça o exercício e volte.

## As aulas

| Aula | Semanas | Em uma frase |
|---|---|---|
| [A1. Algoritmos de detecção](a1-detection-algorithms.md) | 1–3 | A estatística do BLS e do TLS, os trade-offs do detrending e por que monotrânsitos são o nicho mais promissor. |
| [A2. Como as missões fazem vetting](a2-mission-vetting.md) | 3–6 | Data Validation, Robovetter, catálogo de TOIs e catálogo de binárias, comparados lado a lado com os testes do PlanetHunter. |
| [A3. Probabilidade de falso positivo](a3-false-positive-probability.md) | 6–8 | Raciocínio bayesiano, vespa e triceratops, os cenários de falso positivo e o caso real do WASP-100 b. |
| [A4. Aprendizado de máquina](a4-machine-learning.md) | 8–11 | Redes neurais que classificam sinais, rótulos, vazamento, calibração e por que, no projeto, o ML só reordena. |
| [A5. Medir o sistema](a5-measuring-the-system.md) | 11–13 | Recall, completude, injection-recovery, intervalo de Wilson e o método antes/depois para mudar um limite. |
| [A6. Do candidato à comunidade](a6-from-candidate-to-community.md) | 13–16 | ExoFOP, submissão de CTOI, o programa de acompanhamento do TESS, busca de literatura e ética. |
| [Autoavaliação](assessment.md) | 16 | Dez perguntas abertas com modelos de resposta. |

A ordem importa. A1 e A2 dão o vocabulário para A3. A5 depende de tudo que veio antes, porque medir só faz sentido quando você sabe o que está medindo. A6 fecha o ciclo e usa tudo.

## Como ler um artigo científico

Neste nível você vai ler cerca de dez artigos. Ninguém lê um artigo técnico de ponta a ponta na primeira vez, nem os autores dos artigos. A técnica abaixo é uma variação do método de "três passadas" descrito por Keshav (2007).

**Primeira passada (15 a 20 minutos): decidir se vale ler.**

1. Leia o **título** e o **resumo** (abstract). Anote em uma frase: qual problema o artigo resolve?
2. Pule para a **conclusão** (ou "Summary", "Discussion"). Anote: o que eles afirmam ter conseguido?
3. Olhe **todas as figuras e tabelas**, com as legendas. Em artigos de exoplanetas, as figuras carregam metade do conteúdo: curvas de luz, periodogramas, histogramas de completude.
4. Leia os títulos das seções.

Ao fim, você deve saber dizer o que o artigo faz sem ter lido nenhuma equação.

**Segunda passada (1 a 2 horas): entender o argumento.**

1. Leia a **introdução** inteira. Ela diz o que já existia e qual lacuna o artigo preenche.
2. Leia a seção de **método** pulando derivações. Pare em cada equação e pergunte: o que entra, o que sai, em que unidade?
3. Leia os **resultados** com as figuras ao lado.
4. Marque as referências que aparecem várias vezes. Elas são a base do campo.

**Terceira passada (quando precisar): reconstruir.**

Só quando você for implementar algo ou discordar do artigo. Refaça as contas principais, reproduza uma figura com dados públicos e procure as hipóteses escondidas ("assumimos órbita circular", "ignoramos ruído correlacionado").

!!! tip "Onde achar os artigos"
    Quase todo artigo da área tem versão gratuita no arXiv (arxiv.org, seção astro-ph.EP para planetas). O ADS (ui.adsabs.harvard.edu) é o buscador da astronomia: digite autor e ano, por exemplo `author:"Kovacs" year:2002`, e ele mostra o link para o arXiv e para a revista. A aula A6 ensina a usar o ADS para busca de literatura sobre um alvo.

!!! note "Caderno de leitura"
    Para cada artigo, escreva meia página com: (1) problema; (2) método em três frases; (3) o principal número ou figura; (4) uma hipótese que o artigo faz; (5) onde isso aparece no PlanetHunter, ou por que não aparece. Esse caderno vai ser a base das respostas da autoavaliação.

## Ritmo sugerido

Cada aula tem leitura obrigatória (os artigos listados nas [referências](../references.md)), exercícios resolvidos e uma prática na ferramenta. Uma semana típica:

- 2 horas de leitura (primeira e segunda passadas de um artigo).
- 1 hora com a aula do site e os exercícios.
- 1 a 2 horas de prática: rodar um comando, abrir um dossiê, mudar um parâmetro.
- 30 minutos para o caderno de leitura e o caderno de revisões.

Se uma semana render menos, não pule a prática. Ler sobre centróides sem nunca olhar uma imagem-diferença não fixa nada.

## Como saber que terminou

Você terminou o nível avançado quando consegue, sem ajuda:

1. Explicar a um colega, com uma fórmula e um desenho, por que o BLS maximiza $s^2/[r(1-r)]$ e o que isso tem a ver com SNR.
2. Pegar um artigo recente de validação de planeta do TESS e listar cada teste de vetting usado, marcando qual o PlanetHunter tem e qual não tem.
3. Olhar a saída do triceratops de um candidato e dizer qual cenário domina, o que o tornaria menos provável e qual observação ajudaria.
4. Fazer uma mudança em `config/thresholds.yaml`, rodar o benchmark antes e depois, calcular o intervalo de Wilson e escrever um relatório de uma página em `docs/benchmarks/`.
5. Montar o pacote de submissão de um candidato P1 (mesmo hipotético), com efeméride, incertezas, notas, busca de literatura e lista de citações.
6. Acertar com folga a [autoavaliação](assessment.md).

Depois disso, o próximo passo não é mais um curso. É contribuir: revisar candidatos com critério, abrir issues quando um número parecer errado e, um dia, submeter um CTOI que sobreviva ao olhar da equipe do TESS.
