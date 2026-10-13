# Advanced level: think like someone who builds and publishes

<p class="meta">Advanced level · about 16 weeks · 4 to 6 hours per week</p>

You arrive here knowing what a transit is, how to read a periodogram, why SNR 7.1 is a reasonable limit and what each vetting test looks for. This level changes your point of view. Until now you learned to **use** and **interpret** PlanetHunter. From here on you will learn to **question** its choices, read the papers that justify them, measure the effect of a change and take a candidate all the way to the scientific community.

!!! abstract "By the end of this level you will be able to"
    - Read a methods paper (BLS, TLS, Robovetter, triceratops, ExoMiner) and say what it does, what it assumes and where it fails.
    - Compare PlanetHunter's vetting with that of the Kepler and TESS missions and point out what is missing.
    - Interpret a false positive probability (FPP) without treating it as absolute truth.
    - Propose a change to a limit in `config/thresholds.yaml`, measure before and after and write up the result with a confidence interval.
    - Put together a complete CTOI submission package, with a literature search and honest wording.

## Who this level is for

For anyone who has finished the [intermediate level](../intermediate/index.md) and the programming track up to lesson P3. You will run commands, edit a configuration file and read Python code. You do not need to know how to write a pipeline from scratch, but you do need to be able to follow a 50-line function and understand what goes in and what comes out.

The math goes up one step. You will meet sums, chi-squared, conditional probability and Bayes' theorem. Every formula comes with an explanation in words and a worked numerical exercise. If an equation stops you, read the sentence right after it, do the exercise and come back.

## The lessons

| Lesson | Weeks | In one sentence |
|---|---|---|
| [A1. Detection algorithms](a1-detection-algorithms.md) | 1–3 | The statistics behind BLS and TLS, the trade-offs of detrending and why single transits are the most promising niche. |
| [A2. How missions do vetting](a2-mission-vetting.md) | 3–6 | Data Validation, the Robovetter, the TOI catalog and the eclipsing binary catalog, compared side by side with PlanetHunter's tests. |
| [A3. False positive probability](a3-false-positive-probability.md) | 6–8 | Bayesian reasoning, vespa and triceratops, the false positive scenarios and the real case of WASP-100 b. |
| [A4. Machine learning](a4-machine-learning.md) | 8–11 | Neural networks that classify signals, labels, leakage, calibration and why, in this project, ML only reorders. |
| [A5. Measuring the system](a5-measuring-the-system.md) | 11–13 | Recall, completeness, injection-recovery, the Wilson interval and the before/after method for changing a limit. |
| [A6. From candidate to community](a6-from-candidate-to-community.md) | 13–16 | ExoFOP, CTOI submission, the TESS follow-up program, literature search and ethics. |
| [Self-assessment](assessment.md) | 16 | Ten open questions with model answers. |

The order matters. A1 and A2 give you the vocabulary for A3. A5 depends on everything before it, because measuring only makes sense when you know what you are measuring. A6 closes the loop and uses all of it.

## How to read a scientific paper

At this level you will read about ten papers. Nobody reads a technical paper from start to finish the first time, not even the people who wrote it. The technique below is a variation of the "three-pass" method described by Keshav (2007).

**First pass (15 to 20 minutes): decide whether it is worth reading.**

1. Read the **title** and the **abstract**. Write down in one sentence: what problem does the paper solve?
2. Jump to the **conclusion** (or "Summary", "Discussion"). Write down: what do they claim to have achieved?
3. Look at **all figures and tables**, with their captions. In exoplanet papers, the figures carry half the content: light curves, periodograms, completeness histograms.
4. Read the section titles.

At the end, you should be able to say what the paper does without having read a single equation.

**Second pass (1 to 2 hours): understand the argument.**

1. Read the whole **introduction**. It says what already existed and which gap the paper fills.
2. Read the **methods** section, skipping derivations. Stop at each equation and ask: what goes in, what comes out, in what unit?
3. Read the **results** with the figures beside you.
4. Mark the references that show up many times. They are the foundation of the field.

**Third pass (when you need it): rebuild.**

Only when you are going to implement something or disagree with the paper. Redo the main calculations, reproduce a figure with public data and look for hidden assumptions ("we assume a circular orbit", "we ignore correlated noise").

!!! tip "Where to find the papers"
    Almost every paper in the field has a free version on arXiv (arxiv.org, section astro-ph.EP for planets). ADS (ui.adsabs.harvard.edu) is astronomy's search engine: type author and year, for example `author:"Kovacs" year:2002`, and it shows the link to arXiv and to the journal. Lesson A6 teaches you how to use ADS for a literature search on a target.

!!! note "Reading notebook"
    For each paper, write half a page with: (1) the problem; (2) the method in three sentences; (3) the main number or figure; (4) one assumption the paper makes; (5) where this shows up in PlanetHunter, or why it does not. This notebook will be the basis of your self-assessment answers.

## Suggested pace

Each lesson has required reading (the papers listed in the [references](../references.md)), worked exercises and hands-on practice with the tool. A typical week:

- 2 hours of reading (first and second passes of one paper).
- 1 hour with the lesson on this site and its exercises.
- 1 to 2 hours of practice: run a command, open a dossier, change a parameter.
- 30 minutes for the reading notebook and the review notebook.

If a week goes less well, do not skip the practice. Reading about centroids without ever looking at a difference image does not stick.

## How to know you are done

You have finished the advanced level when you can, without help:

1. Explain to a friend, with a formula and a drawing, why BLS maximizes $s^2/[r(1-r)]$ and what that has to do with SNR.
2. Take a recent TESS planet validation paper and list every vetting test it uses, marking which ones PlanetHunter has and which it does not.
3. Look at the triceratops output for a candidate and say which scenario dominates, what would make it less likely and which observation would help.
4. Make a change in `config/thresholds.yaml`, run the benchmark before and after, compute the Wilson interval and write a one-page report in `docs/benchmarks/`.
5. Put together the submission package for a P1 candidate (even a hypothetical one), with ephemeris, uncertainties, notes, literature search and a list of citations.
6. Pass the [self-assessment](assessment.md) comfortably.

After that, the next step is no longer a course. It is contributing: reviewing candidates carefully, opening issues when a number looks wrong and, one day, submitting a CTOI that survives the scrutiny of the TESS team.
