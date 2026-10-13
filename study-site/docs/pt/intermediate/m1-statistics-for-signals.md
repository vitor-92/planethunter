# M1. Estatística para sinais

<p class="meta">Nível médio · semanas 1–3 · cerca de 15 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Média, mediana, desvio padrão e MAD, e por que o PlanetHunter prefere a mediana.
    - O que significa "3 sigma" e por que o sistema exige SNR de 7,1.
    - Por que a razão sinal-ruído cresce com a raiz do número de pontos.
    - A diferença entre ruído branco e ruído vermelho, e como o projeto mede o vermelho em blocos.
    - Como o teste qui-quadrado verifica se vários trânsitos "concordam".
    - Como ler o intervalo de confiança de um recall, como 123/135.

## Por que estatística

Toda medida de brilho do TESS vem com um erro. Se você medir a mesma estrela duas vezes, com dois minutos de diferença, os números não serão iguais. Essa flutuação é o **ruído**.

Um trânsito de Pi Men c derruba o brilho em cerca de 300 ppm. O ruído de cada ponto dessa estrela é de cerca de 130 ppm. Ou seja: em qualquer ponto isolado, o trânsito é só duas vezes maior que a flutuação normal. Mesmo assim, o planeta é detectado com folga. A estatística explica como.

A pergunta central desta aula é sempre a mesma: **essa queda é real ou pode ser acaso?**

## Média, mediana e desvio padrão

Imagine cinco medidas de brilho normalizado (1,0 = brilho normal), em ppm de desvio:

| Medida | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Desvio (ppm) | −120 | +80 | +10 | −40 | +3 000 |

A quinta é um **flare**, uma explosão na superfície da estrela, ou um raio cósmico.

- **Média**: soma dividida pela quantidade. $(-120 + 80 + 10 - 40 + 3000)/5 = 586$ ppm. Um único ponto ruim arrastou a média para longe de tudo.
- **Mediana**: ordene e pegue o do meio. Ordenado: −120, −40, 10, 80, 3 000. Mediana = 10 ppm. O flare não muda nada.
- **Desvio padrão** ($\sigma$): o tamanho típico da flutuação em torno da média. É a raiz da média dos quadrados das diferenças. Também é muito sensível a pontos extremos.

A mediana é **robusta**: aguenta pontos absurdos sem se mover. Por isso o PlanetHunter usa a mediana para definir o nível de brilho "normal" fora do trânsito.

### MAD: o desvio padrão robusto

O **MAD** (*median absolute deviation*, desvio absoluto mediano) faz para o desvio padrão o que a mediana faz para a média:

1. Calcule a mediana dos dados.
2. Calcule a distância de cada ponto até essa mediana.
3. Tire a mediana dessas distâncias.

Para dados com distribuição normal, $\sigma \approx 1{,}4826 \times \text{MAD}$. É exatamente essa conta que o vetting usa (função `_robust_sigma` em `vetting/basic.py`).

O MAD também decide quais pontos jogar fora na limpeza. O PlanetHunter remove pontos **acima** de mediana + 4 × (1,4826 × MAD), o `sigma_upper: 4.0` do `config/thresholds.yaml`. Nunca remove para baixo: um trânsito é justamente uma sequência de pontos abaixo do normal.

!!! example "Exercício 1"
    Calcule o MAD e o sigma robusto das cinco medidas da tabela acima (−120, +80, +10, −40, +3 000 ppm). Compare com o desvio padrão comum (amostral), que é cerca de 1 350 ppm.

    ??? success "Ver resposta"
        Mediana = 10 ppm. Distâncias até 10: 130, 70, 0, 50, 2 990. Ordenadas: 0, 50, 70, 130, 2 990. Mediana delas: **MAD = 70 ppm**.

        Sigma robusto = 1,4826 × 70 ≈ **104 ppm**.

        O desvio padrão comum dá cerca de 1 350 ppm, treze vezes mais, por causa de um único ponto. Com o sigma robusto, o flare fica a (3 000 − 10)/104 ≈ 29 sigmas da mediana e seria removido pelo corte de 4 sigmas.

## A distribuição normal e o "sigma"

Quando o ruído vem de muitas pequenas causas independentes, os valores se distribuem numa **curva normal** (ou gaussiana), o famoso sino. Ela tem uma propriedade útil: a chance de um valor cair longe da média depende só de quantos $\sigma$ ele está afastado.

| Afastamento | Chance de ruído puro passar desse valor (só para baixo) |
|---|---|
| 1 σ | 16 % |
| 2 σ | 2,3 % |
| 3 σ | 0,13 % (1 em 740) |
| 5 σ | 0,000029 % (1 em 3,5 milhões) |
| 7,1 σ | cerca de 6 × 10⁻¹³ (1 em 1,6 trilhão) |

Dizer que um sinal tem "3 sigma" é dizer: se fosse só ruído normal, um valor desses apareceria 1 vez em 740.

### Por que 3 sigma não basta: o efeito de olhar em todo lugar

1 em 740 parece raro. Mas a busca do PlanetHunter testa milhares de períodos e, para cada um, milhares de posições e durações de trânsito. São milhões de tentativas por estrela, e há cerca de 20 000 estrelas por setor. Com um milhão de tentativas, o ruído puro produz cerca de 1 350 "sinais" de 3 sigma. Isso se chama **efeito de olhar em todo lugar** (*look-elsewhere effect*).

O limite de **7,1 sigma** vem da missão Kepler (Jenkins, Caldwell & Borucki, 2002). Foi escolhido para que, numa busca do tamanho da do Kepler, o ruído branco gaussiano produzisse menos de um falso alarme no total. O TESS e o PlanetHunter herdaram esse valor (`snr_min: 7.1`).

!!! warning "Ruído real não é normal"
    A tabela acima vale para ruído gaussiano ideal. Ruído de verdade tem caudas mais gordas. O projeto mediu isso: procurando um sinal numa faixa estreita de períodos em estrelas **sem** sinal (144 tentativas), o SNR mediano foi 5,2, mas 10 % das tentativas passaram de 19 e 1 % passou de 98. Por isso SNR ≥ 7,1 é necessário, mas não suficiente. O vetting existe para isso.

## SNR e a raiz de N

A **razão sinal-ruído** (SNR) compara o tamanho da queda com a incerteza com que você a mede.

A ideia chave: **a média de N pontos independentes tem erro $\sigma/\sqrt{N}$**. Uma medida isolada flutua $\sigma$. A média de 4 medidas flutua $\sigma/2$. A de 100 medidas, $\sigma/10$. O ruído se cancela parcialmente ao somar, porque uns pontos sobem e outros descem.

Num trânsito, medimos a profundidade como a média dos pontos dentro do trânsito menos o nível normal. Então:

$$
\text{SNR} \approx \frac{\delta}{\sigma / \sqrt{N_\text{em trânsito}}} = \frac{\delta}{\sigma}\sqrt{N_\text{em trânsito}}
$$

em que $\delta$ é a profundidade e $\sigma$ o ruído de um ponto.

### Exemplo numérico: Pi Men c no setor 1

Números medidos ao rodar a aula [M4](m4-tess-data-in-python.md) com Lightkurve:

- profundidade média (modelo de caixa): $\delta \approx 228$ ppm. É menos que os ~300 ppm do fundo do trânsito, porque a caixa faz a média incluindo as bordas inclinadas; a aula [M2](m2-transit-physics.md) explica;
- ruído de um ponto de 2 minutos, depois do achatamento: $\sigma \approx 128$ ppm;
- duração do trânsito: cerca de 0,12 dia, ou seja, uns **86 pontos** de 2 minutos por trânsito;
- trânsitos no setor: **5**, total de cerca de 430 pontos em trânsito.

Com um trânsito só:

$$
\text{SNR}_1 = \frac{228}{128/\sqrt{86}} = \frac{228}{13{,}8} \approx 16{,}5
$$

Com os cinco:

$$
\text{SNR}_5 = \frac{228}{128/\sqrt{430}} = \frac{228}{6{,}17} \approx 37
$$

O PlanetHunter mede o SNR com o mesmo espírito, na própria curva achatada, usando a duração real do trânsito e uma estimativa robusta do ruído (baseada na mediana). O valor dele para esse sinal é da mesma ordem.

Repare na consequência: **para dobrar o SNR, você precisa de quatro vezes mais pontos**, ou seja, quatro vezes mais trânsitos. Por isso juntar setores ajuda tanto planetas pequenos, e por isso um planeta de período longo, com 2 trânsitos num setor, é difícil.

!!! example "Exercício 2"
    Uma estrela hipotética tem ruído de 1 000 ppm por ponto de 2 minutos. Um candidato tem profundidade 500 ppm e trânsitos de 3 horas.

    a) Qual o SNR de um único trânsito?
    b) Quantos trânsitos são necessários para chegar a SNR 7,1, supondo ruído branco?

    ??? success "Ver resposta"
        a) 3 horas = 180 minutos = 90 pontos de 2 minutos. Erro da média de um trânsito: $1000/\sqrt{90} = 105$ ppm. SNR = 500/105 ≈ **4,7**.

        b) Com $n$ trânsitos, SNR = $4{,}7\sqrt{n}$. Queremos $4{,}7\sqrt{n} \geq 7{,}1$, logo $\sqrt{n} \geq 1{,}51$ e $n \geq 2{,}3$. São necessários **3 trânsitos**. Com 2, o SNR fica em 6,7 e o sinal é vetado pelo portão `snr`.

## Ruído branco e ruído vermelho

O $\sqrt{N}$ só funciona se cada ponto flutua **independentemente** do vizinho. Isso é **ruído branco**: pense em chuvisco caindo, cada gota num lugar aleatório.

Na prática, há também flutuações que duram horas: a estrela pulsa, uma mancha gira, o telescópio balança um pouco, o detrending deixa sobras. Pontos vizinhos sobem e descem juntos. Isso é **ruído vermelho** (ou correlacionado). Pense em ondas no mar: não adianta fazer a média de dez medidas seguidas se as dez estão na mesma crista.

Com ruído vermelho, a média de N pontos vizinhos **não** cai como $\sigma/\sqrt{N}$. Ela para de cair num certo patamar. E uma ondulação de 2 horas, com 200 ppm, se parece muito com um trânsito.

### Como medir: o método de blocos de Pont et al. (2006)

Pont, Zucker & Queloz (2006) propuseram um modelo simples:

$$
\sigma_N^2 = \frac{\sigma_w^2}{N} + \sigma_r^2
$$

O primeiro termo é o ruído branco, que diminui com N. O segundo, $\sigma_r$, é o ruído vermelho, que **não** diminui. Para N grande, ele domina.

O jeito prático de medir é empírico:

1. Pegue a curva de luz **fora** dos trânsitos.
2. Corte-a em blocos de N pontos consecutivos (N = número de pontos de um trânsito).
3. Calcule a média de cada bloco.
4. Meça o desvio padrão dessas médias.

Se o ruído fosse branco, esse desvio seria $\sigma/\sqrt{N}$. Se der mais, há ruído vermelho, e é esse valor maior que você deve usar como erro.

!!! tip "Na ferramenta"
    A classe `BlockNoise` em `src/planethunter/vetting/basic.py` faz exatamente isso. O erro da média de N pontos é o **maior** entre $\sigma/\sqrt{N}$ (com $\sigma$ robusto, via MAD) e o desvio padrão das médias de blocos de N pontos, medido fora do trânsito. Ela é usada nos testes `odd_even`, `secondary`, `secondary_scan` e `consistency`.

    O motivo foi medido no setor 69: com o erro ingênuo $\sigma/\sqrt{N}$, **4 de 41 planetas confirmados** reprovavam no teste de consistência entre trânsitos. O erro estava pequeno demais, e diferenças normais pareciam significativas.

    A mesma ideia também dá uma medida de detecção, o **S/N_pink** ("pink", rosa, porque mistura ruído branco e vermelho). É o SNR calculado com o erro da fórmula acima, usando $\sigma_r$ medido em blocos do tamanho do trânsito. Ele é sempre menor ou igual ao SNR simples, e bem menor quando a estrela tem oscilações lentas que duram horas. O pipeline de visão rápida do TESS (QLP) exige S/N_pink ≥ 9; no PlanetHunter, um sinal abaixo de 9 leva uma falha leve no teste `snr_pink` (aula [M5](m5-vetting-in-practice.md)).

    Há um segundo indicador na limpeza: a razão entre a dispersão da curva e o ruído ponto a ponto (`red_noise_ratio` em `preprocess/clean.py`), as duas medidas com a MAD para que um trânsito profundo não a infle. Para ruído branco ela vale cerca de 1. Acima de 1,2, o sistema refaz o detrending com janelas menores. A estrela do TOI 862.01 passava bem desse limite com a janela padrão. Veja a aula [M3](m3-periodograms.md).

!!! example "Exercício 3"
    Fora do trânsito, uma curva tem sigma robusto de 600 ppm por ponto. Um trânsito tem 36 pontos. Você corta a curva em blocos de 36 pontos e o desvio padrão das médias dos blocos dá 220 ppm.

    a) Qual seria o erro da média de 36 pontos se o ruído fosse branco?
    b) Que erro o `BlockNoise` usa?
    c) Um trânsito isolado de 500 ppm: qual o SNR em cada caso?

    ??? success "Ver resposta"
        a) $600/\sqrt{36} = 600/6 = 100$ ppm.

        b) O maior entre 100 e 220: **220 ppm**. Há ruído vermelho forte; os blocos flutuam mais que o dobro do esperado.

        c) Ruído branco: 500/100 = 5,0. Com blocos: 500/220 ≈ 2,3. A conta ingênua faria o trânsito parecer duas vezes mais confiável do que é.

## Qui-quadrado: os trânsitos concordam entre si?

Um planeta real produz trânsitos iguais toda órbita. Se um dos trânsitos é muito mais fundo que os outros, algo está errado: um evento instrumental, um flare invertido, ou dois fenômenos misturados.

Como decidir se as diferenças são "normais"? Com o **teste qui-quadrado** ($\chi^2$):

1. Meça a profundidade de cada trânsito, $d_i$, e o erro de cada uma, $\sigma_i$ (aqui entra o `BlockNoise`).
2. Calcule a média ponderada $\bar d$ (trânsitos com erro menor pesam mais).
3. Some os desvios ao quadrado, em unidades de erro:

$$
\chi^2 = \sum_i \left(\frac{d_i - \bar d}{\sigma_i}\right)^2
$$

Se as diferenças forem só ruído, cada termo vale em média cerca de 1, e $\chi^2$ fica perto do número de **graus de liberdade**: número de trânsitos menos 1. Se der muito maior, os trânsitos não concordam.

O **valor-p** traduz $\chi^2$ em probabilidade: a chance de o ruído sozinho produzir uma discordância desse tamanho ou maior. O PlanetHunter reprova se p < 0,001 (`transit_consistency_pvalue_min`).

O teste tem um segundo critério: com 3 ou mais trânsitos, reprova se um único trânsito responde por mais de 80 % do SNR² total. É o caso "um evento estranho dominando".

!!! example "Exercício 4"
    Cinco trânsitos com profundidades 290, 270, 310, 280 e 300 ppm, todos com erro 25 ppm.

    a) Calcule $\chi^2$ e diga se passa no teste.
    b) Troque o último por 600 ppm. O que acontece?

    Dado: com 4 graus de liberdade, p = 0,001 corresponde a $\chi^2 \approx 18{,}5$.

    ??? success "Ver resposta"
        a) Média (pesos iguais) = 290 ppm. Desvios: 0, −20, +20, −10, +10. Em unidades de erro: 0; −0,8; 0,8; −0,4; 0,4. Quadrados: 0; 0,64; 0,64; 0,16; 0,16. **$\chi^2 = 1{,}6$**, bem abaixo de 18,5. O valor-p é cerca de 0,81. **Passa.**

        b) Média = 350 ppm. Desvios: −60, −80, −40, −70, +250. Em erros: −2,4; −3,2; −1,6; −2,8; 10. Quadrados: 5,76; 10,24; 2,56; 7,84; 100. **$\chi^2 \approx 126$**, valor-p da ordem de $10^{-26}$. **Reprova.** Um único trânsito discordante basta.

!!! warning "Armadilha: sinais muito fortes"
    Quando o SNR é enorme, o erro de cada trânsito fica minúsculo, e diferenças reais mas inofensivas (um resíduo de detrending, um trânsito cortado por lacuna) viram dezenas de sigmas. No setor 69, planetas confirmados de alto SNR reprovaram em `consistency`: WASP-97 b (p ≈ $10^{-35}$), WASP-18 b (p ≈ $10^{-26}$), TOI-481 b. Por isso esse teste é uma **falha leve** (multiplica o score por 0,5), não um veto.

!!! tip "Na ferramenta"
    No dossiê, a seção **"Depth per transit"** (profundidade por trânsito) é o qui-quadrado em forma de gráfico: um ponto por trânsito, com barra de erro, e uma linha tracejada na média. Sinal bom: pontos alinhados na linha. Sinal ruim: um ponto muito longe dos outros. Na tabela de vetting, a linha `consistency` mostra o número de trânsitos, o valor-p e a fração do SNR² no maior trânsito.

## Intervalo de confiança binomial: quanto confiar num recall

O benchmark do projeto mede o **recall**: de 135 TOIs que deveriam ser detectáveis no setor 69, quantos o sistema encontra. Resultado: **123 de 135 = 91,1 %**.

Mas 135 é uma amostra pequena. Se você jogar uma moeda viciada 135 vezes, a fração de caras varia de uma rodada para outra. O mesmo vale aqui. A pergunta certa é: qual faixa de recall "verdadeiro" é compatível com 123/135?

Uma conta aproximada: o erro de uma proporção $p$ medida em $n$ casos é

$$
\text{EP} = \sqrt{\frac{p(1-p)}{n}} = \sqrt{\frac{0{,}911 \times 0{,}089}{135}} \approx 0{,}0245
$$

ou seja, 2,45 pontos percentuais. O intervalo de 95 % é cerca de ±1,96 EP: de 86,3 % a 95,9 %.

O relatório do projeto usa uma fórmula melhor, o **intervalo de Wilson**, que não deixa a faixa passar de 100 % e fica assimétrica perto das bordas. Resultado: **85,1 % a 94,8 %**. Em linguagem simples: o recall verdadeiro do sistema, nesse tipo de alvo, está muito provavelmente entre 85 % e 95 %.

Consequência prática: uma mudança que leva o recall de 120/135 (88,9 %) para 123/135 (91,1 %) é **compatível com acaso**. Três TOIs a mais não provam melhora sozinhos. É preciso olhar quais TOIs mudaram e por quê, como o relatório de histórico faz.

!!! example "Exercício 5"
    Calcule, com a aproximação simples, o intervalo de 95 % para o primeiro run do benchmark: 114 de 135 (84,4 %). Ele se sobrepõe ao intervalo do run final (85,1 % a 94,8 %)?

    ??? success "Ver resposta"
        $p = 0{,}844$. EP = $\sqrt{0{,}844 \times 0{,}156 / 135} = \sqrt{0{,}000975} \approx 0{,}0312$. Intervalo: 0,844 ± 1,96 × 0,0312 = 0,844 ± 0,061, ou seja, **78,3 % a 90,5 %**.

        Sim, sobrepõe (de 85,1 % a 90,5 %). Mesmo assim, a melhora de 114 para 123 é mais convincente do que os números sozinhos sugerem, porque o relatório mostra a **causa** de cada TOI recuperado (limites estelares, janela, alias). Estatística e diagnóstico andam juntos.

## Checklist da aula

- [ ] Sei calcular média, mediana, desvio padrão e MAD à mão para poucos números.
- [ ] Sei explicar por que o PlanetHunter usa mediana e MAD na limpeza.
- [ ] Sei o que significa "3 sigma" e por que o limite do sistema é 7,1.
- [ ] Sei calcular o SNR de um trânsito a partir de profundidade, ruído por ponto e número de pontos.
- [ ] Sei explicar ruído vermelho com uma analogia e descrever o método de blocos.
- [ ] Sei calcular um qui-quadrado simples e interpretar o valor-p.
- [ ] Sei explicar por que 91 % de recall com 135 objetos pode ser algo entre 85 % e 95 %.
- [ ] Abri um dossiê, achei a seção "Depth per transit" e a linha `consistency` da tabela de vetting.

## Para ir além

- Khan Academy em português, trilha de estatística e probabilidade ([pt.khanacademy.org](https://pt.khanacademy.org/math/statistics-probability)): estatística descritiva e distribuição normal. Faça antes se média e desvio padrão ainda parecem estranhos.
- Pont, Zucker & Queloz (2006), *Monthly Notices of the Royal Astronomical Society* 373, 231. O artigo que formalizou o ruído vermelho em trânsitos. Leia a introdução e as figuras.
- Jenkins, Caldwell & Borucki (2002), *The Astrophysical Journal* 564, 495. De onde vem o limite de 7,1 sigma do Kepler, herdado pelo TESS.
- Wilson (1927), *Journal of the American Statistical Association* 22, 209. A origem do intervalo usado nos relatórios de benchmark; curto e legível.
- No repositório do PlanetHunter, `docs/benchmarks/2026-10-09-s0069-history.md`: o recall de cada run com o intervalo de 95 %. Bom para treinar a leitura de proporções com incerteza.
