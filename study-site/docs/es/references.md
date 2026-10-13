# Referencias

Bibliografía completa del curso, organizada por nivel y por tema. Cada elemento trae una frase que dice por qué vale la pena. En los artículos, la cita incluye autores, año, revista y volumen; con eso encuentras cualquiera de ellos en el ADS (ui.adsabs.harvard.edu) y, casi siempre, una versión gratuita en arXiv (arxiv.org).

!!! tip "Cómo leer los artículos de esta lista"
    La primera vez, lee el resumen, las figuras y la conclusión. Vuelve a las ecuaciones cuando las necesites. El método está explicado en el [índice del nivel avanzado](advanced/index.md#como-leer-un-articulo-cientifico).

## Libros

- Tasker, E. (2017). *The Planet Factory*. Bloomsbury. Divulgación de alto nivel sobre la formación y la diversidad de los planetas; el mejor punto de partida del nivel básico.
- Seager, S. (ed.) (2010). *Exoplanets*. University of Arizona Press. Libro de referencia del nivel avanzado, con capítulos escritos por los especialistas de cada técnica.
- Haswell, C. A. (2010). *Transiting Exoplanets*. Cambridge University Press. Libro de texto dedicado al método de tránsito, con ejercicios; puente entre el nivel intermedio y el avanzado.
- Perryman, M. (2018). *The Exoplanet Handbook*, 2ª ed. Cambridge University Press. Enciclopedia del área, para consultar cuando un artículo cite algo que no conoces.
- Sivia, D. S. (2006). *Data Analysis: A Bayesian Tutorial*, 2ª ed. Oxford University Press. Introducción corta y clara al razonamiento bayesiano que se usa en la lección A3.
- Ivezić, Ž., Connolly, A. J., VanderPlas, J. T. & Gray, A. *Statistics, Data Mining, and Machine Learning in Astronomy*. Princeton University Press. Estadística y aprendizaje automático con ejemplos astronómicos y código en Python.
- VanderPlas, J. (2016). *Python Data Science Handbook*. O'Reilly. NumPy, pandas, Matplotlib y scikit-learn en un solo libro; hay una versión gratuita en línea.

## Nivel básico

### El cielo, los planetas y el método de tránsito

- NASA, sitio de exoplanetas (science.nasa.gov/exoplanets). Secciones de introducción y "how we find"; explicaciones visuales de los métodos de detección.
- Página de la misión TESS en el sitio de la NASA y guía del TESS en el HEASARC (heasarc.gsfc.nasa.gov/docs/tess). Qué observa el TESS, sectores, cámaras y cadencias.
- Guía para principiantes de PlanetHunter, en `docs/BEGINNERS_GUIDE.md` en el repositorio del proyecto. Explica la herramienta paso a paso, con glosario y tres historias reales.
- Plan de estudios de PlanetHunter, en `docs/STUDY_PLAN.md`. La estructura que sigue este curso, con checklists por módulo.

### Práctica

- Planet Hunters TESS (zooniverse.org). Clasificar curvas de luz reales es el mejor entrenamiento para el ojo que existe, y voluntarios del proyecto ya han tenido candidatos promovidos.

## Nivel intermedio

### Estadística para señales

- Khan Academy en portugués (pt.khanacademy.org), ruta de estadística; también existe en español (es.khanacademy.org). Estadística descriptiva y distribución normal, base del SNR y de "sigma".
- Pont, F., Zucker, S. & Queloz, D. (2006). *Monthly Notices of the RAS* 373, 231. El artículo que mostró el efecto del ruido rojo en los tránsitos; base del error por bloques (`BlockNoise`) que se usa en el vetting.
- Hogg, D. W., Bovy, J. & Lang, D. (2010). "Data analysis recipes: Fitting a model to data", arXiv:1008.4686. Guía práctica y con opiniones propias sobre cómo ajustar modelos con honestidad estadística.

### Física del tránsito

- Winn, J. N. (2010). "Transits and Occultations", arXiv:1001.2010. El texto clásico sobre geometría, duración, forma y eclipse secundario; las secciones 1 a 3 cubren el nivel intermedio.
- Seager, S. & Mallén-Ornelas, G. (2003). *The Astrophysical Journal* 585, 1038. Relaciones analíticas entre la forma del tránsito, la densidad estelar y el período; base de la prueba `duration`.
- Mandel, K. & Agol, E. (2002). *The Astrophysical Journal* 580, L171. El modelo analítico de tránsito con oscurecimiento del limbo que usa casi todo el software del área.

### Periodogramas

- Documentación de Astropy sobre Box Least Squares (docs.astropy.org, sección timeseries). Ejemplo práctico de BLS en Python.
- Hippke, M. & Heller, R. (2019). *Astronomy & Astrophysics* 623, A39. El TLS que usa PlanetHunter; en el nivel intermedio, la introducción y las figuras.
- VanderPlas, J. T. (2018). *The Astrophysical Journal Supplement Series* 236, 16. Explicación didáctica de periodogramas y aliases (en este caso, Lomb-Scargle), útil para entender los picos falsos.

### Python y datos del TESS

- *Curso em Vídeo — Python*, de Gustavo Guanabara, mundos 1, 2 y 3. Curso gratuito en portugués, desde cero hasta el nivel intermedio.
- Documentación introductoria de NumPy (numpy.org) y de pandas (pandas.pydata.org), secciones "getting started". Arrays y tablas, la base de todo el código del proyecto.
- Tutoriales de Lightkurve (lightkurve.github.io). Descargar, limpiar, aplanar y plegar curvas del TESS; el camino para reproducir Pi Men c.

### Cursos complementarios

- *Super-Earths and Life* (Harvard, plataforma edX). Módulos accesibles sobre detección y caracterización de exoplanetas.
- *Astrobiology and the Search for Extraterrestrial Life* (Universidad de Edimburgo, Coursera). Contexto científico más amplio, también accesible.

## Nivel avanzado

### Cómo leer artículos

- Keshav, S. (2007). "How to Read a Paper", *ACM SIGCOMM Computer Communication Review* 37. El método de las tres pasadas, adaptado en el índice del nivel avanzado.

### A1. Algoritmos de detección

- Kovács, G., Zucker, S. & Mazeh, T. (2002). *Astronomy & Astrophysics* 391, 369. El artículo original del BLS; contiene toda la estadística de la lección A1.
- Hippke, M. & Heller, R. (2019). *Astronomy & Astrophysics* 623, A39. El TLS completo, con ecuaciones y comparación con el BLS.
- Ofir, A. (2014). *Astronomy & Astrophysics* 561, A138. Muestreo óptimo de la grilla de períodos, que usa el TLS.
- Hippke, M. et al. (2019). *The Astronomical Journal* 158, 143. wotan y la comparación de métodos de detrending que justifica el biweight con una ventana de cerca de tres duraciones.
- Foreman-Mackey, D. et al. (2017). *The Astronomical Journal* 154, 220. celerite, para procesos gaussianos rápidos en series temporales.
- Aigrain, S. & Foreman-Mackey, D. (2023). *Annual Review of Astronomy and Astrophysics* 61, 329. Revisión sobre procesos gaussianos en series temporales astronómicas; lectura exigente para quien quiera probar GP en el proyecto.
- Kipping, D. M. (2010). *Monthly Notices of the RAS* 408, 1758. Los efectos de integrar y agrupar puntos en la forma del tránsito; ayuda a pensar el `bin_minutes`.
- Osborn, H. P. et al. (2016). *Monthly Notices of the RAS* 457, 2273. Tránsitos únicos en K2 y estimación del período a partir de un solo evento.

### A2. Vetting de las misiones

- Jenkins, J. M. et al. (2010). *The Astrophysical Journal Letters* 713, L87. Visión general del pipeline científico de Kepler, antecesor del SPOC.
- Twicken, J. D. et al. (2018). *Publications of the Astronomical Society of the Pacific* 130, 064502. El Data Validation: imagen de diferencia, centroides y los demás diagnósticos.
- Coughlin, J. L. et al. (2016). *The Astrophysical Journal Supplement Series* 224, 12. El catálogo DR24 de Kepler y la primera versión del Robovetter.
- Thompson, S. E. et al. (2018). *The Astrophysical Journal Supplement Series* 235, 38. El DR25 y el Robovetter, con la confiabilidad medida mediante curvas invertidas y barajadas.
- Guerrero, N. M. et al. (2021). *The Astrophysical Journal Supplement Series* 254, 39. El catálogo de TOIs de la misión principal y el proceso de vetting del equipo del TESS.
- Prša, A. et al. (2022). *The Astrophysical Journal Supplement Series* 258, 16. El catálogo de binarias eclipsantes del TESS, que el proyecto replica como espejo (y que contiene hot Jupiters).
- Bryson, S. T. et al. (2013). *Publications of the Astronomical Society of the Pacific* 125, 889. Identificación de falsos positivos de fondo con imágenes de diferencia.
- Coughlin, J. L. et al. (2014). *The Astronomical Journal* 147, 119. Coincidencia de efemérides en el campo de Kepler; base conceptual de `NEARBY_KNOWN`.

### A3. Probabilidad de falso positivo

- Morton, T. D. (2012). *The Astrophysical Journal* 761, 6. El método de validación estadística implementado en vespa.
- Morton, T. D. & Johnson, J. A. (2011). *The Astrophysical Journal* 738, 170. Estimación de la tasa de falsos positivos esperada entre los candidatos de Kepler.
- Morton, T. D. et al. (2016). *The Astrophysical Journal* 822, 86. Validación masiva de planetas de Kepler; muestra lo que significa "validado".
- Giacalone, S. et al. (2021). *The Astronomical Journal* 161, 24. triceratops, que usa PlanetHunter; escenarios, FPP, NFPP y umbrales.
- Torres, G. et al. (2011). *The Astrophysical Journal* 727, 24. BLENDER y la validación de Kepler-9 d; otra escuela de validación estadística.
- Fressin, F. et al. (2013). *The Astrophysical Journal* 766, 81. Tasa de falsos positivos de Kepler por tipo de escenario; ayuda a calibrar la intuición sobre los priors.
- Lissauer, J. J. et al. (2012). *The Astrophysical Journal* 750, 112. Por qué los candidatos en sistemas múltiples casi siempre son planetas.
- Raghavan, D. et al. (2010). *The Astrophysical Journal Supplement Series* 190, 1. Multiplicidad de las estrellas tipo Sol; de ahí viene la idea de que cerca de la mitad de ellas tiene compañera.

### A4. Aprendizaje automático

- Shallue, C. J. & Vanderburg, A. (2018). *The Astronomical Journal* 155, 94. Red neuronal con vistas global y local para señales de Kepler.
- Yu, L. et al. (2019). *The Astronomical Journal* 158, 25. Adaptación de esa red al TESS, con triaje y vetting.
- Valizadegan, H. et al. (2022). *The Astrophysical Journal* 926, 120. ExoMiner y la validación de 301 planetas de Kepler.
- Armstrong, D. J. et al. (2021). *Monthly Notices of the RAS* 504, 5327. Validación de planetas con varios algoritmos de ML y probabilidades calibradas.
- Guo, C. et al. (2017). "On Calibration of Modern Neural Networks", *Proceedings of the 34th International Conference on Machine Learning*. Las redes profundas tienen exceso de confianza; el temperature scaling lo corrige.

### A5. Medir el sistema

- Wilson, E. B. (1927). *Journal of the American Statistical Association* 22, 209. El intervalo de confianza que se usa en todos los informes de benchmark.
- Brown, L. D., Cai, T. T. & DasGupta, A. (2001). *Statistical Science* 16, 101. Por qué el intervalo ingenuo falla y el de Wilson funciona.
- McNemar, Q. (1947). *Psychometrika* 12, 153. La prueba para comparar proporciones medidas en los mismos objetos, base de la comparación antes/después.
- Christiansen, J. L. et al. (2013). *The Astrophysical Journal Supplement Series* 207, 35. Inyección de tránsitos en Kepler para medir la recuperación; modelo del injection-recovery.
- Burke, C. J. et al. (2015). *The Astrophysical Journal* 809, 8. Completitud de Kepler aplicada a las tasas de ocurrencia de planetas.
- Kreidberg, L. (2015). *Publications of the Astronomical Society of the Pacific* 127, 1161. `batman`, que genera los tránsitos sintéticos.

### A6. Del candidato a la comunidad

- Eisner, N. L. et al. (2021). *Monthly Notices of the RAS* 501, 4669. Resultados de Planet Hunters TESS; cómo los voluntarios llegan a CTOIs, muchos de ellos de tránsito único.
- Collins, K. A. et al. (2017). *The Astronomical Journal* 153, 77. AstroImageJ, la herramienta estándar de la fotometría desde tierra del TFOP.
- Evaluación de los CTOIs de la comunidad (Zenodo, registro 5130660). Los 168 TOIs nacidos de CTOIs hasta 2021 y por qué se concentran en estrellas débiles y tránsitos únicos; evidencia para los nichos del proyecto.
- Página del TFOP en el HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html). Estructura del programa de seguimiento y cómo participar.

## Datos, misiones y catálogos (citas obligatorias)

Cualquier trabajo con datos del TESS debe citar las fuentes de abajo, según lo que se haya usado.

- Ricker, G. R. et al. (2015). *Journal of Astronomical Telescopes, Instruments, and Systems* 1, 014003. La misión TESS.
- Jenkins, J. M. et al. (2016). *Proceedings of the SPIE* 9913. El SPOC, que produce las curvas de 2 minutos y los informes DV.
- Huang, C. X. et al. (2020). *Research Notes of the AAS* 4, 204. El QLP, pipeline de las imágenes completas.
- Stassun, K. G. et al. (2019). *The Astronomical Journal* 158, 138. El TESS Input Catalog (TIC v8), fuente de los parámetros estelares.
- Gaia Collaboration, Prusti, T. et al. (2016). *Astronomy & Astrophysics* 595, A1. La misión Gaia.
- Gaia Collaboration, Vallenari, A. et al. (2023). *Astronomy & Astrophysics* 674, A1. Gaia DR3, usado para los vecinos y las binarias de Gaia.
- Akeson, R. L. et al. (2013). *Publications of the Astronomical Society of the Pacific* 125, 989. El NASA Exoplanet Archive (exoplanetarchive.ipac.caltech.edu).
- Schneider, J. et al. (2011). *Astronomy & Astrophysics* 532, A79. La Encyclopaedia of Exoplanetary Systems (exoplanet.eu).
- ExoFOP-TESS (exofop.ipac.caltech.edu/tess). Tablas de TOIs y CTOIs, notas y archivos de seguimiento; cítalo según la página de ayuda del servicio.

## Herramientas

- Lightkurve Collaboration (2018), ascl:1812.013. Lightkurve, para descargar y manipular curvas del TESS.
- Astropy Collaboration (2022). *The Astrophysical Journal* 935, 167. Astropy, base de unidades, tiempo y BLS.
- Ginsburg, A. et al. (2019). *The Astronomical Journal* 157, 98. Astroquery, para consultar MAST, Gaia, VizieR y SIMBAD.
- wotan (Hippke et al. 2019), TLS (Hippke & Heller 2019), batman (Kreidberg 2015), triceratops (Giacalone et al. 2021), vespa (Morton 2012) y celerite (Foreman-Mackey et al. 2017): cita los artículos listados arriba.

## Sitios y comunidades

- ADS (ui.adsabs.harvard.edu). Buscador de la literatura astronómica; usa `object:` y `full:` para buscar objetivos.
- arXiv, sección astro-ph.EP (arxiv.org). Artículos nuevos sobre planetas, antes de su publicación en las revistas.
- ExoFOP-TESS (exofop.ipac.caltech.edu/tess). Páginas de objetivos, notas de la comunidad y envío de CTOI.
- NASA Exoplanet Archive (exoplanetarchive.ipac.caltech.edu). Planetas confirmados y tabla de TOIs con sus disposiciones.
- Planet Hunters TESS en Zooniverse (zooniverse.org). Clasificación de curvas y foro donde voluntarios y profesionales discuten candidatos.
