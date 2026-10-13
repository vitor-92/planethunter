# Usando o PlanetHunter

<p class="meta">Laboratório · a partir da aula B5 · consulta permanente</p>

!!! abstract "Nesta página você vai aprender"
    - Instalar o PlanetHunter e conferir que ele funciona.
    - O que faz cada comando, quando usar e o que ele imprime.
    - Rodar seu primeiro setor do TESS, em escala pequena, do download ao alerta simulado.
    - Onde ficam os arquivos e como configurar alertas no Telegram com segurança.

Este é o manual de bolso da ferramenta. Ele usa o vocabulário das aulas: **sinal** (queda periódica achada na busca), **candidato** (sinal novo que passou no vetting), **dossiê** (relatório HTML de um sinal). Se um termo parecer estranho, consulte o [glossário](../glossary.md).

## Instalação

Você precisa do **uv** e do **Git**. Se ainda não instalou, siga o passo a passo da [trilha de programação](../programming/index.md). Abra o PowerShell (no VS Code: **Terminal > New Terminal**) e rode:

```powershell
cd ~
git clone https://github.com/vitor-92/planethunter.git planethunter
cd planethunter
uv sync
```

Se você recebeu a pasta do projeto de outra forma, basta entrar nela com `cd` e rodar `uv sync`.

`uv sync` lê o arquivo `pyproject.toml`, baixa o Python 3.12 se faltar e instala todas as bibliotecas numa pasta `.venv` dentro do projeto. Leva alguns minutos na primeira vez.

O cálculo de **FPP** (probabilidade de falso positivo, aula A3) usa a biblioteca triceratops, que exige versões antigas do NumPy. Por isso ela mora num ambiente separado:

```powershell
cd tools\fpp
uv sync
cd ..\..
```

Confira a instalação:

```powershell
uv run planethunter --help
uv run pytest
```

O primeiro mostra a lista de comandos. O segundo roda os testes automáticos, sem internet, em cerca de 45 segundos. Tudo verde: pronto.

!!! note "Sempre `uv run` na frente"
    `uv run planethunter ...` garante que o comando usa o Python e as bibliotecas do projeto. Rode sempre de dentro da pasta `planethunter`. Qualquer comando aceita `--help`, por exemplo `uv run planethunter search --help`.

## Mapa dos comandos

O pipeline tem 8 passos (guia, seção 1). Cada comando cobre um ou mais deles.

| Comando | Passo | Usa internet? | Quando usar |
|---|---|---|---|
| `mirrors sync` / `mirrors status` | 0. Espelhos | sync: sim | Antes de qualquer crossmatch; status quando quiser conferir |
| `ingest sector` / `ingest target` | 1. Ingestão | sim | Baixar curvas de luz |
| `search` | 2 e 3. Limpeza e busca | não | Procurar sinais nas curvas já baixadas |
| `crossmatch` | 4. "Já existe?" | não | Depois de `search` |
| `vet` | 5. Vetting básico | não | Depois de `crossmatch` |
| `vet-deep` | 6. Vetting aprofundado | sim | Para os candidatos que passaram em `vet` |
| `calibrate` | 5 (modelo) | não | Treinar a probabilidade calibrada de planeta com sinais conhecidos |
| `candidates` | 7 | não | Ver a fila de candidatos |
| `dossier` | 7 | não | Gerar o relatório de um sinal |
| `alert` | 7 | só com `--send` | Gerar dossiês e alertar P0/P1 |
| `review` | depois do 7 | não | Registrar sua decisão sobre um candidato |
| `run-target` | 1 a 4 | sim | Estudar uma estrela só, ponta a ponta |
| `run-sector` | 0 a 7 | sim | Rodar tudo num setor |
| `benchmark build` / `benchmark run` | medição | sim | Medir o recall antes e depois de mudar algo |

A regra do projeto é: **nada de internet no caminho crítico da busca**. Os comandos `search`, `crossmatch` e `vet` trabalham só com cópias locais.

## Cada comando

### `mirrors sync` e `mirrors status`

```powershell
uv run planethunter mirrors sync
uv run planethunter mirrors status
```

`sync` baixa 12 listas de objetos conhecidos: NASA Exoplanet Archive, TOIs e CTOIs do ExoFOP, exoplanet.eu, a tabela de KOIs do Kepler, os planetas e candidatos do K2, dois catálogos de binárias eclipsantes do TESS (Prša et al. 2022 e Kostov et al. 2025) e quatro listas publicadas de candidatos (DIAmante, DTARPS, LEO-Vetter e ExoMiner++). As tabelas publicadas nunca mudam, então o `sync` as pula quando já estão no disco (`--force` baixa de novo). O exoplanet.eu leva alguns minutos. `status` mostra, para cada cópia, o estado, o limite de idade, a idade, o número de linhas, o começo do checksum e o arquivo:

```text
archive_pscomppars   ok         <48 h age=   4.1 h rows=   6445 sha256=0833b7792d0f 20261009T193948Z.parquet
exoplanet_eu         ok        <168 h age=   4.1 h rows=   8354 sha256=a39d6af4196b 20261010T054524Z.parquet
toi                  ok         <48 h age=   4.1 h rows=   8151 sha256=fd7a3f98832d 20261009T193908Z.parquet
ctoi                 ok         <48 h age=   4.1 h rows=   5138 sha256=5a5e207dec9a 20261010T055318Z.parquet
eb_catalog           ok        static age=   3.9 h rows=   4584 sha256=d839230f8fce 20261009T194915Z.parquet
koi_cumulative       ok        <720 h age=   4.1 h rows=   9564 sha256=f9e3f26e63bc 20261010T054440Z.parquet
...
```

Na saída, `age` é a idade e `rows` o número de linhas. Cada fonte tem o seu próprio limite: 48 horas para as listas que mudam todo dia (TOI, CTOI, o Archive), 7 dias (168 h) para o exoplanet.eu e o K2, 30 dias (720 h) para os KOIs; tabelas `static` (estáticas) nunca expiram. `STALE` (velho) quer dizer mais velho que o limite. `MISSING` (ausente), que a cópia não existe. `VERSION` (versão), que a cópia no disco foi feita por uma versão mais antiga do código e precisa ser sincronizada de novo. Nos três casos, nenhum sinal pode ser classificado como `NEW`: ele vira `UNVERIFIED` e não gera alerta, e o comando termina com código de erro.

### `ingest sector` e `ingest target`

```powershell
uv run planethunter ingest sector 69 --limit 200
uv run planethunter ingest sector 69 --tics 100100827,261136679
uv run planethunter ingest target 261136679 --sectors 1,4,8
```

`ingest sector` baixa as curvas SPOC de 2 minutos de um setor. Opções: `--limit N` (só os N primeiros alvos, para testes), `--tics` (lista de TICs separados por vírgula, sem espaços) e `--workers` (downloads simultâneos, padrão 8; seja gentil com o MAST). `ingest target` baixa todos os setores de uma estrela, ou só os de `--sectors`.

Arquivos já baixados são pulados. Ao fim aparece um resumo com as contagens `ok`, `skipped` (pulados) e `errors`. Erros de um alvo não derrubam os outros; os primeiros são listados como `ERROR`.

### `search`

```powershell
uv run planethunter search --sector 69
```

Limpa as curvas, remove a variação lenta da estrela e roda a busca TLS em paralelo. Você precisa informar `--sector` ou `--tics`. Outras opções: `--all-sectors` (junta todos os setores de cada alvo), `--workers` (processos em paralelo; o padrão usa todos os núcleos menos um), `--resume <run_id>` (retoma uma busca interrompida, pulando os alvos já feitos) e `--null inverted` ou `--null scrambled` (uma **rodada nula**: a mesma busca em curvas de luz viradas de cabeça para baixo ou com cada órbita deslocada no tempo, para contar alarmes falsos; aula [A1](../advanced/a1-detection-algorithms.md)).

Para limitar o número de núcleos de CPU em todos os comandos, ponha `PLANETHUNTER_MAX_WORKERS=4` (ou qualquer número) no arquivo `.env` (veja "Alertas no Telegram" abaixo) ou defina no terminal: `$env:PLANETHUNTER_MAX_WORKERS = "4"`. Isso limita `search`, `vet`, `vet-deep` e `calibrate`, mesmo quando `--workers` pede mais.

A saída é uma linha (`targets` são os alvos, `done` os feitos, `signals` os sinais, `errors` os erros e `time` o tempo):

```text
run_id=20261009T204130Z-single-s69 targets=2164 done=2164 signals=887 errors=0 time=0.8 min
```

Guarde o **run_id**. Ele identifica a execução e é a entrada dos próximos comandos. O formato é data e hora em UTC, o modo (`single` para um setor, `multi` para vários) e o setor (`s69`, ou `sx` quando são vários).

### `crossmatch`

```powershell
uv run planethunter crossmatch 20261009T204130Z-single-s69
```

Compara cada sinal com os espelhos e imprime quantos caíram em cada classe: `NEW`, `KNOWN_PLANET`, `KNOWN_TOI`, `KNOWN_CTOI`, `KNOWN_PUBLISHED`, `KNOWN_FP`, `NEARBY_KNOWN` ou `UNVERIFIED` (guia, passo 4). Muitos `NEW` é normal: quase todos são ruído ou defeito que nenhum catálogo registra. Se o run não tiver sinais, imprime `no signals`.

Ele também faz duas verificações sobre o run inteiro, guardadas com cada sinal: `epoch_spike_frac` (a fração dos trânsitos que caem em momentos em que muitas estrelas sem relação "transitam" ao mesmo tempo) e o papel de sinal compartilhado (`source`, `victim` ou `duplicate`, quando outro alvo a menos de 2′ tem o mesmo período e o mesmo instante de trânsito). A aula [A2](../advanced/a2-mission-vetting.md) explica as duas.

### `vet`

```powershell
uv run planethunter vet 20261009T204130Z-single-s69
```

Roda os testes do vetting básico, sem internet, nos sinais com SDE de pelo menos 9. Um sinal reprova com qualquer veto, qualquer falha grave ou mais de uma falha leve (aula [M5](../intermediate/m5-vetting-in-practice.md)). Depois usa a classe do crossmatch para promover a candidatos só os sinais `NEW` aprovados. Imprime três coisas: quantos sinais foram testados (`signals vetted: ...`); a **tabela de validação** (colunas `class`, `n`, `pass`, `pass_rate`, `common_failures`, `vetoes`: classe, total, aprovados, taxa de aprovação, falhas mais comuns e vetos); e quantos candidatos ficaram por severidade, como `candidates: 3 {'P2': 3}`.

Use a tabela de validação como termômetro. `KNOWN_PLANET` deve passar cerca de 80 %. `KNOWN_FP` deve passar pouco. Se isso mudar muito, algo no vetting mudou.

Se existir um modelo calibrado (veja `calibrate` abaixo), o `vet` também calcula o `p_rank` e o `p_abs` de cada sinal.

### `vet-deep`

```powershell
uv run planethunter vet-deep 20261009T204130Z-single-s69
uv run planethunter vet-deep 20261009T204130Z-single-s69 --workers 2
uv run planethunter vet-deep 20261009T204130Z-single-s69 --force
```

O vetting aprofundado, só para os candidatos: imagem-diferença nos pixels (TPF), vizinhos e binárias do Gaia, tipo da estrela no SIMBAD, presença do sinal em outros setores e FPP com triceratops. Usa internet e guarda o que baixa em `data/cache/`. O FPP roda 3 vezes por candidato, cerca de 6 minutos cada. Sem `run_id`, processa todos os candidatos do banco. Imprime `signal_id`, `verdict`, `score` e `failed` de cada um, ou `no candidates`.

Roda em paralelo e pode ser retomado. `--workers` define quantos candidatos são processados ao mesmo tempo (o padrão vem de `vetting.deep_workers` em `config/thresholds.yaml`, hoje 4). Cada candidato é gravado assim que termina; se o comando for interrompido, rodar de novo pula os que já foram avaliados. `--force` refaz também esses.

### `calibrate`

```powershell
uv run planethunter calibrate
uv run planethunter calibrate --runs 20261009T204130Z-single-s69 --workers 4
```

Treina a **probabilidade de ser planeta** usada para ordenar a fila (aula A4). Usa os resultados do vetting básico dos sinais cuja resposta já se conhece: `KNOWN_PLANET` (rótulo 1), `KNOWN_FP` (rótulo 0) e, quando há rodadas nulas, todos os sinais que elas produziram (rótulo 0, alarmes falsos por construção). Depois ajusta uma regressão logística aos resultados dos testes e a calibra. Opções: `--runs` (run_ids separados por vírgula; por padrão, o run mais recente de cada setor com sinais rotulados), `--null-runs` (por padrão, a rodada nula mais recente de cada setor; `none` as ignora), `--recompute` (refaz o vetting desses runs com o código atual em vez de usar os resultados guardados; sem gravar no banco), `--workers` (processos para o `--recompute`, padrão 2), `--dry-run` (treina e relata, sem salvar nada) e `--repromote` (depois de salvar, recalcula `p_rank`, `p_abs` e as severidades desses runs).

Imprime a validação cruzada, agrupada por estrela para que a mesma estrela nunca esteja no treino e no teste, comparando o modelo com o score determinístico do vetting, e depois os dois limiares que a severidade usa:

```text
C = ... ; nested out-of-fold: ROC-AUC model ... vs score ... | PR-AUC model ... vs score ... | Brier ...
operating points: P2 cut ... (recall ..., FPR ...); P1 cut ... (recall ..., FPR ...)
model ... saved to .../data/models/vetting_lr.json
```

O ROC-AUC mede quão bem um número separa planetas de falsos positivos (1,0 é perfeito, 0,5 é cara ou coroa). Em 338 sinais conhecidos dos setores 69 e 107, a primeira versão do modelo chegou a 0,97, contra 0,90 do score. O **corte de P2** (`P2 cut`) mantém 90 % dos planetas conhecidos; o **corte de P1** (`P1 cut`) permite no máximo 1 % de falsos positivos. O modelo fica em `data/models/vetting_lr.json`, com a versão e os runs de origem, e é usado na próxima vez que você rodar `vet`.

### `candidates`

```powershell
uv run planethunter candidates 20261009T204130Z-single-s69
uv run planethunter candidates
```

Mostra a fila de candidatos `NEW` que passaram no vetting, do mais forte ao mais fraco. Sem `run_id`, mostra os de todos os runs. Candidatos que você rejeitou com `review` saem da lista. Se a fila estiver vazia, imprime `no candidates`. Cada coluna (`severity`, `period_d`, `rp_rearth`, `score`, `failed`, `epoch_spike_frac`, `shared_signal_role`...) está explicada na seção 4 do guia. `p_rank` é a probabilidade do modelo (aula A4): a severidade a usa só para **baixar** a prioridade, nunca para subir. `p_abs` é o mesmo valor corrigido por quão raros são os planetas entre os sinais novos; serve só para leitura. Só sinais que passaram no vetting determinístico com score de pelo menos 0,8 chegam a P1 ou P0; um sinal reprovado com `p_rank` alto fica no máximo em P2.

### `dossier`

```powershell
uv run planethunter dossier <signal_id>
```

Gera o dossiê HTML de um sinal e imprime o caminho, no formato `data/dossiers/tic<TIC>_sig<signal_id>.html`. Abra no navegador. Como ler cada seção: guia, seção 4, e [aula M5](../intermediate/m5-vetting-in-practice.md).

### `alert`

```powershell
uv run planethunter alert 20261009T204130Z-single-s69
uv run planethunter alert 20261009T204130Z-single-s69 --send
```

Gera o dossiê de cada candidato e prepara a mensagem dos que são P0 ou P1. **Sem `--send`, nada sai do seu computador**: as mensagens vão para `data/outbox/AAAA-MM-DD.md`. Com `--send`, vão para Telegram ou Discord, se configurados (veja abaixo).

Antes de enviar (e também na simulação), o comando roda o crossmatch de novo para cada P0 e P1 contra espelhos recém-carregados, e pula o sinal se: algum espelho estiver ausente ou velho; a classe deixou de ser `NEW`; ou o mesmo alvo, com o mesmo período, já foi alertado nos últimos 30 dias. P2 nunca gera alerta imediato. Cada linha impressa diz o sinal, o canal e o resultado, como `signal 1071: outbox dry_run`.

### `review`

```powershell
uv run planethunter review <signal_id> rejected --reason systematic --note "ausente nos setores 67, 68 e 97"
uv run planethunter review <signal_id> follow_up --note "sem outros setores; esperar novos dados"
uv run planethunter review <signal_id> approved
```

Registra sua decisão. O estado é `approved`, `rejected` ou `follow_up`. Rejeitar exige `--reason`: `eb` (binária eclipsante), `blend` (contaminação por vizinha), `systematic` (defeito instrumental), `noise` (ruído), `already_known` (já conhecido) ou `other` (outro). `--note` é texto livre. O comando confirma com uma linha como `signal 1234: rejected [systematic] ausente nos setores 67, 68 e 97`. Suas decisões viram exemplos de treino para um futuro classificador (aula A4).

### `run-target`

```powershell
uv run planethunter run-target 261136679
uv run planethunter run-target 100100827 --sectors 69
uv run planethunter run-target 261136679 --skip-ingest
```

Faz ingestão, busca juntando todos os setores da estrela que estão no disco, crossmatch e vetting básico, e gera um dossiê para cada sinal com SDE ≥ 9. Imprime o `run_id`, uma tabela com cada sinal (`signal_id`, período, `t0_btjd`, profundidade, duração, `sde`, `snr`, `n_transits`, classe do crossmatch, objeto casado, veredito e score do vetting) e o caminho de cada dossiê, em linhas como:

```text
dossier for signal 1234: data/dossiers/tic261136679_sig1234.html
```

Se nenhum sinal passar do SDE mínimo, a tabela é trocada por `no signal above the minimum SDE`. `--sectors` limita a ingestão (setores já baixados antes continuam entrando na busca); `--skip-ingest` usa só o que já está no disco. O vetting aprofundado não roda aqui. Se aparecer `` WARNING: mirrors missing or stale; run `planethunter mirrors sync`. ``, rode `mirrors sync`.

Bom para estudar estrelas com planetas conhecidos, como Pi Mensae (TIC 261136679, [aula B5](../basic/b5-human-eye-practice.md)) e WASP-18 (TIC 100100827, [aula P3](../programming/p3-lightkurve-in-practice.md)).

### `run-sector`

```powershell
uv run planethunter run-sector 69 --limit 200
```

Tudo ponta a ponta: sincroniza os espelhos se algum estiver perto de vencer, baixa, busca, faz crossmatch, vetting básico, vetting aprofundado dos candidatos, dossiês e alertas. Opções: `--limit`, `--skip-ingest` e `--send` (sem ele, alertas só vão para `data/outbox/`).

### `benchmark build` e `benchmark run`

```powershell
uv run planethunter benchmark build 69
uv run planethunter benchmark run 69
```

`build` baixa a lista de TOIs do ExoFOP e congela os do setor com SNR de pelo menos `--min-snr` (padrão 10) e período até 13 dias, em `data/benchmark/sector_0069.csv`. Com `--kind fp`, congela os falsos positivos do TFOPWG. `run` baixa esses alvos, busca e mede o **recall**: quantos dos TOIs conhecidos o sistema reencontra. Opções: `--workers`, `--skip-ingest` e `--run <run_id>` (avalia um run existente). O relatório vai para `docs/benchmarks/` e o detalhe para `data/benchmark/result_<run_id>.csv`. No setor 69, o recall medido foi 91,1 % (123 de 135 TOIs detectáveis).

Use o benchmark antes e depois de qualquer mudança em `config/thresholds.yaml` (aula A5).

## Roteiro: meu primeiro setor

Vamos rodar o setor 69 com só 200 estrelas, passo a passo. Leva poucos minutos.

```powershell
uv run planethunter mirrors sync
uv run planethunter mirrors status                 # tudo "ok"?
uv run planethunter ingest sector 69 --limit 200   # baixa 200 curvas
uv run planethunter search --sector 69             # anote o run_id
uv run planethunter crossmatch <run_id>
uv run planethunter vet <run_id>
uv run planethunter candidates <run_id>
uv run planethunter dossier <signal_id>            # para cada candidato que quiser ver
uv run planethunter alert <run_id>                 # simulação em data/outbox/
```

Troque `<run_id>` e `<signal_id>` pelos valores impressos. Atenção: `search --sector 69` busca em todas as curvas do setor 69 que já estão no disco, não só nas 200 últimas.

Se preferir, o atalho é `uv run planethunter run-sector 69 --limit 200`. Mas faça o passo a passo pelo menos uma vez: você vê o que cada etapa produz.

**O que esperar.** Muitos sinais, quase todos `NEW` ou `KNOWN_*`, e talvez nenhum candidato. É o resultado mais comum. Na primeira fatia real do projeto, 2 164 estrelas do setor 69 deram 887 sinais, 648 `NEW`, 11 aprovados no vetting básico e, depois do vetting aprofundado, **0 P1** e 3 P2. Cada etapa elimina o que não se sustenta.

!!! tip "Na ferramenta"
    Todos os comandos desta página estão em `src/planethunter/cli.py`. Cada um tem poucas linhas e chama funções de `src/planethunter/pipeline.py`. Depois da [aula P1](../programming/p1-python-basics.md), abra o arquivo e procure, por exemplo, `def run_target`: você vai ver a mesma sequência ingestão, busca e crossmatch descrita acima.

## Onde ficam os arquivos

| Caminho | Conteúdo |
|---|---|
| `data/parquet/` | Curvas de luz, uma por estrela e setor (cerca de 0,5 MB cada) |
| `data/mirrors/` | Cópias dos catálogos, cada uma com um arquivo `.json` que registra as linhas, o checksum e a versão |
| `data/planethunter.duckdb` | Banco com sinais, crossmatch, vetting, candidatos e alertas |
| `data/dossiers/` | Dossiês HTML |
| `data/outbox/` | Alertas simulados, um arquivo por dia |
| `data/cache/` | Pixels, Gaia e FPP baixados pelo `vet-deep` |
| `data/models/` | O modelo calibrado (`vetting_lr.json`) gravado pelo `calibrate` |
| `data/benchmark/` | Listas congeladas e resultados do benchmark |
| `config/thresholds.yaml` | Todos os limites, cada um com o porquê |

A pasta `data/` não vai para o Git. Um setor inteiro tem cerca de 20 000 estrelas; nas 2 164 do teste, os Parquet ocuparam cerca de 1 GB. Para guardar os dados em outro disco, defina a variável `PLANETHUNTER_DATA` antes dos comandos: `$env:PLANETHUNTER_DATA = "D:\planethunter-dados"`. Ela vale para aquele terminal.

Para ler os Parquet e o banco em Python, veja a [aula P3](../programming/p3-lightkurve-in-practice.md).

## Alertas no Telegram

1. No Telegram, converse com **@BotFather**, envie `/newbot` e siga as instruções. Ele devolve um **token**, uma senha do seu bot.
2. Mande qualquer mensagem para o seu bot novo.
3. No navegador, abra `https://api.telegram.org/bot<TOKEN>/getUpdates`, trocando `<TOKEN>` pelo seu. Procure `"chat":{"id":` e anote o número: é o seu **chat id**.
4. No VS Code, crie na raiz do projeto um arquivo chamado exatamente `.env`:

```text
TG_TOKEN=123456:ABC-seu-token
TG_CHAT_ID=123456789
```

Para Discord, acrescente `DISCORD_WEBHOOK=` com o endereço do webhook do canal. Depois rode `alert` ou `run-sector` com `--send`. Só candidatos P0 ou P1 geram mensagem.

O mesmo arquivo `.env` pode ter `PLANETHUNTER_MAX_WORKERS=4` para limitar os núcleos de CPU (veja `search`). Uma configuração por linha, sem comentários na mesma linha.

## Cuidados

!!! warning "O arquivo `.env` é secreto"
    Quem tem o token controla o seu bot. O `.env` já está no `.gitignore`. Confira com `git check-ignore .env`: se imprimir `.env`, está protegido. Nunca o copie para outro lugar, nem o mostre em print de tela. Se vazar, gere um token novo no @BotFather com `/revoke`.

- **Nunca anuncie descoberta.** P1 quer dizer que o sinal sobreviveu aos testes automáticos, não que é planeta. O caminho é: sinal, candidato, CTOI, TOI, planeta validado, planeta confirmado. Os últimos passos exigem outros telescópios (guia, seção 7).
- **Não mude limites sem medir.** Qualquer mudança em `config/thresholds.yaml` exige rodar o benchmark antes e depois.
- **Um comando de cada vez.** Dois comandos escrevendo no banco ao mesmo tempo dão erro de "lock".
- **Seja gentil com os servidores.** Comece com `--limit` e não aumente `--workers` sem motivo.

## Exercícios

!!! example "Exercício 1. Espelho velho"
    O `mirrors status` mostra `toi STALE <48 h age= 52.3 h`. O que acontece se você rodar `search`, `crossmatch` e `alert` agora? Como resolver?

    ??? success "Ver resposta"
        A busca roda normalmente, porque não usa os espelhos. No crossmatch, todo sinal que seria `NEW` vira `UNVERIFIED`: com a lista de TOIs desatualizada, não dá para garantir que é novo. Nenhum alerta sai, e o `alert` informa que pulou o sinal por `stale mirrors` (espelhos velhos). Solução: `uv run planethunter mirrors sync` e depois `crossmatch <run_id>` de novo. O `run-sector` faz isso sozinho quando algum espelho está a menos de 6 horas de vencer.

!!! example "Exercício 2. Do run ao alerta"
    Você rodou `search --sector 70` e recebeu um `run_id`. Escreva a sequência de comandos até ter o vetting aprofundado e um alerta simulado.

    ??? success "Ver resposta"
        ```powershell
        uv run planethunter crossmatch <run_id>
        uv run planethunter vet <run_id>
        uv run planethunter vet-deep <run_id>
        uv run planethunter candidates <run_id>
        uv run planethunter alert <run_id>
        ```
        A ordem importa: `vet` usa a classe do crossmatch para decidir quem vira candidato, e `vet-deep` só olha os candidatos que `vet` criou. Sem `--send`, o alerta fica em `data/outbox/`.

!!! example "Exercício 3. Registrar uma rejeição"
    Um P2 tem `rp_rearth` 25, `depth_ppm` 30 000 e `failed` igual a `odd_even`. No dossiê, os trânsitos ímpares são bem mais fundos que os pares. Registre sua decisão.

    ??? success "Ver resposta"
        ```powershell
        uv run planethunter review <signal_id> rejected --reason eb --note "ímpar/par diferentes, Rp 25"
        ```
        Profundidades alternadas indicam uma binária eclipsante com o dobro do período (aula B4), e 25 R⊕ é grande demais para um planeta. O motivo `eb` ajuda o futuro classificador a aprender esse padrão.

## Checklist do laboratório

- [ ] Instalei com `uv sync` e `tools/fpp`, e os testes passaram
- [ ] Sincronizei os espelhos e li o `mirrors status`
- [ ] Rodei `run-target` em Pi Mensae e em WASP-18
- [ ] Fiz o roteiro "meu primeiro setor" com `--limit 200`
- [ ] Abri um dossiê e um arquivo de `data/outbox/`
- [ ] Registrei pelo menos uma revisão com `review`
- [ ] Conferi que o `.env` está ignorado pelo Git

## Para ir além

- Guia para leigos do projeto (`docs/BEGINNERS_GUIDE.md`, no repositório), seções 3 e 4. Explica cada passo e como ler cada coluna e gráfico.
- ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/)). Página de cada estrela, com TOIs, CTOIs e notas da comunidade; é onde você confere um candidato antes de qualquer decisão.
- Página do TESS no HEASARC da NASA ([heasarc.gsfc.nasa.gov](https://heasarc.gsfc.nasa.gov/docs/tess/)). Explica setores, câmeras e cadências das curvas que o `ingest` baixa.
