# Autoavaliação do nível básico

<p class="meta">Nível básico · fim da semana 6 · cerca de 1 hora</p>

!!! abstract "Como fazer"
    - Responda **sem consultar** as aulas. Escreva as respostas no caderno, com suas palavras e com as contas.
    - Só depois abra "Ver resposta" e compare. Conte como certa a resposta que tem a ideia principal, mesmo com outras palavras.
    - As perguntas 1 a 6 são as do plano de estudos e decidem a aprovação. As perguntas 7 a 10 são extras, para você testar se a base está sólida.

!!! warning "Critério de aprovação"
    Acertou **pelo menos 5 das 6 perguntas principais** (1 a 6)? Siga para o [nível médio](../intermediate/index.md).

    Errou duas ou mais? Volte às aulas indicadas em cada resposta, deixe passar alguns dias e refaça a autoavaliação.

## Perguntas principais

!!! example "Pergunta 1"
    Um planeta com metade do raio de Júpiter transita uma estrela igual ao Sol. Qual a profundidade aproximada, em ppm?

    ??? success "Ver resposta"
        Use $\delta \approx (R_p/R_\star)^2$.

        Júpiter tem cerca de 0,1 R☉ (69 911 km / 696 000 km ≈ 0,100). Metade disso é 0,05 R☉. Então:

        $$ \delta \approx (0{,}05)^2 = 0{,}0025 $$

        Multiplicando por um milhão: **cerca de 2 500 ppm** (0,25 %).

        Atalho: Júpiter dá cerca de 10 000 ppm. Metade do raio dá um quarto da profundidade, porque a profundidade depende do **quadrado** da razão dos raios: $10\,000 / 4 = 2\,500$ ppm.

        Se você respondeu 5 000 ppm, esqueceu o quadrado. Revise a [aula B2](b2-transit-method.md).

!!! example "Pergunta 2"
    Por que três trânsitos igualmente espaçados são mais convincentes que um só?

    ??? success "Ver resposta"
        Três motivos:

        1. **Periodicidade.** Uma órbita se repete com regularidade de relógio. Um evento isolado pode ser quase qualquer coisa: um ajuste do telescópio, uma rampa na borda dos dados, um raio cósmico, um salto instrumental. Três quedas iguais, igualmente espaçadas, são muito difíceis de produzir por acaso.
        2. **Período e previsão.** Com um trânsito só, não se sabe o período, e sem período não se prevê o próximo trânsito nem se calcula a distância do planeta à estrela. Com dois ou mais, temos a **efeméride** (período e instante de trânsito), que pode ser testada em outros dados.
        3. **Testes possíveis e sinal mais forte.** Com vários trânsitos dá para comparar ímpares com pares, checar se todos têm a mesma profundidade e somar todos no trânsito dobrado, o que aumenta o SNR.

        Na ferramenta, o teste `n_transits` **veta** sinais com menos de 2 trânsitos. Revise as aulas [B2](b2-transit-method.md) e [B4](b4-false-positives.md).

!!! example "Pergunta 3"
    O que significa Tmag 6 comparado com Tmag 13?

    ??? success "Ver resposta"
        Tmag é o brilho da estrela na escala de magnitudes do TESS. A escala é **invertida**: número menor quer dizer estrela mais brilhante. Então a estrela de Tmag 6 é muito mais brilhante que a de Tmag 13.

        Quanto mais? A escala é multiplicativa: 5 magnitudes valem 100 vezes. A diferença de 7 magnitudes dá $2{,}512^7 \approx 630$. A estrela de Tmag 6 é **cerca de 630 vezes mais brilhante**.

        Por que importa: mais luz significa menos ruído relativo, então trânsitos rasos ficam detectáveis. E estrelas brilhantes facilitam muito a confirmação com outros telescópios. Revise a [aula B3](b3-tess-telescope.md).

!!! example "Pergunta 4"
    Cite duas diferenças entre a curva de uma binária eclipsante e a de um planeta.

    ??? success "Ver resposta"
        Qualquer duas destas:

        - **Formato.** O planeta faz um trânsito com fundo quase plano (U). Uma binária rasante faz um eclipse pontudo (V).
        - **Ímpares e pares.** O planeta faz todos os trânsitos iguais. Uma binária, quando o algoritmo encontra metade do período verdadeiro, mostra trânsitos alternados com profundidades diferentes.
        - **Eclipse secundário.** A binária mostra uma segunda queda na fase 0,5, quando a companheira passa atrás da estrela principal. Um planeta comum não mostra nada ali (planetas muito quentes mostram uma ocultação pequena, menor que 10 % do trânsito).
        - **Profundidade e raio.** Binárias costumam dar quedas muito fundas; o "planeta" calculado sai grande demais, do tamanho de uma estrela.

        No PlanetHunter: testes `shape`, `odd_even`, `secondary` e `radius`. Revise a [aula B4](b4-false-positives.md).

!!! example "Pergunta 5"
    Por que um sinal pode vir de uma estrela que não é o alvo?

    ??? success "Ver resposta"
        Porque cada pixel do TESS cobre **21 segundos de arco** do céu, uma área grande onde cabem várias estrelas, e a luz de cada estrela ainda se espalha por pixels vizinhos. O brilho "do alvo" é, na verdade, a soma da luz de todas as estrelas na região.

        Se uma estrela vizinha, mais fraca, for uma binária eclipsante, os eclipses dela aparecem **diluídos** na luz total e podem imitar o trânsito raso de um planeta no alvo. Exemplo: uma binária que contribui com 1 % da luz e tem eclipses de 50 % produz uma queda de 0,5 %, ou 5 000 ppm.

        Como se investiga: o teste de centróide (o centro de luz se desloca durante o trânsito?), a imagem-diferença (onde a luz sumiu?) e a lista de vizinhos do Gaia. Revise as aulas [B3](b3-tess-telescope.md) e [B4](b4-false-positives.md).

!!! example "Pergunta 6"
    Qual a diferença entre um TOI e um planeta confirmado?

    ??? success "Ver resposta"
        Um **TOI** (*TESS Object of Interest*) é um **candidato**: um sinal nos dados do TESS que a equipe da missão examinou e considerou promissor. Ele ainda pode ser falso positivo. Muitos TOIs acabam marcados pelo TFOPWG como FP (falso positivo) ou FA (falso alarme).

        Um **planeta confirmado** tem evidência independente do trânsito, obtida com outros telescópios, em geral a massa medida por velocidade radial. No TFOPWG, aparece como CP (confirmado) ou KP (já conhecido).

        Entre os dois fica o **planeta validado**: estatisticamente muito improvável de ser falso positivo, com apoio de imagens de alta resolução, mas sem massa medida.

        A escada completa: sinal → candidato → CTOI → TOI → validado → confirmado. Revise a [aula B3](b3-tess-telescope.md).

## Perguntas extras

!!! example "Pergunta 7"
    Qual a probabilidade aproximada de uma Terra a 1 UA de um Sol transitar para nós? O que isso diz sobre estrelas que não mostram trânsito?

    ??? success "Ver resposta"
        $p \approx R_\star / a = 696\,000 / 149\,600\,000 \approx 0{,}0047$, cerca de **0,5 %**: uma em 200.

        Consequência: a ausência de trânsito quase nunca quer dizer ausência de planeta. Na grande maioria dos casos, a órbita só não está alinhada conosco. E as buscas por trânsito favorecem planetas de período curto, que transitam com probabilidade maior. Revise a [aula B2](b2-transit-method.md).

!!! example "Pergunta 8"
    Por que um planeta de 2 R⊕ é muito mais fácil de achar ao redor de uma anã vermelha de 0,3 R☉ do que ao redor de uma estrela de 1 R☉?

    ??? success "Ver resposta"
        Porque a profundidade é $(R_p/R_\star)^2$. Na estrela de 1 R☉ (109 R⊕): $(2/109)^2 \approx 0{,}00034$, cerca de **340 ppm**. Na anã de 0,3 R☉ (cerca de 33 R⊕): $(2/33)^2 \approx 0{,}0037$, cerca de **3 700 ppm**, onze vezes mais.

        O fator é $(1/0{,}3)^2 \approx 11$. Com o mesmo ruído, uma queda 11 vezes maior tem SNR 11 vezes maior. Além disso, planetas na zona habitável de anãs vermelhas têm períodos curtos, então transitam mais vezes por setor. Revise a [aula B2](b2-transit-method.md) e brinque com o [simulador](../lab/transit-simulator.md).

!!! example "Pergunta 9"
    Um sinal limpo, que passou em todos os testes básicos, aparece num único setor de uma estrela observada em 10 setores. Nos outros 9 ele não aparece. O que você conclui, e qual caso real do setor 69 é parecido?

    ??? success "Ver resposta"
        Quase certamente é um **defeito daquele setor** (sistemático), não um planeta. Um planeta transita sempre: se o sinal fosse real, apareceria nos outros setores com força comparável.

        É o caso de **HD 271883**: sinal de 6,61 dias e 4 900 ppm, perfeito no vetting básico, mas que não reapareceu com a força esperada (SNR esperado de 45 a 64) nos setores 67, 68 e 97. O teste `other_sectors`, do vetting aprofundado, resolveu. Revise a [aula B4](b4-false-positives.md).

!!! example "Pergunta 10"
    Um sinal mostra uma queda pequena na fase 0,5, de cerca de 3 % da profundidade do trânsito principal. Isso prova que é uma binária eclipsante?

    ??? success "Ver resposta"
        **Não.** Planetas gigantes muito quentes brilham o suficiente para que o TESS veja a luz deles sumir quando passam atrás da estrela. Isso é uma **ocultação** e produz uma queda pequena na fase 0,5. Foi o que aconteceu com **WASP-18 b** (cerca de 340 ppm), que o PlanetHunter reprovava como binária até a regra mudar.

        A regra atual só veta se o secundário for de pelo menos **10 %** do principal. Com 3 %, o sinal não é vetado por esse teste. Estrelas companheiras, que emitem muita luz, produzem secundários grandes. Revise a [aula B4](b4-false-positives.md).

## Próximo passo

Passou? Parabéns: você já sabe o que estamos procurando e por que é difícil. O [nível médio](../intermediate/index.md) explica **como** a ferramenta decide: estatística dos sinais, física do trânsito com um pouco mais de matemática, periodogramas, Python com dados reais e vetting na prática.

Antes de começar o médio, se ainda não fez, comece a aula P1 da [trilha de programação](../programming/index.md). Ela passa a ser necessária a partir da aula M4.
