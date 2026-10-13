# M3. Periodogramas: cómo se encuentra un período

<p class="meta">Nivel intermedio · semanas 5–6 · unas 10 horas</p>

!!! abstract "En esta lección vas a aprender"
    - La idea del BLS (Box Least Squares) y qué cambia el TLS.
    - Qué es el SDE y por qué el límite es 9.
    - Cómo se arma la grilla de períodos, y por qué sus límites cambiaron el recall.
    - Por qué aparecen alias (P/2, 2P, P/3) y cómo PlanetHunter corrige el caso P/3.
    - Cómo funciona la búsqueda iterativa con enmascaramiento.
    - Por qué la ventana de detrending decide lo que puedes encontrar, con números medidos.
    - El efecto de los huecos y los bordes de segmento en los datos de TESS.

## El problema

Tienes 27 días de brillo medido cada 2 minutos, unos 18 000 puntos. En algún lugar hay caídas de 300 ppm, con un ruido de 130 ppm por punto. No sabes el período, ni cuándo fue el primer tránsito, ni cuánto dura cada uno.

La solución es fuerza bruta organizada: **probar todas las combinaciones** y medir cuál explica mejor los datos. El gráfico de "qué tan bien explica cada período los datos" es el **periodograma**.

## BLS: buscar cajas

El **BLS** (*Box Least Squares*, Kovács, Zucker & Mazeh, 2002) modela el tránsito como una **caja**: brillo constante afuera, brillo constante y más bajo adentro.

Para cada período $P$ de la grilla:

1. **Pliega** la curva: calcula la fase de cada punto, el resto de dividir el tiempo entre $P$. Si $P$ es correcto, todos los tránsitos caen uno encima del otro.
2. Para cada **posición** de la caja en la fase y cada **duración** de la grilla, compara la media de los puntos dentro de la caja con la media de afuera.
3. Calcula cuánto reduce el modelo de caja el error cuadrático respecto de una línea recta. Esa reducción es la **potencia** del BLS en ese período.

El periodograma guarda, para cada período, la mejor potencia entre todas las posiciones y duraciones. El pico más alto es el candidato a período.

Analogía: es como buscar un golpe de tambor en medio de un ruido. Pruebas varios ritmos y, para cada uno, superpones los compases. En el ritmo correcto, los golpes se suman y se destacan; en los incorrectos, se dispersan.

## TLS: buscar tránsitos de verdad

El **TLS** (*Transit Least Squares*, Hippke & Heller, 2019) hace la misma búsqueda, pero cambia la caja por un **modelo de tránsito realista**: rampas de entrada y salida, fondo redondeado por el oscurecimiento del limbo (lección [M2](m2-transit-physics.md)). El modelo se ajusta a la estrella: PlanetHunter le pasa el radio y la masa del TIC.

¿Por qué ayuda? La caja se equivoca en las rampas y en el fondo. Para tránsitos fuertes, da igual. Para planetas **pequeños**, cerca del límite de detección, ese error se come una parte de la señal. El modelo realista recupera esa parte, y los autores muestran una ganancia de sensibilidad justamente para planetas pequeños. A cambio, el TLS es más lento.

PlanetHunter usa TLS 2.0 (backend `fused-pl`, un hilo por objetivo, en paralelo por estrella).

## SDE: ¿el pico se destaca?

El TLS calcula, para cada período, un valor de calidad del ajuste (llamado SR). El **SDE** (*Signal Detection Efficiency*) mide cuánto se destaca el pico más alto del resto:

$$
\text{SDE} = \frac{\text{SR}_\text{pico} - \overline{\text{SR}}}{\sigma_\text{SR}}
$$

Es el número de desviaciones estándar que el pico está por encima de la media del periodograma. Un SDE alto dice: "este período es mucho mejor que todos los demás".

**¿Por qué 9?** Hippke & Heller (2019) simularon curvas con solo ruido blanco y midieron con qué frecuencia el pico más alto superaba cada SDE: un SDE de 7 da una probabilidad de falsa alarma (FAP) de alrededor del 1 %. La documentación de TLS repite la prueba con más curvas: un SDE de 9,1 da alrededor de $10^{-4}$, 1 de cada 10 000 curvas de ruido puro. Es el `sde_min: 9.0` de `config/thresholds.yaml`. Las curvas reales también tienen ruido rojo, así que la falsa alarma real es mayor que estos números.

El sistema también guarda señales con SDE entre 7 y 9 (`sde_keep: 7.0`), pero no se convierten en candidatos. Sirven como ejemplos débiles para el futuro clasificador de aprendizaje automático.

!!! note "SDE y SNR miden cosas distintas"
    El SDE compara el pico con el **resto del periodograma**: "¿este período se destaca?". El SNR compara la profundidad con el **ruido de la curva**: "¿la caída es grande?" (lección [M1](m1-statistics-for-signals.md)). Una señal puede tener SDE alto y SNR bajo, o al revés. PlanetHunter exige los dos: SDE ≥ 9 **y** SNR ≥ 7,1.

## La grilla de períodos

El TLS no prueba infinitos períodos. Prueba una **grilla**, y la grilla decide qué se puede encontrar. Los parámetros del proyecto:

| Parámetro | Valor | Por qué |
|---|---|---|
| `period_min_days` | 0,2 d | Piso absoluto de la grilla |
| `roche_min_a_rstar` | 2,0 | El período más corto probado es aquel en el que la órbita está a 2 radios estelares del centro de la estrella, como en el pipeline de vista rápida del TESS (QLP); cerca de 0,2 a 0,3 d para una estrella como el Sol |
| `period_max_fraction_of_span` | 0,9 × duración de los datos | Dos tránsitos alcanzan para definir un período |
| `period_max_days` | 40 d | Tope absoluto (ver abajo) |
| `oversampling_factor` | 3 | Densidad de la grilla; mayor = más lento y más fino |
| `duration_grid_step` | 1,1 | Cada duración probada es un 10 % mayor que la anterior |
| `bin_minutes` | 10 | Junta puntos de 2 min en bloques de 10 min para acelerar; se pierde poco para P > 1 d |
| `limb_darkening` | `tess` | El modelo de tránsito usa el oscurecimiento de borde de la banda de TESS, elegido según la temperatura y la gravedad superficial de la estrella |

Cada uno de estos números tiene una historia medida en el benchmark del sector 69:

- **Límites estelares.** Al principio, la grilla de duraciones solo aceptaba estrellas de hasta ±30 % del radio y la masa del TIC. Los tránsitos más cortos que el central (b alto, radio del TIC equivocado) quedaban afuera. TOI 196.01, 347.01, 386.01 y 2339.01 desaparecían; con límites amplios, aparecen con SDE de 8,6 a 16,8.
- **Período mínimo y límite de Roche.** El TLS calcula el período más corto posible a partir del radio del modelo (un planeta no puede orbitar dentro de la estrella). Con el radio del TIC de 4,06 R☉, la grilla empezaba en 4,15 d, y TOI 196.01, con P = 1,16 d, desaparecía. Corrección: el modelo usa como máximo 1,5 R☉ y 1,5 M☉. Una auditoría posterior (2026-10-10) encontró un segundo límite: el TLS supone una órbita de al menos 3 radios estelares, así que el período más corto probado era en realidad de 0,6 a 1,0 d, y 13 de los 505 TOIs del sector 69 quedaban fuera de la grilla. Hoy el mínimo es de 2 radios estelares (como en el QLP), con un piso de 0,2 d.
- **El período máximo real.** El TLS, por defecto, solo prueba períodos con espacio para 2 tránsitos, así que el tope real era la mitad del intervalo de datos y `period_max_fraction_of_span` no hacía nada. Ahora el proyecto deja que el TLS llegue hasta el intervalo completo y aplica él mismo el límite de 0,9; el vetting sigue exigiendo 2 tránsitos.
- **Tope de 40 días.** En la búsqueda con varios sectores separados por años (datos que cubren ~800 días), la grilla se volvía enorme y generaba alias espurios de 26 a 64 días con 1 o 2 tránsitos.

Resultado acumulado de los cambios hasta el 2026-10-09: el recall pasó de 84,4 % a 91,1 % en los TOIs detectables. Los cambios del 2026-10-10 todavía necesitan una nueva medición.

### Lo que PlanetHunter mide después del TLS

El TLS da el período, el instante de tránsito, la profundidad y el SDE. Otros cuatro números los mide de nuevo el proyecto, porque todos los pasos posteriores dependen de ellos:

- **Duración (T14).** El TLS multiplica la duración por la fracción del tiempo que tiene datos (el factor de llenado). En un sector es un poco menor que 1 (0,86 en el sector 69), así que las duraciones salían cerca de un 15 % más cortas. Con dos sectores separados por años es diminuto: un tránsito de 3 h salía como 0,23 h. El proyecto divide por el factor de llenado y guarda la T14 física.
- **SNR.** Medido sobre la curva aplanada, contando como "en tránsito" los puntos a menos de media T14 del centro del tránsito, y con un ruido robusto (MAD) calculado con los puntos de afuera.
- **S/N_pink.** El SNR con el ruido rojo incluido (lección [M1](m1-statistics-for-signals.md)), guardado para el vetting.
- **Número de tránsitos.** Una época solo cuenta si al menos el 50 % de su tiempo de tránsito esperado tiene datos. Un tránsito perdido casi todo en un hueco ya no cuenta.

La auditoría encontró por qué esto importa: la T14 encogida se usaba en todo lo que venía después (el SNR, el enmascaramiento de la búsqueda iterativa, las ventanas de las pruebas de vetting), así que un solo error se propagaba por todo el pipeline.

## Alias: los picos fantasma

Un **alias** es un período incorrecto que es un múltiplo o una fracción simple del verdadero. ¿Por qué aparecen?

- **En 2P**, pliegas la curva con el doble del período. La mitad de los tránsitos cae en la fase 0 y la otra mitad en la fase 0,5. La caja en fase 0 sigue atrapando tránsitos de verdad, con la mitad de los puntos. Un pico más bajo, pero pico al fin.
- **En P/2**, cada "tránsito" previsto alterna entre uno real y uno vacío. La profundidad media cae a la mitad.
- **En P/3, 3P/2, 2P/3**, la misma lógica, con fracciones distintas.

Ejemplo medido en la lección [M4](m4-tess-data-in-python.md), con el BLS de Lightkurve en Pi Men c (sector 1): pico principal en 6,27 d con potencia 1 400; picos menores en 12,53 d (2P, potencia 857), 3,13 d (P/2, potencia 746), además de 9,4 d (3P/2) y 2,09 d (P/3). En el período P/2, la profundidad calculada baja de 228 a 126 ppm: aproximadamente la mitad, como predice la explicación.

!!! warning "Binaria con período 2P"
    Una binaria eclipsante con dos estrellas parecidas tiene dos eclipses por órbita. La búsqueda encuentra el período P entre eclipses consecutivos, que es la **mitad** del período orbital verdadero. Por eso la prueba `odd_even` compara los tránsitos impares con los pares: si las estrellas son un poco distintas, los eclipses alternados tendrán profundidades distintas.

### El caso P/3 y `refine_alias`

Con pocos tránsitos y huecos en los datos, el TLS a veces prefiere un tercio del período verdadero. Imagina un planeta de 12,6 d en un sector de 27 d: dos tránsitos. En P/3 = 4,2 d, el TLS predice seis tránsitos. Dos son reales; los otros cuatro caen en huecos o se diluyen en el promedio. El pico en P/3 puede ganar.

Eso fue exactamente lo que pasó en el sector 69: **TOI 899.01, 924.01 y 3262.01** (períodos de 12 a 13 días) salían con unos 4,2 d.

La corrección, la función `refine_alias` en `search/tls.py`, hace una prueba directa para k = 3 y k = 2:

1. Divide las épocas previstas por P en dos grupos: **A**, las que también predeciría kP, y **B**, las que solo existen en P.
2. Mide la profundidad en cada grupo.
3. Acepta kP si el grupo A muestra tránsito (más de 3 sigma), el grupo B **tiene datos** pero no muestra tránsito (menos de 3 sigma), y la profundidad de A es más de 3 veces la de B.

En palabras: si los tránsitos "extra" que predice P caen en datos buenos y no aparecen, el período verdadero es el mayor. Después, el SNR se mide de nuevo solo con los tránsitos del período verdadero (antes se quedaba demasiado bajo, por un factor de hasta 0,58). El dossier muestra el resultado en el campo "Applied alias factor" (factor de alias aplicado).

## Búsqueda iterativa con enmascaramiento

Una estrella puede tener más de un planeta. El TLS solo devuelve el pico más fuerte. Solución:

1. Busca y encuentra la señal más fuerte.
2. **Borra** (enmascara) los puntos de sus tránsitos, en una ventana de 2 duraciones (`mask_width_durations: 2.0`, usando la T14 física).
3. Busca de nuevo en la curva que quedó.
4. Repite hasta 3 veces (`max_signals_per_target: 3`) o hasta que el SDE baje de 7.

Para Pi Men c, después de enmascarar los 5 tránsitos, la segunda búsqueda del BLS no encuentra nada relevante (el mejor pico tiene 37 ppm y poco destaque). Es lo esperado: en el sector 1, solo transita Pi Men c.

!!! tip "En la herramienta"
    La búsqueda está en `search_periodic` (`src/planethunter/search/tls.py`). Cada señal sale con `iteration` (0, 1, 2), `sde`, `snr`, `n_transits`, `alias_factor` y la ventana de detrending usada. En el vetting, la prueba `independence` verifica si una señal sobrevive cuando se enmascaran las señales más fuertes de la misma estrella: en el sector 69, la señal 1601 (11,95 d) estaba reaprovechando los eclipses de la señal 1600 (6,75 d) y fue vetada.

## Detrending: la ventana que decide

Antes de la búsqueda, hay que **aplanar** la curva: se quita la variación lenta de la estrella (rotación, manchas) para que los tránsitos queden visibles. PlanetHunter usa el filtro **biweight** de la biblioteca wotan: para cada punto, estima la tendencia local en una ventana de ancho fijo, de forma robusta (ignora puntos atípicos como los del tránsito), y divide la curva entre ella.

El dilema: si la ventana es **corta**, el filtro sigue también al tránsito y se lo "come". Si es **larga**, deja restos de la variabilidad rápida de la estrella.

Medido por el proyecto con un tránsito sintético en forma de caja de 1 500 ppm, sin variabilidad:

| Ventana | Tránsito de 3 h | Tránsito de 5 h |
|---|---|---|
| 0,5 d | pierde 8 % de la profundidad | pierde **40 %** |
| 1,0 d | pierde 0 % | pierde 6 % |

La regla práctica es una ventana de unas 3 veces la duración del tránsito más largo que se busca. El valor por defecto es **1,0 d** (`window_length_days`). Los tránsitos de 5 a 6 h aparecen en períodos de 20 a 40 d en una estrella como el Sol (lección M2) o en períodos más cortos en estrellas más grandes.

### Variantes de detrending

Una sola ventana no sirve para todas las estrellas. El sistema mide la variabilidad que queda después del aplanado con la razón entre la dispersión de la curva y el ruido punto a punto, ambos medidos con la MAD (lección M1). La MAD importa: con la desviación estándar, un tránsito profundo inflaba la razón por sí solo y empujaba al sistema hacia las ventanas cortas, las que se comen los tránsitos. Si pasa de 1,2 (`red_noise_max`), rehace el detrending con ventanas de 0,5 d y después 0,3 d (`fallback_windows_days`). Y busca en **las dos** versiones, la por defecto y la adaptativa, juntando las señales (gana la de mayor SDE cuando dos tienen el mismo período).

¿Por qué las dos? Dos casos reales del sector 69:

- **TOI 862.01** (5 092 ppm): la estrella varía rápido. Con una ventana de 1,0 d, la razón de ruido quedaba muy por encima de 1,2 y la señal desaparecía. Con 0,5 d, aparece con SDE 18.
- **TOI 190.01** (tránsito de 5,7 h): con una ventana de 0,3 d, la profundidad de 8 248 ppm se volvía 347 ppm. La ventana corta se comió el tránsito.

Solo con la ventana corta se pierde el segundo; solo con la larga, el primero. Buscar en las dos y juntar salvó a ambos.

### Aplanar de nuevo para el vetting

Una vez encontrada una señal, se conocen su duración y sus instantes de tránsito. El vetting entonces aplana de nuevo cada sector, con la ventana propia de ese sector en la búsqueda pero nunca más corta que 3 veces la T14, y con los tránsitos **enmascarados**: el filtro no los ve y traza la tendencia por encima de ellos (Hippke et al. 2019). Medido con un tránsito de 12 h: una ventana simple de 1,0 d conserva el 50 % de la profundidad; este aplanado con máscara conserva el 99 %. La misma curva alimenta las pruebas de vetting, el FPP y el dossier.

Dos cuidados más en la limpieza: eliminar puntos atípicos **solo hacia arriba** (`sigma_upper: 4.0`), nunca hacia abajo; y no recortar los bordes de los segmentos (`edge_cutoff_days: 0.0`), para conservar los eventos únicos cercanos a ellos.

!!! example "Ejercicio 1"
    Un candidato tiene tránsitos de 5 horas y una profundidad verdadera de 1 500 ppm. ¿Qué profundidad esperas medir con una ventana de 0,5 d? ¿Y con 1,0 d? Si el ruido da un SNR de 10 con la profundidad verdadera, ¿la señal pasaría el límite de SNR con la ventana de 0,5 d?

    ??? success "Ver respuesta"
        Con 0,5 d, pierde 40 %: se miden unas 1 500 × 0,6 = **900 ppm**. Con 1,0 d, pierde 6 %: unas **1 410 ppm**.

        El SNR es proporcional a la profundidad. Con 0,5 d: 10 × 0,6 = **6,0**, por debajo de 7,1. La compuerta `snr` vetaría la señal. Con 1,0 d: 10 × 0,94 = 9,4, pasa. La elección de la ventana, por sí sola, decide si este planeta se encuentra.

## Huecos y bordes de segmento

Los datos de TESS no son continuos. Un sector de ~27 días tiene un **hueco** en el medio para enviar datos a la Tierra, y a veces otros por problemas. Cada tramo continuo es un **segmento**.

Los huecos estorban de tres maneras:

1. **Tránsitos perdidos.** Un tránsito que cae en el hueco no existe en los datos. Con un período largo, esto puede dejar un solo tránsito, y la señal queda vetada por `n_transits`.
2. **Alias.** El hueco es lo que permite el caso P/3: los tránsitos "extra" caen en él y nadie desmiente el período corto.
3. **Bordes.** En los extremos de cada segmento, el detrending tiene datos de un solo lado y puede crear **rampas** artificiales. El proyecto lo midió: ruido puro, con una variabilidad de 2 000 ppm, generó un SDE de ~10 en un período igual a una órbita de TESS, con el "evento" a 0,07 d del borde.

Por eso cada señal sale con `edge_transit_fraction`: la fracción de los tránsitos con datos cuyo centro está a menos de 0,5 d (`edge_window_days`) de un borde de segmento. Las señales con más del 50 % de los tránsitos en bordes (`max_edge_transit_fraction: 0.5`) no se convierten en candidatos, y la prueba `edges_dumps` del vetting reprueba por el mismo criterio (o si más del 50 % cae cerca de un ajuste de apuntado, el *momentum dump*).

!!! example "Ejercicio 2"
    Pi Men c en el sector 1 tuvo 5 tránsitos, en los instantes BTJD 1325,50; 1331,77; 1338,04; 1344,31 y 1350,57. Los datos empiezan en 1325,30, terminan en 1353,18 y hay un hueco entre 1338,52 y 1339,66. Calcula `edge_transit_fraction`. ¿La señal quedaría bloqueada?

    ??? success "Ver respuesta"
        Distancia de cada tránsito al borde más cercano:

        - 1325,50: a 0,20 d del inicio (1325,30). **En borde.**
        - 1331,77: lejos de cualquier borde.
        - 1338,04: a unos 0,48 d del inicio del hueco (1338,52). **En borde.**
        - 1344,31 y 1350,57: lejos de los bordes (el final de los datos está en 1353,18).

        Son 2 de 5: **edge_transit_fraction = 0,4**. Es exactamente el valor que calcula PlanetHunter para esta señal. Como 0,4 ≤ 0,5, la señal **no** queda bloqueada, y la prueba `edges_dumps` pasa.

!!! tip "En la herramienta"
    En el dossier, la sección **"Light curve"** (curva de luz) muestra los tránsitos con líneas rojas y los ajustes del telescopio con líneas azules punteadas. Los tránsitos pegados a un borde de segmento o a una línea azul son una señal de alerta. La nota de la prueba `edges_dumps` da las dos fracciones: "at momentum dump X%, at segment edge Y%" (en momentum dump X %, en borde de segmento Y %). La sección **Provenance** (proveniencia) muestra la ventana de detrending usada.

## Checklist de la lección

- [ ] Sé explicar el BLS en tres pasos (plegar, probar cajas, medir la mejora).
- [ ] Sé qué cambia el TLS y por qué eso ayuda a los planetas pequeños.
- [ ] Sé definir el SDE y decir de dónde viene el límite de 9.
- [ ] Sé explicar por qué aparecen picos en 2P y P/2, y qué hace `refine_alias` con P/3.
- [ ] Sé describir la búsqueda iterativa y la prueba `independence`.
- [ ] Sé explicar el dilema de la ventana de detrending con los números medidos (40 % y 6 %).
- [ ] Sé calcular `edge_transit_fraction` para una lista de tránsitos.
- [ ] Encontré en un dossier el factor de alias y la ventana de detrending.

## Para ir más allá

- Documentación de Astropy sobre Box Least Squares ([docs.astropy.org](https://docs.astropy.org/en/stable/timeseries/bls.html)): ejemplos cortos de BLS en Python.
- Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39 (TLS), también en arXiv ([arXiv:1901.02015](https://arxiv.org/abs/1901.02015)). Lee la introducción y las figuras; ahí están la comparación con el BLS y la calibración del SDE.
- Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. El artículo original del BLS. Queda para el nivel avanzado ([A1](../advanced/a1-detection-algorithms.md)), pero la primera figura ya vale la visita.
- Hippke et al. (2019), *The Astronomical Journal* 158, 143: el artículo de wotan, con la comparación de filtros de detrending.
- En el repositorio, `docs/benchmarks/2026-10-09-s0069-history.md`: la tabla "Causes found and fixed" (causas encontradas y corregidas) es el resumen de esta lección en forma de diagnóstico.
