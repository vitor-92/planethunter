# M4. Datos de TESS en Python

<p class="meta">Nivel intermedio · semanas 6–8 · unas 12 horas</p>

!!! abstract "En esta lección vas a aprender a"
    - Buscar y descargar la curva de luz de una estrella de TESS con la biblioteca Lightkurve.
    - Graficar, limpiar y aplanar (flatten) la curva.
    - Ejecutar un periodograma BLS y reconocer el pico verdadero y los alias.
    - Plegar (fold) la curva en el período encontrado y ver el tránsito.
    - Hacer a mano tres pruebas de vetting: impar/par, fase 0,5 y búsqueda de una segunda señal.
    - Comparar tu resultado con el de PlanetHunter para el mismo objetivo.

!!! warning "Requisito previo: ruta de programación"
    Esta lección supone que terminaste [P1. Python básico](../programming/p1-python-basics.md) y [P2. NumPy, pandas y Matplotlib](../programming/p2-numpy-pandas-matplotlib.md). Necesitas saber qué es un array de NumPy, llamar funciones con argumentos con nombre y hacer un gráfico simple. La lección [P3. Lightkurve en la práctica](../programming/p3-lightkurve-in-practice.md) complementa esta, con más detalles de la biblioteca.

## El objetivo: Pi Mensae c

**Pi Mensae** (TIC 261136679) es una estrella parecida al Sol, muy brillante (Tmag 5,1), en el cielo del hemisferio sur. Su planeta **Pi Men c** fue uno de los primeros anunciados con datos de TESS, en 2018: período de unos **6,27 días** y tránsitos de unos **300 ppm**, poco más de 2 radios terrestres.

Es un objetivo ideal para empezar: la señal es real y conocida, pero no es obvia a simple vista en la curva cruda. Vas a necesitar cada paso de la búsqueda para verla. Vamos a usar solo el **sector 1**, el primero de TESS (julio y agosto de 2018).

## Preparación

Lightkurve ya viene instalado con PlanetHunter. En la carpeta del proyecto, crea un archivo `pimen.py` (fuera de `src/`, por ejemplo en una carpeta tuya `estudios/`) y ejecuta cada bloque con:

```bash
uv run python pimen.py
```

Si prefieres Jupyter, pega los bloques en celdas, en orden. Los gráficos aparecen solos; en un script, usa `plt.show()` al final de cada gráfico, como en el código de abajo.

La primera descarga necesita internet y tarda unos segundos. Lightkurve guarda los archivos en una caché local y no los vuelve a descargar.

## Paso 1. Buscar

```python
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
import lightkurve as lk

# Busca en el archivo MAST todas las curvas de luz SPOC de 2 minutos (120 s) de esta estrella.
busca_todas = lk.search_lightcurve(
    "TIC 261136679", mission="TESS", author="SPOC", exptime=120
)
print(busca_todas)  # una fila por sector

# Ahora solo el sector 1.
busca = lk.search_lightcurve(
    "TIC 261136679", mission="TESS", author="SPOC", exptime=120, sector=1
)
print(busca)
```

**Lo que deberías ver.** La primera tabla tiene más de veinte filas: Pi Mensae está cerca del polo sur de la eclíptica y fue observada en muchos sectores entre 2018 y 2025. Cada fila tiene misión y sector, año, autor (SPOC), tiempo de exposición (120 s) y el nombre del objetivo. La segunda tabla tiene una sola fila: `TESS Sector 01 2018 SPOC 120 261136679`.

!!! note "Por qué SPOC de 2 minutos"
    SPOC es el pipeline oficial de la misión, que produce curvas para objetivos preseleccionados con cadencia de 2 minutos. Es el mismo tipo de dato que PlanetHunter ingiere por defecto. La curva ya viene corregida de efectos del telescopio (columna PDCSAP) y de contaminación por estrellas vecinas.

## Paso 2. Descargar e inspeccionar

```python
lc = busca.download()  # objeto TessLightCurve

# Metadatos del encabezado: brillo, temperatura y radio de la estrella (del TIC).
print(lc.meta["OBJECT"], "sector", lc.meta["SECTOR"])
print("Tmag", lc.meta["TESSMAG"], "Teff", lc.meta["TEFF"], "R*", lc.meta["RADIUS"])
print("columnas:", lc.colnames[:8])
print(len(lc), "puntos, de", lc.time.min(), "a", lc.time.max())
```

**Lo que deberías ver.** `TIC 261136679 sector 1`, Tmag 5,105, Teff de unos 5 990 K, radio 1,149 R☉. Unos 18 264 puntos, de BTJD 1325,30 a 1353,18. BTJD es el tiempo de TESS: días desde una fecha de referencia.

Por defecto, Lightkurve usa la columna `pdcsap_flux` como `flux` y ya descarta las cadencias marcadas como malas por el telescopio (máscara de calidad "default", la misma de PlanetHunter).

## Paso 3. Graficar la curva cruda

```python
lc = lc.remove_nans().normalize()  # quita puntos vacíos y divide por la mediana (brillo normal = 1)
ax = lc.plot()
ax.set_title("Pi Mensae, sector 1, curva normalizada")
plt.show()
```

**Lo que deberías ver.**

- Una franja de puntos entre unos 0,9997 y 1,0003, es decir, ±300 ppm.
- Un **hueco** cerca de BTJD 1339: la pausa para enviar datos a la Tierra, entre las dos órbitas del sector.
- Un tramo más ruidoso cerca de BTJD 1347 a 1349.
- Los tránsitos están ahí, pero apenas se distinguen del ruido. Si miras con atención, cerca de 1325,5, 1331,8, 1338,0, 1344,3 y 1350,6 hay caídas discretas. Sin saber dónde mirar, no las encontrarías.

Es la situación típica: la señal está por debajo del ruido de cada punto. Es la estadística de la lección [M1](m1-statistics-for-signals.md) la que la va a revelar.

## Paso 4. Limpiar y aplanar

```python
# Elimina solo los puntos discrepantes HACIA ARRIBA (fulguraciones). Nunca hacia abajo: borraría tránsitos.
limpa = lc.remove_outliers(sigma_upper=4, sigma_lower=np.inf)

# Aplana: estima la tendencia lenta y divide por ella.
# window_length está en número de puntos y debe ser impar: 721 x 2 min = 1 día.
plana, tendencia = limpa.flatten(window_length=721, return_trend=True)

ax = limpa.plot(label="limpia")
tendencia.plot(ax=ax, color="red", label="tendencia")
plt.show()

ruido_ppm = np.std(plana.flux.value) * 1e6
print(f"{len(limpa)} puntos; ruido por punto: {ruido_ppm:.0f} ppm")
```

**Lo que deberías ver.** Unos 9 puntos eliminados (18 255 restantes). La tendencia roja es casi recta: Pi Mensae es una estrella tranquila. El ruido por punto queda en unos **128 ppm** (el sigma robusto, vía MAD, da unos 120 ppm).

!!! info "Misma idea, filtro distinto"
    El `flatten` de Lightkurve usa un filtro de Savitzky-Golay. PlanetHunter usa el **biweight** de wotan, que es más robusto ante tránsitos dentro de la ventana. Los dos usan aquí una ventana de 1 día, por las razones de la lección [M3](m3-periodograms.md): menos que eso se come los tránsitos largos.

## Paso 5. Periodograma BLS

```python
periodos = np.linspace(1, 15, 20000)            # días
duracoes = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]  # días (1,2 h a 4,8 h)
bls = plana.to_periodogram(method="bls", period=periodos, duration=duracoes)

bls.plot()
plt.show()

P = bls.period_at_max_power
t0 = bls.transit_time_at_max_power  # objeto Time; .value da el número en BTJD
dur = bls.duration_at_max_power
prof = bls.depth_at_max_power
print(f"P = {P:.4f}, t0 = {t0.value:.3f}, duración = {dur:.2f}, profundidad = {prof.value * 1e6:.0f} ppm")

# Realce del pico, en el espíritu del SDE: cuántas desviaciones estándar por encima de la media.
destaque = (bls.max_power - np.mean(bls.power)) / np.std(bls.power)
print(f"realce del pico: {destaque:.1f}")
```

**Lo que deberías ver.**

- Un pico dominante en **6,27 d**, con potencia cercana a 1 400.
- Picos menores, los **alias**: 12,53 d (2P, potencia ~860), 3,13 d (P/2, ~750) y otros en 9,4 d (3P/2), 4,18 d (2P/3) y 2,09 d (P/3).
- Salida: `P = 6.2664 d, t0 = 1325.507, duración = 0.12 d, profundidad = 228 ppm`.
- Realce del pico: unos **12,9**.

La duración de 0,12 d (2,9 h) es el valor más cercano en la **grilla** que diste. Con una grilla más fina, el resultado cambiaría un poco. El realce no es el SDE de TLS (las definiciones de potencia difieren), pero la idea es la misma.

## Paso 6. Plegar y ver el tránsito

```python
dobrada = plana.fold(period=P, epoch_time=t0)  # el tiempo pasa a ser "días desde el tránsito"

ax = dobrada.scatter(alpha=0.3, s=2, label="puntos de 2 min")
dobrada.bin(time_bin_size=10 * u.min).scatter(ax=ax, color="red", s=20, label="promedio cada 10 min")
ax.set_xlim(-0.3, 0.3)
plt.show()
```

**Lo que deberías ver.** Una nube gris ancha y, encima, los puntos rojos formando una **U** clara: un escalón de unos 250 ppm entre −0,06 y +0,06 día. Los cinco tránsitos, invisibles uno por uno, sumados se convierten en una señal nítida. Es la $\sqrt{N}$ de la lección M1 en acción.

Compara la forma con la lección [M2](m2-transit-physics.md): rampas cortas y fondo ancho. Nada de V.

## Paso 7. Tres pruebas de vetting a mano

```python
stats = bls.compute_stats(period=P, duration=dur, transit_time=t0)
print("tránsitos:", stats["transit_times"])
print("puntos por tránsito:", stats["per_transit_count"])
print("impar:", stats["depth_odd"], "par:", stats["depth_even"])
print("en fase 0,5:", stats["depth_phased"])
print("si el período fuera P/2:", stats["depth_half"])

# Búsqueda de una segunda señal: enmascara los tránsitos y ejecuta el BLS de nuevo.
mascara = bls.get_transit_mask(period=P, transit_time=t0, duration=2 * dur)
resto = plana[~mascara]
bls2 = resto.to_periodogram(method="bls", period=periodos, duration=duracoes)
destaque2 = (bls2.max_power - np.mean(bls2.power)) / np.std(bls2.power)
print(f"2.ª señal: P = {bls2.period_at_max_power:.3f}, "
      f"{bls2.depth_at_max_power.value * 1e6:.0f} ppm, realce {destaque2:.1f}")
```

**Lo que deberías ver.** Las profundidades salen como pares (valor, error) en fracción del brillo: `0.00022391` quiere decir 224 ppm.

- Cinco tránsitos (1325,51; 1331,77; 1338,04; 1344,31; 1350,57), con 81 a 87 puntos cada uno.
- Impar: 224 ± 7 ppm. Par: 231 ± 6 ppm. **Iguales dentro del error.**
- Fase 0,5: −10 ± 5 ppm. **Ningún eclipse secundario.**
- Profundidad con P/2: 126 ppm, la mitad, como se prevé para un alias (lección M3).
- Segunda señal: algo cerca de 7 d con 37 ppm y realce de unos 4. **Nada.** Solo un planeta transita en el sector 1.

Acabas de hacer, con tus propias manos, las pruebas `odd_even`, `secondary` y la búsqueda iterativa de PlanetHunter.

!!! example "Ejercicio 1"
    Calcula la significancia de la diferencia impar/par, en sigmas, como lo hace la prueba `odd_even`. ¿La reprobaría?

    ??? success "Ver respuesta"
        Diferencia: 231 − 224 = 7 ppm. Error combinado: $\sqrt{7^2 + 6^2} = \sqrt{85} \approx 9{,}2$ ppm. Significancia: 7/9,2 ≈ **0,8 sigma**.

        La prueba reprueba a partir de 3 sigma y veta a partir de 5. Pasa con holgura. Los tránsitos impares y pares son iguales, como se espera de un planeta.

!!! example "Ejercicio 2"
    Usa la profundidad y el radio de la estrella para estimar el radio de Pi Men c en radios terrestres. Haz la cuenta dos veces: con la profundidad del BLS (228 ppm) y con la del trapecio de PlanetHunter (272 ppm). Dato: 1 R☉ = 109,1 R⊕.

    ??? success "Ver respuesta"
        $R_p = \sqrt{\delta} \times R_\star \times 109{,}1$.

        Con 228 ppm: $\sqrt{0{,}000228} = 0{,}0151$. $0{,}0151 \times 1{,}149 \times 109{,}1 \approx$ **1,9 R⊕**.

        Con 272 ppm: $\sqrt{0{,}000272} = 0{,}0165$. $0{,}0165 \times 1{,}149 \times 109{,}1 \approx$ **2,1 R⊕**, el valor que aparece en la prueba `radius` de PlanetHunter.

        La diferencia viene del modelo: la caja promedia junto con las rampas y subestima la profundidad (lección M2). Un error del 20 % en la profundidad se convierte en un 10 % en el radio, porque el radio va con la raíz.

## Paso 8. Comparar con PlanetHunter

Ahora ejecuta el mismo objetivo en la herramienta, solo con el sector 1:

```bash
uv run planethunter run-target 261136679 --sectors 1
```

El comando descarga el sector, ejecuta la búsqueda (TLS con las variantes de detrending), el crossmatch y el vetting básico, e imprime el `run_id`, una tabla de señales con el `signal_id` y la ruta del dossier de cada señal fuerte. Con los espejos de catálogos actualizados, la señal de 6,27 d debería aparecer como `KNOWN_PLANET`, emparejada con Pi Men c. Si aparece un aviso de espejos desactualizados (`` WARNING: mirrors missing or stale; run `planethunter mirrors sync`. ``), ejecuta antes `uv run planethunter mirrors sync`.

!!! warning "No olvides el `--sectors 1`"
    Sin él, el comando descarga **todos** los sectores de la estrella (más de veinte) y hace una búsqueda multisector. Tarda mucho más y los números cambian (más tránsitos, SNR mayor). Atención: los sectores que ya descargaste antes entran en la búsqueda incluso con `--sectors 1`.

Las últimas líneas de la salida muestran el dossier de cada señal fuerte, por ejemplo `dossier for signal 1234: data/dossiers/tic261136679_sig1234.html`. Ábrelo en el navegador. Para generarlo de nuevo después, usa `uv run planethunter dossier <signal_id>`.

### Qué esperar

Ejecutamos el código de búsqueda y de vetting de PlanetHunter sobre el sector 1 de Pi Mensae el 2026-10-09. La tabla lo compara con lo que obtuviste en esta lección:

| | Lightkurve (esta lección) | PlanetHunter |
|---|---|---|
| Limpieza | NaN y puntos 4σ por encima | máscara de calidad, 4σ por encima antes y después del aplanado |
| Aplanado | Savitzky-Golay, 1 d | biweight (wotan), 1,0 d, segmentos separados en los huecos |
| Búsqueda | BLS, 1 a 15 d, 6 duraciones | TLS, 0,5 a ~25 d (0,9 × duración de los datos), grilla fina, puntos agrupados en 10 min |
| Período | 6,266 d | 6,269 d |
| Instante del 1.er tránsito (BTJD) | 1325,507 | 1325,503 |
| Duración | 2,9 h (valor de la grilla) | 3,08 h (TLS); 3,11 h (trapecio) |
| Profundidad | 228 ppm (caja) | 287 ppm (TLS); 272 ppm (trapecio) |
| Fuerza del pico | realce 12,9 | SDE 19,0 |
| SNR | ~37 (cuenta de la lección M1) | 33,6 |
| Tránsitos | 5 | 5 |
| Impar / par | 224 / 231 ppm | 284 / 259 ppm (1,1σ) |
| Fase 0,5 | −10 ppm | −9 ppm |

El vetting básico completo de PlanetHunter dio **score 1,0, PASS_BASIC**: radio 2,1 R⊕; duración 3,11 h contra 3,79 h prevista (razón 0,82, lección M2); $\tau/T_{14}$ = 0,11 (forma de U); centroide con fuente implícita a 0,15 píxel del objetivo; 40 % de los tránsitos en bordes de segmento (2 de 5, por debajo del límite del 50 %); consistencia entre tránsitos con p = 0,62.

Los números de tu dossier pueden diferir un poco si cambian la versión del pipeline o los parámetros del TIC. Desde el 2026-10-10 la búsqueda también cubre otro rango de períodos (desde unos 0,2–0,3 d; antes, el propio valor por defecto del TLS la detenía en realidad en la mitad del intervalo de datos, unos 14 d aquí), y PlanetHunter mide él mismo la duración y el SNR en lugar de copiarlos del TLS (lección [M3](m3-periodograms.md)), así que esas dos filas van a cambiar un poco en una corrida nueva. La sección **Provenance** (procedencia) del dossier registra el `run_id`, la versión y la ventana usada en cada sector.

!!! tip "En la herramienta"
    Cada paso de esta lección tiene un equivalente en el código: limpieza y aplanado en `src/planethunter/preprocess/clean.py`; búsqueda en `src/planethunter/search/tls.py`; impar/par, fase 0,5, forma y las demás pruebas en `src/planethunter/vetting/basic.py`. En el dossier, el gráfico **"Folded transit"** (tránsito plegado) corresponde a tu paso 6, y el panel **"Odd, even and secondary"** (impar, par y secundario) al paso 7.

!!! example "Ejercicio 3"
    En la tabla, PlanetHunter tiene SDE 19,0 y tu "realce" dio 12,9. Menciona dos razones de la diferencia.

    ??? success "Ver respuesta"
        1. **Modelo.** TLS usa un tránsito realista, con rampas y oscurecimiento del limbo; BLS usa una caja. El mejor modelo ajusta más de la señal y el pico crece.
        2. **Definición y grilla.** El SDE de TLS se calcula sobre otra magnitud (el SR, normalizado) y sobre otra grilla de períodos (de 0,5 a ~25 d, con la densidad elegida por `oversampling_factor`). Tu realce usa la potencia del BLS en 1 a 15 d. La media y la desviación estándar del periodograma cambian con la grilla.

        También cuentan detalles de limpieza (filtro biweight, segmentos separados en los huecos) y el agrupamiento en 10 minutos. Los dos números no son directamente comparables; lo que importa es que los dos métodos encuentran el mismo período, con holgura.

!!! example "Ejercicio 4 (desafío)"
    Elige otro sector de la lista del paso 1 y repite la lección entera cambiando `sector=1`. ¿Coinciden el período y la profundidad? ¿Cuántos tránsitos ves?

    ??? success "Ver respuesta"
        El período debería coincidir con 6,27 d dentro de la incertidumbre (que, con un solo sector, es de algunas milésimas de día), y la profundidad con la del sector 1 dentro de algunas decenas de ppm. El número de tránsitos depende de dónde caen los huecos de ese sector: con ~27 días y período de 6,27 d, espera 4 o 5. Si algún sector da un resultado muy distinto, mira la curva: huecos mayores, tramos ruidosos o un tránsito en el borde explican la mayoría de los casos. Es el mismo razonamiento de la prueba de otros sectores del vetting profundo.

## Checklist de la lección

- [ ] Busqué y descargué la curva del sector 1 de Pi Mensae con Lightkurve.
- [ ] Grafiqué la curva cruda y localicé el hueco de la mitad del sector.
- [ ] Limpié solo hacia arriba y aplané con ventana de 1 día, sabiendo por qué.
- [ ] Ejecuté el BLS y encontré 6,27 d; identifiqué al menos dos alias en el periodograma.
- [ ] Plegué la curva y vi el tránsito en U.
- [ ] Hice a mano las pruebas impar/par, fase 0,5 y la búsqueda de una segunda señal.
- [ ] Ejecuté `planethunter run-target 261136679 --sectors 1`, abrí el dossier generado y lo comparé con la tabla de esta lección.

## Para ir más allá

- Tutoriales oficiales de Lightkurve ([lightkurve.github.io](https://lightkurve.github.io/lightkurve/)): empieza por "LightCurve objects" y después por el tutorial de identificación de señales de tránsito con BLS.
- Página de Pi Mensae en ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/target.php?id=261136679)): parámetros de la estrella, TOIs y notas de la comunidad.
- Huang et al. (2018), *The Astrophysical Journal Letters* 868, L39: el artículo del anuncio de Pi Men c con datos de TESS. Mira las figuras y compáralas con tu tránsito plegado.
- Documentación introductoria de NumPy ([numpy.org](https://numpy.org/doc/stable/user/absolute_beginners.html)) y de pandas ([pandas.pydata.org](https://pandas.pydata.org/docs/getting_started/index.html)), si algún tramo del código te pareció extraño.
