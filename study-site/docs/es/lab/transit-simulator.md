# Simulador de tránsito

<p class="meta">Laboratorio · úsalo junto con las lecciones B2, M1 y M2</p>

Mueve los controles y mira, en vivo, cómo cambia la curva de luz. Es la misma física que PlanetHunter usa para buscar planetas, simplificada.

<div id="transit-sim" markdown="0">
  <div class="ts-presets">
    Ejemplos listos:
    <button data-preset="terra">Tierra en un Sol</button>
    <button data-preset="hotjup">Júpiter caliente</button>
    <button data-preset="anam">Supertierra en una enana roja</button>
    <button data-preset="pimen">Pi Men c</button>
  </div>
  <div class="ts-controls">
    <label>Radio del planeta: <span id="ts-rp-v"></span> R⊕
      <input id="ts-rp" type="range" min="0.5" max="25" step="0.1" value="2.5"></label>
    <label>Radio de la estrella: <span id="ts-rs-v"></span> R☉
      <input id="ts-rs" type="range" min="0.1" max="3" step="0.01" value="1"></label>
    <label>Masa de la estrella: <span id="ts-ms-v"></span> M☉
      <input id="ts-ms" type="range" min="0.1" max="2" step="0.01" value="1"></label>
    <label>Período de la órbita: <span id="ts-per-v"></span> días
      <input id="ts-per" type="range" min="0.5" max="30" step="0.1" value="5"></label>
    <label>Parámetro de impacto b: <span id="ts-b-v"></span> (0 = centro, 1 = borde)
      <input id="ts-b" type="range" min="0" max="1.2" step="0.01" value="0.3"></label>
    <label>Brillo de la estrella (Tmag): <span id="ts-tmag-v"></span> (menor = más brillante)
      <input id="ts-tmag" type="range" min="5" max="15" step="0.1" value="10"></label>
  </div>
  <canvas id="ts-star"></canvas>
  <canvas id="ts-lc"></canvas>
  <canvas id="ts-fold"></canvas>
  <div id="ts-out"></div>
</div>

## Qué observar

1. **Radio del planeta.** Duplica el radio y la profundidad se cuadruplica, porque depende del **área** del disco oscuro: $\delta \approx (R_p/R_\star)^2$.
2. **Radio de la estrella.** Con la misma Tierra, cambia el Sol por una enana roja de 0,2 R☉. La caída se vuelve 25 veces más profunda. Por eso los planetas pequeños son más fáciles de encontrar en estrellas pequeñas.
3. **Período.** Los períodos largos dan menos tránsitos por sector. Por debajo de 2 tránsitos, PlanetHunter no acepta la señal, aunque sea fuerte.
4. **Parámetro de impacto.** Lleva $b$ cerca de 1: el tránsito se vuelve corto y en forma de **V**. Es la forma de la que desconfía la prueba `shape`, porque las binarias rasantes también la producen.
5. **Brillo.** Las estrellas débiles (Tmag alto) tienen más ruido. Mira cómo baja el SNR y cómo se dispersan los puntos.

!!! example "Desafío 1"
    Encuentra el planeta más pequeño que PlanetHunter detectaría, en un sector, alrededor de una estrella como el Sol con Tmag 9 y período de 10 días.

    ??? success "Ver respuesta"
        Con R☉ = 1, M☉ = 1, P = 10 d, b = 0,3 y Tmag 9, el SNR supera 7,1 alrededor de 2,2 R⊕ (el valor exacto varía un poco con b).

        El cálculo detrás: el ruido por medida es ~760 ppm; el tránsito dura ~3,7 h (~110 medidas de 2 min); hay 2 tránsitos en el sector. SNR = profundidad / ruido × √(número de medidas en tránsito), así que la profundidad mínima es cerca de 7,1 × 760 ppm / √180 ≈ 400 ppm, lo que da $R_p \approx \sqrt{0{,}0004} \times 109 \approx 2{,}2$ R⊕. Los planetas del tamaño de la Tierra, en esas condiciones, quedan por debajo del ruido en un solo sector: necesitarían varios sectores sumados.

!!! example "Desafío 2"
    ¿Por qué la "probabilidad de transitar" disminuye cuando aumenta el período?

    ??? success "Ver respuesta"
        La probabilidad es aproximadamente $R_\star/a$. Un período mayor significa una órbita mayor ($a$ crece con $P^{2/3}$, por la tercera ley de Kepler), así que el planeta necesita estar alineado con nosotros de forma más perfecta para pasar por delante de la estrella.

!!! note "Limitaciones del simulador"
    El disco de la estrella es uniforme (sin oscurecimiento del limbo, tema de la lección M2), la órbita es circular y el ruido es una aproximación del TESS de 2 minutos calibrada con estrellas reales del sector 69. Los números sirven para la intuición, no para la investigación.
