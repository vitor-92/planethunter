# A4. Aprendizado de máquina para triagem

<p class="meta">Nível avançado · semanas 8–11 · cerca de 15 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Como Shallue & Vanderburg (2018) usaram uma rede neural para classificar sinais do Kepler, com as visões global e local.
    - O que o ExoMiner (Valizadegan et al. 2022) acrescentou e como chegou à validação de 301 planetas.
    - De onde vêm os rótulos de treino e por que eles são imperfeitos.
    - O que é vazamento entre treino e teste e por que o split precisa ser por estrela.
    - O que é calibração e por que um score de 0,9 nem sempre significa 90 %.
    - Por que, no PlanetHunter, o ML só reordena a fila e nunca veta, e como as suas revisões viram rótulos.

Na primeira fatia real do projeto, com 2 164 estrelas do setor 69, o funil produziu 648 sinais `NEW`, 11 aprovados no vetting básico e 3 candidatos P2 depois do vetting aprofundado. Em um setor inteiro (cerca de 20 000 estrelas), e depois em imagens completas (centenas de milhares), a fila de revisão humana cresce até ficar inviável. O aprendizado de máquina (ML) entra aqui: **ordenar a fila** para que o tempo humano vá primeiro para o que mais vale.

## 1. A ideia: ensinar pelo exemplo

Um classificador de ML aprende uma função "dados de entrada → probabilidade de ser planeta" a partir de exemplos rotulados. Em vez de você escrever regras ("se ímpar/par > 3σ, reprove"), você mostra milhares de casos com a resposta certa e o algoritmo descobre os padrões. A vantagem: ele pode combinar sinais fracos que nenhuma regra isolada pegaria. O risco: ele aprende **qualquer** padrão que separe os rótulos, inclusive padrões que não têm nada a ver com física.

## 2. Shallue & Vanderburg (2018): visões global e local

Shallue & Vanderburg (2018), *The Astronomical Journal* 155, 94, treinaram uma **rede neural convolucional** (CNN, um tipo de rede que aprende padrões locais em sequências ou imagens) com sinais do Kepler. Os rótulos vinham de classificações humanas de TCEs do Kepler: planeta candidato, falso positivo astrofísico ou não-trânsito.

A contribuição mais copiada do artigo é a **representação da entrada**. Em vez da curva de luz inteira, a rede recebe duas visões da curva dobrada no período:

| Visão | O que mostra | Tamanho | Para que serve |
|---|---|---|---|
| **Global** | A órbita inteira, de fase −0,5 a 0,5 | 2 001 bins | Ver eclipse secundário, variações fora do trânsito, forma geral |
| **Local** | Só a vizinhança do trânsito, poucas durações para cada lado | 201 bins | Ver detalhes da forma: fundo plano (U) ou em V, ingresso e egresso |

Cada visão é normalizada (mediana em zero, profundidade em −1), o que faz a rede comparar **formas**, não profundidades absolutas. Os dois ramos convolucionais se juntam em camadas finais que produzem um número entre 0 e 1.

O resultado ficou conhecido por um motivo concreto: aplicada a estrelas do Kepler com vários planetas já conhecidos, a rede apontou sinais fracos que, depois de análise, levaram à validação de **Kepler-90 i** e **Kepler-80 g**. Note a sequência: a rede **sugeriu**; a validação veio de análise posterior.

Yu et al. (2019), *AJ* 158, 25, adaptaram a mesma arquitetura ao TESS. A adaptação não foi trivial: o TESS tem menos trânsitos por sinal, pixels maiores e outro conjunto de sistemáticos. Um modelo treinado no Kepler não serve direto no TESS.

## 3. ExoMiner: dar à rede o que o especialista olha

Valizadegan et al. (2022), *The Astrophysical Journal* 926, 120, apresentaram o **ExoMiner**. A ideia: um especialista humano não decide só pela forma do trânsito. Ele olha o centróide, o ímpar/par, o secundário, os parâmetros da estrela, os diagnósticos do Data Validation (aula A2). O ExoMiner dá à rede **um ramo para cada tipo de evidência**:

- Visões global e local do fluxo (como em Shallue & Vanderburg).
- Visões do **centróide** (movimento durante o trânsito).
- Visões de trânsitos **ímpares e pares** separados.
- Visão em torno do **eclipse secundário**.
- **Parâmetros estelares** e **estatísticas escalares** do DV.

Duas vantagens. Primeiro, desempenho melhor que modelos só com fluxo, porque a rede vê os diagnósticos que separam binárias de fundo e eclipses. Segundo, **explicabilidade**: dá para ver qual ramo pesou na decisão ("rejeitado principalmente pelo centróide"), o que ajuda um humano a confiar ou desconfiar.

Com o ExoMiner, os autores validaram **301 novos planetas** do Kepler. A validação exigiu uma probabilidade muito alta e checagens adicionais, no mesmo espírito da validação estatística da aula A3. O ML entrou como uma forma de estimar a verossimilhança, não como substituto do raciocínio.

## 4. Dados rotulados: de onde vêm e por que são imperfeitos

O plano do projeto (agente `ml-engineer`) define as fontes:

| Rótulo | Fonte | Problema conhecido |
|---|---|---|
| Positivo | TOIs com disposição CP/KP do TFOPWG | Poucos; tendem a ser profundos e em estrelas brilhantes |
| Positivo sintético | Trânsitos injetados com `batman` em curvas reais (aula A5) | Perfeitos demais: sem sistemáticos correlacionados com o trânsito |
| Negativo | FP/FA do TFOPWG | Poucos e heterogêneos |
| Negativo | Catálogo de binárias do TESS | **Contém hot Jupiters confirmados** (aula A2) |
| Negativo | Sinais de ruído rejeitados pelo próprio vetting | Rótulo dado pelo próprio sistema: o modelo aprende a imitar o vetting |

Três lições:

1. **Ruído de rótulo é a regra.** O catálogo de binárias tem planetas. "PC" não é planeta. Alguns FPs antigos foram revistos. Antes de treinar, cruze os rótulos com a mesma prioridade do crossmatch: planeta confirmado vence o catálogo de binárias.
2. **Desbalanceamento.** Há muito mais negativos que positivos. Acurácia é uma métrica inútil aqui: um modelo que diz "não é planeta" para tudo acerta 99 %. Use recall a precisão fixa e área sob a curva precisão-recall (AUC-PR).
3. **Circularidade.** Se os negativos vêm do próprio vetting, o modelo aprende a reproduzir o vetting, incluindo os erros dele. Ele não vai achar o que o vetting perde.

## 5. Vazamento entre treino e teste

**Vazamento** (leakage) é quando informação do conjunto de teste entra, de algum jeito, no treino. O resultado é um desempenho medido ótimo que desaba no uso real.

Em exoplanetas, a forma mais comum é **a mesma estrela nos dois conjuntos**:

- Uma estrela observada em 10 setores gera o mesmo sinal 10 vezes. Se o split for aleatório **por sinal**, 8 vão para o treino e 2 para o teste. A rede "reconhece" a estrela (o nível de ruído, a variabilidade, a profundidade exata) e acerta o teste sem ter aprendido nada geral.
- Uma estrela com vários planetas: os sinais compartilham a mesma curva de luz.
- Injeções na mesma curva em que há um sinal real.

A regra do projeto é explícita: **split por estrela, nunca por sinal**. Todas as linhas de um mesmo TIC vão para o mesmo conjunto. Para medir generalização de verdade, vale ainda separar por **região do céu** ou por **setor**, porque sistemáticos do instrumento variam com câmera e época.

## 6. Calibração: o score significa o que diz?

Um classificador devolve um número entre 0 e 1. Isso **não** faz dele uma probabilidade. Um modelo está **calibrado** quando, entre todos os sinais que recebem score perto de 0,9, cerca de 90 % são de fato da classe positiva.

Redes neurais modernas tendem a ser **confiantes demais** (Guo et al. 2017): scores próximos de 0 ou 1 com mais frequência do que deveriam. Para verificar:

1. Separe um conjunto de validação (por estrela!).
2. Agrupe os sinais por faixa de score (0–0,1, 0,1–0,2, ...).
3. Em cada faixa, compare o score médio com a fração real de positivos. O gráfico disso é o **diagrama de confiabilidade**.

Para corrigir, o plano usa **temperature scaling**: dividir a saída da rede (antes da função que a transforma em 0 a 1) por uma constante ajustada no conjunto de validação. Simples, e não muda a ordem dos sinais, só os valores.

Por que importa no projeto: o score do ML entra no **novelty score**, que multiplica a confiança do vetting e o ineditismo na literatura. Multiplicar probabilidades descalibradas produz números sem significado.

Uma medida resumida é o **escore de Brier**: a média de $(p_i - y_i)^2$, onde $p_i$ é o score e $y_i$ o rótulo (0 ou 1). Quanto menor, melhor. Ele penaliza tanto erros de ordem quanto de calibração.

## 7. Por que, no projeto, o ML só reordena

A regra está no agente `ml-engineer`: **o score do ML nunca veta sozinho; só reordena e rebaixa prioridade. Recall em TOIs conhecidos não pode cair.** Quatro razões:

1. **Os planetas novos estão fora da distribuição de treino.** Os rótulos vêm de TOIs, que são em geral profundos, em estrelas brilhantes e de período curto. Os nichos do projeto (estrelas fracas, períodos longos, anãs M) são exatamente onde há menos exemplos. Um classificador tende a dar score baixo para o que nunca viu, e o que nunca viu é o que se procura.
2. **Erro assimétrico.** Revisar um falso positivo custa alguns minutos. Vetar um planeta real custa o planeta: ninguém olha de novo.
3. **O vetting determinístico é auditável.** Cada veto tem um teste, um número e um limite comentado em `config/thresholds.yaml`, com benchmark antes e depois. Um veto de rede neural é difícil de explicar e de corrigir.
4. **O ML não vê o que a busca não detecta.** Ele atua depois da busca. Se o detrending comeu o trânsito, nenhum classificador recupera. Melhorar a busca é trabalho para o injection-recovery (aula A5), não para o ML.

A meta do plano para a fase 5 é coerente com isso: o ML deve **reduzir em pelo menos 5 vezes o número de candidatos que você precisa revisar primeiro**, mantendo o recall. Os demais continuam na fila, mais abaixo.

Como o código garante isso (`alerts/severity.py`). A probabilidade do modelo, `p_rank`, entra na severidade só por dois limiares, ambos escolhidos medindo quantos planetas conhecidos eles mantêm na validação cruzada: o **limiar de P2** mantém 90 % deles, e o **limiar de P1** é o mais baixo com no máximo 1 % de falsos positivos que ainda mantém pelo menos 70 % dos planetas. Um sinal abaixo do limiar de P1 cai para P2, seja qual for o score. Um `p_rank` alto nunca sobe um sinal: P1 continua exigindo score determinístico de pelo menos 0,8. O único "resgate" é limitado: um sinal que falhou no vetting determinístico sem veto pode chegar a P2, nunca mais que isso. A auditoria de 2026-10-10 descobriu que uma versão anterior deixava o modelo substituir o score, e dois sinais do setor 107 subiram de P2 para P0 e P1 só por causa do modelo.

**Duas probabilidades, dois usos.** Uma probabilidade aprendida num conjunto de treino em que planetas são comuns (planetas conhecidos são uma parte grande dos exemplos) é uma probabilidade **sob aquela mistura**. Entre sinais novos, planetas são muito mais raros, e o mesmo sinal tem uma chance real bem menor de ser planeta. Por isso o projeto guarda dois números: `p_rank` (a saída calibrada do modelo, usada para ordenar e para os limiares acima) e `p_abs`, o mesmo valor corrigido pela regra de Bayes para uma fração suposta de planetas entre os sinais novos (5 %, `severity.new_prior`):

$$
\text{logit}(p_\text{abs}) = \text{logit}(p_\text{rank}) + \text{logit}(0{,}05) - \text{logit}(\text{fração no treino}) .
$$

Os 5 % são uma suposição, não uma medida. Por isso `p_abs` é mostrado, mas nunca usado para decidir nada.

## 8. Suas revisões viram rótulos

Cada vez que você roda

```bash
uv run planethunter review <signal_id> rejected --reason eb --note "secundário visível em fase 0,5"
```

o banco grava `review_status` e `review_note` na tabela `candidates`. Os status possíveis são `approved`, `rejected` e `follow_up`. Rejeições exigem um motivo entre `eb`, `blend`, `systematic` (sistemático), `noise` (ruído), `already_known` (já conhecido) e `other` (outro).

Essas decisões são os **rótulos mais valiosos** do projeto, porque vêm exatamente da distribuição que importa: sinais que passaram por todo o vetting e chegaram à fila. Nenhum catálogo público tem esse tipo de exemplo. Isso é a base do **aprendizado ativo** (active learning) do plano: o modelo pede revisão humana dos casos em que está mais incerto, e cada revisão melhora o próximo treino.

Para que suas revisões sirvam como rótulo:

- **Seja consistente** com o motivo. "eb" e "blend" ensinam coisas diferentes ao modelo.
- **Escreva a nota com a evidência**, não com a conclusão: "profundidade ímpar 4 100 ppm, par 2 300 ppm" vale mais que "parece EB".
- **Entenda o que o rótulo significa.** "approved" quer dizer "sobreviveu ao olhar humano e merece acompanhamento", não "é planeta". Um modelo treinado com isso aprende a prever a sua decisão, com seus vieses.
- **Use `follow_up` quando não souber.** Um rótulo errado com convicção é pior que um rótulo honesto de incerteza.

!!! tip "Na ferramenta"
    - `uv run planethunter candidates` lista a fila; `uv run planethunter dossier <signal_id>` gera o dossiê; `uv run planethunter review ...` grava a decisão.
    - As colunas `review_status`, `review_note` e `reviewed_at` ficam na tabela `candidates` de `data/planethunter.duckdb`.
    - Um primeiro passo, simples, já existe: `uv run planethunter calibrate` treina uma regressão logística com os resultados do vetting básico de sinais conhecidos. Positivos: planetas confirmados. Negativos: falsos positivos catalogados e, quando disponíveis, todos os sinais das rodadas nulas invertidas e embaralhadas (aula A1), que são alarmes falsos por construção. A regularização é escolhida por validação cruzada agrupada por estrela, as probabilidades são calibradas com Platt scaling sobre previsões fora da dobra (out-of-fold), e o modelo é gravado em `data/models/vetting_lr.json` com um `model_version` e as rodadas de origem. A fila passa a mostrar `p_rank` e `p_abs`, e a severidade usa `p_rank` só para baixar a prioridade.
    - O classificador de rede neural descrito nesta aula ainda **não está implementado**. É a fase 5 do plano. O que você revisa hoje é o conjunto de treino de amanhã.

!!! example "Exercício 1. Ache o vazamento"
    Uma pessoa monta um conjunto com 3 000 sinais de 1 200 estrelas, embaralha os sinais e separa 80 % para treino e 20 % para teste. O modelo atinge AUC-PR de 0,97 no teste. Aplicado a um setor novo, a fila ordenada pelo modelo parece quase aleatória. O que aconteceu e como corrigir?

    ??? success "Ver resposta"
        1. Com 3 000 sinais de 1 200 estrelas, muitas estrelas têm vários sinais (vários setores, vários planetas, iterações da busca). O embaralhamento por sinal colocou a mesma estrela no treino e no teste.
        2. O modelo aprendeu a reconhecer estrelas (nível de ruído, variabilidade, profundidade), não padrões de planeta versus binária. O teste mediu memória.
        3. Correção: agrupar por TIC e sortear **estrelas** para treino e teste. Melhor ainda: reservar setores inteiros para o teste, para medir também a mudança de sistemáticos.
        4. Esperado: a AUC-PR no teste corrigido cai, e passa a refletir o desempenho real.

!!! example "Exercício 2. O modelo está calibrado?"
    (a) Num conjunto de validação, 200 sinais receberam score entre 0,85 e 0,95. Desses, 120 são planetas. O modelo está calibrado nessa faixa? (b) Calcule o escore de Brier para quatro sinais com scores 0,9; 0,9; 0,2; 0,6 e rótulos 1; 0; 0; 1.

    ??? success "Ver resposta"
        (a) Score médio ≈ 0,9; fração real $120/200 = 0{,}6$. O modelo é **confiante demais** nessa faixa: promete 90 % e entrega 60 %. Temperature scaling deve trazer esses scores para perto de 0,6.

        (b) Erros ao quadrado: $(0{,}9-1)^2 = 0{,}01$; $(0{,}9-0)^2 = 0{,}81$; $(0{,}2-0)^2 = 0{,}04$; $(0{,}6-1)^2 = 0{,}16$. Soma $1{,}02$. Brier $= 1{,}02/4 = 0{,}255$. O segundo sinal, um negativo com score 0,9, responde por quase todo o erro.

!!! example "Exercício 3. Reordenar ou vetar?"
    A fila tem 200 candidatos, dos quais 4 merecem acompanhamento (você só saberá depois). Você tem tempo para revisar 40 por mês. O modelo coloca 3 dos 4 entre os 40 primeiros e o quarto na posição 150. Compare duas políticas: (A) vetar tudo abaixo da posição 40; (B) reordenar a fila e continuar revisando nos meses seguintes.

    ??? success "Ver resposta"
        - Política A: revisão 5 vezes menor (40 de 200), mas o quarto candidato é **perdido para sempre**. Recall 3/4 = 75 %. Viola a regra "recall não pode cair".
        - Política B: no primeiro mês você acha 3 dos 4, o mesmo ganho de tempo da política A. O quarto aparece no quarto mês. Recall final 100 %.
        - O ML entrega o benefício principal (achar o melhor primeiro) sem o custo irreversível. Esse é o motivo da regra do projeto. E o quarto candidato, com score baixo e decisão humana positiva, é exatamente o exemplo que mais ensina ao próximo treino.

## Checklist da aula

- [ ] Li Shallue & Vanderburg (2018) e sei explicar as visões global e local.
- [ ] Li Valizadegan et al. (2022) e sei listar os ramos do ExoMiner.
- [ ] Sei apontar três problemas nos rótulos disponíveis para o projeto.
- [ ] Sei explicar vazamento e por que o split é por estrela.
- [ ] Sei ler um diagrama de confiabilidade e calcular o escore de Brier.
- [ ] Sei dar quatro razões pelas quais o ML só reordena.
- [ ] Revisei pelo menos 10 candidatos com motivo e nota baseada em evidência.

## Para ir além

- Shallue & Vanderburg (2018), *The Astronomical Journal* 155, 94. O artigo que popularizou as visões global e local; leia a seção de representação dos dados e a de resultados.
- Valizadegan et al. (2022), *The Astrophysical Journal* 926, 120. O ExoMiner; leia a arquitetura e a discussão sobre explicabilidade.
- Yu et al. (2019), *The Astronomical Journal* 158, 25. A adaptação ao TESS; mostra o que muda quando o instrumento muda.
- Armstrong et al. (2021), *Monthly Notices of the RAS* 504, 5327. Validação de planetas do Kepler com vários algoritmos de ML combinados com probabilidades calibradas; ótimo contraponto ao ExoMiner.
- Guo et al. (2017), "On Calibration of Modern Neural Networks", *Proceedings of ICML*. Mostra que redes profundas são confiantes demais e introduz o temperature scaling.
- Ivezić, Connolly, VanderPlas & Gray, *Statistics, Data Mining, and Machine Learning in Astronomy* (Princeton University Press). Livro de referência que liga estatística e ML a problemas astronômicos reais.
