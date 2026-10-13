# M1. Estadística para señales

<p class="meta">Nivel intermedio · semanas 1–3 · unas 15 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Media, mediana, desviación estándar y MAD, y por qué PlanetHunter prefiere la mediana.
    - Qué significa "3 sigma" y por qué el sistema exige un SNR de 7,1.
    - Por qué la relación señal-ruido crece con la raíz del número de puntos.
    - La diferencia entre ruido blanco y ruido rojo, y cómo el proyecto mide el rojo por bloques.
    - Cómo la prueba de chi-cuadrado verifica si varios tránsitos "concuerdan".
    - Cómo leer el intervalo de confianza de un recall, como 123/135.

## Por qué estadística

Toda medición de brillo de TESS viene con un error. Si mides la misma estrella dos veces, con dos minutos de diferencia, los números no serán iguales. Esa fluctuación es el **ruido**.

Un tránsito de Pi Men c baja el brillo en unas 300 ppm. El ruido de cada punto de esa estrella es de unas 130 ppm. O sea: en cualquier punto aislado, el tránsito es solo dos veces mayor que la fluctuación normal. Aun así, el planeta se detecta con holgura. La estadística explica cómo.

La pregunta central de esta lección es siempre la misma: **¿esta caída es real o puede ser casualidad?**

## Media, mediana y desviación estándar

Imagina cinco mediciones de brillo normalizado (1,0 = brillo normal), en ppm de desviación:

| Medición | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Desviación (ppm) | −120 | +80 | +10 | −40 | +3 000 |

La quinta es un **flare** (una fulguración, una explosión en la superficie de la estrella) o un rayo cósmico.

- **Media**: la suma dividida entre la cantidad. $(-120 + 80 + 10 - 40 + 3000)/5 = 586$ ppm. Un solo punto malo arrastró la media lejos de todo lo demás.
- **Mediana**: ordena los valores y toma el del medio. Ordenados: −120, −40, 10, 80, 3 000. Mediana = 10 ppm. El flare no cambia nada.
- **Desviación estándar** ($\sigma$): el tamaño típico de la fluctuación alrededor de la media. Es la raíz de la media de los cuadrados de las diferencias. También es muy sensible a los puntos extremos.

La mediana es **robusta**: aguanta puntos absurdos sin moverse. Por eso PlanetHunter usa la mediana para definir el nivel de brillo "normal" fuera del tránsito.

### MAD: la desviación estándar robusta

La **MAD** (*median absolute deviation*, desviación absoluta mediana) hace con la desviación estándar lo que la mediana hace con la media:

1. Calcula la mediana de los datos.
2. Calcula la distancia de cada punto a esa mediana.
3. Toma la mediana de esas distancias.

Para datos con distribución normal, $\sigma \approx 1{,}4826 \times \text{MAD}$. Esa es exactamente la cuenta que usa el vetting (función `_robust_sigma` en `vetting/basic.py`).

La MAD también decide qué puntos se descartan en la limpieza. PlanetHunter elimina los puntos **por encima** de mediana + 4 × (1,4826 × MAD), el `sigma_upper: 4.0` de `config/thresholds.yaml`. Nunca elimina hacia abajo: un tránsito es justamente una secuencia de puntos por debajo de lo normal.

!!! example "Ejercicio 1"
    Calcula la MAD y la sigma robusta de las cinco mediciones de la tabla de arriba (−120, +80, +10, −40, +3 000 ppm). Compárala con la desviación estándar común (muestral), que es de unas 1 350 ppm.

    ??? success "Ver respuesta"
        Mediana = 10 ppm. Distancias a 10: 130, 70, 0, 50, 2 990. Ordenadas: 0, 50, 70, 130, 2 990. Su mediana: **MAD = 70 ppm**.

        Sigma robusta = 1,4826 × 70 ≈ **104 ppm**.

        La desviación estándar común da unas 1 350 ppm, trece veces más, por culpa de un solo punto. Con la sigma robusta, el flare queda a (3 000 − 10)/104 ≈ 29 sigmas de la mediana y lo eliminaría el corte de 4 sigmas.

## La distribución normal y la "sigma"

Cuando el ruido viene de muchas causas pequeñas e independientes, los valores se distribuyen en una **curva normal** (o gaussiana), la famosa campana. Tiene una propiedad útil: la probabilidad de que un valor caiga lejos de la media depende solo de a cuántas $\sigma$ está.

| Distancia | Probabilidad de que el ruido puro supere ese valor (solo hacia abajo) |
|---|---|
| 1 σ | 16 % |
| 2 σ | 2,3 % |
| 3 σ | 0,13 % (1 en 740) |
| 5 σ | 0,000029 % (1 en 3,5 millones) |
| 7,1 σ | cerca de 6 × 10⁻¹³ (1 en 1,6 billones) |

Decir que una señal tiene "3 sigma" es decir: si fuera solo ruido normal, un valor así aparecería 1 vez de cada 740.

### Por qué 3 sigma no alcanza: el efecto de mirar en todas partes

1 en 740 parece raro. Pero la búsqueda de PlanetHunter prueba miles de períodos y, para cada uno, miles de posiciones y duraciones de tránsito. Son millones de intentos por estrella, y hay unas 20 000 estrellas por sector. Con un millón de intentos, el ruido puro produce unas 1 350 "señales" de 3 sigma. Esto se llama **efecto de mirar en todas partes** (*look-elsewhere effect*).

El límite de **7,1 sigma** viene de la misión Kepler (Jenkins, Caldwell & Borucki, 2002). Se eligió para que, en una búsqueda del tamaño de la de Kepler, el ruido blanco gaussiano produjera menos de una falsa alarma en total. TESS y PlanetHunter heredaron ese valor (`snr_min: 7.1`).

!!! warning "El ruido real no es normal"
    La tabla de arriba vale para un ruido gaussiano ideal. El ruido de verdad tiene colas más gruesas. El proyecto lo midió: al buscar una señal en un rango estrecho de períodos en estrellas **sin** señal (144 intentos), el SNR mediano fue 5,2, pero el 10 % de los intentos pasó de 19 y el 1 % pasó de 98. Por eso un SNR ≥ 7,1 es necesario, pero no suficiente. Para eso existe el vetting (la verificación).

## SNR y la raíz de N

La **relación señal-ruido** (SNR) compara el tamaño de la caída con la incertidumbre con que la mides.

La idea clave: **la media de N puntos independientes tiene un error de $\sigma/\sqrt{N}$**. Una medición aislada fluctúa $\sigma$. La media de 4 mediciones fluctúa $\sigma/2$. La de 100 mediciones, $\sigma/10$. El ruido se cancela en parte al sumar, porque unos puntos suben y otros bajan.

En un tránsito, medimos la profundidad como la media de los puntos dentro del tránsito menos el nivel normal. Entonces:

$$
\text{SNR} \approx \frac{\delta}{\sigma / \sqrt{N_\text{en tránsito}}} = \frac{\delta}{\sigma}\sqrt{N_\text{en tránsito}}
$$

donde $\delta$ es la profundidad y $\sigma$ el ruido de un punto.

### Ejemplo numérico: Pi Men c en el sector 1

Números medidos al hacer la lección [M4](m4-tess-data-in-python.md) con Lightkurve:

- profundidad media (modelo de caja): $\delta \approx 228$ ppm. Es menos que las ~300 ppm del fondo del tránsito, porque la caja promedia incluyendo los bordes inclinados; la lección [M2](m2-transit-physics.md) lo explica;
- ruido de un punto de 2 minutos, después del aplanado: $\sigma \approx 128$ ppm;
- duración del tránsito: unos 0,12 días, o sea, unos **86 puntos** de 2 minutos por tránsito;
- tránsitos en el sector: **5**, en total unos 430 puntos en tránsito.

Con un solo tránsito:

$$
\text{SNR}_1 = \frac{228}{128/\sqrt{86}} = \frac{228}{13{,}8} \approx 16{,}5
$$

Con los cinco:

$$
\text{SNR}_5 = \frac{228}{128/\sqrt{430}} = \frac{228}{6{,}17} \approx 37
$$

PlanetHunter mide el SNR con el mismo espíritu, sobre su propia curva aplanada, usando la duración real del tránsito y una estimación robusta del ruido (basada en la mediana). Su valor para esta señal es del mismo orden.

Fíjate en la consecuencia: **para duplicar el SNR necesitas cuatro veces más puntos**, o sea, cuatro veces más tránsitos. Por eso juntar sectores ayuda tanto con los planetas pequeños, y por eso un planeta de período largo, con 2 tránsitos en un sector, es difícil.

!!! example "Ejercicio 2"
    Una estrella hipotética tiene un ruido de 1 000 ppm por punto de 2 minutos. Un candidato tiene una profundidad de 500 ppm y tránsitos de 3 horas.

    a) ¿Cuál es el SNR de un solo tránsito?
    b) ¿Cuántos tránsitos hacen falta para llegar a un SNR de 7,1, suponiendo ruido blanco?

    ??? success "Ver respuesta"
        a) 3 horas = 180 minutos = 90 puntos de 2 minutos. Error de la media de un tránsito: $1000/\sqrt{90} = 105$ ppm. SNR = 500/105 ≈ **4,7**.

        b) Con $n$ tránsitos, SNR = $4{,}7\sqrt{n}$. Queremos $4{,}7\sqrt{n} \geq 7{,}1$, así que $\sqrt{n} \geq 1{,}51$ y $n \geq 2{,}3$. Hacen falta **3 tránsitos**. Con 2, el SNR queda en 6,7 y la señal la veta la compuerta `snr`.

## Ruido blanco y ruido rojo

La $\sqrt{N}$ solo funciona si cada punto fluctúa **independientemente** del vecino. Eso es **ruido blanco**: piensa en una llovizna, cada gota cae en un lugar al azar.

En la práctica también hay fluctuaciones que duran horas: la estrella pulsa, una mancha gira, el telescopio se balancea un poco, el detrending deja restos. Los puntos vecinos suben y bajan juntos. Eso es **ruido rojo** (o correlacionado). Piensa en las olas del mar: no sirve de nada promediar diez mediciones seguidas si las diez están en la misma cresta.

Con ruido rojo, la media de N puntos vecinos **no** baja como $\sigma/\sqrt{N}$. Deja de bajar en cierto nivel. Y una ondulación de 2 horas, de 200 ppm, se parece mucho a un tránsito.

### Cómo medirlo: el método de bloques de Pont et al. (2006)

Pont, Zucker & Queloz (2006) propusieron un modelo sencillo:

$$
\sigma_N^2 = \frac{\sigma_w^2}{N} + \sigma_r^2
$$

El primer término es el ruido blanco, que disminuye con N. El segundo, $\sigma_r$, es el ruido rojo, que **no** disminuye. Para N grande, domina.

La forma práctica de medirlo es empírica:

1. Toma la curva de luz **fuera** de los tránsitos.
2. Córtala en bloques de N puntos consecutivos (N = número de puntos de un tránsito).
3. Calcula la media de cada bloque.
4. Mide la desviación estándar de esas medias.

Si el ruido fuera blanco, esa desviación sería $\sigma/\sqrt{N}$. Si da más, hay ruido rojo, y ese valor mayor es el que debes usar como error.

!!! tip "En la herramienta"
    La clase `BlockNoise` en `src/planethunter/vetting/basic.py` hace exactamente esto. El error de la media de N puntos es el **mayor** entre $\sigma/\sqrt{N}$ (con $\sigma$ robusta, vía MAD) y la desviación estándar de las medias de bloques de N puntos, medida fuera del tránsito. Se usa en las pruebas `odd_even`, `secondary`, `secondary_scan` y `consistency`.

    El motivo se midió en el sector 69: con el error ingenuo $\sigma/\sqrt{N}$, **4 de 41 planetas confirmados** reprobaban la prueba de consistencia entre tránsitos. El error era demasiado pequeño, y diferencias normales parecían significativas.

    La misma idea da también una medida de detección, la **S/N_pink** ("pink", rosa, porque mezcla ruido blanco y rojo). Es el SNR calculado con el error de la fórmula de arriba, usando $\sigma_r$ medido en bloques del largo del tránsito. Siempre es menor o igual que el SNR simple, y mucho menor cuando la estrella tiene ondulaciones lentas que duran horas. El pipeline de vista rápida del TESS (QLP) exige S/N_pink ≥ 9; en PlanetHunter, una señal por debajo de 9 recibe una falla leve en la prueba `snr_pink` (lección [M5](m5-vetting-in-practice.md)).

    Hay un segundo indicador en la limpieza: la razón entre la dispersión de la curva y el ruido punto a punto (`red_noise_ratio` en `preprocess/clean.py`), ambos medidos con la MAD para que un tránsito profundo no la infle. Para ruido blanco vale alrededor de 1. Por encima de 1,2, el sistema rehace el detrending con ventanas más pequeñas. La estrella de TOI 862.01 pasaba con creces ese límite con la ventana por defecto. Mira la lección [M3](m3-periodograms.md).

!!! example "Ejercicio 3"
    Fuera del tránsito, una curva tiene una sigma robusta de 600 ppm por punto. Un tránsito tiene 36 puntos. Cortas la curva en bloques de 36 puntos y la desviación estándar de las medias de los bloques da 220 ppm.

    a) ¿Cuál sería el error de la media de 36 puntos si el ruido fuera blanco?
    b) ¿Qué error usa `BlockNoise`?
    c) Un tránsito aislado de 500 ppm: ¿cuál es el SNR en cada caso?

    ??? success "Ver respuesta"
        a) $600/\sqrt{36} = 600/6 = 100$ ppm.

        b) El mayor entre 100 y 220: **220 ppm**. Hay ruido rojo fuerte; los bloques fluctúan más del doble de lo esperado.

        c) Ruido blanco: 500/100 = 5,0. Con bloques: 500/220 ≈ 2,3. La cuenta ingenua haría que el tránsito pareciera dos veces más confiable de lo que es.

## Chi-cuadrado: ¿los tránsitos concuerdan entre sí?

Un planeta real produce tránsitos iguales en cada órbita. Si uno de los tránsitos es mucho más profundo que los otros, algo anda mal: un evento instrumental, un flare invertido o dos fenómenos mezclados.

¿Cómo decidir si las diferencias son "normales"? Con la **prueba de chi-cuadrado** ($\chi^2$):

1. Mide la profundidad de cada tránsito, $d_i$, y el error de cada una, $\sigma_i$ (aquí entra `BlockNoise`).
2. Calcula la media ponderada $\bar d$ (los tránsitos con menor error pesan más).
3. Suma las desviaciones al cuadrado, en unidades de error:

$$
\chi^2 = \sum_i \left(\frac{d_i - \bar d}{\sigma_i}\right)^2
$$

Si las diferencias son solo ruido, cada término vale en promedio alrededor de 1, y $\chi^2$ queda cerca del número de **grados de libertad**: el número de tránsitos menos 1. Si da mucho más, los tránsitos no concuerdan.

El **valor p** traduce $\chi^2$ a probabilidad: la probabilidad de que el ruido por sí solo produzca una discrepancia de ese tamaño o mayor. PlanetHunter reprueba si p < 0,001 (`transit_consistency_pvalue_min`).

La prueba tiene un segundo criterio: con 3 o más tránsitos, reprueba si un solo tránsito aporta más del 80 % del SNR² total. Es el caso de "un evento raro que domina".

!!! example "Ejercicio 4"
    Cinco tránsitos con profundidades de 290, 270, 310, 280 y 300 ppm, todos con un error de 25 ppm.

    a) Calcula $\chi^2$ y di si pasa la prueba.
    b) Cambia el último por 600 ppm. ¿Qué pasa?

    Dato: con 4 grados de libertad, p = 0,001 corresponde a $\chi^2 \approx 18{,}5$.

    ??? success "Ver respuesta"
        a) Media (pesos iguales) = 290 ppm. Desviaciones: 0, −20, +20, −10, +10. En unidades de error: 0; −0,8; 0,8; −0,4; 0,4. Cuadrados: 0; 0,64; 0,64; 0,16; 0,16. **$\chi^2 = 1{,}6$**, muy por debajo de 18,5. El valor p es de alrededor de 0,81. **Pasa.**

        b) Media = 350 ppm. Desviaciones: −60, −80, −40, −70, +250. En errores: −2,4; −3,2; −1,6; −2,8; 10. Cuadrados: 5,76; 10,24; 2,56; 7,84; 100. **$\chi^2 \approx 126$**, valor p del orden de $10^{-26}$. **Reprueba.** Basta un solo tránsito discordante.

!!! warning "Trampa: señales muy fuertes"
    Cuando el SNR es enorme, el error de cada tránsito se vuelve minúsculo, y diferencias reales pero inofensivas (un resto de detrending, un tránsito cortado por un hueco en los datos) se convierten en decenas de sigmas. En el sector 69, planetas confirmados de SNR alto reprobaron `consistency`: WASP-97 b (p ≈ $10^{-35}$), WASP-18 b (p ≈ $10^{-26}$), TOI-481 b. Por eso esta prueba es una **falla leve** (multiplica el score por 0,5), no un veto.

!!! tip "En la herramienta"
    En el dossier, la sección **"Depth per transit"** (profundidad por tránsito) es el chi-cuadrado en forma de gráfico: un punto por tránsito, con barra de error, y una línea discontinua en la media. Señal buena: puntos alineados sobre la línea. Señal mala: un punto muy lejos de los demás. En la tabla de vetting, la fila `consistency` muestra el número de tránsitos, el valor p y la fracción del SNR² en el tránsito mayor.

## Intervalo de confianza binomial: cuánto confiar en un recall

El benchmark del proyecto mide el **recall** (la tasa de recuperación): de 135 TOIs que deberían ser detectables en el sector 69, cuántos encuentra el sistema. Resultado: **123 de 135 = 91,1 %**.

Pero 135 es una muestra pequeña. Si lanzas una moneda cargada 135 veces, la fracción de caras varía de una ronda a otra. Aquí pasa lo mismo. La pregunta correcta es: ¿qué rango de recall "verdadero" es compatible con 123/135?

Una cuenta aproximada: el error de una proporción $p$ medida en $n$ casos es

$$
\text{EE} = \sqrt{\frac{p(1-p)}{n}} = \sqrt{\frac{0{,}911 \times 0{,}089}{135}} \approx 0{,}0245
$$

o sea, 2,45 puntos porcentuales. El intervalo del 95 % es de unos ±1,96 EE: de 86,3 % a 95,9 %.

El informe del proyecto usa una fórmula mejor, el **intervalo de Wilson**, que no deja que el rango pase del 100 % y se vuelve asimétrico cerca de los bordes. Resultado: **85,1 % a 94,8 %**. En palabras simples: el recall verdadero del sistema, en este tipo de objetivo, está muy probablemente entre 85 % y 95 %.

Consecuencia práctica: un cambio que lleva el recall de 120/135 (88,9 %) a 123/135 (91,1 %) es **compatible con el azar**. Tres TOIs más no prueban una mejora por sí solos. Hay que mirar qué TOIs cambiaron y por qué, como hace el informe de historial.

!!! example "Ejercicio 5"
    Calcula, con la aproximación simple, el intervalo del 95 % para la primera corrida del benchmark: 114 de 135 (84,4 %). ¿Se superpone con el intervalo de la corrida final (85,1 % a 94,8 %)?

    ??? success "Ver respuesta"
        $p = 0{,}844$. EE = $\sqrt{0{,}844 \times 0{,}156 / 135} = \sqrt{0{,}000975} \approx 0{,}0312$. Intervalo: 0,844 ± 1,96 × 0,0312 = 0,844 ± 0,061, o sea, **78,3 % a 90,5 %**.

        Sí, se superponen (de 85,1 % a 90,5 %). Aun así, la mejora de 114 a 123 es más convincente de lo que sugieren los números solos, porque el informe muestra la **causa** de cada TOI recuperado (límites estelares, ventana, alias). La estadística y el diagnóstico van juntos.

## Checklist de la lección

- [ ] Sé calcular a mano la media, la mediana, la desviación estándar y la MAD de unos pocos números.
- [ ] Sé explicar por qué PlanetHunter usa la mediana y la MAD en la limpieza.
- [ ] Sé qué significa "3 sigma" y por qué el límite del sistema es 7,1.
- [ ] Sé calcular el SNR de un tránsito a partir de la profundidad, el ruido por punto y el número de puntos.
- [ ] Sé explicar el ruido rojo con una analogía y describir el método de bloques.
- [ ] Sé calcular un chi-cuadrado sencillo e interpretar el valor p.
- [ ] Sé explicar por qué un recall de 91 % con 135 objetos puede ser algo entre 85 % y 95 %.
- [ ] Abrí un dossier, encontré la sección "Depth per transit" y la fila `consistency` de la tabla de vetting.

## Para ir más allá

- Khan Academy en español, ruta de estadística y probabilidad ([es.khanacademy.org](https://es.khanacademy.org/math/statistics-probability)): estadística descriptiva y distribución normal. Hazla antes si la media y la desviación estándar todavía te resultan extrañas.
- Pont, Zucker & Queloz (2006), *Monthly Notices of the Royal Astronomical Society* 373, 231. El artículo que formalizó el ruido rojo en tránsitos. Lee la introducción y las figuras.
- Jenkins, Caldwell & Borucki (2002), *The Astrophysical Journal* 564, 495. De dónde viene el límite de 7,1 sigma de Kepler, heredado por TESS.
- Wilson (1927), *Journal of the American Statistical Association* 22, 209. El origen del intervalo que usan los informes de benchmark; corto y legible.
- En el repositorio de PlanetHunter, `docs/benchmarks/2026-10-09-s0069-history.md`: el recall de cada corrida con el intervalo del 95 %. Bueno para practicar la lectura de proporciones con incertidumbre.
