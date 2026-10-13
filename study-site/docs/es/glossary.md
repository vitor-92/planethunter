# Glosario

<p class="meta">Términos del curso, en orden alfabético · consúltalo siempre que lo necesites</p>

Cada término trae una definición corta y, entre paréntesis, la lección en la que se explica con calma. Los términos con nombre en inglés aparecen como se usan en el área, con la traducción al lado. Los nombres en `fuente de código` son columnas, pruebas o comandos de PlanetHunter.

## A

**Alias.** Período equivocado que es múltiplo o fracción del verdadero (P/2, 2P, P/3, 3P...). Aparece porque, con pocos tránsitos y huecos en los datos, varios períodos "encajan" casi igual de bien. PlanetHunter prueba aliases en la búsqueda (`refine_alias`) y en el crossmatch. (B2, M3)

**Año luz.** Distancia que recorre la luz en un año: cerca de 9,46 billones de km. A pesar del nombre, mide distancia, no tiempo. (B1)

**Aprendizaje automático.** Programas que aprenden patrones a partir de ejemplos etiquetados en lugar de reglas escritas a mano. En el área, las redes neuronales clasifican señales de tránsito como planeta o falso positivo; las revisiones hechas con `planethunter review` son las etiquetas del futuro clasificador del proyecto. (A4)

## B

**Benchmark.** Prueba estandarizada que mide el desempeño del sistema siempre de la misma manera, para comparar versiones. El benchmark de recall de PlanetHunter usa 135 TOIs detectables del sector 69. (A5)

**Binaria de fondo.** Binaria eclipsante débil que está casi en la misma dirección que el objetivo, en el mismo píxel o en píxeles vecinos. Sus eclipses aparecen diluidos en la luz total e imitan el tránsito poco profundo de un planeta en el objetivo. (B4)

**Binaria eclipsante (EB).** Dos estrellas que orbitan una alrededor de la otra con la órbita alineada con nosotros, de modo que una eclipsa a la otra. Es el falso positivo más común; se delata por la forma en V, eclipses impares y pares distintos y eclipse secundario. (B4)

**Biweight.** Filtro robusto usado en el detrending: estima la tendencia lenta del brillo en una ventana móvil, sin dejarse arrastrar por puntos fuera de lo normal como los del propio tránsito. PlanetHunter usa la versión de la biblioteca wotan, con ventana de 1 día (ventanas más cortas solo para estrellas que varían rápido). (M4, A1)

**Blend.** Mezcla de la luz de dos o más estrellas en la misma medida. Ver **contaminación**. (B3, B4)

**BLS (Box Least Squares).** Algoritmo clásico de búsqueda de tránsitos: prueba muchos períodos y, para cada uno, ajusta una "caja" (caída rectangular) a los datos plegados. Propuesto por Kovács, Zucker y Mazeh en 2002. (M3, A1)

**Borde de órbita.** Inicio o fin de cada órbita de 13,7 días del TESS, donde aparecen rampas de brillo ligadas a cambios de temperatura. Las rampas mal eliminadas imitan tránsitos; la prueba `edges_dumps` desconfía de los tránsitos que caen en ellas. (B4)

**BTJD (Barycentric TESS Julian Date).** Unidad de tiempo del TESS: días desde una fecha de referencia (BJD − 2 457 000), corregidos al centro de masa del Sistema Solar. Todos los tiempos de PlanetHunter están en BTJD. (B3)

## C

**Cadencia.** Intervalo entre dos medidas seguidas de brillo. El TESS entrega curvas de 20 s y de 2 min para estrellas seleccionadas, e imágenes completas cada 200 s (antes, 10 y 30 min). (B3)

**Candidato.** Señal que sobrevivió al vetting y merece atención, pero no es un planeta. En la escalera del curso: señal → candidato → CTOI → TOI → validado → confirmado. (B3)

**CBV (Cotrending Basis Vectors).** Patrones de variación comunes a muchas estrellas del mismo detector, causados por el instrumento. Restarlos elimina sistemáticos compartidos sin borrar la variación propia de cada estrella. (M4)

**Centroide.** Posición media de la luz de una estrella en la imagen, como el "centro de gravedad" del brillo. Si se desplaza durante el tránsito, la caída probablemente viene de una estrella vecina; es la prueba `centroid`. (B4, M5)

**Chi cuadrado (χ²).** Prueba estadística que mide si varias medidas concuerdan con un modelo, teniendo en cuenta los errores. La prueba `consistency` usa esta idea para ver si todos los tránsitos tienen la misma profundidad. (M1)

**Clase del crossmatch.** Resultado de la pregunta "¿ya existe?": `KNOWN_PLANET` (planeta confirmado), `KNOWN_TOI` y `KNOWN_CTOI` (ya es candidato del TESS), `KNOWN_PUBLISHED` (en una lista publicada de candidatos, como los KOIs de Kepler o DIAmante), `KNOWN_FP` (falso positivo o binaria catalogada), `NEARBY_KNOWN` (vecino conocido con el mismo período), `NEW` (nada coincidió) y `UNVERIFIED` (sería nuevo, pero algún catálogo falta o está desactualizado). (B3, B5)

**Completitud.** Fracción de los planetas reales, de cierto tamaño y período, que el sistema logra encontrar. Se mide con injection-recovery. (A5)

**Contaminación.** Luz de otras estrellas mezclada con la del objetivo en la misma medida, consecuencia del píxel grande del TESS. Una señal "del objetivo" puede venir de una estrella contaminante. (B3, B4)

**Corrida nula.** Búsqueda en curvas de luz puestas de cabeza (invertidas) o con cada órbita desplazada en el tiempo (barajadas). Todo "tránsito" encontrado en ellas es falso por construcción, así que contarlos mide la tasa de falsas alarmas. Kepler usó este método (Thompson et al. 2018); en PlanetHunter es `planethunter search --null inverted` o `--null scrambled`. (A1, A2)

**Crossmatch.** Comparación de cada señal con los catálogos de objetos conocidos, para saber si ya fue registrada. PlanetHunter hace la coincidencia por estrella (número TIC o posición hasta 21″) y por señal (período con aliases y tránsito a tránsito). (B3, B4)

**CROWDSAP.** Número entre 0 y 1, calculado por el pipeline SPOC, que estima la fracción de la luz en la apertura que viene del propio objetivo. Valores muy por debajo de 1 indican mucha contaminación. Aparece en la sección Parameters del dossier. (B5, M4)

**CTOI (Community TOI).** Candidato enviado al ExoFOP por alguien de fuera del equipo del TESS. Puede ser promovido a TOI. Es el destino de un buen candidato de PlanetHunter. (B3, A6)

**Curva de luz.** Gráfico del brillo de una estrella a lo largo del tiempo. Es el dato bruto de toda la búsqueda de tránsitos. (B2)

## D

**Densidad estelar.** Masa de la estrella dividida por su volumen. Junto con el período, determina cuánto debería durar un tránsito; un tránsito demasiado largo o demasiado corto para la estrella sugiere que la señal viene de otra estrella. Es la base de la prueba `duration`. (M2)

**Desviación estándar (σ).** Medida de cuánto se dispersan los valores alrededor de la media. En curvas de luz, la desviación estándar de los puntos fuera del tránsito es el ruido. (M1)

**Detrending.** Eliminación de la variación lenta del brillo (rotación, manchas, efectos del instrumento) para dejar visibles los tránsitos. Si la ventana del filtro es demasiado corta, se "come" el tránsito: con 0,5 día, un tránsito de 5 h pierde el 40 % de la profundidad; con 1 día, el 6 %. (B4, M4, A1)

**Disposición del TFOPWG.** Situación de un TOI registrada por el grupo de seguimiento: PC (candidato a planeta), APC (candidato ambiguo), CP (planeta confirmado), KP (planeta ya conocido), FP (falso positivo), FA (falsa alarma). (B3)

**Dossier.** Informe HTML que PlanetHunter genera para una señal, con parámetros, gráficos, tabla de vetting, crossmatch y proveniencia. Se guarda en `data/dossiers/`. (B5)

**Duotránsito.** Señal con solo dos tránsitos separados por un intervalo largo (por ejemplo, en sectores observados con años de diferencia). El período queda ambiguo entre varios aliases. (A1)

**Duración (T14).** Tiempo desde el inicio hasta el fin de un tránsito, en horas. Depende del período, del tamaño y la densidad de la estrella y del parámetro de impacto. (B2, M2)

## E

**Eclipse secundario.** Segunda caída de brillo de una binaria, cuando la compañera pasa por detrás de la estrella principal; en una órbita circular, ocurre en la fase 0,5. La prueba `secondary` solo veta si es al menos el 10 % del principal. Si el "secundario" es tan profundo y tan largo como la caída principal, es simplemente otro tránsito: la señal se encontró al doble del período verdadero, y PlanetHunter la prueba de nuevo con la mitad del período (`period_halved`). (B4, M5)

**Eclíptica.** Plano en el que la Tierra y los demás planetas orbitan alrededor del Sol. Los sectores del TESS se organizan alrededor de los polos de la eclíptica. (B3)

**Efecto Doppler.** Cambio en el color (longitud de onda) de la luz de una fuente que se acerca o se aleja, como el tono de la sirena de una ambulancia. Es la base del método de velocidad radial. (B1)

**Efeméride.** Predicción de cuándo ocurrirán los próximos tránsitos: un período y un instante de tránsito ($T_0$). (B2)

**Enana roja.** Estrella de tipo espectral M: pequeña (0,1 a 0,6 R☉), fría y poco brillante. Es el tipo de estrella más común de la galaxia y el mejor para encontrar planetas pequeños por tránsito. (B1, B2)

**Espejo (de catálogo).** Copia local de un catálogo de objetos conocidos. PlanetHunter mantiene 12 espejos: el NASA Exoplanet Archive, los TOIs, los CTOIs, exoplanet.eu, los KOIs de Kepler, K2, dos catálogos de binarias del TESS y cuatro listas publicadas de candidatos. Cada uno tiene su propio límite de frescura: 48 h para los TOIs, los CTOIs y el Archive, 7 días para exoplanet.eu y K2, 30 días para los KOIs; las tablas publicadas fijas nunca vencen. Si algún espejo falta o es demasiado antiguo, ninguna señal puede clasificarse como nueva. (B3, B5)

**ExoFOP.** Portal de seguimiento de exoplanetas (exofop.ipac.caltech.edu), con páginas de cada estrella, listas de TOIs y CTOIs, notas de la comunidad y envío de CTOIs. (B3, A6)

**ExoMiner.** Red neuronal de la NASA para clasificar señales de tránsito, descrita por Valizadegan y colaboradores en 2022. (A4)

**Exoplaneta.** Planeta que orbita una estrella distinta del Sol. En 2026 se conocen cerca de 6 400 confirmados. (B1)

**exoplanet.eu.** Catálogo europeo de exoplanetas, más inclusivo que el de la NASA (cerca de 8 300 objetos). Es uno de los espejos de PlanetHunter. (B3)

## F

**Falla dura.** Falla del vetting lo bastante seria como para reprobar la señal por sí sola, sin poner el score en cero: `shape`, `secondary_scan`, `tpf_difference_image` y `fpp_triceratops`. Compara con **falla leve** y **veto**. (M5)

**Falla leve.** Falla del vetting que, por sí sola, solo baja el score. Se tolera una falla leve; dos o más reprueban la señal. (M5)

**Falsa alarma (FA).** Señal que no tiene origen astrofísico: ruido o defecto instrumental. (B3, B4)

**Falso positivo (FP).** Señal real, astrofísica, que parece un planeta pero no lo es: binaria eclipsante, binaria de fondo, contaminación. En uso general, cualquier señal que parece un planeta y no lo es. (B4)

**Fase.** Posición dentro de una órbita, de 0 a 1. El tránsito está en la fase 0; el punto medio entre dos tránsitos, en la fase 0,5. (B4)

**FFI (Full-Frame Image).** Imagen completa de una cámara del TESS, con todas las estrellas del campo. Cadencia actual de 200 s. Permite estudiar estrellas fuera de la lista de 2 minutos. (B3)

**Flare (fulguración).** Explosión en la superficie de una estrella que produce un pico rápido de brillo hacia arriba. PlanetHunter recorta los picos hacia arriba, pero nunca hacia abajo. (B4)

**Forma en U y en V.** Un tránsito de planeta tiene el fondo casi plano (U); un eclipse rasante de binaria es puntiagudo (V). Los planetas rasantes también producen V. Aun así, la prueba `shape` es una falla dura: una forma de V reprueba la señal por sí sola, a costa de unos pocos planetas rasantes reales. (B4, M5)

**FPP (False Positive Probability).** Probabilidad, calculada por un modelo estadístico, de que la señal sea un falso positivo. Por debajo de 0,5, candidato plausible; por debajo de 0,015 (con NFPP por debajo de 0,001 e imagen de alta resolución), nivel usado para validar un planeta. PlanetHunter la calcula con triceratops, y la prueba falla si FPP ≥ 0,5 o NFPP > 0,1. (A3)

**Fusión nuclear.** Unión de núcleos ligeros (hidrógeno) en otros más pesados (helio), con liberación de energía. Es lo que hace brillar a las estrellas. (B1)

## G

**Gaia.** Misión espacial europea que midió la posición, la distancia y el brillo de más de mil millones de estrellas. PlanetHunter usa el catálogo Gaia DR3 para listar estrellas vecinas y binarias eclipsantes conocidas. (A2)

**Gigante.** Estrella que agotó el hidrógeno del centro y se hinchó hasta decenas o cientos de R☉. Esconde planetas pequeños, porque la profundidad cae con el cuadrado del radio de la estrella. (B1)

**GP (proceso gaussiano).** Modelo estadístico flexible que describe variaciones correlacionadas en el tiempo. Es una alternativa al biweight para el detrending de estrellas muy variables. (A1)

## I

**IC 95 % (intervalo de confianza).** Rango de valores compatibles con una medida, dada la cantidad de datos. El recall de 91,1 % de PlanetHunter, medido con 135 objetos, tiene un IC 95 % de 85,1 % a 94,8 % (intervalo de Wilson). (A5)

**Imagen de diferencia.** Resta entre la imagen fuera del tránsito y la imagen durante el tránsito. Lo que "se apagó" aparece en la diferencia y muestra de dónde vino la caída. Prueba `tpf_difference_image`. (B4, A2)

**Imagen directa.** Método de detección que fotografía el propio planeta, bloqueando la luz de la estrella. Solo funciona para planetas gigantes, jóvenes y alejados de la estrella. (B1)

**Impar/par (odd-even).** Comparación entre la profundidad de los tránsitos impares y la de los pares. Si difieren, probablemente es una binaria con el doble del período encontrado. Prueba `odd_even`. (B4)

**Ingesta.** Etapa que descarga las curvas de luz del MAST y las guarda en Parquet. Comando `planethunter ingest`. (B3)

**Injection-recovery.** Técnica que inyecta tránsitos sintéticos en curvas reales, ejecuta el pipeline y cuenta cuántos recupera. Así se mide la completitud. (A5)

## J

**Júpiter caliente.** Planeta gigante gaseoso en una órbita de pocos días, muy cerca de la estrella. Fueron los primeros exoplanetas encontrados alrededor de estrellas tipo Sol (51 Pegasi b, 1995). (B1)

## K

**Kepler (ley).** La tercera ley de Kepler relaciona el período y el tamaño de la órbita: para una estrella de 1 M☉, $a^3 = P^2$ con $a$ en UA y $P$ en años. (B2, M2)

**Kepler (telescopio).** Telescopio espacial de la NASA que observó una región del cielo de 2009 a 2018 y mostró que los planetas son comunes. Antecesor del TESS. (B1, B3)

## L

**Lightkurve.** Biblioteca de Python para descargar, limpiar y analizar curvas de luz de Kepler y del TESS. Base de la ruta de programación. (M4, P3)

**Luz dispersa.** Luz de la Tierra y de la Luna que entra en las cámaras del TESS en ciertas partes de la órbita y cambia el fondo de las imágenes. Uno de los sistemáticos que imitan tránsitos. (B4)

## M

**M☉ (masa solar).** Masa del Sol, cerca de 2 × 10³⁰ kg, usada como unidad para estrellas. (B1)

**Magnitud.** Escala de brillo invertida: número menor, objeto más brillante. Cinco magnitudes corresponden a un factor de 100 en brillo. Ver **Tmag**. (B3)

**MAST (Mikulski Archive for Space Telescopes).** Archivo público de la NASA donde están los datos del TESS. (B3)

**Mediana.** Valor del medio cuando los datos están ordenados. Menos sensible a los valores extremos que la media. (M1)

**Microlente gravitacional.** Método de detección en el que la gravedad de una estrella en primer plano amplifica la luz de otra al fondo; un planeta causa una desviación breve. El evento no se repite. (B1)

**Mini-Neptuno.** Planeta de entre unos 2 y 4 R⊕, con atmósfera espesa. No existe en el Sistema Solar, pero es muy común en la galaxia. (B1)

**Momentum dump.** Encendido de pequeños propulsores del TESS para descargar la rotación acumulada en las ruedas de reacción. El apuntado tiembla y el brillo salta; en el dossier aparecen como líneas azules punteadas. (B4)

**Monotránsito.** Señal con un único tránsito observado; el período queda desconocido. PlanetHunter veta las señales con menos de 2 tránsitos; los monotránsitos exigen un detector propio, previsto en el plan. (B4, A1)

**Multisector.** Análisis que junta los datos de varios sectores de la misma estrella. Aumenta el número de tránsitos y permite verificar si una señal se repite. (B3, M5)

## N

**NFPP (Nearby False Positive Probability).** Probabilidad de que la señal venga de una estrella vecina conocida, y no del objetivo. Para validar un planeta, la literatura usa NFPP por debajo de 0,001; por encima de 0,1, la señal es un probable falso positivo de una vecina y la prueba de FPP de PlanetHunter falla. (A3)

**Normal (distribución).** Distribución en forma de campana que describe bien el ruido aleatorio de muchas medidas. Cerca del 99,7 % de los valores quedan a menos de 3σ de la media. (M1)

## O

**Ocultación.** Paso del planeta **por detrás** de la estrella. En planetas muy calientes, como WASP-18 b, la luz del planeta desaparece y aparece una caída pequeña en la fase 0,5. (B4, M2)

**Oscurecimiento del limbo.** El borde del disco de una estrella se ve más oscuro que el centro, porque ahí vemos capas más altas y más frías. Esto redondea el fondo del tránsito. (B2, M2)

## P

**P0, P1, P2 (severidad).** Prioridad de un candidato nuevo en PlanetHunter. P1: pasó el vetting, score ≥ 0,8 **y**, cuando existe el modelo, `p_rank` igual o mayor que el umbral de P1 del modelo. P0: todo lo que exige P1, más vetting profundo completo (imagen de diferencia y vecinos Gaia aprobados, FPP calculado) con FPP < 0,1, NFPP < 0,001, un planeta menor que 8 R⊕, SNR ≥ 15 y datos de 2 minutos. P2: pasó el vetting pero quedó por debajo de los umbrales de P1; o falló el vetting sin veto, pero lo rescató un `p_rank` igual o mayor que el umbral de P2 del modelo; o quedó limitado por un aviso (la estrella es una binaria catalogada o no tiene radio conocido, NFPP > 0,1, la señal es la fuente de una señal compartida con una vecina, o sus tránsitos coinciden en parte con un objeto conocido). Sin severidad: un veto, tránsitos en picos de época, o una señal que pertenece a una vecina. El modelo solo baja la prioridad, nunca la sube. (B5, A3, A4)

**p_planet, p_rank y p_abs.** `p_rank` (guardada en la columna `p_planet`) es la probabilidad de que una señal sea un planeta, aprendida con `planethunter calibrate` a partir de señales conocidas: planetas confirmados frente a falsos positivos catalogados y las falsas alarmas de las corridas nulas. La severidad la usa solo para bajar la prioridad, mediante dos umbrales elegidos midiendo cuántos planetas conocidos conservan. `p_abs` es la misma probabilidad corregida por lo raros que son los planetas entre las señales nuevas; esa corrección se apoya en una suposición (5 %), así que `p_abs` es solo para leer. (A4)

**Parámetro de impacto (b).** Distancia de la trayectoria del planeta al centro del disco de la estrella, en unidades del radio de la estrella: 0 es central, cerca de 1 es rasante. Los tránsitos con $b$ alto son más cortos y en V. (B2, M2)

**Parquet.** Formato de archivo compacto para tablas, que PlanetHunter usa para guardar curvas de luz en `data/parquet/`. La base de datos DuckDB (`data/planethunter.duckdb`) guarda señales, vetting y candidatos. (B3, P2)

**Parsec (pc).** Unidad de distancia usada por los astrónomos, igual a 3,26 años luz. (B1)

**PDCSAP y SAP.** Dos tipos de flujo en las curvas del pipeline SPOC. SAP es la suma simple de la luz en una apertura; PDCSAP es el SAP corregido de sistemáticos y de contaminación. (M4)

**Período (P).** Tiempo entre dos tránsitos seguidos, en días. (B2)

**Periodograma.** Gráfico que prueba miles de períodos y muestra cuánto "encaja" cada uno en los datos. Un pico destacado indica una señal periódica. (M3)

**Pico de época.** Momento en el que muchas más estrellas sin relación entre sí muestran un "tránsito" de lo que el azar permite. La causa es el telescopio, no las estrellas. PlanetHunter los busca en cada corrida; una señal con la mitad o más de sus tránsitos en picos de época nunca genera alerta. (A2)

**Píxel del TESS.** Cada píxel cubre 21″ × 21″ del cielo. Es grande: caben varias estrellas, lo que causa contaminación. (B3)

**Planeta confirmado.** Planeta con evidencia independiente del tránsito, en general masa medida por velocidad radial. Último peldaño de la escalera. (B3)

**Planeta validado.** Planeta cuya probabilidad de falso positivo se mostró muy pequeña, mediante un análisis estadístico apoyado en imágenes de alta resolución, sin masa medida. (B3, A3)

**Planet Hunters TESS.** Proyecto de ciencia ciudadana en Zooniverse en el que voluntarios marcan tránsitos en curvas de luz reales del TESS. (B5)

**Plegar (phase-fold).** Superponer todos los tránsitos alineándolos según el período, como apilar hojas transparentes. El ruido aleatorio se cancela en parte y el tránsito se suma. Gráfico "Folded transit" (tránsito plegado) del dossier. (B2, B5)

**ppm (partes por millón).** Unidad de profundidad de tránsito. 10 000 ppm = 1 %. (B2)

**Profundidad (δ).** Cuánto cae el brillo en el tránsito, en ppm. Aproximadamente $(R_p/R_\star)^2$. (B2)

**Proveniencia.** Registro de dónde vino cada resultado: sector, autor de los datos, versión del pipeline y `run_id`. Permite reproducir cualquier análisis. (B5)

## Q

**QLP (Quick Look Pipeline).** Pipeline del MIT que extrae curvas de luz de las imágenes completas (FFI) del TESS, y llega a muchas más estrellas que las curvas de 2 minutos. (B3)

## R

**R⊕ (radio terrestre).** Radio de la Tierra, 6 371 km, usado como unidad para planetas. Júpiter tiene cerca de 11 R⊕. (B1)

**R☉ (radio solar).** Radio del Sol, 696 000 km (cerca de 109 R⊕), usado como unidad para estrellas. (B1)

**Razón de radios (Rp/R*).** Radio del planeta dividido por el radio de la estrella. La profundidad es aproximadamente su cuadrado. (B2)

**Recall.** Fracción de objetos conocidos que el sistema recupera. En el sector 69, PlanetHunter recupera 123 de 135 TOIs detectables: 91,1 %. (A5)

**Robovetter.** Sistema automático de vetting de Kepler (catálogo DR25), descrito por Thompson y colaboradores en 2018. Referencia para comparar con el vetting de PlanetHunter. (A2)

**Ruido.** Fluctuaciones en las medidas que no vienen de la señal buscada. Esconde los tránsitos poco profundos. (B2, M1)

**Ruido blanco.** Ruido aleatorio e independiente de una medida a otra; disminuye con la raíz del número de puntos cuando se promedia. (M1)

**Ruido rojo.** Ruido correlacionado en el tiempo (vecinos parecidos entre sí), que no desaparece al promediar. Por eso PlanetHunter estima los errores por bloques de datos, como en Pont, Zucker y Queloz (2006). (M1)

**run_id.** Código único de cada ejecución de PlanetHunter, que imprimen los comandos y que se usa en `vet`, `candidates` y en el dossier. (B5)

## S

**Score de vetting.** Nota de 0 a 1 del vetting. Empieza en 1,0; cada prueba que falla lo multiplica por un peso (0,3 a 0,6) y cada prueba sin datos, por 0,95; un veto lo pone en cero. No decide si aprueba o reprueba (ver **veredicto**): ordena las señales, y P0 y P1 exigen un score de al menos 0,8. Es un ordenamiento útil, no una probabilidad (para una probabilidad, ver **p_planet, p_rank y p_abs**). (B4, M5)

**SDE (Signal Detection Efficiency).** Cuánto se destaca el pico más alto del periodograma respecto del resto, en unidades de desviación estándar. PlanetHunter exige SDE ≥ 9, lo que corresponde a una probabilidad de falsa alarma de cerca de 1 en 10 000 según Hippke y Heller (2019). (M3)

**Sector.** Bloque de cerca de 27 días en el que el TESS observa la misma franja de 24° × 96° del cielo. (B3)

**Secuencia principal.** Fase estable de la vida de una estrella, en la que quema hidrógeno en el centro. El Sol está en ella. (B1)

**Segundo de arco (″).** Unidad de ángulo: 1/3 600 de grado. La Luna llena mide cerca de 1 800″; un píxel del TESS, 21″. (B3)

**Señal.** Caída de brillo periódica encontrada por la búsqueda. Primer peldaño de la escalera: todavía no pasó por ninguna prueba. (B3)

**Señal compartida.** El mismo período y el mismo instante de tránsito en dos estrellas a menos de 2′: la luz de una se filtra en los píxeles de la otra. La estrella que realmente puede producir la caída es la `source` (como máximo P2); la otra es la `victim` (sin alerta). Dos entradas del TIC a menos de 2″ una de otra son un `duplicate` de la misma estrella (sin alerta). (A2)

**Sigma (σ).** Símbolo de la desviación estándar. "3σ" quiere decir tres desviaciones estándar por encima o por debajo de la media: improbable por azar, pero no imposible cuando se hacen muchos intentos. (M1)

**SIMBAD.** Base de datos astronómica (Estrasburgo, Francia) que dice qué tipo de objeto es cada estrella conocida. La prueba `simbad_type` la consulta. (A2)

**Sistemático.** Variación causada por el instrumento o por el procesamiento, no por la estrella. Ejemplos: momentum dumps, bordes de órbita, luz dispersa. (B4)

**S/N_pink.** Relación señal-ruido que también tiene en cuenta el ruido rojo, medida en la escala de tiempo del tránsito (Pont, Zucker y Queloz, 2006). El pipeline de vista rápida del TESS (QLP) exige al menos 9; en PlanetHunter, quedar por debajo de 9 es una falla leve. (M1, M5)

**SNR (relación señal-ruido).** Tamaño del tránsito comparado con el ruido, considerando cuántas medidas hay dentro de los tránsitos. PlanetHunter exige SNR ≥ 7,1. (B2, M1)

**SPOC (Science Processing Operations Center).** Pipeline oficial de la NASA que produce las curvas de luz de 2 minutos y de 20 segundos del TESS. Es el "author" que más usa PlanetHunter. (B3)

**Supertierra.** Planeta rocoso más grande que la Tierra, de unos 1 a 2 R⊕. (B1)

## T

**T0.** Instante de la mitad de un tránsito de referencia, en BTJD. Junto con el período, forma la efeméride. (B2)

**T14.** Ver **duración**.

**Teff.** Temperatura efectiva, o temperatura de la superficie de la estrella, en kelvin. El Sol tiene 5 772 K. (B1)

**TESS (Transiting Exoplanet Survey Satellite).** Telescopio espacial de la NASA lanzado en 2018 que observa casi todo el cielo en busca de tránsitos. Fuente de los datos de PlanetHunter. (B3)

**TFOP y TFOPWG.** TFOP es el programa de observaciones de seguimiento de los TOIs con otros telescopios. TFOPWG es el grupo de trabajo que registra la disposición de cada TOI. (B3, A6)

**Threshold (umbral).** Valor de corte de una prueba, como SNR ≥ 7,1. En PlanetHunter, todos viven en `config/thresholds.yaml`, versionados y comentados. (B4, A5)

**TIC (TESS Input Catalog).** Catálogo con más de 1700 millones de objetos; cada estrella tiene un número, como TIC 261136679 (Pi Mensae). También trae radio, masa y temperatura estimados. (B3)

**Tipo espectral.** Clasificación de las estrellas por temperatura: O, B, A, F, G, K, M, de la más caliente a la más fría. El Sol es G2. (B1)

**TLS (Transit Least Squares).** Algoritmo de búsqueda de tránsitos que, en lugar de una caja, usa un modelo realista de tránsito. Publicado por Hippke y Heller en 2019; es el que usa PlanetHunter. (M3, A1)

**Tmag.** Brillo de la estrella en la escala de magnitudes del TESS. Número menor, estrella más brillante: 6 es muy brillante, 13 es débil. (B3)

**TOI (TESS Object of Interest).** Candidato oficial anunciado por el equipo del TESS, con un número como TOI-144.01. Todavía puede ser un falso positivo. (B3)

**TPF (Target Pixel File).** Archivo con los píxeles alrededor de una estrella, en cada instante. Permite hacer imágenes de diferencia y medir centroides. (A2)

**Tránsito.** Paso de un planeta (u otro cuerpo) por delante de una estrella, desde nuestro punto de vista, que causa una caída de brillo. (B1, B2)

**Tránsito rasante.** Tránsito en el que el planeta solo roza el borde de la estrella ($b$ cerca de 1). Es corto y en V, y por eso puede confundirse con una binaria. (B2, B4)

**Triceratops.** Programa que calcula FPP y NFPP considerando la estrella, los vecinos de Gaia y la forma del tránsito. Descrito por Giacalone y colaboradores en 2021. (A3)

## U

**UA (unidad astronómica).** Distancia media entre la Tierra y el Sol, cerca de 150 millones de km. Se usa para el tamaño de las órbitas. (B1, B2)

## V

**Variabilidad estelar.** Cambios de brillo de la propia estrella: manchas y rotación, pulsaciones, flares. El detrending la elimina en parte. (B4)

**Velocidad radial.** Método de detección que mide el vaivén de la estrella causado por el planeta, mediante el efecto Doppler. Da la masa del planeta y es el principal método de confirmación. (B1)

**Veredicto.** Resultado del vetting: `FAIL` con cualquier veto, cualquier falla dura o más de una falla leve; en otro caso, `PASS_BASIC`. (M5)

**Veto.** Falla grave en una prueba del vetting que elimina la señal de inmediato y pone el score en cero. Las demás fallas son fallas duras o fallas leves. (B4, M5)

**Vetting.** Batería de pruebas para descartar falsos positivos. En PlanetHunter hay un vetting básico (sin internet, con pruebas como `odd_even`, `secondary`, `shape`, `centroid`) y uno profundo (con internet: imagen de diferencia, vecinos de Gaia, otros sectores, FPP). (B4, M5)

## W

**wotan.** Biblioteca de Python de detrending, de Hippke y colaboradores, que PlanetHunter usa con el filtro biweight. (M4, A1)

## Z

**Zona de visión continua (CVZ).** Regiones a hasta unos 12° de los polos de la eclíptica, que el TESS observa en todos los sectores de un año. Las estrellas que están en ellas tienen muchos sectores de datos: en el sector 69, de 10 a 22. (B3)

**Zooniverse.** Plataforma de ciencia ciudadana que aloja Planet Hunters TESS y muchos otros proyectos. (B5)
