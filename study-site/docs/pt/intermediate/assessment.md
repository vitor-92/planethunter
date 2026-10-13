# Autoavaliação do nível médio

<p class="meta">Nível médio · semana 10 · cerca de 3 horas</p>

!!! abstract "Como fazer"
    - Responda por escrito, sem consultar as aulas. Uma calculadora é permitida.
    - Só depois abra cada resposta e compare. Não basta acertar a conclusão: o raciocínio precisa estar lá.
    - As perguntas 1 a 6 são as do plano de estudos e decidem a aprovação. As perguntas 7 a 10 são treino extra.

## Critério de aprovação

**Responda bem pelo menos 5 das 6 primeiras perguntas** e siga para o [nível avançado](../advanced/index.md).

"Responder bem" quer dizer: a resposta cita o mecanismo certo e, quando há conta, a conta chega à ordem de grandeza certa. Se errar duas ou mais, volte às aulas indicadas em cada resposta e refaça os exercícios delas antes de tentar de novo.

## Perguntas do plano

!!! question "1. Por que o sistema exige SNR ≥ 7,1 e não ≥ 3?"

    ??? success "Ver resposta"
        Por causa do **efeito de olhar em todo lugar**. Com ruído gaussiano, um valor de 3 sigma aparece por acaso 1 vez em cerca de 740. Parece raro, mas a busca testa milhares de períodos e, para cada um, milhares de posições e durações, em cerca de 20 000 estrelas por setor. São milhões de tentativas: com um limite de 3 sigma, o ruído puro produziria milhares de "sinais" por setor.

        Em 7,1 sigma, a chance por tentativa cai para cerca de $6 \times 10^{-13}$. O valor vem da missão Kepler (Jenkins, Caldwell & Borucki, 2002), escolhido para que uma busca do tamanho da do Kepler, sobre ruído branco gaussiano, desse menos de um falso alarme no total.

        Ponto extra: ruído real não é gaussiano. O projeto mediu que buscas numa faixa estreita de períodos, em estrelas sem sinal, passam de SNR 19 em 10 % das tentativas. Por isso 7,1 é **necessário, mas não suficiente**: o vetting e o teste de outros setores fazem o resto.

        Revise: [M1](m1-statistics-for-signals.md), seções "A distribuição normal e o sigma" e "SNR e a raiz de N".

!!! question "2. Um trânsito dura 6 horas numa anã vermelha com período de 3 dias. Por que isso é suspeito?"

    ??? success "Ver resposta"
        Porque a duração prevista é muito menor. Tome uma anã vermelha típica, com 0,3 R☉ e 0,3 M☉. A densidade é $0{,}3/0{,}3^3 \approx 11$ vezes a do Sol.

        $a/R_\star = 215 \times (3/365{,}25)^{2/3} \times 11^{1/3} \approx 215 \times 0{,}0407 \times 2{,}23 \approx 19{,}5$.

        $T_{14}(b=0) \approx (P/\pi)(R_\star/a) = (3/\pi)/19{,}5 \approx 0{,}049$ d $\approx$ **1,2 hora**.

        Seis horas é cinco vezes isso. O trânsito central é o mais longo possível numa órbita circular, então a razão 5 passa muito do limite de 1,67 do teste `duration`. Explicações possíveis:

        - o sinal vem de **outra estrela**, maior, no mesmo pixel (blend);
        - a estrela não é uma anã vermelha (raio errado no TIC);
        - o período está errado (a duração cresce com $P^{1/3}$; para 6 h nessa estrela, o período teria de ser centenas de dias);
        - órbita muito excêntrica, o que raramente explica um fator 5.

        Revise: [M2](m2-transit-physics.md), seção "A duração do trânsito".

!!! question "3. O que muda no periodograma se a curva tiver uma lacuna grande no meio?"

    ??? success "Ver resposta"
        Várias coisas, todas para pior:

        - **Menos trânsitos.** Os que caem na lacuna não existem nos dados. O SNR cai (menos pontos) e, com período longo, pode sobrar um só trânsito, vetado por `n_transits`.
        - **Aliases mais fortes.** Os trânsitos "extras" previstos por P/2 ou P/3 podem cair na lacuna, e nada nos dados os desmente. O pico do alias fica tão alto quanto o verdadeiro, ou mais. Foi o que aconteceu com TOI 899.01, 924.01 e 3262.01 no setor 69, achados com cerca de 4,2 d em vez de 12 a 13 d. O `refine_alias` testa 2P e 3P exatamente por isso.
        - **Bordas novas.** Cada lado da lacuna é uma borda de segmento. O detrending cria rampas ali que podem imitar trânsitos (o projeto mediu SDE ~10 em ruído puro com evento a 0,07 d da borda). Sinais com mais de 50 % dos trânsitos em bordas são barrados (`edge_transit_fraction`).
        - **Estrutura no periodograma.** Períodos que colocam todos os trânsitos na lacuna não podem ser testados; o periodograma fica com mais picos espúrios ligados ao espaçamento dos segmentos.

        Revise: [M3](m3-periodograms.md), seções "Aliases" e "Lacunas e bordas de segmento".

!!! question "4. Por que o teste de centróide usa a distância implícita da fonte e não só a significância do deslocamento?"

    ??? success "Ver resposta"
        Porque **significância** responde "o deslocamento existe?", e não "a fonte está longe?". Em estrelas brilhantes, com muitos trânsitos, o erro do centróide fica minúsculo, e até um deslocamento irrelevante, causado pelo próprio alvo, vira mais de 3 sigma.

        A **distância implícita** responde à pergunta certa. Se uma fonte a distância $D$ do centróide escurece com profundidade relativa $\delta$, o centróide se move cerca de $\delta \times D$. Logo, $D \approx$ deslocamento / profundidade. Se $D$ for menor que 1 pixel (21″), a fonte é compatível com o alvo.

        A evidência medida: com o critério só de significância, **11 de 41 planetas confirmados** do setor 69 reprovavam, todos com fonte implícita a no máximo 0,88 pixel. A regra atual exige as duas coisas: mais de 3 sigma **e** fonte a mais de 1 pixel. Um falso positivo como TOI-854.01 (12σ, fonte a 2,0 pixels) continua reprovando. Dois refinamentos tornam o próprio sigma honesto: o erro de uma época é medido em 200 épocas falsas fora dos trânsitos, e a profundidade é corrigida para a profundidade dentro da abertura (CROWDSAP × δ).

        Revise: [M5](m5-vetting-in-practice.md), seção `centroid`.

!!! question "5. Explique, com um desenho, por que uma binária com período 2P aparece com profundidades diferentes em trânsitos ímpares e pares."

    ??? success "Ver resposta"
        Uma binária eclipsante tem **dois** eclipses por órbita: o primário (a estrela mais brilhante é tapada) e o secundário (a menos brilhante é tapada). Se as estrelas forem parecidas, os dois eclipses têm profundidades parecidas, e a busca acha o intervalo entre eclipses consecutivos, P. O período orbital verdadeiro é **2P**.

        ```
        brilho
        ────╮    ╭────╮  ╭────╮    ╭────╮  ╭────
            │    │    ╰──╯    │    │    ╰──╯
            ╰────╯            ╰────╯
              1        2        3        4
            ímpar     par     ímpar     par
            fundo     raso    fundo     raso
              |<- P -->|<- P -->|
              |<----- 2P ------>|
        ```

        Com o período P, numeramos os eventos 1, 2, 3, 4... Os ímpares (1, 3, 5) são sempre primários; os pares (2, 4, 6), sempre secundários. Se as estrelas tiverem tamanho ou temperatura diferentes, os primários são mais fundos que os secundários, e a média dos ímpares difere da média dos pares.

        O teste `odd_even` mede essa diferença em sigmas (com o erro em blocos): falha a partir de 3σ e veta a partir de 5σ. Exemplo real: TOI-343.01, ímpar 2 294 ppm, par 4 583 ppm, 5,8σ, vetado.

        Revise: [M3](m3-periodograms.md), aviso "Binária com período 2P", e [M5](m5-vetting-in-practice.md).

!!! question "6. Abra um dossiê aprovado e diga qual seria o próximo teste que você faria antes de submeter."

    ??? success "Ver resposta"
        Não há resposta única, mas uma boa resposta segue esta lógica:

        1. **Ver o que está pendente.** A tabela de vetting lista os testes aprofundados que ainda não rodaram (`tpf_difference_image`, `gaia_neighbors`, `fpp_triceratops`). Um aprovado no básico ainda não passou por eles.
        2. **O teste mais poderoso costuma ser outros setores.** Se a estrela foi observada em outros setores, o sinal tem de reaparecer com a força esperada. Foi esse teste que derrubou HD 271883 (sinal 1798, 6,61 d): esperado SNR 45 a 64 nos setores 67, 68 e 97, e o sinal não apareceu. Rode `uv run planethunter vet-deep <run_id>`.
        3. **Depois, imagem-diferença no TPF e vizinhos Gaia**, para confirmar que a fonte é o alvo.
        4. **Depois, FPP com triceratops**, só se tudo acima passar.
        5. **E sempre:** página da estrela no ExoFOP e busca no ADS pelo TIC, para ver se alguém já publicou.

        Uma resposta forte cita o dossiê concreto: "esta estrela tem host conhecido e 3 outros setores; o próximo passo é `vet-deep` para o teste de outros setores, porque um sinal novo e profundo num setor só é a assinatura clássica de sistemático".

        Revise: [M5](m5-vetting-in-practice.md), "Roteiro de revisão de candidatos", e o passo 6 do guia para leigos.

## Perguntas extras

!!! question "7. Uma mudança no código levou o recall de 120/135 para 123/135. Isso prova que a mudança melhorou o sistema?"

    ??? success "Ver resposta"
        Não sozinha. O intervalo de confiança de 95 % (Wilson) para 123/135 vai de 85,1 % a 94,8 %; para 120/135 (88,9 %), a aproximação simples dá de 83,6 % a 94,2 %. Os intervalos se sobrepõem quase inteiros: três TOIs a mais são compatíveis com acaso.

        O que torna a mudança convincente é o **diagnóstico**: saber quais TOIs passaram a ser achados e por quê. No histórico do benchmark, a mudança do run final (`refine_alias`) recuperou exatamente TOI 899.01, 924.01 e 3262.01, que antes saíam com P/3. Causa identificada mais efeito no lugar previsto: isso convence.

        Revise: [M1](m1-statistics-for-signals.md), "Intervalo de confiança binomial".

!!! question "8. O que aconteceria se a janela de detrending fosse de 0,2 dia?"

    ??? success "Ver resposta"
        O filtro passaria a seguir o próprio trânsito e "comê-lo". A regra prática é janela de cerca de 3 vezes a duração do trânsito: 0,2 d (4,8 h) só preserva bem trânsitos de até ~1,6 h.

        Os números medidos mostram o tamanho do estrago com janelas maiores que essa: com 0,5 d, um trânsito de 5 h perde 40 % da profundidade; com 0,3 d, o TOI 190.01 (5,7 h) caiu de 8 248 ppm para 347 ppm. Com 0,2 d, trânsitos de 3 h ou mais seriam fortemente reduzidos, o SNR cairia e muitos planetas de período acima de alguns dias sumiriam.

        Em troca, estrelas muito variáveis ficariam mais limpas. Por isso o PlanetHunter só usa janelas curtas (0,5 e 0,3 d) numa **segunda variante**, quando a razão de ruído passa de 1,2, e busca nas duas versões.

        Revise: [M3](m3-periodograms.md), "Detrending: a janela que decide".

!!! question "9. Um planeta de período 10 dias transita uma estrela igual ao Sol, e o trânsito medido dura 3,0 horas. O teste duration passa? Qual o parâmetro de impacto aproximado?"

    ??? success "Ver resposta"
        Previsto com $b = 0$: $a/R_\star \approx 19{,}5$ e $T_{14} \approx (10/\pi)/19{,}5 \approx 0{,}163$ d $\approx$ 3,9 h.

        Razão: 3,0/3,9 ≈ 0,77. Está entre 0,15 e 1,67: **passa**.

        Com $T_{14}/T_{14}(b=0) \approx \sqrt{1-b^2}$: $1 - b^2 = 0{,}77^2 \approx 0{,}59$, então $b \approx 0{,}64$. Um trânsito fora do centro, perfeitamente normal.

        Revise: [M2](m2-transit-physics.md), exercícios 1 e 3.

!!! question "10. Um sinal NEW falha em secondary (4σ, 6 % do primário) e em edges_dumps; o centróide ficou sem dados. Calcule o score, o veredito e a severidade."

    ??? success "Ver resposta"
        `secondary` a 4σ é falha (≥ 3σ), sem veto (não chega a 5σ e está abaixo de 10 %): peso 0,4. Também não é caso de período dobrado, porque 6 % está longe da profundidade do primário. `edges_dumps` falhou: peso 0,4. `centroid` sem dados: 0,95, mas "sem dados" não é falha.

        Score = 0,4 × 0,4 × 0,95 ≈ **0,15**. Veredito: **FAIL**, porque há duas falhas leves e só uma é tolerada. Não vira candidato, logo não tem severidade. (Se o modelo calibrado lhe desse um `p_rank` acima do limiar de P2, ele poderia ser resgatado, mas só até P2.)

        Note que nenhum teste vetou, mas duas falhas leves bastaram. Pelo raciocínio físico também faz sentido: uma queda em fase 0,5 e trânsitos em bordas são, juntos, um perfil pouco convincente.

        Revise: [M5](m5-vetting-in-practice.md), "O veredito e o score".

## Próximo passo

Aprovado? O [nível avançado](../advanced/index.md) leva você aos artigos originais (BLS, TLS, Robovetter, triceratops), ao cálculo da probabilidade de falso positivo, ao benchmark com injeção de trânsitos sintéticos e à preparação de uma submissão de CTOI.

Antes de ir, guarde o caderno de revisões do nível médio. Ele será o material de partida da aula de aprendizado de máquina.
