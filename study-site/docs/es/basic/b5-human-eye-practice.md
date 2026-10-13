# B5. Práctica con ojos humanos

<p class="meta">Nivel básico · semanas 5–6 · unas 6 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Cómo participar en Planet Hunters TESS en Zooniverse y qué observar en cada curva de luz.
    - Cómo correr PlanetHunter en un planeta conocido, Pi Men c, y encontrar su señal.
    - Cómo leer un dossier de PlanetHunter sección por sección.
    - Cómo repasar las tres historias reales del sector 69 identificando la prueba que resolvió cada una.

## Por qué entrenar el ojo

Las lecciones anteriores te dieron las ideas. Esta es de práctica. Los algoritmos son rápidos e incansables, pero el ojo humano entrenado sigue siendo muy bueno para notar cuando algo "no tiene cara" de tránsito: un escalón raro, una caída pegada a un hueco en los datos, eclipses alternados. Toda decisión final sobre un candidato de PlanetHunter pasa por una persona que mira el dossier. Esa persona vas a ser tú.

## Parte 1. Planet Hunters TESS

**Planet Hunters TESS** es un proyecto de ciencia ciudadana en la plataforma **Zooniverse**, creado en 2018 por investigadores de la Universidad de Oxford. Los voluntarios miran curvas de luz reales del TESS y marcan los tránsitos que ven. Cada curva la ven varias personas, y las marcas combinadas señalan las señales que merecen la atención de los científicos.

No es un juego: voluntarios de este proyecto ya tuvieron candidatos que se convirtieron en planetas. El primero fue TOI-813 b, un planeta del tamaño de Saturno con un período de unos 84 días, publicado por Eisner y colaboradores en 2020. Los períodos largos como ese, con pocos tránsitos, son justamente los que a los algoritmos más les cuesta encontrar.

### Cómo participar

1. Entra al proyecto: [Planet Hunters TESS en Zooniverse](https://www.zooniverse.org/projects/nora-dot-eisner/planet-hunters-tess). Crear una cuenta es opcional, pero con cuenta tus clasificaciones quedan registradas y puedes comentar.
2. Haz el **tutorial** que aparece la primera vez. Te muestra la interfaz y ejemplos.
3. Abre la **guía de campo** (*Field Guide*), en el costado. Tiene ejemplos de tránsitos, binarias, variabilidad y defectos, con las mismas categorías de la lección B4.
4. En cada curva, marca las caídas que parecen tránsitos y confirma. Si no hay nada, confirma sin marcar: "aquí no hay nada" también es una respuesta útil.
5. Usa el foro **Talk** para preguntar sobre curvas raras. Ahí conversan voluntarios con experiencia y científicos.

!!! note "Si la interfaz cambia"
    Los proyectos de Zooniverse evolucionan y, a veces, entran en pausa entre lotes de datos. Si Planet Hunters TESS está en pausa cuando llegues, explora la guía de campo y los foros Talk, que siguen abiertos, y vuelve cuando haya datos nuevos.

### Qué observar en cada curva

| Ves | Probablemente es | Recuerda la prueba |
|---|---|---|
| Caídas iguales, con fondo plano, repetidas a intervalos regulares | tránsito de planeta | — |
| Caídas profundas y puntiagudas (V) | binaria eclipsante | `shape` |
| Caídas que se alternan: una profunda, una poco profunda | binaria eclipsante | `odd_even` |
| Una caída menor exactamente entre dos mayores | eclipse secundario de binaria | `secondary` |
| Ondas suaves de varios días | manchas y rotación de la estrella | detrending |
| Picos rápidos hacia **arriba** | fulguraciones (flares) | recorte de picos |
| Caída o rampa pegada a un hueco en los datos | borde de órbita (defecto) | `edges_dumps` |
| Una única caída, sin repetición | monotránsito, o defecto | `n_transits` |

**Meta del plan:** clasifica al menos **200 curvas**. Parece mucho, pero cada una lleva menos de un minuto cuando le agarras la mano. Para la centésima, vas a notar que el ojo ya separa tránsito, binaria y defecto sin pensar.

!!! tip "Consejo de estudio"
    Lleva un cuaderno. Anota el número de las curvas que te dejaron con dudas y lo que decidiste. Después, compáralo con las discusiones en Talk. Ese cuaderno es el comienzo del "cuaderno de revisiones" que el plan recomienda para el resto del curso.

## Parte 2. Pi Men c en PlanetHunter

Ahora vas a correr la herramienta en un planeta que ya sabemos que existe. Esto tiene un objetivo: aprender a leer la salida cuando la respuesta es conocida, antes de mirar señales desconocidas.

**Pi Mensae** (TIC 261136679) es una estrella brillante, parecida al Sol, en el cielo del hemisferio sur. Tiene dos planetas conocidos:

- **Pi Men b**: un gigante con una órbita de varios años, detectado por velocidad radial en 2001. No transita.
- **Pi Men c**: una supertierra de unos 2 R⊕, con un período de **6,27 días** y una profundidad de **unas 300 ppm**. Fue el **primer** planeta en tránsito anunciado a partir de los datos del TESS, en 2018, y es el TOI-144.01.

La estrella está cerca del polo sur de la eclíptica, así que fue observada en muchos sectores.

### Paso a paso

Antes de empezar, instala el proyecto (una sola vez) y actualiza los espejos de los catálogos. Sin espejos actualizados, el sistema no puede decir si una señal es conocida.

```bash
uv sync
uv run planethunter mirrors sync
uv run planethunter mirrors status
```

El `mirrors status` muestra la antigüedad de cada catálogo y su límite. Cada uno tiene que estar dentro de su propio límite (48 horas para los TOIs, los CTOIs y el archivo de la NASA; más para los catálogos que cambian despacio) y todas las líneas tienen que decir `ok`.

**1. Corre el análisis de punta a punta para Pi Mensae.**

```bash
uv run planethunter run-target 261136679
```

Este comando hace todo para una sola estrella: descarga las curvas de luz de MAST, las limpia, busca señales juntando todos los sectores, las compara con los catálogos, corre el vetting básico y genera un dossier para cada señal fuerte. La primera vez, la descarga tarda algunos minutos. Para algo más rápido, limítalo a un sector con `--sectors 1`.

Al final, imprime una línea `run_id=...`, una tabla con una fila por señal (de la más fuerte a la más débil) y la ruta de cada dossier. Las columnas:

| Columna | Qué es | Qué esperar para Pi Men c |
|---|---|---|
| `signal_id` | número de la señal en la base de datos | un número entero |
| `period_days` | período en días | cerca de 6,27 |
| `t0_btjd` | instante de un tránsito, en BTJD | un número con decimales |
| `depth_ppm` | profundidad | cerca de 300 |
| `duration_hours` | duración | algunas horas |
| `sde`, `snr` | fuerza de la señal | por encima de 9 y de 7,1 |
| `n_transits` | tránsitos con datos | varios (muchos sectores) |
| `match_class` | resultado del crossmatch | `KNOWN_PLANET` |
| `matched_name` | con quién coincidió | el nombre de Pi Men c |
| `verdict`, `score` | resultado del vetting básico | `PASS_BASIC`, score cerca de 1 |

Si aparece `` WARNING: mirrors missing or stale; run `planethunter mirrors sync`. `` (los espejos faltan o están desactualizados), vuelve a correr `mirrors sync`. Si aparecen otras señales débiles, es normal: después de encontrar y borrar la señal más fuerte, la búsqueda vuelve a buscar y a veces encuentra ruido.

**2. Abre el dossier.** Las últimas líneas dicen algo como:

```text
dossier for signal 1234: data/dossiers/tic261136679_sig1234.html
```

Abre en el navegador el archivo de la señal de ~6,27 días. Si quieres generarlo de nuevo más adelante, usa `uv run planethunter dossier <signal_id>`.

### Leyendo el dossier de Pi Men c, sección por sección

Recorre el dossier de arriba abajo. El dossier está en inglés; aquí tienes el título de cada sección tal como aparece y su explicación. Para cada sección, la primera frase dice qué muestra; la segunda, qué buscar.

1. **Encabezado y etiquetas.** El dossier se genera en inglés. Las etiquetas muestran la severidad (`severity`), la clase del crossmatch (`crossmatch`), el veredicto del vetting con el score (`vetting ... score`) y el "host conocido" (`known host`). Para Pi Men c: crossmatch `KNOWN_PLANET` y `known host: yes` (la estrella tiene planetas catalogados). La severidad aparece como "—", porque las señales conocidas no se convierten en candidatos ni en alertas. El título dice "Signal TIC ..." (señal): la palabra "Candidate" (candidato) solo aparece para señales nuevas que pasaron el vetting.
2. **Parameters (parámetros).** Tabla con Tmag, temperatura (`Teff (K)`), radio (`R* (R☉)`) y masa (`M* (M☉)`) de la estrella, sectores (`Sectors`), período (`Period (d)`), profundidad ajustada (`Fitted depth (ppm)`), duración (`T14 (h)`), radio del planeta (`Rp (R⊕)`), `SDE / SNR` y número de tránsitos (`Transits with data`). **Comprueba:** el período cerca de 6,27 días, la profundidad cerca de 300 ppm y Rp cerca de 2 R⊕. Usa la regla de la lección B2: $R_p \approx R_\star\sqrt{\delta}$ con el R* de la tabla. ¿Coincide? Fíjate también en el Tmag: Pi Mensae es muy brillante (Tmag alrededor de 5), lo que explica por qué un tránsito tan poco profundo es detectable.
3. **Light curve (curva de luz).** Todo el brillo a lo largo del tiempo, ya limpio. Las líneas **rojas** marcan los tránsitos; las líneas **azules punteadas**, los momentum dumps. **Busca:** los tránsitos en rojo repartidos por los sectores, sin coincidir sistemáticamente con las líneas azules ni con los bordes de los huecos. Con 300 ppm, probablemente **no** vas a ver cada tránsito individual a simple vista, y está bien.
4. **Folded transit (tránsito plegado).** Todos los tránsitos superpuestos, alineados según el período. Los puntos grises son mediciones individuales; los puntos negros son promedios; la curva roja es el modelo ajustado. **Busca:** una "U" clara en los puntos negros, con la curva roja pasando por ellos. Aquí es donde aparece el tránsito invisible en la curva completa: sumar muchos tránsitos reduce el ruido (lección B2).
5. **Odd, even and secondary (impar, par y secundario).** Tres paneles: tránsitos impares, pares y la fase 0,5. **Busca:** los dos primeros con la misma profundidad y el tercero plano. Es lo que hace un planeta.
6. **Depth per transit (profundidad por tránsito).** Un punto por tránsito, con el promedio como línea discontinua. **Busca:** puntos repartidos alrededor de la línea, sin uno mucho más profundo que los demás. En una señal poco profunda como esta, la dispersión entre los puntos es grande: es el ruido de cada tránsito aislado.
7. **TPF difference image (imagen de diferencia).** Esta sección solo aparece cuando se corrió el vetting profundo, y este solo se corre para candidatos nuevos. Para Pi Men c **no** aparece. En un candidato, la `x` roja (donde desapareció la luz) debe caer dentro del círculo naranja (la posición de la estrella en el catálogo).
8. **Vetting (tabla de vetting).** Una prueba por fila, con valor, límite, resultado y nota (columnas `test`, `value`, `threshold`, `result`, `note`). **Busca:** cuáles pasaron y, si alguna falló, lee la nota. Las pruebas del vetting profundo pueden aparecer como `pending` (pendiente).
9. **Crossmatch.** Clase, número de objetos conocidos en la estrella y vecinos, con quién coincidió la señal, y la antigüedad de cada catálogo en el momento de la comparación. **Busca:** la coincidencia con Pi Men c y todos los catálogos dentro de su límite de antigüedad (48 horas para los TOIs, los CTOIs y el archivo de la NASA).
10. **Next action (próxima acción).** Para Pi Men c: "None: known signal or failed vetting." (ninguna: señal conocida o reprobada en el vetting). Para un candidato nuevo aprobado, aquí aparece la sugerencia de vetting profundo y de envío como CTOI.

Al pie, la sección **Provenance** (procedencia) registra el `run_id`, la versión del pipeline y la ventana de detrending usada en cada sector. Es lo que permite reproducir el análisis después.

!!! tip "En la herramienta"
    La guía de uso completa, con más comandos, está en el [manual práctico de PlanetHunter](../lab/using-planethunter.md). Los dossiers quedan en `data/dossiers/`. Hay dossiers de otras señales del sector 69 en esa carpeta; después de leer el de Pi Men c, abre dos o tres de ellos y compáralos.

!!! example "Ejercicio 1"
    Después de correr Pi Men c, responde con los números de **tu** dossier:

    a) ¿Qué período y qué profundidad se encontraron? ¿Qué tan cerca están de 6,27 días y 300 ppm?

    b) Usa el R* del dossier y la profundidad para calcular Rp. ¿El resultado coincide con el Rp que muestra el dossier?

    c) ¿Cuántos tránsitos con datos contó el sistema? ¿Por qué ese número es mucho mayor que los 4 tránsitos de un solo sector?

    ??? success "Ver respuesta"
        a) El período debe salir muy cerca de 6,27 días (la diferencia suele estar en el tercer o cuarto decimal) y la profundidad en el orden de algunos cientos de ppm, cerca de 300. Las diferencias de decenas de ppm son normales: la profundidad depende del modelo ajustado y de la limpieza de los datos.

        b) Con R* alrededor de 1,1 R☉ y una profundidad de 300 ppm: $\sqrt{0{,}0003} \times 1{,}1 \times 109 \approx 2{,}1$ R⊕. El dossier calcula exactamente así ($R_p = R_\star\sqrt{\delta} \times 109{,}076$), así que debe coincidir, con diferencias solo de redondeo.

        c) El `run-target` junta **todos los sectores** en los que se observó la estrella. Pi Mensae está cerca del polo sur de la eclíptica y tiene muchos sectores de datos, cada uno con unos 4 tránsitos. Más tránsitos sumados dan un SNR mucho mayor, y por eso una señal de solo 300 ppm sale tan clara en el tránsito plegado.

## Parte 3. Repaso de las tres historias

Vuelve a leer la sección "Tres historias reales del sector 69" de la [lección B4](b4-false-positives.md). Para cada historia, responde en tu cuaderno, con tus palabras, antes de abrir la respuesta:

1. ¿Qué vio el sistema?
2. ¿Por qué parecía buena?
3. ¿Qué pista reveló el problema?
4. ¿Qué prueba o cambio lo resolvió?

!!! example "Ejercicio 2"
    Completa la tabla para las tres historias.

    | Caso | Lo que parecía | Lo que era | Prueba o cambio que lo resolvió |
    |---|---|---|---|
    | HD 23472 | ? | ? | ? |
    | WASP-18 b | ? | ? | ? |
    | HD 271883 | ? | ? | ? |

    ??? success "Ver respuesta"
        | Caso | Lo que parecía | Lo que era | Prueba o cambio que lo resolvió |
        |---|---|---|---|
        | HD 23472 | un planeta nuevo de 10,29 días | un tránsito del planeta b y uno del planeta c, juntados en un período falso | crossmatch **tránsito a tránsito**: si al menos la mitad de las caídas coincide con tránsitos previstos de planetas conocidos, y es improbable que sea azar, la señal es conocida |
        | WASP-18 b | una binaria eclipsante (caída en la fase 0,5) | un planeta tan caliente que su luz desaparece cuando pasa detrás de la estrella (ocultación, unas 340 ppm) | veto de la prueba `secondary` solo cuando el secundario es al menos el **10 %** del principal |
        | HD 271883 | el candidato perfecto: 6,61 días, 4 900 ppm, pasó todo | defecto de un único sector | prueba `other_sectors`: la señal no reapareció con la fuerza esperada (SNR 45–64) en los sectores 67, 68 y 97 |

        Fíjate en el patrón. En el primer caso, el error fue del **crossmatch** (consideró "nuevo" algo que era conocido). En el segundo, el vetting era **demasiado estricto** (reprobó un planeta real). En el tercero, el vetting básico era **demasiado laxo** para ese tipo de defecto y necesitó una etapa extra. Un sistema confiable tiene que equivocarse poco en las tres direcciones.

!!! example "Ejercicio 3"
    En la curva de luz de un dossier ves tres tránsitos marcados en rojo. Dos de ellos caen exactamente sobre líneas azules punteadas, y el tercero cae al final de un tramo de datos, justo antes de un hueco. El tránsito plegado muestra una "U" bonita. ¿Qué concluyes?

    ??? success "Ver respuesta"
        Sospecha fuertemente de un **defecto del telescopio**. Las líneas azules punteadas son momentum dumps, y el final de un tramo de datos es un borde de órbita, donde aparecen rampas. Las tres caídas coinciden con momentos problemáticos. La "U" bonita en el tránsito plegado no salva la señal: solo muestra que las caídas se parecen entre sí, no de dónde vienen. La prueba `edges_dumps` debe haber fallado; compruébalo en la tabla de vetting. El siguiente paso sería ver si la estrella tiene otros sectores y si la señal aparece en ellos.

## Checklist de la lección

- [ ] Hice el tutorial de Planet Hunters TESS y leí la guía de campo.
- [ ] Clasifiqué al menos 200 curvas de luz en Zooniverse.
- [ ] Corrí `uv run planethunter run-target 261136679` y encontré la señal de 6,27 días con clase `KNOWN_PLANET`.
- [ ] Corrí el vetting y generé el dossier de Pi Men c.
- [ ] Encontré en el dossier el período, la profundidad y los tránsitos marcados en rojo.
- [ ] Recorrí las diez secciones del dossier sabiendo qué buscar en cada una.
- [ ] Expliqué, con mis palabras, qué prueba resolvió cada una de las tres historias.
- [ ] Hice los tres ejercicios sin mirar la respuesta.

## Para ir más allá

- Eisner et al. (2021), "Planet Hunters TESS II: findings from the first two years of TESS", *Monthly Notices of the Royal Astronomical Society* 501, 4669. Lo que encontraron los voluntarios en los primeros dos años. Mira las figuras con ejemplos de curvas.
- Eisner et al. (2020), "Planet Hunters TESS I: TOI 813, a subgiant hosting a transiting Saturn-sized planet on an 84 day orbit", *Monthly Notices of the Royal Astronomical Society* 494, 750. El primer planeta del proyecto, con la historia de cómo lo encontraron los voluntarios.
- Huang et al. (2018), "TESS Discovery of a Transiting Super-Earth in the pi Mensae System", *The Astrophysical Journal Letters* 868, L39. El artículo de Pi Men c. Compara los números del resumen con los de tu dossier.
- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/): busca "pi Men c" y compara el período, el radio y la profundidad con tu dossier, como sugiere la guía del proyecto.
