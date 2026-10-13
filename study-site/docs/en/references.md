# References

The course's complete bibliography, organized by level and by topic. Each item has a sentence saying why it is worth your time. For papers, the citation gives authors, year, journal and volume; with that you can find any of them on ADS (ui.adsabs.harvard.edu) and, almost always, a free version on arXiv (arxiv.org).

!!! tip "How to read the papers on this list"
    The first time, read the abstract, the figures and the conclusion. Come back to the equations when you need them. The method is explained on the [advanced level index](advanced/index.md#how-to-read-a-scientific-paper).

## Books

- Tasker, E. (2017). *The Planet Factory*. Bloomsbury. High-quality popular science on the formation and diversity of planets; the best starting point for the basic level.
- Seager, S. (ed.) (2010). *Exoplanets*. University of Arizona Press. A reference book for the advanced level, with chapters written by the experts in each technique.
- Haswell, C. A. (2010). *Transiting Exoplanets*. Cambridge University Press. A textbook devoted to the transit method, with exercises; a bridge between the intermediate and advanced levels.
- Perryman, M. (2018). *The Exoplanet Handbook*, 2nd ed. Cambridge University Press. An encyclopedia of the field, to look things up when a paper cites something you do not know.
- Sivia, D. S. (2006). *Data Analysis: A Bayesian Tutorial*, 2nd ed. Oxford University Press. A short, clear introduction to the Bayesian reasoning used in lesson A3.
- Ivezić, Ž., Connolly, A. J., VanderPlas, J. T. & Gray, A. *Statistics, Data Mining, and Machine Learning in Astronomy*. Princeton University Press. Statistics and machine learning with astronomical examples and Python code.
- VanderPlas, J. (2016). *Python Data Science Handbook*. O'Reilly. NumPy, pandas, Matplotlib and scikit-learn in a single book; there is a free version online.

## Basic level

### The sky, planets and the transit method

- NASA, exoplanets website (science.nasa.gov/exoplanets). The introduction and "how we find" sections; visual explanations of the detection methods.
- The TESS mission page on NASA's website and the TESS guide at HEASARC (heasarc.gsfc.nasa.gov/docs/tess). What TESS observes, sectors, cameras and cadences.
- PlanetHunter's beginner's guide, in `docs/BEGINNERS_GUIDE.md` in the project repository. Explains the tool step by step, with a glossary and three real stories.
- PlanetHunter's study plan, in `docs/STUDY_PLAN.md`. The structure this course follows, with checklists per module.

### Practice

- Planet Hunters TESS (zooniverse.org). Classifying real light curves is the best eye training there is, and volunteers in the project have already had candidates promoted.

## Intermediate level

### Statistics for signals

- Khan Academy (khanacademy.org), statistics course. Descriptive statistics and the normal distribution, the basis of SNR and "sigma".
- Pont, F., Zucker, S. & Queloz, D. (2006). *Monthly Notices of the RAS* 373, 231. The paper that showed the effect of red noise on transits; the basis of the block error (`BlockNoise`) used in vetting.
- Hogg, D. W., Bovy, J. & Lang, D. (2010). "Data analysis recipes: Fitting a model to data", arXiv:1008.4686. A practical, opinionated guide to fitting models with statistical honesty.

### Transit physics

- Winn, J. N. (2010). "Transits and Occultations", arXiv:1001.2010. The classic text on geometry, duration, shape and secondary eclipse; sections 1 to 3 cover the intermediate level.
- Seager, S. & Mallén-Ornelas, G. (2003). *The Astrophysical Journal* 585, 1038. Analytic relations between transit shape, stellar density and period; the basis of the `duration` test.
- Mandel, K. & Agol, E. (2002). *The Astrophysical Journal* 580, L171. The analytic transit model with limb darkening used by almost every piece of software in the field.

### Periodograms

- Astropy documentation on Box Least Squares (docs.astropy.org, timeseries section). A practical BLS example in Python.
- Hippke, M. & Heller, R. (2019). *Astronomy & Astrophysics* 623, A39. The TLS used by PlanetHunter; at the intermediate level, the introduction and figures.
- VanderPlas, J. T. (2018). *The Astrophysical Journal Supplement Series* 236, 16. A teaching-oriented explanation of periodograms and aliases (Lomb-Scargle, in this case), useful for understanding false peaks.

### Python and TESS data

- *Curso em Vídeo — Python*, by Gustavo Guanabara, worlds 1, 2 and 3. A free course in Portuguese, from zero to intermediate.
- Introductory documentation for NumPy (numpy.org) and pandas (pandas.pydata.org), "getting started" sections. Arrays and tables, the foundation of all the project's code.
- Lightkurve tutorials (lightkurve.github.io). Downloading, cleaning, flattening and folding TESS light curves; the path to reproducing Pi Men c.

### Companion courses

- *Super-Earths and Life* (Harvard, edX platform). Accessible modules on the detection and characterization of exoplanets.
- *Astrobiology and the Search for Extraterrestrial Life* (University of Edinburgh, Coursera). Broader scientific context, also accessible.

## Advanced level

### How to read papers

- Keshav, S. (2007). "How to Read a Paper", *ACM SIGCOMM Computer Communication Review* 37. The three-pass method adapted on the advanced level index.

### A1. Detection algorithms

- Kovács, G., Zucker, S. & Mazeh, T. (2002). *Astronomy & Astrophysics* 391, 369. The original BLS paper; contains all the statistics in lesson A1.
- Hippke, M. & Heller, R. (2019). *Astronomy & Astrophysics* 623, A39. The full TLS, with equations and a comparison with BLS.
- Ofir, A. (2014). *Astronomy & Astrophysics* 561, A138. Optimal sampling of the period grid, used by TLS.
- Hippke, M. et al. (2019). *The Astronomical Journal* 158, 143. wotan and the comparison of detrending methods that justifies the biweight with a window of about three durations.
- Foreman-Mackey, D. et al. (2017). *The Astronomical Journal* 154, 220. celerite, for fast Gaussian processes on time series.
- Aigrain, S. & Foreman-Mackey, D. (2023). *Annual Review of Astronomy and Astrophysics* 61, 329. A review of Gaussian processes for astronomical time series; substantial reading for anyone who wants to test GPs in the project.
- Kipping, D. M. (2010). *Monthly Notices of the RAS* 408, 1758. The effects of integrating and binning points on the transit shape; helps you think about `bin_minutes`.
- Osborn, H. P. et al. (2016). *Monthly Notices of the RAS* 457, 2273. Single transits in K2 and estimating the period from a single event.

### A2. Mission vetting

- Jenkins, J. M. et al. (2010). *The Astrophysical Journal Letters* 713, L87. An overview of the Kepler science pipeline, the ancestor of SPOC.
- Twicken, J. D. et al. (2018). *Publications of the Astronomical Society of the Pacific* 130, 064502. Data Validation: difference images, centroids and the other diagnostics.
- Coughlin, J. L. et al. (2016). *The Astrophysical Journal Supplement Series* 224, 12. The Kepler DR24 catalog and the first version of the Robovetter.
- Thompson, S. E. et al. (2018). *The Astrophysical Journal Supplement Series* 235, 38. DR25 and the Robovetter, with reliability measured using inverted and scrambled curves.
- Guerrero, N. M. et al. (2021). *The Astrophysical Journal Supplement Series* 254, 39. The prime mission TOI catalog and the TESS team's vetting process.
- Prša, A. et al. (2022). *The Astrophysical Journal Supplement Series* 258, 16. The TESS eclipsing binary catalog, mirrored by the project (and which contains hot Jupiters).
- Bryson, S. T. et al. (2013). *Publications of the Astronomical Society of the Pacific* 125, 889. Identifying background false positives with difference images.
- Coughlin, J. L. et al. (2014). *The Astronomical Journal* 147, 119. Ephemeris matching in the Kepler field; the conceptual basis of `NEARBY_KNOWN`.

### A3. False positive probability

- Morton, T. D. (2012). *The Astrophysical Journal* 761, 6. The statistical validation method implemented in vespa.
- Morton, T. D. & Johnson, J. A. (2011). *The Astrophysical Journal* 738, 170. An estimate of the false positive rate expected among Kepler candidates.
- Morton, T. D. et al. (2016). *The Astrophysical Journal* 822, 86. Mass validation of Kepler planets; shows what "validated" means.
- Giacalone, S. et al. (2021). *The Astronomical Journal* 161, 24. triceratops, used by PlanetHunter; scenarios, FPP, NFPP and thresholds.
- Torres, G. et al. (2011). *The Astrophysical Journal* 727, 24. BLENDER and the validation of Kepler-9 d; another school of statistical validation.
- Fressin, F. et al. (2013). *The Astrophysical Journal* 766, 81. Kepler's false positive rate by type of scenario; helps calibrate your intuition about priors.
- Lissauer, J. J. et al. (2012). *The Astrophysical Journal* 750, 112. Why candidates in multiple systems are almost always planets.
- Raghavan, D. et al. (2010). *The Astrophysical Journal Supplement Series* 190, 1. The multiplicity of Sun-like stars; where the idea that about half of them have a companion comes from.

### A4. Machine learning

- Shallue, C. J. & Vanderburg, A. (2018). *The Astronomical Journal* 155, 94. A neural network with global and local views for Kepler signals.
- Yu, L. et al. (2019). *The Astronomical Journal* 158, 25. The adaptation of that network to TESS, with triage and vetting.
- Valizadegan, H. et al. (2022). *The Astrophysical Journal* 926, 120. ExoMiner and the validation of 301 Kepler planets.
- Armstrong, D. J. et al. (2021). *Monthly Notices of the RAS* 504, 5327. Planet validation with several ML algorithms and calibrated probabilities.
- Guo, C. et al. (2017). "On Calibration of Modern Neural Networks", *Proceedings of the 34th International Conference on Machine Learning*. Deep networks are overconfident; temperature scaling fixes it.

### A5. Measuring the system

- Wilson, E. B. (1927). *Journal of the American Statistical Association* 22, 209. The confidence interval used in every benchmark report.
- Brown, L. D., Cai, T. T. & DasGupta, A. (2001). *Statistical Science* 16, 101. Why the naive interval fails and Wilson works.
- McNemar, Q. (1947). *Psychometrika* 12, 153. The test for comparing proportions measured on the same objects, the basis of the before/after comparison.
- Christiansen, J. L. et al. (2013). *The Astrophysical Journal Supplement Series* 207, 35. Injecting transits into Kepler data to measure recovery; the model for injection-recovery.
- Burke, C. J. et al. (2015). *The Astrophysical Journal* 809, 8. Kepler completeness applied to planet occurrence rates.
- Kreidberg, L. (2015). *Publications of the Astronomical Society of the Pacific* 127, 1161. `batman`, which generates the synthetic transits.

### A6. From candidate to community

- Eisner, N. L. et al. (2021). *Monthly Notices of the RAS* 501, 4669. Results from Planet Hunters TESS; how volunteers get to CTOIs, many of them single transits.
- Collins, K. A. et al. (2017). *The Astronomical Journal* 153, 77. AstroImageJ, the standard tool for TFOP ground-based photometry.
- Assessment of community CTOIs (Zenodo, record 5130660). The 168 TOIs that started as CTOIs up to 2021 and why they concentrate on faint stars and single transits; evidence for the project's niches.
- TFOP page at HEASARC (heasarc.gsfc.nasa.gov/docs/tess/tfop.html). The structure of the follow-up program and how to take part.

## Data, missions and catalogs (required citations)

Any work using TESS data must cite the sources below, depending on what was used.

- Ricker, G. R. et al. (2015). *Journal of Astronomical Telescopes, Instruments, and Systems* 1, 014003. The TESS mission.
- Jenkins, J. M. et al. (2016). *Proceedings of the SPIE* 9913. SPOC, which produces the 2-minute light curves and the DV reports.
- Huang, C. X. et al. (2020). *Research Notes of the AAS* 4, 204. QLP, the full-frame image pipeline.
- Stassun, K. G. et al. (2019). *The Astronomical Journal* 158, 138. The TESS Input Catalog (TIC v8), the source of the stellar parameters.
- Gaia Collaboration, Prusti, T. et al. (2016). *Astronomy & Astrophysics* 595, A1. The Gaia mission.
- Gaia Collaboration, Vallenari, A. et al. (2023). *Astronomy & Astrophysics* 674, A1. Gaia DR3, used for the neighbors and the Gaia binaries.
- Akeson, R. L. et al. (2013). *Publications of the Astronomical Society of the Pacific* 125, 989. The NASA Exoplanet Archive (exoplanetarchive.ipac.caltech.edu).
- Schneider, J. et al. (2011). *Astronomy & Astrophysics* 532, A79. The Encyclopaedia of Exoplanetary Systems (exoplanet.eu).
- ExoFOP-TESS (exofop.ipac.caltech.edu/tess). TOI and CTOI tables, notes and follow-up files; cite it as described on the service's help page.

## Tools

- Lightkurve Collaboration (2018), ascl:1812.013. Lightkurve, for downloading and handling TESS light curves.
- Astropy Collaboration (2022). *The Astrophysical Journal* 935, 167. Astropy, the basis for units, time and BLS.
- Ginsburg, A. et al. (2019). *The Astronomical Journal* 157, 98. Astroquery, for querying MAST, Gaia, VizieR and SIMBAD.
- wotan (Hippke et al. 2019), TLS (Hippke & Heller 2019), batman (Kreidberg 2015), triceratops (Giacalone et al. 2021), vespa (Morton 2012) and celerite (Foreman-Mackey et al. 2017): cite the papers listed above.

## Websites and communities

- ADS (ui.adsabs.harvard.edu). The search engine for the astronomical literature; use `object:` and `full:` to search for targets.
- arXiv, astro-ph.EP section (arxiv.org). New papers on planets, before they are published in journals.
- ExoFOP-TESS (exofop.ipac.caltech.edu/tess). Target pages, community notes and CTOI submission.
- NASA Exoplanet Archive (exoplanetarchive.ipac.caltech.edu). Confirmed planets and a TOI table with dispositions.
- Planet Hunters TESS on Zooniverse (zooniverse.org). Light curve classification and a forum where volunteers and professionals discuss candidates.
