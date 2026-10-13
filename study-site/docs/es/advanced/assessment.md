# Autoevaluación del nivel avanzado

<p class="meta">Nivel avanzado · semana 16 · unas 6 horas</p>

!!! abstract "Cómo usar esta página"
    - Las cuatro primeras preguntas son las del plan de estudios. Las otras seis cubren puntos de cada lección.
    - Escribe tu respuesta **antes** de abrir el modelo. Usa el cuaderno de lectura y el de revisiones, pero no esta página.
    - Las preguntas son abiertas. Los modelos de respuesta muestran los elementos que una buena respuesta necesita tener, no la única respuesta correcta.

## Preguntas del plan

!!! question "Pregunta 1. Propón un cambio en el vetting"
    Propón un cambio en el vetting de PlanetHunter. Explica la hipótesis, cómo medirías el efecto y qué resultado te haría abandonarla.

    ??? success "Ver respuesta"
        Una buena respuesta tiene cuatro partes. Ejemplo de modelo:

        **Cambio.** Nueva prueba de **profundidad por apertura**: medir la profundidad del tránsito con la apertura del pipeline, con una apertura menor (solo los píxeles más brillantes del objetivo) y con una mayor. Falla leve si la profundidad crece con la apertura de forma significativa.

        **Hipótesis con mecanismo.** Si el tránsito está en el objetivo, la profundidad fraccionaria es aproximadamente la misma en cualquier apertura centrada en él. Si viene de una vecina en el borde de la apertura, la apertura mayor incluye más luz de la vecina y la profundidad cambia. De los 8 FPs del TFOPWG que todavía pasan en el sector 69, algunos son binarias de fondo; la hipótesis es que la prueba atrape parte de ellas.

        **Medición.** Correr la prueba en los 54 `KNOWN_PLANET` y 18 `KNOWN_FP` del benchmark de vetting del sector 69. Métricas: cuántos de los 8 FPs restantes pasan a fallar; cuántos planetas pasan a fallar; intervalos de Wilson. Comparación pareada: lista de señales que cambiaron de veredicto. Informe en `docs/benchmarks/`.

        **Criterio de abandono, escrito antes.** Abandono si atrapa 0 de los 8 FPs restantes, o si marca más de 2 de los 54 planetas, o si el efecto depende de un único objeto. También abandono si, al mirar caso por caso, los FPs atrapados ya eran reprobados por otra prueba en el vetting profundo (ganancia redundante).

        Puntos que la respuesta necesita tener: un mecanismo físico, conjuntos de prueba con respuesta conocida, métrica de los dos lados (planetas y FPs), incertidumbre con muestra pequeña y un criterio de parada definido antes de ver el resultado.

!!! question "Pregunta 2. La zona de visión continua"
    Explica por qué una señal nueva y profunda, en una estrella de la zona de visión continua de TESS, es casi siempre sistemática.

    ??? success "Ver respuesta"
        1. Las estrellas cerca de los polos de la eclíptica (zona de visión continua) se observan en muchos sectores. En el sector 69, las estrellas anfitrionas de esa región tenían **10 a 22 sectores** de datos.
        2. Una señal profunda tiene SNR alto. Si fuera real y periódica, habría aparecido en muchos de esos sectores, con un SNR enorme sumándolos todos. El SPOC, el QLP y la comunidad ya habrían producido un TOI o CTOI. Si no está en ningún catálogo, la explicación más simple es que **no existe** en los otros sectores.
        3. Una señal que aparece en un solo sector es la firma de un sistemático de ese sector: luz dispersa, ajuste de apuntado, problema de detrending en un borde.
        4. Evidencia del proyecto: HD 271883, señal limpia de 6,61 d y 4 900 ppm, pasó todas las pruebas básicas. En los sectores 67, 68 y 97, el SNR esperado era de 45 a 64. No apareció. La prueba `other_sectors` la vetó.
        5. Excepciones a considerar: un monotránsito de período muy largo (raro, porque la cobertura continua abarca casi un año) o un evento que cayó en un hueco de los otros sectores. Por eso la prueba exige ausencia **decisiva** (SNR esperado ≥ 10 y ≥ 1,5 veces el piso de ruido) en al menos dos sectores, y también hace la búsqueda a ciegas.

!!! question "Pregunta 3. Disecciona un artículo"
    Lee un artículo reciente de validación o confirmación de un planeta de TESS. Identifica cada prueba de vetting que usó y cuál no tiene PlanetHunter.

    ??? success "Ver respuesta"
        La respuesta depende del artículo elegido. Arma una tabla con tres columnas: prueba, evidencia en el artículo (figura o tabla), equivalente en PlanetHunter. Pruebas que suelen aparecer:

        | Prueba en el artículo | En PlanetHunter |
        |---|---|
        | Informe DV del SPOC: impar/par, secundario, centroide de la imagen diferencia | `odd_even`, `secondary`, `tpf_difference_image` |
        | Diagnóstico de fantasma óptico del DV | No tiene |
        | Fotometría en tierra (SG1): tránsito en el objetivo, vecinas excluidas, profundidad en varios colores | No tiene (fuera del alcance; viene del seguimiento) |
        | Espectroscopía de reconocimiento (SG2): sin binaria espectroscópica, parámetros estelares | No tiene; usa el TIC |
        | Imagen de alta resolución (SG3) con curva de contraste | No tiene; triceratops corre sin curva de contraste |
        | Indicador de binariedad de la astrometría de Gaia (por ejemplo, el RUWE) | No tiene |
        | FPP con vespa o triceratops | `fpp_triceratops` |
        | Velocidad radial (SG4) | No tiene |
        | Consistencia entre sectores | `other_sectors` |

        La conclusión esperada: PlanetHunter cubre bien la parte automática hecha solo con datos de TESS y de Gaia; le falta todo lo que exige otro telescopio, más algunos diagnósticos del DV (fantasma óptico) y de la astrometría. La respuesta es buena si indica, para cada laguna, si es implementable en el proyecto o si solo se resuelve con seguimiento.

!!! question "Pregunta 4. Escribe un envío"
    Escribe el texto de un envío de CTOI para un candidato hipotético, con los números del dossier.

    ??? success "Ver respuesta"
        Modelo, con números **hipotéticos** de un dossier:

        - **TIC**: XXXXXXXXX
        - **Período**: 9,8714 ± 0,0009 d
        - **Época**: 2 460 156,3381 ± 0,0016 BJD (TDB), en medio de los datos
        - **Profundidad**: 1 240 ± 110 ppm
        - **Duración**: 3,4 ± 0,2 h
        - **Radio estimado**: 3,1 R⊕ para R* = 0,81 R☉ (TIC)
        - **Disposición del usuario**: PC

        **Notas**: "Señal encontrada con TLS en la curva SPOC de 2 min de los sectores 68–69 (PlanetHunter versión X, run Y), 3 tránsitos, SDE 14,2, SNR 11,8. Impar/par: diferencia de 0,6σ. Sin secundario en fase 0,5 (límite 3σ: 180 ppm) ni en otras fases. Forma de U (τ/T14 = 0,18). Duración compatible con la densidad estelar del TIC (razón 0,92). Imagen diferencia: centroide a 0,15 ± 0,21 px del objetivo. Vecinos Gaia: ninguno capaz de producir la caída fuera del radio de exclusión de 6″. No aparece en catálogos de planetas, TOIs, CTOIs ni binarias (espejos con 6 h); búsqueda en ADS y arXiv el 2026-10-09 sin resultados. Triceratops: FPP 0,08, NFPP 0,0004, escenario competidor principal PEB. Limitaciones: sin otros sectores con datos; sin imagen de alta resolución. Sugerencia: SG1 en el próximo tránsito previsto (2 460 412,995 ± 0,023 BJD, 26 órbitas después de la época) y SG3."

        Criterios: época en BJD completo; incertidumbres en todos los números; pruebas con valores, no adjetivos; limitaciones explícitas; vocabulario correcto; procedencia; sugerencia de seguimiento con predicción de tránsito.

## Preguntas extra

!!! question "Pregunta 5. El BLS es una SNR"
    Muestra, con el modelo de caja y errores iguales, por qué maximizar $s^2/[r(1-r)]$ equivale a maximizar la SNR del tránsito.

    ??? success "Ver respuesta"
        Con datos centrados en cero, profundidad $\delta$ y fracción en tránsito $r$: nivel dentro $L = -\delta(1-r)$, fuera $H = \delta r$. Entonces $s = rL = -\delta\, r(1-r)$ y $s^2/[r(1-r)] = \delta^2 r(1-r)$. Volviendo de los pesos normalizados al chi cuadrado con error $\sigma$: $\Delta\chi^2 = N\delta^2 r(1-r)/\sigma^2$. La raíz es $(\delta/\sigma)\sqrt{N r(1-r)} \approx (\delta/\sigma)\sqrt{N_\text{en tránsito}}$, la SNR. Punto extra: recordar que, con ruido rojo, la $\sigma$ por punto subestima el error de los promedios, y la SNR del BLS queda optimista.

!!! question "Pregunta 6. El catálogo que tenía planetas"
    Cuenta el problema de los jupíteres calientes en el catálogo de binarias de TESS y explica la regla que lo resolvió.

    ??? success "Ver respuesta"
        En la calibración del sector 69, las 9 señales que coincidieron con el catálogo de binarias de Prša et al. (2022) eran planetas confirmados, como WASP-18 b, WASP-100 b y HATS-16 b. Tránsitos profundos de gigantes calientes, a veces con ocultación visible, fueron incluidos en el catálogo por criterios automáticos. La corrección define un orden de evidencia en el crossmatch: planeta confirmado > FP/FA del TFOPWG > TOI > CTOI > catálogo de binarias. La lección general: cada catálogo tiene un objetivo y una tasa de error; la prioridad debe seguir la fuerza de la evidencia (una medida de masa le gana a una clasificación por forma).

!!! question "Pregunta 7. Un planeta con FPP 0,35"
    El planeta confirmado WASP-100 b dio FPP 0,35 en triceratops (TP 0,54, PEB 0,35, PTP 0,11, NFPP ≈ 0). ¿Eso indica un defecto en triceratops?

    ??? success "Ver respuesta"
        No. El FPP mide lo que los datos **proporcionados** permiten excluir. Solo con fotometría de TESS, sin curva de contraste, el escenario PEB (objetivo con una compañera ligada no resuelta, eclipsada por una estrella) reproduce razonablemente un tránsito profundo. La velocidad radial que confirmó el planeta no entró en el cálculo. Una curva de contraste de imagen de alta resolución recortaría la prior de compañeras y derribaría el PEB. Un NFPP despreciable muestra que ninguna vecina conocida es sospechosa. Conclusión: el resultado es coherente e ilustra por qué el FPP es una prueba entre otras, y por qué la validación exige imagen de alta resolución.

!!! question "Pregunta 8. El ML que se filtró"
    ¿Por qué el conjunto de entrenamiento y el de prueba de un clasificador de señales deben separarse por estrella, y por qué, en el proyecto, el ML no puede vetar?

    ??? success "Ver respuesta"
        Separación por estrella: la misma estrella genera varias señales (varios sectores, varios planetas, iteraciones). Si separas por señal, la red reconoce la estrella en la prueba (ruido, variabilidad, profundidad) y el desempeño medido es memoria, no generalización.

        Sin veto: (1) los planetas que el proyecto busca están en los nichos con menos ejemplos de entrenamiento; (2) vetar un planeta real es irreversible, revisar uno falso cuesta minutos; (3) el vetting determinista es auditable y se mide con benchmark; (4) el ML no recupera lo que la búsqueda no detecta. El ML reordena la cola, manteniendo el recall.

!!! question "Pregunta 9. ¿Cuánto vale 81 %?"
    En el benchmark de vetting, 44 de 54 planetas confirmados fueron aprobados (81 %). Calcula el intervalo de Wilson del 95 % y di qué implica para comparar dos versiones del vetting.

    ??? success "Ver respuesta"
        $p = 0{,}8148$; $z^2/n = 3{,}8416/54 = 0{,}0711$; denominador $1{,}0711$. Centro $= (0{,}8148 + 3{,}8416/108)/1{,}0711 = (0{,}8148 + 0{,}0356)/1{,}0711 = 0{,}794$. $p(1-p)/n = 0{,}00279$; $z^2/(4n^2) = 0{,}00033$; suma $0{,}00312$; raíz $0{,}0559$; $h = 1{,}96 \times 0{,}0559/1{,}0711 = 0{,}102$. IC ≈ **69 % a 90 %**.

        Implicación: dos versiones con 81 % y 85 % tienen intervalos casi iguales. Comparar intervalos no decide. Como los objetos son los mismos, compara de forma pareada: lista los planetas que cambiaron de veredicto y usa la prueba de McNemar, junto con el mecanismo de cada cambio.

!!! question "Pregunta 10. Una ausencia que no prueba nada"
    Un candidato no aparece en el sector 95, donde el SNR esperado era 12. El piso de ruido medido en la propia estrella en ese sector es 13,5. ¿Se debe vetar el candidato?

    ??? success "Ver respuesta"
        No con base en ese sector. El piso de 13,5 significa que la búsqueda en banda estrecha, en esa estrella, encuentra picos de SNR 13,5 en el 10 % de los intentos en períodos aleatorios. Una señal real con SNR esperado 12 puede simplemente no destacarse. El proyecto solo cuenta la ausencia como decisiva si el SNR esperado es ≥ 10 **y** ≥ 1,5 veces el piso (aquí, exigiría 20), y solo veta con ausencia decisiva en al menos dos sectores. Es el caso real de la señal 1634: la decisión vino de la búsqueda a ciegas en los sectores 95 a 97, que no recuperó ni el período ni el doble. La idea general: un límite fijo de SNR no sirve, porque el ruido de búsqueda (mediana 5,2, p90 19, p99 98 en el sector 69) varía mucho de una estrella a otra.

## Criterio de aprobación

- **Concluido con holgura**: respuestas completas en al menos 8 de las 10 preguntas, **incluyendo** las preguntas 1 y 4. Esas dos son de producción: lo que importa es la estructura (hipótesis, medición, criterio de parada; efeméride, incertidumbres, pruebas, limitaciones).
- **Casi listo**: 6 o 7 preguntas completas. Vuelve a las lecciones de las preguntas que fallaste y rehaz los ejercicios resueltos sin mirar la respuesta.
- **Todavía no**: menos de 6. Relee las lecciones A3 y A5, que concentran los conceptos más evaluados, y rehaz la autoevaluación en dos semanas.

Para cada pregunta equivocada, anota en el cuaderno qué lección la responde y qué faltó. Ese registro vale más que la nota.

Cuando apruebes, el siguiente paso es práctico: revisar la cola de candidatos de un sector nuevo con criterio, documentar las revisiones y, si un candidato sobrevive a todo, preparar el paquete de envío de la lección A6.
