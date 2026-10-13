# P2. NumPy, pandas e Matplotlib

<p class="meta">Trilha de programação · depois do básico, antes de M4 · cerca de 12 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Usar arrays do NumPy para fazer contas em milhares de pontos de uma vez.
    - Simular uma curva de luz com ruído e um trânsito em forma de caixa, e medir a profundidade.
    - Ler a tabela de TOIs do ExoFOP com pandas, filtrar e resumir.
    - Fazer gráficos com Matplotlib: curva de luz, curva dobrada no período e diagrama período versus raio.

Pré-requisito: a [aula P1](p1-python-basics.md). Na pasta de estudos, instale as bibliotecas (se ainda não fez):

```powershell
uv add numpy pandas matplotlib
```

## NumPy: contas com muitos números de uma vez

Uma curva de luz do TESS tem cerca de 20 000 medidas por setor. Fazer contas com um laço `for`, ponto a ponto, é lento e verboso. O **NumPy** resolve isso com o **array**: uma sequência de números do mesmo tipo em que cada operação vale para todos os elementos ao mesmo tempo. Isso se chama **operação vetorial**.

```python
import numpy as np

prof_ppm = np.array([84, 1251, 10090])   # Terra, Netuno, Júpiter no Sol
print(prof_ppm / 1e6)                    # divide os três de uma vez
print(np.sqrt(prof_ppm / 1e6) * 109.1)   # raios em R_terra: ~[1, 3.9, 11]
```

Com uma lista comum, `lista / 1e6` dá erro. Com array, funciona. É a diferença mais importante entre os dois.

Outras ferramentas que você vai usar o tempo todo:

| Código | O que faz |
|---|---|
| `np.arange(0, 27, 0.5)` | Números de 0 até antes de 27, de 0,5 em 0,5 |
| `np.median(a)`, `np.mean(a)`, `np.std(a)` | Mediana, média e desvio padrão |
| `a > 1.0` | Array de `True`/`False`, uma **máscara** |
| `a[mascara]` | Só os elementos onde a máscara é `True` |
| `np.abs(a)` | Valor absoluto de cada elemento |

## Simular uma curva de luz

Vamos fabricar uma curva de luz com um trânsito conhecido. Assim você sabe a resposta certa e pode testar se a sua medida a recupera. É a mesma ideia do teste de injeção de trânsitos que o projeto usa para medir a si mesmo (aula A5).

Crie o arquivo `simula.py`:

```python
"""Simula 27 dias de TESS (cadência de 2 min) com um trânsito em caixa e ruído."""
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(seed=42)   # gerador de números aleatórios, sempre igual

# 1. Eixo do tempo: um setor de 27 dias, um ponto a cada 2 minutos
cadencia_dias = 2 / (60 * 24)
tempo = np.arange(0.0, 27.0, cadencia_dias)
print("pontos:", tempo.size)            # 19440

# 2. Parâmetros do planeta inventado
periodo = 3.0            # dias
t0 = 1.5                 # instante do primeiro trânsito, dias
duracao_horas = 3.0
profundidade_ppm = 5000.0
ruido_ppm = 1000.0       # espalhamento de cada medida

# 3. Fase: distância de cada ponto até o trânsito mais próximo, em dias
fase = (tempo - t0 + 0.5 * periodo) % periodo - 0.5 * periodo
em_transito = np.abs(fase) < (duracao_horas / 24) / 2

# 4. Modelo de caixa: brilho 1 fora do trânsito, 1 - profundidade dentro
modelo = np.ones_like(tempo)
modelo[em_transito] = 1.0 - profundidade_ppm / 1e6

# 5. Ruído gaussiano somado ao modelo
ruido = rng.normal(loc=0.0, scale=ruido_ppm / 1e6, size=tempo.size)
fluxo = modelo + ruido
```

O passo 3 é o coração da simulação. O operador `%` dá o resto da divisão. Ele "enrola" o tempo em voltas de um período, como um relógio que volta ao zero a cada 3 dias. Somar e subtrair meio período centraliza o trânsito em fase zero. O resultado `fase` vai de −1,5 a +1,5 dia.

O passo 5 usa um **ruído gaussiano** (distribuição normal, aula M1): cada medida erra um pouco, para cima ou para baixo, com desvio padrão de 1 000 ppm.

### Medir a profundidade

Agora finja que não sabe a resposta. Compare o brilho típico dentro e fora do trânsito. Use a **mediana**, que é menos sensível a pontos estranhos do que a média.

```python
nivel_fora = np.median(fluxo[~em_transito])    # ~ quer dizer "não"
nivel_dentro = np.median(fluxo[em_transito])
prof_medida = (1 - nivel_dentro / nivel_fora) * 1e6
n_dentro = em_transito.sum()                   # True conta como 1
snr = prof_medida / (ruido_ppm / np.sqrt(n_dentro))

print(f"pontos em trânsito: {n_dentro}")       # 801
print(f"profundidade medida: {prof_medida:.0f} ppm (verdadeira: 5000)")   # ~4975
print(f"SNR aproximado: {snr:.0f}")            # ~141
```

Por que dividir o ruído por $\sqrt{N}$? Ao fazer a média de $N$ medidas independentes, o erro da média cai com a raiz de $N$. Com 801 pontos em trânsito, o ruído efetivo cai de 1 000 para cerca de 35 ppm. Uma queda de 5 000 ppm fica muito acima disso. Esta é uma versão simplificada da **razão sinal-ruído** (SNR) que o PlanetHunter exige ser pelo menos 7,1 (aula M1).

## Matplotlib: ver os dados

O **Matplotlib** desenha gráficos. Continue no mesmo arquivo:

```python
fig, eixos = plt.subplots(2, 1, figsize=(10, 7))

# Painel de cima: a curva de luz inteira
eixos[0].plot(tempo, fluxo, ".", markersize=1, color="0.5")
eixos[0].set_xlabel("tempo (dias)")
eixos[0].set_ylabel("brilho relativo")
eixos[0].set_title("Curva de luz simulada")

# Painel de baixo: curva dobrada (todos os trânsitos sobrepostos)
fase_horas = fase * 24
eixos[1].plot(fase_horas, fluxo, ".", markersize=1, color="0.7", label="medidas")

# Médias em caixas de 15 minutos, para enxergar a forma
bordas = np.linspace(-36, 36, 289)               # 288 caixas de 0,25 h
idx = np.digitize(fase_horas, bordas) - 1        # em que caixa cai cada ponto
soma = np.bincount(idx, weights=fluxo, minlength=288)
contagem = np.bincount(idx, minlength=288)
centros = 0.5 * (bordas[:-1] + bordas[1:])
eixos[1].plot(centros, soma / contagem, "o", color="C3", label="média em 15 min")

eixos[1].set_xlim(-6, 6)
eixos[1].set_xlabel("horas desde o centro do trânsito")
eixos[1].set_ylabel("brilho relativo")
eixos[1].legend()

fig.tight_layout()
plt.show()
```

Rode com `uv run python simula.py`. No painel de cima, o trânsito quase some no ruído. No de baixo, depois de **dobrar** a curva no período, os 9 trânsitos se empilham e a caixa aparece nítida. Isso é o que o dossiê do PlanetHunter mostra na seção "Trânsito dobrado".

`np.bincount` soma os fluxos de cada caixa de uma vez, sem laço. Dividir a soma pela contagem dá a média por caixa.

!!! info "Por que dobrar funciona"
    Dobrar no período certo põe todos os trânsitos no mesmo lugar. O ruído, que é aleatório, se cancela na média. O trânsito, que se repete, se soma. Dobrar no período errado espalha os trânsitos e a caixa some. Um periodograma (aula M3) é, no fundo, testar milhares de dobras e ver qual deixa a caixa mais funda.

## pandas: tabelas

O **pandas** trabalha com tabelas, chamadas **DataFrame**: linhas e colunas com nome, como uma planilha que você controla com código.

### Ler a lista de TOIs do ExoFOP

O ExoFOP publica a lista de todos os TOIs (candidatos oficiais do TESS) num arquivo CSV, um texto com valores separados por vírgula. O pandas lê direto da internet:

```python
import pandas as pd

URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
tois = pd.read_csv(URL, low_memory=False)
tois.to_csv("tois.csv", index=False)     # guarda uma cópia local
print(tois.shape)                        # (linhas, colunas)
```

Nas próximas vezes, leia a cópia local com `pd.read_csv("tois.csv")`. É mais rápido e poupa o servidor do ExoFOP.

Em 9 de outubro de 2026 a tabela tinha 8 151 linhas e 63 colunas. Os seus números serão maiores: a lista cresce toda semana.

### Olhar e selecionar colunas

```python
colunas = ["TOI", "TIC ID", "TFOPWG Disposition", "Period (days)",
           "Depth (ppm)", "Planet Radius (R_Earth)"]
print(tois[colunas].head())             # as 5 primeiras linhas
print(tois["TFOPWG Disposition"].value_counts(dropna=False))
```

`value_counts` conta quantas vezes cada valor aparece. A coluna `TFOPWG Disposition` traz a decisão do grupo de acompanhamento do TESS:

| Código | Significado | Em 9/10/2026 |
|---|---|---|
| PC | Candidato a planeta | 4 820 |
| FP | Falso positivo | 1 315 |
| CP | Planeta confirmado (achado pelo TESS) | 815 |
| KP | Planeta já conhecido antes do TESS | 606 |
| APC | Candidato ambíguo | 490 |
| FA | Alarme falso | 100 |

### Filtrar

Filtrar no pandas é usar uma máscara, igual ao NumPy:

```python
# Planetas confirmados ou conhecidos
planetas = tois[tois["TFOPWG Disposition"].isin(["CP", "KP"])]

# Desses, os de período menor que 1 dia, do mais profundo para o mais raso
curtos = planetas[planetas["Period (days)"] < 1.0]
print(len(planetas), len(curtos))       # 1421 e 78 em 9/10/2026
print(curtos.sort_values("Depth (ppm)", ascending=False)[colunas].head(8))

# Um alvo específico: WASP-18, TIC 100100827
wasp18 = tois[tois["TIC ID"] == 100100827]
print(wasp18[["TOI", "TFOPWG Disposition", "Period (days)", "Depth (ppm)",
              "Duration (hours)", "Planet Radius (R_Earth)", "Sectors"]])
```

WASP-18 b aparece como TOI-185.01, disposição KP, período 0,941453 dia, profundidade 11 445 ppm, duração 2,05 horas, raio 15,3 R⊕, observado nos setores 2, 3, 29, 30 e 69. Você vai medir esses números sozinho na [aula P3](p3-lightkurve-in-practice.md).

Para combinar condições, use `&` (e) e `|` (ou), com cada condição entre parênteses:

```python
pequenos = planetas[(planetas["Planet Radius (R_Earth)"] < 2) &
                    (planetas["Period (days)"] < 10)]
```

### Estatísticas e grupos

```python
print(planetas["Period (days)"].describe())   # contagem, média, quartis...
print(tois.groupby("TFOPWG Disposition")["Planet Radius (R_Earth)"].median())
```

`describe` mostra que a mediana do período dos planetas CP e KP é de cerca de 4,3 dias. A busca do TESS favorece períodos curtos: com só 27 dias por setor, um planeta de 4 dias transita várias vezes, um de 40 dias talvez uma só.

`groupby` separa a tabela por disposição e calcula a mediana do raio em cada grupo. Em 9/10/2026, os CP tinham mediana de 3,2 R⊕, e os FP, de 10,0 R⊕. Falsos positivos tendem a parecer "grandes", porque muitos são binárias eclipsantes com quedas profundas.

### Gráfico período versus raio

```python
fig, ax = plt.subplots(figsize=(8, 6))
for disp, cor in [("PC", "0.7"), ("FP", "C3"), ("CP", "C0"), ("KP", "C2")]:
    grupo = tois[tois["TFOPWG Disposition"] == disp]
    ax.scatter(grupo["Period (days)"], grupo["Planet Radius (R_Earth)"],
               s=4, color=cor, label=f"{disp} ({len(grupo)})")
ax.set_xscale("log")      # escala logarítmica: 1, 10, 100 com o mesmo espaço
ax.set_yscale("log")
ax.set_xlabel("período (dias)")
ax.set_ylabel("raio (R_terra)")
ax.legend()
plt.show()
```

A **escala logarítmica** dá o mesmo espaço para "de 1 a 10" e "de 10 a 100". Sem ela, quase todos os pontos ficariam espremidos num canto.

!!! tip "Na ferramenta"
    O PlanetHunter lê exatamente esse CSV do ExoFOP, com as mesmas colunas (`TFOPWG Disposition`, `Period (days)`, `Epoch (BJD)`). Veja `normalize_exofop_toi` em `src/planethunter/catalogs/mirrors.py`, que monta o espelho local usado no crossmatch, e `build` em `src/planethunter/benchmark.py`, que escolhe os TOIs de um setor com `str.split(",")` na coluna `Sectors`, como no exercício 2 abaixo. As curvas de luz são gravadas como arrays NumPy `float32` (o tempo em `float64`), e quase toda função do pipeline recebe e devolve DataFrames.

## Exercícios

!!! example "Exercício 1. Uma Terra no ruído"
    No `simula.py`, troque a profundidade para 84 ppm (a Terra diante do Sol) e mantenha ruído de 1 000 ppm. Calcule o SNR. O planeta seria detectado pelo critério SNR ≥ 7,1? E com 500 ppm?

    ??? success "Ver resposta"
        Com os mesmos 801 pontos em trânsito, o ruído efetivo é $1000/\sqrt{801} \approx 35$ ppm.

        - 84 ppm: SNR $\approx 84/35 \approx 2{,}4$. Não passa. Uma Terra num único setor, com esse ruído, fica escondida.
        - 500 ppm: SNR $\approx 14$. Passa com folga.

        Os valores medidos variam um pouco, porque o ruído é aleatório. Para uma Terra aparecer, é preciso menos ruído (estrela mais brilhante), mais trânsitos (vários setores) ou uma estrela menor, que torna a queda mais funda.

!!! example "Exercício 2. TOIs do setor 69"
    A coluna `Sectors` é um texto como `"2,3,29,30,69"`. Selecione os TOIs observados no setor 69 e conte por disposição.

    ??? success "Ver resposta"
        ```python
        listas = tois["Sectors"].fillna("").astype(str).str.split(",")
        no_69 = listas.apply(lambda xs: "69" in [x.strip() for x in xs])
        s69 = tois[no_69]
        print(len(s69))
        print(s69["TFOPWG Disposition"].value_counts(dropna=False))
        ```
        `str.split(",")` transforma cada texto numa lista. `apply` roda uma pequena função (`lambda`) em cada linha. Procurar `"69"` dentro da lista evita confundir 69 com 169. Em 9/10/2026 eram 407 TOIs: 260 PC, 74 CP, 37 FP, 22 KP, 13 APC, 1 FA. Não use `str.contains("69")`: ele aceitaria um setor 169 no futuro.

!!! example "Exercício 3. Dobrar no período errado"
    Na simulação, dobre a curva em 6 dias (o dobro) e em 1,5 dia (a metade) em vez de 3. Meça a profundidade no centro em cada caso. O que acontece?

    ??? success "Ver resposta"
        ```python
        for p in (6.0, 1.5):
            f = (tempo - t0 + 0.5 * p) % p - 0.5 * p
            dentro = np.abs(f) < (duracao_horas / 24) / 2
            print(p, (1 - np.median(fluxo[dentro])) * 1e6)
        ```
        - Com 6 dias (2P), o centro ainda mostra cerca de 5 000 ppm, mas só metade dos trânsitos está ali. A outra metade cai em fase ±3 dias, a "fase 0,5". Visualmente parece uma binária com dois eclipses iguais.
        - Com 1,5 dia (P/2), metade das "janelas" em fase zero não tem trânsito. A profundidade medida cai para cerca de 2 500 ppm, a metade.

        É por isso que aliases como $2P$ e $P/2$ enganam (aula M3), e por isso o vetting compara trânsitos ímpares e pares (aula M5).

## Checklist da aula

- [ ] Fiz contas com arrays sem usar laços
- [ ] Simulei uma curva com trânsito e recuperei a profundidade
- [ ] Calculei um SNR aproximado e entendi o papel de $\sqrt{N}$
- [ ] Fiz o gráfico da curva e da curva dobrada com médias por caixa
- [ ] Li o CSV de TOIs, filtrei por disposição e período e achei WASP-18 b
- [ ] Usei `describe` e `groupby`
- [ ] Fiz o diagrama período versus raio em escala logarítmica
- [ ] Resolvi os três exercícios

## Para ir além

- NumPy, guia para iniciantes absolutos ([numpy.org](https://numpy.org/doc/stable/user/absolute_beginners.html)). Explica arrays, máscaras e operações vetoriais com calma.
- pandas, "10 minutes to pandas" ([pandas.pydata.org](https://pandas.pydata.org/docs/user_guide/10min.html)). Tour rápido por leitura, seleção, filtro e agrupamento.
- Página de download de TOIs do ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/view_toi.php)). Mostra a mesma tabela no navegador, útil para conferir seus filtros.
- Curso em Vídeo — Python, mundo 3 (Gustavo Guanabara). Reforça listas, dicionários e funções, base para usar bem o NumPy e o pandas.
