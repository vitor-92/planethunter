# A6. Del candidato a la comunidad

<p class="meta">Nivel avanzado · semanas 13–16 · cerca de 16 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Quién decide cada peldaño de la escalera señal → candidato → CTOI → TOI → validado → confirmado.
    - Cómo usar el ExoFOP: páginas de objetivo, notas de la comunidad, archivos de seguimiento.
    - Qué campos necesita un envío de CTOI y cómo calcular las incertidumbres de la efeméride.
    - Qué hace cada subgrupo del programa de seguimiento de TESS (TFOP).
    - Cómo buscar literatura en ADS y en arXiv antes de enviar cualquier cosa.
    - Las reglas de ética y el checklist de un paquete de envío completo.

Hasta aquí, todo ocurrió dentro de tu computadora. Esta lección trata del momento en que un candidato sale de ella. A partir de ahí, otras personas van a gastar tiempo de telescopio en lo que enviaste. Eso exige cuidado, honestidad y un paquete de información que permita a cualquier persona rehacer tu razonamiento.

## 1. La escalera y quién decide cada peldaño

| Peldaño | Qué significa | Quién decide |
|---|---|---|
| **Señal** | Una caída periódica que superó los límites de detección | El pipeline (SDE ≥ 9, SNR ≥ 7,1, ≥ 2 tránsitos) |
| **Candidato** | Una señal nueva que sobrevivió al vetting y a la revisión humana | Tú, con PlanetHunter |
| **CTOI** | Candidato registrado en el ExoFOP por la comunidad | Tú lo envías |
| **TOI** | Objeto de interés oficial de TESS | El equipo de TOIs de TESS, que puede promover el CTOI |
| **Planeta validado** | Probabilidad de falso positivo muy baja, con datos de seguimiento (en general imagen de alta resolución y fotometría desde tierra) | Un artículo revisado por pares |
| **Planeta confirmado** | Naturaleza planetaria demostrada por una medida independiente, en general la masa por velocidad radial o por variación en el tiempo de los tránsitos | Un artículo revisado por pares |

PlanetHunter llega, como máximo, hasta el segundo peldaño. Enviar el CTOI es un acto tuyo. Todos los peldaños siguientes dependen de otras personas y de otros telescopios. Por eso ningún texto tuyo, en ningún lugar, debe usar la palabra "descubrimiento" para un candidato.

## 2. El ExoFOP

El **ExoFOP** (exofop.ipac.caltech.edu/tess) es el punto de encuentro de quienes hacen seguimiento de los objetivos de TESS. Ahí el equipo de TESS publica los TOIs, la comunidad envía CTOIs y los observadores del programa de seguimiento registran lo que hicieron.

### La página de un objetivo

Escribe el número TIC en la búsqueda del ExoFOP. La página del objetivo reúne, en general:

- **Parámetros de la estrella** del TIC (radio, masa, temperatura, Tmag, distancia) y nombres alternativos (HD, Gaia, 2MASS).
- **TOIs y CTOIs** asociados a la estrella, con período, época, profundidad, disposición e historial.
- **Notas** (observing notes) escritas por miembros del equipo y de la comunidad: "secundario visible en el sector X", "binaria visual a 3″", "tránsito confirmado desde tierra". **Léelas todas** antes de cualquier decisión.
- **Archivos subidos** por observadores: curvas de luz de telescopios en tierra, imágenes de alta resolución con curvas de contraste, espectros.
- **Resumen de las observaciones** ya hechas: imagen, espectroscopía, series temporales.
- **Enlaces** a los informes de Data Validation del SPOC (lección A2).

Para enviar CTOIs o escribir notas, necesitas crear una cuenta en el ExoFOP.

!!! info "PlanetHunter ya lee el ExoFOP"
    Los espejos `toi` y `ctoi` del proyecto son copias de las tablas públicas del ExoFOP, sincronizadas con `uv run planethunter mirrors sync`. El crossmatch se niega a clasificar una señal como `NEW` si algún espejo falta o es demasiado antiguo para su propio límite (48 horas para las tablas de TOIs, CTOIs y del NASA Exoplanet Archive), y el comando de alertas vuelve a verificarlo justo antes de enviar. El proyecto también mantiene espejos de algunas listas de candidatos publicados (clase `KNOWN_PUBLISHED`), pero ni de lejos de todas. Y las **notas** y los **archivos** de la página del objetivo no están en los espejos. Esa lectura siempre te toca a ti.

## 3. Antes de enviar: búsqueda de literatura

Los catálogos se atrasan. Un planeta puede estar en un artículo aceptado hace dos semanas y todavía no estar en el NASA Exoplanet Archive. Un candidato puede aparecer en la tabla de un artículo sobre otro tema. La búsqueda de literatura es la última línea de defensa contra enviar algo ya conocido.

### En ADS

ADS (ui.adsabs.harvard.edu) indexa prácticamente toda la literatura de astronomía. Estrategias:

1. **Por el nombre del objeto**: `object:"HD 23472"`. ADS resuelve nombres conocidos mediante las bases de datos de objetos astronómicos y encuentra artículos que citan la estrella.
2. **Por el número TIC en el texto completo**: `full:"TIC 261136679"`. Captura tablas y apéndices.
3. **Por todos los nombres**: repite con el nombre HD, el identificador Gaia DR3 y el 2MASS de la página del ExoFOP. Los artículos antiguos no usan TIC.
4. **Ordena por fecha** y lee al menos los resúmenes de los resultados de los últimos dos años.

### En arXiv

Los artículos recientes aparecen primero en arXiv (arxiv.org), en la sección **astro-ph.EP** (planetas). La búsqueda de arXiv busca en el título, los autores y el resumen, no en el texto completo. Por eso, además de buscar por el nombre, recorre el listado de las últimas semanas de astro-ph.EP buscando trabajos sobre el mismo campo, la misma misión o el mismo tipo de objeto (por ejemplo, "TESS single transits").

### Qué registrar

Fecha de la búsqueda, consultas usadas, número de resultados, artículos relevantes y conclusión. En el proyecto, el agente `research-scout` hace este barrido antes de cualquier P0. Pero el registro escrito es parte del paquete de envío.

## 4. El envío de un CTOI

El formulario del ExoFOP cambia de vez en cuando. Revisa siempre la página de ayuda antes de enviar. Los campos habituales, visibles en las columnas de la tabla pública de CTOIs, son:

| Campo | Unidad | De dónde viene en PlanetHunter |
|---|---|---|
| TIC ID | — | `tic_id` |
| Período y error | días | `period_days` e incertidumbre del ajuste |
| Época del tránsito y error | BJD (TDB), completo | `t0_btjd` + 2 457 000 |
| Profundidad y error | ppm | `depth_ppm` del ajuste |
| Duración y error | horas | `t14_h` del ajuste |
| Radio del planeta (opcional) | R⊕ | `rp_rearth`, con el radio estelar del TIC |
| Disposición del usuario | por ejemplo PC | tu decisión de revisión |
| Notas | texto libre | resumen del dossier |

### Cuidados con la efeméride

- **BTJD no es BJD.** TESS usa BTJD = BJD − 2 457 000. El ExoFOP espera el BJD completo. Error clásico: enviar 3180,45 en lugar de 2 460 180,45.
- **Elige la época en el medio de los datos.** El período y la época salen correlacionados de un ajuste. Una época en el centro del intervalo observado minimiza esa correlación y da el menor error de época.
- **Incertidumbres reales.** El paso de la grilla del TLS no es una incertidumbre. Usa un ajuste de modelo de tránsito con estimación de error (por ejemplo, muestreo por MCMC o bootstrap), o al menos el ancho del pico del periodograma, y di cuál usaste.
- **Propagación.** La incertidumbre de un tránsito futuro, $n$ órbitas después, crece con $n$:

$$
\sigma_{T}(n) = \sqrt{\sigma_{T_0}^2 + n^2\, \sigma_P^2} .
$$

Esto decide si los observadores en tierra pueden planificar una observación, y es el mismo motivo por el que el crossmatch del proyecto ignora efemérides con incertidumbre propagada mayor a 1 día.

### Las notas

Las notas las leen personas ocupadas. Deben decir, en pocas líneas: cómo se encontró la señal (datos, sectores, pipeline), qué se probó y con qué resultado, qué **no** se probó, y qué observación ayudaría. Números, no adjetivos.

## 5. El programa de seguimiento de TESS (TFOP)

El **TFOP** (TESS Follow-up Observing Program) organiza a los observadores que hacen seguimiento de los TOIs. El grupo de trabajo (TFOPWG) se divide en subgrupos. Cada uno ataca escenarios de falso positivo diferentes, y vale la pena leer la tabla con la lección A3 abierta:

| Subgrupo | Qué hace | Escenarios que elimina |
|---|---|---|
| **SG1** fotometría desde tierra | Observa un tránsito previsto con un telescopio en tierra, con píxeles mucho más pequeños que los de TESS | Vecinas (NEB, NTP): muestra en qué estrella ocurre el tránsito; verifica si la profundidad cambia con el color (las binarias tienden a cambiar) |
| **SG2** espectroscopía de reconocimiento | Espectros de resolución moderada | Binarias espectroscópicas, estrellas gigantes o de rotación rápida; refina los parámetros estelares |
| **SG3** imagen de alta resolución | Óptica adaptativa o speckle, produce una curva de contraste | Compañeras cercanas no resueltas (PEB, SEB, STP, BEB) |
| **SG4** velocidad radial precisa | Mide la oscilación de la estrella causada por el planeta | Mide la masa: es el camino de la confirmación |
| **SG5** fotometría espacial | Observaciones con otros telescopios espaciales | Refina la efeméride y la forma del tránsito |

El SG1 es el subgrupo más abierto a observadores con telescopios modestos, incluidos aficionados experimentados, para objetivos brillantes con tránsitos profundos. Participar exige seguir las reglas del programa. La página del TFOP en el HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html) es el punto de partida. El software AstroImageJ (Collins et al. 2017) es la herramienta estándar para reducir esas observaciones.

## 6. Ética

1. **Vocabulario.** Señal, candidato, CTOI, TOI, validado, confirmado. Nunca "descubrimiento", ni en redes sociales, ni en una conversación con un periodista, ni "entre amigos" en una publicación pública.
2. **Cita a quien produjo los datos.** Toda presentación, nota o artículo cita: la misión TESS (Ricker et al. 2015), el pipeline de la curva de luz usada (SPOC, Jenkins et al. 2016; o QLP, Huang et al. 2020), el TIC (Stassun et al. 2019), Gaia (Gaia Collaboration, Prusti et al. 2016; y Vallenari et al. 2023 para el DR3), el MAST, y las bibliotecas usadas (lightkurve, astropy, TLS, wotan, triceratops). Los datos son públicos porque mucha gente trabajó para eso.
3. **Da crédito a quien lo vio antes.** Si una nota del ExoFOP o un voluntario de Planet Hunters TESS ya señaló la señal, cítalo. Si la señal ya está en un artículo, no es tuya para enviarla como nueva.
4. **Respeta los datos de seguimiento.** Los archivos que los observadores suben al ExoFOP tienen reglas de uso. Antes de usarlos en un trabajo, lee la política y, si tienes dudas, pregunta a los autores.
5. **No desperdicies tiempo de telescopio.** Cada CTOI débil consume horas de voluntarios y profesionales. Envía pocos y buenos. Un CTOI que resulta ser un falso positivo obvio en la primera observación quema credibilidad.
6. **Informa lo que falló.** Una prueba que no pudiste correr, un FPP intermedio, un vecino no excluido: todo va en las notas. Esconder un problema es peor que tener el problema.

!!! tip "En la herramienta"
    - El dossier (`uv run planethunter dossier <signal_id>`) ya trae enlaces a la página del objetivo en el ExoFOP, al Exoplanet Archive y a SIMBAD, además de la sección "Next action" (próxima acción).
    - La tabla `signals` graba la proveniencia de cada fila: sector, autor de la curva, `pipeline_version` y `run_id`. Copia esos campos al paquete.
    - `uv run planethunter review <signal_id> follow_up --note "..."` marca el candidato mientras preparas el envío.

## 7. Checklist del paquete de envío

- [ ] Dossier HTML del candidato, revisado sección por sección.
- [ ] Clase `NEW` con cada espejo dentro de su límite de antigüedad en la fecha del paquete (48 h para TOIs, CTOIs y el Archive; anota las edades).
- [ ] Página del objetivo en el ExoFOP leída, incluidas todas las notas y archivos.
- [ ] Búsqueda de literatura registrada: fecha, consultas en ADS y en arXiv, resultado.
- [ ] Efeméride: período ± error (d), época BJD completa ± error, con la época en el medio de los datos y el método de error declarado.
- [ ] Profundidad ± error (ppm), duración ± error (h), radio estimado (R⊕) y radio estelar usado.
- [ ] Tabla de vetting completa: cada prueba con valor, límite y veredicto, incluidas las "sin datos".
- [ ] Imagen de diferencia, vecinos Gaia y resultado de otros sectores.
- [ ] FPP y NFPP con los escenarios principales, o la razón por la que no se corrió.
- [ ] Proveniencia: sectores, autor de la curva (SPOC/QLP), `pipeline_version`, `run_id`.
- [ ] Predicción de los próximos tránsitos con incertidumbre, para facilitar el trabajo del SG1.
- [ ] Texto de las notas, con números y limitaciones.
- [ ] Lista de citas.
- [ ] Revisión por una segunda persona antes de enviar.

!!! example "Ejercicio 1. Efeméride para el ExoFOP"
    Tu ajuste dio una época de 3180,4512 ± 0,0011 BTJD y un período de 7,23492 ± 0,00004 d. (a) ¿Cuál es la época en BJD? (b) Predice el tránsito 50 órbitas después, con incertidumbre en minutos. (c) ¿Y 1 000 órbitas después?

    ??? success "Ver respuesta"
        (a) $3180{,}4512 + 2\,457\,000 = 2\,460\,180{,}4512$ BJD.

        (b) $3180{,}4512 + 50 \times 7{,}23492 = 3180{,}4512 + 361{,}7460 = 3542{,}1972$ BTJD, o $2\,460\,542{,}1972$ BJD. Incertidumbre: $\sqrt{0{,}0011^2 + (50 \times 0{,}00004)^2} = \sqrt{1{,}21 \times 10^{-6} + 4{,}0 \times 10^{-6}} = 0{,}00228$ d ≈ **3,3 min**. Excelente para planificar una observación.

        (c) $\sqrt{0{,}0011^2 + (1000 \times 0{,}00004)^2} \approx 0{,}040$ d ≈ **58 min**, unos 20 años después. La efeméride "envejece": domina el término del período. Por eso las nuevas observaciones de tránsito son valiosas incluso para planetas ya conocidos.

!!! example "Ejercicio 2. ¿Qué está mal en esta nota?"
    "¡Descubrimos un nuevo planeta rocoso potencialmente habitable en TIC 123456789! Período 14,2 días, FPP 0,02, lo que confirma que es un planeta. Época 3201,77."

    ??? success "Ver respuesta"
        1. "Descubrimos": vocabulario equivocado. Es un candidato.
        2. "Rocoso": sin masa, no se conoce la composición. Como mucho, "radio estimado de X R⊕".
        3. "Potencialmente habitable": afirmación sin base y sensacionalista; no pertenece a una nota técnica.
        4. "FPP 0,02 confirma": el FPP no confirma nada. Además, 0,02 está por encima de 0,015 y no se menciona el NFPP ni una imagen de alta resolución.
        5. "Época 3201,77": está en BTJD, sin error, y sin el período con su error.
        6. Falta: sectores, autor de la curva, pruebas hechas y limitaciones.

        Versión aceptable: "Candidato a tránsito en TIC 123456789, sectores 68–69 (SPOC 2 min), P = 14,2031 ± 0,0012 d, T0 = 2 460 201,7712 ± 0,0018 BJD, profundidad 610 ± 70 ppm, duración 3,1 ± 0,2 h, Rp ≈ 2,3 R⊕ para R* = 0,86 R☉ (TIC). Impar/par y secundario consistentes con cero; imagen de diferencia en el objetivo (desplazamiento 0,2 ± 0,3 px); sin vecinos Gaia capaces de producir la caída fuera del radio de exclusión de 6″. Triceratops: FPP 0,02, NFPP < 0,001, escenario principal PEB. Sin imagen de alta resolución. Se sugieren SG3 y SG1." (Números hipotéticos.)

!!! example "Ejercicio 3. Lo encontré en un preprint"
    Tu candidato pasó todo y es `NEW`. En la búsqueda de literatura, encuentras en arXiv un preprint de hace tres semanas que lista la misma estrella con un período compatible con el tuyo, en una tabla de "candidatos de tránsito único resueltos". No hay CTOI en el ExoFOP. ¿Qué haces?

    ??? success "Ver respuesta"
        1. **No enviarlo como nuevo.** La señal ya fue reportada. Enviarla sería apropiarse del trabajo de otra persona, aunque sin intención.
        2. Comparar con cuidado: ¿el período es el mismo, un alias, u otro planeta de la misma estrella? Si es otro período incompatible, puede ser un planeta adicional, y la nota debe citar el preprint.
        3. Si es el mismo: registrarlo en tu cuaderno, clasificarlo como conocido en la revisión (`rejected --reason already_known`, con la referencia en la nota) y, si tienes algo que agregar (sectores nuevos, mejor efeméride), escribir a los autores o dejar una nota en el ExoFOP citando su trabajo.
        4. Para el proyecto: abrir un issue sugiriendo que se consulte el espejo de literatura (ADS/arXiv) antes de la alerta, porque los catálogos todavía no reflejan el preprint.

## Checklist de la lección

- [ ] Sé quién decide cada peldaño de la escalera hasta el planeta confirmado.
- [ ] Abrí la página de al menos tres objetivos en el ExoFOP y leí las notas.
- [ ] Sé hacer búsquedas por objeto y por texto completo en ADS y recorrer astro-ph.EP.
- [ ] Sé convertir BTJD a BJD y propagar la incertidumbre de una efeméride.
- [ ] Sé qué hace cada subgrupo del TFOP y qué escenario de falso positivo elimina.
- [ ] Armé un paquete de envío completo para un candidato P1 (aunque sea hipotético), sin enviarlo.

## Para ir más allá

- Guerrero et al. (2021), *The Astrophysical Journal Supplement Series* 254, 39. Relee la parte sobre los CTOIs y la promoción a TOI, ahora desde el punto de vista de quien envía.
- Ricker et al. (2015), *Journal of Astronomical Telescopes, Instruments, and Systems* 1, 014003. El artículo de la misión TESS; es la cita obligatoria de cualquier trabajo con sus datos.
- Collins et al. (2017), *The Astronomical Journal* 153, 77. AstroImageJ, la herramienta estándar del SG1; muestra lo que la fotometría desde tierra puede verificar.
- Eisner et al. (2021), *Monthly Notices of the RAS* 501, 4669. Resultados de Planet Hunters TESS: cómo una comunidad de voluntarios organiza el envío de candidatos, con muchos tránsitos únicos.
- Página del TFOP en el HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html). Estructura del programa y cómo participar.
- Página de ayuda del ExoFOP (exofop.ipac.caltech.edu/tess). Formato actual de envío de CTOI y reglas de uso de los datos.
