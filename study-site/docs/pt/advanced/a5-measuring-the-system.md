# A5. Medir o sistema: completude e benchmarks

<p class="meta">Nível avançado · semanas 11–13 · cerca de 14 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - A diferença entre recall, completude e precisão, e qual pergunta cada uma responde.
    - Como funciona o benchmark de recall do projeto e por que a métrica principal é o recall nos TOIs "detectáveis em um setor".
    - Como calcular o intervalo de Wilson à mão e por que ele é melhor que o intervalo "mais ou menos".
    - Como se faz injection-recovery: grade de parâmetros, injeção no fluxo bruto, critério de recuperação.
    - O que é o piso de ruído medido pelo projeto (mediana 5,2; p90 19; p99 98) e por que limite fixo não serve.
    - A metodologia antes/depois para mudar um limite, e como fazer isso você mesmo.

Uma regra do projeto resume esta aula: **mudar busca ou vetting exige rerodar o benchmark e anexar antes e depois**. Sem medição, uma mudança é uma opinião.

## 1. Três perguntas, três métricas

| Métrica | Pergunta | Como se mede |
|---|---|---|
| **Recall** | Dos objetos reais que existem no conjunto, quantos o sistema acha? | Recuperados ÷ total de objetos reais conhecidos |
| **Completude** | Como o recall varia com período, raio, brilho da estrela? | Recall por célula de uma grade de parâmetros, em geral com injeções |
| **Precisão** | Dos alertas que o sistema emite, quantos são reais? | Alertas confirmados ÷ alertas emitidos (exige revisão humana ou acompanhamento) |

Recall e precisão puxam em direções opostas. Afrouxar um limite aumenta o recall e derruba a precisão. Toda mudança precisa medir as duas, ou um substituto razoável para a segunda. No vetting, o projeto usa a **taxa de aprovação de `KNOWN_FP`** como substituto: se ela sobe, o vetting ficou frouxo.

## 2. O benchmark de recall do projeto

O código está em `src/planethunter/benchmark.py`. O procedimento:

1. **Congelar uma lista** (`benchmark build`). Do ExoFOP, pegam-se os TOIs com disposição CP, KP ou PC, "Planet SNR" ≥ 10 e período entre 0,5 e 13 dias que foram observados no setor 69. Resultado: **220 TOIs**. A lista fica gravada em CSV e não muda mais, para que execuções diferentes sejam comparáveis.
2. **Rodar a busca** só nesses alvos (`benchmark run`). **185** têm curva SPOC de 2 minutos.
3. **Avaliar**: um TOI é recuperado se algum sinal do run casa com o período (alias 1, 2 ou 1/2) **e** com a fase. Aliases 3, 1/3, 3/2 e 2/3 são contados à parte, como "achado com período ambíguo".

### Por que "detectáveis em um setor"

No primeiro run, 68 TOIs foram perdidos. Investigando, **55 deles tinham SNR esperado abaixo de 7 só com os dados do setor 69**. O "Planet SNR" do ExoFOP soma todos os setores em que a estrela foi observada. Com um setor só, nenhum pipeline acharia esses objetos. Contá-los como falha mediria o tamanho do conjunto de dados, não a qualidade da busca.

Por isso o benchmark calcula, para cada TOI, o **SNR esperado** neste setor:

$$
\text{SNR}_\text{esperado} = \frac{\delta}{\sigma_\text{p2p}} \sqrt{N_\text{em trânsito}},
\qquad
\sigma_\text{p2p} = \frac{\text{desvio padrão}(\text{diferenças entre pontos vizinhos})}{\sqrt{2}} ,
$$

com a profundidade do catálogo, o ruído ponto a ponto da curva já tratada e o número de pontos que caem dentro dos trânsitos previstos. Um TOI é **detectável** se o SNR esperado é ≥ 7,1 e há pelo menos 2 épocas com dados. São **135**. O ruído ponto a ponto é usado porque é pouco sensível a variações lentas: mede o "chiado" de um ponto para o seguinte.

### O histórico

| Run | Mudança | Recall detectáveis |
|---|---|---|
| baseline | janela 1,0 d, limites estelares ±30 % | 114/135 = 84,4 % |
| 2 | grade de durações larga + janela adaptativa | 117/135 = 86,7 % |
| 3 | variantes de detrending (soma) + modelo estelar limitado a 1,5 | 120/135 = 88,9 % |
| 4 | `refine_alias` + `period_max` 0,9 × intervalo | **123/135 = 91,1 %** (IC 95 % 85,1–94,8 %) |

E por profundidade, no run final:

| Profundidade (ppm) | Recuperados | Total | Recall |
|---|---|---|---|
| 0–500 | 6 | 10 | 60 % |
| 500–1 000 | 11 | 13 | 85 % |
| 1 000–3 000 | 19 | 23 | 83 % |
| 3 000–10 000 | 34 | 36 | 94 % |
| acima de 10 000 | 53 | 53 | 100 % |

A meta do plano é ≥ 90 %. O número agregado passa, mas a tabela mostra onde está o problema: trânsitos rasos. É ali que o próximo trabalho rende.

## 3. Intervalo de Wilson

Com 135 objetos, 91,1 % não é um número exato. Se o projeto rodasse num outro setor com outros 135 TOIs, o resultado seria um pouco diferente. O **intervalo de confiança** diz quanto.

O intervalo "ingênuo" ($p \pm 1{,}96\sqrt{p(1-p)/n}$) falha justamente onde mais importa: perto de 0 % ou 100 % e com amostras pequenas. Com 53 de 53, ele dá largura zero, como se 100 % fosse certeza. O **intervalo de Wilson** (Wilson 1927) corrige isso. Com $p = k/n$ e $z = 1{,}96$ para 95 %:

$$
\text{centro} = \frac{p + \dfrac{z^2}{2n}}{1 + \dfrac{z^2}{n}},
\qquad
h = \frac{z\sqrt{\dfrac{p(1-p)}{n} + \dfrac{z^2}{4n^2}}}{1 + \dfrac{z^2}{n}},
\qquad
\text{IC} = [\text{centro} - h,\ \text{centro} + h] .
$$

É exatamente o que a função `wilson` de `benchmark.py` calcula.

### A conta para 123 de 135

1. $p = 123/135 = 0{,}9111$; $z^2 = 3{,}8416$; $z^2/n = 0{,}02846$; denominador $= 1{,}02846$.
2. Centro: $(0{,}9111 + 3{,}8416/270)/1{,}02846 = (0{,}9111 + 0{,}01423)/1{,}02846 = 0{,}8997$.
3. $p(1-p)/n = 0{,}9111 \times 0{,}0889/135 = 0{,}000600$; $z^2/(4n^2) = 3{,}8416/72\,900 = 0{,}0000527$; soma $0{,}000653$; raiz $0{,}02555$.
4. $h = 1{,}96 \times 0{,}02555 / 1{,}02846 = 0{,}0487$.
5. IC $= [0{,}851;\ 0{,}948]$, ou **85,1 % a 94,8 %**. Confere com o relatório.

Repare que o centro (90,0 %) é um pouco menor que $p$: Wilson "puxa" a estimativa para longe dos extremos, o que é honesto com amostras finitas.

## 4. Injection-recovery

O benchmark em TOIs mede o sistema **no que já se sabe**. Mas os TOIs são, em geral, profundos e em estrelas brilhantes. Para medir os nichos onde o projeto quer achar coisas novas (rasos, longos, estrelas fracas), não há TOIs suficientes. A solução é fabricar o teste: **injetar trânsitos sintéticos em curvas reais** e ver quais o sistema recupera. É o mesmo princípio que o Kepler usou para medir a completude do pipeline (Christiansen et al. 2013).

A receita está na skill `injection-recovery` do projeto:

**Onde injetar.** No fluxo **bruto**, antes do detrending. Assim a medida inclui a perda causada pelo próprio detrending, que a aula A1 mostrou ser grande (até 40 % com janela curta).

**Como gerar.** Com a biblioteca `batman` (Kreidberg 2015): modelo de trânsito com escurecimento de borda quadrático, coeficientes escolhidos pela temperatura da estrela, $a/R_\star$ calculado da densidade estelar e o parâmetro de impacto sorteado.

**A grade.**

| Eixo | Valores |
|---|---|
| Período (d) | 0,5; 1; 2; 4; 8; 13; 20; 27; 40 |
| Raio do planeta (R⊕) | 1; 1,5; 2; 3; 4; 6; 10; 15 |
| Parâmetro de impacto $b$ | 0; 0,3; 0,6; 0,9 |
| Tmag do alvo | 8–10; 10–12; 12–13,5; 13,5–15 |

**As curvas.** 200 curvas reais **sem sinal** (SDE < 6 na busca original) por faixa de Tmag. Pelo menos 50 injeções por célula, com época aleatória.

**O critério.** Recuperado se o período achado está a 1 % do injetado (ou alias 2 ou 1/2) e o SDE passa do limite. Guardar também a profundidade e o SDE medidos, para estimar o viés (o detrending encolhe trânsitos?).

**O relatório.** Mapa de completude (período × raio) por faixa de Tmag, com intervalo de Wilson em cada célula.

Estado no código: o benchmark de recall está implementado; o injection-recovery com grade **ainda não**. É o próximo passo, e um ótimo projeto para quem termina este nível.

## 5. O piso de ruído: 5,2, 19 e 98

O teste `other_sectors` (aula A2) procura o sinal em outros setores com uma busca **numa faixa estreita** em torno do período: 300 períodos a ±1 % de $P$ e outros 300 em torno de $2P$, com três durações. Parece uma busca pequena. Não é.

O projeto mediu o que essa busca acha **em estrelas sem sinal**, em 144 tentativas com períodos aleatórios no setor 69. O SNR do melhor pico:

| Estatística | SNR achado no ruído |
|---|---|
| Mediana | 5,2 |
| Percentil 90 | 19 |
| Percentil 99 | 98 |

Em 10 % das tentativas, o ruído sozinho deu SNR acima de 19. Em 1 %, acima de 98. Duas causas se somam: o efeito de olhar em outro lugar (centenas de períodos, várias durações, todas as fases, e se guarda o máximo) e o **ruído vermelho** com sistemáticos residuais, que produz quedas coerentes de várias horas.

A consequência: **um limite fixo de SNR não serve** para decidir se o sinal "apareceu" em outro setor. O projeto mede o piso **de cada estrela**: roda a mesma busca em 40 períodos aleatórios (entre 0,6 e 1,7 vez $P$, longe de $P/2$, $P$ e $2P$) e usa o percentil 90 como piso. Antes de medi-lo, os trânsitos do próprio candidato são mascarados. Sem a máscara, um sinal forte elevava o próprio piso (um SNR de 2 192 contra um piso de 2 272), e 16 de 24 falhas desse teste eram falsas. Uma ausência só conta como evidência se o SNR esperado é pelo menos 10 **e** pelo menos 1,5 vez o piso. O veto exige ausência decisiva em pelo menos dois setores.

Os casos reais mostram as duas faces:

- **HD 271883** (sinal 1798, 6,61 d): SNR esperado de 45 a 64 nos setores 67, 68 e 97. Não apareceu. Ausência decisiva: veto.
- **Sinal 1634** (11,35 d): SNR esperado de 12 e 9 nos setores 95 e 96, com pisos de 13,5 e 11,6. A ausência ali **não é evidência**: o ruído da própria estrela produziria picos daquele tamanho. A decisão veio da busca às cegas nos setores 95 a 97, que não recuperou nem 11,35 nem 22,7 dias.

## 6. A metodologia antes/depois

Para qualquer mudança em `config/thresholds.yaml` ou no código de busca e vetting:

1. **Hipótese com mecanismo.** Não "acho que 1,2 é melhor que 1,3", mas "TOIs X e Y são perdidos porque o detrending deixa variabilidade; reduzir a janela nessas estrelas deve recuperá-los".
2. **Critério de sucesso e de desistência, escrito antes.** Por exemplo: "aceito se o recall dos detectáveis não cair e pelo menos 2 dos 11 perdidos forem recuperados; desisto se algum planeta `KNOWN_PLANET` passar a ser vetado".
3. **Mesma lista congelada e mesmos espelhos.** Anote o `params_hash` e a `pipeline_version` que o relatório grava.
4. **Uma mudança por vez.** Duas mudanças juntas tornam impossível saber qual fez o quê.
5. **Rodar antes e depois** com o mesmo código, exceto a mudança.
6. **Comparar com pareamento.** Os dois runs usam os **mesmos** objetos. Não basta comparar os intervalos de confiança, que se sobrepõem quase sempre. Liste os objetos que **mudaram de status**: ganhos e perdas.
7. **Medir o outro lado.** Taxa de aprovação de `KNOWN_PLANET` e de `KNOWN_FP` (tabela do `vet`), tempo de busca.
8. **Escrever** `docs/benchmarks/<data>-<sha>.md` com tabela antes/depois, lista de mudanças de status e decisão.

### Comparação pareada em uma linha

Se a mudança fez $g$ objetos passarem de perdido para recuperado e $l$ fazerem o contrário, e se a mudança não tivesse efeito nenhum, cada um desses $g + l$ casos teria chance de 50 % de ir para cada lado. A probabilidade de um resultado tão desequilibrado por acaso é a do **teste de McNemar** exato, uma conta de cara ou coroa:

$$
p = 2 \times P\big(X \ge \max(g, l)\big), \qquad X \sim \text{Binomial}(g + l,\ 0{,}5) .
$$

!!! tip "Na ferramenta"
    - `uv run planethunter benchmark build 69` congela a lista de planetas; com `--kind fp`, a de falsos positivos do TFOPWG.
    - `uv run planethunter benchmark run 69 --skip-ingest` refaz a busca e grava o relatório em `docs/benchmarks/`. Com `--run <run_id>`, só reavalia um run existente.
    - `uv run planethunter vet <run_id>` imprime a tabela de validação por classe (`KNOWN_PLANET`, `KNOWN_FP`...).
    - Os relatórios existentes: `2026-10-09-s0069-history.md` e `2026-10-09-s0069-vetting.md`.

!!! example "Exercício 1. Cem por cento, mas quanto?"
    Na faixa de profundidade acima de 10 000 ppm, o recall foi 53/53. Calcule o limite inferior do intervalo de Wilson.

    ??? success "Ver resposta"
        Com $k = n$, $p = 1$ e o termo $p(1-p)/n$ some. Então $h = (z^2/2n)/(1 + z^2/n)$ e o centro é $(1 + z^2/2n)/(1 + z^2/n)$. O limite inferior fica:

        $$
        \frac{1}{1 + z^2/n} = \frac{1}{1 + 3{,}8416/53} = \frac{1}{1{,}0725} \approx 0{,}932 .
        $$

        "100 %" quer dizer, com 95 % de confiança, **pelo menos 93 %**. O intervalo ingênuo diria "100 % ± 0", o que é falso.

!!! example "Exercício 2. Vale a pena apertar o formato em V?"
    O projeto mudou `v_shape_max` de 0,45 para 0,35. Com 0,45, o teste `shape` não pegava nenhum dos 18 FPs do TFOPWG. Com 0,35, pega 8 de 18 e marca 3 de 50 planetas (HIP 65 A b, LTT 9779 b e TOI-2382 b, todos rasantes). (a) Calcule o IC de Wilson para 8/18. (b) A mudança se justifica? Que precaução foi tomada?

    ??? success "Ver resposta"
        (a) $p = 0{,}444$, $z^2/n = 0{,}2134$, denominador $1{,}2134$. Centro $= (0{,}444 + 0{,}1067)/1{,}2134 = 0{,}454$. $p(1-p)/n = 0{,}01372$; $z^2/(4n^2) = 0{,}00296$; soma $0{,}01668$; raiz $0{,}1292$; $h = 1{,}96 \times 0{,}1292/1{,}2134 = 0{,}209$. IC $\approx$ **25 % a 66 %**. Com 18 objetos, a incerteza é enorme.

        (b) Mesmo no pior caso (25 %), sair de 0 para pelo menos um quarto dos FPs é um ganho real. O custo são 3 planetas rasantes marcados. A precaução na época: o teste virou **falha leve** (peso 0,5 no score), não veto, então um planeta rasante podia continuar na fila se o resto estivesse limpo. Desde a auditoria de 2026-10-10 `shape` é **falha grave** (uma falha sozinha reprova o veredito, sem ser veto): medido nos setores 69 e 107, custa uns 3 planetas rasantes por setor e barra de 4 a 9 binárias eclipsantes encontradas na metade do período. As duas decisões estão comentadas em `config/thresholds.yaml`, com nomes e números.

!!! example "Exercício 3. Três ganhos bastam?"
    Do run 2 para o run 3, o recall subiu de 117 para 120. Suponha que 3 TOIs passaram a ser recuperados e nenhum foi perdido. (a) Qual o $p$ de McNemar? (b) Isso invalida a mudança?

    ??? success "Ver resposta"
        (a) $g = 3$, $l = 0$. $P(X \ge 3)$ com $X \sim \text{Binomial}(3; 0{,}5)$ é $0{,}5^3 = 0{,}125$. $p = 2 \times 0{,}125 = 0{,}25$. Sozinho, o resultado é compatível com acaso.

        (b) Não invalida. A estatística diz que 3 ganhos não provam nada **por si**. Mas cada ganho tem um mecanismo diagnosticado antes (por exemplo, TOI 862.01 só aparece com janela de 0,5 d, por variabilidade rápida medida) e nenhuma perda. Hipótese com mecanismo + ganhos nos objetos previstos + zero perdas é evidência forte. O que seria preocupante: ganhos em objetos que a hipótese não previa, ou qualquer perda sem explicação.

!!! example "Exercício 4. Quanto custa a grade de injeção?"
    Quantas buscas exige a grade completa da seção 4 com 50 injeções por célula? O benchmark buscou 185 alvos em 1,3 minuto com 15 processos. Estime o tempo.

    ??? success "Ver resposta"
        1. Células: $9 \times 8 \times 4 \times 4 = 1\,152$. Injeções: $1\,152 \times 50 = 57\,600$ buscas.
        2. Tempo por alvo (relógio, 15 processos): $1{,}3 \times 60 / 185 \approx 0{,}42$ s.
        3. Total: $57\,600 \times 0{,}42 \approx 24\,000$ s, cerca de **6,7 horas** na mesma máquina.
        4. Viável numa noite. Na prática, comece com uma faixa de Tmag e uma fatia da grade para validar o código antes de gastar a noite.

## Prática: mude um limite e meça

Faça numa branch do git (`git switch -c experimento-<nome>`), nunca direto na principal.

1. Escolha **um** limite do vetting, por exemplo `duration_ratio_max` (1,67) ou `odd_even_fail_sigma` (3,0). Escreva a hipótese e os critérios de sucesso e desistência.
2. Gere as listas: `uv run planethunter benchmark build 69` e `uv run planethunter benchmark build 69 --kind fp`.
3. Rode a busca nos alvos das duas listas (`uv run planethunter search --sector 69 --tics <TICs separados por vírgula>`), depois `crossmatch` e `vet` no run. Guarde a tabela de validação: esse é o **antes**.
4. Mude o limite. Rode `vet` de novo no mesmo run (mudanças de vetting não exigem nova busca). Esse é o **depois**.
5. Compare: taxa de aprovação de `KNOWN_PLANET` e `KNOWN_FP` com Wilson, lista de sinais que mudaram de veredito.
6. Se mudar um parâmetro de busca (`window_length_days`, por exemplo), rode `benchmark run 69 --skip-ingest` antes e depois e compare o recall pareado.
7. Escreva uma página em `docs/benchmarks/` com hipótese, tabela, mudanças de status e decisão. Mesmo que a decisão seja "desisti". Um experimento negativo bem documentado evita que outra pessoa o repita.

## Checklist da aula

- [ ] Sei a diferença entre recall, completude e precisão.
- [ ] Sei explicar por que a métrica principal é o recall nos 135 detectáveis, e não nos 220.
- [ ] Calculei à mão o intervalo de Wilson para 123/135 e para 53/53.
- [ ] Sei descrever a grade de injection-recovery e por que a injeção é no fluxo bruto.
- [ ] Sei explicar o piso de ruído (5,2; 19; 98) e como o projeto o usa.
- [ ] Fiz uma mudança de limite numa branch, medi antes e depois e escrevi o relatório.

## Para ir além

- Wilson (1927), *Journal of the American Statistical Association* 22, 209. O artigo original do intervalo; curto e legível.
- Brown, Cai & DasGupta (2001), *Statistical Science* 16, 101. Mostra, com gráficos, por que o intervalo ingênuo falha e por que Wilson é uma boa escolha.
- Christiansen et al. (2013), *The Astrophysical Journal Supplement Series* 207, 35. Injeção de trânsitos nos pixels do Kepler para medir a recuperação do pipeline; o modelo do que o projeto quer fazer.
- Burke et al. (2015), *The Astrophysical Journal* 809, 8. Como a completude medida entra no cálculo de taxas de ocorrência de planetas.
- Kreidberg (2015), *Publications of the Astronomical Society of the Pacific* 127, 1161. O `batman`, usado para gerar os trânsitos sintéticos.
- McNemar (1947), *Psychometrika* 12, 153. O teste para comparar duas proporções medidas nos mesmos objetos.
