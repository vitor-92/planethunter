# M2. Física del tránsito

<p class="meta">Nivel intermedio · semanas 3–5 · unas 12 horas</p>

!!! abstract "En esta lección vas a aprender"
    - La tercera ley de Kepler y cómo conecta el período, la distancia y la densidad de la estrella.
    - Cómo predecir la duración de un tránsito, la fórmula que usa la prueba `duration`.
    - Qué es el parámetro de impacto y por qué los tránsitos rasantes tienen forma de V.
    - Por qué el fondo del tránsito es redondeado (oscurecimiento del limbo).
    - La diferencia entre el eclipse secundario de una binaria y la ocultación de un planeta, con el caso de WASP-18 b.
    - Por qué un tránsito demasiado corto en una estrella gigante indica un blend.

## Tercera ley de Kepler

En 1619, Johannes Kepler descubrió que, cuanto más lejos está un planeta del Sol, más tiempo tarda en dar una vuelta. Después, Newton mostró la fórmula exacta. Para un planeta de masa despreciable en órbita circular de radio $a$ alrededor de una estrella de masa $M_\star$:

$$
P^2 = \frac{4\pi^2 a^3}{G M_\star}
$$

$G$ es la constante gravitacional. En palabras: el cuadrado del período es proporcional al cubo de la distancia.

Para los tránsitos, la distancia en kilómetros importa menos. Lo que importa es la distancia **en radios de la estrella**, $a/R_\star$. Y aquí pasa algo bonito. Escribe la masa de la estrella como volumen por densidad, $M_\star = \tfrac{4}{3}\pi R_\star^3 \rho_\star$, y sustituye:

$$
\left(\frac{a}{R_\star}\right)^3 = \frac{G \rho_\star P^2}{3\pi}
$$

El radio y la masa desaparecieron por separado. Solo quedó la **densidad media de la estrella**, $\rho_\star$. Dado el período, $a/R_\star$ depende solo de qué tan compacta es la estrella.

Dos valores para tener de referencia:

- La Tierra y el Sol: $a/R_\star \approx 215$. La densidad media del Sol es 1,41 g/cm³.
- Como $a/R_\star \propto P^{2/3}$, un planeta de 10 días alrededor del Sol tiene $a/R_\star = 215 \times (10/365{,}25)^{2/3} \approx 19{,}5$.

## La duración del tránsito

Piensa en el planeta como un auto en una pista circular. La pista mide $2\pi a$, y el auto tarda el período $P$ en dar una vuelta. Durante el tránsito, recorre solo el tramo que queda delante del disco de la estrella. En un tránsito central, ese tramo mide unos $2R_\star$ (más el diámetro del propio planeta). Entonces:

$$
T_{14} \approx \frac{P}{2\pi a} \times 2R_\star(1+k) = \frac{P}{\pi}\,\frac{R_\star}{a}\,(1+k)
$$

donde $k = R_p/R_\star$. $T_{14}$ es la duración total, del primer al cuarto contacto (desde que el planeta toca el disco por primera vez hasta que sale por completo).

La forma exacta, que usa PlanetHunter en la función `predicted_duration_days` de `vetting/basic.py`, para órbita circular y tránsito central ($b = 0$):

$$
T_{14} = \frac{P}{\pi}\,\arcsin\!\left(\frac{1+k}{a/R_\star}\right), \qquad \frac{a}{R_\star} = \left(\frac{G\rho_\star P^2}{3\pi}\right)^{1/3}
$$

Como $a/R_\star$ suele ser mucho mayor que 1, el arcoseno casi no cambia el resultado. Juntando todo, la duración crece con $P^{1/3}$ y baja con $\rho_\star^{1/3}$. Las estrellas grandes y poco densas (gigantes) tienen tránsitos largos. Las estrellas pequeñas y densas (enanas rojas) tienen tránsitos cortos.

Duraciones previstas para un tránsito central en una estrella igual al Sol:

| Período | 1 d | 3 d | 5 d | 10 d | 20 d | 40 d | 1 año |
|---|---|---|---|---|---|---|---|
| $T_{14}$ (b = 0) | 1,8 h | 2,6 h | 3,1 h | 3,9 h | 4,9 h | 6,2 h | 13,0 h |

!!! example "Ejercicio 1"
    Estima la duración de un tránsito central ($b = 0$) de un planeta con período de 10 días en una estrella igual al Sol. Usa $T_{14} \approx (P/\pi)(R_\star/a)$, ignorando el tamaño del planeta. Después compáralo con el valor de un dossier real.

    ??? success "Ver respuesta"
        **Paso 1: $a/R_\star$.** Por la escala con la Tierra: $a/R_\star = 215 \times (10/365{,}25)^{2/3}$. La razón 10/365,25 = 0,0274. Elevada a 2/3: 0,0908. Entonces $a/R_\star = 215 \times 0{,}0908 \approx 19{,}5$.

        Comprobación con la fórmula de la densidad: $\rho_\odot = 1410$ kg/m³, $P = 864\,000$ s, $G = 6{,}674 \times 10^{-11}$. $G\rho P^2/(3\pi) = 6{,}674\times10^{-11} \times 1410 \times 7{,}46\times10^{11} / 9{,}42 \approx 7\,450$. Raíz cúbica: **19,5**. Coincide.

        **Paso 2: duración.** $T_{14} \approx (10/\pi) \times (1/19{,}5) = 3{,}183 / 19{,}5 = 0{,}163$ días. En horas: 0,163 × 24 ≈ **3,9 horas**.

        Con un planeta del tamaño de la Tierra ($k \approx 0{,}009$), multiplica por 1,009: sigue dando 3,9 h. Con la fórmula exacta (arcoseno), da 3,91 h. La aproximación es excelente.

        **Comparación.** En un dossier, la tabla de vetting muestra en la fila `duration` algo como "T14 3.11 h vs predicted (b=0) 3.79 h" (duración observada frente a la prevista con $b = 0$). Ese es el caso de Pi Men c (período 6,27 d, estrella con 1,15 R☉ y 1,1 M☉). Si la estrella se parece al Sol y el período está cerca de 10 días, espera un valor previsto cercano a 3,9 h, y uno observado igual o menor.

!!! tip "En la herramienta"
    La prueba `duration` divide la duración observada (del ajuste de trapecio) entre la prevista con $b = 0$. Pasa si la razón está entre **0,15** y **1,67** (`duration_ratio_min` y `duration_ratio_max`). La masa viene del TIC; si falta, se estima a partir de $\log g$ y del radio. Sin el radio de la estrella, o cuando el ajuste choca con el borde de su rango permitido (entonces la duración no está realmente medida), la prueba queda "sin datos" y el score se multiplica por 0,95. Fallar es una falla leve que cuesta un factor de 0,6 en el score. En el dossier, la sección **Parameters** (parámetros) muestra R* (R☉), M* (M☉) y T14 (h).

### Por qué más de 1,67 es sospechoso

Para una órbita circular, el tránsito central es el **más largo posible**. Cualquier inclinación acorta la cuerda. Así que una duración mucho mayor que la prevista con $b = 0$ dice que alguna premisa falló:

- la estrella es más grande y menos densa de lo que dice el TIC (una subgigante catalogada como enana);
- la señal viene de **otra** estrella, más grande, en el mismo píxel;
- la órbita es excéntrica, y el tránsito ocurre lejos del punto más cercano a la estrella;
- el período está mal.

¿Por qué 1,67 y no apenas por encima de 1? Porque el radio estelar del TIC tiene errores y una órbita excéntrica puede alargar un tránsito (Kipping 2010). El límite de 1,67 es el que usa LEO-Vetter (Kunimoto et al. 2025). El proyecto usaba antes 1,3; cuando midió el cambio, subir el límite a 1,67 no hizo reprobar a ningún planeta conocido y dejó de reprobar a decenas de señales nuevas cuyo único problema era un tránsito algo largo.

Caso real del sector 69: TOI-724.01 mostró T14 = 8,40 h contra 3,56 h previstas, una razón de 2,36. Falla leve en `duration`.

### Por qué menos de 0,15 es sospechoso: la señal 1594

En la primera porción real del sector 69 (2164 estrellas), la señal **1594** llegó a P1 con score 1,0. ¿Un candidato perfecto? Los números del dossier:

- estrella TIC 31273263: radio 3,06 R☉, masa 1 M☉. Es una **gigante** (o subgigante): tres veces el radio del Sol con la misma masa;
- período 6,354 d, profundidad 1 091 ppm;
- duración observada: **0,58 h**;
- duración prevista con $b = 0$: **10,71 h**. Razón: 0,054.

Una gigante tiene una densidad bajísima: $\rho = 1/3{,}06^3 \approx 0{,}035$ veces la del Sol. Por eso $a/R_\star$ es pequeño (unos 4,7) y un planeta tarda horas en cruzar el disco enorme. Un tránsito de media hora no encaja con esa estrella.

Para acortarlo de 10,7 h a 0,58 h (factor 18,5) cambiando solo la estrella, la densidad tendría que ser $18{,}5^3 \approx 6\,300$ veces mayor. Ni una enana roja llega a tanto. Las explicaciones plausibles son: la señal viene de **otra estrella**, más pequeña y densa, mezclada en el mismo píxel (un **blend**), probablemente con un eclipse rasante; o es un tránsito extremadamente rasante ($b \approx 0{,}99$) en la propia gigante; o no es un tránsito. En cualquier caso, no es un candidato fuerte. Hay otro indicio en la misma dirección: la estrella ya tiene objetos catalogados, y el código de severidad (`alerts/severity.py`) cita la señal 1594 como ejemplo de estrella que es una binaria eclipsante catalogada, caso en el que una señal nueva casi siempre es un eclipse.

Esta señal motivó el límite inferior `duration_ratio_min: 0.15`, con el comentario en `config/thresholds.yaml` que cita la propia señal 1594. Con la regla actual, esta falla multiplica el score por 0,6, y deja de ser P1.

!!! example "Ejercicio 2"
    Rehaz la predicción de la señal 1594. Datos: $P = 6{,}354$ d, $R_\star = 3{,}06$ R☉, $M_\star = 1$ M☉, $k = 0{,}033$. Usa la escala con el Sol: $a/R_\star = 215 \times (P/365{,}25)^{2/3} \times (\rho_\star/\rho_\odot)^{1/3}$.

    ??? success "Ver respuesta"
        Densidad relativa: $\rho_\star/\rho_\odot = M/R^3 = 1/28{,}65 = 0{,}0349$. Raíz cúbica: 0,327.

        Período: $6{,}354/365{,}25 = 0{,}0174$. Elevado a 2/3: 0,0671.

        $a/R_\star = 215 \times 0{,}0671 \times 0{,}327 \approx 4{,}72$.

        $T_{14} = (P/\pi)\arcsin((1+k)/(a/R_\star)) = 2{,}023 \times \arcsin(1{,}033/4{,}72) = 2{,}023 \times \arcsin(0{,}219) = 2{,}023 \times 0{,}221 = 0{,}447$ d = **10,7 h**. Exactamente el valor del dossier.

        Razón observada/prevista: 0,58/10,7 = 0,054, por debajo de 0,15. Falla.

## Parámetro de impacto y la forma de V

El **parámetro de impacto** $b$ indica por dónde cruza el planeta el disco de la estrella, medido en radios estelares desde el centro:

$$
b = \frac{a\cos i}{R_\star}
$$

donde $i$ es la inclinación de la órbita (90° = vista exactamente de canto).

- $b = 0$: el planeta pasa por el centro. Cuerda más larga.
- $b = 0{,}7$: pasa por arriba, cuerda más corta.
- $b \approx 1$: roza el borde. Tránsito **rasante**.

La longitud de la cuerda es proporcional a $\sqrt{(1+k)^2 - b^2}$. Para planetas pequeños, $T_{14} \approx T_{14}(b=0)\sqrt{1-b^2}$. Esto explica por qué la razón de la prueba `duration` suele quedar por debajo de 1 en los planetas reales.

!!! example "Ejercicio 3"
    En el sector 1, PlanetHunter midió para Pi Men c: T14 = 3,11 h, previsto con $b = 0$: 3,79 h. Estima el parámetro de impacto.

    ??? success "Ver respuesta"
        Razón: 3,11/3,79 = 0,82. Con $T_{14}/T_{14}(b=0) \approx \sqrt{1-b^2}$: $1 - b^2 = 0{,}82^2 = 0{,}672$, entonces $b^2 = 0{,}328$ y **$b \approx 0{,}57$**.

        Es una estimación burda: el ajuste de trapecio, el radio del TIC y la masa estimada tienen incertidumbre. Busca en el NASA Exoplanet Archive el valor publicado para Pi Men c y compáralo.

### Las rampas del tránsito

Un tránsito tiene cuatro contactos. Entre el 1.º y el 2.º, el planeta está **entrando** en el disco (rampa de bajada, duración $\tau$). Entre el 2.º y el 3.º, está entero delante de la estrella (fondo). Entre el 3.º y el 4.º, está saliendo (rampa de subida).

Para planetas pequeños y $b$ no muy cerca de 1 (Winn, 2010):

$$
\frac{\tau}{T_{14}} \approx \frac{k}{1-b^2}
$$

Dos cosas alargan las rampas:

1. **$k$ grande.** Un planeta pequeño entra rápido: $k = 0{,}016$ da rampas finísimas. Una estrella compañera con la mitad del radio de la primaria ($k = 0{,}5$) pasa casi la mitad del eclipse entrando.
2. **$b$ cerca de 1.** En un tránsito rasante, el planeta nunca queda entero sobre el disco. No hay fondo plano.

En el límite, las rampas se juntan en el medio y el tránsito se vuelve un **triángulo**: la forma de V. Una caja o una U sugiere un planeta. Una V sugiere una binaria o un rasante.

!!! tip "En la herramienta"
    La prueba `shape` ajusta un **trapecio** a la curva plegada y mide $\tau/T_{14}$. El valor 0,5 es un triángulo perfecto. El límite actual es **0,35** (`v_shape_max`). La misma prueba reprueba si $R_p/R_\star > 0{,}3$ (`rp_rs_max`), tamaño de estrella, no de planeta.

    La calibración se midió en el sector 69. Con un límite de 0,45, la prueba no atrapaba **ningún** falso positivo. Con 0,35, atrapa **8 de 18** falsos positivos del TFOPWG y marca **3 de 50** planetas, todos rasantes reales: HIP 65 A b, LTT 9779 b y TOI-2382 b. Por eso empezó como falla leve (peso 0,5). Desde la auditoría del 2026-10-10 es una **falla dura**: una falla sola reprueba el veredicto, aunque sigue sin ser un veto. El costo medido es de unos 3 planetas rasantes por sector; la ganancia es frenar binarias eclipsantes encontradas a la mitad de su período.

    Valores medidos: Pi Men c 0,11; WASP-18 b 0,14; los falsos positivos TOI-297.01 0,42, TOI-4858.01 0,41 y TOI-189.01 0,41.

## Oscurecimiento del limbo

Mira una foto del Sol: el centro es más brillante que el borde. Eso es el **oscurecimiento del limbo** (*limb darkening*). En el borde, tu línea de visión atraviesa la atmósfera de la estrella de costado y solo ve las capas más altas, que son más frías y emiten menos.

Consecuencia para el tránsito: cuando el planeta está en el centro del disco, tapa la región más brillante, y la caída es mayor. Cerca del borde, tapa una región más oscura, y la caída es menor. El fondo del tránsito deja de ser plano y se vuelve **redondeado**, con forma de U.

Esto afecta la medición de la profundidad. Para Pi Men c en el sector 1:

| Modelo | Profundidad |
|---|---|
| Caja (BLS de Lightkurve, lección M4) | 228 ppm |
| Trapecio (vetting de PlanetHunter) | 272 ppm |
| Modelo de TLS, con oscurecimiento del limbo | 287 ppm |

La caja promedia el tránsito entero, incluidas las rampas y las partes poco profundas de la U. El modelo con oscurecimiento del limbo captura el fondo más profundo. Por eso TLS, que usa ese modelo, es más sensible que BLS (lección [M3](m3-periodograms.md)).

El redondeo también infla un poco el $\tau/T_{14}$ medido por el trapecio: el ajuste interpreta la curvatura del fondo como rampa. Por eso los planetas de verdad aparecen con 0,1 a 0,15, y no con el valor geométrico de 0,02.

## Eclipse secundario y ocultación planetaria

En una órbita circular, medio período después del tránsito, el objeto pasa **detrás** de la estrella. Lo que se ve en ese momento, en **fase 0,5**, depende de cuánto brilla.

- **Binaria eclipsante.** La compañera es una estrella y tiene luz propia. Cuando queda oculta, el brillo total baja: es el **eclipse secundario**. Si las dos estrellas son parecidas, los dos eclipses tienen profundidades parecidas.
- **Planeta.** El planeta brilla muy poco: luz reflejada y calor. Cuando desaparece detrás de la estrella, la caída es minúscula. Se llama **ocultación**. Para casi todos los planetas, es invisible para TESS.

La excepción son los **Júpiter ultracalientes**. WASP-18 b orbita su estrella en menos de un día y es tan caliente que TESS ve desaparecer su luz. La documentación del proyecto registra unas 340 ppm en fase 0,5. En la corrida final del sector 69, la prueba `secondary` midió 276 ppm, **3 % del primario** (que tiene unas 10 300 ppm), con una significancia de 8 sigma. Una caída real y significativa en fase 0,5, en un planeta confirmado.

En el primer día del proyecto, WASP-18 b quedaba **vetado como binaria**. La corrección se apoyó en la física: la ocultación de un planeta es una fracción pequeña del tránsito, mientras que el secundario de una binaria suele ser una fracción grande. La regla actual veta solo si se cumplen las dos condiciones a la vez:

- secundario con más de 5 sigma (`secondary_veto_sigma`), **y**
- secundario con el 10 % o más de la profundidad del primario (`secondary_veto_ratio: 0.1`).

Entre 3 y 5 sigma, o por encima de 5 sigma pero por debajo del 10 %, es una falla leve (peso 0,4).

Casos del sector 69 vetados por secundario: TOI-287.01 (4 503 ppm en fase 0,5, 37 % del primario), TOI-349.01 (1 376 ppm, 13 %) y TOI-187.01 (108 %, o sea, dos eclipses prácticamente iguales). Todos son falsos positivos del TFOPWG.

!!! warning "Órbitas excéntricas"
    Si la órbita es excéntrica, el secundario no cae en fase 0,5. La prueba `secondary_scan` busca la mayor caída en cualquier fase entre 0,1 y 0,9, con un límite más alto (5 sigma), porque mira en muchos lugares (recuerda el efecto de mirar en todas partes, lección M1). Se creó porque la binaria excéntrica TOI-367.01 pasaba todas las pruebas.

!!! example "Ejercicio 4"
    Decide, con las reglas de PlanetHunter, el resultado de la prueba `secondary` en cada caso:

    a) Primario de 8 000 ppm; caída en fase 0,5 de 400 ppm con 9 sigma.
    b) Primario de 3 000 ppm; caída en fase 0,5 de 600 ppm con 6 sigma.
    c) Primario de 3 000 ppm; caída en fase 0,5 de 600 ppm con 4 sigma.

    ??? success "Ver respuesta"
        a) Razón 400/8 000 = 5 %. Significativo (9 > 5 sigma), pero por debajo del 10 %. **Falla leve, sin veto.** Compatible con la ocultación de un planeta muy caliente, como WASP-18 b.

        b) Razón 600/3 000 = 20 %, y 6 > 5 sigma. **Veto.** Perfil de binaria eclipsante.

        c) Razón 20 %, pero solo 4 sigma: supera los 3 sigma (falla) y no llega a 5 (sin veto). **Falla leve.** Vale la pena mirar el panel "Odd, even and secondary" (impar, par y secundario) del dossier y buscar el secundario en otros sectores.

## Resumen: de la física a la prueba

| Física | Magnitud | Prueba del vetting |
|---|---|---|
| Kepler + densidad estelar | $T_{14}$ previsto | `duration` |
| Parámetro de impacto, $k$ grande | $\tau/T_{14}$ | `shape` |
| Profundidad $\approx k^2$ | $R_p$ | `radius`, `shape` ($R_p/R_\star$) |
| Compañera luminosa | caída en fase 0,5 | `secondary` |
| Órbita excéntrica | caída en otra fase | `secondary_scan` |

## Checklist de la lección

- [ ] Sé escribir la tercera ley de Kepler y explicar por qué $a/R_\star$ depende solo de la densidad de la estrella.
- [ ] Calculé la duración de un tránsito de 10 días en una estrella como el Sol (unas 3,9 h).
- [ ] Sé por qué una razón por encima de 1,67 o por debajo de 0,15 en la prueba `duration` es sospechosa.
- [ ] Sé explicar el parámetro de impacto y por qué los rasantes y las binarias tienen forma de V.
- [ ] Sé por qué el fondo del tránsito es redondeado y por qué la caja subestima la profundidad.
- [ ] Sé la diferencia entre eclipse secundario y ocultación, y la regla del 10 %.
- [ ] Abrí un dossier y leí las notas de `duration`, `shape` y `secondary` en la tabla de vetting.

## Para ir más allá

- Winn (2010), "Transits and Occultations", gratis en arXiv ([arXiv:1001.2010](https://arxiv.org/abs/1001.2010)). Secciones 1 a 3. Es el texto clásico: todas las fórmulas de esta lección están ahí, con sus deducciones.
- Seager & Mallén-Ornelas (2003), *The Astrophysical Journal* 585, 1038. Muestra cómo obtener la densidad de la estrella solo a partir de la forma del tránsito; la base de la prueba `duration`.
- Página de Pi Men c en el NASA Exoplanet Archive ([exoplanetarchive.ipac.caltech.edu](https://exoplanetarchive.ipac.caltech.edu)): compara el parámetro de impacto publicado con el que estimaste en el ejercicio 3.
- [Simulador de tránsito](../lab/transit-simulator.md) de este curso: cambia los parámetros y mira cómo responde la forma de la curva.
