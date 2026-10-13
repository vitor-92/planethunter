# P3. Lightkurve en la práctica

<p class="meta">Ruta de programación · junto con el módulo M4 · cerca de 10 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Buscar y descargar curvas de luz reales de TESS con la biblioteca Lightkurve.
    - Limpiar, aplanar (flatten), encontrar el período con BLS y plegar la curva.
    - Medir la profundidad del tránsito y estimar el radio del planeta.
    - Abrir los archivos Parquet que PlanetHunter guarda y consultar la base de datos DuckDB con SQL.

Requisitos previos: [P2](p2-numpy-pandas-matplotlib.md) y la [lección M3](../intermediate/m3-periodograms.md) sobre periodogramas. Esta lección es la parte práctica de la [lección M4](../intermediate/m4-tess-data-in-python.md). Vas a necesitar internet. En la carpeta de estudios:

```powershell
uv add lightkurve pyarrow duckdb
```

## El objetivo: WASP-18 b

Vamos a trabajar con **WASP-18 b**, un planeta gigante muy caliente, pegado a su estrella.

| Dato | Valor (ExoFOP, TOI-185.01) |
|---|---|
| Estrella | WASP-18, TIC 100100827, Tmag 8,83, radio 1,35 R☉ |
| Período | 0,941453 días (22,6 horas) |
| Profundidad | 11 445 ppm (cerca de 1 %) |
| Duración | 2,05 horas |
| Disposición | KP (planeta conocido antes de TESS) |

Es un objetivo excelente para aprender: el tránsito es profundo y el período corto. En un sector de 27 días caben más de 20 tránsitos. También aparece en una de las historias reales del proyecto: PlanetHunter ya lo confundió con una binaria eclipsante (guía para principiantes, sección 5).

Junta los bloques de las secciones 1 a 5, en orden, en un archivo `wasp18.py` y ejecútalo con `uv run python wasp18.py`.

## 1. Buscar

```python
import lightkurve as lk
import matplotlib.pyplot as plt
import numpy as np

busqueda = lk.search_lightcurve("TIC 100100827", mission="TESS",
                             author="SPOC", exptime=120)
print(busqueda)
```

`search_lightcurve` le pregunta a **MAST**, el archivo público de datos de TESS, qué curvas existen. Los filtros piden las curvas de **SPOC** (el pipeline oficial de la NASA) con cadencia de 120 segundos. En octubre de 2026 la respuesta tenía 10 filas: sectores 2, 3, 29, 30, 69, 96, 103, 104, 105 y 106.

Al importar Lightkurve puede aparecer un aviso sobre `oktopus`. Puedes ignorarlo: es un módulo opcional que no usamos.

## 2. Descargar el sector 69

```python
busqueda69 = lk.search_lightcurve("TIC 100100827", author="SPOC",
                               exptime=120, sector=69)
lc_bruta = busqueda69.download()     # descarga y guarda en caché en tu disco
print(len(lc_bruta))              # 16499 medidas
print(lc_bruta.time[:3])          # tiempo en BTJD
print(lc_bruta.flux.unit)         # electron / s
print(lc_bruta.meta["RADIUS"], lc_bruta.meta["TESSMAG"], lc_bruta.meta["TEFF"])
lc_bruta.plot()
```

`download()` devuelve un objeto **LightCurve**: una tabla con `time` (tiempo en BTJD), `flux` (brillo en electrones por segundo, ya corregido por SPOC, el llamado PDCSAP) y `flux_err` (error de cada medida). El diccionario `meta` guarda el encabezado del archivo, con datos de la estrella: radio 1,3466 R☉, Tmag 8,83, temperatura 6 226 K.

Por defecto, `download()` ya descarta las medidas que TESS marcó como malas, como las de los ajustes de apuntado ("momentum dumps").

## 3. Limpiar

```python
lc = lc_bruta.remove_nans().normalize()
lc = lc.remove_outliers(sigma_upper=4, sigma_lower=np.inf)
print(len(lc))                    # 14665
```

- `remove_nans()` quita las medidas vacías (NaN quiere decir "no es un número").
- `normalize()` divide entre el brillo mediano. El flujo pasa a quedar alrededor de 1, y una caída de 0,01 significa 1 %.
- `remove_outliers` corta los puntos a más de 4 desviaciones estándar **por encima** de la curva. El `sigma_lower=np.inf` desactiva el corte hacia abajo. Cortar hacia abajo borraría los propios tránsitos. PlanetHunter hace lo mismo: `sigma_upper: 4.0` en `config/thresholds.yaml`.

## 4. Aplanar y encontrar el período con BLS

La estrella varía un poco a lo largo de los días. **Aplanar** (flatten, o detrending) estima esa variación lenta y divide entre ella. El parámetro `window_length` es el tamaño de la ventana, en número de medidas, y tiene que ser impar. Con 901 medidas de 2 minutos, la ventana tiene 30 horas, mucho más larga que el tránsito de 2 horas.

Lo hacemos en dos pasadas. La primera encuentra los tránsitos de forma aproximada. La segunda rehace el aplanado **ocultando** los tránsitos, para que el filtro no se "coma" parte de la caída.

```python
periodos = np.linspace(0.5, 10, 20000)        # períodos probados, en días
duraciones = [0.04, 0.06, 0.08, 0.10, 0.12]     # duraciones probadas, en días

# Pasada 1
pg1 = lc.flatten(window_length=901).to_periodogram(
    method="bls", period=periodos, duration=duraciones)
P = float(pg1.period_at_max_power.value)
T0 = float(pg1.transit_time_at_max_power.value)
D = float(pg1.duration_at_max_power.value)

# Pasada 2: máscara en los tránsitos y nuevo aplanado
mascara = lc.create_transit_mask(period=P, transit_time=T0, duration=1.5 * D)
plana = lc.flatten(window_length=901, mask=mascara)
pg = plana.to_periodogram(method="bls", period=periodos, duration=duraciones)
P = float(pg.period_at_max_power.value)
T0 = float(pg.transit_time_at_max_power.value)
D = float(pg.duration_at_max_power.value)
print(f"P = {P:.5f} d   T0 = {T0:.4f} BTJD   duración = {D * 24:.1f} h")
pg.plot()
```

**BLS** (Box Least Squares) prueba cada período y cada duración de la lista, ajusta una caja a los datos plegados y mide cuánto explica la caída. El resultado es un **periodograma** con un pico en el período correcto (lección M3). Salida:

```text
P = 0.94130 d   T0 = 3182.7619 BTJD   duración = 1.9 h
```

El período coincide con el de ExoFOP hasta el tercer decimal. La diferencia en el cuarto viene de la grilla: 20 000 períodos entre 0,5 y 10 días tienen un paso de 0,0005 días.

!!! note "¿Por qué `float(...)`?"
    Lightkurve devuelve los resultados como magnitudes con unidad (días) y, en las versiones recientes de Astropy, con una "máscara" incorporada. `float(x.value)` lo convierte todo en un número simple. Sin eso, `create_transit_mask` da error (`TypeError: cannot write to unmasked output`) con Lightkurve 2.6 y Astropy 8.

## 5. Plegar y medir

```python
plegada = plana.fold(period=P, epoch_time=T0)
fase = np.asarray(plegada.time.value, dtype=float)    # días desde el centro
flujo = np.asarray(plegada.flux.value, dtype=float)

dentro = np.abs(fase) < 0.25 * D      # núcleo del tránsito
fuera = np.abs(fase) > 1.0 * D         # bien lejos del tránsito
nivel = np.median(flujo[fuera])
prof_ppm = (nivel - np.median(flujo[dentro])) * 1e6
ruido_ppm = np.std(flujo[fuera]) * 1e6

R_estrella = lc.meta["RADIUS"]                        # R_sol
Rp = np.sqrt(prof_ppm / 1e6) * R_estrella * 109.1     # R_tierra
print(f"profundidad = {prof_ppm:.0f} ppm, ruido por punto = {ruido_ppm:.0f} ppm")
print(f"radio del planeta = {Rp:.1f} R_tierra")

ax = plegada.scatter(alpha=0.3)
plegada.bin(time_bin_size=10 / (60 * 24)).plot(ax=ax, color="C3", lw=2)
ax.set_xlim(-0.2, 0.2)
plt.show()
```

Salida:

```text
profundidad = 10830 ppm, ruido por punto = 613 ppm
radio del planeta = 15.3 R_tierra
```

Medimos solo el **núcleo** del tránsito (la mitad central de la duración) para evitar los bordes inclinados, la entrada y la salida del planeta. El radio viene de la regla de la lección B2, la misma función `raio_planeta` de la [lección P1](p1-python-basics.md).

### Comparando con PlanetHunter y ExoFOP

| Fuente | Período (d) | Profundidad (ppm) | Radio (R⊕) |
|---|---|---|---|
| Tú, con BLS | 0,94130 | 10 830 | 15,3 |
| PlanetHunter, sector 69 (TLS) | 0,941592 | 10 583 | 15,1 |
| ExoFOP, TOI-185.01 (varios sectores) | 0,941453 | 11 445 | 15,3 |

Los números coinciden dentro de unos pocos por ciento. Las diferencias vienen del método (caja en BLS, modelo realista de tránsito en TLS), de cuántos sectores entraron y de dónde se mide el "fondo". Los estudios dedicados, que modelan el oscurecimiento del limbo (lección M2), encuentran un radio un poco menor, cerca de 1,2 radios de Júpiter. La cuenta $\delta \approx (R_p/R_\star)^2$ es una aproximación: el centro de la estrella es más brillante que el borde, así que el núcleo del tránsito queda un poco más profundo que $(R_p/R_\star)^2$.

!!! tip "En la herramienta"
    PlanetHunter hace las mismas etapas con otras herramientas: limpieza en `src/planethunter/preprocess/clean.py`, detrending con el filtro biweight de la biblioteca wotan (ventana de 1 día, en lugar del filtro de Lightkurve) y búsqueda con TLS en `src/planethunter/search/tls.py`, en lugar de BLS. Para WASP-18 b en el sector 69 registró SDE 36,1, SNR 473,8 y 21 tránsitos con datos. El dossier muestra el mismo "tránsito plegado" que acabas de dibujar.

!!! question "Para pensar"
    Repite las secciones 2 a 5 con `busqueda.download_all().stitch()`, que descarga y une todos los sectores de la búsqueda. Con tránsitos repartidos a lo largo de años, ¿qué pasa con la precisión del período? ¿Y con el tiempo de cálculo del BLS? Pista: con años de datos, la grilla de 20 000 períodos entre 0,5 y 10 días se vuelve demasiado gruesa y falla el pico; usa una grilla fina alrededor del valor conocido, como `np.linspace(0.94, 0.943, 20000)`.

## 6. Leer el Parquet guardado por PlanetHunter

Cuando PlanetHunter descarga una curva, la convierte a **Parquet**, un formato de tabla compacto y rápido. La ruta sigue un patrón:

```text
data/parquet/sector=0069/author=SPOC/tic_0000000100100827.parquet
```

El sector tiene 4 dígitos y el TIC tiene 16, completados con ceros. Para tener ese archivo, ejecuta en la carpeta de PlanetHunter `uv run planethunter ingest target 100100827 --sectors 69` (mira el [laboratorio](../lab/using-planethunter.md)).

```python
import json
from pathlib import Path

import pyarrow.parquet as pq

RAIZ = Path(r"C:\Users\tu_usuario\planethunter")  # ajústalo a tu carpeta
arq = RAIZ / "data" / "parquet" / "sector=0069" / "author=SPOC" / f"tic_{100100827:016d}.parquet"

tabla = pq.read_table(arq)
df = tabla.to_pandas()
print(df.dtypes)
print(len(df))                                    # 18098 filas

meta = json.loads(tabla.schema.metadata[b"planethunter"])
print(meta["sector"], meta["camera"], meta["procver"])
print(meta["star"]["radius_rsun"], meta["star"]["tmag"])
```

Las columnas:

| Columna | Contenido | Tipo |
|---|---|---|
| `time` | Tiempo en BTJD | float64 |
| `flux`, `flux_err` | Brillo corregido (PDCSAP) y error, en e⁻/s | float32 |
| `sap_flux` | Brillo sin la corrección de SPOC | float32 |
| `quality` | Indicadores de problemas (0 = todo bien) | int32 |
| `cadenceno` | Número de la medida | int64 |
| `mom_centr1`, `mom_centr2` | Posición de la luz en el detector, en píxeles | float32 |

Los **metadatos** quedan en el encabezado del archivo, como texto JSON en la clave `b"planethunter"`: sector, cámara, versión del procesamiento (`procver`), suma de verificación del archivo original y los parámetros de la estrella. La `b` antes de las comillas indica bytes en lugar de texto, una exigencia del formato.

El archivo guarda **todas** las medidas, incluidas las malas. Fíltralas y conviértelas en LightCurve:

```python
from astropy.time import Time

buenos = df[(df["quality"] == 0) & np.isfinite(df["flux"])]
print(len(buenos))                                  # 14665, igual que la descarga
lc_ph = lk.LightCurve(
    time=Time(buenos["time"].to_numpy(), format="btjd", scale="tdb"),
    flux=buenos["flux"].to_numpy(),
    flux_err=buenos["flux_err"].to_numpy(),
).normalize()
```

De aquí en adelante, `lc_ph` acepta `flatten`, `fold` y `to_periodogram` como antes.

## 7. Consultar la base de datos DuckDB

PlanetHunter guarda los resultados en `data/planethunter.duckdb`, una base de datos en un único archivo. Le haces preguntas en **SQL**, el lenguaje estándar de las bases de datos. Para tener WASP-18 b en tu base de datos, ejecuta en la carpeta de PlanetHunter `uv run planethunter run-target 100100827 --sectors 69` y después `uv run planethunter vet <run_id>`, con el `run_id` que imprima el primer comando. Las tablas principales:

| Tabla | Una fila por | Columnas útiles |
|---|---|---|
| `signals` | señal encontrada en la búsqueda | `signal_id`, `run_id`, `tic_id`, `period_days`, `depth_ppm`, `sde`, `snr`, `n_transits` |
| `crossmatch` | señal comparada con los catálogos | `match_class`, `matched_name`, `host_known` |
| `vetting` | señal evaluada | `score`, `verdict`, `vetoed_by`, `failed` |
| `candidates` | candidato en la cola | `severity`, `review_status` |

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

Lee el SQL como una frase: "selecciona (`SELECT`) estas columnas de la tabla (`FROM`) donde (`WHERE`) se cumpla la condición, en orden de (`ORDER BY`)". El `JOIN ... USING (signal_id)` une dos tablas por las filas que tienen el mismo `signal_id`. El `.df()` devuelve un DataFrame de pandas.

En la base de datos del proyecto, al 9/10/2026, el lote de 2 164 estrellas del sector 69 (run `20261009T204130Z-single-s69`) registró WASP-18 b como la señal 2020: `KNOWN_PLANET`, emparejada con TOI-185.01. El vetting básico dio `FAIL`, score 0,2, con fallas en `secondary` y `consistency`. El vetting no es perfecto: aprueba cerca del 81 % de los planetas confirmados del sector 69. Esto no causa una alerta falsa, porque un `KNOWN_PLANET` nunca se convierte en candidato.

!!! warning "Base de datos en uso"
    Ábrela siempre con `read_only=True` y ciérrala con `con.close()`. Si un comando de PlanetHunter se está ejecutando, DuckDB puede rechazar la conexión con un error de "lock". Espera a que el comando termine.

## Ejercicios

!!! example "Ejercicio 1. Impares y pares"
    Una binaria eclipsante con el doble del período muestra eclipses alternados de profundidades diferentes (lección B4). Mide la profundidad de los tránsitos impares y pares de WASP-18 b.

    ??? success "Ver respuesta"
        ```python
        t = np.asarray(plana.time.value, dtype=float)
        f = np.asarray(plana.flux.value, dtype=float)
        n = np.round((t - T0) / P).astype(int)          # número de cada tránsito
        nucleo = np.abs(t - (T0 + n * P)) < 0.25 * D
        impar = (1 - np.median(f[nucleo & (n % 2 == 1)])) * 1e6
        par = (1 - np.median(f[nucleo & (n % 2 == 0)])) * 1e6
        print(f"impares {impar:.0f} ppm, pares {par:.0f} ppm")
        ```
        Resultado: cerca de 10 770 ppm en los impares y 10 880 en los pares, una diferencia del 1 %. Para una binaria con período duplicado, la diferencia suele ser grande. Es lo que mide la prueba `odd_even` del vetting, con barras de error.

!!! example "Ejercicio 2. Mirar la fase 0,5"
    WASP-18 b es tan caliente que TESS ve desaparecer la luz del propio planeta cuando pasa detrás de la estrella. Mide el brillo en fase 0,5 (a mitad de camino entre tránsitos). Compáralo con la regla de PlanetHunter: la prueba `secondary` solo veta si la caída secundaria es de al menos el 10 % de la principal.

    ??? success "Ver respuesta"
        ```python
        sec = np.abs(np.abs(fase) - 0.5 * P) < 0.25 * D
        prof_sec = (nivel - np.median(flujo[sec])) * 1e6
        print(f"fase 0,5: {prof_sec:.0f} ppm = {100 * prof_sec / prof_ppm:.1f} % de la principal")
        ```
        Da cerca de 310 ppm, alrededor del 3 % de la principal. La calibración del vetting del proyecto (sector 69) registra cerca de 340 ppm para esta ocultación. Parte del valor puede venir de la variación de brillo a lo largo de la órbita, que la ventana de 30 horas no elimina por completo. Como el 3 % queda por debajo del 10 %, la regla no veta. La prueba igual registra una falla leve, que reduce el score: por eso la señal 2020 aparece con `secondary` en la columna `failed`. Antes de esta regla, el sistema vetaba WASP-18 b como binaria (guía para principiantes, sección 5).

!!! example "Ejercicio 3. Contar candidatos"
    Escribe una consulta SQL que cuente los candidatos por severidad y por estado de revisión.

    ??? success "Ver respuesta"
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
        `GROUP BY` con dos columnas crea un grupo para cada combinación. En la base de datos del proyecto, al 9/10/2026: 13 P1 pendientes, 49 P2 pendientes, 2 P2 rechazados y 1 P2 en `follow_up`. Tu base de datos tendrá otros números. P1 y P2 no son planetas: son señales que esperan revisión humana.

## Checklist de la lección

- [ ] Busqué y descargué la curva del sector 69 de WASP-18
- [ ] Limpié la curva, cortando solo los puntos altos
- [ ] Encontré el período con BLS en dos pasadas, con máscara en los tránsitos
- [ ] Plegué la curva, medí la profundidad y estimé el radio
- [ ] Comparé mis números con PlanetHunter y ExoFOP
- [ ] Leí un Parquet de PlanetHunter y los metadatos de la clave `b"planethunter"`
- [ ] Consulté `signals`, `crossmatch`, `vetting` y `candidates` con SQL
- [ ] Resolví los tres ejercicios

## Para ir más allá

- Tutoriales de Lightkurve ([lightkurve.github.io](https://lightkurve.github.io/lightkurve/tutorials/index.html)), en especial "Identifying transiting exoplanet signals". El recorrido de esta lección sigue el mismo camino, con más detalles sobre cada función.
- Documentación de Astropy sobre Box Least Squares ([docs.astropy.org](https://docs.astropy.org/en/stable/timeseries/bls.html)). El BLS de Lightkurve llama a esa implementación por debajo.
- Página de WASP-18 b en el NASA Exoplanet Archive ([exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu/overview/WASP-18%20b)). Reúne los parámetros publicados para compararlos con tu medida.
