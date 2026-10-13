# P2. NumPy, pandas y Matplotlib

<p class="meta">Ruta de programación · después del básico, antes de M4 · cerca de 12 horas</p>

!!! abstract "En esta lección vas a aprender"
    - Usar arrays de NumPy para hacer cálculos sobre miles de puntos a la vez.
    - Simular una curva de luz con ruido y un tránsito en forma de caja, y medir la profundidad.
    - Leer la tabla de TOIs de ExoFOP con pandas, filtrar y resumir.
    - Hacer gráficos con Matplotlib: curva de luz, curva plegada en el período y diagrama período versus radio.

Requisito previo: la [lección P1](p1-python-basics.md). En la carpeta de estudios, instala las bibliotecas (si todavía no lo hiciste):

```powershell
uv add numpy pandas matplotlib
```

## NumPy: cálculos con muchos números a la vez

Una curva de luz de TESS tiene cerca de 20 000 medidas por sector. Hacer cálculos con un bucle `for`, punto por punto, es lento y verboso. **NumPy** lo resuelve con el **array**: una secuencia de números del mismo tipo en la que cada operación se aplica a todos los elementos al mismo tiempo. Esto se llama **operación vectorial**.

```python
import numpy as np

prof_ppm = np.array([84, 1251, 10090])   # Tierra, Neptuno, Júpiter frente al Sol
print(prof_ppm / 1e6)                    # divide los tres a la vez
print(np.sqrt(prof_ppm / 1e6) * 109.1)   # radios en R_tierra: ~[1, 3.9, 11]
```

Con una lista común, `lista / 1e6` da error. Con un array, funciona. Es la diferencia más importante entre los dos.

Otras herramientas que vas a usar todo el tiempo:

| Código | Qué hace |
|---|---|
| `np.arange(0, 27, 0.5)` | Números de 0 hasta antes de 27, de 0,5 en 0,5 |
| `np.median(a)`, `np.mean(a)`, `np.std(a)` | Mediana, media y desviación estándar |
| `a > 1.0` | Array de `True`/`False`, una **máscara** |
| `a[mascara]` | Solo los elementos donde la máscara es `True` |
| `np.abs(a)` | Valor absoluto de cada elemento |

## Simular una curva de luz

Vamos a fabricar una curva de luz con un tránsito conocido. Así sabes la respuesta correcta y puedes comprobar si tu medida la recupera. Es la misma idea de la prueba de inyección de tránsitos que el proyecto usa para medirse a sí mismo (lección A5).

Crea el archivo `simula.py`:

```python
"""Simula 27 días de TESS (cadencia de 2 min) con un tránsito en caja y ruido."""
import matplotlib.pyplot as plt
import numpy as np

rng = np.random.default_rng(seed=42)   # generador de números aleatorios, siempre igual

# 1. Eje del tiempo: un sector de 27 días, un punto cada 2 minutos
cadencia_dias = 2 / (60 * 24)
tiempo = np.arange(0.0, 27.0, cadencia_dias)
print("puntos:", tiempo.size)            # 19440

# 2. Parámetros del planeta inventado
periodo = 3.0            # días
t0 = 1.5                 # instante del primer tránsito, días
duracion_horas = 3.0
profundidad_ppm = 5000.0
ruido_ppm = 1000.0       # dispersión de cada medida

# 3. Fase: distancia de cada punto al tránsito más cercano, en días
fase = (tiempo - t0 + 0.5 * periodo) % periodo - 0.5 * periodo
en_transito = np.abs(fase) < (duracion_horas / 24) / 2

# 4. Modelo de caja: brillo 1 fuera del tránsito, 1 - profundidad dentro
modelo = np.ones_like(tiempo)
modelo[en_transito] = 1.0 - profundidad_ppm / 1e6

# 5. Ruido gaussiano sumado al modelo
ruido = rng.normal(loc=0.0, scale=ruido_ppm / 1e6, size=tiempo.size)
flujo = modelo + ruido
```

El paso 3 es el corazón de la simulación. El operador `%` da el resto de la división. "Enrolla" el tiempo en vueltas de un período, como un reloj que vuelve a cero cada 3 días. Sumar y restar medio período centra el tránsito en fase cero. El resultado `fase` va de −1,5 a +1,5 días.

El paso 5 usa un **ruido gaussiano** (distribución normal, lección M1): cada medida se equivoca un poco, hacia arriba o hacia abajo, con una desviación estándar de 1 000 ppm.

### Medir la profundidad

Ahora finge que no sabes la respuesta. Compara el brillo típico dentro y fuera del tránsito. Usa la **mediana**, que es menos sensible a los puntos extraños que la media.

```python
nivel_fuera = np.median(flujo[~en_transito])    # ~ quiere decir "no"
nivel_dentro = np.median(flujo[en_transito])
prof_medida = (1 - nivel_dentro / nivel_fuera) * 1e6
n_dentro = en_transito.sum()                   # True cuenta como 1
snr = prof_medida / (ruido_ppm / np.sqrt(n_dentro))

print(f"puntos en tránsito: {n_dentro}")       # 801
print(f"profundidad medida: {prof_medida:.0f} ppm (verdadera: 5000)")   # ~4975
print(f"SNR aproximado: {snr:.0f}")            # ~141
```

¿Por qué dividir el ruido entre $\sqrt{N}$? Al promediar $N$ medidas independientes, el error de la media baja con la raíz de $N$. Con 801 puntos en tránsito, el ruido efectivo baja de 1 000 a cerca de 35 ppm. Una caída de 5 000 ppm queda muy por encima de eso. Esta es una versión simplificada de la **relación señal-ruido** (SNR) que PlanetHunter exige que sea al menos 7,1 (lección M1).

## Matplotlib: ver los datos

**Matplotlib** dibuja gráficos. Continúa en el mismo archivo:

```python
fig, ejes = plt.subplots(2, 1, figsize=(10, 7))

# Panel de arriba: la curva de luz completa
ejes[0].plot(tiempo, flujo, ".", markersize=1, color="0.5")
ejes[0].set_xlabel("tiempo (días)")
ejes[0].set_ylabel("brillo relativo")
ejes[0].set_title("Curva de luz simulada")

# Panel de abajo: curva plegada (todos los tránsitos superpuestos)
fase_horas = fase * 24
ejes[1].plot(fase_horas, flujo, ".", markersize=1, color="0.7", label="medidas")

# Medias en cajas de 15 minutos, para ver la forma
bordes = np.linspace(-36, 36, 289)               # 288 cajas de 0,25 h
idx = np.digitize(fase_horas, bordes) - 1        # en qué caja cae cada punto
suma = np.bincount(idx, weights=flujo, minlength=288)
conteo = np.bincount(idx, minlength=288)
centros = 0.5 * (bordes[:-1] + bordes[1:])
ejes[1].plot(centros, suma / conteo, "o", color="C3", label="media en 15 min")

ejes[1].set_xlim(-6, 6)
ejes[1].set_xlabel("horas desde el centro del tránsito")
ejes[1].set_ylabel("brillo relativo")
ejes[1].legend()

fig.tight_layout()
plt.show()
```

Ejecútalo con `uv run python simula.py`. En el panel de arriba, el tránsito casi desaparece en el ruido. En el de abajo, después de **plegar** la curva en el período, los 9 tránsitos se apilan y la caja aparece nítida. Esto es lo que el dossier de PlanetHunter muestra en la sección "Folded transit" (tránsito plegado).

`np.bincount` suma los flujos de cada caja de una vez, sin bucle. Dividir la suma entre el conteo da la media por caja.

!!! info "Por qué funciona plegar"
    Plegar en el período correcto pone todos los tránsitos en el mismo lugar. El ruido, que es aleatorio, se cancela en la media. El tránsito, que se repite, se suma. Plegar en el período equivocado dispersa los tránsitos y la caja desaparece. Un periodograma (lección M3) es, en el fondo, probar miles de plegados y ver cuál deja la caja más profunda.

## pandas: tablas

**pandas** trabaja con tablas, llamadas **DataFrame**: filas y columnas con nombre, como una hoja de cálculo que controlas con código.

### Leer la lista de TOIs de ExoFOP

ExoFOP publica la lista de todos los TOIs (candidatos oficiales de TESS) en un archivo CSV, un texto con valores separados por comas. pandas lo lee directo de internet:

```python
import pandas as pd

URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
tois = pd.read_csv(URL, low_memory=False)
tois.to_csv("tois.csv", index=False)     # guarda una copia local
print(tois.shape)                        # (filas, columnas)
```

Las próximas veces, lee la copia local con `pd.read_csv("tois.csv")`. Es más rápido y le ahorra trabajo al servidor de ExoFOP.

El 9 de octubre de 2026 la tabla tenía 8 151 filas y 63 columnas. Tus números serán mayores: la lista crece cada semana.

### Mirar y seleccionar columnas

```python
columnas = ["TOI", "TIC ID", "TFOPWG Disposition", "Period (days)",
           "Depth (ppm)", "Planet Radius (R_Earth)"]
print(tois[columnas].head())             # las 5 primeras filas
print(tois["TFOPWG Disposition"].value_counts(dropna=False))
```

`value_counts` cuenta cuántas veces aparece cada valor. La columna `TFOPWG Disposition` trae la decisión del grupo de seguimiento de TESS:

| Código | Significado | Al 9/10/2026 |
|---|---|---|
| PC | Candidato a planeta | 4 820 |
| FP | Falso positivo | 1 315 |
| CP | Planeta confirmado (hallado por TESS) | 815 |
| KP | Planeta ya conocido antes de TESS | 606 |
| APC | Candidato ambiguo | 490 |
| FA | Falsa alarma | 100 |

### Filtrar

Filtrar en pandas es usar una máscara, igual que en NumPy:

```python
# Planetas confirmados o conocidos
planetas = tois[tois["TFOPWG Disposition"].isin(["CP", "KP"])]

# De esos, los de período menor que 1 día, del más profundo al menos profundo
cortos = planetas[planetas["Period (days)"] < 1.0]
print(len(planetas), len(cortos))       # 1421 y 78 al 9/10/2026
print(cortos.sort_values("Depth (ppm)", ascending=False)[columnas].head(8))

# Un objetivo específico: WASP-18, TIC 100100827
wasp18 = tois[tois["TIC ID"] == 100100827]
print(wasp18[["TOI", "TFOPWG Disposition", "Period (days)", "Depth (ppm)",
              "Duration (hours)", "Planet Radius (R_Earth)", "Sectors"]])
```

WASP-18 b aparece como TOI-185.01, disposición KP, período 0,941453 días, profundidad 11 445 ppm, duración 2,05 horas, radio 15,3 R⊕, observado en los sectores 2, 3, 29, 30 y 69. Vas a medir esos números por tu cuenta en la [lección P3](p3-lightkurve-in-practice.md).

Para combinar condiciones, usa `&` (y) y `|` (o), con cada condición entre paréntesis:

```python
pequenos = planetas[(planetas["Planet Radius (R_Earth)"] < 2) &
                    (planetas["Period (days)"] < 10)]
```

### Estadísticas y grupos

```python
print(planetas["Period (days)"].describe())   # conteo, media, cuartiles...
print(tois.groupby("TFOPWG Disposition")["Planet Radius (R_Earth)"].median())
```

`describe` muestra que la mediana del período de los planetas CP y KP es de cerca de 4,3 días. La búsqueda de TESS favorece los períodos cortos: con solo 27 días por sector, un planeta de 4 días transita varias veces, uno de 40 días tal vez una sola.

`groupby` separa la tabla por disposición y calcula la mediana del radio en cada grupo. Al 9/10/2026, los CP tenían una mediana de 3,2 R⊕, y los FP, de 10,0 R⊕. Los falsos positivos tienden a parecer "grandes", porque muchos son binarias eclipsantes con caídas profundas.

### Gráfico período versus radio

```python
fig, ax = plt.subplots(figsize=(8, 6))
for disp, cor in [("PC", "0.7"), ("FP", "C3"), ("CP", "C0"), ("KP", "C2")]:
    grupo = tois[tois["TFOPWG Disposition"] == disp]
    ax.scatter(grupo["Period (days)"], grupo["Planet Radius (R_Earth)"],
               s=4, color=cor, label=f"{disp} ({len(grupo)})")
ax.set_xscale("log")      # escala logarítmica: 1, 10, 100 con el mismo espacio
ax.set_yscale("log")
ax.set_xlabel("período (días)")
ax.set_ylabel("radio (R_tierra)")
ax.legend()
plt.show()
```

La **escala logarítmica** da el mismo espacio a "de 1 a 10" y a "de 10 a 100". Sin ella, casi todos los puntos quedarían apretados en una esquina.

!!! tip "En la herramienta"
    PlanetHunter lee exactamente ese CSV de ExoFOP, con las mismas columnas (`TFOPWG Disposition`, `Period (days)`, `Epoch (BJD)`). Mira `normalize_exofop_toi` en `src/planethunter/catalogs/mirrors.py`, que arma el espejo local usado en el crossmatch, y `build` en `src/planethunter/benchmark.py`, que elige los TOIs de un sector con `str.split(",")` en la columna `Sectors`, como en el ejercicio 2 más abajo. Las curvas de luz se guardan como arrays NumPy `float32` (el tiempo en `float64`), y casi toda función del pipeline recibe y devuelve DataFrames.

## Ejercicios

!!! example "Ejercicio 1. Una Tierra en el ruido"
    En `simula.py`, cambia la profundidad a 84 ppm (la Tierra frente al Sol) y mantén el ruido de 1 000 ppm. Calcula el SNR. ¿El planeta sería detectado con el criterio SNR ≥ 7,1? ¿Y con 500 ppm?

    ??? success "Ver respuesta"
        Con los mismos 801 puntos en tránsito, el ruido efectivo es $1000/\sqrt{801} \approx 35$ ppm.

        - 84 ppm: SNR $\approx 84/35 \approx 2{,}4$. No pasa. Una Tierra en un solo sector, con ese ruido, queda escondida.
        - 500 ppm: SNR $\approx 14$. Pasa con holgura.

        Los valores medidos varían un poco, porque el ruido es aleatorio. Para que aparezca una Tierra, hace falta menos ruido (estrella más brillante), más tránsitos (varios sectores) o una estrella más pequeña, que hace la caída más profunda.

!!! example "Ejercicio 2. TOIs del sector 69"
    La columna `Sectors` es un texto como `"2,3,29,30,69"`. Selecciona los TOIs observados en el sector 69 y cuéntalos por disposición.

    ??? success "Ver respuesta"
        ```python
        listas = tois["Sectors"].fillna("").astype(str).str.split(",")
        en_69 = listas.apply(lambda xs: "69" in [x.strip() for x in xs])
        s69 = tois[en_69]
        print(len(s69))
        print(s69["TFOPWG Disposition"].value_counts(dropna=False))
        ```
        `str.split(",")` transforma cada texto en una lista. `apply` ejecuta una pequeña función (`lambda`) en cada fila. Buscar `"69"` dentro de la lista evita confundir 69 con 169. Al 9/10/2026 eran 407 TOIs: 260 PC, 74 CP, 37 FP, 22 KP, 13 APC, 1 FA. No uses `str.contains("69")`: aceptaría un sector 169 en el futuro.

!!! example "Ejercicio 3. Plegar en el período equivocado"
    En la simulación, pliega la curva en 6 días (el doble) y en 1,5 días (la mitad) en lugar de 3. Mide la profundidad en el centro en cada caso. ¿Qué pasa?

    ??? success "Ver respuesta"
        ```python
        for p in (6.0, 1.5):
            f = (tiempo - t0 + 0.5 * p) % p - 0.5 * p
            dentro = np.abs(f) < (duracion_horas / 24) / 2
            print(p, (1 - np.median(flujo[dentro])) * 1e6)
        ```
        - Con 6 días (2P), el centro todavía muestra cerca de 5 000 ppm, pero solo la mitad de los tránsitos está ahí. La otra mitad cae en fase ±3 días, la "fase 0,5". Visualmente parece una binaria con dos eclipses iguales.
        - Con 1,5 días (P/2), la mitad de las "ventanas" en fase cero no tiene tránsito. La profundidad medida baja a cerca de 2 500 ppm, la mitad.

        Por eso los alias como $2P$ y $P/2$ engañan (lección M3), y por eso el vetting compara los tránsitos impares y pares (lección M5).

## Checklist de la lección

- [ ] Hice cálculos con arrays sin usar bucles
- [ ] Simulé una curva con tránsito y recuperé la profundidad
- [ ] Calculé un SNR aproximado y entendí el papel de $\sqrt{N}$
- [ ] Hice el gráfico de la curva y de la curva plegada con medias por caja
- [ ] Leí el CSV de TOIs, filtré por disposición y período y encontré WASP-18 b
- [ ] Usé `describe` y `groupby`
- [ ] Hice el diagrama período versus radio en escala logarítmica
- [ ] Resolví los tres ejercicios

## Para ir más allá

- NumPy, guía para principiantes absolutos ([numpy.org](https://numpy.org/doc/stable/user/absolute_beginners.html)). Explica arrays, máscaras y operaciones vectoriales con calma.
- pandas, "10 minutes to pandas" ([pandas.pydata.org](https://pandas.pydata.org/docs/user_guide/10min.html)). Recorrido rápido por lectura, selección, filtrado y agrupamiento.
- Página de descarga de TOIs de ExoFOP ([exofop.ipac.caltech.edu](https://exofop.ipac.caltech.edu/tess/view_toi.php)). Muestra la misma tabla en el navegador, útil para comprobar tus filtros.
- Curso em Vídeo — Python, mundo 3 (Gustavo Guanabara). Curso en portugués que refuerza listas, diccionarios y funciones, la base para usar bien NumPy y pandas.
