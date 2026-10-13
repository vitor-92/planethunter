# A1. Algoritmos de detección a fondo

<p class="meta">Nivel avanzado · semanas 1–3 · cerca de 14 horas</p>

!!! abstract "En esta lección vas a aprender"
    - La estadística detrás del BLS (Kovács, Zucker & Mazeh 2002) y por qué, en el fondo, es una relación señal-ruido.
    - Qué cambia el TLS (Hippke & Heller 2019) respecto al BLS y cuánto cuesta eso.
    - Los compromisos entre tres formas de detrending: biweight, spline y procesos gaussianos.
    - Por qué los monotránsitos y duotránsitos son el nicho con más planetas por encontrar, y por qué son difíciles.
    - Los límites actuales de la búsqueda de PlanetHunter y de dónde vienen.

En la [lección M3](../intermediate/m3-periodograms.md) viste la idea del periodograma. Ahora la pregunta es: **¿qué se está maximizando exactamente, y por qué?**

## 1. La búsqueda como prueba de hipótesis en una grilla

Toda búsqueda de tránsitos periódicos prueba tres parámetros: **período** $P$ (días), **época** $T_0$ (instante de un tránsito, en BTJD) y **duración** $T_{14}$ (horas). Para cada trío, el algoritmo compara "brillo constante" con "brillo constante, excepto durante tránsitos que se repiten cada $P$". El periodograma muestra, para cada $P$, la mejora obtenida con el mejor $T_0$ y la mejor duración.

Consecuencia importante: son **millones de pruebas**, y el ruido por sí solo produce picos. Con un millón de intentos, casi con seguridad aparece por azar algún pico de 3 sigma. Es el **efecto de mirar en otro lugar** (look-elsewhere effect), que vuelve en la lección A5, en el piso de ruido medido por el proyecto.

## 2. BLS: la estadística detrás

El **BLS** (Box Least Squares) fue publicado por Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. El modelo es una caja: brillo $H$ fuera del tránsito, brillo $L$ dentro, con transición instantánea.

### Las definiciones del artículo

Los datos son $N$ medidas de flujo $x_i$ con errores $\sigma_i$. Primero se resta la media ponderada, de modo que los datos quedan centrados en cero. Cada punto recibe un peso normalizado:

$$
w_i = \frac{\sigma_i^{-2}}{\sum_j \sigma_j^{-2}}, \qquad \sum_i w_i = 1 .
$$

Para un período de prueba, los puntos se pliegan en fase. Se elige un intervalo de fase candidato a tránsito y se define:

$$
r = \sum_{i \in \text{tránsito}} w_i, \qquad s = \sum_{i \in \text{tránsito}} w_i \, x_i .
$$

En palabras: $r$ es la **fracción del peso** que cae dentro del tránsito (si todos los errores son iguales, es simplemente la fracción de los puntos) y $s$ es la **suma ponderada del flujo** dentro del tránsito. Si hay una caída, $s$ es negativo.

El artículo muestra que la suma de los residuos al cuadrado del mejor modelo de caja es

$$
D = \sum_i w_i x_i^2 - \frac{s^2}{r(1-r)} .
$$

El primer término no depende del modelo. Entonces **minimizar $D$ es lo mismo que maximizar $s^2/[r(1-r)]$**. El BLS calcula esa cantidad para todos los intervalos y guarda el valor más grande. Su raíz es el **SR** (signal residue) de ese período:

$$
\text{SR} = \max \left[ \frac{s^2}{r(1-r)} \right]^{1/2} .
$$

La profundidad del mejor modelo sale gratis: $\delta = H - L = |s| / [r(1-r)]$.

### Por qué esto es una relación señal-ruido

Supón errores iguales, $\sigma_i = \sigma$, y un tránsito de profundidad $\delta$ que ocupa la fracción $r$ de los puntos. Con los datos centrados en cero, el nivel dentro es $L = -\delta(1-r)$ y fuera es $H = \delta r$. Entonces $s = rL = -\delta\, r(1-r)$ y

$$
\frac{s^2}{r(1-r)} = \delta^2\, r(1-r) .
$$

Multiplicando por $N/\sigma^2$ (para volver de los pesos normalizados al chi-cuadrado), la mejora del ajuste es

$$
\Delta\chi^2 = \frac{N \, \delta^2 \, r(1-r)}{\sigma^2}
\quad \Longrightarrow \quad
\sqrt{\Delta\chi^2} = \frac{\delta}{\sigma}\sqrt{N r (1-r)} \approx \frac{\delta}{\sigma}\sqrt{N_\text{en tránsito}} .
$$

Es la fórmula de SNR del nivel intermedio: profundidad sobre el ruido de un punto, por la raíz del número de puntos en tránsito. El BLS busca el período que **maximiza la SNR de una caja**. Y vale lo que viste en la [lección M1](../intermediate/m1-statistics-for-signals.md): con ruido correlacionado, $\sigma/\sqrt{N}$ subestima el error y el BLS resulta optimista.

### SDE: ¿el pico se destaca?

El SR por sí solo depende de la escala de los datos. Para comparar estrellas, Kovács et al. definen el **SDE** (Signal Detection Efficiency):

$$
\text{SDE} = \frac{\text{SR}_\text{pico} - \langle \text{SR} \rangle}{\text{desviación estándar}(\text{SR})} .
$$

En palabras: cuántas desviaciones estándar está el pico por encima de la media del periodograma. Por ser **relativo al propio periodograma**, es comparable entre estrellas de brillo diferente.

## 3. TLS: qué cambia

El **TLS** (Transit Least Squares), de Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39, es el algoritmo que usa PlanetHunter. La idea central es simple: **un tránsito real no es una caja**. Tiene entrada y salida graduales (ingreso y egreso) y un fondo redondeado por el oscurecimiento de borde (el borde de la estrella es más oscuro que el centro, como viste en la [lección M2](../intermediate/m2-transit-physics.md)).

### Las diferencias principales

| Aspecto | BLS | TLS |
|---|---|---|
| Modelo | Caja de dos alturas | Tránsito con oscurecimiento de borde (en PlanetHunter, coeficientes de la banda de TESS elegidos según la temperatura y la gravedad de la estrella) |
| Medida de ajuste | $s^2/[r(1-r)]$ | Chi-cuadrado del ajuste del modelo |
| Espectro | SR(P) | $\text{SR}(P) = \chi^2_\text{min, global} / \chi^2_\text{min}(P)$, entre 0 y 1 |
| SDE | (pico − media) / desviación | $(1 - \langle\text{SR}\rangle)/\sigma_\text{SR}$, con la tendencia del espectro removida |
| Grilla de períodos | Libre | Muestreo óptimo en frecuencia (Ofir 2014) |
| Grilla de duraciones | Libre | Limitada por la física: el radio y la masa de la estrella fijan la duración posible para cada período |
| Costo | Bajo | Mucho mayor; exige paralelismo |

La ganancia viene de dos fuentes. El modelo realista se ajusta mejor a la señal, sobre todo en planetas pequeños, donde el ingreso y el egreso son una fracción grande del tránsito; los autores muestran un SDE mayor que el del BLS en los mismos datos. Y la grilla de duraciones limitada por la estrella evita probar duraciones imposibles, lo que reduce los intentos y los picos espurios.

El límite **SDE ≥ 9** viene del artículo del TLS: con ruido blanco, corresponde a una probabilidad de falsa alarma del orden de $10^{-4}$ (`sde_min` en `config/thresholds.yaml`).

### Lo que no hay que tomar del TLS tal cual

Dos salidas del TLS estaban silenciosamente equivocadas para el uso del proyecto, y la auditoría de código del 2026-10-10 encontró las dos:

- **Duración.** El TLS 2.0 multiplica la duración del tránsito por el factor de llenado de la serie (la fracción de cadencias presentes en todo el intervalo). En un sector es un poco menor que 1 (0,86 en el sector 69). En dos sectores separados por 700 días es cerca de 0,07, y un tránsito de 3 h salía como 0,23 h. Como esa misma duración alimentaba la SNR, el enmascaramiento iterativo y las ventanas del vetting, el error se propagaba por todo el pipeline. El proyecto ahora deshace esa multiplicación (`search/stats.py`) y guarda el valor del TLS solo como `duration_raw_hours`.
- **SNR y S/N_pink.** La SNR se recalcula sobre la curva aplanada, con la T14 física y un ruido robusto. El TLS ya calcula una S/N_pink por tránsito (Pont et al. 2006), que se estaba descartando; ahora se combina, $\sqrt{\sum_i \text{S/N}_{\text{pink},i}^2}$, y se guarda sin costo extra de CPU. El vetting la usa con el umbral de 9 del QLP.

La regla general: antes de confiar en un número de una biblioteca, verifica su definición contra el artículo y contra un caso conocido.

### Medir la tasa de falsas alarmas: corridas nulas

El umbral de SDE supone ruido blanco; las curvas de luz reales no son blancas. Kepler midió la tasa de falsas alarmas directamente (Thompson et al. 2018): buscó en curvas de luz que **no pueden** contener tránsitos reales y contó lo que salía. PlanetHunter hace lo mismo con `planethunter search --null inverted` (el flujo se pone de cabeza, así que las caídas se vuelven subidas) y `--null scrambled` (cada órbita de datos se desplaza en el tiempo, así que los tránsitos dejan de alinearse entre órbitas). Toda señal de estas corridas es una falsa alarma por construcción. Sirven para dos cosas: estimar cuántas de las señales `NEW` se espera que sean ruido y darle al modelo de aprendizaje automático negativos realistas (lección A4). El costo es una búsqueda extra por cada modo nulo.

### El precio de la física: límites estelares

La grilla de duraciones depende del radio y la masa de la estrella, y el proyecto se cortó con esto dos veces (historial del benchmark):

- **Límites demasiado estrechos.** Con el radio y la masa limitados a ±30 % del TIC, los tránsitos más cortos de lo previsto (parámetro de impacto alto) quedaban fuera de la grilla. TOI 196.01, 347.01, 386.01 y 2339.01 solo aparecieron con límites amplios (SDE 8,6 a 16,8).
- **Radio estelar en el período mínimo.** El TLS deriva el período más corto a partir del límite de Roche, que depende del radio. Con $R = 4{,}06\,R_\odot$ en el TIC, la grilla empezaba en 4,15 días, y TOI 196.01 tiene 1,16 días. Corrección: modelo con radio y masa limitados a 1,5.
- **Tres radios estelares.** El TLS pone la órbita más corta a 3 radios estelares, lo que dejaba el período mínimo real entre 0,6 y 1,0 días: 13 de los 505 TOIs del sector 69 quedaban fuera de la grilla. El proyecto ahora usa 2 radios estelares, como el QLP (Kunimoto et al. 2023), con un piso de 0,2 días.

Lección: cada dato "físico" que se le da al algoritmo es también una hipótesis que puede estar equivocada.

## 4. Detrending: biweight, spline y GP

Antes de buscar, hay que remover la variación lenta de la estrella (rotación, manchas, sistemáticos del telescopio). La elección del método decide qué sobrevive.

| Método | Cómo funciona | Ventaja | Riesgo |
|---|---|---|---|
| **Biweight** en ventana deslizante | Para cada punto, estima el "nivel típico" de los vecinos en una ventana de tiempo, dando poco peso a los puntos muy alejados de la mediana | Robusto ante tránsitos y valores atípicos; un solo parámetro (la ventana); rápido | Una ventana corta se come un tránsito largo; una ventana larga deja la variabilidad rápida |
| **Spline** robusta | Curva suave hecha de polinomios por partes, ajustada varias veces descartando los puntos discrepantes | Buena para tendencias lentas y suaves | El espaciado de los nodos cumple el papel de la ventana; puede oscilar cerca de huecos |
| **Proceso gaussiano** (GP) | Modelo estadístico del ruido correlacionado, con un "kernel" que describe cuánto se parecen los puntos cercanos (por ejemplo, casi periódico para la rotación) | Sigue la variabilidad compleja de estrellas jóvenes y activas; da incertidumbre | Demasiado flexible: absorbe el tránsito si no se enmascara; caro; exige elegir el kernel |

El artículo de wotan (Hippke et al. 2019, *AJ* 158, 143), la biblioteca que usa el proyecto, comparó decenas de métodos y concluyó que el biweight con una ventana de cerca de **tres veces la duración del tránsito** es la mejor opción general.

### Lo que midió el proyecto

- Tránsito de caja de 1 500 ppm sin variabilidad: una ventana de **0,5 días** pierde el 8 % de la profundidad en un tránsito de 3 h y el **40 %** en uno de 5 h; una ventana de **1,0 día** pierde el 0 % y el 6 %. Los tránsitos con período mayor a 10 días en estrellas tipo Sol duran de 5 a 6 horas: la ventana por defecto es 1,0 día.
- **TOI 862.01** (5 092 ppm) desaparece con 1,0 día (la dispersión de la curva se queda muy por encima del ruido punto a punto: variabilidad rápida que quedó) y aparece con 0,5 días, SDE 18.
- **TOI 190.01** (5,7 h, 8 248 ppm) se reduce a 347 ppm con una ventana de 0,3 días.

No hay una ventana única para los dos casos. Solución: si la razón entre la dispersión de la curva y el ruido punto a punto supera 1,2 (`red_noise_max`), rehacer el detrending con 0,5 y 0,3 días (`fallback_windows_days`) y **buscar en todas las versiones**. Junto con otros cambios, esto llevó el recall de 86,7 % a 88,9 %.

La propia razón tenía una trampa. Con la desviación estándar, un tránsito profundo en ruido blanco puro daba una razón mayor que 3, así que las estrellas con los tránsitos más profundos se mandaban a las ventanas cortas, que se comen los tránsitos. Desde el 2026-10-10 los dos términos usan la MAD, que unos pocos puntos en tránsito no logran mover (300 estrellas del sector 69: 18,7 % marcadas con la desviación estándar, 16,0 % con la MAD; las 8 estrellas que cambiaron tienen caídas profundas, y 5 de ellas son TOIs).

**Aplanado para el vetting.** Después de la detección ya se conocen la duración y los instantes de tránsito, así que el vetting puede hacerlo mejor que la búsqueda: aplana cada sector con la ventana propia de ese sector, nunca más corta que 3 × T14, y **enmascara** los tránsitos para que el biweight interpole por encima de ellos (Hippke et al. 2019). Con un tránsito de 12 h, una ventana simple de 1,0 día conserva el 50 % de la profundidad; el aplanado con máscara conserva el 99 %.

El caso que todavía falla: **TOI 251.01** (845 ppm, 4,94 d), una estrella joven con ruido rojo de 1,8, justo donde un GP podría ayudar. El historial lo lista como "próxima hipótesis". Hipótesis, no solución: solo el benchmark lo dirá.

## 5. Monotránsitos y duotránsitos: el nicho con más planetas por encontrar

Un **monotránsito** es un único tránsito observado. Un **duotránsito** son dos tránsitos separados por un intervalo largo, en general en sectores de años diferentes, sin ningún tránsito observado entre ellos.

### Por qué es el nicho más prometedor

1. **TESS observa en bloques de cerca de 27 días.** Un planeta de 60 días muestra como máximo un tránsito por sector, y en gran parte del cielo la estrella solo vuelve a observarse años después.
2. **Los pipelines oficiales exigen al menos dos tránsitos.** Los eventos únicos quedan fuera.
3. **La evidencia es concreta.** De los TOIs que nacieron como CTOIs de la comunidad (168 hasta 2021, Zenodo 5130660), la mayoría son estrellas débiles de las imágenes completas o **tránsitos únicos rechazados por las búsquedas periódicas**.
4. **Los planetas de período largo son valiosos**: más fríos y menos irradiados.

Por otro lado, sin período no existen las pruebas de impar/par, secundario y consistencia; y un evento único es fácil de imitar (ajuste de apuntamiento, luz dispersa, un asteroide cruzando la región usada para estimar el fondo del cielo).

### Estimando el período por la duración

La duración de un tránsito central ($b = 0$) en una órbita circular es $T \approx P R_\star / (\pi a)$. Combinándola con la tercera ley de Kepler, $a^3 = G M_\star P^2 / (4\pi^2)$, y despejando $P$:

$$
P \approx \frac{\pi \, G M_\star \, T^3}{4 \, R_\star^3} .
$$

Si el tránsito no es central ($b > 0$), es más corto de lo que sería con $b = 0$ para el mismo período. Por lo tanto, usar la duración observada en esta fórmula da un **límite inferior** para el período. Esta idea (estimar el período a partir de la forma de un único tránsito y de la densidad de la estrella) es la base de trabajos como Osborn et al. (2016), *MNRAS* 457, 2273, hechos con datos de K2.

### Duotránsitos: alias en peine

Con dos tránsitos separados por $\Delta t$, el período verdadero es $\Delta t / n$ para algún entero $n$. Cada $n$ es un candidato. El límite inferior por la duración elimina los $n$ grandes. Los sectores de TESS en los que la estrella se observó sin tránsito eliminan otros: si el alias $n$ predice un tránsito en una fecha con datos y no aparece nada, queda descartado.

### Estado en el proyecto

PlanetHunter todavía **no tiene** detector de monotránsitos. Hoy, `n_transits` veta cualquier señal con menos de dos tránsitos. Pero la base ya respeta el nicho: `edge_cutoff_days: 0.0` en el detrending preserva los eventos cerca de los bordes de los datos, justamente para no borrar monotránsitos. El detector está en la fase 4 del plan.

## 6. Los límites de la búsqueda del proyecto

| Parámetro | Valor | Por qué |
|---|---|---|
| `period_min_days` | 0,2 | Piso absoluto de la grilla |
| `roche_min_a_rstar` | 2,0 | Órbita más corta: 2 radios estelares (QLP) |
| `period_max_fraction_of_span` | 0,9 | Deben caber dos tránsitos en el intervalo de datos |
| `n_transits_min` (TLS) | 1 | Deja que el límite de 0,9 de arriba tenga efecto; el vetting sigue exigiendo 2 tránsitos |
| `period_max_days` | 40 | Techo absoluto, explicado abajo |
| `max_signals_per_target` | 3 | Búsqueda iterativa: encuentra, enmascara 2 duraciones alrededor, busca de nuevo |
| `bin_minutes` | 10 | Acelera la búsqueda; pierde poco para períodos mayores a 1 día |

En un solo sector (cerca de 27 días), el período máximo efectivo es 0,9 × 27 ≈ 24 días. (Hasta el 2026-10-10 era en realidad cerca de 13,5 días: el valor por defecto del propio TLS exige espacio para dos tránsitos, lo que limita el período a la mitad del intervalo, y el ajuste de 0,9 no hacía nada). El techo de 40 días solo muerde en la búsqueda **multisector**. Y mordió: al juntar sectores separados por años (cerca de 800 días en total), aparecieron **alias espurios de 26 a 64 días** con uno o dos tránsitos (TIC 41230546 y 31929204). El mecanismo es el peine de duotránsitos: con dos bloques de datos distantes, muchos períodos $\Delta t / n$ alinean una caída de ruido en un sector con otra en el otro, y con miles de intentos algún alineamiento ocurre. El techo corta el problema de raíz; los períodos largos quedan para el futuro detector de monotránsitos y duotránsitos.

Otro límite: con pocos tránsitos y huecos, el TLS a veces devuelve un tercio del período (TOI 899.01, 924.01 y 3262.01 aparecían alrededor de 4,2 días). La función `refine_alias` prueba $2P$ y $3P$: si las épocas predichas solo por el período corto caen en tramos con datos y sin caída, gana el período mayor. Esta corrección llevó el recall a 91,1 %. Faltaba un detalle hasta la auditoría: después de cambiar a $kP$, la SNR se quedaba con el valor medido con las épocas de $P$, demasiado baja por un factor $\sqrt{n_A/n}$ (0,58 para $k = 3$). Ahora se mide de nuevo sobre las épocas del período verdadero.

!!! tip "En la herramienta"
    - Todos los parámetros de esta lección están en `config/thresholds.yaml`, secciones `preprocess` y `search`, cada uno con el comentario del porqué.
    - El detrending y las variantes de ventana están en `src/planethunter/preprocess/clean.py`; la búsqueda TLS y `refine_alias`, en `src/planethunter/search/tls.py`.
    - En el dossier, el gráfico "Curva de luz" muestra el resultado del detrending. Compáralo con la curva cruda y busca tránsitos encogidos.
    - `uv run planethunter run-target 261136679` ejecuta la búsqueda multisector en Pi Mensae; fíjate en las iteraciones.

!!! example "Ejercicio 1. La SNR escondida en el BLS"
    Una estrella tiene un ruido de 1 000 ppm por punto de 2 minutos. El sector tiene $N = 18\,000$ puntos válidos. Un planeta con período de 5 días produce tránsitos de 1 000 ppm y 3 horas. Calcula $r$, la mejora $\sqrt{\Delta\chi^2}$ prevista por el BLS y di si la señal pasa el límite de SNR del proyecto.

    ??? success "Ver respuesta"
        1. Fracción en tránsito: $r = 3\ \text{h} / (5 \times 24\ \text{h}) = 3/120 = 0{,}025$.
        2. $\sqrt{\Delta\chi^2} = (\delta/\sigma)\sqrt{N r (1-r)} = (1000/1000)\sqrt{18\,000 \times 0{,}025 \times 0{,}975}$.
        3. $18\,000 \times 0{,}025 = 450$ puntos en tránsito; $450 \times 0{,}975 = 438{,}75$; raíz $\approx 20{,}9$.
        4. SNR ≈ 21, muy por encima de 7,1. Pasa.

        Observación: los bins de 10 minutos (5 puntos) reducen el ruido por punto a $1000/\sqrt{5} \approx 447$ ppm, pero dividen $N$ entre 5. Con ruido blanco, la SNR queda igual: el binning acelera sin perder sensibilidad.

!!! example "Ejercicio 2. Período mínimo de un monotránsito"
    Ves un único tránsito de 10 horas en una estrella igual al Sol ($M = 1\,M_\odot$, $R = 1\,R_\odot$). Usa $G M_\odot = 1{,}327 \times 10^{20}\ \text{m}^3/\text{s}^2$ y $R_\odot = 6{,}957 \times 10^{8}\ \text{m}$. ¿Cuál es el período más corto compatible con una órbita circular?

    ??? success "Ver respuesta"
        1. $T = 10\ \text{h} = 36\,000\ \text{s}$; $T^3 = 4{,}666 \times 10^{13}\ \text{s}^3$.
        2. $R_\star^3 = (6{,}957 \times 10^8)^3 = 3{,}367 \times 10^{26}\ \text{m}^3$.
        3. Numerador: $\pi \times 1{,}327 \times 10^{20} \times 4{,}666 \times 10^{13} = 1{,}945 \times 10^{34}$.
        4. Denominador: $4 \times 3{,}367 \times 10^{26} = 1{,}347 \times 10^{27}$.
        5. $P \approx 1{,}444 \times 10^{7}\ \text{s} \approx 167$ días.

        Como $b > 0$ acorta el tránsito, el período real es **de al menos** unos 167 días (órbita circular). Comprobación: la Tierra tiene un tránsito de cerca de 13 horas; $(13/10)^3 \times 167 \approx 367$ días, cerca del año real.

!!! example "Ejercicio 3. El peine de un duotránsito"
    La misma estrella del ejercicio 2 muestra un segundo tránsito idéntico 730,0 días después del primero, en un sector de dos años más tarde. Lista los períodos posibles. Después, supón que TESS observó la estrella en un sector intermedio en el que el alias de 365 días predice un tránsito en medio de los datos, y no apareció nada. ¿Qué queda?

    ??? success "Ver respuesta"
        1. Candidatos: $P_n = 730{,}0/n$.
        2. Del ejercicio 2, $P \gtrsim 167$ días, entonces $n \le 730/167 \approx 4{,}4$, es decir, $n \in \{1, 2, 3, 4\}$.
        3. Períodos: 730,0; 365,0; 243,3; 182,5 días.
        4. El sector intermedio elimina $n = 2$ (365 días). Atención: también elimina $n = 4$, porque todo tránsito previsto por 365 días también lo prevé 182,5 días (182,5 es la mitad de 365).
        5. Quedan 730,0 y 243,3 días. Decidir exige observar en una fecha predicha por uno y no por el otro: así es como los duotránsitos se convierten en solicitudes de observación desde tierra.

!!! warning "Trampa común"
    Concluir que el período es correcto porque el pico es alto. Puede ser $P/2$, $2P$, $P/3$, un alias multisector o tránsitos de **dos planetas diferentes** combinados (caso HD 23472, lección A2).

## Checklist de la lección

- [ ] Hice la primera y la segunda pasada de Kovács, Zucker & Mazeh (2002).
- [ ] Sé derivar, con ayuda de esta lección, por qué maximizar $s^2/[r(1-r)]$ equivale a maximizar la SNR de una caja.
- [ ] Leí Hippke & Heller (2019), ahora con las ecuaciones, y sé decir las tres diferencias principales respecto al BLS.
- [ ] Sé explicar con números del proyecto por qué la ventana de detrending es 1,0 día y cuándo el sistema usa 0,5 y 0,3.
- [ ] Sé estimar el período mínimo de un monotránsito y listar los alias de un duotránsito.
- [ ] Sé por qué existe el techo `period_max_days: 40`.

## Para ir más allá

- Kovács, Zucker & Mazeh (2002), *Astronomy & Astrophysics* 391, 369. El artículo original del BLS, con toda la estadística de esta lección.
- Hippke & Heller (2019), *Astronomy & Astrophysics* 623, A39. El TLS; lee la sección de método y la comparación con el BLS.
- Ofir (2014), *Astronomy & Astrophysics* 561, A138. Cómo elegir la grilla de períodos de forma óptima; el TLS usa esta idea.
- Hippke et al. (2019), *The Astronomical Journal* 158, 143. El artículo de wotan, con la comparación de métodos de detrending que justifica el biweight.
- Foreman-Mackey et al. (2017), *The Astronomical Journal* 154, 220. celerite, procesos gaussianos rápidos; punto de partida para probar GP en estrellas activas.
- Osborn et al. (2016), *Monthly Notices of the RAS* 457, 2273. Tránsitos únicos en K2 y estimación del período a partir de un solo evento.
- Seager & Mallén-Ornelas (2003), *The Astrophysical Journal* 585, 1038. Las relaciones analíticas entre la forma del tránsito, la densidad estelar y el período, base de la fórmula del ejercicio 2.
