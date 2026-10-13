# P1. Python basics

<p class="meta">Programming track · alongside the basic level · about 10 hours</p>

!!! abstract "In this lesson you will learn"
    - Store numbers and text in variables and know the type of each one.
    - Organize data in lists (periods) and dictionaries (the parameters of a star).
    - Repeat calculations with `for` loops and make decisions with `if`.
    - Write functions that compute the transit depth and the planet radius.
    - Split your code into modules and import them.

Before you start, set up your computer as explained on the [track page](index.md). Create each example as a `.py` file in the `exoplanet-studies` folder and run it with `uv run python file_name.py`.

## Variables and types

A **variable** is a name that points to a value. Think of a label stuck on a box: the label is the name, the contents are the value.

```python
period_days = 3.7             # number with decimals (float)
n_transits = 7                # whole number (int)
star_name = "Pi Mensae"       # text (str, from "string")
has_transit = True            # true or false (bool)

print(period_days, n_transits, star_name, has_transit)
print(type(period_days))      # <class 'float'>
```

The `=` sign is not the "equals" of math. It means "store the value on the right under the name on the left". Everything after `#` is a **comment**: Python ignores it; it is there for you.

Practical rules for names: only letters without accents, digits and `_`; do not start with a digit; use names that state the unit. `radius_rsun` is better than `r`. PlanetHunter follows this rule: `period_days`, `depth_ppm`, `duration_hours`.

### Arithmetic

```python
sun_radius_km = 696_000      # the _ only separates thousands to make it easier to read
earth_radius_km = 6_371

ratio = earth_radius_km / sun_radius_km   # division
depth = ratio ** 2                        # ** is "to the power of"
print(depth)                              # 8.379...e-05
```

The result `8.379e-05` is scientific notation: $8.379 \times 10^{-5}$. It is the fraction of the Sun's light that Earth blocks. This comes from the rule in [lesson B2](../basic/b2-transit-method.md):

$$\delta \approx \left(\frac{R_p}{R_\star}\right)^2$$

where $\delta$ is the depth, $R_p$ the planet's radius and $R_\star$ the star's radius.

### Converting to ppm and percent

**ppm** means parts per million. To go from a fraction to ppm, multiply by one million. For percent, by one hundred.

```python
depth_ppm = depth * 1e6     # 1e6 = 1,000,000
depth_pct = depth * 100
print(f"Earth: {depth_ppm:.0f} ppm = {depth_pct:.4f} %")
# Earth: 84 ppm = 0.0084 %
```

The `f` before the quotes creates an **f-string**: whatever is inside curly braces is computed and inserted into the text. The `:.0f` says "show it with zero decimal places".

!!! warning "Pitfall: decimal comma"
    In Python, `3,7` is not the number three point seven. It is a pair of numbers, 3 and 7. Always use a point: `3.7`.

## Lists

A **list** holds several values in order, between square brackets.

```python
periods_days = [0.94, 3.7, 6.27, 11.4]

print(len(periods_days))      # 4 elements
print(periods_days[0])        # 0.94  (counting starts at ZERO)
print(periods_days[-1])       # 11.4  (index -1 is the last one)
print(periods_days[1:3])      # [3.7, 6.27]  (slice: from 1 up to, but not including, 3)

periods_days.append(25.0)     # adds to the end
print(min(periods_days), max(periods_days), sum(periods_days))
print(sorted(periods_days, reverse=True))
```

Counting from zero looks strange at first. Think of the index as "how many steps to walk from the start".

## Dictionaries

A **dictionary** holds key-value pairs, between curly braces. It is great for describing something with several attributes, like a star.

```python
star = {
    "name": "WASP-18",
    "tic_id": 100100827,
    "radius_rsun": 1.35,   # radius in solar radii
    "tmag": 8.83,          # brightness in the TESS band (smaller = brighter)
}

print(star["radius_rsun"])         # 1.35
star["teff_k"] = 6226              # adds a new key
for key, value in star.items():
    print(key, "=", value)
```

The values for WASP-18 come from the file PlanetHunter wrote for sector 69. You will open that file in [lesson P3](p3-lightkurve-in-practice.md).

## Decisions with `if`

```python
rp_rearth = 15.1   # planet radius in Earth radii

if rp_rearth < 4:
    size_class = "rocky to mini-Neptune"
elif rp_rearth < 8:
    size_class = "Neptune-sized"
elif rp_rearth <= 20:
    size_class = "giant"
else:
    size_class = "too big: probably not a planet"

print(size_class)
```

Notice the **indentation**: the 4 spaces at the start of the lines tell Python what is "inside" each `if`. In Python, indentation is not decoration, it is a rule. The size ranges follow the table for reading candidates in the project's guide.

## `for` loops

A **loop** repeats a block for each element of a list.

```python
sun_radius_km = 696_000
planets_km = {"Earth": 6_371, "Neptune": 24_622, "Jupiter": 69_911}

for name, radius_km in planets_km.items():
    d_ppm = (radius_km / sun_radius_km) ** 2 * 1e6
    print(f"{name:8s} {d_ppm:8.0f} ppm")
```

Output:

```text
Earth          84 ppm
Neptune      1251 ppm
Jupiter     10090 ppm
```

Compare with the table in lesson B2 (84, ~1,300 and ~10,000 ppm). The guide rounds Neptune to 1,300.

To repeat a fixed number of times, use `range`:

```python
period = 0.9416      # days
t0 = 3182.758        # time of the first transit, in BTJD
for n in range(5):   # n = 0, 1, 2, 3, 4
    print(f"transit {n}: BTJD {t0 + n * period:.3f}")
```

**BTJD** is the day count TESS uses (days since a reference date). This calculation is an **ephemeris**: the prediction of when the next transits will happen.

## Functions

A **function** is a recipe with a name. You define it once and use it as many times as you like. It takes **parameters** (inputs) and gives back a result with `return`.

```python
RSUN_IN_REARTH = 109.1   # one solar radius is 109.1 Earth radii


def depth_ppm(rp_rearth: float, rs_rsun: float) -> float:
    """Transit depth in ppm. Rp in R_earth, R* in R_sun."""
    ratio = rp_rearth / (rs_rsun * RSUN_IN_REARTH)
    return ratio**2 * 1e6


def planet_radius(d_ppm: float, rs_rsun: float) -> float:
    """Planet radius in R_earth from the depth (ppm) and R* (R_sun)."""
    return (d_ppm / 1e6) ** 0.5 * rs_rsun * RSUN_IN_REARTH


print(depth_ppm(1.0, 1.0))        # Earth and the Sun: ~84 ppm
print(planet_radius(84, 1.0))     # back to ~1 R_earth
print(planet_radius(84, 0.2))     # same dip on a red dwarf: ~0.2 R_earth
```

Details:

- `rp_rearth: float` is a **type annotation**. It tells the reader that a number is expected. Python does not enforce it, but PlanetHunter uses it in every function.
- The text between `"""` right below the `def` is the **docstring**: it explains what the function does and the units.
- `planet_radius` is the inverse of `depth_ppm`: the square root of the depth (`** 0.5`) times the star's radius.

The last line shows an important idea from the basic level: the same 84 ppm dip on a star five times smaller corresponds to a planet five times smaller. That is why it is easier to find small planets around small stars.

!!! tip "In the tool"
    PlanetHunter does exactly the `planet_radius` calculation to show the `rp_rearth` column in the candidate list. It is in `src/planethunter/pipeline.py`, in the `candidate_table` function, written in SQL: `sqrt(fit_depth_ppm * 1e-6) * radius_rsun * 109.076`. Another example: in `src/planethunter/cli.py`, the `_parse_ints` function turns the text `"1,4,8"` from the `--sectors` option into the list `[1, 4, 8]`, using `split(",")` and a compact loop.

## Modules

A **module** is a `.py` file whose functions you reuse in other files with `import`.

Python comes with many modules. `math` has the square root, pi and other functions:

```python
import math

print(math.sqrt(10_583e-6))   # square root of 0.010583 = 0.1029
print(math.pi)
```

You can also make your own. Save the two functions above in a file called `transit.py`. In another file, in the same folder:

```python
from transit import planet_radius

rp = planet_radius(10_583, 1.3466)
print(f"WASP-18 b: {rp:.1f} Earth radii")   # 15.1
```

The numbers are real: 10,583 ppm is the depth PlanetHunter measured for WASP-18 b in sector 69, and 1.3466 R☉ is the star's radius in the TESS catalog.

Libraries like NumPy and Lightkurve are modules made by other people. You install them with `uv add` and import them the same way.

## Errors: read the last line

Making mistakes is part of it. When Python runs into a problem, it shows a **traceback**. The most useful information is on the **last line**:

| Message | Most common cause |
|---|---|
| `NameError: name 'period' is not defined` | Name mistyped, or variable created after it was used |
| `IndentationError` | Spaces at the start of the line are misaligned |
| `TypeError: can't multiply sequence by non-int of type 'float'` | You tried to multiply a list by a number (that only works with NumPy, lesson P2) |
| `KeyError: 'radius'` | A key that does not exist in the dictionary |
| `IndexError: list index out of range` | You asked for an element past the end of the list |

## Exercises

!!! example "Exercise 1. Conversions"
    PlanetHunter measured 10,583 ppm for WASP-18 b. Write a script that shows this value as a fraction and as a percentage.

    ??? success "Show answer"
        ```python
        d_ppm = 10_583
        fraction = d_ppm / 1e6
        pct = d_ppm / 1e4        # 1 % = 10,000 ppm
        print(f"{fraction:.6f}  {pct:.4f} %")
        ```
        Output: `0.010583  1.0583 %`. A transit of about 1 %, typical of a hot Jupiter in front of a Sun-like star.

!!! example "Exercise 2. A classification function"
    Write the function `classify(d_ppm, rs_rsun)` that uses `planet_radius` and returns the text of the size class (use the `if` from the "Decisions" section). Test it with WASP-18 b (10,583 ppm, 1.3466 R☉) and with a 40,000 ppm dip on a 1.5 R☉ star.

    ??? success "Show answer"
        ```python
        from transit import planet_radius


        def classify(d_ppm: float, rs_rsun: float) -> str:
            """Size class from the depth (ppm) and R* (R_sun)."""
            rp = planet_radius(d_ppm, rs_rsun)
            if rp < 4:
                return f"{rp:.1f} R_earth: rocky to mini-Neptune"
            elif rp < 8:
                return f"{rp:.1f} R_earth: Neptune-sized"
            elif rp <= 20:
                return f"{rp:.1f} R_earth: giant"
            return f"{rp:.1f} R_earth: too big, suspect a binary"


        print(classify(10_583, 1.3466))   # 15.1 R_earth: giant
        print(classify(40_000, 1.5))      # 32.7 R_earth: too big...
        ```
        The second case would give a "planet" of almost 33 Earth radii, three times Jupiter. That is what the vetting's `radius` test is suspicious of: probably a small star eclipsing another one (lesson B4).

!!! example "Exercise 3. Hunting aliases"
    A search returned these periods for the same star: `[0.9416, 1.8832, 0.4708, 2.8248]`. Use a loop to divide each one by the first and say which ones are **aliases** (multiples or fractions of the true period).

    ??? success "Show answer"
        ```python
        periods = [0.9416, 1.8832, 0.4708, 2.8248]
        base = periods[0]
        for p in periods:
            ratio = p / base
            print(f"{p:.4f} d  ->  {ratio:.2f} x the first")
        ```
        The ratios are 1.00, 2.00, 0.50 and 3.00. The last three are aliases: $2P$, $P/2$ and $3P$. Peaks like these show up in the periodogram (lesson M3), and PlanetHunter's crossmatch tests these ratios when comparing a signal with known planets.

## Lesson checklist

- [ ] I created variables of each type and checked them with `type()`
- [ ] I converted a depth between fraction, ppm and percent
- [ ] I used a list and a dictionary with a star's data
- [ ] I wrote a loop that computes the depths of several planets
- [ ] I wrote the `depth_ppm` and `planet_radius` functions with a docstring and units
- [ ] I imported my functions from a `transit.py` module
- [ ] I solved the three exercises

## Going further

- Curso em Vídeo — Python, worlds 1 and 2 (Gustavo Guanabara). Covers everything in this lesson calmly, with exercises solved on video (in Portuguese).
- The official Python tutorial, on docs.python.org. Good for looking up a specific topic, such as dictionaries.
- The section on the transit method on NASA's website ([science.nasa.gov/exoplanets](https://science.nasa.gov/exoplanets/)). To review the physics behind the calculations you programmed.
