# M4. Dados do TESS em Python

<p class="meta">Nível médio · semanas 6–8 · cerca de 12 horas</p>

!!! abstract "Nesta aula você vai aprender"
    - Buscar e baixar a curva de luz de uma estrela do TESS com a biblioteca Lightkurve.
    - Plotar, limpar e achatar (flatten) a curva.
    - Rodar um periodograma BLS e reconhecer o pico verdadeiro e os aliases.
    - Dobrar (fold) a curva no período encontrado e ver o trânsito.
    - Fazer à mão três testes de vetting: ímpar/par, fase 0,5 e busca de um segundo sinal.
    - Comparar seu resultado com o do PlanetHunter para o mesmo alvo.

!!! warning "Pré-requisito: trilha de programação"
    Esta aula assume que você terminou [P1. Python básico](../programming/p1-python-basics.md) e [P2. NumPy, pandas e Matplotlib](../programming/p2-numpy-pandas-matplotlib.md). Você precisa saber o que é um array do NumPy, chamar funções com argumentos nomeados e fazer um gráfico simples. A aula [P3. Lightkurve na prática](../programming/p3-lightkurve-in-practice.md) complementa esta, com mais detalhes da biblioteca.

## O alvo: Pi Mensae c

**Pi Mensae** (TIC 261136679) é uma estrela parecida com o Sol, muito brilhante (Tmag 5,1), no céu do hemisfério sul. Seu planeta **Pi Men c** foi um dos primeiros anunciados com dados do TESS, em 2018: período de cerca de **6,27 dias** e trânsitos de cerca de **300 ppm**, pouco mais de 2 raios terrestres.

É um alvo ideal para começar: o sinal é real e conhecido, mas não é óbvio a olho nu na curva bruta. Você vai precisar de cada passo da busca para enxergá-lo. Vamos usar só o **setor 1**, o primeiro do TESS (julho e agosto de 2018).

## Preparação

O Lightkurve já vem instalado com o PlanetHunter. Na pasta do projeto, crie um arquivo `pimen.py` (fora de `src/`, por exemplo numa pasta `estudos/` sua) e rode cada bloco com:

```bash
uv run python pimen.py
```

Se preferir Jupyter, cole os blocos em células, na ordem. Os gráficos aparecem sozinhos; num script, use `plt.show()` no fim de cada gráfico, como no código abaixo.

O primeiro download precisa de internet e leva alguns segundos. O Lightkurve guarda os arquivos num cache local e não baixa de novo.

## Passo 1. Buscar

```python
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
import lightkurve as lk

# Busca no arquivo MAST todas as curvas de luz SPOC de 2 minutos (120 s) desta estrela.
busca_todas = lk.search_lightcurve(
    "TIC 261136679", mission="TESS", author="SPOC", exptime=120
)
print(busca_todas)  # uma linha por setor

# Agora só o setor 1.
busca = lk.search_lightcurve(
    "TIC 261136679", mission="TESS", author="SPOC", exptime=120, sector=1
)
print(busca)
```

**O que você deve ver.** A primeira tabela tem mais de vinte linhas: Pi Mensae fica perto do polo sul da eclíptica e foi observada em muitos setores entre 2018 e 2025. Cada linha tem missão e setor, ano, autor (SPOC), tempo de exposição (120 s) e o nome do alvo. A segunda tabela tem uma linha só: `TESS Sector 01 2018 SPOC 120 261136679`.

!!! note "Por que SPOC de 2 minutos"
    SPOC é o pipeline oficial da missão, que produz curvas para alvos pré-selecionados com cadência de 2 minutos. É o mesmo tipo de dado que o PlanetHunter ingere por padrão. A curva já vem corrigida de efeitos do telescópio (coluna PDCSAP) e de contaminação por vizinhas.

## Passo 2. Baixar e inspecionar

```python
lc = busca.download()  # objeto TessLightCurve

# Metadados do cabeçalho: brilho, temperatura e raio da estrela (do TIC).
print(lc.meta["OBJECT"], "setor", lc.meta["SECTOR"])
print("Tmag", lc.meta["TESSMAG"], "Teff", lc.meta["TEFF"], "R*", lc.meta["RADIUS"])
print("colunas:", lc.colnames[:8])
print(len(lc), "pontos, de", lc.time.min(), "a", lc.time.max())
```

**O que você deve ver.** `TIC 261136679 setor 1`, Tmag 5,105, Teff cerca de 5 990 K, raio 1,149 R☉. Cerca de 18 264 pontos, de BTJD 1325,30 a 1353,18. BTJD é o tempo do TESS: dias desde uma data de referência.

Por padrão, o Lightkurve usa a coluna `pdcsap_flux` como `flux` e já descarta as cadências marcadas como ruins pelo telescópio (máscara de qualidade "default", a mesma do PlanetHunter).

## Passo 3. Plotar a curva bruta

```python
lc = lc.remove_nans().normalize()  # tira pontos vazios e divide pela mediana (brilho normal = 1)
ax = lc.plot()
ax.set_title("Pi Mensae, setor 1, curva normalizada")
plt.show()
```

**O que você deve ver.**

- Uma faixa de pontos entre cerca de 0,9997 e 1,0003, ou seja, ±300 ppm.
- Uma **lacuna** perto de BTJD 1339: a pausa para envio de dados à Terra, entre as duas órbitas do setor.
- Um trecho mais ruidoso perto de BTJD 1347 a 1349.
- Os trânsitos estão lá, mas mal se distinguem do ruído. Se olhar com atenção, perto de 1325,5, 1331,8, 1338,0, 1344,3 e 1350,6 há quedas discretas. Sem saber onde olhar, você não as acharia.

É a situação típica: o sinal está abaixo do ruído de cada ponto. É a estatística da aula [M1](m1-statistics-for-signals.md) que vai revelá-lo.

## Passo 4. Limpar e achatar

```python
# Remove só pontos discrepantes PARA CIMA (flares). Nunca para baixo: apagaria trânsitos.
limpa = lc.remove_outliers(sigma_upper=4, sigma_lower=np.inf)

# Achata: estima a tendência lenta e divide por ela.
# window_length é em número de pontos e precisa ser ímpar: 721 x 2 min = 1 dia.
plana, tendencia = limpa.flatten(window_length=721, return_trend=True)

ax = limpa.plot(label="limpa")
tendencia.plot(ax=ax, color="red", label="tendência")
plt.show()

ruido_ppm = np.std(plana.flux.value) * 1e6
print(f"{len(limpa)} pontos; ruído por ponto: {ruido_ppm:.0f} ppm")
```

**O que você deve ver.** Uns 9 pontos removidos (18 255 restantes). A tendência vermelha é quase reta: Pi Mensae é uma estrela calma. O ruído por ponto fica em cerca de **128 ppm** (o sigma robusto, via MAD, dá cerca de 120 ppm).

!!! info "Mesma ideia, filtro diferente"
    O `flatten` do Lightkurve usa um filtro de Savitzky-Golay. O PlanetHunter usa o **biweight** do wotan, que é mais robusto a trânsitos dentro da janela. Os dois usam janela de 1 dia aqui, pelas razões da aula [M3](m3-periodograms.md): menos que isso come trânsitos longos.

## Passo 5. Periodograma BLS

```python
periodos = np.linspace(1, 15, 20000)            # dias
duracoes = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]  # dias (1,2 h a 4,8 h)
bls = plana.to_periodogram(method="bls", period=periodos, duration=duracoes)

bls.plot()
plt.show()

P = bls.period_at_max_power
t0 = bls.transit_time_at_max_power  # objeto Time; .value dá o número em BTJD
dur = bls.duration_at_max_power
prof = bls.depth_at_max_power
print(f"P = {P:.4f}, t0 = {t0.value:.3f}, duração = {dur:.2f}, profundidade = {prof.value * 1e6:.0f} ppm")

# Destaque do pico, no espírito do SDE: quantos desvios padrão acima da média.
destaque = (bls.max_power - np.mean(bls.power)) / np.std(bls.power)
print(f"destaque do pico: {destaque:.1f}")
```

**O que você deve ver.**

- Um pico dominante em **6,27 d**, com potência perto de 1 400.
- Picos menores, os **aliases**: 12,53 d (2P, potência ~860), 3,13 d (P/2, ~750) e outros em 9,4 d (3P/2), 4,18 d (2P/3) e 2,09 d (P/3).
- Saída: `P = 6.2664 d, t0 = 1325.507, duração = 0.12 d, profundidade = 228 ppm`.
- Destaque do pico: cerca de **12,9**.

A duração de 0,12 d (2,9 h) é o valor mais próximo na **grade** que você deu. Com uma grade mais fina, o resultado mudaria um pouco. O destaque não é o SDE do TLS (as definições de potência diferem), mas a ideia é a mesma.

## Passo 6. Dobrar e ver o trânsito

```python
dobrada = plana.fold(period=P, epoch_time=t0)  # tempo vira "dias desde o trânsito"

ax = dobrada.scatter(alpha=0.3, s=2, label="pontos de 2 min")
dobrada.bin(time_bin_size=10 * u.min).scatter(ax=ax, color="red", s=20, label="média a cada 10 min")
ax.set_xlim(-0.3, 0.3)
plt.show()
```

**O que você deve ver.** Uma nuvem cinza larga e, por cima, os pontos vermelhos formando um **U** claro: um degrau de cerca de 250 ppm entre −0,06 e +0,06 dia. Os cinco trânsitos, invisíveis um a um, somados viram um sinal nítido. É o $\sqrt{N}$ da aula M1 em ação.

Compare o formato com a aula [M2](m2-transit-physics.md): rampas curtas e fundo largo. Nada de V.

## Passo 7. Três testes de vetting à mão

```python
stats = bls.compute_stats(period=P, duration=dur, transit_time=t0)
print("trânsitos:", stats["transit_times"])
print("pontos por trânsito:", stats["per_transit_count"])
print("ímpar:", stats["depth_odd"], "par:", stats["depth_even"])
print("em fase 0,5:", stats["depth_phased"])
print("se o período fosse P/2:", stats["depth_half"])

# Busca de um segundo sinal: mascara os trânsitos e roda o BLS de novo.
mascara = bls.get_transit_mask(period=P, transit_time=t0, duration=2 * dur)
resto = plana[~mascara]
bls2 = resto.to_periodogram(method="bls", period=periodos, duration=duracoes)
destaque2 = (bls2.max_power - np.mean(bls2.power)) / np.std(bls2.power)
print(f"2º sinal: P = {bls2.period_at_max_power:.3f}, "
      f"{bls2.depth_at_max_power.value * 1e6:.0f} ppm, destaque {destaque2:.1f}")
```

**O que você deve ver.** As profundidades saem como pares (valor, erro) em fração do brilho: `0.00022391` quer dizer 224 ppm.

- Cinco trânsitos (1325,51; 1331,77; 1338,04; 1344,31; 1350,57), com 81 a 87 pontos cada.
- Ímpar: 224 ± 7 ppm. Par: 231 ± 6 ppm. **Iguais dentro do erro.**
- Fase 0,5: −10 ± 5 ppm. **Nenhum eclipse secundário.**
- Profundidade com P/2: 126 ppm, a metade, como previsto para um alias (aula M3).
- Segundo sinal: algo perto de 7 d com 37 ppm e destaque de cerca de 4. **Nada.** Só um planeta transita no setor 1.

Você acabou de fazer, com suas mãos, os testes `odd_even`, `secondary` e a busca iterativa do PlanetHunter.

!!! example "Exercício 1"
    Calcule a significância da diferença ímpar/par, em sigmas, como o teste `odd_even` faz. Ela reprovaria?

    ??? success "Ver resposta"
        Diferença: 231 − 224 = 7 ppm. Erro combinado: $\sqrt{7^2 + 6^2} = \sqrt{85} \approx 9{,}2$ ppm. Significância: 7/9,2 ≈ **0,8 sigma**.

        O teste reprova a partir de 3 sigma e veta a partir de 5. Passa com folga. Os trânsitos ímpares e pares são iguais, como se espera de um planeta.

!!! example "Exercício 2"
    Use a profundidade e o raio da estrela para estimar o raio de Pi Men c em raios terrestres. Faça a conta duas vezes: com a profundidade do BLS (228 ppm) e com a do trapézio do PlanetHunter (272 ppm). Dado: 1 R☉ = 109,1 R⊕.

    ??? success "Ver resposta"
        $R_p = \sqrt{\delta} \times R_\star \times 109{,}1$.

        Com 228 ppm: $\sqrt{0{,}000228} = 0{,}0151$. $0{,}0151 \times 1{,}149 \times 109{,}1 \approx$ **1,9 R⊕**.

        Com 272 ppm: $\sqrt{0{,}000272} = 0{,}0165$. $0{,}0165 \times 1{,}149 \times 109{,}1 \approx$ **2,1 R⊕**, o valor que aparece no teste `radius` do PlanetHunter.

        A diferença vem do modelo: a caixa faz a média com as rampas e subestima a profundidade (aula M2). Um erro de 20 % na profundidade vira 10 % no raio, porque o raio vai com a raiz.

## Passo 8. Comparar com o PlanetHunter

Agora rode o mesmo alvo na ferramenta, só com o setor 1:

```bash
uv run planethunter run-target 261136679 --sectors 1
```

O comando baixa o setor, roda a busca (TLS com as variantes de detrending), o crossmatch e o vetting básico, e imprime o `run_id`, uma tabela de sinais com o `signal_id` e o caminho do dossiê de cada sinal forte. Com os espelhos de catálogos atualizados, o sinal de 6,27 d deve aparecer como `KNOWN_PLANET`, casado com Pi Men c. Se aparecer um aviso de espelhos velhos, rode antes `uv run planethunter mirrors sync`.

!!! warning "Não esqueça o `--sectors 1`"
    Sem ele, o comando baixa **todos** os setores da estrela (mais de vinte) e faz uma busca multissetor. Demora muito mais e os números mudam (mais trânsitos, SNR maior). Atenção: setores que você já baixou antes entram na busca mesmo com `--sectors 1`.

As últimas linhas da saída mostram o dossiê de cada sinal forte, por exemplo `dossier for signal 1234: data/dossiers/tic261136679_sig1234.html`. Abra no navegador. Para gerar de novo depois, use `uv run planethunter dossier <signal_id>`.

### O que esperar

Rodamos o código de busca e de vetting do PlanetHunter sobre o setor 1 de Pi Mensae em 2026-10-09. A tabela compara com o que você obteve nesta aula:

| | Lightkurve (esta aula) | PlanetHunter |
|---|---|---|
| Limpeza | NaN e pontos 4σ acima | máscara de qualidade, 4σ acima antes e depois do achatamento |
| Achatamento | Savitzky-Golay, 1 d | biweight (wotan), 1,0 d, segmentos separados nas lacunas |
| Busca | BLS, 1 a 15 d, 6 durações | TLS, 0,5 a ~25 d (0,9 × duração dos dados), grade fina, pontos agrupados em 10 min |
| Período | 6,266 d | 6,269 d |
| Instante do 1º trânsito (BTJD) | 1325,507 | 1325,503 |
| Duração | 2,9 h (valor da grade) | 3,08 h (TLS); 3,11 h (trapézio) |
| Profundidade | 228 ppm (caixa) | 287 ppm (TLS); 272 ppm (trapézio) |
| Força do pico | destaque 12,9 | SDE 19,0 |
| SNR | ~37 (conta da aula M1) | 33,6 |
| Trânsitos | 5 | 5 |
| Ímpar / par | 224 / 231 ppm | 284 / 259 ppm (1,1σ) |
| Fase 0,5 | −10 ppm | −9 ppm |

O vetting básico completo do PlanetHunter deu **score 1,0, PASS_BASIC**: raio 2,1 R⊕; duração 3,11 h contra 3,79 h prevista (razão 0,82, aula M2); $\tau/T_{14}$ = 0,11 (forma em U); centróide com fonte implícita a 0,15 pixel do alvo; 40 % dos trânsitos em bordas de segmento (2 de 5, abaixo do limite de 50 %); consistência entre trânsitos com p = 0,62.

Os números do seu dossiê podem diferir um pouco, se a versão do pipeline ou os parâmetros do TIC mudarem. Desde 2026-10-10, a busca também cobre outra faixa de períodos (a partir de cerca de 0,2–0,3 d; antes, o padrão do próprio TLS a fazia parar, na prática, na metade do intervalo de dados, cerca de 14 d aqui), e o PlanetHunter mede a duração e o SNR por conta própria em vez de copiá-los do TLS (aula [M3](m3-periodograms.md)), então essas duas linhas vão mudar um pouco numa nova execução. A seção **Provenance** (proveniência) do dossiê registra o `run_id`, a versão e a janela usada em cada setor.

!!! tip "Na ferramenta"
    Cada passo desta aula tem um equivalente no código: limpeza e achatamento em `src/planethunter/preprocess/clean.py`; busca em `src/planethunter/search/tls.py`; ímpar/par, fase 0,5, forma e os demais testes em `src/planethunter/vetting/basic.py`. No dossiê, o gráfico **"Folded transit"** (trânsito dobrado) corresponde ao seu passo 6, e o painel **"Odd, even and secondary"** ao passo 7.

!!! example "Exercício 3"
    Na tabela, o PlanetHunter tem SDE 19,0 e o seu "destaque" deu 12,9. Cite duas razões para a diferença.

    ??? success "Ver resposta"
        1. **Modelo.** O TLS usa um trânsito realista, com rampas e escurecimento de borda; o BLS usa caixa. O modelo melhor ajusta mais do sinal e o pico cresce.
        2. **Definição e grade.** O SDE do TLS é calculado sobre outra grandeza (o SR, normalizado) e sobre outra grade de períodos (de 0,5 a ~25 d, com densidade escolhida pelo `oversampling_factor`). O seu destaque usa a potência do BLS em 1 a 15 d. Média e desvio padrão do periodograma mudam com a grade.

        Também contam detalhes de limpeza (filtro biweight, segmentos separados nas lacunas) e o agrupamento em 10 minutos. Os dois números não são comparáveis diretamente; o que importa é que os dois métodos acham o mesmo período, com folga.

!!! example "Exercício 4 (desafio)"
    Escolha outro setor da lista do passo 1 e repita a aula inteira trocando `sector=1`. O período e a profundidade batem? Quantos trânsitos você vê?

    ??? success "Ver resposta"
        O período deve bater com 6,27 d dentro da incerteza (que, com um setor só, é de alguns milésimos de dia), e a profundidade com o setor 1 dentro de algumas dezenas de ppm. O número de trânsitos depende de onde caem as lacunas daquele setor: com ~27 dias e período de 6,27 d, espere 4 ou 5. Se algum setor der um resultado muito diferente, olhe a curva: lacunas maiores, trechos ruidosos ou um trânsito na borda explicam a maioria dos casos. É o mesmo raciocínio do teste de outros setores do vetting aprofundado.

## Checklist da aula

- [ ] Busquei e baixei a curva do setor 1 de Pi Mensae com Lightkurve.
- [ ] Plotei a curva bruta e localizei a lacuna do meio do setor.
- [ ] Limpei só para cima e achatei com janela de 1 dia, sabendo por quê.
- [ ] Rodei o BLS e encontrei 6,27 d; identifiquei pelo menos dois aliases no periodograma.
- [ ] Dobrei a curva e vi o trânsito em U.
- [ ] Fiz à mão os testes ímpar/par, fase 0,5 e a busca de um segundo sinal.
- [ ] Rodei `planethunter run-target 261136679 --sectors 1`, abri o dossiê gerado e comparei com a tabela desta aula.

## Para ir além

- Tutoriais oficiais do Lightkurve ([lightkurve.github.io](https://lightkurve.github.io/lightkurve/)): comece por "LightCurve objects" e depois pelo tutorial de identificação de sinais de trânsito com BLS.
- Página de Pi Mensae no ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/target.php?id=261136679)): parâmetros da estrela, TOIs e notas da comunidade.
- Huang et al. (2018), *The Astrophysical Journal Letters* 868, L39: o artigo do anúncio de Pi Men c com dados do TESS. Veja as figuras e compare com o seu trânsito dobrado.
- Documentação introdutória do NumPy ([numpy.org](https://numpy.org/doc/stable/user/absolute_beginners.html)) e do pandas ([pandas.pydata.org](https://pandas.pydata.org/docs/getting_started/index.html)), se algum trecho do código pareceu estranho.
