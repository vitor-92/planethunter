# B2. O método de trânsito

<p class="meta">Nível básico · semanas 2–3 · cerca de 4 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Por que a luz de uma estrela cai quando um planeta passa na frente dela.
    - A regra principal: profundidade ≈ (raio do planeta / raio da estrela)².
    - O que período, duração e profundidade dizem sobre o sistema.
    - Por que só uma fração pequena dos planetas transita, e como calcular essa fração.
    - O que é uma curva de luz e como se mede uma queda em ppm.

## A geometria do trânsito

Volte à lanterna e à mosca da aula B1. A mosca bloqueia uma parte da luz proporcional à **área** dela comparada à área da lanterna. Com estrelas é igual: visto daqui, a estrela é um disco brilhante e o planeta é um disco escuro, muito menor, que atravessa esse disco.

```
  visto de lado (órbita de perfil)          visto daqui (o que o telescópio "vê")

   estrela        planeta                          .-""""-.
   (  O  )  ------- o ------->  nós              /          \
                                                |     ●      |   ● = disco escuro
   o planeta passa entre a estrela e nós        |            |       do planeta
                                                 \          /
                                                   '-....-'
```

A área de um disco é $\pi R^2$. A fração de luz bloqueada é a razão entre as duas áreas:

$$ \delta \approx \frac{\pi R_p^2}{\pi R_\star^2} = \left(\frac{R_p}{R_\star}\right)^2 $$

Aqui $\delta$ (letra grega "delta") é a **profundidade** do trânsito, $R_p$ é o raio do planeta e $R_\star$ é o raio da estrela. O $\pi$ cancela. Sobra só a razão dos raios, ao quadrado.

O quadrado é o detalhe mais importante da aula. Dobre o raio do planeta e a profundidade quadruplica. Reduza o raio da estrela à metade e a profundidade também quadruplica.

!!! note "Por que \"aproximadamente\""
    A regra supõe que a estrela brilha igual em todo o disco. Na verdade, a borda de uma estrela é um pouco mais escura que o centro (**escurecimento de borda**, assunto da aula M2). Isso arredonda o fundo do trânsito e muda a profundidade em alguns por cento. Para intuição, a regra basta.

## Profundidade em ppm

As quedas são minúsculas. Por isso a área usa **ppm**, partes por milhão:

| Fração | Porcentagem | ppm |
|---|---|---|
| 0,01 | 1 % | 10 000 ppm |
| 0,001 | 0,1 % | 1 000 ppm |
| 0,0001 | 0,01 % | 100 ppm |

Para converter uma fração em ppm, multiplique por um milhão. Para converter porcentagem em ppm, multiplique por 10 000.

Com a regra e os raios da aula B1, sai a tabela que aparece no guia do projeto:

| Planeta na frente de uma estrela igual ao Sol | $R_p/R_\star$ | Profundidade |
|---|---|---|
| Terra | 0,0092 | cerca de 84 ppm (0,0084 %) |
| Netuno | 0,035 | cerca de 1 250 ppm (0,13 %) |
| Júpiter | 0,100 | cerca de 10 000 ppm (1 %) |

Uma Terra na frente do Sol apaga 84 milésimos de milésimo da luz. É como perceber que uma lâmpada de 100 watts virou uma de 99,99 watts.

Você também pode usar a regra ao contrário. Se você mediu a profundidade e conhece o raio da estrela:

$$ R_p \approx R_\star \sqrt{\delta} $$

É assim que o PlanetHunter estima o raio do planeta de cada sinal.

## Período, duração e profundidade

Um trânsito tem três números principais. Cada um conta uma coisa diferente.

| Número | Símbolo | Unidade no projeto | O que diz |
|---|---|---|---|
| Período | $P$ | dias | quanto tempo o planeta leva para dar uma volta; daí, pela terceira lei de Kepler, a distância até a estrela |
| Duração | $T_{14}$ | horas | quanto tempo o planeta leva para atravessar o disco; depende do tamanho da estrela e da velocidade do planeta |
| Profundidade | $\delta$ | ppm | o tamanho do planeta comparado ao da estrela |

O **período** é o intervalo entre dois trânsitos seguidos. Com o período e um instante de trânsito (chamado $T_0$), dá para prever todos os trânsitos futuros. Esse par de números se chama **efeméride**.

O período também dá a distância. A **terceira lei de Kepler** diz que órbitas maiores levam mais tempo. Para uma estrela com a massa do Sol, medindo o período em anos e a distância $a$ em UA:

$$ a^3 = P^2 $$

A Terra: $P = 1$ ano, $a = 1$ UA. Um planeta de 10 dias ($P = 0{,}0274$ ano) fica a cerca de 0,09 UA, quatro vezes mais perto que Mercúrio.

A **duração** depende de quanto caminho o planeta percorre na frente do disco e da velocidade dele. Para um trânsito que passa pelo centro do disco, numa órbita circular, uma boa aproximação é:

$$ T_{14} \approx \frac{P}{\pi}\,\frac{R_\star}{a} $$

Para a Terra: $P = 8\,766$ horas, $R_\star / a = 696\,000 / 149\,600\,000 = 0{,}00465$. Então $T_{14} \approx 8\,766 / 3{,}14 \times 0{,}00465 \approx 13$ horas. Um observador distante veria a Terra levar cerca de 13 horas para cruzar o Sol, uma vez por ano.

Se o planeta passar perto da borda do disco, e não pelo centro, o trânsito fica mais curto e mais pontudo. Isso é medido pelo **parâmetro de impacto** $b$ (0 = centro, 1 = borda), e você vai brincar com ele no simulador.

## Por que só uma fração dos planetas transita

Para haver trânsito, a órbita precisa estar quase de perfil para nós. Se ela estiver inclinada, o planeta passa "acima" ou "abaixo" da estrela, e nada acontece com o brilho.

Pense numa lâmpada no centro de uma sala e numa formiga andando num círculo ao redor dela. Só quem olha da altura certa vê a formiga passar na frente da lâmpada. Quanto maior o círculo, mais estreita fica essa faixa de altura.

A probabilidade de uma órbita, com orientação ao acaso, produzir trânsitos é aproximadamente:

$$ p_{\text{trânsito}} \approx \frac{R_\star}{a} $$

Para a Terra e o Sol: $p \approx 696\,000 / 149\,600\,000 \approx 0{,}0047$, ou seja, cerca de **0,5 %**. De cada 200 sistemas com uma Terra gêmea a 1 UA de um Sol, só um estaria alinhado para mostrar trânsitos.

Para um planeta de 10 dias ao redor de uma estrela como o Sol ($a \approx 0{,}09$ UA), a chance sobe para cerca de 5 %. Para um Júpiter quente de 3 dias ($a \approx 0{,}04$ UA), mais de 10 %. Por isso as buscas por trânsito acham principalmente planetas de período curto: eles transitam com mais frequência **e** com mais probabilidade.

!!! warning "Armadilha comum"
    "Não vi trânsito, então a estrela não tem planeta" está errado. A ausência de trânsito quase sempre quer dizer só que a órbita não está alinhada conosco. A grande maioria dos planetas da galáxia nunca vai transitar para nós.

## A curva de luz

Uma **curva de luz** é o gráfico do brilho de uma estrela ao longo do tempo. É o dado bruto de tudo neste curso. No eixo horizontal vai o tempo (no TESS, em dias **BTJD**, explicados na aula B3). No eixo vertical vai o brilho, dividido pelo brilho médio, de modo que "normal" vale 1,000.

```
brilho
  1.000 ─────────╮      ╭──────────────────╮      ╭─────────
                 │      │                  │      │
  0.999          ╰──────╯                  ╰──────╯
                 ↑ trânsito                ↑ trânsito
                 |←─────── período ───────→|
                                                       tempo →
```

Um trânsito de planeta tem uma forma característica:

1. **Entrada** (ingresso): o brilho cai enquanto o disco do planeta entra na frente da estrela.
2. **Fundo**: o planeta inteiro está na frente do disco; o brilho fica quase constante, levemente arredondado pelo escurecimento de borda. O formato lembra um **U**.
3. **Saída** (egresso): o brilho volta ao normal.

Na prática, os pontos da curva não ficam numa linha limpa. Cada medida tem **ruído**: pequenas flutuações aleatórias. Um trânsito de 84 ppm numa estrela cujo ruído por medida é de 700 ppm fica invisível a olho. A saída é **juntar muitos trânsitos**: o pipeline sobrepõe todos eles alinhados pelo período (isso se chama **dobrar** a curva) e o ruído aleatório se cancela parcialmente, enquanto o trânsito, que está sempre no mesmo lugar, se soma.

Quanto o trânsito se destaca do ruído é medido pela **razão sinal-ruído**, o **SNR**. Você vai estudá-lo a fundo no nível médio. Por enquanto, guarde: mais trânsitos, estrela mais brilhante e planeta maior aumentam o SNR.

!!! tip "Na ferramenta"
    Os três números do trânsito são colunas da lista de candidatos (`uv run planethunter candidates`): `period_d` (período em dias), `t14_h` (duração em horas) e `depth_ppm` (profundidade em ppm). A coluna `rp_rearth` é o raio estimado com $R_p = R_\star\sqrt{\delta}$. No dossiê, o gráfico **Folded transit** (trânsito dobrado) mostra todos os trânsitos sobrepostos: um "U" claro é bom sinal. O PlanetHunter exige pelo menos **2 trânsitos** (teste `n_transits`) e SNR de pelo menos **7,1** (teste `snr`) para levar um sinal adiante. Esses limites ficam em `config/thresholds.yaml`.

!!! question "Experimente no simulador"
    Abra o [simulador de trânsito](../lab/transit-simulator.md) e **experimente mudar o raio do planeta**. Dobre o raio e confira que a profundidade quadruplica. Depois troque o Sol por uma anã vermelha de 0,2 R☉ mantendo a Terra. Por fim, leve o parâmetro de impacto para perto de 1 e veja o trânsito virar um "V".

!!! example "Exercício 1 (do plano de estudos)"
    Raios: Sol 696 000 km, Terra 6 371 km, Netuno 24 622 km, Júpiter 69 911 km.

    a) Calcule a profundidade de trânsito da Terra, de Netuno e de Júpiter na frente do Sol, em ppm.

    b) Repita para uma anã vermelha com raio 0,2 R☉.

    c) Por que é mais fácil achar planetas pequenos em estrelas pequenas?

    ??? success "Ver resposta"
        **a) Sol ($R_\star$ = 696 000 km).** Use $\delta = (R_p/R_\star)^2$ e multiplique por $10^6$.

        - Terra: $6\,371 / 696\,000 = 0{,}009154$. Ao quadrado: $0{,}0000838$. Em ppm: **cerca de 84 ppm**.
        - Netuno: $24\,622 / 696\,000 = 0{,}03538$. Ao quadrado: $0{,}001251$. Em ppm: **cerca de 1 250 ppm** (o guia arredonda para 1 300; 0,13 %).
        - Júpiter: $69\,911 / 696\,000 = 0{,}1004$. Ao quadrado: $0{,}01009$. Em ppm: **cerca de 10 100 ppm**, ou 1 %.

        **b) Anã vermelha ($R_\star = 0{,}2 \times 696\,000 = 139\,200$ km).**

        - Terra: $6\,371 / 139\,200 = 0{,}04577$. Ao quadrado: $0{,}002095$. **Cerca de 2 100 ppm** (0,2 %).
        - Netuno: $24\,622 / 139\,200 = 0{,}1769$. Ao quadrado: $0{,}03129$. **Cerca de 31 000 ppm** (3,1 %).
        - Júpiter: $69\,911 / 139\,200 = 0{,}5022$. Ao quadrado: $0{,}2522$. **Cerca de 252 000 ppm** (25 %).

        Atalho: a estrela tem 1/5 do raio do Sol, então todas as profundidades ficam $5^2 = 25$ vezes maiores.

        **c)** A profundidade cresce com o inverso do quadrado do raio da estrela. A mesma Terra que mal se nota no Sol (84 ppm, abaixo do ruído de uma única medida do TESS para a maioria das estrelas) produz 2 100 ppm numa anã de 0,2 R☉, uma queda facilmente detectável. Repare também no Júpiter: 25 % de queda é tão fundo que pareceria um eclipse entre duas estrelas. Profundidade muito grande é motivo para desconfiar, como você verá na aula B4.

!!! example "Exercício 2"
    a) Qual a probabilidade de uma Terra a 1 UA de uma estrela igual ao Sol transitar para nós?

    b) Se você observasse 10 000 estrelas iguais ao Sol, cada uma com uma Terra gêmea, quantas mostrariam trânsitos?

    c) E se cada uma tivesse um planeta de 3 dias (a ≈ 0,04 UA)?

    ??? success "Ver resposta"
        a) $p \approx R_\star / a = 696\,000 \text{ km} / 149\,600\,000 \text{ km} \approx 0{,}0047$, ou seja, cerca de **0,5 %**.

        b) $10\,000 \times 0{,}0047 \approx$ **47 estrelas**. As outras 9 953 têm o planeta, mas a órbita não está alinhada conosco.

        c) $a = 0{,}04 \times 149\,600\,000 \approx 5\,984\,000$ km. $p \approx 696\,000 / 5\,984\,000 \approx 0{,}116$, cerca de **12 %**: perto de **1 160 estrelas**. Órbitas pequenas transitam com probabilidade muito maior.

!!! example "Exercício 3"
    O planeta Pi Men c, que você vai ver no PlanetHunter na aula B5, tem período de 6,27 dias e profundidade de cerca de 300 ppm. A estrela Pi Mensae tem raio de cerca de 1,1 R☉.

    a) Estime o raio do planeta em R⊕.

    b) Quantos trânsitos cabem num setor do TESS, que dura cerca de 27 dias?

    ??? success "Ver resposta"
        a) $\delta = 300 \text{ ppm} = 0{,}0003$. $\sqrt{0{,}0003} \approx 0{,}0173$. Esse é $R_p/R_\star$. Então $R_p \approx 0{,}0173 \times 1{,}1 \text{ R☉} \approx 0{,}019$ R☉. Convertendo com 1 R☉ ≈ 109 R⊕: $0{,}019 \times 109 \approx$ **2,1 R⊕**. Uma super-Terra ou mini-Netuno, com cerca do dobro do raio da Terra.

        b) $27 / 6{,}27 \approx 4{,}3$. Cabem **4 trânsitos**, às vezes 5 dependendo de onde caiu o primeiro. Na prática pode ser menos: o TESS tem uma pausa de cerca de um dia no meio de cada setor para enviar dados à Terra (aula B3), e um trânsito pode cair nela.

## Checklist da aula

- [ ] Sei explicar por que a luz cai num trânsito (o disco do planeta bloqueia parte do disco da estrela).
- [ ] Sei usar $\delta \approx (R_p/R_\star)^2$ nos dois sentidos: do raio para a profundidade e da profundidade para o raio.
- [ ] Sei converter entre fração, porcentagem e ppm.
- [ ] Sei o que cada um dos três números (período, duração, profundidade) diz sobre o sistema.
- [ ] Sei o que é efeméride ($P$ e $T_0$).
- [ ] Sei calcular a probabilidade de trânsito $R_\star/a$ e por que ela favorece órbitas curtas.
- [ ] Sei descrever as partes de um trânsito numa curva de luz (entrada, fundo em U, saída).
- [ ] Brinquei com o simulador mudando o raio do planeta, o raio da estrela e o parâmetro de impacto.
- [ ] Fiz os três exercícios sem olhar a resposta.

## Para ir além

- Winn (2010), "Transits and Occultations", gratuito no arXiv (arXiv:1001.2010). O texto clássico sobre a física dos trânsitos. Neste nível, leia só a introdução e olhe as figuras; volte a ele na aula M2.
- NASA Science, página sobre o método de trânsito (science.nasa.gov/exoplanets). Tem animações curtas que mostram a curva de luz se formando enquanto o planeta passa.
- [Simulador de trânsito](../lab/transit-simulator.md) deste curso. Faça os dois desafios da página.
- Charbonneau et al. (2000), "Detection of planetary transits across a Sun-like star", *The Astrophysical Journal* 529, L45. O primeiro trânsito de exoplaneta observado (HD 209458 b). Veja a figura da curva de luz: é o mesmo "U" desta aula.
