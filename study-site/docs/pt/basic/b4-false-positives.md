# B4. Por que quase todo sinal é falso

<p class="meta">Nível básico · semana 5 · cerca de 4 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - O que é uma binária eclipsante e as três marcas que a denunciam: formato em V, eclipses ímpares e pares diferentes, eclipse secundário.
    - Como uma estrela vizinha no mesmo pixel produz um falso trânsito no alvo.
    - Quais defeitos do telescópio imitam trânsitos: momentum dumps, bordas de órbita, luz espalhada.
    - Como a variabilidade da própria estrela atrapalha.
    - Três histórias reais do setor 69 e quanto o vetting do PlanetHunter consegue derrubar.

## O tamanho do problema

Uma queda de brilho periódica **não** prova que existe um planeta. Na primeira análise real do PlanetHunter, com 2 164 estrelas do setor 69, o funil ficou assim:

| Etapa | Sinais |
|---|---|
| Quedas periódicas encontradas (SDE ≥ 7) | 887 |
| Sem correspondência em nenhum catálogo (classe `NEW`) | 648 |
| Aprovados no vetting básico | 11 |
| Candidatos fortes (P1) depois do vetting aprofundado | **0** |

De 887 sinais, nenhum sobreviveu como candidato forte. Isso não é defeito: é o esperado. O TESS e a comunidade já vasculharam esses dados muitas vezes, e a imensa maioria das quedas que ninguém catalogou é ruído ou imitação. O trabalho real não é achar quedas. É **descartar** tudo que não é planeta.

O nome técnico de um sinal que parece planeta mas não é: **falso positivo**. A bateria de testes que tenta derrubá-los se chama **vetting** (do inglês *to vet*, examinar com cuidado). Vamos às imitações mais comuns.

## Binárias eclipsantes

Uma **binária eclipsante** (EB, do inglês *eclipsing binary*) são duas estrelas orbitando uma à outra, com a órbita alinhada conosco. Uma passa na frente da outra, e o brilho total cai. É o falso positivo mais comum.

Se as duas estrelas têm tamanhos parecidos, o eclipse é fundo, de dezenas de por cento, e ninguém confunde com planeta. O perigo está nos casos em que a queda fica rasa. Isso acontece quando o eclipse é **rasante** (uma estrela só raspa a borda da outra) ou quando a estrela que passa na frente é muito pequena. Três marcas denunciam a binária.

### Marca 1: formato em V

No trânsito de um planeta, o disco pequeno entra inteiro na frente da estrela, e o fundo fica quase plano: formato de **U**. Num eclipse rasante entre estrelas, a parte coberta cresce até um máximo e já começa a diminuir, sem fundo plano: formato de **V**.

```
   planeta (U)                binária rasante (V)
  ───╮       ╭───            ───╮       ╭───
     ╰───────╯                   ╲     ╱
                                  ╲   ╱
                                   ╲ ╱
```

Cuidado: planetas que passam perto da borda da estrela também fazem V. Por isso o formato, sozinho, é uma pista, não uma prova.

### Marca 2: eclipses ímpares e pares diferentes

Numa binária, há dois eclipses por volta: a estrela A na frente de B, e depois B na frente de A. Se as estrelas são diferentes, os dois eclipses têm profundidades diferentes. O algoritmo de busca, procurando quedas iguais, às vezes junta os dois e devolve **metade do período verdadeiro**. Aí os trânsitos "ímpares" (1º, 3º, 5º...) são de um tipo e os "pares" (2º, 4º, 6º...) de outro.

```
brilho
  ───╮   ╭───╮ ╭───╮   ╭───╮ ╭───
     │   │   ╰─╯   │   │   ╰─╯        ímpares fundos, pares rasos
     ╰───╯         ╰───╯              -> é binária com período 2P
      1º    2º      3º    4º
```

Um planeta faz todos os trânsitos com a mesma profundidade.

### Marca 3: eclipse secundário

A estrela companheira também brilha. Quando ela passa **atrás** da principal, a luz dela some por um tempo, e o brilho total cai de novo, em geral menos. Numa órbita circular, isso acontece exatamente na metade do caminho entre dois eclipses principais: na **fase 0,5**.

Um planeta comum quase não emite luz própria visível, então não produz secundário mensurável. Há exceções, e uma delas é uma das histórias deste capítulo.

| Característica | Planeta | Binária eclipsante |
|---|---|---|
| Formato | U (fundo plano) | V, quando rasante |
| Ímpares e pares | mesma profundidade | podem diferir |
| Fase 0,5 | plana (ou queda muito pequena) | eclipse secundário |
| Profundidade | em geral abaixo de 2 % | muitas vezes acima |
| Raio calculado | até ~2 raios de Júpiter | grande demais para planeta |

## Binárias de fundo e contaminação

Lembre da aula B3: cada pixel do TESS cobre 21″, e cabem várias estrelas nele. Imagine o alvo brilhante e, atrás dele, quase na mesma direção, uma binária eclipsante fraca. A binária tem eclipses fundos, mas contribui com só uma fração pequena da luz total do pixel. O eclipse dela aparece **diluído**, raso, parecendo o trânsito de um planeta no alvo.

$$ \delta_{\text{observada}} \approx \delta_{\text{binária}} \times \frac{\text{luz da binária}}{\text{luz total}} $$

Isso se chama **binária de fundo** ou, de forma mais geral, **blend** (mistura). É traiçoeiro porque a curva pode parecer perfeita: formato em U, ímpares iguais aos pares, nenhum secundário visível (ele também está diluído).

Como pegar: se a queda vem de outra estrela, o "centro de luz" da imagem se desloca um pouquinho durante o trânsito, na direção da culpada. É o teste de **centróide**. No vetting aprofundado, o PlanetHunter também subtrai a imagem fora do trânsito da imagem durante o trânsito e vê **onde** a luz sumiu (imagem-diferença).

## Defeitos do telescópio

Algumas quedas não vêm de estrela nenhuma. Vêm do próprio instrumento. São os **sistemáticos**.

- **Momentum dumps.** O TESS se mantém apontado com rodas de reação, que acumulam rotação com o tempo. De tempos em tempos, pequenos propulsores são acionados para descarregar essa rotação. O apontamento treme por um instante e o brilho medido salta. Se esses eventos se repetem em intervalos regulares, parecem trânsitos periódicos.
- **Bordas de órbita.** No começo e no fim de cada órbita de 13,7 dias, o telescópio muda de temperatura e o brilho medido sobe ou desce aos poucos, em rampa. Quando a limpeza dos dados tenta remover essa rampa, pode sobrar uma depressão que lembra um trânsito.
- **Luz espalhada.** Perto do ponto da órbita mais próximo da Terra, luz da Terra e da Lua entra nas câmeras e muda o fundo da imagem.

A marca registrada dos sistemáticos: acontecem em **um setor** e não se repetem nos outros, ou caem exatamente em cima de momentum dumps e bordas.

## Variabilidade da própria estrela

Estrelas não são lâmpadas perfeitas.

- **Manchas e rotação.** Estrelas giram e têm manchas escuras, como o Sol. Quando a mancha passa pelo lado visível, o brilho cai; quando sai, sobe. Isso cria ondas de dias.
- **Pulsações.** Algumas estrelas incham e encolhem ritmicamente, em minutos ou horas.
- **Flares.** Explosões na superfície geram picos de brilho **para cima**, rápidos.

O PlanetHunter remove a variação lenta com um filtro (o **detrending**) e corta só os picos para cima. Nunca corta pontos para baixo, senão apagaria os próprios trânsitos. Quando a estrela varia rápido demais, o filtro deixa sobras que podem parecer quedas.

## Três histórias reais do setor 69

Estes casos aconteceram no primeiro dia de testes do PlanetHunter. Cada um mostra por que uma etapa existe.

### 1. O planeta inventado: HD 23472

A estrela HD 23472 tem **5 planetas conhecidos**. Num só setor, o sistema viu um trânsito do planeta b e um trânsito do planeta c. Com só essas duas quedas, ele concluiu que havia um planeta de **10,29 dias**, que não existe. O crossmatch por período não pegou, porque 10,29 dias não é o período de nenhum dos dois.

Não foi caso isolado: o mesmo aconteceu com TOI-703 e GJ 143, e os três chegavam a P1, a categoria de alerta imediato. **O que resolveu:** o casamento **trânsito a trânsito**. Agora o crossmatch verifica cada queda observada: se pelo menos metade delas coincide com trânsitos previstos de objetos conhecidos, e uma coincidência tão boa dificilmente aconteceria por acaso (menos de 1 %), o sinal é marcado como conhecido. A verificação de acaso veio depois: sem ela, a regra também "explicava" quedas aleatórias, porque com janelas de tempo folgadas uma coincidência é fácil.

### 2. O planeta que parecia binária: WASP-18 b

WASP-18 b é um planeta gigante, muito massivo e tão quente que brilha. O TESS vê a luz dele sumir quando ele passa **atrás** da estrela: uma queda de cerca de **340 ppm** na fase 0,5. Esse fenômeno se chama **ocultação**. O teste de eclipse secundário via a queda e vetava o planeta como binária.

**O que resolveu:** o veto do secundário passou a exigir que a queda secundária seja de **pelo menos 10 % da principal**. Planetas produzem ocultações pequenas; estrelas companheiras, grandes. No mesmo dia apareceu outro problema parecido: o catálogo de binárias eclipsantes do TESS contém alguns Júpiteres quentes conhecidos (WASP-18 b, WASP-100 b, HATS-16 b). A correção foi dar prioridade ao catálogo de planetas confirmados sobre o de binárias.

### 3. O melhor candidato que não era: HD 271883

HD 271883 mostrou um sinal limpo de **6,61 dias** e **4 900 ppm**. Passou em todos os testes básicos, o centróide estava no alvo, não havia binária conhecida. Parecia o candidato perfeito.

Mas a estrela foi observada em **10 setores**. Se o sinal fosse um planeta, deveria aparecer forte nos outros: o SNR esperado nos setores 67, 68 e 97 era de 45 a 64. Não apareceu com essa força. Era um defeito de um setor só. **O que resolveu:** o teste de **outros setores** (`other_sectors`), que procura o sinal, inclusive às cegas, nos outros setores da mesma estrela.

!!! warning "A lição geral"
    Um alerta precisa sobreviver a tentativas sérias de derrubá-lo. Desconfie de sinais bonitos demais: as três histórias são de sinais que pareciam ótimos.

## Quanto o vetting básico consegue

O projeto mediu o vetting básico (sem internet) em objetos de resposta conhecida do setor 69:

| Grupo | Sinais | Aprovados | Reprovados |
|---|---|---|---|
| Planetas confirmados (`KNOWN_PLANET`) | 54 | 44 (81 %) | 10 (19 %) |
| Falsos positivos conhecidos (`KNOWN_FP`) | 18 | 8 (44 %) | **10 (56 %)** |

Leia a segunda linha com atenção: o vetting básico reprova **56 % dos falsos positivos conhecidos**, sem nenhuma consulta à internet, e mantém a maioria dos planetas reais. Mas 8 falsos positivos ainda passam. Segundo os comentários do TFOPWG, quatro deles só mostram o eclipse secundário quando se somam vários setores, um é binária com órbita excêntrica (secundário fora da fase 0,5), dois têm formato em V só marginal e um é binária de fundo. Por isso existe o vetting aprofundado, que olha os pixels, as estrelas vizinhas e os outros setores.

Há sempre uma troca. O limite do teste de formato em V foi escolhido medindo: com o valor atual, ele marca 8 dos 18 falsos positivos, mas também marca 3 de 50 planetas reais (planetas rasantes, como HIP 65 A b, LTT 9779 b e TOI-2382 b). Mesmo assim, desde 2026-10-10 um formato em V reprova o sinal sozinho (uma **falha grave**), sem zerar o score. O projeto mediu o preço e o aceitou: alguns Júpiteres quentes rasantes se perdem a cada setor, e várias binárias deixam de passar. Você vai ver como as falhas se somam na aula [M5](../intermediate/m5-vetting-in-practice.md).

!!! tip "Na ferramenta"
    Cada imitação desta aula tem um teste no vetting (`uv run planethunter vet <run_id>`):

    | Imitação | Testes |
    |---|---|
    | Binária eclipsante | `odd_even` (ímpar/par), `secondary` (fase 0,5), `secondary_scan` (outras fases), `shape` (V ou U), `kdr25_grazing` (só raspa a borda da estrela), `radius` (grande demais) |
    | Binária de fundo, contaminação | `centroid`, `duration`; no aprofundado, `tpf_difference_image` e `gaia_neighbors` |
    | Defeitos do telescópio | `edges_dumps`, `consistency`; no aprofundado, `other_sectors` |
    | Variabilidade da estrela | o detrending, na etapa de limpeza, e o teste `consistency` |

    No dossiê, o gráfico **Odd, even and secondary** (ímpar, par e secundário) mostra três painéis lado a lado: trânsitos ímpares, pares e a fase 0,5. Na curva de luz, linhas azuis pontilhadas marcam os momentum dumps. Os limites de cada teste estão em `config/thresholds.yaml`, com um comentário explicando o porquê de cada valor.

!!! example "Exercício 1"
    O alvo de um pixel é uma estrela brilhante. Atrás dela há uma binária eclipsante fraca que contribui com **1 %** da luz total do pixel. A binária tem eclipses que apagam **50 %** da luz dela. Qual profundidade o TESS mede? Que tamanho de planeta isso imitaria numa estrela igual ao Sol?

    ??? success "Ver resposta"
        Profundidade observada: $0{,}50 \times 0{,}01 = 0{,}005$, ou seja, **5 000 ppm** (0,5 %).

        Planeta equivalente: $R_p/R_\star = \sqrt{0{,}005} \approx 0{,}071$. Numa estrela de 1 R☉ (109 R⊕), $R_p \approx 0{,}071 \times 109 \approx 7{,}7$ R⊕, um planeta do tamanho de Netuno a Saturno. Totalmente plausível. Só testes que olham **onde** a luz sumiu (centróide, imagem-diferença) ou que conhecem as estrelas vizinhas (Gaia) desmascaram esse caso.

!!! example "Exercício 2"
    Suponha um trânsito principal de 10 000 ppm. Na fase 0,5, aparece uma queda de 340 ppm. Pela regra do PlanetHunter, esse secundário veta o sinal? E se a queda na fase 0,5 fosse de 2 500 ppm?

    ??? success "Ver resposta"
        A regra: veta só se o secundário for de pelo menos 10 % do principal. 10 % de 10 000 ppm é 1 000 ppm.

        - 340 ppm é 3,4 % do principal. **Não veta.** É compatível com a ocultação de um planeta quente, como WASP-18 b.
        - 2 500 ppm é 25 % do principal. **Veta.** Um secundário desse tamanho indica uma companheira que emite muita luz: uma estrela, não um planeta.

        Repare que a regra não diz "qualquer secundário é binária". Ela foi ajustada depois que um planeta real foi reprovado.

!!! example "Exercício 3"
    Para cada descrição, diga qual é o suspeito mais provável e qual teste o pegaria.

    1. Os trânsitos 1, 3 e 5 têm 8 000 ppm; os trânsitos 2, 4 e 6 têm 3 000 ppm.
    2. Todas as quedas caem a poucos minutos de uma linha azul pontilhada no dossiê.
    3. Um sinal lindo num setor; a estrela tem mais 9 setores e o sinal não aparece em nenhum.
    4. Durante o trânsito, o centro de luz da imagem se desloca na direção de uma estrela vizinha.

    ??? success "Ver resposta"
        1. **Binária eclipsante** com período verdadeiro igual ao dobro do encontrado. Teste `odd_even`.
        2. **Defeito do telescópio** (momentum dumps). Teste `edges_dumps`.
        3. **Sistemático de um setor**, como HD 271883. Teste `other_sectors`.
        4. **Contaminação por estrela vizinha** (provável binária de fundo). Testes `centroid` e `tpf_difference_image`.

## Checklist da aula

- [ ] Sei o que é uma binária eclipsante e as três marcas (V, ímpar/par, secundário).
- [ ] Sei explicar por que o formato em V é pista e não prova (planetas rasantes).
- [ ] Sei calcular a diluição de uma binária de fundo.
- [ ] Sei citar três defeitos do telescópio e a marca deles (um setor só, em cima de dumps ou bordas).
- [ ] Sei como manchas, pulsações e flares atrapalham, e por que o detrending nunca corta para baixo.
- [ ] Sei contar as três histórias (HD 23472, WASP-18 b, HD 271883) e o teste que resolveu cada uma.
- [ ] Sei que o vetting básico reprova 56 % dos falsos positivos conhecidos do setor 69 e mantém 81 % dos planetas.
- [ ] Fiz os três exercícios sem olhar a resposta.

## Para ir além

- Prša et al. (2022), "TESS Eclipsing Binary Stars. I. Short-cadence Observations of 4584 Eclipsing Binaries in Sectors 1–26", *The Astrophysical Journal Supplement Series* 258, 16. O catálogo de binárias que o PlanetHunter espelha. Folheie as figuras de curvas de luz para ver eclipses de verdade.
- Winn (2010), "Transits and Occultations", arXiv:1001.2010. A seção sobre ocultações explica por que planetas quentes como WASP-18 b mostram queda na fase 0,5.
- Guerrero et al. (2021), *The Astrophysical Journal Supplement Series* 254, 39. Mostra como a equipe do TESS separa planetas de falsos positivos; compare com a tabela "Na ferramenta" desta aula.
- O arquivo `docs/benchmarks/2026-10-09-s0069-vetting.md` do repositório. A tabela "What was measured and fixed" (o que foi medido e corrigido) conta, com números, cada ajuste do vetting. Você vai estudá-la a fundo na aula M5.
