# A4. Aprendizaje automático para la clasificación inicial

<p class="meta">Nivel avanzado · semanas 8–11 · cerca de 15 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Cómo Shallue & Vanderburg (2018) usaron una red neuronal para clasificar señales de Kepler, con las vistas global y local.
    - Qué agregó ExoMiner (Valizadegan et al. 2022) y cómo llegó a la validación de 301 planetas.
    - De dónde vienen las etiquetas de entrenamiento y por qué son imperfectas.
    - Qué es la fuga entre entrenamiento y prueba y por qué la división tiene que hacerse por estrella.
    - Qué es la calibración y por qué un score de 0,9 no siempre significa 90 %.
    - Por qué, en PlanetHunter, el ML solo reordena la cola y nunca veta, y cómo tus revisiones se convierten en etiquetas.

En la primera porción real del proyecto, con 2 164 estrellas del sector 69, el embudo produjo 648 señales `NEW`, 11 aprobadas en el vetting básico y 3 candidatos P2 después del vetting profundo. En un sector entero (cerca de 20 000 estrellas), y luego en imágenes completas (cientos de miles), la cola de revisión humana crece hasta volverse inmanejable. El aprendizaje automático (ML) entra aquí: **ordenar la cola** para que el tiempo humano vaya primero a lo que más vale.

## 1. La idea: enseñar con ejemplos

Un clasificador de ML aprende una función "datos de entrada → probabilidad de ser planeta" a partir de ejemplos etiquetados. En lugar de escribir reglas ("si impar/par > 3σ, reprueba"), le muestras miles de casos con la respuesta correcta y el algoritmo descubre los patrones. La ventaja: puede combinar señales débiles que ninguna regla aislada detectaría. El riesgo: aprende **cualquier** patrón que separe las etiquetas, incluso patrones que no tienen nada que ver con la física.

## 2. Shallue & Vanderburg (2018): vistas global y local

Shallue & Vanderburg (2018), *The Astronomical Journal* 155, 94, entrenaron una **red neuronal convolucional** (CNN, un tipo de red que aprende patrones locales en secuencias o imágenes) con señales de Kepler. Las etiquetas venían de clasificaciones humanas de TCEs de Kepler: planeta candidato, falso positivo astrofísico o no-tránsito.

La contribución más copiada del artículo es la **representación de la entrada**. En lugar de la curva de luz completa, la red recibe dos vistas de la curva plegada en el período:

| Vista | Qué muestra | Tamaño | Para qué sirve |
|---|---|---|---|
| **Global** | La órbita completa, de fase −0,5 a 0,5 | 2 001 bins | Ver el eclipse secundario, variaciones fuera del tránsito, la forma general |
| **Local** | Solo la vecindad del tránsito, pocas duraciones a cada lado | 201 bins | Ver detalles de la forma: fondo plano (U) o en V, ingreso y egreso |

Cada vista se normaliza (mediana en cero, profundidad en −1), lo que hace que la red compare **formas**, no profundidades absolutas. Las dos ramas convolucionales se unen en capas finales que producen un número entre 0 y 1.

El resultado se hizo conocido por un motivo concreto: aplicada a estrellas de Kepler con varios planetas ya conocidos, la red señaló señales débiles que, tras un análisis, llevaron a la validación de **Kepler-90 i** y **Kepler-80 g**. Fíjate en la secuencia: la red **sugirió**; la validación vino de un análisis posterior.

Yu et al. (2019), *AJ* 158, 25, adaptaron la misma arquitectura a TESS. La adaptación no fue trivial: TESS tiene menos tránsitos por señal, píxeles más grandes y otro conjunto de sistemáticos. Un modelo entrenado en Kepler no sirve directamente en TESS.

## 3. ExoMiner: darle a la red lo que mira el especialista

Valizadegan et al. (2022), *The Astrophysical Journal* 926, 120, presentaron **ExoMiner**. La idea: un especialista humano no decide solo por la forma del tránsito. Mira el centroide, el impar/par, el secundario, los parámetros de la estrella, los diagnósticos del Data Validation (lección A2). ExoMiner le da a la red **una rama para cada tipo de evidencia**:

- Vistas global y local del flujo (como en Shallue & Vanderburg).
- Vistas del **centroide** (movimiento durante el tránsito).
- Vistas de los tránsitos **impares y pares** por separado.
- Vista alrededor del **eclipse secundario**.
- **Parámetros estelares** y **estadísticas escalares** del DV.

Dos ventajas. Primero, mejor desempeño que los modelos solo con flujo, porque la red ve los diagnósticos que separan binarias de fondo y eclipses. Segundo, **explicabilidad**: se puede ver qué rama pesó en la decisión ("rechazado principalmente por el centroide"), lo que ayuda a un humano a confiar o desconfiar.

Con ExoMiner, los autores validaron **301 nuevos planetas** de Kepler. La validación exigió una probabilidad muy alta y verificaciones adicionales, en el mismo espíritu de la validación estadística de la lección A3. El ML entró como una forma de estimar la verosimilitud, no como sustituto del razonamiento.

## 4. Datos etiquetados: de dónde vienen y por qué son imperfectos

El plan del proyecto (agente `ml-engineer`) define las fuentes:

| Etiqueta | Fuente | Problema conocido |
|---|---|---|
| Positivo | TOIs con disposición CP/KP del TFOPWG | Pocos; tienden a ser profundos y en estrellas brillantes |
| Positivo sintético | Tránsitos inyectados con `batman` en curvas reales (lección A5) | Demasiado perfectos: sin sistemáticos correlacionados con el tránsito |
| Negativo | FP/FA del TFOPWG | Pocos y heterogéneos |
| Negativo | Catálogo de binarias de TESS | **Contiene hot Jupiters confirmados** (lección A2) |
| Negativo | Señales de ruido rechazadas por el propio vetting | Etiqueta dada por el propio sistema: el modelo aprende a imitar el vetting |

Tres lecciones:

1. **El ruido en las etiquetas es la regla.** El catálogo de binarias tiene planetas. "PC" no es planeta. Algunos FPs antiguos fueron revisados. Antes de entrenar, cruza las etiquetas con la misma prioridad del crossmatch: un planeta confirmado le gana al catálogo de binarias.
2. **Desbalance.** Hay muchos más negativos que positivos. La exactitud (accuracy) es una métrica inútil aquí: un modelo que dice "no es planeta" para todo acierta el 99 %. Usa el recall a precisión fija y el área bajo la curva precisión-recall (AUC-PR).
3. **Circularidad.** Si los negativos vienen del propio vetting, el modelo aprende a reproducir el vetting, incluidos sus errores. No va a encontrar lo que el vetting pierde.

## 5. Fuga entre entrenamiento y prueba

La **fuga** (leakage) ocurre cuando información del conjunto de prueba entra, de alguna manera, en el entrenamiento. El resultado es un desempeño medido excelente que se desploma en el uso real.

En exoplanetas, la forma más común es **la misma estrella en los dos conjuntos**:

- Una estrella observada en 10 sectores genera la misma señal 10 veces. Si la división es aleatoria **por señal**, 8 van al entrenamiento y 2 a la prueba. La red "reconoce" la estrella (el nivel de ruido, la variabilidad, la profundidad exacta) y acierta la prueba sin haber aprendido nada general.
- Una estrella con varios planetas: las señales comparten la misma curva de luz.
- Inyecciones en la misma curva en la que hay una señal real.

La regla del proyecto es explícita: **división por estrella, nunca por señal**. Todas las filas de un mismo TIC van al mismo conjunto. Para medir la generalización de verdad, conviene además separar por **región del cielo** o por **sector**, porque los sistemáticos del instrumento varían con la cámara y la época.

## 6. Calibración: ¿el score significa lo que dice?

Un clasificador devuelve un número entre 0 y 1. Eso **no** lo convierte en una probabilidad. Un modelo está **calibrado** cuando, entre todas las señales que reciben un score cercano a 0,9, cerca del 90 % son de verdad de la clase positiva.

Las redes neuronales modernas tienden a ser **demasiado confiadas** (Guo et al. 2017): dan scores cercanos a 0 o 1 con más frecuencia de la que deberían. Para verificarlo:

1. Separa un conjunto de validación (¡por estrella!).
2. Agrupa las señales por rango de score (0–0,1, 0,1–0,2, ...).
3. En cada rango, compara el score medio con la fracción real de positivos. El gráfico de esto es el **diagrama de confiabilidad**.

Para corregirlo, el plan usa **temperature scaling**: dividir la salida de la red (antes de la función que la transforma a un valor entre 0 y 1) entre una constante ajustada en el conjunto de validación. Es simple y no cambia el orden de las señales, solo los valores.

Por qué importa en el proyecto: el score del ML entra en el **novelty score**, que multiplica la confianza del vetting por la novedad en la literatura. Multiplicar probabilidades descalibradas produce números sin significado.

Una medida resumida es la **puntuación de Brier**: el promedio de $(p_i - y_i)^2$, donde $p_i$ es el score e $y_i$ la etiqueta (0 o 1). Cuanto menor, mejor. Penaliza tanto los errores de orden como los de calibración.

## 7. Por qué, en el proyecto, el ML solo reordena

La regla está en el agente `ml-engineer`: **el score del ML nunca veta por sí solo; solo reordena y baja la prioridad. El recall en TOIs conocidos no puede caer.** Cuatro razones:

1. **Los planetas nuevos están fuera de la distribución de entrenamiento.** Las etiquetas vienen de TOIs, que en general son profundos, en estrellas brillantes y de período corto. Los nichos del proyecto (estrellas débiles, períodos largos, enanas M) son justamente donde hay menos ejemplos. Un clasificador tiende a dar un score bajo a lo que nunca vio, y lo que nunca vio es lo que se busca.
2. **Error asimétrico.** Revisar un falso positivo cuesta unos minutos. Vetar un planeta real cuesta el planeta: nadie vuelve a mirarlo.
3. **El vetting determinista es auditable.** Cada veto tiene una prueba, un número y un límite comentado en `config/thresholds.yaml`, con benchmark antes y después. Un veto de una red neuronal es difícil de explicar y de corregir.
4. **El ML no ve lo que la búsqueda no detecta.** Actúa después de la búsqueda. Si el detrending se comió el tránsito, ningún clasificador lo recupera. Mejorar la búsqueda es trabajo del injection-recovery (lección A5), no del ML.

La meta del plan para la fase 5 es coherente con esto: el ML debe **reducir al menos 5 veces el número de candidatos que necesitas revisar primero**, manteniendo el recall. Los demás siguen en la cola, más abajo.

Cómo lo impone el código (`alerts/severity.py`). La probabilidad del modelo, `p_rank`, entra en la severidad solo a través de dos umbrales, ambos elegidos midiendo cuántos planetas conocidos conservan en la validación cruzada: el **umbral de P2** conserva el 90 % de ellos, y el **umbral de P1** es el más bajo que tiene como máximo un 1 % de falsos positivos y aun así conserva al menos el 70 % de los planetas. Una señal por debajo del umbral de P1 baja a P2, sea cual sea su score. Un `p_rank` alto nunca sube una señal: P1 sigue exigiendo un score determinista de al menos 0,8. El único "rescate" es limitado: una señal que falló el vetting determinista sin veto puede llegar a P2, nunca más. La auditoría del 2026-10-10 encontró que una versión anterior dejaba que el modelo reemplazara al score, y dos señales del sector 107 pasaron de P2 a P0 y a P1 solo por culpa del modelo.

**Dos probabilidades, dos usos.** Una probabilidad aprendida en un conjunto de entrenamiento en el que los planetas son comunes (los planetas conocidos son una parte grande de los ejemplos) es una probabilidad **bajo esa mezcla**. Entre las señales nuevas, los planetas son mucho más raros, así que la misma señal tiene una probabilidad real mucho menor de ser un planeta. Por eso el proyecto guarda dos números: `p_rank` (la salida calibrada del modelo, usada para ordenar y para los umbrales de arriba) y `p_abs`, el mismo valor corregido con la regla de Bayes para una fracción supuesta de planetas entre las señales nuevas (5 %, `severity.new_prior`):

$$
\text{logit}(p_\text{abs}) = \text{logit}(p_\text{rank}) + \text{logit}(0{,}05) - \text{logit}(\text{fracción de entrenamiento}) .
$$

El 5 % es una suposición, no una medida. Por eso `p_abs` se muestra, pero nunca se usa para decidir nada.

## 8. Tus revisiones se convierten en etiquetas

Cada vez que ejecutas

```bash
uv run planethunter review <signal_id> rejected --reason eb --note "secundario visible en fase 0.5"
```

la base de datos guarda `review_status` y `review_note` en la tabla `candidates`. Los estados posibles son `approved`, `rejected` y `follow_up`. Los rechazos exigen un motivo entre `eb`, `blend`, `systematic`, `noise`, `already_known` y `other`.

Estas decisiones son las **etiquetas más valiosas** del proyecto, porque vienen exactamente de la distribución que importa: señales que pasaron por todo el vetting y llegaron a la cola. Ningún catálogo público tiene este tipo de ejemplos. Esta es la base del **aprendizaje activo** (active learning) del plan: el modelo pide revisión humana de los casos en los que está más inseguro, y cada revisión mejora el siguiente entrenamiento.

Para que tus revisiones sirvan como etiquetas:

- **Sé consistente** con el motivo. "eb" y "blend" le enseñan cosas distintas al modelo.
- **Escribe la nota con la evidencia**, no con la conclusión: "profundidad impar 4 100 ppm, par 2 300 ppm" vale más que "parece EB".
- **Entiende lo que significa la etiqueta.** "approved" quiere decir "sobrevivió a la mirada humana y merece seguimiento", no "es un planeta". Un modelo entrenado con esto aprende a predecir tu decisión, con tus sesgos.
- **Usa `follow_up` cuando no sepas.** Una etiqueta equivocada con convicción es peor que una etiqueta honesta de incertidumbre.

!!! tip "En la herramienta"
    - `uv run planethunter candidates` lista la cola; `uv run planethunter dossier <signal_id>` genera el dossier; `uv run planethunter review ...` guarda la decisión.
    - Las columnas `review_status`, `review_note` y `reviewed_at` están en la tabla `candidates` de `data/planethunter.duckdb`.
    - Ya existe un primer paso simple: `uv run planethunter calibrate` entrena una regresión logística con los resultados del vetting básico de señales conocidas. Positivos: planetas confirmados. Negativos: falsos positivos catalogados y, cuando las hay, todas las señales de las corridas nulas invertidas y barajadas (lección A1), que son falsas alarmas por construcción. La regularización se elige por validación cruzada agrupada por estrella, las probabilidades se calibran con Platt scaling sobre las predicciones fuera de pliegue, y el modelo se guarda en `data/models/vetting_lr.json` con un `model_version` y las corridas de las que vino. La cola muestra entonces `p_rank` y `p_abs`, y la severidad usa `p_rank` solo para bajar la prioridad.
    - El clasificador de red neuronal descrito en esta lección todavía **no está implementado**. Es la fase 5 del plan. Lo que revisas hoy es el conjunto de entrenamiento de mañana.

!!! example "Ejercicio 1. Encuentra la fuga"
    Una persona arma un conjunto con 3 000 señales de 1 200 estrellas, mezcla las señales y separa el 80 % para entrenamiento y el 20 % para prueba. El modelo alcanza una AUC-PR de 0,97 en la prueba. Aplicado a un sector nuevo, la cola ordenada por el modelo parece casi aleatoria. ¿Qué pasó y cómo corregirlo?

    ??? success "Ver respuesta"
        1. Con 3 000 señales de 1 200 estrellas, muchas estrellas tienen varias señales (varios sectores, varios planetas, iteraciones de la búsqueda). La mezcla por señal puso la misma estrella en el entrenamiento y en la prueba.
        2. El modelo aprendió a reconocer estrellas (nivel de ruido, variabilidad, profundidad), no patrones de planeta frente a binaria. La prueba midió memoria.
        3. Corrección: agrupar por TIC y sortear **estrellas** para entrenamiento y prueba. Mejor aún: reservar sectores enteros para la prueba, para medir también el cambio de sistemáticos.
        4. Lo esperado: la AUC-PR en la prueba corregida baja y pasa a reflejar el desempeño real.

!!! example "Ejercicio 2. ¿El modelo está calibrado?"
    (a) En un conjunto de validación, 200 señales recibieron un score entre 0,85 y 0,95. De ellas, 120 son planetas. ¿Está calibrado el modelo en ese rango? (b) Calcula la puntuación de Brier para cuatro señales con scores 0,9; 0,9; 0,2; 0,6 y etiquetas 1; 0; 0; 1.

    ??? success "Ver respuesta"
        (a) Score medio ≈ 0,9; fracción real $120/200 = 0{,}6$. El modelo es **demasiado confiado** en ese rango: promete 90 % y entrega 60 %. El temperature scaling debería acercar esos scores a 0,6.

        (b) Errores al cuadrado: $(0{,}9-1)^2 = 0{,}01$; $(0{,}9-0)^2 = 0{,}81$; $(0{,}2-0)^2 = 0{,}04$; $(0{,}6-1)^2 = 0{,}16$. Suma $1{,}02$. Brier $= 1{,}02/4 = 0{,}255$. La segunda señal, un negativo con score 0,9, explica casi todo el error.

!!! example "Ejercicio 3. ¿Reordenar o vetar?"
    La cola tiene 200 candidatos, de los cuales 4 merecen seguimiento (solo lo sabrás después). Tienes tiempo para revisar 40 por mes. El modelo coloca 3 de los 4 entre los 40 primeros y el cuarto en la posición 150. Compara dos políticas: (A) vetar todo lo que esté por debajo de la posición 40; (B) reordenar la cola y seguir revisando en los meses siguientes.

    ??? success "Ver respuesta"
        - Política A: revisión 5 veces menor (40 de 200), pero el cuarto candidato se **pierde para siempre**. Recall 3/4 = 75 %. Viola la regla "el recall no puede caer".
        - Política B: en el primer mes encuentras 3 de los 4, la misma ganancia de tiempo que con la política A. El cuarto aparece en el cuarto mes. Recall final 100 %.
        - El ML entrega el beneficio principal (encontrar lo mejor primero) sin el costo irreversible. Ese es el motivo de la regla del proyecto. Y el cuarto candidato, con score bajo y decisión humana positiva, es justamente el ejemplo que más le enseña al siguiente entrenamiento.

## Checklist de la lección

- [ ] Leí Shallue & Vanderburg (2018) y sé explicar las vistas global y local.
- [ ] Leí Valizadegan et al. (2022) y sé enumerar las ramas de ExoMiner.
- [ ] Sé señalar tres problemas en las etiquetas disponibles para el proyecto.
- [ ] Sé explicar la fuga y por qué la división es por estrella.
- [ ] Sé leer un diagrama de confiabilidad y calcular la puntuación de Brier.
- [ ] Sé dar cuatro razones por las cuales el ML solo reordena.
- [ ] Revisé al menos 10 candidatos con motivo y una nota basada en evidencia.

## Para ir más allá

- Shallue & Vanderburg (2018), *The Astronomical Journal* 155, 94. El artículo que popularizó las vistas global y local; lee la sección de representación de los datos y la de resultados.
- Valizadegan et al. (2022), *The Astrophysical Journal* 926, 120. ExoMiner; lee la arquitectura y la discusión sobre explicabilidad.
- Yu et al. (2019), *The Astronomical Journal* 158, 25. La adaptación a TESS; muestra qué cambia cuando cambia el instrumento.
- Armstrong et al. (2021), *Monthly Notices of the RAS* 504, 5327. Validación de planetas de Kepler con varios algoritmos de ML combinados con probabilidades calibradas; excelente contrapunto a ExoMiner.
- Guo et al. (2017), "On Calibration of Modern Neural Networks", *Proceedings of ICML*. Muestra que las redes profundas son demasiado confiadas e introduce el temperature scaling.
- Ivezić, Connolly, VanderPlas & Gray, *Statistics, Data Mining, and Machine Learning in Astronomy* (Princeton University Press). Libro de referencia que conecta la estadística y el ML con problemas astronómicos reales.
