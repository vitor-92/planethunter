# A4. Machine learning for triage

<p class="meta">Advanced level · weeks 8–11 · about 15 hours</p>

!!! abstract "In this lesson you will learn"
    - How Shallue & Vanderburg (2018) used a neural network to classify Kepler signals, with global and local views.
    - What ExoMiner (Valizadegan et al. 2022) added and how it led to the validation of 301 planets.
    - Where training labels come from and why they are imperfect.
    - What leakage between training and test sets is and why the split must be done by star.
    - What calibration is and why a score of 0.9 does not always mean 90 %.
    - Why, in PlanetHunter, ML only reorders the queue and never vetoes, and how your reviews become labels.

In the project's first real slice, with 2,164 stars from sector 69, the funnel produced 648 `NEW` signals, 11 that passed basic vetting and 3 P2 candidates after deep vetting. In a full sector (about 20,000 stars), and later in full-frame images (hundreds of thousands), the human review queue grows until it becomes unmanageable. This is where machine learning (ML) comes in: **sorting the queue** so that human time goes first to what is most worth it.

## 1. The idea: teaching by example

An ML classifier learns a function "input data → probability of being a planet" from labeled examples. Instead of you writing rules ("if odd/even > 3σ, reject"), you show it thousands of cases with the right answer and the algorithm finds the patterns. The advantage: it can combine weak clues that no single rule would catch. The risk: it learns **any** pattern that separates the labels, including patterns that have nothing to do with physics.

## 2. Shallue & Vanderburg (2018): global and local views

Shallue & Vanderburg (2018), *The Astronomical Journal* 155, 94, trained a **convolutional neural network** (CNN, a type of network that learns local patterns in sequences or images) on Kepler signals. The labels came from human classifications of Kepler TCEs: planet candidate, astrophysical false positive or non-transit.

The paper's most copied contribution is the **input representation**. Instead of the whole light curve, the network receives two views of the curve folded on the period:

| View | What it shows | Size | What it is for |
|---|---|---|---|
| **Global** | The whole orbit, from phase −0.5 to 0.5 | 2,001 bins | Seeing a secondary eclipse, out-of-transit variations, the overall shape |
| **Local** | Only the neighborhood of the transit, a few durations on each side | 201 bins | Seeing details of the shape: flat bottom (U) or V, ingress and egress |

Each view is normalized (median at zero, depth at −1), which makes the network compare **shapes**, not absolute depths. The two convolutional branches join in final layers that produce a number between 0 and 1.

The result became famous for a concrete reason: applied to Kepler stars with several known planets, the network pointed to weak signals that, after analysis, led to the validation of **Kepler-90 i** and **Kepler-80 g**. Note the sequence: the network **suggested**; the validation came from later analysis.

Yu et al. (2019), *AJ* 158, 25, adapted the same architecture to TESS. The adaptation was not trivial: TESS has fewer transits per signal, larger pixels and a different set of systematics. A model trained on Kepler does not work directly on TESS.

## 3. ExoMiner: giving the network what the expert looks at

Valizadegan et al. (2022), *The Astrophysical Journal* 926, 120, presented **ExoMiner**. The idea: a human expert does not decide only from the shape of the transit. They look at the centroid, the odd/even depths, the secondary, the star's parameters, the Data Validation diagnostics (lesson A2). ExoMiner gives the network **one branch for each type of evidence**:

- Global and local views of the flux (as in Shallue & Vanderburg).
- Views of the **centroid** (motion during the transit).
- Views of **odd and even** transits separately.
- A view around the **secondary eclipse**.
- **Stellar parameters** and **scalar statistics** from DV.

Two advantages. First, better performance than flux-only models, because the network sees the diagnostics that separate background binaries and eclipses. Second, **explainability**: you can see which branch weighed most in the decision ("rejected mainly because of the centroid"), which helps a human decide whether to trust it.

With ExoMiner, the authors validated **301 new Kepler planets**. Validation required a very high probability and extra checks, in the same spirit as the statistical validation of lesson A3. ML came in as a way of estimating the likelihood, not as a substitute for reasoning.

## 4. Labeled data: where it comes from and why it is imperfect

The project plan (the `ml-engineer` agent) defines the sources:

| Label | Source | Known problem |
|---|---|---|
| Positive | TOIs with TFOPWG CP/KP disposition | Few; they tend to be deep and around bright stars |
| Synthetic positive | Transits injected with `batman` into real curves (lesson A5) | Too perfect: no systematics correlated with the transit |
| Negative | TFOPWG FP/FA | Few and heterogeneous |
| Negative | TESS binary catalog | **Contains confirmed hot Jupiters** (lesson A2) |
| Negative | Noise signals rejected by the vetting itself | Label given by the system itself: the model learns to imitate the vetting |

Three lessons:

1. **Label noise is the rule.** The binary catalog has planets. "PC" is not a planet. Some old FPs have been revised. Before training, cross-check the labels with the same priority as the crossmatch: a confirmed planet beats the binary catalog.
2. **Imbalance.** There are many more negatives than positives. Accuracy is a useless metric here: a model that says "not a planet" for everything is right 99 % of the time. Use recall at fixed precision and the area under the precision-recall curve (AUC-PR).
3. **Circularity.** If the negatives come from the vetting itself, the model learns to reproduce the vetting, including its mistakes. It will not find what the vetting misses.

## 5. Leakage between training and test sets

**Leakage** is when information from the test set somehow gets into training. The result is a measured performance that looks great and collapses in real use.

In exoplanets, the most common form is **the same star in both sets**:

- A star observed in 10 sectors produces the same signal 10 times. If the split is random **by signal**, 8 go to training and 2 to test. The network "recognizes" the star (the noise level, the variability, the exact depth) and gets the test right without having learned anything general.
- A star with several planets: the signals share the same light curve.
- Injections into the same curve that contains a real signal.

The project's rule is explicit: **split by star, never by signal**. All rows for the same TIC go into the same set. To measure real generalization, it is also worth splitting by **sky region** or by **sector**, because instrument systematics vary with camera and epoch.

## 6. Calibration: does the score mean what it says?

A classifier returns a number between 0 and 1. That does **not** make it a probability. A model is **calibrated** when, among all signals that get a score near 0.9, about 90 % really are in the positive class.

Modern neural networks tend to be **overconfident** (Guo et al. 2017): scores near 0 or 1 more often than they should be. To check:

1. Set aside a validation set (by star!).
2. Group the signals by score range (0–0.1, 0.1–0.2, ...).
3. In each range, compare the mean score with the real fraction of positives. The plot of this is the **reliability diagram**.

To correct it, the plan uses **temperature scaling**: dividing the network's output (before the function that maps it to 0 to 1) by a constant tuned on the validation set. It is simple, and it does not change the order of the signals, only their values.

Why it matters in the project: the ML score goes into the **novelty score**, which multiplies the vetting confidence and the novelty in the literature. Multiplying uncalibrated probabilities produces meaningless numbers.

A summary measure is the **Brier score**: the mean of $(p_i - y_i)^2$, where $p_i$ is the score and $y_i$ the label (0 or 1). The lower, the better. It penalizes both ordering errors and calibration errors.

## 7. Why, in the project, ML only reorders

The rule is in the `ml-engineer` agent: **the ML score never vetoes on its own; it only reorders and lowers priority. Recall on known TOIs must not drop.** Four reasons:

1. **New planets are outside the training distribution.** The labels come from TOIs, which are usually deep, around bright stars and with short periods. The project's niches (faint stars, long periods, M dwarfs) are exactly where there are fewest examples. A classifier tends to give a low score to what it has never seen, and what it has never seen is what you are looking for.
2. **Asymmetric error.** Reviewing a false positive costs a few minutes. Vetoing a real planet costs the planet: nobody looks again.
3. **Deterministic vetting is auditable.** Every veto has a test, a number and a commented limit in `config/thresholds.yaml`, with a before-and-after benchmark. A neural network veto is hard to explain and to fix.
4. **ML does not see what the search does not detect.** It acts after the search. If the detrending ate the transit, no classifier will recover it. Improving the search is a job for injection-recovery (lesson A5), not for ML.

The plan's goal for phase 5 is consistent with this: ML should **cut by at least 5 times the number of candidates you need to review first**, while keeping recall. The rest stay in the queue, further down.

How the code enforces it (`alerts/severity.py`). The model's probability, `p_rank`, enters severity only through two thresholds, both chosen by measuring how many known planets they keep in cross-validation: the **P2 threshold** keeps 90 % of them, and the **P1 threshold** is the lowest one with at most 1 % false positives that still keeps at least 70 % of the planets. A signal below the P1 threshold drops to P2, whatever its score. A high `p_rank` never raises a signal: P1 still needs a deterministic score of at least 0.8. The only "rescue" is limited: a signal that failed the deterministic vetting without a veto can reach P2, never more. The 2026-10-10 audit found that an earlier version let the model replace the score, and two sector 107 signals went from P2 to P0 and P1 because of the model alone.

**Two probabilities, two uses.** A probability learned on a training set in which planets are common (known planets make up a large share of the examples) is a probability **under that mix**. Among new signals, planets are much rarer, so the same signal has a much lower real chance of being a planet. The project therefore stores two numbers: `p_rank` (the calibrated model output, used for ranking and for the thresholds above) and `p_abs`, the same value corrected with Bayes' rule to an assumed fraction of planets among new signals (5 %, `severity.new_prior`):

$$
\text{logit}(p_\text{abs}) = \text{logit}(p_\text{rank}) + \text{logit}(0.05) - \text{logit}(\text{training fraction}) .
$$

The 5 % is an assumption, not a measurement. That is why `p_abs` is shown but never used to decide anything.

## 8. Your reviews become labels

Every time you run

```bash
uv run planethunter review <signal_id> rejected --reason eb --note "secondary visible at phase 0.5"
```

the database records `review_status` and `review_note` in the `candidates` table. The possible statuses are `approved`, `rejected` and `follow_up`. Rejections require a reason among `eb`, `blend`, `systematic`, `noise`, `already_known` and `other`.

These decisions are the project's **most valuable labels**, because they come from exactly the distribution that matters: signals that went through all the vetting and reached the queue. No public catalog has this kind of example. This is the basis of the plan's **active learning**: the model asks for human review of the cases it is least sure about, and each review improves the next training run.

For your reviews to work as labels:

- **Be consistent** with the reason. "eb" and "blend" teach the model different things.
- **Write the note with the evidence**, not the conclusion: "odd depth 4,100 ppm, even 2,300 ppm" is worth more than "looks like an EB".
- **Understand what the label means.** "approved" means "survived the human look and deserves follow-up", not "is a planet". A model trained on this learns to predict your decision, with your biases.
- **Use `follow_up` when you do not know.** A wrong label given with conviction is worse than an honest label of uncertainty.

!!! tip "In the tool"
    - `uv run planethunter candidates` lists the queue; `uv run planethunter dossier <signal_id>` generates the dossier; `uv run planethunter review ...` records the decision.
    - The `review_status`, `review_note` and `reviewed_at` columns live in the `candidates` table of `data/planethunter.duckdb`.
    - A first, simple step already exists: `uv run planethunter calibrate` trains a logistic regression on the basic vetting results of known signals. Positives: confirmed planets. Negatives: cataloged false positives and, when available, every signal from the inverted and scrambled null runs (lesson A1), which are false alarms by construction. The regularization is chosen by cross-validation grouped by star, the probabilities are calibrated with Platt scaling on out-of-fold predictions, and the model is saved in `data/models/vetting_lr.json` with a `model_version` and the runs it came from. The queue then shows `p_rank` and `p_abs`, and severity uses `p_rank` only to lower priority.
    - The neural network classifier described in this lesson is **not implemented yet**. It is phase 5 of the plan. What you review today is tomorrow's training set.

!!! example "Exercise 1. Find the leak"
    Someone builds a set of 3,000 signals from 1,200 stars, shuffles the signals and splits 80 % for training and 20 % for test. The model reaches an AUC-PR of 0.97 on the test set. Applied to a new sector, the queue sorted by the model looks almost random. What happened and how do you fix it?

    ??? success "Show answer"
        1. With 3,000 signals from 1,200 stars, many stars have several signals (several sectors, several planets, search iterations). Shuffling by signal put the same star in both training and test.
        2. The model learned to recognize stars (noise level, variability, depth), not planet-versus-binary patterns. The test measured memory.
        3. Fix: group by TIC and draw **stars** for training and test. Even better: hold out whole sectors for the test, to also measure the change in systematics.
        4. Expected: the AUC-PR on the corrected test drops, and now reflects the real performance.

!!! example "Exercise 2. Is the model calibrated?"
    (a) In a validation set, 200 signals got a score between 0.85 and 0.95. Of these, 120 are planets. Is the model calibrated in this range? (b) Compute the Brier score for four signals with scores 0.9, 0.9, 0.2, 0.6 and labels 1, 0, 0, 1.

    ??? success "Show answer"
        (a) Mean score ≈ 0.9; real fraction $120/200 = 0.6$. The model is **overconfident** in this range: it promises 90 % and delivers 60 %. Temperature scaling should bring these scores close to 0.6.

        (b) Squared errors: $(0.9-1)^2 = 0.01$; $(0.9-0)^2 = 0.81$; $(0.2-0)^2 = 0.04$; $(0.6-1)^2 = 0.16$. Sum $1.02$. Brier $= 1.02/4 = 0.255$. The second signal, a negative with a score of 0.9, accounts for almost all of the error.

!!! example "Exercise 3. Reorder or veto?"
    The queue has 200 candidates, of which 4 deserve follow-up (you will only know later). You have time to review 40 per month. The model puts 3 of the 4 among the top 40 and the fourth at position 150. Compare two policies: (A) veto everything below position 40; (B) reorder the queue and keep reviewing in the following months.

    ??? success "Show answer"
        - Policy A: 5 times less review (40 of 200), but the fourth candidate is **lost forever**. Recall 3/4 = 75 %. It breaks the rule "recall must not drop".
        - Policy B: in the first month you find 3 of the 4, the same time saving as policy A. The fourth shows up in the fourth month. Final recall 100 %.
        - ML delivers the main benefit (finding the best first) without the irreversible cost. That is the reason for the project's rule. And the fourth candidate, with a low score and a positive human decision, is exactly the example that teaches the next training run the most.

## Lesson checklist

- [ ] I read Shallue & Vanderburg (2018) and can explain the global and local views.
- [ ] I read Valizadegan et al. (2022) and can list the branches of ExoMiner.
- [ ] I can point out three problems with the labels available to the project.
- [ ] I can explain leakage and why the split is by star.
- [ ] I can read a reliability diagram and compute the Brier score.
- [ ] I can give four reasons why ML only reorders.
- [ ] I reviewed at least 10 candidates with a reason and an evidence-based note.

## Going further

- Shallue & Vanderburg (2018), *The Astronomical Journal* 155, 94. The paper that popularized the global and local views; read the data representation section and the results section.
- Valizadegan et al. (2022), *The Astrophysical Journal* 926, 120. ExoMiner; read the architecture and the discussion of explainability.
- Yu et al. (2019), *The Astronomical Journal* 158, 25. The adaptation to TESS; shows what changes when the instrument changes.
- Armstrong et al. (2021), *Monthly Notices of the RAS* 504, 5327. Validation of Kepler planets with several ML algorithms combined with calibrated probabilities; a great counterpoint to ExoMiner.
- Guo et al. (2017), "On Calibration of Modern Neural Networks", *Proceedings of ICML*. Shows that deep networks are overconfident and introduces temperature scaling.
- Ivezić, Connolly, VanderPlas & Gray, *Statistics, Data Mining, and Machine Learning in Astronomy* (Princeton University Press). A reference book that connects statistics and ML to real astronomical problems.
