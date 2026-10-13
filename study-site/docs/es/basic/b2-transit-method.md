# B2. El método de tránsito

<p class="meta">Nivel básico · semanas 2–3 · unas 4 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Por qué baja la luz de una estrella cuando un planeta pasa por delante.
    - La regla principal: profundidad ≈ (radio del planeta / radio de la estrella)².
    - Qué dicen el período, la duración y la profundidad sobre el sistema.
    - Por qué solo una pequeña fracción de los planetas transita, y cómo calcular esa fracción.
    - Qué es una curva de luz y cómo se mide una caída en ppm.

## La geometría del tránsito

Vuelve a la linterna y la mosca de la lección B1. La mosca bloquea una parte de la luz proporcional a su **área** comparada con el área de la linterna. Con las estrellas es igual: vista desde aquí, la estrella es un disco brillante y el planeta es un disco oscuro, mucho más pequeño, que atraviesa ese disco.

```
  visto de lado (órbita de perfil)          visto desde aquí (lo que el telescopio "ve")

   estrella       planeta                          .-""""-.
   (  O  )  ------- o ------->  nosotros         /          \
                                                |     ●      |   ● = disco oscuro
   el planeta pasa entre la estrella y nosotros |            |       del planeta
                                                 \          /
                                                   '-....-'
```

El área de un disco es $\pi R^2$. La fracción de luz bloqueada es la razón entre las dos áreas:

$$ \delta \approx \frac{\pi R_p^2}{\pi R_\star^2} = \left(\frac{R_p}{R_\star}\right)^2 $$

Aquí $\delta$ (letra griega "delta") es la **profundidad** del tránsito, $R_p$ es el radio del planeta y $R_\star$ es el radio de la estrella. La $\pi$ se cancela. Queda solo la razón de los radios, al cuadrado.

El cuadrado es el detalle más importante de la lección. Duplica el radio del planeta y la profundidad se cuadruplica. Reduce el radio de la estrella a la mitad y la profundidad también se cuadruplica.

!!! note "Por qué \"aproximadamente\""
    La regla supone que la estrella brilla igual en todo el disco. En realidad, el borde de una estrella es un poco más oscuro que el centro (**oscurecimiento de borde**, tema de la lección M2). Eso redondea el fondo del tránsito y cambia la profundidad en algunos por ciento. Para la intuición, la regla alcanza.

## Profundidad en ppm

Las caídas son minúsculas. Por eso el área usa **ppm**, partes por millón:

| Fracción | Porcentaje | ppm |
|---|---|---|
| 0,01 | 1 % | 10 000 ppm |
| 0,001 | 0,1 % | 1 000 ppm |
| 0,0001 | 0,01 % | 100 ppm |

Para convertir una fracción en ppm, multiplica por un millón. Para convertir un porcentaje en ppm, multiplica por 10 000.

Con la regla y los radios de la lección B1, sale la tabla que aparece en la guía del proyecto:

| Planeta frente a una estrella igual al Sol | $R_p/R_\star$ | Profundidad |
|---|---|---|
| Tierra | 0,0092 | unos 84 ppm (0,0084 %) |
| Neptuno | 0,035 | unos 1 250 ppm (0,13 %) |
| Júpiter | 0,100 | unos 10 000 ppm (1 %) |

Una Tierra frente al Sol apaga 84 milésimas de milésima de la luz. Es como notar que un foco de 100 watts se convirtió en uno de 99,99 watts.

También puedes usar la regla al revés. Si mediste la profundidad y conoces el radio de la estrella:

$$ R_p \approx R_\star \sqrt{\delta} $$

Así es como PlanetHunter estima el radio del planeta de cada señal.

## Período, duración y profundidad

Un tránsito tiene tres números principales. Cada uno cuenta algo distinto.

| Número | Símbolo | Unidad en el proyecto | Qué dice |
|---|---|---|---|
| Período | $P$ | días | cuánto tarda el planeta en dar una vuelta; de ahí, por la tercera ley de Kepler, la distancia a la estrella |
| Duración | $T_{14}$ | horas | cuánto tarda el planeta en atravesar el disco; depende del tamaño de la estrella y de la velocidad del planeta |
| Profundidad | $\delta$ | ppm | el tamaño del planeta comparado con el de la estrella |

El **período** es el intervalo entre dos tránsitos seguidos. Con el período y un instante de tránsito (llamado $T_0$), se pueden predecir todos los tránsitos futuros. Ese par de números se llama **efeméride**.

El período también da la distancia. La **tercera ley de Kepler** dice que las órbitas más grandes tardan más. Para una estrella con la masa del Sol, midiendo el período en años y la distancia $a$ en UA:

$$ a^3 = P^2 $$

La Tierra: $P = 1$ año, $a = 1$ UA. Un planeta de 10 días ($P = 0{,}0274$ años) está a unos 0,09 UA, cuatro veces más cerca que Mercurio.

La **duración** depende de cuánto camino recorre el planeta frente al disco y de su velocidad. Para un tránsito que pasa por el centro del disco, en una órbita circular, una buena aproximación es:

$$ T_{14} \approx \frac{P}{\pi}\,\frac{R_\star}{a} $$

Para la Tierra: $P = 8\,766$ horas, $R_\star / a = 696\,000 / 149\,600\,000 = 0{,}00465$. Entonces $T_{14} \approx 8\,766 / 3{,}14 \times 0{,}00465 \approx 13$ horas. Un observador lejano vería que la Tierra tarda unas 13 horas en cruzar el Sol, una vez al año.

Si el planeta pasa cerca del borde del disco, y no por el centro, el tránsito se vuelve más corto y más puntiagudo. Esto se mide con el **parámetro de impacto** $b$ (0 = centro, 1 = borde), y vas a jugar con él en el simulador.

## Por qué solo una fracción de los planetas transita

Para que haya tránsito, la órbita tiene que estar casi de perfil respecto a nosotros. Si está inclinada, el planeta pasa "por encima" o "por debajo" de la estrella, y no le pasa nada al brillo.

Piensa en un foco en el centro de una sala y en una hormiga que camina en círculo a su alrededor. Solo quien mira desde la altura correcta ve a la hormiga pasar frente al foco. Cuanto más grande es el círculo, más estrecha se vuelve esa franja de altura.

La probabilidad de que una órbita, con orientación al azar, produzca tránsitos es aproximadamente:

$$ p_{\text{tránsito}} \approx \frac{R_\star}{a} $$

Para la Tierra y el Sol: $p \approx 696\,000 / 149\,600\,000 \approx 0{,}0047$, es decir, alrededor de **0,5 %**. De cada 200 sistemas con una Tierra gemela a 1 UA de un Sol, solo uno estaría alineado para mostrar tránsitos.

Para un planeta de 10 días alrededor de una estrella como el Sol ($a \approx 0{,}09$ UA), la probabilidad sube a cerca de 5 %. Para un Júpiter caliente de 3 días ($a \approx 0{,}04$ UA), más de 10 %. Por eso las búsquedas por tránsito encuentran sobre todo planetas de período corto: transitan con más frecuencia **y** con más probabilidad.

!!! warning "Trampa común"
    "No vi tránsito, entonces la estrella no tiene planeta" es incorrecto. La ausencia de tránsito casi siempre significa solo que la órbita no está alineada con nosotros. La gran mayoría de los planetas de la galaxia nunca va a transitar para nosotros.

## La curva de luz

Una **curva de luz** es el gráfico del brillo de una estrella a lo largo del tiempo. Es el dato en bruto de todo este curso. En el eje horizontal va el tiempo (en TESS, en días **BTJD**, que se explican en la lección B3). En el eje vertical va el brillo, dividido entre el brillo promedio, de modo que "normal" vale 1,000.

```
brillo
  1.000 ─────────╮      ╭──────────────────╮      ╭─────────
                 │      │                  │      │
  0.999          ╰──────╯                  ╰──────╯
                 ↑ tránsito                ↑ tránsito
                 |←─────── período ───────→|
                                                       tiempo →
```

Un tránsito de planeta tiene una forma característica:

1. **Entrada** (ingreso): el brillo baja mientras el disco del planeta entra frente a la estrella.
2. **Fondo**: el planeta entero está frente al disco; el brillo se mantiene casi constante, levemente redondeado por el oscurecimiento de borde. La forma recuerda una **U**.
3. **Salida** (egreso): el brillo vuelve a la normalidad.

En la práctica, los puntos de la curva no quedan en una línea limpia. Cada medida tiene **ruido**: pequeñas fluctuaciones aleatorias. Un tránsito de 84 ppm en una estrella cuyo ruido por medida es de 700 ppm es invisible a simple vista. La solución es **juntar muchos tránsitos**: el pipeline los superpone todos alineados por el período (esto se llama **doblar** la curva) y el ruido aleatorio se cancela en parte, mientras que el tránsito, que siempre está en el mismo lugar, se suma.

Cuánto se destaca el tránsito sobre el ruido se mide con la **razón señal-ruido**, el **SNR**. Lo vas a estudiar a fondo en el nivel intermedio. Por ahora, recuerda: más tránsitos, una estrella más brillante y un planeta más grande aumentan el SNR.

!!! tip "En la herramienta"
    Los tres números del tránsito son columnas de la lista de candidatos (`uv run planethunter candidates`): `period_d` (período en días), `t14_h` (duración en horas) y `depth_ppm` (profundidad en ppm). La columna `rp_rearth` es el radio estimado con $R_p = R_\star\sqrt{\delta}$. En el dossier, el gráfico **Folded transit** (tránsito doblado) muestra todos los tránsitos superpuestos: una "U" clara es buena señal. PlanetHunter exige al menos **2 tránsitos** (prueba `n_transits`) y un SNR de al menos **7,1** (prueba `snr`) para llevar una señal adelante. Esos límites están en `config/thresholds.yaml`.

!!! question "Prueba en el simulador"
    Abre el [simulador de tránsito](../lab/transit-simulator.md) y **prueba a cambiar el radio del planeta**. Duplica el radio y comprueba que la profundidad se cuadruplica. Después cambia el Sol por una enana roja de 0,2 R☉ manteniendo la Tierra. Por último, lleva el parámetro de impacto cerca de 1 y mira cómo el tránsito se convierte en una "V".

!!! example "Ejercicio 1 (del plan de estudios)"
    Radios: Sol 696 000 km, Tierra 6 371 km, Neptuno 24 622 km, Júpiter 69 911 km.

    a) Calcula la profundidad de tránsito de la Tierra, de Neptuno y de Júpiter frente al Sol, en ppm.

    b) Repite para una enana roja con radio 0,2 R☉.

    c) ¿Por qué es más fácil encontrar planetas pequeños en estrellas pequeñas?

    ??? success "Ver respuesta"
        **a) Sol ($R_\star$ = 696 000 km).** Usa $\delta = (R_p/R_\star)^2$ y multiplica por $10^6$.

        - Tierra: $6\,371 / 696\,000 = 0{,}009154$. Al cuadrado: $0{,}0000838$. En ppm: **unos 84 ppm**.
        - Neptuno: $24\,622 / 696\,000 = 0{,}03538$. Al cuadrado: $0{,}001251$. En ppm: **unos 1 250 ppm** (la guía redondea a 1 300; 0,13 %).
        - Júpiter: $69\,911 / 696\,000 = 0{,}1004$. Al cuadrado: $0{,}01009$. En ppm: **unos 10 100 ppm**, o 1 %.

        **b) Enana roja ($R_\star = 0{,}2 \times 696\,000 = 139\,200$ km).**

        - Tierra: $6\,371 / 139\,200 = 0{,}04577$. Al cuadrado: $0{,}002095$. **Unos 2 100 ppm** (0,2 %).
        - Neptuno: $24\,622 / 139\,200 = 0{,}1769$. Al cuadrado: $0{,}03129$. **Unos 31 000 ppm** (3,1 %).
        - Júpiter: $69\,911 / 139\,200 = 0{,}5022$. Al cuadrado: $0{,}2522$. **Unos 252 000 ppm** (25 %).

        Atajo: la estrella tiene 1/5 del radio del Sol, así que todas las profundidades son $5^2 = 25$ veces mayores.

        **c)** La profundidad crece con el inverso del cuadrado del radio de la estrella. La misma Tierra que apenas se nota en el Sol (84 ppm, por debajo del ruido de una sola medida de TESS para la mayoría de las estrellas) produce 2 100 ppm en una enana de 0,2 R☉, una caída fácil de detectar. Fíjate también en Júpiter: una caída de 25 % es tan profunda que parecería un eclipse entre dos estrellas. Una profundidad muy grande es motivo para desconfiar, como verás en la lección B4.

!!! example "Ejercicio 2"
    a) ¿Cuál es la probabilidad de que una Tierra a 1 UA de una estrella igual al Sol transite para nosotros?

    b) Si observaras 10 000 estrellas iguales al Sol, cada una con una Tierra gemela, ¿cuántas mostrarían tránsitos?

    c) ¿Y si cada una tuviera un planeta de 3 días (a ≈ 0,04 UA)?

    ??? success "Ver respuesta"
        a) $p \approx R_\star / a = 696\,000 \text{ km} / 149\,600\,000 \text{ km} \approx 0{,}0047$, es decir, alrededor de **0,5 %**.

        b) $10\,000 \times 0{,}0047 \approx$ **47 estrellas**. Las otras 9 953 tienen el planeta, pero la órbita no está alineada con nosotros.

        c) $a = 0{,}04 \times 149\,600\,000 \approx 5\,984\,000$ km. $p \approx 696\,000 / 5\,984\,000 \approx 0{,}116$, alrededor de **12 %**: cerca de **1 160 estrellas**. Las órbitas pequeñas transitan con una probabilidad mucho mayor.

!!! example "Ejercicio 3"
    El planeta Pi Men c, que vas a ver en PlanetHunter en la lección B5, tiene un período de 6,27 días y una profundidad de unos 300 ppm. La estrella Pi Mensae tiene un radio de unos 1,1 R☉.

    a) Estima el radio del planeta en R⊕.

    b) ¿Cuántos tránsitos caben en un sector de TESS, que dura unos 27 días?

    ??? success "Ver respuesta"
        a) $\delta = 300 \text{ ppm} = 0{,}0003$. $\sqrt{0{,}0003} \approx 0{,}0173$. Ese es $R_p/R_\star$. Entonces $R_p \approx 0{,}0173 \times 1{,}1 \text{ R☉} \approx 0{,}019$ R☉. Convirtiendo con 1 R☉ ≈ 109 R⊕: $0{,}019 \times 109 \approx$ **2,1 R⊕**. Una supertierra o mininetuno, con alrededor del doble del radio de la Tierra.

        b) $27 / 6{,}27 \approx 4{,}3$. Caben **4 tránsitos**, a veces 5 según dónde haya caído el primero. En la práctica pueden ser menos: TESS hace una pausa de alrededor de un día a mitad de cada sector para enviar datos a la Tierra (lección B3), y un tránsito puede caer en ella.

## Checklist de la lección

- [ ] Sé explicar por qué baja la luz en un tránsito (el disco del planeta bloquea parte del disco de la estrella).
- [ ] Sé usar $\delta \approx (R_p/R_\star)^2$ en los dos sentidos: del radio a la profundidad y de la profundidad al radio.
- [ ] Sé convertir entre fracción, porcentaje y ppm.
- [ ] Sé qué dice cada uno de los tres números (período, duración, profundidad) sobre el sistema.
- [ ] Sé qué es una efeméride ($P$ y $T_0$).
- [ ] Sé calcular la probabilidad de tránsito $R_\star/a$ y por qué favorece las órbitas cortas.
- [ ] Sé describir las partes de un tránsito en una curva de luz (entrada, fondo en U, salida).
- [ ] Jugué con el simulador cambiando el radio del planeta, el radio de la estrella y el parámetro de impacto.
- [ ] Hice los tres ejercicios sin mirar la respuesta.

## Para ir más allá

- Winn (2010), "Transits and Occultations", gratuito en arXiv (arXiv:1001.2010). El texto clásico sobre la física de los tránsitos. En este nivel, lee solo la introducción y mira las figuras; vuelve a él en la lección M2.
- NASA Science, página sobre el método de tránsito (science.nasa.gov/exoplanets). Tiene animaciones cortas que muestran cómo se forma la curva de luz mientras pasa el planeta.
- [Simulador de tránsito](../lab/transit-simulator.md) de este curso. Haz los dos desafíos de la página.
- Charbonneau et al. (2000), "Detection of planetary transits across a Sun-like star", *The Astrophysical Journal* 529, L45. El primer tránsito de exoplaneta observado (HD 209458 b). Mira la figura de la curva de luz: es la misma "U" de esta lección.
