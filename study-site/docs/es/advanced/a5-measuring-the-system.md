# A5. Medir el sistema: completitud y benchmarks

<p class="meta">Nivel avanzado · semanas 11–13 · cerca de 14 horas</p>

!!! abstract "En esta lección vas a aprender"
    - La diferencia entre recall, completitud y precisión, y qué pregunta responde cada una.
    - Cómo funciona el benchmark de recall del proyecto y por qué la métrica principal es el recall en los TOIs "detectables en un sector".
    - Cómo calcular el intervalo de Wilson a mano y por qué es mejor que el intervalo "más o menos".
    - Cómo se hace injection-recovery: grilla de parámetros, inyección en el flujo bruto, criterio de recuperación.
    - Qué es el piso de ruido medido por el proyecto (mediana 5,2; p90 19; p99 98) y por qué un límite fijo no sirve.
    - La metodología antes/después para cambiar un límite, y cómo hacerlo tú mismo.

Una regla del proyecto resume esta lección: **cambiar la búsqueda o el vetting exige volver a correr el benchmark y adjuntar el antes y el después**. Sin medición, un cambio es una opinión.

## 1. Tres preguntas, tres métricas

| Métrica | Pregunta | Cómo se mide |
|---|---|---|
| **Recall** | De los objetos reales que existen en el conjunto, ¿cuántos encuentra el sistema? | Recuperados ÷ total de objetos reales conocidos |
| **Completitud** | ¿Cómo varía el recall con el período, el radio y el brillo de la estrella? | Recall por celda de una grilla de parámetros, en general con inyecciones |
| **Precisión** | De las alertas que emite el sistema, ¿cuántas son reales? | Alertas confirmadas ÷ alertas emitidas (exige revisión humana o seguimiento) |

El recall y la precisión tiran en direcciones opuestas. Aflojar un límite aumenta el recall y derrumba la precisión. Todo cambio necesita medir las dos, o un sustituto razonable de la segunda. En el vetting, el proyecto usa la **tasa de aprobación de `KNOWN_FP`** como sustituto: si sube, el vetting quedó flojo.

## 2. El benchmark de recall del proyecto

El código está en `src/planethunter/benchmark.py`. El procedimiento:

1. **Congelar una lista** (`benchmark build`). Del ExoFOP se toman los TOIs con disposición CP, KP o PC, "Planet SNR" ≥ 10 y período entre 0,5 y 13 días que fueron observados en el sector 69. Resultado: **220 TOIs**. La lista queda grabada en CSV y ya no cambia, para que ejecuciones diferentes sean comparables.
2. **Correr la búsqueda** solo en esos objetivos (`benchmark run`). **185** tienen curva SPOC de 2 minutos.
3. **Evaluar**: un TOI se considera recuperado si alguna señal del run coincide con el período (alias 1, 2 o 1/2) **y** con la fase. Los aliases 3, 1/3, 3/2 y 2/3 se cuentan aparte, como "encontrado con período ambiguo".

### Por qué "detectables en un sector"

En el primer run se perdieron 68 TOIs. Al investigar, **55 de ellos tenían un SNR esperado por debajo de 7 solo con los datos del sector 69**. El "Planet SNR" del ExoFOP suma todos los sectores en los que se observó la estrella. Con un solo sector, ningún pipeline encontraría esos objetos. Contarlos como falla mediría el tamaño del conjunto de datos, no la calidad de la búsqueda.

Por eso el benchmark calcula, para cada TOI, el **SNR esperado** en este sector:

$$
\text{SNR}_\text{esperado} = \frac{\delta}{\sigma_\text{p2p}} \sqrt{N_\text{en tránsito}},
\qquad
\sigma_\text{p2p} = \frac{\text{desviación estándar}(\text{diferencias entre puntos vecinos})}{\sqrt{2}} ,
$$

con la profundidad del catálogo, el ruido punto a punto de la curva ya tratada y el número de puntos que caen dentro de los tránsitos previstos. Un TOI es **detectable** si el SNR esperado es ≥ 7,1 y hay al menos 2 épocas con datos. Son **135**. Se usa el ruido punto a punto porque es poco sensible a variaciones lentas: mide el "siseo" de un punto al siguiente.

### El historial

| Run | Cambio | Recall detectables |
|---|---|---|
| baseline | ventana 1,0 d, límites estelares ±30 % | 114/135 = 84,4 % |
| 2 | grilla de duraciones amplia + ventana adaptativa | 117/135 = 86,7 % |
| 3 | variantes de detrending (suma) + modelo estelar limitado a 1,5 | 120/135 = 88,9 % |
| 4 | `refine_alias` + `period_max` 0,9 × intervalo | **123/135 = 91,1 %** (IC 95 % 85,1–94,8 %) |

Y por profundidad, en el run final:

| Profundidad (ppm) | Recuperados | Total | Recall |
|---|---|---|---|
| 0–500 | 6 | 10 | 60 % |
| 500–1 000 | 11 | 13 | 85 % |
| 1 000–3 000 | 19 | 23 | 83 % |
| 3 000–10 000 | 34 | 36 | 94 % |
| más de 10 000 | 53 | 53 | 100 % |

La meta del plan es ≥ 90 %. El número agregado pasa, pero la tabla muestra dónde está el problema: los tránsitos poco profundos. Ahí es donde el próximo trabajo rinde.

## 3. Intervalo de Wilson

Con 135 objetos, 91,1 % no es un número exacto. Si el proyecto corriera en otro sector con otros 135 TOIs, el resultado sería un poco diferente. El **intervalo de confianza** dice cuánto.

El intervalo "ingenuo" ($p \pm 1{,}96\sqrt{p(1-p)/n}$) falla justamente donde más importa: cerca de 0 % o 100 % y con muestras pequeñas. Con 53 de 53, da ancho cero, como si 100 % fuera certeza. El **intervalo de Wilson** (Wilson 1927) corrige eso. Con $p = k/n$ y $z = 1{,}96$ para 95 %:

$$
\text{centro} = \frac{p + \dfrac{z^2}{2n}}{1 + \dfrac{z^2}{n}},
\qquad
h = \frac{z\sqrt{\dfrac{p(1-p)}{n} + \dfrac{z^2}{4n^2}}}{1 + \dfrac{z^2}{n}},
\qquad
\text{IC} = [\text{centro} - h,\ \text{centro} + h] .
$$

Es exactamente lo que calcula la función `wilson` de `benchmark.py`.

### La cuenta para 123 de 135

1. $p = 123/135 = 0{,}9111$; $z^2 = 3{,}8416$; $z^2/n = 0{,}02846$; denominador $= 1{,}02846$.
2. Centro: $(0{,}9111 + 3{,}8416/270)/1{,}02846 = (0{,}9111 + 0{,}01423)/1{,}02846 = 0{,}8997$.
3. $p(1-p)/n = 0{,}9111 \times 0{,}0889/135 = 0{,}000600$; $z^2/(4n^2) = 3{,}8416/72\,900 = 0{,}0000527$; suma $0{,}000653$; raíz $0{,}02555$.
4. $h = 1{,}96 \times 0{,}02555 / 1{,}02846 = 0{,}0487$.
5. IC $= [0{,}851;\ 0{,}948]$, o sea **85,1 % a 94,8 %**. Coincide con el informe.

Fíjate que el centro (90,0 %) es un poco menor que $p$: Wilson "empuja" la estimación lejos de los extremos, lo cual es honesto con muestras finitas.

## 4. Injection-recovery

El benchmark en TOIs mide el sistema **en lo que ya se sabe**. Pero los TOIs son, en general, profundos y en estrellas brillantes. Para medir los nichos donde el proyecto quiere encontrar cosas nuevas (poco profundos, de período largo, estrellas débiles), no hay suficientes TOIs. La solución es fabricar la prueba: **inyectar tránsitos sintéticos en curvas reales** y ver cuáles recupera el sistema. Es el mismo principio que usó Kepler para medir la completitud de su pipeline (Christiansen et al. 2013).

La receta está en la skill `injection-recovery` del proyecto:

**Dónde inyectar.** En el flujo **bruto**, antes del detrending. Así la medida incluye la pérdida causada por el propio detrending, que la lección A1 mostró que es grande (hasta 40 % con ventana corta).

**Cómo generar.** Con la biblioteca `batman` (Kreidberg 2015): modelo de tránsito con oscurecimiento de borde cuadrático, coeficientes elegidos según la temperatura de la estrella, $a/R_\star$ calculado a partir de la densidad estelar y el parámetro de impacto sorteado.

**La grilla.**

| Eje | Valores |
|---|---|
| Período (d) | 0,5; 1; 2; 4; 8; 13; 20; 27; 40 |
| Radio del planeta (R⊕) | 1; 1,5; 2; 3; 4; 6; 10; 15 |
| Parámetro de impacto $b$ | 0; 0,3; 0,6; 0,9 |
| Tmag del objetivo | 8–10; 10–12; 12–13,5; 13,5–15 |

**Las curvas.** 200 curvas reales **sin señal** (SDE < 6 en la búsqueda original) por rango de Tmag. Al menos 50 inyecciones por celda, con época aleatoria.

**El criterio.** Recuperado si el período encontrado está a menos de 1 % del inyectado (o alias 2 o 1/2) y el SDE supera el límite. Guarda también la profundidad y el SDE medidos, para estimar el sesgo (¿el detrending encoge los tránsitos?).

**El informe.** Mapa de completitud (período × radio) por rango de Tmag, con intervalo de Wilson en cada celda.

Estado en el código: el benchmark de recall está implementado; el injection-recovery con grilla **todavía no**. Es el próximo paso, y un excelente proyecto para quien termine este nivel.

## 5. El piso de ruido: 5,2, 19 y 98

La prueba `other_sectors` (lección A2) busca la señal en otros sectores con una búsqueda **en un rango estrecho** alrededor del período: 300 períodos a ±1 % de $P$ y otros 300 alrededor de $2P$, con tres duraciones. Parece una búsqueda pequeña. No lo es.

El proyecto midió lo que esa búsqueda encuentra **en estrellas sin señal**, en 144 intentos con períodos aleatorios en el sector 69. El SNR del mejor pico:

| Estadística | SNR encontrado en el ruido |
|---|---|
| Mediana | 5,2 |
| Percentil 90 | 19 |
| Percentil 99 | 98 |

En 10 % de los intentos, el ruido por sí solo dio un SNR mayor a 19. En 1 %, mayor a 98. Se suman dos causas: el efecto de mirar en otro lugar (cientos de períodos, varias duraciones, todas las fases, y se guarda el máximo) y el **ruido rojo** con sistemáticos residuales, que produce caídas coherentes de varias horas.

La consecuencia: **un límite fijo de SNR no sirve** para decidir si la señal "apareció" en otro sector. El proyecto mide el piso **de cada estrella**: corre la misma búsqueda en 40 períodos aleatorios (entre 0,6 y 1,7 veces $P$, lejos de $P/2$, $P$ y $2P$) y usa el percentil 90 como piso. Antes de medirlo, se enmascaran los tránsitos del propio candidato. Sin la máscara, una señal fuerte elevaba su propio piso (un SNR de 2 192 frente a un piso de 2 272), y 16 de 24 fallas de esta prueba eran falsas. Una ausencia solo cuenta como evidencia si el SNR esperado es al menos 10 **y** al menos 1,5 veces el piso. El veto exige ausencia decisiva en al menos dos sectores.

Los casos reales muestran las dos caras:

- **HD 271883** (señal 1798, 6,61 d): SNR esperado de 45 a 64 en los sectores 67, 68 y 97. No apareció. Ausencia decisiva: veto.
- **Señal 1634** (11,35 d): SNR esperado de 12 y 9 en los sectores 95 y 96, con pisos de 13,5 y 11,6. Ahí la ausencia **no es evidencia**: el ruido de la propia estrella produciría picos de ese tamaño. La decisión vino de la búsqueda a ciegas en los sectores 95 a 97, que no recuperó ni 11,35 ni 22,7 días.

## 6. La metodología antes/después

Para cualquier cambio en `config/thresholds.yaml` o en el código de búsqueda y vetting:

1. **Hipótesis con mecanismo.** No "creo que 1,2 es mejor que 1,3", sino "los TOIs X e Y se pierden porque el detrending deja variabilidad; reducir la ventana en esas estrellas debería recuperarlos".
2. **Criterio de éxito y de abandono, escrito antes.** Por ejemplo: "acepto si el recall de los detectables no baja y se recuperan al menos 2 de los 11 perdidos; abandono si algún planeta `KNOWN_PLANET` pasa a ser vetado".
3. **Misma lista congelada y mismos espejos.** Anota el `params_hash` y la `pipeline_version` que graba el informe.
4. **Un cambio a la vez.** Dos cambios juntos hacen imposible saber cuál hizo qué.
5. **Correr antes y después** con el mismo código, salvo el cambio.
6. **Comparar de forma pareada.** Los dos runs usan los **mismos** objetos. No basta comparar los intervalos de confianza, que casi siempre se superponen. Lista los objetos que **cambiaron de estado**: ganancias y pérdidas.
7. **Medir el otro lado.** Tasa de aprobación de `KNOWN_PLANET` y de `KNOWN_FP` (tabla del `vet`), tiempo de búsqueda.
8. **Escribir** `docs/benchmarks/<fecha>-<sha>.md` con tabla antes/después, lista de cambios de estado y decisión.

### Comparación pareada en una línea

Si el cambio hizo que $g$ objetos pasaran de perdidos a recuperados y que $l$ hicieran lo contrario, y si el cambio no tuviera ningún efecto, cada uno de esos $g + l$ casos tendría 50 % de probabilidad de ir hacia cada lado. La probabilidad de un resultado tan desequilibrado por azar es la de la **prueba de McNemar** exacta, una cuenta de cara o cruz:

$$
p = 2 \times P\big(X \ge \max(g, l)\big), \qquad X \sim \text{Binomial}(g + l,\ 0{,}5) .
$$

!!! tip "En la herramienta"
    - `uv run planethunter benchmark build 69` congela la lista de planetas; con `--kind fp`, la de falsos positivos del TFOPWG.
    - `uv run planethunter benchmark run 69 --skip-ingest` rehace la búsqueda y graba el informe en `docs/benchmarks/`. Con `--run <run_id>`, solo reevalúa un run existente.
    - `uv run planethunter vet <run_id>` imprime la tabla de validación por clase (`KNOWN_PLANET`, `KNOWN_FP`...).
    - Los informes existentes: `2026-10-09-s0069-history.md` y `2026-10-09-s0069-vetting.md`.

!!! example "Ejercicio 1. Cien por ciento, pero ¿cuánto?"
    En el rango de profundidad mayor a 10 000 ppm, el recall fue 53/53. Calcula el límite inferior del intervalo de Wilson.

    ??? success "Ver respuesta"
        Con $k = n$, $p = 1$ y el término $p(1-p)/n$ desaparece. Entonces $h = (z^2/2n)/(1 + z^2/n)$ y el centro es $(1 + z^2/2n)/(1 + z^2/n)$. El límite inferior queda:

        $$
        \frac{1}{1 + z^2/n} = \frac{1}{1 + 3{,}8416/53} = \frac{1}{1{,}0725} \approx 0{,}932 .
        $$

        "100 %" quiere decir, con 95 % de confianza, **al menos 93 %**. El intervalo ingenuo diría "100 % ± 0", lo cual es falso.

!!! example "Ejercicio 2. ¿Vale la pena endurecer la forma en V?"
    El proyecto cambió `v_shape_max` de 0,45 a 0,35. Con 0,45, la prueba `shape` no detectaba ninguno de los 18 FPs del TFOPWG. Con 0,35, detecta 8 de 18 y marca 3 de 50 planetas (HIP 65 A b, LTT 9779 b y TOI-2382 b, todos rasantes). (a) Calcula el IC de Wilson para 8/18. (b) ¿Se justifica el cambio? ¿Qué precaución se tomó?

    ??? success "Ver respuesta"
        (a) $p = 0{,}444$, $z^2/n = 0{,}2134$, denominador $1{,}2134$. Centro $= (0{,}444 + 0{,}1067)/1{,}2134 = 0{,}454$. $p(1-p)/n = 0{,}01372$; $z^2/(4n^2) = 0{,}00296$; suma $0{,}01668$; raíz $0{,}1292$; $h = 1{,}96 \times 0{,}1292/1{,}2134 = 0{,}209$. IC $\approx$ **25 % a 66 %**. Con 18 objetos, la incertidumbre es enorme.

        (b) Incluso en el peor caso (25 %), pasar de 0 a al menos un cuarto de los FPs es una ganancia real. El costo son 3 planetas rasantes marcados. La precaución de entonces: la prueba se convirtió en **falla leve** (peso 0,5 en el score), no en veto, así que un planeta rasante podía seguir en la cola si el resto estaba limpio. Desde la auditoría del 2026-10-10 `shape` es una **falla dura** (una falla sola reprueba el veredicto, sin ser veto): medido en los sectores 69 y 107, cuesta unos 3 planetas rasantes por sector y frena de 4 a 9 binarias eclipsantes encontradas a la mitad de su período. Ambas decisiones están comentadas en `config/thresholds.yaml`, con nombres y números.

!!! example "Ejercicio 3. ¿Bastan tres ganancias?"
    Del run 2 al run 3, el recall subió de 117 a 120. Supón que 3 TOIs pasaron a ser recuperados y ninguno se perdió. (a) ¿Cuál es el $p$ de McNemar? (b) ¿Eso invalida el cambio?

    ??? success "Ver respuesta"
        (a) $g = 3$, $l = 0$. $P(X \ge 3)$ con $X \sim \text{Binomial}(3; 0{,}5)$ es $0{,}5^3 = 0{,}125$. $p = 2 \times 0{,}125 = 0{,}25$. Por sí solo, el resultado es compatible con el azar.

        (b) No lo invalida. La estadística dice que 3 ganancias no prueban nada **por sí mismas**. Pero cada ganancia tiene un mecanismo diagnosticado antes (por ejemplo, TOI 862.01 solo aparece con ventana de 0,5 d, por una variabilidad rápida medida) y ninguna pérdida. Hipótesis con mecanismo + ganancias en los objetos previstos + cero pérdidas es evidencia fuerte. Lo que sería preocupante: ganancias en objetos que la hipótesis no preveía, o cualquier pérdida sin explicación.

!!! example "Ejercicio 4. ¿Cuánto cuesta la grilla de inyección?"
    ¿Cuántas búsquedas exige la grilla completa de la sección 4 con 50 inyecciones por celda? El benchmark buscó en 185 objetivos en 1,3 minutos con 15 procesos. Estima el tiempo.

    ??? success "Ver respuesta"
        1. Celdas: $9 \times 8 \times 4 \times 4 = 1\,152$. Inyecciones: $1\,152 \times 50 = 57\,600$ búsquedas.
        2. Tiempo por objetivo (reloj, 15 procesos): $1{,}3 \times 60 / 185 \approx 0{,}42$ s.
        3. Total: $57\,600 \times 0{,}42 \approx 24\,000$ s, cerca de **6,7 horas** en la misma máquina.
        4. Viable en una noche. En la práctica, empieza con un rango de Tmag y una porción de la grilla para validar el código antes de gastar la noche.

## Práctica: cambia un límite y mide

Hazlo en una rama de git (`git switch -c experimento-<nombre>`), nunca directamente en la principal.

1. Elige **un** límite del vetting, por ejemplo `duration_ratio_max` (1,67) u `odd_even_fail_sigma` (3,0). Escribe la hipótesis y los criterios de éxito y de abandono.
2. Genera las listas: `uv run planethunter benchmark build 69` y `uv run planethunter benchmark build 69 --kind fp`.
3. Corre la búsqueda en los objetivos de las dos listas (`uv run planethunter search --sector 69 --tics <TICs separados por coma>`), después `crossmatch` y `vet` en el run. Guarda la tabla de validación: ese es el **antes**.
4. Cambia el límite. Corre `vet` de nuevo en el mismo run (los cambios de vetting no exigen una nueva búsqueda). Ese es el **después**.
5. Compara: tasa de aprobación de `KNOWN_PLANET` y `KNOWN_FP` con Wilson, lista de señales que cambiaron de veredicto.
6. Si cambias un parámetro de búsqueda (`window_length_days`, por ejemplo), corre `benchmark run 69 --skip-ingest` antes y después y compara el recall de forma pareada.
7. Escribe una página en `docs/benchmarks/` con hipótesis, tabla, cambios de estado y decisión. Aunque la decisión sea "abandoné". Un experimento negativo bien documentado evita que otra persona lo repita.

## Checklist de la lección

- [ ] Sé la diferencia entre recall, completitud y precisión.
- [ ] Sé explicar por qué la métrica principal es el recall en los 135 detectables, y no en los 220.
- [ ] Calculé a mano el intervalo de Wilson para 123/135 y para 53/53.
- [ ] Sé describir la grilla de injection-recovery y por qué la inyección se hace en el flujo bruto.
- [ ] Sé explicar el piso de ruido (5,2; 19; 98) y cómo lo usa el proyecto.
- [ ] Hice un cambio de límite en una rama, medí antes y después y escribí el informe.

## Para ir más allá

- Wilson (1927), *Journal of the American Statistical Association* 22, 209. El artículo original del intervalo; corto y legible.
- Brown, Cai & DasGupta (2001), *Statistical Science* 16, 101. Muestra, con gráficos, por qué falla el intervalo ingenuo y por qué Wilson es una buena elección.
- Christiansen et al. (2013), *The Astrophysical Journal Supplement Series* 207, 35. Inyección de tránsitos en los píxeles de Kepler para medir la recuperación del pipeline; el modelo de lo que el proyecto quiere hacer.
- Burke et al. (2015), *The Astrophysical Journal* 809, 8. Cómo entra la completitud medida en el cálculo de tasas de ocurrencia de planetas.
- Kreidberg (2015), *Publications of the Astronomical Society of the Pacific* 127, 1161. El `batman`, usado para generar los tránsitos sintéticos.
- McNemar (1947), *Psychometrika* 12, 153. La prueba para comparar dos proporciones medidas en los mismos objetos.
