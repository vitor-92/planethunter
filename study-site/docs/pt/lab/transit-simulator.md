# Simulador de trânsito

<p class="meta">Laboratório · use junto das aulas B2, M1 e M2</p>

Mexa nos controles e veja, ao vivo, como a curva de luz muda. É a mesma física que o PlanetHunter usa para procurar planetas, simplificada.

<div id="transit-sim" markdown="0">
  <div class="ts-presets">
    Exemplos prontos:
    <button data-preset="terra">Terra num Sol</button>
    <button data-preset="hotjup">Júpiter quente</button>
    <button data-preset="anam">Super-Terra numa anã vermelha</button>
    <button data-preset="pimen">Pi Men c</button>
  </div>
  <div class="ts-controls">
    <label>Raio do planeta: <span id="ts-rp-v"></span> R⊕
      <input id="ts-rp" type="range" min="0.5" max="25" step="0.1" value="2.5"></label>
    <label>Raio da estrela: <span id="ts-rs-v"></span> R☉
      <input id="ts-rs" type="range" min="0.1" max="3" step="0.01" value="1"></label>
    <label>Massa da estrela: <span id="ts-ms-v"></span> M☉
      <input id="ts-ms" type="range" min="0.1" max="2" step="0.01" value="1"></label>
    <label>Período da órbita: <span id="ts-per-v"></span> dias
      <input id="ts-per" type="range" min="0.5" max="30" step="0.1" value="5"></label>
    <label>Parâmetro de impacto b: <span id="ts-b-v"></span> (0 = centro, 1 = borda)
      <input id="ts-b" type="range" min="0" max="1.2" step="0.01" value="0.3"></label>
    <label>Brilho da estrela (Tmag): <span id="ts-tmag-v"></span> (menor = mais brilhante)
      <input id="ts-tmag" type="range" min="5" max="15" step="0.1" value="10"></label>
  </div>
  <canvas id="ts-star"></canvas>
  <canvas id="ts-lc"></canvas>
  <canvas id="ts-fold"></canvas>
  <div id="ts-out"></div>
</div>

## O que observar

1. **Raio do planeta.** Dobre o raio e a profundidade quadruplica, porque ela depende da **área** do disco escuro: $\delta \approx (R_p/R_\star)^2$.
2. **Raio da estrela.** Com a mesma Terra, troque o Sol por uma anã vermelha de 0,2 R☉. A queda fica 25 vezes mais funda. Por isso planetas pequenos são mais fáceis de achar em estrelas pequenas.
3. **Período.** Períodos longos dão menos trânsitos por setor. Abaixo de 2 trânsitos, o PlanetHunter não aceita o sinal, mesmo que ele seja forte.
4. **Parâmetro de impacto.** Leve $b$ para perto de 1: o trânsito fica curto e em forma de **V**. É o formato que o teste `shape` desconfia, porque binárias rasantes também o produzem.
5. **Brilho.** Estrelas fracas (Tmag alto) têm mais ruído. Veja o SNR cair e os pontos se espalharem.

!!! example "Desafio 1"
    Ache o menor planeta que o PlanetHunter detectaria, num setor, ao redor de uma estrela como o Sol com Tmag 9 e período de 10 dias.

    ??? success "Ver resposta"
        Com R☉ = 1, M☉ = 1, P = 10 d, b = 0,3 e Tmag 9, o SNR passa de 7,1 por volta de 2,2 R⊕ (o valor exato varia um pouco com b).

        A conta por trás: o ruído por medida é ~760 ppm; o trânsito dura ~3,7 h (~110 medidas de 2 min); há 2 trânsitos no setor. SNR = profundidade / ruído × √(número de medidas em trânsito), então a profundidade mínima é cerca de 7,1 × 760 ppm / √180 ≈ 400 ppm, o que dá $R_p \approx \sqrt{0{,}0004} \times 109 \approx 2{,}2$ R⊕. Planetas do tamanho da Terra, nessas condições, ficam abaixo do ruído num único setor: precisariam de vários setores somados.

!!! example "Desafio 2"
    Por que a "chance de transitar" diminui quando o período aumenta?

    ??? success "Ver resposta"
        A chance é aproximadamente $R_\star/a$. Período maior significa órbita maior ($a$ cresce com $P^{2/3}$, pela terceira lei de Kepler), então o planeta precisa estar mais perfeitamente alinhado conosco para passar na frente da estrela.

!!! note "Limitações do simulador"
    O disco da estrela é uniforme (sem escurecimento de borda, assunto da aula M2), a órbita é circular e o ruído é uma aproximação do TESS de 2 minutos calibrada com estrelas reais do setor 69. Os números servem para intuição, não para pesquisa.
