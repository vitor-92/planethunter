# Autoevaluación del nivel básico

<p class="meta">Nivel básico · fin de la semana 6 · cerca de 1 hora</p>

!!! abstract "Cómo hacerla"
    - Responde **sin consultar** las lecciones. Escribe las respuestas en tu cuaderno, con tus palabras y con las cuentas.
    - Solo después abre "Ver respuesta" y compara. Cuenta como correcta la respuesta que tiene la idea principal, aunque use otras palabras.
    - Las preguntas 1 a 6 son las del plan de estudios y deciden la aprobación. Las preguntas 7 a 10 son extras, para que compruebes si la base está sólida.

!!! warning "Criterio de aprobación"
    ¿Acertaste **al menos 5 de las 6 preguntas principales** (1 a 6)? Sigue al [nivel intermedio](../intermediate/index.md).

    ¿Fallaste dos o más? Vuelve a las lecciones indicadas en cada respuesta, deja pasar algunos días y repite la autoevaluación.

## Preguntas principales

!!! example "Pregunta 1"
    Un planeta con la mitad del radio de Júpiter transita una estrella igual al Sol. ¿Cuál es la profundidad aproximada, en ppm?

    ??? success "Ver respuesta"
        Usa $\delta \approx (R_p/R_\star)^2$.

        Júpiter tiene cerca de 0,1 R☉ (69 911 km / 696 000 km ≈ 0,100). La mitad de eso es 0,05 R☉. Entonces:

        $$ \delta \approx (0{,}05)^2 = 0{,}0025 $$

        Multiplicando por un millón: **cerca de 2 500 ppm** (0,25 %).

        Atajo: Júpiter da cerca de 10 000 ppm. La mitad del radio da un cuarto de la profundidad, porque la profundidad depende del **cuadrado** de la razón de los radios: $10\,000 / 4 = 2\,500$ ppm.

        Si respondiste 5 000 ppm, olvidaste el cuadrado. Repasa la [lección B2](b2-transit-method.md).

!!! example "Pregunta 2"
    ¿Por qué tres tránsitos igualmente espaciados son más convincentes que uno solo?

    ??? success "Ver respuesta"
        Tres motivos:

        1. **Periodicidad.** Una órbita se repite con regularidad de reloj. Un evento aislado puede ser casi cualquier cosa: un ajuste del telescopio, una rampa en el borde de los datos, un rayo cósmico, un salto instrumental. Tres caídas iguales, igualmente espaciadas, son muy difíciles de producir por casualidad.
        2. **Período y predicción.** Con un solo tránsito no se conoce el período, y sin período no se puede predecir el siguiente tránsito ni calcular la distancia del planeta a la estrella. Con dos o más tenemos la **efeméride** (período e instante del tránsito), que se puede poner a prueba en otros datos.
        3. **Pruebas posibles y señal más fuerte.** Con varios tránsitos se pueden comparar los impares con los pares, revisar si todos tienen la misma profundidad y sumarlos todos en el tránsito plegado, lo que aumenta el SNR.

        En la herramienta, la prueba `n_transits` **veta** las señales con menos de 2 tránsitos. Repasa las lecciones [B2](b2-transit-method.md) y [B4](b4-false-positives.md).

!!! example "Pregunta 3"
    ¿Qué significa Tmag 6 comparado con Tmag 13?

    ??? success "Ver respuesta"
        Tmag es el brillo de la estrella en la escala de magnitudes del TESS. La escala está **invertida**: un número menor quiere decir una estrella más brillante. Entonces la estrella de Tmag 6 es mucho más brillante que la de Tmag 13.

        ¿Cuánto más? La escala es multiplicativa: 5 magnitudes equivalen a 100 veces. La diferencia de 7 magnitudes da $2{,}512^7 \approx 630$. La estrella de Tmag 6 es **unas 630 veces más brillante**.

        Por qué importa: más luz significa menos ruido relativo, así que los tránsitos poco profundos se vuelven detectables. Y las estrellas brillantes facilitan mucho la confirmación con otros telescopios. Repasa la [lección B3](b3-tess-telescope.md).

!!! example "Pregunta 4"
    Menciona dos diferencias entre la curva de una binaria eclipsante y la de un planeta.

    ??? success "Ver respuesta"
        Dos cualesquiera de estas:

        - **Forma.** El planeta hace un tránsito con fondo casi plano (U). Una binaria rasante hace un eclipse puntiagudo (V).
        - **Impares y pares.** El planeta hace todos los tránsitos iguales. Una binaria, cuando el algoritmo encuentra la mitad del período verdadero, muestra tránsitos alternados con profundidades diferentes.
        - **Eclipse secundario.** La binaria muestra una segunda caída en la fase 0,5, cuando la compañera pasa detrás de la estrella principal. Un planeta común no muestra nada ahí (los planetas muy calientes muestran una ocultación pequeña, menor que el 10 % del tránsito).
        - **Profundidad y radio.** Las binarias suelen dar caídas muy profundas; el "planeta" calculado sale demasiado grande, del tamaño de una estrella.

        En PlanetHunter: pruebas `shape`, `odd_even`, `secondary` y `radius`. Repasa la [lección B4](b4-false-positives.md).

!!! example "Pregunta 5"
    ¿Por qué una señal puede venir de una estrella que no es el objetivo?

    ??? success "Ver respuesta"
        Porque cada píxel del TESS cubre **21 segundos de arco** del cielo, un área grande donde caben varias estrellas, y además la luz de cada estrella se reparte por píxeles vecinos. El brillo "del objetivo" es, en realidad, la suma de la luz de todas las estrellas de la región.

        Si una estrella vecina, más débil, es una binaria eclipsante, sus eclipses aparecen **diluidos** en la luz total y pueden imitar el tránsito poco profundo de un planeta en el objetivo. Ejemplo: una binaria que aporta el 1 % de la luz y tiene eclipses del 50 % produce una caída del 0,5 %, o 5 000 ppm.

        Cómo se investiga: la prueba de centroide (¿el centro de luz se desplaza durante el tránsito?), la imagen de diferencia (¿dónde desapareció la luz?) y la lista de vecinas de Gaia. Repasa las lecciones [B3](b3-tess-telescope.md) y [B4](b4-false-positives.md).

!!! example "Pregunta 6"
    ¿Cuál es la diferencia entre un TOI y un planeta confirmado?

    ??? success "Ver respuesta"
        Un **TOI** (*TESS Object of Interest*) es un **candidato**: una señal en los datos del TESS que el equipo de la misión examinó y consideró prometedora. Todavía puede ser un falso positivo. Muchos TOI terminan marcados por el TFOPWG como FP (falso positivo) o FA (falsa alarma).

        Un **planeta confirmado** tiene evidencia independiente del tránsito, obtenida con otros telescopios, en general la masa medida por velocidad radial. En el TFOPWG aparece como CP (confirmado) o KP (ya conocido).

        Entre los dos está el **planeta validado**: estadísticamente muy improbable de ser un falso positivo, con apoyo de imágenes de alta resolución, pero sin masa medida.

        La escalera completa: señal → candidato → CTOI → TOI → validado → confirmado. Repasa la [lección B3](b3-tess-telescope.md).

## Preguntas extra

!!! example "Pregunta 7"
    ¿Cuál es la probabilidad aproximada de que una Tierra a 1 UA de un Sol transite para nosotros? ¿Qué dice eso sobre las estrellas que no muestran tránsito?

    ??? success "Ver respuesta"
        $p \approx R_\star / a = 696\,000 / 149\,600\,000 \approx 0{,}0047$, cerca del **0,5 %**: una de cada 200.

        Consecuencia: la ausencia de tránsito casi nunca quiere decir ausencia de planeta. En la gran mayoría de los casos, la órbita simplemente no está alineada con nosotros. Y las búsquedas por tránsito favorecen a los planetas de período corto, que transitan con mayor probabilidad. Repasa la [lección B2](b2-transit-method.md).

!!! example "Pregunta 8"
    ¿Por qué un planeta de 2 R⊕ es mucho más fácil de encontrar alrededor de una enana roja de 0,3 R☉ que alrededor de una estrella de 1 R☉?

    ??? success "Ver respuesta"
        Porque la profundidad es $(R_p/R_\star)^2$. En la estrella de 1 R☉ (109 R⊕): $(2/109)^2 \approx 0{,}00034$, cerca de **340 ppm**. En la enana de 0,3 R☉ (cerca de 33 R⊕): $(2/33)^2 \approx 0{,}0037$, cerca de **3 700 ppm**, once veces más.

        El factor es $(1/0{,}3)^2 \approx 11$. Con el mismo ruido, una caída 11 veces mayor tiene un SNR 11 veces mayor. Además, los planetas en la zona habitable de las enanas rojas tienen períodos cortos, así que transitan más veces por sector. Repasa la [lección B2](b2-transit-method.md) y juega con el [simulador](../lab/transit-simulator.md).

!!! example "Pregunta 9"
    Una señal limpia, que pasó todas las pruebas básicas, aparece en un único sector de una estrella observada en 10 sectores. En los otros 9 no aparece. ¿Qué concluyes, y qué caso real del sector 69 se parece?

    ??? success "Ver respuesta"
        Casi seguro es un **defecto de ese sector** (sistemático), no un planeta. Un planeta transita siempre: si la señal fuera real, aparecería en los otros sectores con una fuerza comparable.

        Es el caso de **HD 271883**: señal de 6,61 días y 4 900 ppm, perfecta en el vetting básico, pero que no reapareció con la fuerza esperada (SNR esperado de 45 a 64) en los sectores 67, 68 y 97. La prueba `other_sectors`, del vetting profundo, lo resolvió. Repasa la [lección B4](b4-false-positives.md).

!!! example "Pregunta 10"
    Una señal muestra una caída pequeña en la fase 0,5, de cerca del 3 % de la profundidad del tránsito principal. ¿Eso prueba que es una binaria eclipsante?

    ??? success "Ver respuesta"
        **No.** Los planetas gigantes muy calientes brillan lo suficiente como para que el TESS vea su luz desaparecer cuando pasan detrás de la estrella. Eso es una **ocultación** y produce una caída pequeña en la fase 0,5. Fue lo que pasó con **WASP-18 b** (cerca de 340 ppm), que PlanetHunter reprobaba como binaria hasta que cambió la regla.

        La regla actual solo veta si el secundario es de al menos el **10 %** del principal. Con un 3 %, esta prueba no veta la señal. Las estrellas compañeras, que emiten mucha luz, producen secundarios grandes. Repasa la [lección B4](b4-false-positives.md).

## Próximo paso

¿Aprobaste? Felicitaciones: ya sabes qué estamos buscando y por qué es difícil. El [nivel intermedio](../intermediate/index.md) explica **cómo** decide la herramienta: estadística de las señales, física del tránsito con un poco más de matemática, periodogramas, Python con datos reales y vetting en la práctica.

Antes de empezar el intermedio, si todavía no lo hiciste, empieza la lección P1 de la [ruta de programación](../programming/index.md). Se vuelve necesaria a partir de la lección M4.
