# Nivel avanzado: pensar como quien construye y publica

<p class="meta">Nivel avanzado · cerca de 16 semanas · 4 a 6 horas por semana</p>

Llegaste aquí sabiendo qué es un tránsito, cómo se lee un periodograma, por qué SNR 7,1 es un límite razonable y qué busca cada prueba del vetting. Este nivel cambia el punto de vista. Hasta ahora aprendiste a **usar** e **interpretar** PlanetHunter. A partir de aquí vas a aprender a **cuestionar** sus decisiones, leer los artículos que las justifican, medir el efecto de un cambio y llevar un candidato hasta la comunidad científica.

!!! abstract "Al final de este nivel vas a poder"
    - Leer un artículo de método (BLS, TLS, Robovetter, triceratops, ExoMiner) y decir qué hace, qué supone y dónde falla.
    - Comparar el vetting de PlanetHunter con el de las misiones Kepler y TESS y señalar qué falta.
    - Interpretar una probabilidad de falso positivo (FPP) sin tratarla como verdad absoluta.
    - Proponer un cambio en un límite de `config/thresholds.yaml`, medir antes y después y escribir el resultado con intervalo de confianza.
    - Armar un paquete de envío de CTOI completo, con búsqueda de literatura y texto honesto.

## Para quién es este nivel

Para quien terminó el [nivel intermedio](../intermediate/index.md) y la ruta de programación hasta la lección P3. Vas a ejecutar comandos, editar un archivo de configuración y leer código Python. No necesitas saber escribir un pipeline desde cero, pero sí poder seguir una función de 50 líneas y entender qué entra y qué sale.

La matemática sube un escalón. Aparecen sumatorias, chi-cuadrado, probabilidad condicional y el teorema de Bayes. Cada fórmula viene con la explicación en palabras y con un ejercicio numérico resuelto. Si una ecuación te traba, lee la frase que viene después, haz el ejercicio y vuelve.

## Las lecciones

| Lección | Semanas | En una frase |
|---|---|---|
| [A1. Algoritmos de detección](a1-detection-algorithms.md) | 1–3 | La estadística del BLS y del TLS, los compromisos del detrending y por qué los monotránsitos son el nicho más prometedor. |
| [A2. Cómo hacen vetting las misiones](a2-mission-vetting.md) | 3–6 | Data Validation, Robovetter, catálogo de TOIs y catálogo de binarias, comparados lado a lado con las pruebas de PlanetHunter. |
| [A3. Probabilidad de falso positivo](a3-false-positive-probability.md) | 6–8 | Razonamiento bayesiano, vespa y triceratops, los escenarios de falso positivo y el caso real de WASP-100 b. |
| [A4. Aprendizaje automático](a4-machine-learning.md) | 8–11 | Redes neuronales que clasifican señales, etiquetas, fuga de información, calibración y por qué, en el proyecto, el ML solo reordena. |
| [A5. Medir el sistema](a5-measuring-the-system.md) | 11–13 | Recall, completitud, injection-recovery, intervalo de Wilson y el método antes/después para cambiar un límite. |
| [A6. Del candidato a la comunidad](a6-from-candidate-to-community.md) | 13–16 | ExoFOP, envío de CTOI, el programa de seguimiento de TESS, búsqueda de literatura y ética. |
| [Autoevaluación](assessment.md) | 16 | Diez preguntas abiertas con modelos de respuesta. |

El orden importa. A1 y A2 dan el vocabulario para A3. A5 depende de todo lo anterior, porque medir solo tiene sentido cuando sabes qué estás midiendo. A6 cierra el ciclo y usa todo.

## Cómo leer un artículo científico

En este nivel vas a leer unos diez artículos. Nadie lee un artículo técnico de principio a fin la primera vez, ni siquiera sus autores. La técnica de abajo es una variación del método de "tres pasadas" descrito por Keshav (2007).

**Primera pasada (15 a 20 minutos): decidir si vale la pena leerlo.**

1. Lee el **título** y el **resumen** (abstract). Anota en una frase: ¿qué problema resuelve el artículo?
2. Salta a la **conclusión** (o "Summary", "Discussion"). Anota: ¿qué afirman haber logrado?
3. Mira **todas las figuras y tablas**, con sus leyendas. En artículos de exoplanetas, las figuras cargan la mitad del contenido: curvas de luz, periodogramas, histogramas de completitud.
4. Lee los títulos de las secciones.

Al final, deberías poder decir qué hace el artículo sin haber leído ninguna ecuación.

**Segunda pasada (1 a 2 horas): entender el argumento.**

1. Lee la **introducción** completa. Dice qué existía antes y qué vacío llena el artículo.
2. Lee la sección de **método** saltándote las derivaciones. Detente en cada ecuación y pregúntate: ¿qué entra, qué sale, en qué unidad?
3. Lee los **resultados** con las figuras al lado.
4. Marca las referencias que aparecen varias veces. Son la base del campo.

**Tercera pasada (cuando la necesites): reconstruir.**

Solo cuando vayas a implementar algo o no estés de acuerdo con el artículo. Rehaz las cuentas principales, reproduce una figura con datos públicos y busca las hipótesis escondidas ("suponemos órbita circular", "ignoramos el ruido correlacionado").

!!! tip "Dónde encontrar los artículos"
    Casi todos los artículos del área tienen versión gratuita en arXiv (arxiv.org, sección astro-ph.EP para planetas). ADS (ui.adsabs.harvard.edu) es el buscador de la astronomía: escribe autor y año, por ejemplo `author:"Kovacs" year:2002`, y te muestra el enlace a arXiv y a la revista. La lección A6 enseña a usar ADS para buscar literatura sobre un objetivo.

!!! note "Cuaderno de lectura"
    Para cada artículo, escribe media página con: (1) problema; (2) método en tres frases; (3) el número o la figura principal; (4) una hipótesis que hace el artículo; (5) dónde aparece eso en PlanetHunter, o por qué no aparece. Ese cuaderno será la base de tus respuestas en la autoevaluación.

## Ritmo sugerido

Cada lección tiene lectura obligatoria (los artículos listados en las [referencias](../references.md)), ejercicios resueltos y una práctica en la herramienta. Una semana típica:

- 2 horas de lectura (primera y segunda pasada de un artículo).
- 1 hora con la lección del sitio y los ejercicios.
- 1 a 2 horas de práctica: ejecutar un comando, abrir un dossier, cambiar un parámetro.
- 30 minutos para el cuaderno de lectura y el cuaderno de revisiones.

Si una semana rinde menos, no te saltes la práctica. Leer sobre centroides sin mirar nunca una imagen de diferencia no fija nada.

## Cómo saber que terminaste

Terminaste el nivel avanzado cuando puedes, sin ayuda:

1. Explicarle a un compañero, con una fórmula y un dibujo, por qué el BLS maximiza $s^2/[r(1-r)]$ y qué tiene que ver eso con la SNR.
2. Tomar un artículo reciente de validación de un planeta de TESS y listar cada prueba de vetting usada, marcando cuál tiene PlanetHunter y cuál no.
3. Mirar la salida de triceratops de un candidato y decir qué escenario domina, qué lo haría menos probable y qué observación ayudaría.
4. Hacer un cambio en `config/thresholds.yaml`, ejecutar el benchmark antes y después, calcular el intervalo de Wilson y escribir un informe de una página en `docs/benchmarks/`.
5. Armar el paquete de envío de un candidato P1 (aunque sea hipotético), con efeméride, incertidumbres, notas, búsqueda de literatura y lista de citas.
6. Aprobar con holgura la [autoevaluación](assessment.md).

Después de eso, el siguiente paso ya no es otro curso. Es contribuir: revisar candidatos con criterio, abrir issues cuando un número parezca incorrecto y, algún día, enviar un CTOI que sobreviva a la mirada del equipo de TESS.
