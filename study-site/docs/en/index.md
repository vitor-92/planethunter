# Planet Hunters

A course for people who have never studied astronomy and want to truly understand how we search for planets outside the Solar System, and how **PlanetHunter** works: a tool that runs this search on public data from the TESS space telescope.

!!! abstract "What you will be able to do"
    - Explain how a small dip in a star's brightness reveals a planet.
    - Tell a planet apart from a double star, from a neighbor star contaminating the signal and from a telescope glitch.
    - Read a candidate dossier and decide, with good judgment, whether it deserves attention.
    - Run analyses in Python with real TESS data.
    - Understand each design decision in PlanetHunter and measure the effect of changing it.

## How the course is organized

<div class="course-grid" markdown>

<div class="course-card" markdown>
### Basic level
~6 weeks. Stars, planets, the transit method, TESS and why almost every signal is false.

[Start](basic/index.md)
</div>

<div class="course-card" markdown>
### Intermediate level
~10 weeks. Signal statistics, transit physics, periodograms, Python with real data and vetting in practice.

[See lessons](intermediate/index.md)
</div>

<div class="course-card" markdown>
### Advanced level
~16 weeks. Algorithms, how missions do vetting, false positive probability, machine learning, benchmarks and submission.

[See lessons](advanced/index.md)
</div>

<div class="course-card" markdown>
### Programming track
Alongside the levels. Python from scratch up to Lightkurve and the PlanetHunter database.

[See track](programming/index.md)
</div>

</div>

Beyond the lessons: an [interactive transit simulator](lab/transit-simulator.md), a [hands-on PlanetHunter manual](lab/using-planethunter.md), the [glossary](glossary.md) and the [references](references.md).

## Your progress

Each lesson ends with a checklist. Tick the items as you finish them: the site remembers what you ticked **in this browser** (nothing is sent anywhere).

<div id="progresso" markdown="0"></div>

## Get the code

PlanetHunter is open source ([MIT License](https://github.com/vitor-92/planethunter/blob/main/LICENSE)). The tool, this course and all the documentation live in one repository:

**[github.com/vitor-92/planethunter](https://github.com/vitor-92/planethunter)**

```
git clone https://github.com/vitor-92/planethunter.git
cd planethunter
uv sync
uv run planethunter --help
```

The step-by-step installation and every command are in [Using PlanetHunter](lab/using-planethunter.md). Found a mistake in a lesson? Click the pencil at the top of the page to suggest a fix on GitHub.

## Where to start

1. Read [How to study](how-to-study.md) (5 minutes).
2. Open lesson [B1. The sky, stars and planets](basic/b1-sky-stars-planets.md).
3. Play with the [simulator](lab/transit-simulator.md) when you reach lesson B2.

!!! info "About the content"
    The course follows the PlanetHunter project's study plan and uses real examples from the first week of searches (TESS sectors 69 and 107, October 2026). When a number appears, it was measured, not made up.
