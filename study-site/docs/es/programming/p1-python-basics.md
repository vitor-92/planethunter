# P1. Python básico

<p class="meta">Ruta de programación · junto con el nivel básico · unas 10 horas</p>

!!! abstract "En esta lección vas a aprender a"
    - Guardar números y textos en variables y saber el tipo de cada uno.
    - Organizar datos en listas (períodos) y diccionarios (parámetros de una estrella).
    - Repetir cuentas con bucles `for` y decidir con `if`.
    - Escribir funciones que calculan la profundidad del tránsito y el radio del planeta.
    - Separar tu código en módulos e importarlos.

Antes de empezar, prepara la computadora como se explica en la [página de la ruta](index.md). Crea cada ejemplo como un archivo `.py` en la carpeta `estudios-exoplanetas` y córrelo con `uv run python nombre_del_archivo.py`.

## Variables y tipos

Una **variable** es un nombre que apunta a un valor. Piensa en una etiqueta pegada en una caja: la etiqueta es el nombre, el contenido es el valor.

```python
periodo_dias = 3.7            # número con decimales (float)
n_transitos = 7               # número entero (int)
nombre_estrella = "Pi Mensae" # texto (str, de "string")
hay_transito = True           # verdadero o falso (bool)

print(periodo_dias, n_transitos, nombre_estrella, hay_transito)
print(type(periodo_dias))     # <class 'float'>
```

El signo `=` no es el "igual" de las matemáticas. Significa "guarda el valor de la derecha en el nombre de la izquierda". Todo lo que va después de `#` es un **comentario**: Python lo ignora, sirve para ti.

Reglas prácticas para los nombres: solo letras sin acento, números y `_`; no empieces con un número; usa nombres que digan la unidad. `radio_rsun` es mejor que `r`. PlanetHunter sigue esta regla: `period_days`, `depth_ppm`, `duration_hours`.

### Cuentas

```python
radio_sol_km = 696_000      # el _ solo separa los miles para facilitar la lectura
radio_tierra_km = 6_371

razon = radio_tierra_km / radio_sol_km   # división
profundidad = razon ** 2                 # ** es potencia
print(profundidad)                       # 8.379...e-05
```

El resultado `8.379e-05` es notación científica: $8{,}379 \times 10^{-5}$. Es la fracción de la luz del Sol que bloquea la Tierra. Esto viene de la regla de la [lección B2](../basic/b2-transit-method.md):

$$\delta \approx \left(\frac{R_p}{R_\star}\right)^2$$

donde $\delta$ es la profundidad, $R_p$ el radio del planeta y $R_\star$ el radio de la estrella.

### Convertir a ppm y a porcentaje

**ppm** significa partes por millón. Para pasar de fracción a ppm, multiplica por un millón. Para porcentaje, por cien.

```python
profundidad_ppm = profundidad * 1e6     # 1e6 = 1 000 000
profundidad_pct = profundidad * 100
print(f"Tierra: {profundidad_ppm:.0f} ppm = {profundidad_pct:.4f} %")
# Tierra: 84 ppm = 0.0084 %
```

La `f` antes de las comillas crea una **f-string**: lo que está entre llaves se calcula y se inserta en el texto. El `:.0f` dice "muestra con cero decimales".

!!! warning "Trampa: coma decimal"
    En Python, `3,7` no es el número tres coma siete. Es un par de números, 3 y 7. Usa siempre punto: `3.7`.

## Listas

Una **lista** guarda varios valores en orden, entre corchetes.

```python
periodos_dias = [0.94, 3.7, 6.27, 11.4]

print(len(periodos_dias))      # 4 elementos
print(periodos_dias[0])        # 0.94  (la cuenta empieza en CERO)
print(periodos_dias[-1])       # 11.4  (el índice -1 es el último)
print(periodos_dias[1:3])      # [3.7, 6.27]  (rebanada: del 1 hasta antes del 3)

periodos_dias.append(25.0)     # agrega al final
print(min(periodos_dias), max(periodos_dias), sum(periodos_dias))
print(sorted(periodos_dias, reverse=True))
```

Empezar a contar desde cero parece raro al principio. Piensa en el índice como "cuántos pasos avanzar desde el comienzo".

## Diccionarios

Un **diccionario** guarda pares de clave y valor, entre llaves. Es ideal para describir una cosa con varios atributos, como una estrella.

```python
estrella = {
    "nombre": "WASP-18",
    "tic_id": 100100827,
    "radio_rsun": 1.35,    # radio en radios solares
    "tmag": 8.83,          # brillo en la banda de TESS (menor = más brillante)
}

print(estrella["radio_rsun"])      # 1.35
estrella["teff_k"] = 6226          # agrega una clave nueva
for clave, valor in estrella.items():
    print(clave, "=", valor)
```

Los valores de WASP-18 vienen del archivo que PlanetHunter grabó para el sector 69. Vas a abrir ese archivo en la [lección P3](p3-lightkurve-in-practice.md).

## Decisiones con `if`

```python
rp_rearth = 15.1   # radio del planeta en radios terrestres

if rp_rearth < 4:
    clase = "rocoso a mini-Neptuno"
elif rp_rearth < 8:
    clase = "tamaño de Neptuno"
elif rp_rearth <= 20:
    clase = "gigante"
else:
    clase = "demasiado grande: probablemente no es un planeta"

print(clase)
```

Fíjate en la **indentación**: los 4 espacios al comienzo de las líneas le dicen a Python qué está "dentro" de cada `if`. En Python, la indentación no es adorno, es una regla. Los rangos de tamaño siguen la tabla de lectura de candidatos de la guía del proyecto.

## Bucles `for`

Un **bucle** repite un bloque para cada elemento de una lista.

```python
radio_sol_km = 696_000
planetas_km = {"Tierra": 6_371, "Neptuno": 24_622, "Júpiter": 69_911}

for nombre, radio_km in planetas_km.items():
    prof_ppm = (radio_km / radio_sol_km) ** 2 * 1e6
    print(f"{nombre:8s} {prof_ppm:8.0f} ppm")
```

Salida:

```text
Tierra         84 ppm
Neptuno      1251 ppm
Júpiter     10090 ppm
```

Compara con la tabla de la lección B2 (84, ~1 300 y ~10 000 ppm). La guía redondea Neptuno a 1 300.

Para repetir un número fijo de veces, usa `range`:

```python
periodo = 0.9416     # días
t0 = 3182.758        # instante del primer tránsito, en BTJD
for n in range(5):   # n = 0, 1, 2, 3, 4
    print(f"tránsito {n}: BTJD {t0 + n * periodo:.3f}")
```

**BTJD** es la cuenta de días que usa TESS (días desde una fecha de referencia). Este cálculo es una **efeméride**: la predicción de cuándo ocurren los próximos tránsitos.

## Funciones

Una **función** es una receta con nombre. La defines una vez y la usas cuantas veces quieras. Recibe **parámetros** (entradas) y devuelve un resultado con `return`.

```python
RSUN_EN_REARTH = 109.1   # un radio solar equivale a 109.1 radios terrestres


def profundidad_ppm(rp_rearth: float, rs_rsun: float) -> float:
    """Profundidad del tránsito en ppm. Rp en R_tierra, R* en R_sol."""
    razon = rp_rearth / (rs_rsun * RSUN_EN_REARTH)
    return razon**2 * 1e6


def radio_planeta(prof_ppm: float, rs_rsun: float) -> float:
    """Radio del planeta en R_tierra a partir de la profundidad (ppm) y de R* (R_sol)."""
    return (prof_ppm / 1e6) ** 0.5 * rs_rsun * RSUN_EN_REARTH


print(profundidad_ppm(1.0, 1.0))     # la Tierra frente al Sol: ~84 ppm
print(radio_planeta(84, 1.0))        # vuelve a ~1 R_tierra
print(radio_planeta(84, 0.2))        # la misma caída en una enana roja: ~0.2 R_tierra
```

Detalles:

- `rp_rearth: float` es una **anotación de tipo**. Le avisa a quien lee que se espera un número. Python no la exige, pero PlanetHunter la usa en todas las funciones.
- El texto entre `"""` justo debajo del `def` es la **docstring**: explica qué hace la función y las unidades.
- `radio_planeta` es la cuenta inversa de `profundidad_ppm`: raíz cuadrada de la profundidad (`** 0.5`) por el radio de la estrella.

La última línea muestra una idea importante del nivel básico: la misma caída de 84 ppm en una estrella cinco veces más pequeña corresponde a un planeta cinco veces más pequeño. Por eso es más fácil encontrar planetas pequeños en estrellas pequeñas.

!!! tip "En la herramienta"
    PlanetHunter hace exactamente la cuenta de `radio_planeta` para mostrar la columna `rp_rearth` en la lista de candidatos. Está en `src/planethunter/pipeline.py`, en la función `candidate_table`, escrita en SQL: `sqrt(fit_depth_ppm * 1e-6) * radius_rsun * 109.076`. Otro ejemplo: en `src/planethunter/cli.py`, la función `_parse_ints` transforma el texto `"1,4,8"` de la opción `--sectors` en la lista `[1, 4, 8]`, usando `split(",")` y un bucle compacto.

## Módulos

Un **módulo** es un archivo `.py` cuyas funciones reutilizas en otros archivos con `import`.

Python ya trae muchos módulos. El módulo `math` tiene raíz cuadrada, pi y otras funciones:

```python
import math

print(math.sqrt(10_583e-6))   # raíz cuadrada de 0.010583 = 0.1029
print(math.pi)
```

También puedes crear el tuyo. Guarda las dos funciones de arriba en un archivo `transito.py`. En otro archivo, en la misma carpeta:

```python
from transito import radio_planeta

rp = radio_planeta(10_583, 1.3466)
print(f"WASP-18 b: {rp:.1f} radios terrestres")   # 15.1
```

Los números son reales: 10 583 ppm es la profundidad que PlanetHunter midió para WASP-18 b en el sector 69, y 1,3466 R☉ es el radio de la estrella en el catálogo de TESS.

Bibliotecas como NumPy y Lightkurve son módulos hechos por otras personas. Las instalas con `uv add` y las importas de la misma manera.

## Errores: lee la última línea

Equivocarse es parte del proceso. Cuando Python encuentra un problema, muestra un **traceback**. La información más útil está en la **última línea**:

| Mensaje | Causa más común |
|---|---|
| `NameError: name 'periodo' is not defined` | Nombre mal escrito o variable creada después de usarla |
| `IndentationError` | Espacios al comienzo de la línea desalineados |
| `TypeError: can't multiply sequence by non-int of type 'float'` | Intentaste multiplicar una lista por un número (eso solo funciona con NumPy, lección P2) |
| `KeyError: 'radio'` | Clave que no existe en el diccionario |
| `IndexError: list index out of range` | Pediste un elemento más allá del final de la lista |

## Ejercicios

!!! example "Ejercicio 1. Conversiones"
    PlanetHunter midió 10 583 ppm para WASP-18 b. Escribe un script que muestre ese valor como fracción y como porcentaje.

    ??? success "Ver respuesta"
        ```python
        prof_ppm = 10_583
        fraccion = prof_ppm / 1e6
        pct = prof_ppm / 1e4        # 1 % = 10 000 ppm
        print(f"{fraccion:.6f}  {pct:.4f} %")
        ```
        Salida: `0.010583  1.0583 %`. Un tránsito de cerca del 1 %, típico de un Júpiter caliente frente a una estrella parecida al Sol.

!!! example "Ejercicio 2. Función de clasificación"
    Escribe la función `clasifica(prof_ppm, rs_rsun)` que use `radio_planeta` y devuelva el texto de la clase de tamaño (usa el `if` de la sección "Decisiones"). Pruébala con WASP-18 b (10 583 ppm, 1,3466 R☉) y con una caída de 40 000 ppm en una estrella de 1,5 R☉.

    ??? success "Ver respuesta"
        ```python
        from transito import radio_planeta


        def clasifica(prof_ppm: float, rs_rsun: float) -> str:
            """Clase de tamaño a partir de la profundidad (ppm) y de R* (R_sol)."""
            rp = radio_planeta(prof_ppm, rs_rsun)
            if rp < 4:
                return f"{rp:.1f} R_tierra: rocoso a mini-Neptuno"
            elif rp < 8:
                return f"{rp:.1f} R_tierra: tamaño de Neptuno"
            elif rp <= 20:
                return f"{rp:.1f} R_tierra: gigante"
            return f"{rp:.1f} R_tierra: demasiado grande, sospecha de una binaria"


        print(clasifica(10_583, 1.3466))   # 15.1 R_tierra: gigante
        print(clasifica(40_000, 1.5))      # 32.7 R_tierra: demasiado grande...
        ```
        El segundo caso daría un "planeta" de casi 33 radios terrestres, tres veces Júpiter. Es lo que sospecha la prueba `radius` del vetting: probablemente una estrella pequeña eclipsando a otra (lección B4).

!!! example "Ejercicio 3. A la caza de aliases"
    Una búsqueda devolvió estos períodos para la misma estrella: `[0.9416, 1.8832, 0.4708, 2.8248]`. Usa un bucle para dividir cada uno por el primero y di cuáles son **aliases** (múltiplos o fracciones del período verdadero).

    ??? success "Ver respuesta"
        ```python
        periodos = [0.9416, 1.8832, 0.4708, 2.8248]
        base = periodos[0]
        for p in periodos:
            razon = p / base
            print(f"{p:.4f} d  ->  {razon:.2f} x el primero")
        ```
        Las razones son 1,00, 2,00, 0,50 y 3,00. Los tres últimos son aliases: $2P$, $P/2$ y $3P$. Picos así aparecen en el periodograma (lección M3), y el crossmatch de PlanetHunter prueba esas razones al comparar una señal con planetas conocidos.

## Checklist de la lección

- [ ] Creé variables de cada tipo y las comprobé con `type()`
- [ ] Convertí una profundidad entre fracción, ppm y porcentaje
- [ ] Usé una lista y un diccionario con datos de una estrella
- [ ] Escribí un bucle que calcula las profundidades de varios planetas
- [ ] Escribí las funciones `profundidad_ppm` y `radio_planeta` con docstring y unidades
- [ ] Importé mis funciones desde un módulo `transito.py`
- [ ] Resolví los tres ejercicios

## Para ir más allá

- Curso em Vídeo — Python, mundos 1 y 2 (Gustavo Guanabara). Cubre con calma todo lo de esta lección, con ejercicios corregidos en video (en portugués).
- Tutorial oficial de Python, que tiene traducción al español en el sitio docs.python.org. Bueno para consultar un tema específico, como los diccionarios.
- Sección sobre el método de tránsito en el sitio de la NASA ([science.nasa.gov/exoplanets](https://science.nasa.gov/exoplanets/)). Para repasar la física detrás de las cuentas que programaste.
