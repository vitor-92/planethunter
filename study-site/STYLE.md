# Lesson style guide (for content writers)

Online course "Planet Hunters", for a student **with no background in astronomy** who wants to understand the search for exoplanets and the PlanetHunter tool (code in this repository).

## Languages

The course exists in three languages, with the same structure and file names in each:

- `docs/en/` — English (default language, served at the site root)
- `docs/es/` — Spanish ("Cazadores de Planetas")
- `docs/pt/` — Brazilian Portuguese ("Caçadores de Planetas")

Rules:

- **Every new lesson must be added in all three languages**, with the same file name and path under `docs/en/`, `docs/es/` and `docs/pt/`, and listed in `mkdocs.yml` (the default `nav` for English plus the `nav` of each language in the `i18n` plugin).
- Any change to the content of a lesson (numbers, exercises, answers, links) must be made in all three versions.
- File and folder names are in English in all three languages (e.g. `basic/b2-transit-method.md`).
- Box titles and fixed labels ("In this lesson you will learn", "In the tool", "Exercise", "Show answer", "Lesson checklist", "Going further") are translated into the lesson's language; keep them consistent with the existing lessons in the same folder.

Mandatory sources to consult before writing:
- `docs/STUDY_PLAN.md` (structure, objectives and readings for each module; the course follows this plan)
- `docs/BEGINNERS_GUIDE.md` (explanation of the tool, glossary, real stories)
- `docs/benchmarks/2026-10-09-s0069-history.md` and `docs/benchmarks/2026-10-09-s0069-vetting.md` (real measured numbers)
- `config/thresholds.yaml` (current limits, each with a comment explaining why)

## Tone

- Short sentences, active voice, address the reader directly as "you" (in Portuguese, "você"; in Spanish, "tú").
- Explain every technical term the first time it appears in the lesson. Use everyday analogies.
- Scientific rigor: no invented numbers. Use the project's numbers (sector 69) for illustrations.
- Never call a candidate a "discovery". Vocabulary: signal, candidate, CTOI, TOI, validated planet, confirmed planet.
- No emojis.

## Structure of each lesson (.md file)

```markdown
# B2. The transit method

<p class="meta">Basic level · weeks 2–3 · about 4 hours</p>

!!! abstract "In this lesson you will learn"
    - objective 1
    - objective 2

## Section 1
Explanatory text...

## Section 2
...

!!! tip "In the tool"
    Where this concept shows up in PlanetHunter: command, column, dossier plot, vetting test.

!!! example "Exercise 1"
    Problem statement.

    ??? success "Show answer"
        Step-by-step solution.

## Lesson checklist

- [ ] item the student ticks off when done
- [ ] ...

## Going further

- Reference 1 (authors, year, journal or website). Explain in one sentence why to read it.
```

Formatting rules (MkDocs Material):
- Content inside admonitions (`!!!`, `???`) is indented with **4 spaces**. Nested admonition: 8 spaces.
- Box types: `abstract` (objectives), `note` (remark), `tip` (in the tool), `warning` (common pitfall), `example` (exercise), `success` (answer, always collapsible with `???`), `question` (question to think about), `info` (fun fact).
- Math: inline `$...$`, block `$$ ... $$` on its own line. Example: `$\delta \approx (R_p/R_\star)^2$`.
- Diagrams: ```` ```mermaid ```` blocks are allowed.
- Markdown tables are welcome for comparisons.
- Code: blocks with a language (```` ```python ````, ```` ```bash ````).
- Internal links: relative to the file, e.g. `[lesson B2](../basic/b2-transit-method.md)`. Link to the simulator: `../lab/transit-simulator.md`. Links stay within the same language folder.
- External links: only stable, well-known domains (nasa.gov, arxiv.org, adsabs.harvard.edu, zooniverse.org, lightkurve.github.io, docs.astropy.org, numpy.org, pandas.pydata.org, khanacademy.org (use the language edition when one exists, e.g. pt.khanacademy.org, es.khanacademy.org), exofop.ipac.caltech.edu, exoplanetarchive.ipac.caltech.edu). For papers, prefer citing authors, year, journal and volume; arXiv only when you know the identifier.
- Each lesson: 1,200 to 2,500 words, at least 2 exercises with answers, 1 "In the tool" box, a checklist and "Going further".
- `index.md` page of each level: introduction, objectives of the level, list of lessons with one sentence each, how long it takes, how to know you are done.
- `assessment.md` page of each level: the self-assessment questions from the plan (plus a few more, up to 10), each with `??? success "Show answer"`, and a passing criterion.
