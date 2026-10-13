# Autoevaluación del nivel intermedio

<p class="meta">Nivel intermedio · semana 10 · unas 3 horas</p>

!!! abstract "Cómo hacerla"
    - Responde por escrito, sin consultar las lecciones. Se permite usar calculadora.
    - Solo después abre cada respuesta y compara. No basta con acertar la conclusión: el razonamiento tiene que estar ahí.
    - Las preguntas 1 a 6 son las del plan de estudios y deciden la aprobación. Las preguntas 7 a 10 son práctica extra.

## Criterio de aprobación

**Responde bien al menos 5 de las 6 primeras preguntas** y sigue al [nivel avanzado](../advanced/index.md).

"Responder bien" quiere decir: la respuesta menciona el mecanismo correcto y, cuando hay una cuenta, la cuenta llega al orden de magnitud correcto. Si fallas dos o más, vuelve a las lecciones indicadas en cada respuesta y rehaz sus ejercicios antes de intentarlo de nuevo.

## Preguntas del plan

!!! question "1. ¿Por qué el sistema exige SNR ≥ 7,1 y no ≥ 3?"

    ??? success "Ver respuesta"
        Por el **efecto de mirar en todas partes**. Con ruido gaussiano, un valor de 3 sigma aparece por azar 1 vez de cada 740, más o menos. Parece raro, pero la búsqueda prueba miles de períodos y, para cada uno, miles de posiciones y duraciones, en unas 20 000 estrellas por sector. Son millones de intentos: con un límite de 3 sigma, el ruido puro produciría miles de "señales" por sector.

        En 7,1 sigma, la probabilidad por intento baja a unos $6 \times 10^{-13}$. El valor viene de la misión Kepler (Jenkins, Caldwell & Borucki, 2002), elegido para que una búsqueda del tamaño de la de Kepler, sobre ruido blanco gaussiano, diera menos de una falsa alarma en total.

        Punto extra: el ruido real no es gaussiano. El proyecto midió que las búsquedas en una franja estrecha de períodos, en estrellas sin señal, superan SNR 19 en el 10 % de los intentos. Por eso 7,1 es **necesario, pero no suficiente**: el vetting y la prueba de otros sectores hacen el resto.

        Repasa: [M1](m1-statistics-for-signals.md), secciones "La distribución normal y la sigma" y "SNR y la raíz de N".

!!! question "2. Un tránsito dura 6 horas en una enana roja con período de 3 días. ¿Por qué es sospechoso?"

    ??? success "Ver respuesta"
        Porque la duración prevista es mucho menor. Toma una enana roja típica, con 0,3 R☉ y 0,3 M☉. Su densidad es $0{,}3/0{,}3^3 \approx 11$ veces la del Sol.

        $a/R_\star = 215 \times (3/365{,}25)^{2/3} \times 11^{1/3} \approx 215 \times 0{,}0407 \times 2{,}23 \approx 19{,}5$.

        $T_{14}(b=0) \approx (P/\pi)(R_\star/a) = (3/\pi)/19{,}5 \approx 0{,}049$ d $\approx$ **1,2 horas**.

        Seis horas es cinco veces eso. El tránsito central es el más largo posible en una órbita circular, así que la razón 5 supera con mucho el límite de 1,67 de la prueba `duration`. Explicaciones posibles:

        - la señal viene de **otra estrella**, más grande, en el mismo píxel (blend, mezcla);
        - la estrella no es una enana roja (radio equivocado en el TIC);
        - el período está mal (la duración crece con $P^{1/3}$; para 6 h en esa estrella, el período tendría que ser de cientos de días);
        - órbita muy excéntrica, que rara vez explica un factor 5.

        Repasa: [M2](m2-transit-physics.md), sección "La duración del tránsito".

!!! question "3. ¿Qué cambia en el periodograma si la curva tiene un hueco grande en el medio?"

    ??? success "Ver respuesta"
        Varias cosas, todas para peor:

        - **Menos tránsitos.** Los que caen en el hueco no existen en los datos. El SNR baja (menos puntos) y, con un período largo, puede quedar un solo tránsito, vetado por `n_transits`.
        - **Alias más fuertes.** Los tránsitos "extra" que predicen P/2 o P/3 pueden caer en el hueco, y nada en los datos los desmiente. El pico del alias queda tan alto como el verdadero, o más. Es lo que pasó con TOI 899.01, 924.01 y 3262.01 en el sector 69, encontrados con unos 4,2 d en lugar de 12 a 13 d. El `refine_alias` prueba 2P y 3P justamente por eso.
        - **Bordes nuevos.** Cada lado del hueco es un borde de segmento. El detrending crea rampas ahí que pueden imitar tránsitos (el proyecto midió SDE ~10 en ruido puro con un evento a 0,07 d del borde). Las señales con más del 50 % de los tránsitos en bordes se bloquean (`edge_transit_fraction`).
        - **Estructura en el periodograma.** Los períodos que ponen todos los tránsitos en el hueco no se pueden probar; el periodograma queda con más picos espurios ligados al espaciado de los segmentos.

        Repasa: [M3](m3-periodograms.md), secciones "Alias: los picos fantasma" y "Huecos y bordes de segmento".

!!! question "4. ¿Por qué la prueba de centroide usa la distancia implícita de la fuente y no solo la significancia del desplazamiento?"

    ??? success "Ver respuesta"
        Porque la **significancia** responde "¿existe el desplazamiento?", y no "¿la fuente está lejos?". En estrellas brillantes, con muchos tránsitos, el error del centroide se vuelve minúsculo, y hasta un desplazamiento irrelevante, causado por el propio objetivo, supera los 3 sigma.

        La **distancia implícita** responde la pregunta correcta. Si una fuente a una distancia $D$ del centroide se oscurece con profundidad relativa $\delta$, el centroide se mueve aproximadamente $\delta \times D$. Por lo tanto, $D \approx$ desplazamiento / profundidad. Si $D$ es menor que 1 píxel (21″), la fuente es compatible con el objetivo.

        La evidencia medida: con el criterio de solo significancia, **11 de 41 planetas confirmados** del sector 69 reprobaban, todos con la fuente implícita a 0,88 píxel como máximo. La regla actual exige las dos cosas: más de 3 sigma **y** fuente a más de 1 píxel. Un falso positivo como TOI-854.01 (12σ, fuente a 2,0 píxeles) sigue reprobando. Dos refinamientos hacen honesto al propio sigma: el error de una época se mide en 200 épocas falsas fuera de los tránsitos, y la profundidad se corrige a la profundidad dentro de la apertura (CROWDSAP × δ).

        Repasa: [M5](m5-vetting-in-practice.md), sección `centroid`.

!!! question "5. Explica, con un dibujo, por qué una binaria con período 2P aparece con profundidades distintas en los tránsitos impares y pares."

    ??? success "Ver respuesta"
        Una binaria eclipsante tiene **dos** eclipses por órbita: el primario (se tapa la estrella más brillante) y el secundario (se tapa la menos brillante). Si las estrellas son parecidas, los dos eclipses tienen profundidades parecidas, y la búsqueda encuentra el intervalo entre eclipses consecutivos, P. El período orbital verdadero es **2P**.

        ```
        brillo
        ────╮    ╭────╮  ╭────╮    ╭────╮  ╭────
            │    │    ╰──╯    │    │    ╰──╯
            ╰────╯            ╰────╯
              1        2        3        4
            impar     par     impar     par
            hondo     leve    hondo     leve
              |<- P -->|<- P -->|
              |<----- 2P ------>|
        ```

        Con el período P, numeramos los eventos 1, 2, 3, 4... Los impares (1, 3, 5) son siempre primarios; los pares (2, 4, 6), siempre secundarios. Si las estrellas tienen tamaño o temperatura distintos, los primarios son más profundos que los secundarios, y el promedio de los impares difiere del promedio de los pares.

        La prueba `odd_even` mide esa diferencia en sigmas (con el error en bloques): falla a partir de 3σ y veta a partir de 5σ. Ejemplo real: TOI-343.01, impar 2 294 ppm, par 4 583 ppm, 5,8σ, vetado.

        Repasa: [M3](m3-periodograms.md), aviso "Binaria con período 2P", y [M5](m5-vetting-in-practice.md).

!!! question "6. Abre un dossier aprobado y di cuál sería la siguiente prueba que harías antes de enviarlo."

    ??? success "Ver respuesta"
        No hay una respuesta única, pero una buena respuesta sigue esta lógica:

        1. **Ver lo que está pendiente.** La tabla **Vetting** del dossier lista las pruebas profundas que todavía no se ejecutaron (`tpf_difference_image`, `gaia_neighbors`, `fpp_triceratops`). Una señal aprobada en el básico todavía no pasó por ellas.
        2. **La prueba más poderosa suele ser la de otros sectores.** Si la estrella se observó en otros sectores, la señal tiene que reaparecer con la fuerza esperada. Fue esta prueba la que derribó a HD 271883 (señal 1798, 6,61 d): se esperaba SNR de 45 a 64 en los sectores 67, 68 y 97, y la señal no apareció. Ejecuta `uv run planethunter vet-deep <run_id>`.
        3. **Después, imagen de diferencia en el TPF y vecinas de Gaia**, para confirmar que la fuente es el objetivo.
        4. **Después, FPP con triceratops**, solo si todo lo anterior pasa.
        5. **Y siempre:** la página de la estrella en ExoFOP y una búsqueda en ADS por el TIC, para ver si alguien ya publicó algo.

        Una respuesta sólida menciona el dossier concreto: "esta estrella tiene host conocido y otros 3 sectores; el siguiente paso es `vet-deep` para la prueba de otros sectores, porque una señal nueva y profunda en un solo sector es la firma clásica de un sistemático".

        Repasa: [M5](m5-vetting-in-practice.md), "Guía de revisión de candidatos", y el paso 6 de la guía para principiantes (`docs/BEGINNERS_GUIDE.md`).

## Preguntas extra

!!! question "7. Un cambio en el código llevó el recall de 120/135 a 123/135. ¿Eso prueba que el cambio mejoró el sistema?"

    ??? success "Ver respuesta"
        No por sí solo. El intervalo de confianza del 95 % (Wilson) para 123/135 va de 85,1 % a 94,8 %; para 120/135 (88,9 %), la aproximación simple da de 83,6 % a 94,2 %. Los intervalos se superponen casi por completo: tres TOIs más son compatibles con el azar.

        Lo que hace convincente el cambio es el **diagnóstico**: saber qué TOIs empezaron a encontrarse y por qué. En el historial del benchmark (`docs/benchmarks/2026-10-09-s0069-history.md`), el cambio de la ejecución final (`refine_alias`) recuperó exactamente TOI 899.01, 924.01 y 3262.01, que antes salían con P/3. Causa identificada más efecto en el lugar previsto: eso convence.

        Repasa: [M1](m1-statistics-for-signals.md), "Intervalo de confianza binomial".

!!! question "8. ¿Qué pasaría si la ventana de detrending fuera de 0,2 días?"

    ??? success "Ver respuesta"
        El filtro empezaría a seguir el propio tránsito y a "comérselo". La regla práctica es una ventana de unas 3 veces la duración del tránsito: 0,2 d (4,8 h) solo preserva bien tránsitos de hasta ~1,6 h.

        Los números medidos muestran el tamaño del daño con ventanas mayores que esa: con 0,5 d, un tránsito de 5 h pierde el 40 % de la profundidad; con 0,3 d, TOI 190.01 (5,7 h) cayó de 8 248 ppm a 347 ppm. Con 0,2 d, los tránsitos de 3 h o más quedarían fuertemente reducidos, el SNR caería y muchos planetas con períodos de más de algunos días desaparecerían.

        A cambio, las estrellas muy variables quedarían más limpias. Por eso PlanetHunter solo usa ventanas cortas (0,5 y 0,3 d) en una **segunda variante**, cuando la razón de ruido supera 1,2, y busca en las dos versiones.

        Repasa: [M3](m3-periodograms.md), "Detrending: la ventana que decide".

!!! question "9. Un planeta de período de 10 días transita una estrella igual al Sol, y el tránsito medido dura 3,0 horas. ¿Pasa la prueba duration? ¿Cuál es el parámetro de impacto aproximado?"

    ??? success "Ver respuesta"
        Previsto con $b = 0$: $a/R_\star \approx 19{,}5$ y $T_{14} \approx (10/\pi)/19{,}5 \approx 0{,}163$ d $\approx$ 3,9 h.

        Razón: 3,0/3,9 ≈ 0,77. Está entre 0,15 y 1,67: **pasa**.

        Con $T_{14}/T_{14}(b=0) \approx \sqrt{1-b^2}$: $1 - b^2 = 0{,}77^2 \approx 0{,}59$, así que $b \approx 0{,}64$. Un tránsito fuera del centro, perfectamente normal.

        Repasa: [M2](m2-transit-physics.md), ejercicios 1 y 3.

!!! question "10. Una señal NEW falla en secondary (4σ, 6 % del primario) y en edges_dumps; el centroide quedó sin datos. Calcula el score, el veredicto y la severidad."

    ??? success "Ver respuesta"
        `secondary` a 4σ es falla (≥ 3σ), sin veto (no llega a 5σ y está por debajo del 10 %): peso 0,4. Tampoco es un caso de período a la mitad, porque 6 % está lejos de la profundidad del primario. `edges_dumps` falló: peso 0,4. `centroid` sin datos: 0,95, pero "sin datos" no es una falla.

        Score = 0,4 × 0,4 × 0,95 ≈ **0,15**. Veredicto: **FAIL**, porque hay dos fallas leves y solo se tolera una. No se convierte en candidato, así que no tiene severidad. (Si el modelo calibrado le diera un `p_rank` por encima de su umbral de P2, podría rescatarse, pero solo hasta P2).

        Observa que ninguna prueba vetó, pero dos fallas leves bastaron. Desde el razonamiento físico también tiene sentido: una caída en fase 0,5 y tránsitos en bordes forman, juntos, un perfil poco convincente.

        Repasa: [M5](m5-vetting-in-practice.md), "El veredicto y el score".

## Siguiente paso

¿Aprobaste? El [nivel avanzado](../advanced/index.md) te lleva a los artículos originales (BLS, TLS, Robovetter, triceratops), al cálculo de la probabilidad de falso positivo, al benchmark con inyección de tránsitos sintéticos y a la preparación de un envío de CTOI.

Antes de irte, guarda el cuaderno de revisiones del nivel intermedio. Será el material de partida de la lección de aprendizaje automático.
