# M3. Periodogramas: como se acha um período

<p class="meta">Nível médio · semanas 5–6 · cerca de 10 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - A ideia do BLS (Box Least Squares) e o que o TLS muda.
    - O que é SDE e por que o limite é 9.
    - Como a grade de períodos é montada, e por que seus limites mudaram o recall.
    - Por que aparecem aliases (P/2, 2P, P/3) e como o PlanetHunter corrige o caso P/3.
    - Como funciona a busca iterativa com mascaramento.
    - Por que a janela de detrending decide o que você consegue achar, com números medidos.
    - O efeito de lacunas e bordas de segmento nos dados do TESS.

## O problema

Você tem 27 dias de brilho medido a cada 2 minutos, cerca de 18 000 pontos. Em algum lugar há quedas de 300 ppm, com ruído de 130 ppm por ponto. Você não sabe o período, nem quando foi o primeiro trânsito, nem quanto dura cada um.

A solução é força bruta organizada: **testar todas as combinações** e medir qual explica melhor os dados. O gráfico de "quão bem cada período explica os dados" é o **periodograma**.

## BLS: procurar caixas

O **BLS** (*Box Least Squares*, Kovács, Zucker & Mazeh, 2002) modela o trânsito como uma **caixa**: brilho constante fora, brilho constante e mais baixo dentro.

Para cada período $P$ da grade:

1. **Dobre** a curva: calcule a fase de cada ponto, o resto da divisão do tempo por $P$. Se $P$ estiver certo, todos os trânsitos caem um em cima do outro.
2. Para cada **posição** da caixa na fase e cada **duração** da grade, compare a média dos pontos dentro da caixa com a média fora.
3. Calcule quanto o modelo de caixa reduz o erro quadrático em relação a uma linha reta. Essa redução é a **potência** do BLS naquele período.

O periodograma guarda, para cada período, a melhor potência entre todas as posições e durações. O pico mais alto é o candidato a período.

Analogia: é como procurar uma batida num barulho. Você tenta vários ritmos e, para cada um, sobrepõe os compassos. No ritmo certo, as batidas se somam e se destacam; nos errados, se espalham.

## TLS: procurar trânsitos de verdade

O **TLS** (*Transit Least Squares*, Hippke & Heller, 2019) faz a mesma busca, mas troca a caixa por um **modelo de trânsito realista**: rampas de entrada e saída, fundo arredondado pelo escurecimento de borda (aula [M2](m2-transit-physics.md)). O modelo é ajustado à estrela: o PlanetHunter passa raio e massa do TIC.

Por que isso ajuda? A caixa erra nas rampas e no fundo. Para trânsitos fortes, tanto faz. Para planetas **pequenos**, perto do limite de detecção, esse erro come uma parte do sinal. O modelo realista recupera essa parte, e os autores mostram ganho de sensibilidade justamente para planetas pequenos. Em troca, o TLS é mais lento.

O PlanetHunter usa o TLS 2.0 (backend `fused-pl`, uma thread por alvo, em paralelo por estrela).

## SDE: o pico se destaca?

O TLS calcula, para cada período, um valor de qualidade do ajuste (chamado SR). O **SDE** (*Signal Detection Efficiency*) mede quanto o pico mais alto se destaca do resto:

$$
\text{SDE} = \frac{\text{SR}_\text{pico} - \overline{\text{SR}}}{\sigma_\text{SR}}
$$

É o número de desvios padrão que o pico está acima da média do periodograma. Um SDE alto diz: "esse período é muito melhor que todos os outros".

**Por que 9?** Hippke & Heller (2019) simularam curvas só com ruído branco e mediram com que frequência o maior pico passava de cada SDE: SDE 7 dá uma probabilidade de falso alarme (FAP) de cerca de 1 %. A documentação do TLS repete o teste com mais curvas: SDE 9,1 dá cerca de $10^{-4}$, 1 em 10 000 curvas de ruído puro. É o `sde_min: 9.0` do `config/thresholds.yaml`. Curvas reais também têm ruído vermelho, então o falso alarme de verdade é maior que esses números.

O sistema guarda também sinais com SDE entre 7 e 9 (`sde_keep: 7.0`), mas eles não viram candidatos. Servem de exemplos fracos para o futuro classificador de aprendizado de máquina.

!!! note "SDE e SNR medem coisas diferentes"
    O SDE compara o pico com o **resto do periodograma**: "esse período se destaca?". O SNR compara a profundidade com o **ruído da curva**: "a queda é grande?" (aula [M1](m1-statistics-for-signals.md)). Um sinal pode ter SDE alto e SNR baixo, ou o contrário. O PlanetHunter exige os dois: SDE ≥ 9 **e** SNR ≥ 7,1.

## A grade de períodos

O TLS não testa infinitos períodos. Testa uma **grade**, e a grade decide o que pode ser encontrado. Os parâmetros do projeto:

| Parâmetro | Valor | Por quê |
|---|---|---|
| `period_min_days` | 0,2 d | Piso absoluto da grade |
| `roche_min_a_rstar` | 2,0 | O menor período testado é aquele em que a órbita fica a 2 raios estelares do centro da estrela, como no pipeline de visão rápida do TESS (QLP); cerca de 0,2 a 0,3 d para uma estrela como o Sol |
| `period_max_fraction_of_span` | 0,9 × duração dos dados | Dois trânsitos bastam para definir um período |
| `period_max_days` | 40 d | Teto absoluto (ver abaixo) |
| `oversampling_factor` | 3 | Densidade da grade; maior = mais lento e mais fino |
| `duration_grid_step` | 1,1 | Cada duração testada é 10 % maior que a anterior |
| `bin_minutes` | 10 | Junta pontos de 2 min em blocos de 10 min para acelerar; perde pouco para P > 1 d |
| `limb_darkening` | `tess` | O modelo de trânsito usa o escurecimento de borda da banda do TESS, escolhido pela temperatura e pela gravidade superficial da estrela |

Cada um desses números tem uma história medida no benchmark do setor 69:

- **Limites estelares.** No início, a grade de durações só aceitava estrelas até ±30 % do raio e da massa do TIC. Trânsitos mais curtos que o central (b alto, raio do TIC errado) ficavam fora. TOI 196.01, 347.01, 386.01 e 2339.01 sumiam; com limites largos, aparecem com SDE de 8,6 a 16,8.
- **Período mínimo e limite de Roche.** O TLS calcula o menor período possível a partir do raio do modelo (um planeta não pode orbitar dentro da estrela). Com o raio do TIC de 4,06 R☉, a grade começava em 4,15 d, e o TOI 196.01, com P = 1,16 d, sumia. Correção: o modelo usa no máximo 1,5 R☉ e 1,5 M☉. Uma auditoria posterior (2026-10-10) achou um segundo limite: o TLS supõe uma órbita de pelo menos 3 raios estelares, então o menor período testado era na prática de 0,6 a 1,0 d, e 13 dos 505 TOIs do setor 69 ficavam fora da grade. Hoje o mínimo é de 2 raios estelares (como no QLP), com piso de 0,2 d.
- **O período máximo real.** O TLS, por padrão, só testa períodos com espaço para 2 trânsitos, então o teto real era metade do intervalo de dados e `period_max_fraction_of_span` não fazia nada. O projeto agora deixa o TLS ir até o intervalo inteiro e aplica ele mesmo o limite de 0,9; o vetting continua exigindo 2 trânsitos.
- **Teto de 40 dias.** Na busca com vários setores separados por anos (dados cobrindo ~800 dias), a grade ficava enorme e gerava aliases espúrios de 26 a 64 dias com 1 ou 2 trânsitos.

Resultado acumulado das mudanças até 2026-10-09: recall de 84,4 % para 91,1 % nos TOIs detectáveis. As mudanças de 2026-10-10 ainda precisam de uma nova medição.

### O que o PlanetHunter mede depois do TLS

O TLS dá o período, o instante do trânsito, a profundidade e o SDE. Quatro outros números são medidos de novo pelo projeto, porque todas as etapas seguintes dependem deles:

- **Duração (T14).** O TLS multiplica a duração pela fração do tempo que tem dados (o fator de preenchimento). Para um setor, isso fica um pouco abaixo de 1 (0,86 no setor 69), e as durações saíam cerca de 15 % curtas. Com dois setores separados por anos, o fator é minúsculo: um trânsito de 3 h saía com 0,23 h. O projeto divide pelo fator de preenchimento e guarda o T14 físico.
- **SNR.** Medido na curva achatada, contando como "em trânsito" os pontos a menos de meio T14 do centro do trânsito, e com um ruído robusto (MAD) dos pontos de fora.
- **S/N_pink.** O SNR com o ruído vermelho incluído (aula [M1](m1-statistics-for-signals.md)), guardado para o vetting.
- **Número de trânsitos.** Uma época só conta se pelo menos 50 % do tempo de trânsito esperado tem dados. Um trânsito quase todo perdido numa lacuna não conta mais.

A auditoria mostrou por que isso importa: o T14 encolhido era usado em tudo depois (o SNR, o mascaramento na busca iterativa, as janelas dos testes de vetting), e um só erro se espalhava pelo pipeline inteiro.

## Aliases: os picos fantasmas

Um **alias** é um período errado que é múltiplo ou fração simples do verdadeiro. Por que eles aparecem?

- **Em 2P**, você dobra a curva com o dobro do período. Metade dos trânsitos cai na fase 0 e a outra metade na fase 0,5. A caixa em fase 0 ainda pega trânsitos de verdade, com metade dos pontos. Pico mais baixo, mas pico.
- **Em P/2**, cada "trânsito" previsto alterna entre um real e um vazio. A profundidade média cai pela metade.
- **Em P/3, 3P/2, 2P/3**, a mesma lógica, com frações diferentes.

Exemplo medido na aula [M4](m4-tess-data-in-python.md), com o BLS do Lightkurve em Pi Men c (setor 1): pico principal em 6,27 d com potência 1 400; picos menores em 12,53 d (2P, potência 857), 3,13 d (P/2, potência 746), além de 9,4 d (3P/2) e 2,09 d (P/3). No período P/2, a profundidade calculada cai de 228 para 126 ppm: cerca de metade, como a explicação prevê.

!!! warning "Binária com período 2P"
    Uma binária eclipsante com duas estrelas parecidas tem dois eclipses por órbita. A busca acha o período P entre eclipses consecutivos, que é **metade** do período orbital verdadeiro. É por isso que o teste `odd_even` compara trânsitos ímpares e pares: se as estrelas forem um pouco diferentes, os eclipses alternados terão profundidades diferentes.

### O caso P/3 e o `refine_alias`

Com poucos trânsitos e lacunas nos dados, o TLS às vezes prefere um terço do período verdadeiro. Imagine um planeta de 12,6 d num setor de 27 d: dois trânsitos. Em P/3 = 4,2 d, o TLS prevê seis trânsitos. Dois são reais; os outros quatro caem em lacunas ou são diluídos na média. O pico em P/3 pode ganhar.

Foi exatamente o que aconteceu no setor 69: **TOI 899.01, 924.01 e 3262.01** (períodos de 12 a 13 dias) saíam com cerca de 4,2 d.

A correção, a função `refine_alias` em `search/tls.py`, faz um teste direto para k = 3 e k = 2:

1. Divide as épocas previstas por P em dois grupos: **A**, as que também seriam previstas por kP, e **B**, as que só existem em P.
2. Mede a profundidade em cada grupo.
3. Aceita kP se o grupo A mostra trânsito (mais de 3 sigma), o grupo B **tem dados** mas não mostra trânsito (menos de 3 sigma), e a profundidade de A é mais de 3 vezes a de B.

Em palavras: se os trânsitos "extras" previstos por P caem em dados bons e não aparecem, o período verdadeiro é o maior. O SNR é então medido de novo só com os trânsitos do período verdadeiro (antes, ele ficava baixo demais por um fator de até 0,58). O dossiê mostra o resultado no campo "Applied alias factor" (fator de alias aplicado).

## Busca iterativa com mascaramento

Uma estrela pode ter mais de um planeta. O TLS só devolve o pico mais forte. Solução:

1. Busque e ache o sinal mais forte.
2. **Apague** (mascare) os pontos dos trânsitos dele, numa janela de 2 durações (`mask_width_durations: 2.0`, usando o T14 físico).
3. Busque de novo na curva que sobrou.
4. Repita até 3 vezes (`max_signals_per_target: 3`) ou até o SDE cair abaixo de 7.

Para Pi Men c, depois de mascarar os 5 trânsitos, a segunda busca do BLS não acha nada relevante (melhor pico com 37 ppm e destaque baixo). É o esperado: no setor 1, só Pi Men c transita.

!!! tip "Na ferramenta"
    A busca está em `search_periodic` (`src/planethunter/search/tls.py`). Cada sinal sai com `iteration` (0, 1, 2), `sde`, `snr`, `n_transits`, `alias_factor` e a janela de detrending usada. No vetting, o teste `independence` verifica se um sinal sobrevive quando os sinais mais fortes da mesma estrela são mascarados: no setor 69, o sinal 1601 (11,95 d) estava reaproveitando os eclipses do sinal 1600 (6,75 d) e foi vetado.

## Detrending: a janela que decide

Antes da busca, a curva precisa ser **achatada**: a variação lenta da estrela (rotação, manchas) é removida para deixar os trânsitos visíveis. O PlanetHunter usa o filtro **biweight** da biblioteca wotan: para cada ponto, estima a tendência local numa janela de largura fixa, de forma robusta (ignora pontos discrepantes como os do trânsito), e divide a curva por ela.

O dilema: se a janela for **curta**, o filtro segue também o trânsito e o "come". Se for **longa**, deixa sobrar a variabilidade rápida da estrela.

Medido pelo projeto com um trânsito sintético em caixa de 1 500 ppm, sem variabilidade:

| Janela | Trânsito de 3 h | Trânsito de 5 h |
|---|---|---|
| 0,5 d | perde 8 % da profundidade | perde **40 %** |
| 1,0 d | perde 0 % | perde 6 % |

A regra prática é uma janela de cerca de 3 vezes a duração do trânsito mais longo procurado. O padrão é **1,0 d** (`window_length_days`). Trânsitos de 5 a 6 h aparecem em períodos de 20 a 40 d numa estrela como o Sol (aula M2) ou em períodos menores em estrelas maiores.

### Variantes de detrending

Uma janela só não serve para todas as estrelas. O sistema mede a sobra de variabilidade depois do achatamento pela razão entre a dispersão da curva e o ruído ponto a ponto, as duas medidas com a MAD (aula M1). A MAD importa: com o desvio padrão, um trânsito profundo inflava a razão sozinho e empurrava o sistema para janelas curtas, justamente as que comem trânsitos. Se passar de 1,2 (`red_noise_max`), refaz com janelas de 0,5 d e depois 0,3 d (`fallback_windows_days`). E busca nas **duas** versões, padrão e adaptativa, juntando os sinais (o de maior SDE vence quando dois têm o mesmo período).

Por que as duas? Dois casos reais do setor 69:

- **TOI 862.01** (5 092 ppm): a estrela varia rápido. Com janela de 1,0 d, a razão de ruído ficava bem acima de 1,2 e o sinal sumia. Com 0,5 d, aparece com SDE 18.
- **TOI 190.01** (trânsito de 5,7 h): com janela de 0,3 d, a profundidade de 8 248 ppm virava 347 ppm. A janela curta comeu o trânsito.

Só a janela curta perde o segundo; só a longa perde o primeiro. Buscar nas duas e juntar salvou ambos.

### Achatar de novo para o vetting

Depois que um sinal é achado, a duração e os instantes dos trânsitos são conhecidos. O vetting então achata cada setor de novo, com a janela que aquele setor usou na busca, mas nunca menor que 3 vezes o T14, e com os trânsitos **mascarados**: o filtro não os vê e traça a tendência por cima deles (Hippke et al. 2019). Medido com um trânsito de 12 h: uma janela simples de 1,0 d mantém 50 % da profundidade; esse achatamento com máscara mantém 99 %. A mesma curva alimenta os testes de vetting, o FPP e o dossiê.

Mais dois cuidados na limpeza: remover pontos discrepantes **só para cima** (`sigma_upper: 4.0`), nunca para baixo; e não cortar as bordas dos segmentos (`edge_cutoff_days: 0.0`), para preservar eventos únicos perto delas.

!!! example "Exercício 1"
    Um candidato tem trânsitos de 5 horas e profundidade verdadeira de 1 500 ppm. Que profundidade você espera medir com janela de 0,5 d? E com 1,0 d? Se o ruído der SNR 10 com a profundidade verdadeira, o sinal passaria no limite de SNR com a janela de 0,5 d?

    ??? success "Ver resposta"
        Com 0,5 d, perde 40 %: mede-se cerca de 1 500 × 0,6 = **900 ppm**. Com 1,0 d, perde 6 %: cerca de **1 410 ppm**.

        O SNR é proporcional à profundidade. Com 0,5 d: 10 × 0,6 = **6,0**, abaixo de 7,1. O portão `snr` vetaria o sinal. Com 1,0 d: 10 × 0,94 = 9,4, passa. A escolha da janela, sozinha, decide se esse planeta é achado.

## Lacunas e bordas de segmento

Os dados do TESS não são contínuos. Um setor de ~27 dias tem uma **lacuna** no meio para enviar dados à Terra, e às vezes outras por problemas. Cada trecho contínuo é um **segmento**.

Lacunas atrapalham de três jeitos:

1. **Trânsitos perdidos.** Um trânsito que cai na lacuna não existe nos dados. Com período longo, isso pode deixar um único trânsito, e o sinal é vetado por `n_transits`.
2. **Aliases.** É a lacuna que permite o caso P/3: os trânsitos "extras" caem nela e ninguém desmente o período curto.
3. **Bordas.** Nas pontas de cada segmento, o detrending tem dados de um lado só e pode criar **rampas** artificiais. O projeto mediu: ruído puro, com variabilidade de 2 000 ppm, gerou SDE ~10 num período igual a uma órbita do TESS, com o "evento" a 0,07 d da borda.

Por isso cada sinal sai com `edge_transit_fraction`: a fração dos trânsitos com dados cujo centro está a menos de 0,5 d (`edge_window_days`) de uma borda de segmento. Sinais com mais de 50 % dos trânsitos em bordas (`max_edge_transit_fraction: 0.5`) não viram candidatos, e o teste `edges_dumps` do vetting reprova pelo mesmo critério (ou se mais de 50 % caem perto de um ajuste de apontamento, o *momentum dump*).

!!! example "Exercício 2"
    Pi Men c no setor 1 teve 5 trânsitos, nos instantes BTJD 1325,50; 1331,77; 1338,04; 1344,31 e 1350,57. Os dados começam em 1325,30, terminam em 1353,18 e há uma lacuna entre 1338,52 e 1339,66. Calcule `edge_transit_fraction`. O sinal seria barrado?

    ??? success "Ver resposta"
        Distância de cada trânsito à borda mais próxima:

        - 1325,50: a 0,20 d do início (1325,30). **Em borda.**
        - 1331,77: longe de qualquer borda.
        - 1338,04: a cerca de 0,48 d do início da lacuna (1338,52). **Em borda.**
        - 1344,31 e 1350,57: longe das bordas (o fim dos dados está em 1353,18).

        São 2 de 5: **edge_transit_fraction = 0,4**. É exatamente o valor que o PlanetHunter calcula para esse sinal. Como 0,4 ≤ 0,5, o sinal **não** é barrado, e o teste `edges_dumps` passa.

!!! tip "Na ferramenta"
    No dossiê, a seção **"Light curve"** (curva de luz) mostra os trânsitos em linhas vermelhas e os ajustes do telescópio em linhas azuis pontilhadas. Trânsitos colados numa borda de segmento ou numa linha azul são sinal de alerta. A nota do teste `edges_dumps` diz as duas frações: "at momentum dump X%, at segment edge Y%" (em momentum dump, em borda de segmento). A seção **Provenance** (proveniência) mostra a janela de detrending usada.

## Checklist da aula

- [ ] Sei explicar o BLS em três passos (dobrar, testar caixas, medir a melhora).
- [ ] Sei o que o TLS muda e por que isso ajuda planetas pequenos.
- [ ] Sei definir SDE e dizer de onde vem o limite 9.
- [ ] Sei explicar por que aparecem picos em 2P e P/2, e o que o `refine_alias` faz com P/3.
- [ ] Sei descrever a busca iterativa e o teste `independence`.
- [ ] Sei explicar o dilema da janela de detrending com os números medidos (40 % e 6 %).
- [ ] Sei calcular `edge_transit_fraction` para uma lista de trânsitos.
- [ ] Achei num dossiê o fator de alias e a janela de detrending.

## Para ir além

- Documentação do Astropy sobre Box Least Squares ([docs.astropy.org](https://docs.astropy.org/en/stable/timeseries/bls.html)): exemplos curtos de BLS em Python.
- Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39 (TLS), também no arXiv ([arXiv:1901.02015](https://arxiv.org/abs/1901.02015)). Leia a introdução e as figuras; a comparação com o BLS e a calibração do SDE estão lá.
- Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. O artigo original do BLS. Fica para o nível avançado ([A1](../advanced/a1-detection-algorithms.md)), mas a primeira figura já vale a visita.
- Hippke et al. (2019), *The Astronomical Journal* 158, 143: o artigo do wotan, com a comparação de filtros de detrending.
- No repositório, `docs/benchmarks/2026-10-09-s0069-history.md`: a tabela "Causes found and fixed" (causas encontradas e corrigidas) é o resumo desta aula em forma de diagnóstico.
