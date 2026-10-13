# Autoavaliação do nível avançado

<p class="meta">Nível avançado · semana 16 · cerca de 6 horas</p>

!!! abstract "Como usar esta página"
    - As quatro primeiras perguntas são as do plano de estudos. As outras seis cobrem pontos de cada aula.
    - Escreva sua resposta **antes** de abrir o modelo. Use o caderno de leitura e o de revisões, mas não esta página.
    - As perguntas são abertas. Os modelos de resposta mostram os elementos que uma boa resposta precisa ter, não a única resposta certa.

## Perguntas do plano

!!! question "Pergunta 1. Proponha uma mudança no vetting"
    Proponha uma mudança no vetting do PlanetHunter. Explique a hipótese, como mediria o efeito e qual resultado faria você desistir dela.

    ??? success "Ver resposta"
        Uma boa resposta tem quatro partes. Exemplo de modelo:

        **Mudança.** Novo teste de **profundidade por abertura**: medir a profundidade do trânsito com a abertura do pipeline, com uma abertura menor (só os pixels mais brilhantes do alvo) e com uma maior. Falha leve se a profundidade crescer com a abertura de forma significativa.

        **Hipótese com mecanismo.** Se o trânsito está no alvo, a profundidade fracionária é aproximadamente a mesma em qualquer abertura centrada nele. Se vem de uma vizinha na borda da abertura, a abertura maior inclui mais luz da vizinha e a profundidade muda. Dos 8 FPs do TFOPWG que ainda passam no setor 69, alguns são binárias de fundo; a hipótese é que o teste pegue parte delas.

        **Medição.** Rodar o teste nos 54 `KNOWN_PLANET` e 18 `KNOWN_FP` do benchmark de vetting do setor 69. Métricas: quantos dos 8 FPs restantes passam a falhar; quantos planetas passam a falhar; intervalos de Wilson. Comparação pareada: lista de sinais que mudaram de veredito. Relatório em `docs/benchmarks/`.

        **Critério de desistência, escrito antes.** Desisto se pegar 0 dos 8 FPs restantes, ou se marcar mais de 2 dos 54 planetas, ou se o efeito depender de um único objeto. Também desisto se, ao olhar caso a caso, os FPs pegos já fossem reprovados por outro teste no vetting aprofundado (ganho redundante).

        Pontos que a resposta precisa ter: um mecanismo físico, conjuntos de teste com resposta conhecida, métrica dos dois lados (planetas e FPs), incerteza com amostra pequena e um critério de parada definido antes de ver o resultado.

!!! question "Pergunta 2. A zona de visão contínua"
    Explique por que um sinal novo e profundo, numa estrela da zona de visão contínua do TESS, é quase sempre sistemático.

    ??? success "Ver resposta"
        1. Estrelas perto dos polos da eclíptica (zona de visão contínua) são observadas em muitos setores. No setor 69, os hosts dessa região tinham **10 a 22 setores** de dados.
        2. Um sinal profundo tem SNR alto. Se fosse real e periódico, teria aparecido em muitos desses setores, com SNR enorme somando todos. O SPOC, o QLP e a comunidade já teriam produzido um TOI ou CTOI. Se não está em nenhum catálogo, a explicação mais simples é que ele **não existe** nos outros setores.
        3. Um sinal que aparece em um setor só é a assinatura de um sistemático daquele setor: luz espalhada, ajuste de apontamento, problema de detrending numa borda.
        4. Evidência do projeto: HD 271883, sinal limpo de 6,61 d e 4 900 ppm, passou em todos os testes básicos. Nos setores 67, 68 e 97, o SNR esperado era 45 a 64. Não apareceu. O teste `other_sectors` vetou.
        5. Exceções a considerar: um monotrânsito de período muito longo (raro, porque a cobertura contínua cobre quase um ano) ou um evento que caiu numa lacuna dos outros setores. Por isso o teste exige ausência **decisiva** (SNR esperado ≥ 10 e ≥ 1,5 vez o piso de ruído) em pelo menos dois setores, e faz também a busca às cegas.

!!! question "Pergunta 3. Disseque um artigo"
    Leia um artigo de validação ou confirmação recente de um planeta do TESS. Identifique cada teste de vetting que ele usou e qual o PlanetHunter não tem.

    ??? success "Ver resposta"
        A resposta depende do artigo escolhido. Monte uma tabela com três colunas: teste, evidência no artigo (figura ou tabela), equivalente no PlanetHunter. Testes que costumam aparecer:

        | Teste no artigo | No PlanetHunter |
        |---|---|
        | Relatório DV do SPOC: ímpar/par, secundário, centróide da imagem-diferença | `odd_even`, `secondary`, `tpf_difference_image` |
        | Diagnóstico de fantasma óptico do DV | Não tem |
        | Fotometria em solo (SG1): trânsito no alvo, vizinhas excluídas, profundidade em várias cores | Não tem (fora do escopo; vem do acompanhamento) |
        | Espectroscopia de reconhecimento (SG2): sem binária espectroscópica, parâmetros estelares | Não tem; usa o TIC |
        | Imagem de alta resolução (SG3) com curva de contraste | Não tem; o triceratops roda sem curva de contraste |
        | Indicador de binaridade da astrometria do Gaia (por exemplo, o RUWE) | Não tem |
        | FPP com vespa ou triceratops | `fpp_triceratops` |
        | Velocidade radial (SG4) | Não tem |
        | Consistência entre setores | `other_sectors` |

        A conclusão esperada: o PlanetHunter cobre bem a parte automática feita só com dados do TESS e do Gaia; falta tudo o que exige outro telescópio, mais alguns diagnósticos do DV (fantasma óptico) e da astrometria. A resposta é boa se aponta, para cada lacuna, se ela é implementável no projeto ou só resolvida por acompanhamento.

!!! question "Pergunta 4. Escreva uma submissão"
    Escreva o texto de uma submissão de CTOI para um candidato hipotético, com os números do dossiê.

    ??? success "Ver resposta"
        Modelo, com números **hipotéticos** de um dossiê:

        - **TIC**: XXXXXXXXX
        - **Período**: 9,8714 ± 0,0009 d
        - **Época**: 2 460 156,3381 ± 0,0016 BJD (TDB), no meio dos dados
        - **Profundidade**: 1 240 ± 110 ppm
        - **Duração**: 3,4 ± 0,2 h
        - **Raio estimado**: 3,1 R⊕ para R* = 0,81 R☉ (TIC)
        - **Disposição do usuário**: PC

        **Notas**: "Sinal achado com TLS na curva SPOC de 2 min dos setores 68–69 (PlanetHunter versão X, run Y), 3 trânsitos, SDE 14,2, SNR 11,8. Ímpar/par: diferença 0,6σ. Sem secundário em fase 0,5 (limite 3σ: 180 ppm) nem em outras fases. Formato U (τ/T14 = 0,18). Duração compatível com a densidade estelar do TIC (razão 0,92). Imagem-diferença: centróide a 0,15 ± 0,21 px do alvo. Vizinhos Gaia: nenhum capaz de produzir a queda fora do raio de exclusão de 6″. Não aparece em catálogos de planetas, TOIs, CTOIs nem binárias (espelhos com 6 h); busca no ADS e arXiv em 2026-10-09 sem resultados. Triceratops: FPP 0,08, NFPP 0,0004, cenário concorrente principal PEB. Limitações: sem outros setores com dados; sem imagem de alta resolução. Sugestão: SG1 no próximo trânsito previsto (2 460 412,995 ± 0,023 BJD, 26 órbitas depois da época) e SG3."

        Critérios: época em BJD completo; incertezas em todos os números; testes com valores, não adjetivos; limitações explícitas; vocabulário correto; proveniência; sugestão de acompanhamento com previsão de trânsito.

## Perguntas extras

!!! question "Pergunta 5. O BLS é uma SNR"
    Mostre, com o modelo de caixa e erros iguais, por que maximizar $s^2/[r(1-r)]$ equivale a maximizar a SNR do trânsito.

    ??? success "Ver resposta"
        Com dados centrados em zero, profundidade $\delta$ e fração em trânsito $r$: nível dentro $L = -\delta(1-r)$, fora $H = \delta r$. Então $s = rL = -\delta\, r(1-r)$ e $s^2/[r(1-r)] = \delta^2 r(1-r)$. Voltando dos pesos normalizados ao qui-quadrado com erro $\sigma$: $\Delta\chi^2 = N\delta^2 r(1-r)/\sigma^2$. A raiz é $(\delta/\sigma)\sqrt{N r(1-r)} \approx (\delta/\sigma)\sqrt{N_\text{em trânsito}}$, a SNR. Ponto extra: lembrar que, com ruído vermelho, $\sigma$ por ponto subestima o erro de médias, e a SNR do BLS fica otimista.

!!! question "Pergunta 6. O catálogo que tinha planetas"
    Conte o problema dos hot Jupiters no catálogo de binárias do TESS e explique a regra que o resolveu.

    ??? success "Ver resposta"
        Na calibração do setor 69, os 9 sinais que casaram com o catálogo de binárias de Prša et al. (2022) eram planetas confirmados, como WASP-18 b, WASP-100 b e HATS-16 b. Trânsitos profundos de gigantes quentes, às vezes com ocultação visível, foram incluídos no catálogo por critérios automáticos. A correção define uma ordem de evidência no crossmatch: planeta confirmado > FP/FA do TFOPWG > TOI > CTOI > catálogo de binárias. A lição geral: cada catálogo tem objetivo e taxa de erro; a prioridade deve seguir a força da evidência (medida de massa vence classificação de forma).

!!! question "Pergunta 7. Um planeta com FPP 0,35"
    O planeta confirmado WASP-100 b deu FPP 0,35 no triceratops (TP 0,54, PEB 0,35, PTP 0,11, NFPP ≈ 0). Isso indica um defeito no triceratops?

    ??? success "Ver resposta"
        Não. O FPP mede o que os dados **fornecidos** permitem excluir. Só com fotometria do TESS, sem curva de contraste, o cenário PEB (alvo com companheira ligada não resolvida, eclipsado por uma estrela) reproduz razoavelmente um trânsito profundo. A velocidade radial que confirmou o planeta não entrou no cálculo. Uma curva de contraste de imagem de alta resolução cortaria a prior de companheiras e derrubaria o PEB. NFPP desprezível mostra que nenhuma vizinha conhecida é suspeita. Conclusão: o resultado é coerente e ilustra por que FPP é um teste entre outros, e por que validação exige imagem de alta resolução.

!!! question "Pergunta 8. O ML que vazou"
    Por que o conjunto de treino e teste de um classificador de sinais deve ser separado por estrela, e por que, no projeto, o ML não pode vetar?

    ??? success "Ver resposta"
        Split por estrela: a mesma estrela gera vários sinais (vários setores, vários planetas, iterações). Separando por sinal, a rede reconhece a estrela no teste (ruído, variabilidade, profundidade) e o desempenho medido é memória, não generalização.

        Sem veto: (1) os planetas que o projeto procura estão nos nichos com menos exemplos de treino; (2) vetar um planeta real é irreversível, revisar um falso custa minutos; (3) o vetting determinístico é auditável e medido por benchmark; (4) o ML não recupera o que a busca não detecta. O ML reordena a fila, mantendo o recall.

!!! question "Pergunta 9. Quanto vale 81 %?"
    No benchmark de vetting, 44 de 54 planetas confirmados foram aprovados (81 %). Calcule o intervalo de Wilson de 95 % e diga o que ele implica para comparar duas versões do vetting.

    ??? success "Ver resposta"
        $p = 0{,}8148$; $z^2/n = 3{,}8416/54 = 0{,}0711$; denominador $1{,}0711$. Centro $= (0{,}8148 + 3{,}8416/108)/1{,}0711 = (0{,}8148 + 0{,}0356)/1{,}0711 = 0{,}794$. $p(1-p)/n = 0{,}00279$; $z^2/(4n^2) = 0{,}00033$; soma $0{,}00312$; raiz $0{,}0559$; $h = 1{,}96 \times 0{,}0559/1{,}0711 = 0{,}102$. IC ≈ **69 % a 90 %**.

        Implicação: duas versões com 81 % e 85 % têm intervalos quase iguais. Comparar intervalos não decide. Como os objetos são os mesmos, compare de forma pareada: liste os planetas que mudaram de veredito e use o teste de McNemar, junto com o mecanismo de cada mudança.

!!! question "Pergunta 10. Ausência que não prova nada"
    Um candidato não aparece no setor 95, onde o SNR esperado era 12. O piso de ruído medido na própria estrela nesse setor é 13,5. O candidato deve ser vetado?

    ??? success "Ver resposta"
        Não com base nesse setor. O piso de 13,5 significa que a busca em faixa estreita, nessa estrela, acha picos de SNR 13,5 em 10 % das tentativas em períodos aleatórios. Um sinal real com SNR esperado 12 pode simplesmente não se destacar. O projeto só conta ausência como decisiva se o SNR esperado for ≥ 10 **e** ≥ 1,5 vez o piso (aqui, exigiria 20), e só veta com ausência decisiva em pelo menos dois setores. É o caso real do sinal 1634: a decisão veio da busca às cegas nos setores 95 a 97, que não recuperou nem o período nem o dobro. A ideia geral: um limite fixo de SNR não serve, porque o ruído de busca (mediana 5,2, p90 19, p99 98 no setor 69) varia muito de estrela para estrela.

## Critério de aprovação

- **Concluído com folga**: respostas completas em pelo menos 8 das 10 perguntas, **incluindo** as perguntas 1 e 4. Essas duas são de produção: o que importa é a estrutura (hipótese, medição, critério de parada; efeméride, incertezas, testes, limitações).
- **Quase lá**: 6 ou 7 perguntas completas. Volte às aulas das perguntas que falharam e refaça os exercícios resolvidos sem olhar a resposta.
- **Ainda não**: menos de 6. Releia as aulas A3 e A5, que concentram os conceitos mais cobrados, e refaça a autoavaliação em duas semanas.

Para cada pergunta errada, anote no caderno qual aula responde e o que faltou. Esse registro vale mais que a nota.

Quando passar, o próximo passo é prático: revisar a fila de candidatos de um setor novo com critério, documentar as revisões e, se um candidato sobreviver a tudo, preparar o pacote de submissão da aula A6.
