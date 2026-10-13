# Usar PlanetHunter

<p class="meta">Laboratorio · a partir de la lección B5 · consulta permanente</p>

!!! abstract "En esta página vas a aprender"
    - Instalar PlanetHunter y comprobar que funciona.
    - Qué hace cada comando, cuándo usarlo y qué imprime.
    - Procesar tu primer sector de TESS, a pequeña escala, desde la descarga hasta la alerta simulada.
    - Dónde quedan los archivos y cómo configurar alertas en Telegram de forma segura.

Este es el manual de bolsillo de la herramienta. Usa el vocabulario de las lecciones: **señal** (caída periódica encontrada en la búsqueda), **candidato** (señal nueva que pasó el vetting), **dossier** (informe HTML de una señal). Si un término te resulta extraño, consulta el [glosario](../glossary.md).

La herramienta imprime sus mensajes en inglés. En esta página las explicaciones están en español y las salidas se citan tal como aparecen en la pantalla.

## Instalación

Necesitas **uv** y **Git**. Si todavía no los instalaste, sigue el paso a paso de la [ruta de programación](../programming/index.md). Abre PowerShell (en VS Code: **Terminal > New Terminal**) y ejecuta:

```powershell
cd ~
git clone https://github.com/vitor-92/planethunter.git planethunter
cd planethunter
uv sync
```

Si recibiste la carpeta del proyecto de otra forma, basta con entrar en ella con `cd` y ejecutar `uv sync`.

`uv sync` lee el archivo `pyproject.toml`, descarga Python 3.12 si falta e instala todas las bibliotecas en una carpeta `.venv` dentro del proyecto. La primera vez tarda algunos minutos.

El cálculo de la **FPP** (probabilidad de falso positivo, lección A3) usa la biblioteca triceratops, que exige versiones antiguas de NumPy. Por eso vive en un entorno separado:

```powershell
cd tools\fpp
uv sync
cd ..\..
```

Comprueba la instalación:

```powershell
uv run planethunter --help
uv run pytest
```

El primero muestra la lista de comandos. El segundo ejecuta las pruebas automáticas, sin internet, en unos 45 segundos. Todo en verde: listo.

!!! note "Siempre `uv run` adelante"
    `uv run planethunter ...` garantiza que el comando use el Python y las bibliotecas del proyecto. Ejecútalo siempre desde dentro de la carpeta `planethunter`. Cualquier comando acepta `--help`, por ejemplo `uv run planethunter search --help`.

## Mapa de los comandos

El pipeline tiene 8 pasos (guía, sección 1). Cada comando cubre uno o más de ellos.

| Comando | Paso | ¿Usa internet? | Cuándo usarlo |
|---|---|---|---|
| `mirrors sync` / `mirrors status` | 0. Espejos | sync: sí | Antes de cualquier crossmatch; status cuando quieras revisar |
| `ingest sector` / `ingest target` | 1. Ingesta | sí | Descargar curvas de luz |
| `search` | 2 y 3. Limpieza y búsqueda | no | Buscar señales en las curvas ya descargadas |
| `crossmatch` | 4. "¿Ya existe?" | no | Después de `search` |
| `vet` | 5. Vetting básico | no | Después de `crossmatch` |
| `vet-deep` | 6. Vetting profundo | sí | Para los candidatos que pasaron `vet` |
| `candidates` | 7 | no | Ver la cola de candidatos |
| `dossier` | 7 | no | Generar el informe de una señal |
| `alert` | 7 | solo con `--send` | Generar dossiers y alertar P0/P1 |
| `review` | después del 7 | no | Registrar tu decisión sobre un candidato |
| `calibrate` | ajuste del vetting | no | Entrenar la probabilidad calibrada de ser planeta |
| `run-target` | 1 a 4 | sí | Estudiar una sola estrella, de punta a punta |
| `run-sector` | 0 a 7 | sí | Procesar todo un sector |
| `benchmark build` / `benchmark run` | medición | sí | Medir el recall antes y después de cambiar algo |

La regla del proyecto es: **nada de internet en el camino crítico de la búsqueda**. Los comandos `search`, `crossmatch` y `vet` trabajan solo con copias locales.

## Cada comando

### `mirrors sync` y `mirrors status`

```powershell
uv run planethunter mirrors sync
uv run planethunter mirrors status
```

`sync` descarga 12 listas de objetos conocidos: el NASA Exoplanet Archive, los TOIs y CTOIs de ExoFOP, exoplanet.eu, la tabla de KOIs de Kepler, los planetas y candidatos de K2, dos catálogos de binarias eclipsantes de TESS (Prša et al. 2022 y Kostov et al. 2025) y cuatro listas publicadas de candidatos (DIAmante, DTARPS, LEO-Vetter y ExoMiner++). Las tablas publicadas nunca cambian, así que `sync` las salta una vez que están en el disco (`--force` las vuelve a descargar). exoplanet.eu tarda algunos minutos. `status` muestra, para cada copia, su estado, su límite de antigüedad, su antigüedad (`age`), el número de filas (`rows`), el inicio de su checksum y el archivo:

```text
archive_pscomppars   ok         <48 h age=   4.1 h rows=   6445 sha256=0833b7792d0f 20261009T193948Z.parquet
exoplanet_eu         ok        <168 h age=   4.1 h rows=   8354 sha256=a39d6af4196b 20261010T054524Z.parquet
toi                  ok         <48 h age=   4.1 h rows=   8151 sha256=fd7a3f98832d 20261009T193908Z.parquet
ctoi                 ok         <48 h age=   4.1 h rows=   5138 sha256=5a5e207dec9a 20261010T055318Z.parquet
eb_catalog           ok        static age=   3.9 h rows=   4584 sha256=d839230f8fce 20261009T194915Z.parquet
koi_cumulative       ok        <720 h age=   4.1 h rows=   9564 sha256=f9e3f26e63bc 20261010T054440Z.parquet
...
```

Cada fuente tiene su propio límite: 48 horas para las listas que cambian todos los días (TOI, CTOI, el Archive), 7 días (168 h) para exoplanet.eu y K2, 30 días (720 h) para los KOIs; las tablas `static` nunca vencen. `STALE` (vencida) significa más antigua que el límite. `MISSING` (ausente), que la copia no existe. `VERSION`, que la copia del disco la hizo una versión anterior del código y hay que sincronizarla de nuevo. En los tres casos, ninguna señal puede clasificarse como `NEW`: pasa a `UNVERIFIED` y no genera alerta, y el comando termina con un código de error.

### `ingest sector` e `ingest target`

```powershell
uv run planethunter ingest sector 69 --limit 200
uv run planethunter ingest sector 69 --tics 100100827,261136679
uv run planethunter ingest target 261136679 --sectors 1,4,8
```

`ingest sector` descarga las curvas SPOC de 2 minutos de un sector. Opciones: `--limit N` (solo los N primeros objetivos, para pruebas), `--tics` (lista de TICs separados por comas, sin espacios) y `--workers` (descargas simultáneas, 8 por defecto; sé amable con MAST). `ingest target` descarga todos los sectores de una estrella, o solo los de `--sectors`.

Los archivos ya descargados se saltan. Al final aparece un resumen con los conteos `ok`, `skipped` (saltados) y `errors`. Los errores de un objetivo no tumban a los demás; los primeros se listan como `ERROR`.

### `search`

```powershell
uv run planethunter search --sector 69
```

Limpia las curvas, quita la variación lenta de la estrella y ejecuta la búsqueda TLS en paralelo. Tienes que indicar `--sector` o `--tics`. Otras opciones: `--all-sectors` (une todos los sectores de cada objetivo), `--workers` (procesos en paralelo; por defecto usa todos los núcleos menos uno), `--resume <run_id>` (retoma una búsqueda interrumpida, saltando los objetivos ya procesados) y `--null inverted` o `--null scrambled` (una **corrida nula**: la misma búsqueda en curvas de luz puestas de cabeza o con cada órbita desplazada en el tiempo, para contar falsas alarmas; lección [A1](../advanced/a1-detection-algorithms.md)).

Para limitar el número de núcleos de CPU en todos los comandos, pon `PLANETHUNTER_MAX_WORKERS=4` (o cualquier número) en el archivo `.env` (ver "Alertas en Telegram" más abajo) o defínelo en la terminal: `$env:PLANETHUNTER_MAX_WORKERS = "4"`. Limita `search`, `vet`, `vet-deep` y `calibrate`, aunque `--workers` pida más.

La salida es una línea (`targets` = objetivos, `done` = procesados, `signals` = señales, `errors` = errores, `time` = tiempo):

```text
run_id=20261009T204130Z-single-s69 targets=2164 done=2164 signals=887 errors=0 time=0.8 min
```

Guarda el **run_id**. Identifica la ejecución y es la entrada de los comandos siguientes. El formato es fecha y hora en UTC, el modo (`single` para un sector, `multi` para varios) y el sector (`s69`, o `sx` cuando son varios).

### `crossmatch`

```powershell
uv run planethunter crossmatch 20261009T204130Z-single-s69
```

Compara cada señal con los espejos e imprime cuántas cayeron en cada clase: `NEW`, `KNOWN_PLANET`, `KNOWN_TOI`, `KNOWN_CTOI`, `KNOWN_PUBLISHED`, `KNOWN_FP`, `NEARBY_KNOWN` o `UNVERIFIED` (guía, paso 4). Que haya muchos `NEW` es normal: casi todos son ruido o defectos que ningún catálogo registra.

También hace dos verificaciones sobre toda la corrida, guardadas con cada señal: `epoch_spike_frac` (la fracción de sus tránsitos que caen en momentos en que muchas estrellas sin relación "transitan" a la vez) y el papel de señal compartida (`source`, `victim` o `duplicate`, cuando otro objetivo a menos de 2′ tiene el mismo período y el mismo instante de tránsito). La lección [A2](../advanced/a2-mission-vetting.md) explica las dos.

### `vet`

```powershell
uv run planethunter vet 20261009T204130Z-single-s69
```

Ejecuta las pruebas del vetting básico, sin internet, en las señales con SDE de al menos 9. Una señal reprueba con cualquier veto, cualquier falla dura o más de una falla leve (lección [M5](../intermediate/m5-vetting-in-practice.md)). Después usa la clase del crossmatch para promover a candidatos solo las señales `NEW` aprobadas. Imprime tres cosas: cuántas señales se probaron (`signals vetted: ...`); la **tabla de validación** (columnas `class`, `n`, `pass`, `pass_rate`, `common_failures`, `vetoes`, es decir, clase, cantidad, aprobadas, tasa de aprobación, fallas más comunes y vetos); y cuántos candidatos quedaron por severidad, como `candidates: 3 {'P2': 3}`.

Usa la tabla de validación como termómetro. `KNOWN_PLANET` debería pasar cerca del 80 %. `KNOWN_FP` debería pasar poco. Si eso cambia mucho, algo en el vetting cambió.

Si existe un modelo calibrado (ver `calibrate` más abajo), `vet` también calcula el `p_rank` y el `p_abs` de cada señal.

### `vet-deep`

```powershell
uv run planethunter vet-deep 20261009T204130Z-single-s69
uv run planethunter vet-deep 20261009T204130Z-single-s69 --workers 4
uv run planethunter vet-deep 20261009T204130Z-single-s69 --force
```

El vetting profundo, solo para los candidatos: imagen de diferencia en los píxeles (TPF), vecinas y binarias de Gaia, tipo de estrella en SIMBAD, presencia de la señal en otros sectores y FPP con triceratops. Usa internet y guarda lo que descarga en `data/cache/`. La FPP se ejecuta 3 veces por candidato, unos 6 minutos cada vez. Sin `run_id`, procesa todos los candidatos de la base de datos. Imprime `signal_id`, `verdict`, `score` y `failed` de cada uno, o `no candidates` si no hay ninguno.

Opciones:

- `--workers N`: cuántos candidatos se evalúan en paralelo. Por defecto usa el valor `vetting.deep_workers` de `config/thresholds.yaml` (4).
- `--force`: vuelve a evaluar también los candidatos que ya tenían vetting profundo.

El comando es **reanudable**: guarda cada candidato apenas termina y, en la siguiente ejecución, salta los que ya fueron evaluados. Si se corta la conexión o cierras la terminal a mitad de camino, vuelve a ejecutar el mismo comando y sigue desde donde quedó. Usa `--force` solo cuando quieras rehacer todo, por ejemplo después de cambiar un límite.

### `candidates`

```powershell
uv run planethunter candidates 20261009T204130Z-single-s69
uv run planethunter candidates
```

Muestra la cola de candidatos `NEW` que pasaron el vetting, del más fuerte al más débil. Sin `run_id`, muestra los de todos los runs. Los candidatos que rechazaste con `review` salen de la lista. Si la cola está vacía, imprime `no candidates`. Cada columna (`severity`, `period_d`, `rp_rearth`, `score`, `failed`, `epoch_spike_frac`, `shared_signal_role`...) está explicada en la sección 4 de la guía.

`p_rank` es la probabilidad del modelo (lección A4), aprendida con el comando `calibrate` (ver más abajo): la severidad la usa solo para **bajar** la prioridad, nunca para subirla. `p_abs` es el mismo valor corregido por lo raros que son los planetas entre las señales nuevas; es solo para leer. Solo las señales que pasaron el vetting determinista con un score de al menos 0,8 pueden llegar a P1 o P0; una señal reprobada con un `p_rank` alto queda como máximo en P2. Un veto del vetting sigue eliminando la señal, sea cual sea la probabilidad.

### `dossier`

```powershell
uv run planethunter dossier <signal_id>
```

Genera el dossier HTML de una señal e imprime la ruta, con el formato `data/dossiers/tic<TIC>_sig<signal_id>.html`. Ábrelo en el navegador. Cómo leer cada sección: guía, sección 4, y [lección M5](../intermediate/m5-vetting-in-practice.md).

### `alert`

```powershell
uv run planethunter alert 20261009T204130Z-single-s69
uv run planethunter alert 20261009T204130Z-single-s69 --send
```

Genera el dossier de cada candidato y prepara el mensaje de los que son P0 o P1. **Sin `--send`, nada sale de tu computadora**: los mensajes van a `data/outbox/AAAA-MM-DD.md`. Con `--send`, van a Telegram o Discord, si están configurados (ver más abajo).

Antes de enviar (y también en la simulación), el comando vuelve a ejecutar el crossmatch de cada P0 y P1 contra espejos recién cargados, y salta la señal si: algún espejo falta o está vencido; la clase dejó de ser `NEW`; o el mismo objetivo, con el mismo período, ya se alertó en los últimos 30 días. P2 nunca genera alerta inmediata. Cada línea impresa indica la señal, el canal y el resultado, como `signal 1071: outbox dry_run`; cuando la señal se salta, el resultado es `skipped`, seguido del motivo en inglés: `stale mirrors: [...]` (espejos vencidos), `class is now ...` (la clase cambió) o `already alerted in the last 30 days` (ya alertada en los últimos 30 días).

### `review`

```powershell
uv run planethunter review <signal_id> rejected --reason systematic --note "ausente en los sectores 67, 68 y 97"
uv run planethunter review <signal_id> follow_up --note "sin otros sectores; esperar datos nuevos"
uv run planethunter review <signal_id> approved
```

Registra tu decisión. El estado es `approved` (aprobado), `rejected` (rechazado) o `follow_up` (seguimiento). Rechazar exige `--reason`: `eb` (binaria eclipsante), `blend` (contaminación por una estrella vecina), `systematic` (defecto instrumental), `noise` (ruido), `already_known` (ya conocido) u `other` (otro). `--note` es texto libre. Tus decisiones se convierten en ejemplos de entrenamiento para un futuro clasificador (lección A4).

### `calibrate`

```powershell
uv run planethunter calibrate
uv run planethunter calibrate --runs 20261009T204130Z-single-s69 --workers 4
```

Entrena la **probabilidad de ser planeta** que se usa para ordenar la cola (`p_rank`, guardada en la columna `p_planet`; lección A4). El `score` del vetting combina las pruebas con pesos elegidos a mano; `calibrate` aprende esos pesos a partir de los resultados del vetting básico de señales cuya respuesta ya se conoce: `KNOWN_PLANET` (planetas, etiqueta 1), `KNOWN_FP` (falsos positivos catalogados, etiqueta 0) y, cuando hay corridas nulas, todas las señales que produjeron (etiqueta 0, falsas alarmas por construcción). Después ajusta una regresión logística a los resultados de las pruebas y la calibra.

Opciones: `--runs` (run_ids separados por comas; por defecto, el run más reciente de cada sector que tiene señales etiquetadas), `--null-runs` (por defecto, la corrida nula más reciente de cada sector; `none` las salta), `--recompute` (vuelve a hacer el vetting de esos runs con el código actual en lugar de usar los resultados guardados; sin escribir en la base de datos), `--workers` (procesos para `--recompute`, 2 por defecto), `--dry-run` (entrena e informa, no guarda nada) y `--repromote` (después de guardar, recalcula `p_rank`, `p_abs` y las severidades de esos runs).

Imprime la **validación cruzada agrupada por estrella** (la misma estrella nunca está a la vez en el entrenamiento y en la prueba), que compara el modelo con el score determinista del vetting, y después los dos umbrales que usa la severidad:

```text
C = ... ; nested out-of-fold: ROC-AUC model ... vs score ... | PR-AUC model ... vs score ... | Brier ...
operating points: P2 cut ... (recall ..., FPR ...); P1 cut ... (recall ..., FPR ...)
model ... saved to .../data/models/vetting_lr.json
```

Un ROC-AUC más alto significa que el modelo separa mejor planetas de falsos positivos (1,0 es perfecto, 0,5 es azar). En las mediciones del proyecto, con 338 señales conocidas de los sectores 69 y 107, la primera versión del modelo llegó a un ROC-AUC de 0,97 frente a 0,90 del score. El **corte de P2** (`P2 cut`) conserva el 90 % de los planetas conocidos; el **corte de P1** (`P1 cut`) admite como máximo un 1 % de falsos positivos. El modelo se guarda en `data/models/vetting_lr.json`, con su versión y los runs de los que vino, y se usa la próxima vez que ejecutes `vet`.

Vuelve a ejecutar `calibrate` cuando tengas runs nuevos con muchas señales conocidas o después de cambiar alguna prueba del vetting. Como cualquier cambio en el vetting, compara el benchmark antes y después.

### `run-target`

```powershell
uv run planethunter run-target 261136679
uv run planethunter run-target 100100827 --sectors 69
uv run planethunter run-target 261136679 --skip-ingest
```

Hace la ingesta, la búsqueda uniendo todos los sectores de la estrella que están en el disco, el crossmatch y el vetting básico, y genera un dossier para cada señal con SDE ≥ 9. Imprime el `run_id`, una tabla con cada señal (`signal_id`, período, `t0_btjd`, profundidad, duración, `sde`, `snr`, `n_transits`, clase del crossmatch, objeto emparejado, veredicto y score del vetting) y la ruta de cada dossier, en líneas como `dossier for signal 1234: data/dossiers/tic261136679_sig1234.html`. Si ninguna señal supera el SDE mínimo, la tabla se reemplaza por `no signal above the minimum SDE`. `--sectors` limita la ingesta (los sectores ya descargados antes siguen entrando en la búsqueda); `--skip-ingest` usa solo lo que ya está en el disco. El vetting profundo no se ejecuta aquí. Si aparece ``WARNING: mirrors missing or stale; run `planethunter mirrors sync`.``, significa que faltan espejos o están vencidos: ejecuta `mirrors sync`.

Es bueno para estudiar estrellas con planetas conocidos, como Pi Mensae (TIC 261136679, [lección B5](../basic/b5-human-eye-practice.md)) y WASP-18 (TIC 100100827, [lección P3](../programming/p3-lightkurve-in-practice.md)).

### `run-sector`

```powershell
uv run planethunter run-sector 69 --limit 200
```

Todo de punta a punta: sincroniza los espejos si alguno está por vencer, descarga, busca, hace el crossmatch, el vetting básico, el vetting profundo de los candidatos, los dossiers y las alertas. Opciones: `--limit`, `--skip-ingest` y `--send` (sin él, las alertas solo van a `data/outbox/`).

### `benchmark build` y `benchmark run`

```powershell
uv run planethunter benchmark build 69
uv run planethunter benchmark run 69
```

`build` descarga la lista de TOIs de ExoFOP y congela los del sector con SNR de al menos `--min-snr` (10 por defecto) y período de hasta 13 días, en `data/benchmark/sector_0069.csv`. Con `--kind fp`, congela los falsos positivos del TFOPWG. `run` descarga esos objetivos, busca y mide el **recall**: cuántos de los TOIs conocidos vuelve a encontrar el sistema. Opciones: `--workers`, `--skip-ingest` y `--run <run_id>` (evalúa un run existente). El informe va a `docs/benchmarks/` y el detalle a `data/benchmark/result_<run_id>.csv`. En el sector 69, el recall medido fue de 91,1 % (123 de 135 TOIs detectables).

Usa el benchmark antes y después de cualquier cambio en `config/thresholds.yaml` (lección A5).

## Guía: mi primer sector

Vamos a procesar el sector 69 con solo 200 estrellas, paso a paso. Tarda pocos minutos.

```powershell
uv run planethunter mirrors sync
uv run planethunter mirrors status                 # ¿todo "ok"?
uv run planethunter ingest sector 69 --limit 200   # descarga 200 curvas
uv run planethunter search --sector 69             # anota el run_id
uv run planethunter crossmatch <run_id>
uv run planethunter vet <run_id>
uv run planethunter candidates <run_id>
uv run planethunter dossier <signal_id>            # para cada candidato que quieras ver
uv run planethunter alert <run_id>                 # simulación en data/outbox/
```

Reemplaza `<run_id>` y `<signal_id>` por los valores impresos. Atención: `search --sector 69` busca en todas las curvas del sector 69 que ya están en el disco, no solo en las últimas 200.

Si prefieres, el atajo es `uv run planethunter run-sector 69 --limit 200`. Pero haz el paso a paso al menos una vez: así ves lo que produce cada etapa.

**Qué esperar.** Muchas señales, casi todas `NEW` o `KNOWN_*`, y tal vez ningún candidato. Es el resultado más común. En la primera tanda real del proyecto, 2164 estrellas del sector 69 dieron 887 señales, 648 `NEW`, 11 aprobadas en el vetting básico y, después del vetting profundo, **0 P1** y 3 P2. Cada etapa elimina lo que no se sostiene.

!!! tip "En la herramienta"
    Todos los comandos de esta página están en `src/planethunter/cli.py`. Cada uno tiene pocas líneas y llama a funciones de `src/planethunter/pipeline.py`. Después de la [lección P1](../programming/p1-python-basics.md), abre el archivo y busca, por ejemplo, `def run_target`: vas a ver la misma secuencia de ingesta, búsqueda y crossmatch descrita arriba.

## Dónde quedan los archivos

| Ruta | Contenido |
|---|---|
| `data/parquet/` | Curvas de luz, una por estrella y sector (cerca de 0,5 MB cada una) |
| `data/mirrors/` | Copias de los catálogos, cada una con un archivo `.json` que registra las filas, el checksum y la versión |
| `data/planethunter.duckdb` | Base de datos con señales, crossmatch, vetting, candidatos y alertas |
| `data/dossiers/` | Dossiers HTML |
| `data/outbox/` | Alertas simuladas, un archivo por día |
| `data/cache/` | Píxeles, Gaia y FPP descargados por `vet-deep` |
| `data/models/` | Modelo de probabilidad calibrada (`vetting_lr.json`), creado por `calibrate` |
| `data/benchmark/` | Listas congeladas y resultados del benchmark |
| `config/thresholds.yaml` | Todos los límites, cada uno con su porqué |

La carpeta `data/` no va a Git. Un sector entero tiene cerca de 20 000 estrellas; en las 2164 de la prueba, los Parquet ocuparon cerca de 1 GB. Para guardar los datos en otro disco, define la variable `PLANETHUNTER_DATA` antes de los comandos: `$env:PLANETHUNTER_DATA = "D:\planethunter-datos"`. Vale para esa terminal.

Para leer los Parquet y la base de datos en Python, mira la [lección P3](../programming/p3-lightkurve-in-practice.md).

## Alertas en Telegram

1. En Telegram, habla con **@BotFather**, envía `/newbot` y sigue las instrucciones. Te devuelve un **token**, una contraseña de tu bot.
2. Envía cualquier mensaje a tu bot nuevo.
3. En el navegador, abre `https://api.telegram.org/bot<TOKEN>/getUpdates`, reemplazando `<TOKEN>` por el tuyo. Busca `"chat":{"id":` y anota el número: es tu **chat id**.
4. En VS Code, crea en la raíz del proyecto un archivo llamado exactamente `.env`:

```text
TG_TOKEN=123456:ABC-tu-token
TG_CHAT_ID=123456789
```

Para Discord, agrega `DISCORD_WEBHOOK=` con la dirección del webhook del canal. Después ejecuta `alert` o `run-sector` con `--send`. Solo los candidatos P0 o P1 generan mensaje.

El mismo archivo `.env` puede tener `PLANETHUNTER_MAX_WORKERS=4` para limitar los núcleos de CPU (ver `search`). Una configuración por línea, sin comentarios en la misma línea.

## Precauciones

!!! warning "El archivo `.env` es secreto"
    Quien tiene el token controla tu bot. El `.env` ya está en el `.gitignore`. Compruébalo con `git check-ignore .env`: si imprime `.env`, está protegido. Nunca lo copies a otro lugar ni lo muestres en una captura de pantalla. Si se filtra, genera un token nuevo en @BotFather con `/revoke`.

- **Nunca anuncies un descubrimiento.** P1 significa que la señal sobrevivió a las pruebas automáticas, no que sea un planeta. El camino es: señal, candidato, CTOI, TOI, planeta validado, planeta confirmado. Los últimos pasos exigen otros telescopios (guía, sección 7).
- **No cambies límites sin medir.** Cualquier cambio en `config/thresholds.yaml` exige ejecutar el benchmark antes y después.
- **Un comando a la vez.** Dos comandos escribiendo en la base de datos al mismo tiempo dan un error de "lock" (bloqueo).
- **Sé amable con los servidores.** Empieza con `--limit` y no aumentes `--workers` sin motivo.

## Ejercicios

!!! example "Ejercicio 1. Espejo vencido"
    `mirrors status` muestra `toi STALE <48 h age= 52.3 h`. ¿Qué pasa si ejecutas `search`, `crossmatch` y `alert` ahora? ¿Cómo lo resuelves?

    ??? success "Ver respuesta"
        La búsqueda funciona normalmente, porque no usa los espejos. En el crossmatch, toda señal que sería `NEW` pasa a `UNVERIFIED`: con la lista de TOIs desactualizada, no se puede garantizar que sea nueva. No sale ninguna alerta, y `alert` marca las señales como `skipped` con el motivo `stale mirrors: ['toi']`. Solución: `uv run planethunter mirrors sync` y después `crossmatch <run_id>` de nuevo. `run-sector` lo hace solo cuando a algún espejo le faltan menos de 6 horas para vencer.

!!! example "Ejercicio 2. Del run a la alerta"
    Ejecutaste `search --sector 70` y recibiste un `run_id`. Escribe la secuencia de comandos hasta tener el vetting profundo y una alerta simulada.

    ??? success "Ver respuesta"
        ```powershell
        uv run planethunter crossmatch <run_id>
        uv run planethunter vet <run_id>
        uv run planethunter vet-deep <run_id>
        uv run planethunter candidates <run_id>
        uv run planethunter alert <run_id>
        ```
        El orden importa: `vet` usa la clase del crossmatch para decidir quién pasa a candidato, y `vet-deep` solo mira los candidatos que `vet` creó. Si `vet-deep` se interrumpe, vuelve a ejecutarlo: retoma desde donde quedó. Sin `--send`, la alerta queda en `data/outbox/`.

!!! example "Ejercicio 3. Registrar un rechazo"
    Un P2 tiene `rp_rearth` 25, `depth_ppm` 30 000 y `failed` igual a `odd_even`. En el dossier, los tránsitos impares son bastante más profundos que los pares. Registra tu decisión.

    ??? success "Ver respuesta"
        ```powershell
        uv run planethunter review <signal_id> rejected --reason eb --note "impar/par diferentes, Rp 25"
        ```
        Las profundidades alternadas indican una binaria eclipsante con el doble del período (lección B4), y 25 R⊕ es demasiado grande para un planeta. El motivo `eb` ayuda al futuro clasificador a aprender ese patrón.

## Lista de verificación del laboratorio

- [ ] Instalé con `uv sync` y `tools/fpp`, y las pruebas pasaron
- [ ] Sincronicé los espejos y leí `mirrors status`
- [ ] Ejecuté `run-target` en Pi Mensae y en WASP-18
- [ ] Hice la guía "mi primer sector" con `--limit 200`
- [ ] Abrí un dossier y un archivo de `data/outbox/`
- [ ] Registré al menos una revisión con `review`
- [ ] Comprobé que Git ignora el `.env`

## Para ir más allá

- Guía para principiantes del proyecto (`docs/BEGINNERS_GUIDE.md`, en el repositorio), secciones 3 y 4. Explica cada paso y cómo leer cada columna y gráfico.
- ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/)). Página de cada estrella, con TOIs, CTOIs y notas de la comunidad; es donde revisas un candidato antes de cualquier decisión.
- Página de TESS en el HEASARC de la NASA ([heasarc.gsfc.nasa.gov](https://heasarc.gsfc.nasa.gov/docs/tess/)). Explica los sectores, las cámaras y las cadencias de las curvas que descarga `ingest`.
