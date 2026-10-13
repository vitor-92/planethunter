/* Transit simulator: uniform-disk geometry, approximate TESS 2-min noise.
 * Noise per 2-min point ~ 1200 ppm * 10^(0.2 (Tmag - 10)); matches PlanetHunter data:
 * Tmag 9 -> ~760 ppm (measured 807), Tmag 11.6 -> ~2500 ppm (measured 2412).
 * Texts follow the page language (<html lang>): en, es, pt.
 */
(function () {
  "use strict";

  const G = 6.674e-11, MSUN = 1.98847e30, RSUN = 6.957e8, REARTH_PER_RSUN = 109.076;
  const SECTOR_DAYS = 27.0, CADENCE_MIN = 2.0;

  const I18N = {
    en: {
      star: "Seen from Earth: the planet crosses the star's disk",
      xSector: "days (one TESS sector)", xFold: "days from mid-transit (folded curve)",
      depth: "Depth", noTransit: "no transit (b too large)", ratio: "Planet radius / star radius",
      dur: "Transit duration (T14)", ars: "Distance in stellar radii (a/R*)",
      prob: "Chance that such a planet transits", ntr: "Transits in a 27-day sector",
      noise: "Noise per 2-min measurement (approx.)", snr: "SNR in one sector",
      detect: "Would PlanetHunter detect it?", yes: "yes (SNR ≥ 7.1 and ≥ 2 transits)",
      no: "no", lt2: "fewer than 2 transits", lowSnr: "SNR below 7.1", dec: ".",
    },
    es: {
      star: "Visto desde la Tierra: el planeta cruza el disco de la estrella",
      xSector: "días (un sector de TESS)", xFold: "días desde el centro del tránsito (curva plegada)",
      depth: "Profundidad", noTransit: "sin tránsito (b demasiado grande)", ratio: "Radio del planeta / radio de la estrella",
      dur: "Duración del tránsito (T14)", ars: "Distancia en radios estelares (a/R*)",
      prob: "Probabilidad de que un planeta así transite", ntr: "Tránsitos en un sector de 27 días",
      noise: "Ruido por medida de 2 min (aprox.)", snr: "SNR en un sector",
      detect: "¿PlanetHunter lo detectaría?", yes: "sí (SNR ≥ 7,1 y ≥ 2 tránsitos)",
      no: "no", lt2: "menos de 2 tránsitos", lowSnr: "SNR por debajo de 7,1", dec: ",",
    },
    pt: {
      star: "Visto da Terra: o planeta cruza o disco da estrela",
      xSector: "dias (um setor do TESS)", xFold: "dias desde o meio do trânsito (curva dobrada)",
      depth: "Profundidade", noTransit: "sem trânsito (b grande demais)", ratio: "Raio do planeta / raio da estrela",
      dur: "Duração do trânsito (T14)", ars: "Distância em raios estelares (a/R*)",
      prob: "Chance de um planeta assim transitar", ntr: "Trânsitos num setor de 27 dias",
      noise: "Ruído por medida de 2 min (aprox.)", snr: "SNR em um setor",
      detect: "O PlanetHunter detectaria?", yes: "sim (SNR ≥ 7,1 e ≥ 2 trânsitos)",
      no: "não", lt2: "menos de 2 trânsitos", lowSnr: "SNR abaixo de 7,1", dec: ",",
    },
  };
  function S() {
    const lang = (document.documentElement.lang || "en").slice(0, 2);
    return I18N[lang] || I18N.en;
  }
  function fmt(x, d) {
    return x.toFixed(d).replace(".", S().dec);
  }

  // Fraction of the stellar disk (radius 1) covered by a disk of radius k at distance z.
  function overlap(z, k) {
    if (z >= 1 + k) return 0;
    if (z <= 1 - k) return k * k;
    if (z <= k - 1) return 1;
    const k2 = k * k, z2 = z * z;
    const a1 = Math.acos(Math.min(1, Math.max(-1, (z2 + k2 - 1) / (2 * z * k))));
    const a2 = Math.acos(Math.min(1, Math.max(-1, (z2 + 1 - k2) / (2 * z))));
    const s = Math.sqrt(Math.max(0, (-z + k + 1) * (z + k - 1) * (z - k + 1) * (z + k + 1)));
    return (k2 * a1 + a2 - 0.5 * s) / Math.PI;
  }

  function model(p) {
    const k = p.rp / (REARTH_PER_RSUN * p.rs);
    const aM = Math.cbrt((G * p.ms * MSUN * Math.pow(p.per * 86400, 2)) / (4 * Math.PI * Math.PI));
    const aRs = aM / (p.rs * RSUN);
    const arg = (Math.pow(1 + k, 2) - p.b * p.b);
    const t14 = arg > 0 ? (p.per / Math.PI) * Math.asin(Math.min(1, Math.sqrt(arg) / aRs)) : 0;
    const sigma = 1200e-6 * Math.pow(10, 0.2 * (p.tmag - 10));
    // Count transits inside the sector (same t0 as the plot), outside the mid-sector gap.
    let nTr = 0;
    for (let tt = 0.37 * p.per; tt < SECTOR_DAYS; tt += p.per) if (tt < 13.2 || tt > 14.2) nTr++;
    const ptsPerTr = (t14 * 1440) / CADENCE_MIN;
    const depth = overlap(p.b, k);
    const snr = depth > 0 ? (depth / sigma) * Math.sqrt(Math.max(0, nTr * ptsPerTr * 0.8)) : 0;
    return { k, aRs, t14, sigma, nTr, depth, snr, prob: (1 + k) / aRs };
  }

  // Flux at time t (days from mid-transit).
  function flux(t, p, m) {
    const ph = ((t % p.per) + p.per) % p.per;
    const d = Math.min(ph, p.per - ph);
    const x = m.aRs * Math.sin((2 * Math.PI * d) / p.per);
    if (Math.cos((2 * Math.PI * d) / p.per) < 0) return 1; // planet behind the star
    return 1 - overlap(Math.sqrt(p.b * p.b + x * x), m.k);
  }

  function gauss(rng) {
    let u = 0, v = 0;
    while (u === 0) u = rng();
    while (v === 0) v = rng();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }

  function mulberry(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function colors() {
    const cs = getComputedStyle(document.body);
    return {
      fg: cs.getPropertyValue("--md-default-fg-color").trim() || "#222",
      muted: cs.getPropertyValue("--md-default-fg-color--lighter").trim() || "#999",
      accent: cs.getPropertyValue("--md-accent-fg-color").trim() || "#f0a000",
      primary: cs.getPropertyValue("--md-primary-fg-color").trim() || "#3f51b5",
    };
  }

  function setupCanvas(cv, h) {
    const w = cv.parentElement.clientWidth;
    const dpr = window.devicePixelRatio || 1;
    cv.width = w * dpr; cv.height = h * dpr;
    cv.style.width = w + "px"; cv.style.height = h + "px";
    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w, h };
  }

  function drawStar(cv, p, m, c) {
    const { ctx, w, h } = setupCanvas(cv, 180);
    ctx.clearRect(0, 0, w, h);
    const R = Math.min(70, h / 2 - 10), cx = w / 2, cy = h / 2;
    const grad = ctx.createRadialGradient(cx, cy, R * 0.1, cx, cy, R);
    grad.addColorStop(0, "#fff6d0"); grad.addColorStop(1, "#f5a623");
    ctx.fillStyle = grad;
    ctx.beginPath(); ctx.arc(cx, cy, R, 0, 2 * Math.PI); ctx.fill();
    const y = cy + p.b * R;
    ctx.strokeStyle = c.muted; ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(10, y); ctx.lineTo(w - 10, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = "#1b1b1b";
    ctx.beginPath(); ctx.arc(cx, y, Math.max(1.5, m.k * R), 0, 2 * Math.PI); ctx.fill();
    ctx.fillStyle = c.fg; ctx.font = "12px sans-serif";
    ctx.fillText(S().star + " (b = " + fmt(p.b, 2) + ")", 10, 16);
  }

  function axes(ctx, w, h, pad, xmin, xmax, ymin, ymax, xlabel, c) {
    ctx.strokeStyle = c.muted; ctx.lineWidth = 1;
    ctx.strokeRect(pad.l, pad.t, w - pad.l - pad.r, h - pad.t - pad.b);
    ctx.fillStyle = c.fg; ctx.font = "11px sans-serif";
    ctx.fillText(xlabel, w / 2 - 40, h - 4);
    ctx.fillText(((ymax - 1) * 1e6).toFixed(0) + " ppm", 2, pad.t + 10);
    ctx.fillText(((ymin - 1) * 1e6).toFixed(0) + " ppm", 2, h - pad.b);
    ctx.fillText(xmin.toFixed(1), pad.l, h - pad.b + 12);
    ctx.fillText(xmax.toFixed(1), w - pad.r - 24, h - pad.b + 12);
  }

  function drawCurve(cv, p, m, c, folded) {
    const { ctx, w, h } = setupCanvas(cv, 220);
    ctx.clearRect(0, 0, w, h);
    const pad = { l: 70, r: 10, t: 10, b: 28 };
    const rng = mulberry(42);
    const binMin = 30, sigB = m.sigma / Math.sqrt(binMin / CADENCE_MIN);
    const span = folded ? Math.max(3 * m.t14, 0.2) : SECTOR_DAYS;
    const xmin = folded ? -span : 0, xmax = folded ? span : SECTOR_DAYS;
    const ymin = 1 - Math.max(m.depth * 1.6, 4 * sigB), ymax = 1 + 4 * sigB;
    const X = (x) => pad.l + ((x - xmin) / (xmax - xmin)) * (w - pad.l - pad.r);
    const Y = (y) => pad.t + ((ymax - y) / (ymax - ymin)) * (h - pad.t - pad.b);
    axes(ctx, w, h, pad, xmin, xmax, ymin, ymax, folded ? S().xFold : S().xSector, c);
    const t0 = p.per * 0.37;
    ctx.fillStyle = c.muted;
    const step = binMin / 1440;
    for (let t = 0; t < SECTOR_DAYS; t += step) {
      if (t > 13.2 && t < 14.2) continue; // mid-sector data downlink gap
      const f = flux(t - t0, p, m) + sigB * gauss(rng);
      let x = t;
      if (folded) {
        const ph = ((((t - t0) % p.per) + 1.5 * p.per) % p.per) - 0.5 * p.per;
        if (Math.abs(ph) > span) continue;
        x = ph;
      }
      ctx.fillRect(X(x) - 1, Y(Math.min(ymax, Math.max(ymin, f))) - 1, 2.2, 2.2);
    }
    ctx.strokeStyle = c.accent; ctx.lineWidth = 2; ctx.beginPath();
    for (let i = 0; i <= 600; i++) {
      const x = xmin + ((xmax - xmin) * i) / 600;
      const f = folded ? flux(x, p, m) : (x > 13.2 && x < 14.2 ? NaN : flux(x - t0, p, m));
      if (isNaN(f)) { ctx.stroke(); ctx.beginPath(); continue; }
      if (i === 0) ctx.moveTo(X(x), Y(f)); else ctx.lineTo(X(x), Y(f));
    }
    ctx.stroke();
  }

  function render(root) {
    const get = (id) => parseFloat(root.querySelector("#" + id).value);
    const p = { rp: get("ts-rp"), rs: get("ts-rs"), ms: get("ts-ms"), per: get("ts-per"), b: get("ts-b"), tmag: get("ts-tmag") };
    for (const [id, v, d] of [["rp", p.rp, 1], ["rs", p.rs, 2], ["ms", p.ms, 2], ["per", p.per, 1], ["b", p.b, 2], ["tmag", p.tmag, 1]]) {
      root.querySelector("#ts-" + id + "-v").textContent = fmt(v, d);
    }
    const m = model(p);
    const c = colors();
    drawStar(root.querySelector("#ts-star"), p, m, c);
    drawCurve(root.querySelector("#ts-lc"), p, m, c, false);
    drawCurve(root.querySelector("#ts-fold"), p, m, c, true);
    const ok = m.snr >= 7.1 && m.nTr >= 2;
    const s = S();
    const rows = [
      [s.depth, m.depth > 0 ? fmt(m.depth * 1e6, 0) + " ppm (" + fmt(m.depth * 100, 3) + " %)" : s.noTransit],
      [s.ratio, fmt(m.k, 4)],
      [s.dur, fmt(m.t14 * 24, 2) + " h"],
      [s.ars, fmt(m.aRs, 1)],
      [s.prob, fmt(100 * Math.min(1, m.prob), 2) + " %"],
      [s.ntr, String(m.nTr)],
      [s.noise, fmt(m.sigma * 1e6, 0) + " ppm"],
      [s.snr, fmt(m.snr, 1)],
      [s.detect, ok ? s.yes : s.no + " (" + (m.nTr < 2 ? s.lt2 : s.lowSnr) + ")"],
    ];
    root.querySelector("#ts-out").innerHTML =
      "<table><tbody>" + rows.map((r) => "<tr><td>" + r[0] + "</td><td><strong>" + r[1] + "</strong></td></tr>").join("") + "</tbody></table>";
  }

  const PRESETS = {
    terra: { rp: 1, rs: 1, ms: 1, per: 30, b: 0.2, tmag: 8 },
    hotjup: { rp: 12, rs: 1.1, ms: 1.1, per: 3.5, b: 0.3, tmag: 10 },
    anam: { rp: 1.5, rs: 0.2, ms: 0.18, per: 4, b: 0.2, tmag: 11 },
    pimen: { rp: 2.0, rs: 1.1, ms: 1.1, per: 6.27, b: 0.6, tmag: 5.1 },
  };

  function init() {
    const root = document.getElementById("transit-sim");
    if (!root) return;
    const inputs = root.querySelectorAll("input[type=range]");
    inputs.forEach((el) => el.addEventListener("input", () => render(root)));
    root.querySelectorAll("button[data-preset]").forEach((btn) =>
      btn.addEventListener("click", () => {
        const pr = PRESETS[btn.dataset.preset];
        for (const k in pr) root.querySelector("#ts-" + k).value = pr[k];
        render(root);
      })
    );
    window.addEventListener("resize", () => render(root));
    new MutationObserver(() => render(root)).observe(document.body, { attributes: true, attributeFilter: ["data-md-color-scheme"] });
    render(root);
  }

  if (typeof document$ !== "undefined") document$.subscribe(init);
  else document.addEventListener("DOMContentLoaded", init);
})();
