# P3. Lightkurve na prática

<p class="meta">Trilha de programação · junto do módulo M4 · cerca de 10 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Buscar e baixar curvas de luz reais do TESS com a biblioteca Lightkurve.
    - Limpar, achatar (flatten), achar o período com BLS e dobrar a curva.
    - Medir a profundidade do trânsito e estimar o raio do planeta.
    - Abrir os arquivos Parquet que o PlanetHunter grava e consultar o banco DuckDB com SQL.

Pré-requisitos: [P2](p2-numpy-pandas-matplotlib.md) e a [aula M3](../intermediate/m3-periodograms.md) sobre periodogramas. Esta aula é a parte prática da [aula M4](../intermediate/m4-tess-data-in-python.md). Você vai precisar de internet. Na pasta de estudos:

```powershell
uv add lightkurve pyarrow duckdb
```

## O alvo: WASP-18 b

Vamos trabalhar com **WASP-18 b**, um planeta gigante muito quente, colado na sua estrela.

| Dado | Valor (ExoFOP, TOI-185.01) |
|---|---|
| Estrela | WASP-18, TIC 100100827, Tmag 8,83, raio 1,35 R☉ |
| Período | 0,941453 dia (22,6 horas) |
| Profundidade | 11 445 ppm (cerca de 1 %) |
| Duração | 2,05 horas |
| Disposição | KP (planeta conhecido antes do TESS) |

É um alvo ótimo para aprender: o trânsito é fundo e o período curto. Num setor de 27 dias cabem mais de 20 trânsitos. Ele também aparece numa das histórias reais do projeto: o PlanetHunter já o confundiu com uma binária eclipsante (guia, seção 5).

Junte os blocos das seções 1 a 5, na ordem, num arquivo `wasp18.py` e rode com `uv run python wasp18.py`.

## 1. Buscar

```python
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np

busca = lk.search_lightcurve("TIC 100100827", mission="TESS",
                             author="SPOC", exptime=120)
print(busca)
```

`search_lightcurve` pergunta ao **MAST**, o arquivo público de dados do TESS, quais curvas existem. Os filtros pedem as curvas do **SPOC** (o pipeline oficial da NASA) com cadência de 120 segundos. Em outubro de 2026 a resposta tinha 10 linhas: setores 2, 3, 29, 30, 69, 96, 103, 104, 105 e 106.

Ao importar o Lightkurve pode aparecer um aviso sobre `oktopus`. Pode ignorar: é um módulo opcional que não usamos.

## 2. Baixar o setor 69

```python
busca69 = lk.search_lightcurve("TIC 100100827", author="SPOC",
                               exptime=120, sector=69)
lc_bruta = busca69.download()     # baixa e guarda em cache no seu disco
print(len(lc_bruta))              # 16499 medidas
print(lc_bruta.time[:3])          # tempo em BTJD
print(lc_bruta.flux.unit)         # electron / s
print(lc_bruta.meta["RADIUS"], lc_bruta.meta["TESSMAG"], lc_bruta.meta["TEFF"])
lc_bruta.plot()
```

`download()` devolve um objeto **LightCurve**: uma tabela com `time` (tempo em BTJD), `flux` (brilho em elétrons por segundo, já corrigido pelo SPOC, o chamado PDCSAP) e `flux_err` (erro de cada medida). O dicionário `meta` guarda o cabeçalho do arquivo, com dados da estrela: raio 1,3466 R☉, Tmag 8,83, temperatura 6 226 K.

Por padrão, `download()` já descarta medidas que o TESS marcou como ruins, como as dos ajustes de apontamento ("momentum dumps").

## 3. Limpar

```python
lc = lc_bruta.remove_nans().normalize()
lc = lc.remove_outliers(sigma_upper=4, sigma_lower=np.inf)
print(len(lc))                    # 14665
```

- `remove_nans()` tira medidas vazias (NaN quer dizer "não é um número").
- `normalize()` divide pelo brilho mediano. O fluxo passa a ficar em torno de 1, e uma queda de 0,01 significa 1 %.
- `remove_outliers` corta pontos a mais de 4 desvios padrão **acima** da curva. O `sigma_lower=np.inf` desliga o corte para baixo. Cortar para baixo apagaria os próprios trânsitos. O PlanetHunter faz o mesmo: `sigma_upper: 4.0` em `config/thresholds.yaml`.

## 4. Achatar e achar o período com BLS

A estrela varia um pouco ao longo dos dias. **Achatar** (flatten, ou detrending) estima essa variação lenta e divide por ela. O parâmetro `window_length` é o tamanho da janela, em número de medidas, e precisa ser ímpar. Com 901 medidas de 2 minutos, a janela tem 30 horas, bem mais longa que o trânsito de 2 horas.

Fazemos em duas passadas. A primeira acha os trânsitos de forma grosseira. A segunda refaz o achatamento **escondendo** os trânsitos, para que o filtro não "coma" parte da queda.

```python
periodos = np.linspace(0.5, 10, 20000)        # períodos testados, em dias
duracoes = [0.04, 0.06, 0.08, 0.10, 0.12]     # durações testadas, em dias

# Passada 1
pg1 = lc.flatten(window_length=901).to_periodogram(
    method="bls", period=periodos, duration=duracoes)
P = float(pg1.period_at_max_power.value)
T0 = float(pg1.transit_time_at_max_power.value)
D = float(pg1.duration_at_max_power.value)

# Passada 2: máscara nos trânsitos e novo achatamento
mascara = lc.create_transit_mask(period=P, transit_time=T0, duration=1.5 * D)
plana = lc.flatten(window_length=901, mask=mascara)
pg = plana.to_periodogram(method="bls", period=periodos, duration=duracoes)
P = float(pg.period_at_max_power.value)
T0 = float(pg.transit_time_at_max_power.value)
D = float(pg.duration_at_max_power.value)
print(f"P = {P:.5f} d   T0 = {T0:.4f} BTJD   duração = {D * 24:.1f} h")
pg.plot()
```

O **BLS** (Box Least Squares) testa cada período e cada duração da lista, encaixa uma caixa nos dados dobrados e mede o quanto ela explica a queda. O resultado é um **periodograma** com um pico no período certo (aula M3). Saída:

```text
P = 0.94130 d   T0 = 3182.7619 BTJD   duração = 1.9 h
```

O período bate com o do ExoFOP até a terceira casa decimal. A diferença na quarta vem da grade: 20 000 períodos entre 0,5 e 10 dias têm passo de 0,0005 dia.

!!! note "Por que `float(...)`?"
    O Lightkurve devolve os resultados como grandezas com unidade (dias) e, nas versões recentes da Astropy, com "máscara" embutida. `float(x.value)` transforma tudo em número simples. Sem isso, `create_transit_mask` dá erro (`TypeError: cannot write to unmasked output`) com Lightkurve 2.6 e Astropy 8.

## 5. Dobrar e medir

```python
dobrada = plana.fold(period=P, epoch_time=T0)
fase = np.asarray(dobrada.time.value, dtype=float)    # dias desde o centro
fluxo = np.asarray(dobrada.flux.value, dtype=float)

dentro = np.abs(fase) < 0.25 * D      # miolo do trânsito
fora = np.abs(fase) > 1.0 * D         # bem longe do trânsito
nivel = np.median(fluxo[fora])
prof_ppm = (nivel - np.median(fluxo[dentro])) * 1e6
ruido_ppm = np.std(fluxo[fora]) * 1e6

R_estrela = lc.meta["RADIUS"]                        # R_sol
Rp = np.sqrt(prof_ppm / 1e6) * R_estrela * 109.1     # R_terra
print(f"profundidade = {prof_ppm:.0f} ppm, ruído por ponto = {ruido_ppm:.0f} ppm")
print(f"raio do planeta = {Rp:.1f} R_terra")

ax = dobrada.scatter(alpha=0.3)
dobrada.bin(time_bin_size=10 / (60 * 24)).plot(ax=ax, color="C3", lw=2)
ax.set_xlim(-0.2, 0.2)
plt.show()
```

Saída:

```text
profundidade = 10830 ppm, ruído por ponto = 613 ppm
raio do planeta = 15.3 R_terra
```

Medimos só o **miolo** do trânsito (metade central da duração) para fugir das bordas inclinadas, a entrada e a saída do planeta. O raio vem da regra da aula B2, a mesma função `raio_planeta` da [aula P1](p1-python-basics.md).

### Comparando com o PlanetHunter e o ExoFOP

| Fonte | Período (d) | Profundidade (ppm) | Raio (R⊕) |
|---|---|---|---|
| Você, com BLS | 0,94130 | 10 830 | 15,3 |
| PlanetHunter, setor 69 (TLS) | 0,941592 | 10 583 | 15,1 |
| ExoFOP, TOI-185.01 (vários setores) | 0,941453 | 11 445 | 15,3 |

Os números concordam em poucos por cento. As diferenças vêm do método (caixa no BLS, modelo realista de trânsito no TLS), de quantos setores entraram e de onde se mede o "fundo". Estudos dedicados, que modelam o escurecimento de borda (aula M2), encontram um raio um pouco menor, cerca de 1,2 raio de Júpiter. A conta $\delta \approx (R_p/R_\star)^2$ é uma aproximação: o centro da estrela é mais brilhante que a borda, então o miolo do trânsito fica um pouco mais fundo que $(R_p/R_\star)^2$.

!!! tip "Na ferramenta"
    O PlanetHunter faz as mesmas etapas com outras ferramentas: limpeza em `src/planethunter/preprocess/clean.py`, detrending com o filtro biweight da biblioteca wotan (janela de 1 dia, em vez do filtro do Lightkurve) e busca com TLS em `src/planethunter/search/tls.py`, em vez de BLS. Para WASP-18 b no setor 69 ele registrou SDE 36,1, SNR 473,8 e 21 trânsitos com dados. O dossiê mostra o mesmo "trânsito dobrado" que você acabou de desenhar.

!!! question "Para pensar"
    Repita as seções 2 a 5 com `busca.download_all().stitch()`, que baixa e junta todos os setores da busca. Com trânsitos espalhados por anos, o que acontece com a precisão do período? E com o tempo de cálculo do BLS? Dica: com anos de dados, a grade de 20 000 períodos entre 0,5 e 10 dias fica grossa demais e erra o pico; use uma grade fina em volta do valor conhecido, como `np.linspace(0.94, 0.943, 20000)`.

## 6. Ler o Parquet salvo pelo PlanetHunter

Quando o PlanetHunter baixa uma curva, ele a converte para **Parquet**, um formato de tabela compacto e rápido. O caminho segue um padrão:

```text
data/parquet/sector=0069/author=SPOC/tic_0000000100100827.parquet
```

O setor tem 4 dígitos e o TIC tem 16, completados com zeros. Para ter esse arquivo, rode na pasta do PlanetHunter `uv run planethunter ingest target 100100827 --sectors 69` (veja o [laboratório](../lab/using-planethunter.md)).

```python
import json
from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(r"C:\Users\voce\planethunter")       # ajuste para a sua pasta
arq = RAIZ / "data" / "parquet" / "sector=0069" / "author=SPOC" / f"tic_{100100827:016d}.parquet"

tabela = pq.read_table(arq)
df = tabela.to_pandas()
print(df.dtypes)
print(len(df))                                    # 18098 linhas

meta = json.loads(tabela.schema.metadata[b"planethunter"])
print(meta["sector"], meta["camera"], meta["procver"])
print(meta["star"]["radius_rsun"], meta["star"]["tmag"])
```

As colunas:

| Coluna | Conteúdo | Tipo |
|---|---|---|
| `time` | Tempo em BTJD | float64 |
| `flux`, `flux_err` | Brilho corrigido (PDCSAP) e erro, em e⁻/s | float32 |
| `sap_flux` | Brilho sem a correção do SPOC | float32 |
| `quality` | Sinalizadores de problema (0 = tudo certo) | int32 |
| `cadenceno` | Número da medida | int64 |
| `mom_centr1`, `mom_centr2` | Posição da luz no detector, em pixels | float32 |

Os **metadados** ficam no cabeçalho do arquivo, como texto JSON na chave `b"planethunter"`: setor, câmera, versão do processamento (`procver`), soma de verificação do arquivo original e os parâmetros da estrela. O `b` antes das aspas indica bytes em vez de texto, exigência do formato.

O arquivo guarda **todas** as medidas, inclusive as ruins. Filtre e transforme em LightCurve:

```python
from astropy.time import Time

bons = df[(df["quality"] == 0) & np.isfinite(df["flux"])]
print(len(bons))                                  # 14665, igual ao download
lc_ph = lk.LightCurve(
    time=Time(bons["time"].to_numpy(), format="btjd", scale="tdb"),
    flux=bons["flux"].to_numpy(),
    flux_err=bons["flux_err"].to_numpy(),
).normalize()
```

Daqui em diante, `lc_ph` aceita `flatten`, `fold` e `to_periodogram` como antes.

## 7. Consultar o banco DuckDB

O PlanetHunter guarda resultados em `data/planethunter.duckdb`, um banco de dados num único arquivo. Você faz perguntas a ele em **SQL**, a linguagem padrão de bancos de dados. Para ter WASP-18 b no seu banco, rode na pasta do PlanetHunter `uv run planethunter run-target 100100827 --sectors 69` e depois `uv run planethunter vet <run_id>`, com o `run_id` que o primeiro comando imprimir. As tabelas principais:

| Tabela | Uma linha por | Colunas úteis |
|---|---|---|
| `signals` | sinal achado na busca | `signal_id`, `run_id`, `tic_id`, `period_days`, `depth_ppm`, `sde`, `snr`, `n_transits` |
| `crossmatch` | sinal comparado aos catálogos | `match_class`, `matched_name`, `host_known` |
| `vetting` | sinal testado | `score`, `verdict`, `vetoed_by`, `failed`, `p_planet` |
| `candidates` | candidato na fila | `severity`, `review_status` |

```python
import duckdb

con = duckdb.connect(str(RAIZ / "data" / "planethunter.duckdb"), read_only=True)

print(con.sql("""
    SELECT signal_id, run_id, period_days, depth_ppm, sde, snr, n_transits
    FROM signals
    WHERE tic_id = 100100827
    ORDER BY signal_id
""").df())

print(con.sql("""
    SELECT s.signal_id, s.period_days, c.match_class, c.matched_name,
           v.verdict, v.score, v.failed
    FROM signals s
    JOIN crossmatch c USING (signal_id)
    LEFT JOIN vetting v USING (signal_id)
    WHERE s.tic_id = 100100827
""").df())

print(con.sql("""
    SELECT match_class, count(*) AS n
    FROM crossmatch GROUP BY match_class ORDER BY n DESC
""").df())
con.close()
```

Leia o SQL como uma frase: "selecione (`SELECT`) estas colunas da tabela (`FROM`) onde (`WHERE`) a condição vale, em ordem de (`ORDER BY`)". O `JOIN ... USING (signal_id)` junta duas tabelas pelas linhas que têm o mesmo `signal_id`. O `.df()` devolve um DataFrame do pandas.

No banco do projeto, em 9/10/2026, a fatia de 2 164 estrelas do setor 69 (run `20261009T204130Z-single-s69`) registrou WASP-18 b como o sinal 2020: `KNOWN_PLANET`, casado com TOI-185.01. O vetting básico deu `FAIL`, score 0,2, com falhas em `secondary` e `consistency`. O vetting não é perfeito: ele aprova cerca de 81 % dos planetas confirmados do setor 69. Isso não causa alerta falso, porque um `KNOWN_PLANET` nunca vira candidato.

!!! warning "Banco em uso"
    Abra sempre com `read_only=True` e feche com `con.close()`. Se um comando do PlanetHunter estiver rodando, o DuckDB pode recusar a conexão com um erro de "lock". Espere o comando terminar.

## Exercícios

!!! example "Exercício 1. Ímpares e pares"
    Uma binária eclipsante com o dobro do período mostra eclipses alternados de profundidades diferentes (aula B4). Meça a profundidade dos trânsitos ímpares e pares de WASP-18 b.

    ??? success "Ver resposta"
        ```python
        t = np.asarray(plana.time.value, dtype=float)
        f = np.asarray(plana.flux.value, dtype=float)
        n = np.round((t - T0) / P).astype(int)          # número de cada trânsito
        miolo = np.abs(t - (T0 + n * P)) < 0.25 * D
        impar = (1 - np.median(f[miolo & (n % 2 == 1)])) * 1e6
        par = (1 - np.median(f[miolo & (n % 2 == 0)])) * 1e6
        print(f"ímpares {impar:.0f} ppm, pares {par:.0f} ppm")
        ```
        Resultado: cerca de 10 770 ppm nos ímpares e 10 880 nos pares, diferença de 1 %. Para uma binária com período dobrado, a diferença costuma ser grande. É o que o teste `odd_even` do vetting mede, com barras de erro.

!!! example "Exercício 2. Olhar a fase 0,5"
    WASP-18 b é tão quente que o TESS vê a luz do próprio planeta sumir quando ele passa atrás da estrela. Meça o brilho em fase 0,5 (meio caminho entre trânsitos). Compare com a regra do PlanetHunter: o teste `secondary` só veta se a queda secundária for de pelo menos 10 % da principal.

    ??? success "Ver resposta"
        ```python
        sec = np.abs(np.abs(fase) - 0.5 * P) < 0.25 * D
        prof_sec = (nivel - np.median(fluxo[sec])) * 1e6
        print(f"fase 0,5: {prof_sec:.0f} ppm = {100 * prof_sec / prof_ppm:.1f} % da principal")
        ```
        Dá cerca de 310 ppm, perto de 3 % da principal. A calibração do vetting do projeto (setor 69) registra cerca de 340 ppm para essa ocultação. Parte do valor pode vir da variação de brilho ao longo da órbita, que a janela de 30 horas não remove por completo. Como 3 % fica abaixo de 10 %, a regra não veta. O teste ainda registra uma falha leve, que reduz o score: é por isso que o sinal 2020 aparece com `secondary` na coluna `failed`. Antes dessa regra, o sistema vetava WASP-18 b como binária (guia, seção 5).

!!! example "Exercício 3. Contar candidatos"
    Escreva uma consulta SQL que conte os candidatos por severidade e por estado de revisão.

    ??? success "Ver resposta"
        ```python
        con = duckdb.connect(str(RAIZ / "data" / "planethunter.duckdb"), read_only=True)
        print(con.sql("""
            SELECT severity, review_status, count(*) AS n
            FROM candidates
            GROUP BY severity, review_status
            ORDER BY severity
        """).df())
        con.close()
        ```
        `GROUP BY` com duas colunas cria um grupo para cada combinação. No banco do projeto, em 9/10/2026: 13 P1 pendentes, 49 P2 pendentes, 2 P2 rejeitados e 1 P2 em `follow_up`. O seu banco terá outros números. P1 e P2 não são planetas: são sinais que esperam revisão humana.

## Checklist da aula

- [ ] Busquei e baixei a curva do setor 69 de WASP-18
- [ ] Limpei a curva, cortando só pontos altos
- [ ] Achei o período com BLS em duas passadas, com máscara nos trânsitos
- [ ] Dobrei a curva, medi a profundidade e estimei o raio
- [ ] Comparei meus números com o PlanetHunter e o ExoFOP
- [ ] Li um Parquet do PlanetHunter e os metadados da chave `b"planethunter"`
- [ ] Consultei `signals`, `crossmatch`, `vetting` e `candidates` com SQL
- [ ] Resolvi os três exercícios

## Para ir além

- Tutoriais do Lightkurve ([lightkurve.github.io](https://lightkurve.github.io/lightkurve/tutorials/index.html)), em especial "Identifying transiting exoplanet signals". O roteiro desta aula segue o mesmo caminho, com mais detalhes sobre cada função.
- Documentação da Astropy sobre Box Least Squares ([docs.astropy.org](https://docs.astropy.org/en/stable/timeseries/bls.html)). O BLS do Lightkurve chama essa implementação por baixo.
- Página de WASP-18 b no NASA Exoplanet Archive ([exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu/overview/WASP-18%20b)). Reúne os parâmetros publicados para comparar com a sua medida.
