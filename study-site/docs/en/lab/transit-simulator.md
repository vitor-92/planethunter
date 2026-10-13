# Transit simulator

<p class="meta">Lab · use it alongside lessons B2, M1 and M2</p>

Move the controls and watch, live, how the light curve changes. It is the same physics PlanetHunter uses to look for planets, simplified.

<div id="transit-sim" markdown="0">
  <div class="ts-presets">
    Ready-made examples:
    <button data-preset="terra">Earth around a Sun</button>
    <button data-preset="hotjup">Hot Jupiter</button>
    <button data-preset="anam">Super-Earth around a red dwarf</button>
    <button data-preset="pimen">Pi Men c</button>
  </div>
  <div class="ts-controls">
    <label>Planet radius: <span id="ts-rp-v"></span> R⊕
      <input id="ts-rp" type="range" min="0.5" max="25" step="0.1" value="2.5"></label>
    <label>Star radius: <span id="ts-rs-v"></span> R☉
      <input id="ts-rs" type="range" min="0.1" max="3" step="0.01" value="1"></label>
    <label>Star mass: <span id="ts-ms-v"></span> M☉
      <input id="ts-ms" type="range" min="0.1" max="2" step="0.01" value="1"></label>
    <label>Orbital period: <span id="ts-per-v"></span> days
      <input id="ts-per" type="range" min="0.5" max="30" step="0.1" value="5"></label>
    <label>Impact parameter b: <span id="ts-b-v"></span> (0 = center, 1 = edge)
      <input id="ts-b" type="range" min="0" max="1.2" step="0.01" value="0.3"></label>
    <label>Star brightness (Tmag): <span id="ts-tmag-v"></span> (smaller = brighter)
      <input id="ts-tmag" type="range" min="5" max="15" step="0.1" value="10"></label>
  </div>
  <canvas id="ts-star"></canvas>
  <canvas id="ts-lc"></canvas>
  <canvas id="ts-fold"></canvas>
  <div id="ts-out"></div>
</div>

## What to watch for

1. **Planet radius.** Double the radius and the depth quadruples, because it depends on the **area** of the dark disk: $\delta \approx (R_p/R_\star)^2$.
2. **Star radius.** With the same Earth, swap the Sun for a 0.2 R☉ red dwarf. The dip becomes 25 times deeper. That is why small planets are easier to find around small stars.
3. **Period.** Long periods give fewer transits per sector. Below 2 transits, PlanetHunter does not accept the signal, even if it is strong.
4. **Impact parameter.** Push $b$ close to 1: the transit becomes short and **V**-shaped. This is the shape the `shape` test is suspicious of, because grazing binaries also produce it.
5. **Brightness.** Faint stars (high Tmag) have more noise. Watch the SNR drop and the points spread out.

!!! example "Challenge 1"
    Find the smallest planet PlanetHunter would detect, in one sector, around a Sun-like star with Tmag 9 and a period of 10 days.

    ??? success "Show answer"
        With R☉ = 1, M☉ = 1, P = 10 d, b = 0.3 and Tmag 9, the SNR crosses 7.1 at around 2.2 R⊕ (the exact value varies a little with b).

        The math behind it: the noise per measurement is ~760 ppm; the transit lasts ~3.7 h (~110 two-minute measurements); there are 2 transits in the sector. SNR = depth / noise × √(number of measurements in transit), so the minimum depth is about 7.1 × 760 ppm / √180 ≈ 400 ppm, which gives $R_p \approx \sqrt{0.0004} \times 109 \approx 2.2$ R⊕. Earth-sized planets, under these conditions, stay below the noise in a single sector: they would need several sectors added together.

!!! example "Challenge 2"
    Why does the "chance of transiting" go down as the period goes up?

    ??? success "Show answer"
        The chance is roughly $R_\star/a$. A longer period means a larger orbit ($a$ grows as $P^{2/3}$, by Kepler's third law), so the planet must be more perfectly lined up with us to pass in front of the star.

!!! note "Limitations of the simulator"
    The star's disk is uniform (no limb darkening, the subject of lesson M2), the orbit is circular and the noise is an approximation of 2-minute TESS data calibrated on real stars from sector 69. The numbers are for building intuition, not for research.
