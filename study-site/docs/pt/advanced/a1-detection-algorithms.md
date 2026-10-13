# A1. Algoritmos de detecção a fundo

<p class="meta">Nível avançado · semanas 1–3 · cerca de 14 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - A estatística por trás do BLS (Kovács, Zucker & Mazeh 2002) e por que ela é, no fundo, uma razão sinal-ruído.
    - O que o TLS (Hippke & Heller 2019) muda em relação ao BLS e quanto isso custa.
    - Os trade-offs entre três formas de detrending: biweight, spline e processos gaussianos.
    - Por que monotrânsitos e duotrânsitos são o nicho com mais planetas por achar, e por que são difíceis.
    - Os limites atuais da busca do PlanetHunter e de onde eles vieram.

Na [aula M3](../intermediate/m3-periodograms.md) você viu a ideia do periodograma. Agora a pergunta é: **o que exatamente está sendo maximizado, e por quê?**

## 1. A busca como teste de hipóteses em grade

Toda busca de trânsitos periódicos testa três parâmetros: **período** $P$ (dias), **época** $T_0$ (instante de um trânsito, em BTJD) e **duração** $T_{14}$ (horas). Para cada trio, o algoritmo compara "brilho constante" com "brilho constante, exceto durante trânsitos que se repetem a cada $P$". O periodograma mostra, para cada $P$, a melhora obtida com o melhor $T_0$ e a melhor duração.

Consequência importante: são **milhões de testes**, e o ruído sozinho produz picos. Com um milhão de tentativas, algum pico de 3 sigma aparece por acaso quase com certeza. É o **efeito de olhar em outro lugar** (look-elsewhere effect), que volta na aula A5, no piso de ruído medido pelo projeto.

## 2. BLS: a estatística por trás

O **BLS** (Box Least Squares) foi publicado por Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. O modelo é uma caixa: brilho $H$ fora do trânsito, brilho $L$ dentro, com transição instantânea.

### As definições do artigo

Os dados são $N$ medidas de fluxo $x_i$ com erros $\sigma_i$. Primeiro, subtrai-se a média ponderada, de modo que os dados ficam centrados em zero. Cada ponto recebe um peso normalizado:

$$
w_i = \frac{\sigma_i^{-2}}{\sum_j \sigma_j^{-2}}, \qquad \sum_i w_i = 1 .
$$

Para um período de teste, os pontos são dobrados em fase. Escolhe-se um intervalo de fase candidato a trânsito e define-se:

$$
r = \sum_{i \in \text{trânsito}} w_i, \qquad s = \sum_{i \in \text{trânsito}} w_i \, x_i .
$$

Em palavras: $r$ é a **fração do peso** que cai dentro do trânsito (se todos os erros forem iguais, é simplesmente a fração dos pontos) e $s$ é a **soma ponderada do fluxo** dentro do trânsito. Se há uma queda, $s$ é negativo.

O artigo mostra que a soma dos resíduos ao quadrado do melhor modelo de caixa é

$$
D = \sum_i w_i x_i^2 - \frac{s^2}{r(1-r)} .
$$

O primeiro termo não depende do modelo. Então **minimizar $D$ é o mesmo que maximizar $s^2/[r(1-r)]$**. O BLS calcula essa quantidade para todos os intervalos e guarda o maior valor. A raiz dela é o **SR** (signal residue) daquele período:

$$
\text{SR} = \max \left[ \frac{s^2}{r(1-r)} \right]^{1/2} .
$$

A profundidade do melhor modelo sai de graça: $\delta = H - L = |s| / [r(1-r)]$.

### Por que isso é uma razão sinal-ruído

Suponha erros iguais, $\sigma_i = \sigma$, e um trânsito de profundidade $\delta$ ocupando a fração $r$ dos pontos. Com os dados centrados em zero, o nível dentro é $L = -\delta(1-r)$ e fora é $H = \delta r$. Então $s = rL = -\delta\, r(1-r)$ e

$$
\frac{s^2}{r(1-r)} = \delta^2\, r(1-r) .
$$

Multiplicando por $N/\sigma^2$ (para voltar dos pesos normalizados ao qui-quadrado), a melhora do ajuste é

$$
\Delta\chi^2 = \frac{N \, \delta^2 \, r(1-r)}{\sigma^2}
\quad \Longrightarrow \quad
\sqrt{\Delta\chi^2} = \frac{\delta}{\sigma}\sqrt{N r (1-r)} \approx \frac{\delta}{\sigma}\sqrt{N_\text{em trânsito}} .
$$

É a fórmula de SNR do nível médio: profundidade sobre ruído de um ponto, vezes a raiz do número de pontos em trânsito. O BLS procura o período que **maximiza a SNR de uma caixa**. E vale o que você viu na [aula M1](../intermediate/m1-statistics-for-signals.md): com ruído correlacionado, $\sigma/\sqrt{N}$ subestima o erro e o BLS fica otimista.

### SDE: o pico se destaca?

O SR sozinho depende da escala dos dados. Para comparar estrelas, Kovács et al. definem o **SDE** (Signal Detection Efficiency):

$$
\text{SDE} = \frac{\text{SR}_\text{pico} - \langle \text{SR} \rangle}{\text{desvio padrão}(\text{SR})} .
$$

Em palavras: quantos desvios padrão o pico está acima da média do periodograma. Por ser **relativa ao próprio periodograma**, é comparável entre estrelas de brilho diferente.

## 3. TLS: o que muda

O **TLS** (Transit Least Squares), de Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39, é o algoritmo que o PlanetHunter usa. A ideia central é simples: **um trânsito real não é uma caixa**. Ele tem entrada e saída graduais (ingresso e egresso) e fundo arredondado por causa do escurecimento de borda (a borda da estrela é mais escura que o centro, como você viu na [aula M2](../intermediate/m2-transit-physics.md)).

### As diferenças principais

| Aspecto | BLS | TLS |
|---|---|---|
| Modelo | Caixa de duas alturas | Trânsito com escurecimento de borda (no PlanetHunter, coeficientes da banda do TESS escolhidos pela temperatura e pela gravidade da estrela) |
| Medida de ajuste | $s^2/[r(1-r)]$ | Qui-quadrado do ajuste do modelo |
| Espectro | SR(P) | $\text{SR}(P) = \chi^2_\text{min, global} / \chi^2_\text{min}(P)$, entre 0 e 1 |
| SDE | (pico − média) / desvio | $(1 - \langle\text{SR}\rangle)/\sigma_\text{SR}$, com a tendência do espectro removida |
| Grade de períodos | Livre | Amostragem ótima em frequência (Ofir 2014) |
| Grade de durações | Livre | Limitada pela física: raio e massa da estrela fixam a duração possível para cada período |
| Custo | Baixo | Bem maior; exige paralelismo |

O ganho vem de duas fontes. O modelo realista casa melhor com o sinal, sobretudo em planetas pequenos, onde ingresso e egresso são uma fração grande do trânsito; os autores mostram SDE maior que o do BLS nos mesmos dados. E a grade de durações limitada pela estrela evita testar durações impossíveis, o que reduz as tentativas e os picos espúrios.

O limite **SDE ≥ 9** vem do artigo do TLS: com ruído branco, corresponde a uma probabilidade de alarme falso da ordem de $10^{-4}$ (`sde_min` em `config/thresholds.yaml`).

### O que não aproveitar do TLS sem conferir

Duas saídas do TLS estavam silenciosamente erradas para o uso do projeto, e a auditoria de código de 2026-10-10 encontrou as duas:

- **Duração.** O TLS 2.0 multiplica a duração do trânsito pelo fator de preenchimento da série (a fração de cadências presentes em todo o intervalo). Para um setor, isso fica um pouco abaixo de 1 (0,86 no setor 69). Para dois setores separados por 700 dias, fica perto de 0,07, e um trânsito de 3 h saía com 0,23 h. Como essa mesma duração alimentava o SNR, o mascaramento iterativo e as janelas do vetting, o erro se espalhava pelo pipeline inteiro. O projeto agora desfaz a divisão (`search/stats.py`) e guarda o valor do TLS só como `duration_raw_hours`.
- **SNR e S/N_pink.** O SNR é recalculado na curva achatada, com o T14 físico e um ruído robusto. O TLS já calcula um S/N_pink por trânsito (Pont et al. 2006), que estava sendo descartado; agora ele é combinado, $\sqrt{\sum_i \text{S/N}_{\text{pink},i}^2}$, e guardado sem custo extra de CPU. O vetting o usa com o limite de 9 do QLP.

A regra geral: antes de confiar num número de uma biblioteca, confira a definição dele no artigo e num caso conhecido.

### Medindo a taxa de alarmes falsos: rodadas nulas

O limite de SDE supõe ruído branco; curvas de luz reais não são brancas. O Kepler mediu a taxa de alarmes falsos diretamente (Thompson et al. 2018): buscou em curvas de luz que **não podem** conter trânsitos reais e contou o que saiu. O PlanetHunter faz o mesmo com `planethunter search --null inverted` (o fluxo é virado de cabeça para baixo, e as quedas viram elevações) e `--null scrambled` (cada órbita de dados é deslocada no tempo, e os trânsitos deixam de se alinhar entre órbitas). Todo sinal dessas rodadas é um alarme falso por construção. Elas servem a dois propósitos: estimar quantos dos sinais `NEW` devem ser ruído e dar ao modelo de aprendizado de máquina negativos realistas (aula A4). O custo é uma busca a mais por modo nulo.

### O preço da física: limites estelares

A grade de durações depende do raio e da massa da estrela, e o projeto se cortou nisso duas vezes (histórico do benchmark):

- **Limites estreitos demais.** Com raio e massa limitados a ±30 % do TIC, trânsitos mais curtos que o previsto (impacto alto) ficavam fora da grade. TOI 196.01, 347.01, 386.01 e 2339.01 só apareceram com limites largos (SDE 8,6 a 16,8).
- **Raio estelar no período mínimo.** O TLS deriva o menor período pelo limite de Roche, que depende do raio. Com $R = 4{,}06\,R_\odot$ no TIC, a grade começava em 4,15 dias, e o TOI 196.01 tem 1,16 dia. Correção: modelo com raio e massa limitados a 1,5.
- **Três raios estelares.** O TLS coloca a órbita mais curta em 3 raios estelares, o que punha o período mínimo real entre 0,6 e 1,0 dia: 13 dos 505 TOIs do setor 69 ficavam fora da grade. O projeto agora usa 2 raios estelares, como o QLP (Kunimoto et al. 2023), com um piso de 0,2 dia.

Lição: cada informação "física" dada ao algoritmo é também uma hipótese que pode estar errada.

## 4. Detrending: biweight, spline e GP

Antes de buscar, é preciso remover a variação lenta da estrela (rotação, manchas, sistemáticos do telescópio). A escolha do método decide o que sobrevive.

| Método | Como funciona | Vantagem | Risco |
|---|---|---|---|
| **Biweight** em janela deslizante | Para cada ponto, estima o "nível típico" dos vizinhos numa janela de tempo, dando peso pequeno a pontos muito distantes da mediana | Robusto a trânsitos e outliers; um só parâmetro (a janela); rápido | Janela curta come trânsito longo; janela longa deixa variabilidade rápida |
| **Spline** robusta | Curva suave feita de polinômios por partes, ajustada várias vezes descartando pontos discrepantes | Boa para tendências lentas e suaves | O espaçamento dos nós faz o papel da janela; pode oscilar perto de lacunas |
| **Processo gaussiano** (GP) | Modelo estatístico do ruído correlacionado, com um "kernel" que descreve como pontos próximos se parecem (por exemplo, quase periódico para rotação) | Segue variabilidade complexa de estrelas jovens e ativas; dá incerteza | Flexível demais: absorve o trânsito se ele não for mascarado; caro; exige escolher o kernel |

O artigo do wotan (Hippke et al. 2019, *AJ* 158, 143), biblioteca usada pelo projeto, comparou dezenas de métodos e concluiu que o biweight com janela de cerca de **três vezes a duração do trânsito** é a melhor escolha geral.

### O que o projeto mediu

- Trânsito-caixa de 1 500 ppm sem variabilidade: janela de **0,5 dia** perde 8 % da profundidade num trânsito de 3 h e **40 %** num de 5 h; janela de **1,0 dia** perde 0 % e 6 %. Trânsitos de período acima de 10 dias em estrelas tipo Sol duram 5 a 6 horas: a janela padrão é 1,0 dia.
- **TOI 862.01** (5 092 ppm) some com 1,0 dia (a dispersão da curva fica bem acima do ruído ponto a ponto: variabilidade rápida que sobrou) e aparece com 0,5 dia, SDE 18.
- **TOI 190.01** (5,7 h, 8 248 ppm) vira 347 ppm com janela de 0,3 dia.

Não há janela única para os dois casos. Solução: se a razão entre a dispersão da curva e o ruído ponto a ponto passar de 1,2 (`red_noise_max`), refazer o detrending com 0,5 e 0,3 dia (`fallback_windows_days`) e **buscar em todas as versões**. Com outras mudanças, isso levou o recall de 86,7 % para 88,9 %.

A própria razão tinha uma armadilha. Com o desvio padrão, um trânsito profundo em ruído branco puro dava razão acima de 3, e as estrelas com os trânsitos mais profundos eram mandadas para as janelas curtas que comem trânsitos. Desde 2026-10-10, os dois termos usam a MAD, que poucos pontos dentro do trânsito não conseguem mover (300 estrelas do setor 69: 18,7 % sinalizadas com o desvio padrão, 16,0 % com a MAD; as 8 estrelas que mudaram têm quedas profundas, e 5 delas são TOIs).

**Achatamento para o vetting.** Depois da detecção, a duração e os instantes dos trânsitos são conhecidos, e o vetting pode fazer melhor que a busca: ele achata cada setor com a janela daquele setor, nunca menor que 3 × T14, e **mascara** os trânsitos para que o biweight interpole por cima deles (Hippke et al. 2019). Com um trânsito de 12 h, uma janela simples de 1,0 dia mantém 50 % da profundidade; o achatamento com máscara mantém 99 %.

O caso que ainda falha: **TOI 251.01** (845 ppm, 4,94 d), estrela jovem com ruído vermelho de 1,8, exatamente onde um GP poderia ajudar. O histórico o lista como "próxima hipótese". Hipótese, não solução: só o benchmark vai dizer.

## 5. Monotrânsitos e duotrânsitos: o nicho com mais planetas por achar

Um **monotrânsito** é um único trânsito observado. Um **duotrânsito** são dois trânsitos separados por um intervalo longo, em geral em setores de anos diferentes, sem nenhum trânsito no meio observado.

### Por que é o nicho mais promissor

1. **O TESS observa em blocos de cerca de 27 dias.** Um planeta de 60 dias mostra no máximo um trânsito por setor, e em grande parte do céu a estrela só volta a ser observada anos depois.
2. **Os pipelines oficiais exigem pelo menos dois trânsitos.** Eventos únicos ficam de fora.
3. **A evidência é concreta.** Dos TOIs que nasceram como CTOIs da comunidade (168 até 2021, Zenodo 5130660), a maioria são estrelas fracas das imagens completas ou **trânsitos únicos rejeitados pelas buscas periódicas**.
4. **Planetas de período longo são valiosos**: mais frios e menos irradiados.

Por outro lado, sem período não existem os testes de ímpar/par, secundário e consistência; e um evento único é fácil de imitar (ajuste de apontamento, luz espalhada, um asteroide cruzando a região usada para estimar o fundo do céu).

### Estimando o período pela duração

A duração de um trânsito central ($b = 0$) numa órbita circular é $T \approx P R_\star / (\pi a)$. Combinando com a terceira lei de Kepler, $a^3 = G M_\star P^2 / (4\pi^2)$, e isolando $P$:

$$
P \approx \frac{\pi \, G M_\star \, T^3}{4 \, R_\star^3} .
$$

Se o trânsito não for central ($b > 0$), ele é mais curto do que seria com $b = 0$ para o mesmo período. Logo, usar a duração observada nessa fórmula dá um **limite inferior** para o período. Essa ideia (estimar período a partir da forma de um único trânsito e da densidade da estrela) é a base de trabalhos como Osborn et al. (2016), *MNRAS* 457, 2273, feitos com dados do K2.

### Duotrânsitos: aliases em pente

Com dois trânsitos separados por $\Delta t$, o período verdadeiro é $\Delta t / n$ para algum inteiro $n$. Cada $n$ é um candidato. O limite inferior da duração corta os $n$ grandes. Os setores do TESS em que a estrela foi observada sem trânsito cortam outros: se o alias $n$ prevê um trânsito numa data com dados e nada aparece, ele está descartado.

### Estado no projeto

O PlanetHunter ainda **não tem** detector de monotrânsito. Hoje, `n_transits` veta qualquer sinal com menos de dois trânsitos. Mas a fundação já respeita o nicho: `edge_cutoff_days: 0.0` no detrending preserva eventos perto das bordas dos dados, justamente para não apagar monotrânsitos. O detector está na fase 4 do plano.

## 6. Os limites da busca do projeto

| Parâmetro | Valor | Por quê |
|---|---|---|
| `period_min_days` | 0,2 | Piso absoluto da grade |
| `roche_min_a_rstar` | 2,0 | Órbita mais curta: 2 raios estelares (QLP) |
| `period_max_fraction_of_span` | 0,9 | Precisa caber dois trânsitos no intervalo de dados |
| `n_transits_min` (TLS) | 1 | Deixa o limite de 0,9 acima valer de fato; o vetting continua exigindo 2 trânsitos |
| `period_max_days` | 40 | Teto absoluto, explicado abaixo |
| `max_signals_per_target` | 3 | Busca iterativa: acha, mascara 2 durações em volta, busca de novo |
| `bin_minutes` | 10 | Acelera a busca; perde pouco para períodos acima de 1 dia |

Num setor só (cerca de 27 dias), o período máximo efetivo é 0,9 × 27 ≈ 24 dias. (Até 2026-10-10 ele era, na prática, cerca de 13,5 dias: o padrão do próprio TLS exige espaço para dois trânsitos, o que limita o período à metade do intervalo, e o ajuste de 0,9 não fazia nada.) O teto de 40 dias só morde na busca **multi-setor**. E mordeu: juntando setores separados por anos (cerca de 800 dias no total), apareceram **aliases espúrios de 26 a 64 dias** com um ou dois trânsitos (TIC 41230546 e 31929204). O mecanismo é o pente de duotrânsitos: com dois blocos de dados distantes, muitos períodos $\Delta t / n$ alinham uma queda de ruído num setor com outra no outro, e com milhares de tentativas algum alinhamento acontece. O teto corta o problema na raiz; períodos longos ficam para o futuro detector de monotrânsitos e duotrânsitos.

Outro limite: com poucos trânsitos e lacunas, o TLS às vezes devolve um terço do período (TOI 899.01, 924.01 e 3262.01 apareciam em torno de 4,2 dias). A função `refine_alias` testa $2P$ e $3P$: se as épocas previstas só pelo período curto caem em trechos com dados e sem queda, o período maior vence. Essa correção levou o recall a 91,1 %. Faltava um detalhe até a auditoria: depois de trocar para $kP$, o SNR ficava com o valor medido nas épocas de $P$, baixo demais por um fator $\sqrt{n_A/n}$ (0,58 para $k = 3$). Agora ele é medido de novo nas épocas do período verdadeiro.

!!! tip "Na ferramenta"
    - Todos os parâmetros desta aula estão em `config/thresholds.yaml`, seções `preprocess` e `search`, cada um com o comentário do porquê.
    - O detrending e as variantes de janela estão em `src/planethunter/preprocess/clean.py`; a busca TLS e o `refine_alias`, em `src/planethunter/search/tls.py`.
    - No dossiê, o gráfico "Curva de luz" mostra o resultado do detrending. Compare com a curva bruta e procure trânsitos encolhidos.
    - `uv run planethunter run-target 261136679` roda a busca multi-setor em Pi Mensae; repare nas iterações.

!!! example "Exercício 1. A SNR escondida no BLS"
    Uma estrela tem ruído de 1 000 ppm por ponto de 2 minutos. O setor tem $N = 18\,000$ pontos válidos. Um planeta com período de 5 dias produz trânsitos de 1 000 ppm e 3 horas. Calcule $r$, a melhora $\sqrt{\Delta\chi^2}$ prevista pelo BLS e diga se o sinal passa no limite de SNR do projeto.

    ??? success "Ver resposta"
        1. Fração em trânsito: $r = 3\ \text{h} / (5 \times 24\ \text{h}) = 3/120 = 0{,}025$.
        2. $\sqrt{\Delta\chi^2} = (\delta/\sigma)\sqrt{N r (1-r)} = (1000/1000)\sqrt{18\,000 \times 0{,}025 \times 0{,}975}$.
        3. $18\,000 \times 0{,}025 = 450$ pontos em trânsito; $450 \times 0{,}975 = 438{,}75$; raiz $\approx 20{,}9$.
        4. SNR ≈ 21, bem acima de 7,1. Passa.

        Observação: bins de 10 minutos (5 pontos) reduzem o ruído por ponto para $1000/\sqrt{5} \approx 447$ ppm, mas dividem $N$ por 5. Com ruído branco, a SNR fica igual: o binning acelera sem perder sensibilidade.

!!! example "Exercício 2. Período mínimo de um monotrânsito"
    Você vê um único trânsito de 10 horas numa estrela igual ao Sol ($M = 1\,M_\odot$, $R = 1\,R_\odot$). Use $G M_\odot = 1{,}327 \times 10^{20}\ \text{m}^3/\text{s}^2$ e $R_\odot = 6{,}957 \times 10^{8}\ \text{m}$. Qual o menor período compatível com órbita circular?

    ??? success "Ver resposta"
        1. $T = 10\ \text{h} = 36\,000\ \text{s}$; $T^3 = 4{,}666 \times 10^{13}\ \text{s}^3$.
        2. $R_\star^3 = (6{,}957 \times 10^8)^3 = 3{,}367 \times 10^{26}\ \text{m}^3$.
        3. Numerador: $\pi \times 1{,}327 \times 10^{20} \times 4{,}666 \times 10^{13} = 1{,}945 \times 10^{34}$.
        4. Denominador: $4 \times 3{,}367 \times 10^{26} = 1{,}347 \times 10^{27}$.
        5. $P \approx 1{,}444 \times 10^{7}\ \text{s} \approx 167$ dias.

        Como $b > 0$ encurta o trânsito, o período real é **pelo menos** cerca de 167 dias (órbita circular). Conferência: a Terra tem trânsito de cerca de 13 horas; $(13/10)^3 \times 167 \approx 367$ dias, perto do ano real.

!!! example "Exercício 3. O pente de um duotrânsito"
    A mesma estrela do exercício 2 mostra um segundo trânsito idêntico 730,0 dias depois do primeiro, num setor de dois anos mais tarde. Liste os períodos possíveis. Depois, suponha que o TESS observou a estrela num setor intermediário em que o alias de 365 dias prevê um trânsito no meio dos dados, e nada apareceu. O que sobra?

    ??? success "Ver resposta"
        1. Candidatos: $P_n = 730{,}0/n$.
        2. Do exercício 2, $P \gtrsim 167$ dias, então $n \le 730/167 \approx 4{,}4$, ou seja, $n \in \{1, 2, 3, 4\}$.
        3. Períodos: 730,0; 365,0; 243,3; 182,5 dias.
        4. O setor intermediário elimina $n = 2$ (365 dias). Atenção: ele também elimina $n = 4$, porque todo trânsito previsto por 365 dias também é previsto por 182,5 dias (182,5 é a metade de 365).
        5. Sobram 730,0 e 243,3 dias. Decidir exige observar numa data prevista por um e não pelo outro: é assim que duotrânsitos viram pedidos de observação em solo.

!!! warning "Armadilha comum"
    Concluir que o período está certo porque o pico é alto. Ele pode ser $P/2$, $2P$, $P/3$, um alias multi-setor ou trânsitos de **dois planetas diferentes** combinados (caso HD 23472, aula A2).

## Checklist da aula

- [ ] Li a primeira e a segunda passada de Kovács, Zucker & Mazeh (2002).
- [ ] Sei derivar, com a ajuda desta aula, por que maximizar $s^2/[r(1-r)]$ equivale a maximizar a SNR de uma caixa.
- [ ] Li Hippke & Heller (2019) agora com as equações e sei dizer as três diferenças principais em relação ao BLS.
- [ ] Sei explicar com números do projeto por que a janela de detrending é 1,0 dia e quando o sistema usa 0,5 e 0,3.
- [ ] Sei estimar o período mínimo de um monotrânsito e listar os aliases de um duotrânsito.
- [ ] Sei por que existe o teto `period_max_days: 40`.

## Para ir além

- Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. O artigo original do BLS, com toda a estatística desta aula.
- Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39. O TLS; leia a seção de método e a comparação com o BLS.
- Ofir (2014), *Astronomy & Astrophysics* 561, A138. Como escolher a grade de períodos de forma ótima; o TLS usa essa ideia.
- Hippke et al. (2019), *The Astronomical Journal* 158, 143. O artigo do wotan, com a comparação de métodos de detrending que justifica o biweight.
- Foreman-Mackey et al. (2017), *The Astronomical Journal* 154, 220. O celerite, processos gaussianos rápidos; ponto de partida para testar GP em estrelas ativas.
- Osborn et al. (2016), *Monthly Notices of the RAS* 457, 2273. Trânsitos únicos no K2 e estimativa de período a partir de um só evento.
- Seager & Mallén-Ornelas (2003), *The Astrophysical Journal* 585, 1038. As relações analíticas entre forma do trânsito, densidade estelar e período, base da fórmula do exercício 2.
