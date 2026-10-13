# M2. Física do trânsito

<p class="meta">Nível médio · semanas 3–5 · cerca de 12 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - A terceira lei de Kepler e como ela liga período, distância e densidade da estrela.
    - Como prever a duração de um trânsito, a fórmula usada no teste `duration`.
    - O que é o parâmetro de impacto e por que trânsitos rasantes têm formato em V.
    - Por que o fundo do trânsito é arredondado (escurecimento de borda).
    - A diferença entre o eclipse secundário de uma binária e a ocultação de um planeta, com o caso WASP-18 b.
    - Por que um trânsito curto demais numa estrela gigante indica blend.

## Terceira lei de Kepler

Em 1619, Johannes Kepler descobriu que, quanto mais longe um planeta está do Sol, mais tempo ele leva para dar uma volta. Newton depois mostrou a fórmula exata. Para um planeta de massa desprezível em órbita circular de raio $a$ em torno de uma estrela de massa $M_\star$:

$$
P^2 = \frac{4\pi^2 a^3}{G M_\star}
$$

$G$ é a constante gravitacional. Em palavras: o quadrado do período é proporcional ao cubo da distância.

Para trânsitos, a distância em quilômetros importa menos. O que importa é a distância **em raios da estrela**, $a/R_\star$. E aqui acontece algo bonito. Escreva a massa da estrela como volume vezes densidade, $M_\star = \tfrac{4}{3}\pi R_\star^3 \rho_\star$, e substitua:

$$
\left(\frac{a}{R_\star}\right)^3 = \frac{G \rho_\star P^2}{3\pi}
$$

O raio e a massa sumiram separadamente. Sobrou só a **densidade média da estrela**, $\rho_\star$. Dado o período, $a/R_\star$ depende só de quão compacta é a estrela.

Dois valores para ancorar:

- Terra e Sol: $a/R_\star \approx 215$. A densidade média do Sol é 1,41 g/cm³.
- Como $a/R_\star \propto P^{2/3}$, um planeta de 10 dias em torno do Sol tem $a/R_\star = 215 \times (10/365{,}25)^{2/3} \approx 19{,}5$.

## A duração do trânsito

Pense no planeta como um carro numa pista circular. A pista tem comprimento $2\pi a$, e o carro leva o período $P$ para dar uma volta. Durante o trânsito, ele percorre só o trecho que fica na frente do disco da estrela. Num trânsito central, esse trecho tem comprimento de cerca de $2R_\star$ (mais o diâmetro do próprio planeta). Então:

$$
T_{14} \approx \frac{P}{2\pi a} \times 2R_\star(1+k) = \frac{P}{\pi}\,\frac{R_\star}{a}\,(1+k)
$$

em que $k = R_p/R_\star$. $T_{14}$ é a duração total, do primeiro ao quarto contato (do primeiro toque do planeta no disco até a saída completa).

A forma exata, usada pelo PlanetHunter na função `predicted_duration_days` de `vetting/basic.py`, para órbita circular e trânsito central ($b = 0$):

$$
T_{14} = \frac{P}{\pi}\,\arcsin\!\left(\frac{1+k}{a/R_\star}\right), \qquad \frac{a}{R_\star} = \left(\frac{G\rho_\star P^2}{3\pi}\right)^{1/3}
$$

Como $a/R_\star$ costuma ser bem maior que 1, o arco-seno quase não muda o resultado. Juntando tudo, a duração cresce com $P^{1/3}$ e cai com $\rho_\star^{1/3}$. Estrelas grandes e pouco densas (gigantes) têm trânsitos longos. Estrelas pequenas e densas (anãs vermelhas) têm trânsitos curtos.

Durações previstas para trânsito central numa estrela igual ao Sol:

| Período | 1 d | 3 d | 5 d | 10 d | 20 d | 40 d | 1 ano |
|---|---|---|---|---|---|---|---|
| $T_{14}$ (b = 0) | 1,8 h | 2,6 h | 3,1 h | 3,9 h | 4,9 h | 6,2 h | 13,0 h |

!!! example "Exercício 1"
    Estime a duração de um trânsito central ($b = 0$) de um planeta com período de 10 dias numa estrela igual ao Sol. Use $T_{14} \approx (P/\pi)(R_\star/a)$, ignorando o tamanho do planeta. Depois compare com o valor de um dossiê real.

    ??? success "Ver resposta"
        **Passo 1: $a/R_\star$.** Pela escala com a Terra: $a/R_\star = 215 \times (10/365{,}25)^{2/3}$. A razão 10/365,25 = 0,0274. Elevada a 2/3: 0,0908. Então $a/R_\star = 215 \times 0{,}0908 \approx 19{,}5$.

        Conferindo pela fórmula com densidade: $\rho_\odot = 1410$ kg/m³, $P = 864\,000$ s, $G = 6{,}674 \times 10^{-11}$. $G\rho P^2/(3\pi) = 6{,}674\times10^{-11} \times 1410 \times 7{,}46\times10^{11} / 9{,}42 \approx 7\,450$. Raiz cúbica: **19,5**. Bate.

        **Passo 2: duração.** $T_{14} \approx (10/\pi) \times (1/19{,}5) = 3{,}183 / 19{,}5 = 0{,}163$ dia. Em horas: 0,163 × 24 ≈ **3,9 horas**.

        Com um planeta do tamanho da Terra ($k \approx 0{,}009$), multiplique por 1,009: ainda 3,9 h. Com a fórmula exata (arco-seno), dá 3,91 h. A aproximação é excelente.

        **Comparação.** Num dossiê, a tabela de vetting mostra na linha `duration` algo como "T14 3.11 h vs predicted (b=0) 3.79 h" (*predicted* é a duração prevista). Esse é o caso de Pi Men c (período 6,27 d, estrela com 1,15 R☉ e 1,1 M☉). Se a estrela for parecida com o Sol e o período perto de 10 dias, espere um previsto perto de 3,9 h, e um observado igual ou menor.

!!! tip "Na ferramenta"
    O teste `duration` divide a duração observada (do ajuste de trapézio) pela prevista com $b = 0$. Passa se a razão estiver entre **0,15** e **1,67** (`duration_ratio_min` e `duration_ratio_max`). A massa vem do TIC; se faltar, é estimada a partir de $\log g$ e do raio. Sem raio da estrela, ou quando o ajuste bate no limite da faixa permitida (aí a duração não foi medida de verdade), o teste fica "sem dados" e o score é multiplicado por 0,95. Falhar é uma falha leve que custa um fator 0,6 no score. No dossiê, a seção **Parameters** mostra R*, M* e T14.

### Por que acima de 1,67 é suspeito

Para órbita circular, o trânsito central é o **mais longo possível**. Qualquer inclinação encurta a corda. Então uma duração bem maior que a prevista com $b = 0$ diz que alguma premissa falhou:

- a estrela é maior e menos densa do que o TIC diz (uma subgigante catalogada como anã);
- o sinal vem de **outra** estrela, maior, no mesmo pixel;
- a órbita é excêntrica, e o trânsito acontece longe do ponto mais próximo da estrela;
- o período está errado.

Por que 1,67 e não algo logo acima de 1? Porque o raio estelar do TIC tem erros e uma órbita excêntrica pode alongar um trânsito (Kipping 2010). O limite de 1,67 é o usado pelo LEO-Vetter (Kunimoto et al. 2025). O projeto usava 1,3 antes; quando mediu a mudança, subir o limite para 1,67 não reprovou nenhum planeta conhecido e deixou de reprovar dezenas de sinais novos cujo único problema era um trânsito um pouco longo.

Caso real do setor 69: o TOI-724.01 mostrou T14 = 8,40 h contra 3,56 h previstas, razão 2,36. Falha leve em `duration`.

### Por que abaixo de 0,15 é suspeito: o sinal 1594

Na primeira fatia real do setor 69 (2164 estrelas), o sinal **1594** chegou a P1 com score 1,0. Um candidato perfeito? Os números do dossiê:

- estrela TIC 31273263: raio 3,06 R☉, massa 1 M☉. É uma **gigante** (ou subgigante): três vezes o raio do Sol com a mesma massa;
- período 6,354 d, profundidade 1 091 ppm;
- duração observada: **0,58 h**;
- duração prevista com $b = 0$: **10,71 h**. Razão: 0,054.

Uma gigante tem densidade baixíssima: $\rho = 1/3{,}06^3 \approx 0{,}035$ vez a do Sol. Por isso $a/R_\star$ é pequeno (cerca de 4,7) e um planeta leva horas para cruzar o disco enorme. Um trânsito de meia hora não combina com essa estrela.

Para encurtar de 10,7 h para 0,58 h (fator 18,5) só mudando a estrela, a densidade teria de ser $18{,}5^3 \approx 6\,300$ vezes maior. Nem uma anã vermelha chega a tanto. As explicações plausíveis são: o sinal vem de **outra estrela**, menor e mais densa, misturada no mesmo pixel (um **blend**), provavelmente com eclipse rasante; ou é um trânsito extremamente rasante ($b \approx 0{,}99$) na própria gigante; ou não é um trânsito. Em qualquer caso, não é um candidato forte. Há outro indício na mesma direção: a estrela já tem objetos catalogados, e o código de severidade (`alerts/severity.py`) cita o sinal 1594 como exemplo de estrela que é binária eclipsante catalogada, caso em que um sinal novo quase sempre é eclipse.

Esse sinal motivou o limite inferior `duration_ratio_min: 0.15`, com o comentário no `config/thresholds.yaml` citando o próprio sinal 1594. Pela regra atual, essa falha multiplica o score por 0,6, e ele deixa de ser P1.

!!! example "Exercício 2"
    Refaça a previsão do sinal 1594. Dados: $P = 6{,}354$ d, $R_\star = 3{,}06$ R☉, $M_\star = 1$ M☉, $k = 0{,}033$. Use a escala com o Sol: $a/R_\star = 215 \times (P/365{,}25)^{2/3} \times (\rho_\star/\rho_\odot)^{1/3}$.

    ??? success "Ver resposta"
        Densidade relativa: $\rho_\star/\rho_\odot = M/R^3 = 1/28{,}65 = 0{,}0349$. Raiz cúbica: 0,327.

        Período: $6{,}354/365{,}25 = 0{,}0174$. Elevado a 2/3: 0,0671.

        $a/R_\star = 215 \times 0{,}0671 \times 0{,}327 \approx 4{,}72$.

        $T_{14} = (P/\pi)\arcsin((1+k)/(a/R_\star)) = 2{,}023 \times \arcsin(1{,}033/4{,}72) = 2{,}023 \times \arcsin(0{,}219) = 2{,}023 \times 0{,}221 = 0{,}447$ d = **10,7 h**. Exatamente o valor do dossiê.

        Razão observada/prevista: 0,58/10,7 = 0,054, abaixo de 0,15. Falha.

## Parâmetro de impacto e o formato em V

O **parâmetro de impacto** $b$ diz por onde o planeta cruza o disco da estrela, medido em raios estelares a partir do centro:

$$
b = \frac{a\cos i}{R_\star}
$$

em que $i$ é a inclinação da órbita (90° = vista exatamente de lado).

- $b = 0$: o planeta passa pelo centro. Corda mais longa.
- $b = 0{,}7$: passa por cima, corda menor.
- $b \approx 1$: raspa a borda. Trânsito **rasante**.

O comprimento da corda é proporcional a $\sqrt{(1+k)^2 - b^2}$. Para planetas pequenos, $T_{14} \approx T_{14}(b=0)\sqrt{1-b^2}$. Isso explica por que a razão do teste `duration` costuma ficar abaixo de 1 para planetas reais.

!!! example "Exercício 3"
    No setor 1, o PlanetHunter mediu para Pi Men c: T14 = 3,11 h, previsto com $b = 0$: 3,79 h. Estime o parâmetro de impacto.

    ??? success "Ver resposta"
        Razão: 3,11/3,79 = 0,82. Com $T_{14}/T_{14}(b=0) \approx \sqrt{1-b^2}$: $1 - b^2 = 0{,}82^2 = 0{,}672$, então $b^2 = 0{,}328$ e **$b \approx 0{,}57$**.

        É uma estimativa grosseira: o ajuste de trapézio, o raio do TIC e a massa estimada têm incerteza. Confira no NASA Exoplanet Archive o valor publicado para Pi Men c e compare.

### As rampas do trânsito

Um trânsito tem quatro contatos. Entre o 1º e o 2º, o planeta está **entrando** no disco (rampa de descida, duração $\tau$). Entre o 2º e o 3º, está inteiro na frente da estrela (fundo). Entre o 3º e o 4º, está saindo (rampa de subida).

Para planetas pequenos e $b$ não muito perto de 1 (Winn, 2010):

$$
\frac{\tau}{T_{14}} \approx \frac{k}{1-b^2}
$$

Duas coisas aumentam as rampas:

1. **$k$ grande.** Um planeta pequeno entra rápido: $k = 0{,}016$ dá rampas finíssimas. Uma estrela companheira com metade do raio da primária ($k = 0{,}5$) leva quase metade do eclipse entrando.
2. **$b$ perto de 1.** Num trânsito rasante, o planeta nunca fica inteiro sobre o disco. Não há fundo chato.

No limite, as rampas se encontram no meio e o trânsito vira um **triângulo**: o formato em V. Uma caixa ou um U sugere planeta. Um V sugere binária ou rasante.

!!! tip "Na ferramenta"
    O teste `shape` ajusta um **trapézio** na curva dobrada e mede $\tau/T_{14}$. O valor 0,5 é um triângulo perfeito. O limite atual é **0,35** (`v_shape_max`). O mesmo teste reprova se $R_p/R_\star > 0{,}3$ (`rp_rs_max`), tamanho de estrela, não de planeta.

    A calibração foi medida no setor 69. Com limite 0,45, o teste não pegava **nenhum** falso positivo. Com 0,35, pega **8 de 18** falsos positivos do TFOPWG e marca **3 de 50** planetas, todos rasantes reais: HIP 65 A b, LTT 9779 b e TOI-2382 b. Por isso começou como falha leve (peso 0,5). Desde a auditoria de 2026-10-10 é **falha grave**: uma falha sozinha reprova o veredito, mas continua não sendo veto. O custo medido é de uns 3 planetas rasantes por setor; o ganho é barrar binárias eclipsantes encontradas na metade do período.

    Valores medidos: Pi Men c 0,11; WASP-18 b 0,14; os falsos positivos TOI-297.01 0,42, TOI-4858.01 0,41 e TOI-189.01 0,41.

## Escurecimento de borda

Olhe uma foto do Sol: o centro é mais brilhante que a borda. Isso é o **escurecimento de borda** (*limb darkening*). Na borda, sua linha de visada atravessa a atmosfera da estrela de lado e só enxerga as camadas mais altas, que são mais frias e emitem menos.

Consequência para o trânsito: quando o planeta está no centro do disco, ele tapa a região mais brilhante, e a queda é maior. Perto da borda, tapa uma região mais escura, e a queda é menor. O fundo do trânsito deixa de ser chato e fica **arredondado**, em forma de U.

Isso afeta a medida da profundidade. Para Pi Men c no setor 1:

| Modelo | Profundidade |
|---|---|
| Caixa (BLS do Lightkurve, aula M4) | 228 ppm |
| Trapézio (vetting do PlanetHunter) | 272 ppm |
| Modelo do TLS, com escurecimento de borda | 287 ppm |

A caixa faz a média do trânsito inteiro, incluindo as rampas e as partes rasas do U. O modelo com escurecimento de borda captura o fundo mais profundo. É por isso que o TLS, que usa esse modelo, é mais sensível que o BLS (aula [M3](m3-periodograms.md)).

O arredondamento também infla um pouco o $\tau/T_{14}$ medido pelo trapézio: o ajuste interpreta a curvatura do fundo como rampa. Por isso planetas de verdade aparecem com 0,1 a 0,15, e não com o valor geométrico de 0,02.

## Eclipse secundário e ocultação planetária

Numa órbita circular, meio período depois do trânsito, o objeto passa **atrás** da estrela. O que se vê nesse momento, em **fase 0,5**, depende de quanto ele brilha.

- **Binária eclipsante.** A companheira é uma estrela e tem luz própria. Quando ela é escondida, o brilho total cai: é o **eclipse secundário**. Se as duas estrelas forem parecidas, os dois eclipses têm profundidades parecidas.
- **Planeta.** O planeta brilha muito pouco: luz refletida e calor. Quando ele some atrás da estrela, a queda é minúscula. Chama-se **ocultação**. Para quase todos os planetas, é invisível para o TESS.

A exceção são os **Júpiteres ultraquentes**. WASP-18 b orbita sua estrela em menos de um dia e é tão quente que o TESS vê sua luz sumir. A documentação do projeto registra cerca de 340 ppm em fase 0,5. No run final do setor 69, o teste `secondary` mediu 276 ppm, **3 % do primário** (que tem cerca de 10 300 ppm), com significância de 8 sigma. Uma queda real e significativa em fase 0,5, num planeta confirmado.

No primeiro dia do projeto, WASP-18 b era **vetado como binária**. A correção usou a física: a ocultação de um planeta é uma fração pequena do trânsito, enquanto o secundário de uma binária costuma ser uma fração grande. A regra atual veta só se as duas condições valem juntas:

- secundário com mais de 5 sigma (`secondary_veto_sigma`), **e**
- secundário com 10 % ou mais da profundidade do primário (`secondary_veto_ratio: 0.1`).

Entre 3 e 5 sigma, ou acima de 5 sigma mas abaixo de 10 %, é falha leve (peso 0,4).

Casos do setor 69 vetados por secundário: TOI-287.01 (4 503 ppm em fase 0,5, 37 % do primário), TOI-349.01 (1 376 ppm, 13 %) e TOI-187.01 (108 %, ou seja, dois eclipses praticamente iguais). Todos são falsos positivos do TFOPWG.

!!! warning "Órbitas excêntricas"
    Se a órbita for excêntrica, o secundário não cai em fase 0,5. O teste `secondary_scan` procura a maior queda em qualquer fase entre 0,1 e 0,9, com limite mais alto (5 sigma), porque olha em muitos lugares (lembre do efeito de olhar em todo lugar, aula M1). Ele foi criado porque a binária excêntrica TOI-367.01 passava em tudo.

!!! example "Exercício 4"
    Decida, com as regras do PlanetHunter, o resultado do teste `secondary` em cada caso:

    a) Primário de 8 000 ppm; queda em fase 0,5 de 400 ppm com 9 sigma.
    b) Primário de 3 000 ppm; queda em fase 0,5 de 600 ppm com 6 sigma.
    c) Primário de 3 000 ppm; queda em fase 0,5 de 600 ppm com 4 sigma.

    ??? success "Ver resposta"
        a) Razão 400/8 000 = 5 %. Significativo (9 > 5 sigma), mas abaixo de 10 %. **Falha leve, sem veto.** Compatível com ocultação de um planeta muito quente, como WASP-18 b.

        b) Razão 600/3 000 = 20 %, e 6 > 5 sigma. **Veto.** Perfil de binária eclipsante.

        c) Razão 20 %, mas só 4 sigma: passa de 3 sigma (falha) e não chega a 5 (sem veto). **Falha leve.** Vale olhar o painel "Odd, even and secondary" do dossiê e procurar o secundário em outros setores.

## Resumo: da física ao teste

| Física | Grandeza | Teste do vetting |
|---|---|---|
| Kepler + densidade estelar | $T_{14}$ previsto | `duration` |
| Parâmetro de impacto, $k$ grande | $\tau/T_{14}$ | `shape` |
| Profundidade $\approx k^2$ | $R_p$ | `radius`, `shape` ($R_p/R_\star$) |
| Companheira luminosa | queda em fase 0,5 | `secondary` |
| Órbita excêntrica | queda em outra fase | `secondary_scan` |

## Checklist da aula

- [ ] Sei escrever a terceira lei de Kepler e explicar por que $a/R_\star$ depende só da densidade da estrela.
- [ ] Calculei a duração de um trânsito de 10 dias numa estrela como o Sol (cerca de 3,9 h).
- [ ] Sei por que razão acima de 1,67 e abaixo de 0,15 no teste `duration` são suspeitas.
- [ ] Sei explicar o parâmetro de impacto e por que rasantes e binárias têm formato em V.
- [ ] Sei por que o fundo do trânsito é arredondado e por que a caixa subestima a profundidade.
- [ ] Sei a diferença entre eclipse secundário e ocultação, e a regra dos 10 %.
- [ ] Abri um dossiê e li as notas de `duration`, `shape` e `secondary` na tabela de vetting.

## Para ir além

- Winn (2010), "Transits and Occultations", gratuito no arXiv ([arXiv:1001.2010](https://arxiv.org/abs/1001.2010)). Seções 1 a 3. É o texto clássico: todas as fórmulas desta aula estão lá, com as derivações.
- Seager & Mallén-Ornelas (2003), *The Astrophysical Journal* 585, 1038. Mostra como tirar a densidade da estrela só da forma do trânsito; a base do teste `duration`.
- Página de Pi Men c no NASA Exoplanet Archive ([exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu)): compare o parâmetro de impacto publicado com o que você estimou no exercício 3.
- [Simulador de trânsito](../lab/transit-simulator.md) deste curso: mude os parâmetros e veja a forma da curva responder.
