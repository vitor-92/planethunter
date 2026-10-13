# B4. Por qué casi toda señal es falsa

<p class="meta">Nivel básico · semana 5 · unas 4 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Qué es una binaria eclipsante y las tres marcas que la delatan: forma de V, eclipses impares y pares diferentes, eclipse secundario.
    - Cómo una estrella vecina en el mismo píxel produce un falso tránsito en el objetivo.
    - Qué defectos del telescopio imitan tránsitos: momentum dumps, bordes de órbita, luz dispersa.
    - Cómo estorba la variabilidad de la propia estrella.
    - Tres historias reales del sector 69 y cuánto logra descartar el vetting de PlanetHunter.

## El tamaño del problema

Una caída de brillo periódica **no** prueba que exista un planeta. En el primer análisis real de PlanetHunter, con 2 164 estrellas del sector 69, el embudo quedó así:

| Etapa | Señales |
|---|---|
| Caídas periódicas encontradas (SDE ≥ 7) | 887 |
| Sin correspondencia en ningún catálogo (clase `NEW`) | 648 |
| Aprobadas en el vetting básico | 11 |
| Candidatos fuertes (P1) después del vetting profundo | **0** |

De 887 señales, ninguna sobrevivió como candidato fuerte. Esto no es un defecto: es lo esperado. El TESS y la comunidad ya revisaron estos datos muchas veces, y la inmensa mayoría de las caídas que nadie catalogó son ruido o imitaciones. El trabajo real no es encontrar caídas. Es **descartar** todo lo que no es planeta.

El nombre técnico de una señal que parece planeta pero no lo es: **falso positivo**. La batería de pruebas que intenta descartarlos se llama **vetting** (del inglés *to vet*, examinar con cuidado; en español puedes pensarlo como "verificación"). Vamos a las imitaciones más comunes.

## Binarias eclipsantes

Una **binaria eclipsante** (EB, del inglés *eclipsing binary*) son dos estrellas que orbitan una alrededor de la otra, con la órbita alineada con nosotros. Una pasa por delante de la otra, y el brillo total cae. Es el falso positivo más común.

Si las dos estrellas tienen tamaños parecidos, el eclipse es profundo, de decenas por ciento, y nadie lo confunde con un planeta. El peligro está en los casos en que la caída queda poco profunda. Eso pasa cuando el eclipse es **rasante** (una estrella solo roza el borde de la otra) o cuando la estrella que pasa por delante es muy pequeña. Tres marcas delatan a la binaria.

### Marca 1: forma de V

En el tránsito de un planeta, el disco pequeño entra entero delante de la estrella, y el fondo queda casi plano: forma de **U**. En un eclipse rasante entre estrellas, la parte cubierta crece hasta un máximo y enseguida empieza a disminuir, sin fondo plano: forma de **V**.

```
   planeta (U)                binaria rasante (V)
  ───╮       ╭───            ───╮       ╭───
     ╰───────╯                   ╲     ╱
                                  ╲   ╱
                                   ╲ ╱
```

Cuidado: los planetas que pasan cerca del borde de la estrella también hacen V. Por eso la forma, por sí sola, es una pista, no una prueba.

### Marca 2: eclipses impares y pares diferentes

En una binaria hay dos eclipses por vuelta: la estrella A delante de B, y después B delante de A. Si las estrellas son diferentes, los dos eclipses tienen profundidades diferentes. El algoritmo de búsqueda, que busca caídas iguales, a veces junta los dos y devuelve **la mitad del período verdadero**. Entonces los tránsitos "impares" (1.º, 3.º, 5.º...) son de un tipo y los "pares" (2.º, 4.º, 6.º...) de otro.

```
brillo
  ───╮   ╭───╮ ╭───╮   ╭───╮ ╭───
     │   │   ╰─╯   │   │   ╰─╯        impares profundos, pares poco profundos
     ╰───╯         ╰───╯              -> es binaria con período 2P
      1º    2º      3º    4º
```

Un planeta hace todos los tránsitos con la misma profundidad.

### Marca 3: eclipse secundario

La estrella compañera también brilla. Cuando pasa **detrás** de la principal, su luz desaparece por un tiempo, y el brillo total vuelve a caer, en general menos. En una órbita circular, esto ocurre exactamente a mitad de camino entre dos eclipses principales: en la **fase 0,5**.

Un planeta común casi no emite luz propia visible, así que no produce un secundario medible. Hay excepciones, y una de ellas es una de las historias de este capítulo.

| Característica | Planeta | Binaria eclipsante |
|---|---|---|
| Forma | U (fondo plano) | V, cuando es rasante |
| Impares y pares | misma profundidad | pueden diferir |
| Fase 0,5 | plana (o caída muy pequeña) | eclipse secundario |
| Profundidad | en general por debajo del 2 % | muchas veces por encima |
| Radio calculado | hasta ~2 radios de Júpiter | demasiado grande para un planeta |

## Binarias de fondo y contaminación

Recuerda la lección B3: cada píxel del TESS cubre 21″, y caben varias estrellas en él. Imagina el objetivo brillante y, detrás de él, casi en la misma dirección, una binaria eclipsante débil. La binaria tiene eclipses profundos, pero aporta solo una fracción pequeña de la luz total del píxel. Su eclipse aparece **diluido**, poco profundo, y parece el tránsito de un planeta en el objetivo.

$$ \delta_{\text{observada}} \approx \delta_{\text{binaria}} \times \frac{\text{luz de la binaria}}{\text{luz total}} $$

Esto se llama **binaria de fondo** o, de forma más general, **blend** (mezcla). Es traicionero porque la curva puede parecer perfecta: forma de U, impares iguales a los pares, ningún secundario visible (también está diluido).

Cómo atraparlo: si la caída viene de otra estrella, el "centro de luz" de la imagen se desplaza un poquito durante el tránsito, en dirección a la culpable. Es la prueba de **centroide**. En el vetting profundo, PlanetHunter también resta la imagen fuera del tránsito de la imagen durante el tránsito y ve **dónde** desapareció la luz (imagen de diferencia).

## Defectos del telescopio

Algunas caídas no vienen de ninguna estrella. Vienen del propio instrumento. Son los **sistemáticos**.

- **Momentum dumps.** El TESS se mantiene apuntado con ruedas de reacción, que acumulan rotación con el tiempo. Cada cierto tiempo se encienden pequeños propulsores para descargar esa rotación. El apuntado tiembla por un instante y el brillo medido salta. Si estos eventos se repiten a intervalos regulares, parecen tránsitos periódicos.
- **Bordes de órbita.** Al principio y al final de cada órbita de 13,7 días, el telescopio cambia de temperatura y el brillo medido sube o baja poco a poco, en rampa. Cuando la limpieza de los datos intenta quitar esa rampa, puede quedar una depresión que recuerda a un tránsito.
- **Luz dispersa.** Cerca del punto de la órbita más próximo a la Tierra, la luz de la Tierra y de la Luna entra en las cámaras y cambia el fondo de la imagen.

La marca registrada de los sistemáticos: ocurren en **un sector** y no se repiten en los otros, o caen exactamente encima de momentum dumps y bordes.

## Variabilidad de la propia estrella

Las estrellas no son lámparas perfectas.

- **Manchas y rotación.** Las estrellas giran y tienen manchas oscuras, como el Sol. Cuando la mancha pasa por el lado visible, el brillo cae; cuando sale, sube. Esto crea ondas de días.
- **Pulsaciones.** Algunas estrellas se hinchan y se encogen rítmicamente, en minutos u horas.
- **Fulguraciones (flares).** Explosiones en la superficie generan picos de brillo **hacia arriba**, rápidos.

PlanetHunter quita la variación lenta con un filtro (el **detrending**) y recorta solo los picos hacia arriba. Nunca recorta puntos hacia abajo, porque si no borraría los propios tránsitos. Cuando la estrella varía demasiado rápido, el filtro deja restos que pueden parecer caídas.

## Tres historias reales del sector 69

Estos casos ocurrieron el primer día de pruebas de PlanetHunter. Cada uno muestra por qué existe una etapa.

### 1. El planeta inventado: HD 23472

La estrella HD 23472 tiene **5 planetas conocidos**. En un solo sector, el sistema vio un tránsito del planeta b y un tránsito del planeta c. Con solo esas dos caídas, concluyó que había un planeta de **10,29 días**, que no existe. El crossmatch por período no lo atrapó, porque 10,29 días no es el período de ninguno de los dos.

No fue un caso aislado: lo mismo pasó con TOI-703 y GJ 143, y los tres llegaban a P1, la categoría de alerta inmediata. **Lo que lo resolvió:** la coincidencia **tránsito a tránsito**. Ahora el crossmatch revisa cada caída observada: si al menos la mitad de ellas coincide con tránsitos previstos de objetos conocidos, y una coincidencia así de buena es improbable por azar (menos del 1 %), la señal se marca como conocida. La verificación del azar llegó después: sin ella, la regla también "explicaba" caídas aleatorias, porque con ventanas de tiempo amplias es fácil que haya una coincidencia.

### 2. El planeta que parecía binaria: WASP-18 b

WASP-18 b es un planeta gigante, muy masivo y tan caliente que brilla. El TESS ve su luz desaparecer cuando pasa **detrás** de la estrella: una caída de unas **340 ppm** en la fase 0,5. Este fenómeno se llama **ocultación**. La prueba de eclipse secundario veía la caída y vetaba el planeta como binaria.

**Lo que lo resolvió:** el veto del secundario pasó a exigir que la caída secundaria sea de **al menos el 10 % de la principal**. Los planetas producen ocultaciones pequeñas; las estrellas compañeras, grandes. Ese mismo día apareció otro problema parecido: el catálogo de binarias eclipsantes del TESS contiene algunos Júpiter calientes conocidos (WASP-18 b, WASP-100 b, HATS-16 b). La corrección fue dar prioridad al catálogo de planetas confirmados sobre el de binarias.

### 3. El mejor candidato que no lo era: HD 271883

HD 271883 mostró una señal limpia de **6,61 días** y **4 900 ppm**. Pasó todas las pruebas básicas, el centroide estaba en el objetivo, no había binaria conocida. Parecía el candidato perfecto.

Pero la estrella fue observada en **10 sectores**. Si la señal fuera un planeta, debería aparecer fuerte en los otros: el SNR esperado en los sectores 67, 68 y 97 era de 45 a 64. No apareció con esa fuerza. Era un defecto de un solo sector. **Lo que lo resolvió:** la prueba de **otros sectores** (`other_sectors`), que busca la señal, incluso a ciegas, en los otros sectores de la misma estrella.

!!! warning "La lección general"
    Una alerta tiene que sobrevivir a intentos serios de descartarla. Desconfía de las señales demasiado bonitas: las tres historias son de señales que parecían excelentes.

## Cuánto logra el vetting básico

El proyecto midió el vetting básico (sin internet) en objetos de respuesta conocida del sector 69:

| Grupo | Señales | Aprobadas | Reprobadas |
|---|---|---|---|
| Planetas confirmados (`KNOWN_PLANET`) | 54 | 44 (81 %) | 10 (19 %) |
| Falsos positivos conocidos (`KNOWN_FP`) | 18 | 8 (44 %) | **10 (56 %)** |

Lee la segunda fila con atención: el vetting básico reprueba **el 56 % de los falsos positivos conocidos**, sin ninguna consulta a internet, y mantiene la mayoría de los planetas reales. Pero 8 falsos positivos todavía pasan. Según los comentarios del TFOPWG, cuatro de ellos solo muestran el eclipse secundario cuando se suman varios sectores, uno es una binaria con órbita excéntrica (secundario fuera de la fase 0,5), dos tienen forma de V solo marginal y uno es una binaria de fondo. Por eso existe el vetting profundo, que mira los píxeles, las estrellas vecinas y los otros sectores.

Siempre hay un compromiso. El límite de la prueba de forma de V se eligió midiendo: con el valor actual, marca 8 de los 18 falsos positivos, pero también marca 3 de 50 planetas reales (planetas rasantes, como HIP 65 A b, LTT 9779 b y TOI-2382 b). Aun así, desde el 2026-10-10 una forma de V reprueba la señal por sí sola (una **falla dura**), sin poner su score en cero. El proyecto midió el precio y lo aceptó: se pierden unos pocos Júpiter calientes rasantes por sector, y varias binarias dejan de colarse. Vas a ver cómo se suman las fallas en la lección [M5](../intermediate/m5-vetting-in-practice.md).

!!! tip "En la herramienta"
    Cada imitación de esta lección tiene una prueba en el vetting (`uv run planethunter vet <run_id>`):

    | Imitación | Pruebas |
    |---|---|
    | Binaria eclipsante | `odd_even` (impar/par), `secondary` (fase 0,5), `secondary_scan` (otras fases), `shape` (V o U), `kdr25_grazing` (solo roza el borde de la estrella), `radius` (demasiado grande) |
    | Binaria de fondo, contaminación | `centroid`, `duration`; en el profundo, `tpf_difference_image` y `gaia_neighbors` |
    | Defectos del telescopio | `edges_dumps`, `consistency`; en el profundo, `other_sectors` |
    | Variabilidad de la estrella | el detrending, en la etapa de limpieza, y la prueba `consistency` |

    En el dossier, el gráfico **Odd, even and secondary** (impar, par y secundario) muestra tres paneles lado a lado: tránsitos impares, pares y la fase 0,5. En la curva de luz, líneas azules punteadas marcan los momentum dumps. Los límites de cada prueba están en `config/thresholds.yaml`, con un comentario que explica el porqué de cada valor.

!!! example "Ejercicio 1"
    El objetivo de un píxel es una estrella brillante. Detrás de ella hay una binaria eclipsante débil que aporta el **1 %** de la luz total del píxel. La binaria tiene eclipses que apagan el **50 %** de su luz. ¿Qué profundidad mide el TESS? ¿Qué tamaño de planeta imitaría eso en una estrella igual al Sol?

    ??? success "Ver respuesta"
        Profundidad observada: $0{,}50 \times 0{,}01 = 0{,}005$, es decir, **5 000 ppm** (0,5 %).

        Planeta equivalente: $R_p/R_\star = \sqrt{0{,}005} \approx 0{,}071$. En una estrella de 1 R☉ (109 R⊕), $R_p \approx 0{,}071 \times 109 \approx 7{,}7$ R⊕, un planeta del tamaño de Neptuno a Saturno. Totalmente plausible. Solo las pruebas que miran **dónde** desapareció la luz (centroide, imagen de diferencia) o que conocen las estrellas vecinas (Gaia) desenmascaran este caso.

!!! example "Ejercicio 2"
    Supón un tránsito principal de 10 000 ppm. En la fase 0,5 aparece una caída de 340 ppm. Según la regla de PlanetHunter, ¿este secundario veta la señal? ¿Y si la caída en la fase 0,5 fuera de 2 500 ppm?

    ??? success "Ver respuesta"
        La regla: veta solo si el secundario es de al menos el 10 % del principal. El 10 % de 10 000 ppm es 1 000 ppm.

        - 340 ppm es el 3,4 % del principal. **No veta.** Es compatible con la ocultación de un planeta caliente, como WASP-18 b.
        - 2 500 ppm es el 25 % del principal. **Veta.** Un secundario de ese tamaño indica una compañera que emite mucha luz: una estrella, no un planeta.

        Fíjate en que la regla no dice "cualquier secundario es binaria". Se ajustó después de que un planeta real fue reprobado.

!!! example "Ejercicio 3"
    Para cada descripción, di cuál es el sospechoso más probable y qué prueba lo atraparía.

    1. Los tránsitos 1, 3 y 5 tienen 8 000 ppm; los tránsitos 2, 4 y 6 tienen 3 000 ppm.
    2. Todas las caídas quedan a pocos minutos de una línea azul punteada en el dossier.
    3. Una señal preciosa en un sector; la estrella tiene otros 9 sectores y la señal no aparece en ninguno.
    4. Durante el tránsito, el centro de luz de la imagen se desplaza en dirección a una estrella vecina.

    ??? success "Ver respuesta"
        1. **Binaria eclipsante** con período verdadero igual al doble del encontrado. Prueba `odd_even`.
        2. **Defecto del telescopio** (momentum dumps). Prueba `edges_dumps`.
        3. **Sistemático de un solo sector**, como HD 271883. Prueba `other_sectors`.
        4. **Contaminación por una estrella vecina** (probable binaria de fondo). Pruebas `centroid` y `tpf_difference_image`.

## Checklist de la lección

- [ ] Sé qué es una binaria eclipsante y las tres marcas (V, impar/par, secundario).
- [ ] Sé explicar por qué la forma de V es una pista y no una prueba (planetas rasantes).
- [ ] Sé calcular la dilución de una binaria de fondo.
- [ ] Sé citar tres defectos del telescopio y su marca (un solo sector, encima de dumps o bordes).
- [ ] Sé cómo estorban las manchas, las pulsaciones y las fulguraciones, y por qué el detrending nunca recorta hacia abajo.
- [ ] Sé contar las tres historias (HD 23472, WASP-18 b, HD 271883) y la prueba que resolvió cada una.
- [ ] Sé que el vetting básico reprueba el 56 % de los falsos positivos conocidos del sector 69 y mantiene el 81 % de los planetas.
- [ ] Hice los tres ejercicios sin mirar la respuesta.

## Para ir más allá

- Prša et al. (2022), "TESS Eclipsing Binary Stars. I. Short-cadence Observations of 4584 Eclipsing Binaries in Sectors 1–26", *The Astrophysical Journal Supplement Series* 258, 16. El catálogo de binarias que PlanetHunter replica localmente. Hojea las figuras de curvas de luz para ver eclipses de verdad.
- Winn (2010), "Transits and Occultations", arXiv:1001.2010. La sección sobre ocultaciones explica por qué los planetas calientes como WASP-18 b muestran una caída en la fase 0,5.
- Guerrero et al. (2021), *The Astrophysical Journal Supplement Series* 254, 39. Muestra cómo el equipo del TESS separa planetas de falsos positivos; compáralo con la tabla "En la herramienta" de esta lección.
- El archivo `docs/benchmarks/2026-10-09-s0069-vetting.md` del repositorio. La tabla "What was measured and fixed" (lo que se midió y se corrigió) cuenta, con números, cada ajuste del vetting. La vas a estudiar a fondo en la lección M5.
