# Glossary

<p class="meta">Course terms, in alphabetical order · look things up whenever you need to</p>

Each term has a short definition and, in parentheses, the lesson where it is explained in detail. Names in `code font` are PlanetHunter columns, tests or commands.

## A

**Alias.** A wrong period that is a multiple or a fraction of the true one (P/2, 2P, P/3, 3P...). It shows up because, with few transits and gaps in the data, several periods "fit" almost equally well. PlanetHunter tests aliases in the search (`refine_alias`) and in the crossmatch. (B2, M3)

**Arcsecond (″).** A unit of angle: 1/3,600 of a degree. The full Moon is about 1,800″ across; a TESS pixel, 21″. (B3)

**Astronomical unit (AU).** The average distance between Earth and the Sun, about 150 million km. Used for the size of orbits. (B1, B2)

## B

**Background binary.** A faint eclipsing binary that lies in almost the same direction as the target, in the same pixel or in neighboring pixels. Its eclipses appear diluted in the total light and mimic the shallow transit of a planet on the target. (B4)

**Benchmark.** A standardized test that always measures the system's performance in the same way, so versions can be compared. PlanetHunter's recall benchmark uses 135 detectable TOIs from sector 69. (A5)

**Biweight.** A robust filter used in detrending: it estimates the slow brightness trend in a moving window, without being thrown off by unusual points such as those of the transit itself. PlanetHunter uses the version from the wotan library, with a 1-day window (shorter windows only for stars that vary quickly). (M4, A1)

**Blend.** The mixing of light from two or more stars in the same measurement. See **contamination**. (B3, B4)

**BLS (Box Least Squares).** A classic transit search algorithm: it tests many periods and, for each one, fits a "box" (a rectangular dip) to the folded data. Proposed by Kovács, Zucker and Mazeh in 2002. (M3, A1)

**BTJD (Barycentric TESS Julian Date).** The TESS unit of time: days since a reference date (BJD − 2,457,000), corrected to the center of mass of the Solar System. All PlanetHunter times are in BTJD. (B3)

## C

**Cadence.** The interval between two consecutive brightness measurements. TESS provides 20 s and 2 min light curves for selected stars, and full-frame images every 200 s (previously 10 and 30 min). (B3)

**Candidate.** A signal that survived vetting and deserves attention, but is not a planet. On the course's ladder: signal → candidate → CTOI → TOI → validated → confirmed. (B3)

**CBV (Cotrending Basis Vectors).** Variation patterns shared by many stars on the same detector, caused by the instrument. Subtracting them removes shared systematics without erasing each star's own variation. (M4)

**Centroid.** The average position of a star's light on the image, like the "center of gravity" of its brightness. If it moves during the transit, the dip probably comes from a neighboring star; this is the `centroid` test. (B4, M5)

**Chi-squared (χ²).** A statistical test that measures whether several measurements agree with a model, taking the errors into account. The `consistency` test uses this idea to check whether all transits have the same depth. (M1)

**Completeness.** The fraction of real planets, of a given size and period, that the system manages to find. It is measured with injection-recovery. (A5)

**Confidence interval (95 % CI).** The range of values compatible with a measurement, given the amount of data. PlanetHunter's recall of 91.1 %, measured with 135 objects, has a 95 % CI of 85.1 % to 94.8 % (Wilson interval). (A5)

**Confirmed planet.** A planet with evidence independent of the transit, usually a mass measured by radial velocity. The last step of the ladder. (B3)

**Contamination.** Light from other stars mixed with the target's light in the same measurement, a consequence of the large TESS pixel. A signal "from the target" may come from a contaminating star. (B3, B4)

**Continuous viewing zone (CVZ).** Regions within about 12° of the ecliptic poles, observed by TESS in every sector of a year. Stars there have many sectors of data: in sector 69, from 10 to 22. (B3)

**Crossmatch.** Comparing each signal with catalogs of known objects, to find out whether it has already been recorded. PlanetHunter matches by star (TIC number or position within 21″) and by signal (period with aliases, and transit by transit). (B3, B4)

**Crossmatch class.** The answer to the question "does it already exist?": `KNOWN_PLANET` (confirmed planet), `KNOWN_TOI` and `KNOWN_CTOI` (already a TESS candidate), `KNOWN_PUBLISHED` (in a published candidate list, such as Kepler's KOIs or DIAmante), `KNOWN_FP` (cataloged false positive or binary), `NEARBY_KNOWN` (known neighbor with the same period), `NEW` (nothing matched) and `UNVERIFIED` (it would be new, but some catalog is missing or stale). (B3, B5)

**CROWDSAP.** A number between 0 and 1, computed by the SPOC pipeline, that estimates the fraction of the light in the aperture that comes from the target itself. Values well below 1 mean a lot of contamination. It appears in the Parameters section of the dossier. (B5, M4)

**CTOI (Community TOI).** A candidate submitted to ExoFOP by someone outside the TESS team. It can be promoted to TOI. It is where a good PlanetHunter candidate ends up. (B3, A6)

## D

**Depth (δ).** How much the brightness drops during the transit, in ppm. Roughly $(R_p/R_\star)^2$. (B2)

**Detrending.** Removing the slow variation in brightness (rotation, spots, instrument effects) so the transits become visible. If the filter window is too short, it "eats" the transit: with 0.5 day, a 5 h transit loses 40 % of its depth; with 1 day, 6 %. (B4, M4, A1)

**Difference image.** The in-transit image subtracted from the out-of-transit image. Whatever "dimmed" shows up in the difference and reveals where the dip came from. The `tpf_difference_image` test. (B4, A2)

**Direct imaging.** A detection method that photographs the planet itself, blocking the star's light. It only works for giant, young planets far from their star. (B1)

**Doppler effect.** A change in the color (wavelength) of light from a source moving toward or away from us, like the pitch of an ambulance siren. It is the basis of the radial velocity method. (B1)

**Dossier.** The HTML report PlanetHunter generates for a signal, with parameters, plots, the vetting table, the crossmatch and provenance. It is saved in `data/dossiers/`. (B5)

**Double transit (duotransit).** A signal with only two transits separated by a long gap (for example, in sectors observed years apart). The period is ambiguous among several aliases. (A1)

**Duration (T14).** The time from the start to the end of a transit, in hours. It depends on the period, the star's size and density, and the impact parameter. (B2, M2)

## E

**Eclipsing binary (EB).** Two stars orbiting each other with their orbit lined up with us, so that one eclipses the other. It is the most common false positive; it gives itself away with a V shape, different odd and even eclipses and a secondary eclipse. (B4)

**Ecliptic.** The plane in which Earth and the other planets orbit the Sun. TESS sectors are arranged around the ecliptic poles. (B3)

**Ephemeris.** The prediction of when the next transits will happen: a period and a transit time ($T_0$). (B2)

**Epoch spike.** A moment at which far more unrelated stars show a "transit" than chance allows. The cause is the telescope, not the stars. PlanetHunter checks every run for them; a signal with half or more of its transits on epoch spikes never generates an alert. (A2)

**ExoFOP.** The exoplanet follow-up portal (exofop.ipac.caltech.edu), with a page for each star, lists of TOIs and CTOIs, community notes and CTOI submission. (B3, A6)

**ExoMiner.** A NASA neural network for classifying transit signals, described by Valizadegan and collaborators in 2022. (A4)

**Exoplanet.** A planet that orbits a star other than the Sun. In 2026 about 6,400 confirmed ones are known. (B1)

**exoplanet.eu.** A European exoplanet catalog, more inclusive than NASA's (about 8,300 objects). It is one of PlanetHunter's mirrors. (B3)

## F

**False alarm (FA).** A signal with no astrophysical origin: noise or an instrumental defect. (B3, B4)

**False positive (FP).** A real, astrophysical signal that looks like a planet but is not one: eclipsing binary, background binary, contamination. In general use, any signal that looks like a planet and is not. (B4)

**FFI (Full-Frame Image).** A complete image from a TESS camera, with all the stars in the field. Current cadence: 200 s. It makes it possible to study stars outside the 2-minute list. (B3)

**Flare.** An explosion on a star's surface that produces a quick upward spike in brightness. PlanetHunter cuts upward spikes, but never downward ones. (B4)

**FPP (False Positive Probability).** The probability, computed by a statistical model, that the signal is a false positive. Below 0.5, a plausible candidate; below 0.015 (with NFPP below 0.001 and high-resolution imaging), the level used to validate a planet. PlanetHunter computes it with triceratops, and the test fails if FPP ≥ 0.5 or NFPP > 0.1. (A3)

## G

**Gaia.** A European space mission that measured the position, distance and brightness of more than a billion stars. PlanetHunter uses the Gaia DR3 catalog to list neighboring stars and known eclipsing binaries. (A2)

**Gaussian process (GP).** A flexible statistical model that describes variations correlated in time. It is an alternative to the biweight for detrending very variable stars. (A1)

**Giant.** A star that has used up the hydrogen in its core and swelled to tens or hundreds of R☉. It hides small planets, because the depth falls with the square of the star's radius. (B1)

**Grazing transit.** A transit in which the planet only skims the edge of the star ($b$ close to 1). It is short and V-shaped, and so it can be mistaken for a binary. (B2, B4)

## H

**Hard fail.** A vetting failure serious enough to fail the signal on its own, without setting the score to zero: `shape`, `secondary_scan`, `tpf_difference_image` and `fpp_triceratops`. Compare with **soft fail** and **veto**. (M5)

**Hot Jupiter.** A gas giant planet on an orbit of a few days, very close to its star. They were the first exoplanets found around Sun-like stars (51 Pegasi b, 1995). (B1)

## I

**Impact parameter (b).** The distance from the planet's path to the center of the star's disk, in units of the star's radius: 0 is central, close to 1 is grazing. Transits with a high $b$ are shorter and V-shaped. (B2, M2)

**Ingestion.** The stage that downloads light curves from MAST and stores them as Parquet. The `planethunter ingest` command. (B3)

**Injection-recovery.** A technique that injects synthetic transits into real curves, runs the pipeline and counts how many it recovers. It is how completeness is measured. (A5)

## K

**Kepler (law).** Kepler's third law relates the period and the size of the orbit: for a 1 M☉ star, $a^3 = P^2$ with $a$ in AU and $P$ in years. (B2, M2)

**Kepler (telescope).** A NASA space telescope that observed one region of the sky from 2009 to 2018 and showed that planets are common. The predecessor of TESS. (B1, B3)

## L

**Light curve.** A plot of a star's brightness over time. It is the raw data of every transit search. (B2)

**Light-year.** The distance light travels in one year: about 9.46 trillion km. Despite the name, it measures distance, not time. (B1)

**Lightkurve.** A Python library for downloading, cleaning and analyzing Kepler and TESS light curves. The basis of the programming track. (M4, P3)

**Limb darkening.** The edge of a star's disk looks darker than its center, because there we see higher, cooler layers. This rounds off the bottom of the transit. (B2, M2)

## M

**M☉ (solar mass).** The mass of the Sun, about 2 × 10³⁰ kg, used as a unit for stars. (B1)

**Machine learning.** Programs that learn patterns from labeled examples instead of hand-written rules. In the field, neural networks classify transit signals as planet or false positive; the reviews made with `planethunter review` are the labels for the project's future classifier. (A4)

**Magnitude.** An inverted brightness scale: a smaller number means a brighter object. Five magnitudes correspond to a factor of 100 in brightness. See **Tmag**. (B3)

**Main sequence.** The stable phase of a star's life, in which it burns hydrogen in its core. The Sun is in it. (B1)

**MAST (Mikulski Archive for Space Telescopes).** NASA's public archive, where the TESS data are kept. (B3)

**Median.** The middle value when the data are sorted. Less sensitive to extreme values than the mean. (M1)

**Microlensing (gravitational).** A detection method in which the gravity of a foreground star magnifies the light of another star behind it; a planet causes a brief deviation. The event does not repeat. (B1)

**Mini-Neptune.** A planet between about 2 and 4 R⊕, with a thick atmosphere. There is none in the Solar System, but they are very common in the galaxy. (B1)

**Mirror (catalog).** A local copy of a catalog of known objects. PlanetHunter keeps 12 mirrors: the NASA Exoplanet Archive, the TOIs, the CTOIs, exoplanet.eu, Kepler's KOIs, K2, two TESS binary catalogs and four published candidate lists. Each one has its own freshness limit: 48 h for the TOIs, the CTOIs and the Archive, 7 days for exoplanet.eu and K2, 30 days for the KOIs; fixed published tables never expire. If any mirror is missing or too old, no signal can be classified as new. (B3, B5)

**Momentum dump.** Firing small TESS thrusters to unload the rotation built up in the reaction wheels. The pointing jitters and the brightness jumps; in the dossier, they show up as dotted blue lines. (B4)

**Multi-sector.** An analysis that combines data from several sectors of the same star. It increases the number of transits and makes it possible to check whether a signal repeats. (B3, M5)

## N

**NFPP (Nearby False Positive Probability).** The probability that the signal comes from a known neighboring star rather than the target. To validate a planet, the literature uses an NFPP below 0.001; above 0.1, the signal is a likely nearby false positive and PlanetHunter's FPP test fails. (A3)

**Noise.** Fluctuations in the measurements that do not come from the signal you are looking for. It hides shallow transits. (B2, M1)

**Normal (distribution).** A bell-shaped distribution that describes the random noise of many measurements well. About 99.7 % of the values fall within 3σ of the mean. (M1)

**Nuclear fusion.** The joining of light nuclei (hydrogen) into heavier ones (helium), releasing energy. It is what makes stars shine. (B1)

**Null run.** A search on light curves turned upside down (inverted) or with each orbit shifted in time (scrambled). Every "transit" found in them is false by construction, so counting them measures the false alarm rate. Kepler used this method (Thompson et al. 2018); in PlanetHunter it is `planethunter search --null inverted` or `--null scrambled`. (A1, A2)

## O

**Occultation.** The planet passing **behind** the star. For very hot planets, such as WASP-18 b, the planet's light disappears and a small dip shows up at phase 0.5. (B4, M2)

**Odd/even.** A comparison between the depth of the odd and the even transits. If they differ, it is probably a binary with twice the period found. The `odd_even` test. (B4)

**Orbit edge.** The start or end of each 13.7-day TESS orbit, where brightness ramps linked to temperature changes appear. Poorly removed ramps mimic transits; the `edges_dumps` test is suspicious of transits that fall on them. (B4)

## P

**P0, P1, P2 (severity).** The priority of a new candidate in PlanetHunter. P1: passed vetting, score ≥ 0.8 **and**, when the model exists, `p_rank` at or above the model's P1 threshold. P0: everything P1 needs, plus complete deep vetting (difference image and Gaia neighbors passed, FPP computed) with FPP < 0.1, NFPP < 0.001, a planet smaller than 8 R⊕, SNR ≥ 15 and 2-minute data. P2: passed vetting but below the P1 thresholds; or failed vetting without a veto but rescued by a `p_rank` at or above the model's P2 threshold; or capped by a warning (the star is a cataloged binary or has no known radius, NFPP > 0.1, the signal is the source of a signal shared with a neighbor, or its transits partly coincide with a known object). No severity: a veto, transits on epoch spikes, or a signal that belongs to a neighbor. The model only lowers priority, never raises it. (B5, A3, A4)

**p_planet, p_rank and p_abs.** `p_rank` (stored in the `p_planet` column) is the probability that a signal is a planet, learned with `planethunter calibrate` from known signals: confirmed planets against cataloged false positives and the false alarms of null runs. Severity uses it only to lower priority, through two thresholds chosen by measuring how many known planets they keep. `p_abs` is the same probability corrected for how rare planets are among new signals; that correction rests on an assumption (5 %), so `p_abs` is for reading only. (A4)

**Parquet.** A compact file format for tables, used by PlanetHunter to store light curves in `data/parquet/`. The DuckDB database (`data/planethunter.duckdb`) holds signals, vetting and candidates. (B3, P2)

**Parsec (pc).** A unit of distance used by astronomers, equal to 3.26 light-years. (B1)

**PDCSAP and SAP.** Two kinds of flux in the SPOC pipeline light curves. SAP is the simple sum of the light in an aperture; PDCSAP is SAP corrected for systematics and contamination. (M4)

**Period (P).** The time between two consecutive transits, in days. (B2)

**Periodogram.** A plot that tests thousands of periods and shows how well each one "fits" the data. A peak that stands out points to a periodic signal. (M3)

**Phase.** The position within an orbit, from 0 to 1. The transit is at phase 0; halfway between two transits is phase 0.5. (B4)

**Phase folding.** Stacking all the transits by lining them up on the period, like piling up transparent sheets. The random noise partly cancels out and the transit adds up. The "Folded transit" plot in the dossier. (B2, B5)

**Pixel (TESS).** Each pixel covers 21″ × 21″ of sky. That is large: several stars fit in it, which causes contamination. (B3)

**Planet Hunters TESS.** A citizen science project on Zooniverse in which volunteers mark transits in real TESS light curves. (B5)

**ppm (parts per million).** The unit of transit depth. 10,000 ppm = 1 %. (B2)

**Provenance.** The record of where each result came from: sector, data author, pipeline version and `run_id`. It makes it possible to reproduce any analysis. (B5)

## Q

**QLP (Quick Look Pipeline).** An MIT pipeline that extracts light curves from the TESS full-frame images (FFI), reaching many more stars than the 2-minute light curves. (B3)

## R

**R⊕ (Earth radius).** The radius of Earth, 6,371 km, used as a unit for planets. Jupiter is about 11 R⊕. (B1)

**R☉ (solar radius).** The radius of the Sun, 696,000 km (about 109 R⊕), used as a unit for stars. (B1)

**Radial velocity.** A detection method that measures the back-and-forth motion of the star caused by the planet, through the Doppler effect. It gives the planet's mass and is the main confirmation method. (B1)

**Radius ratio (Rp/R*).** The planet's radius divided by the star's radius. The depth is roughly its square. (B2)

**Recall.** The fraction of known objects the system recovers. In sector 69, PlanetHunter recovers 123 of 135 detectable TOIs: 91.1 %. (A5)

**Red dwarf.** A star of spectral type M: small (0.1 to 0.6 R☉), cool and dim. It is the most common type of star in the galaxy and the best for finding small planets by transit. (B1, B2)

**Red noise.** Noise correlated in time (neighboring points resemble each other), which does not go away when you average. That is why PlanetHunter estimates errors using blocks of data, as in Pont, Zucker and Queloz (2006). (M1)

**Robovetter.** Kepler's automatic vetting system (DR25 catalog), described by Thompson and collaborators in 2018. A reference for comparison with PlanetHunter's vetting. (A2)

**run_id.** The unique code of each PlanetHunter run, printed by the commands and used in `vet`, `candidates` and the dossier. (B5)

## S

**Scattered light.** Light from Earth and the Moon that enters the TESS cameras in certain parts of the orbit and changes the background of the images. One of the systematics that mimic transits. (B4)

**SDE (Signal Detection Efficiency).** How much the highest peak of the periodogram stands out from the rest, in units of standard deviation. PlanetHunter requires SDE ≥ 9, which corresponds to a false alarm chance of about 1 in 10,000 according to Hippke and Heller (2019). (M3)

**Secondary eclipse.** The second dip in brightness of a binary, when the companion passes behind the main star; on a circular orbit, it happens at phase 0.5. The `secondary` test only vetoes if it is at least 10 % of the main one. If the "secondary" is as deep and as long as the main dip, it is just another transit: the signal was found at twice the true period, and PlanetHunter tests it again at half the period (`period_halved`). (B4, M5)

**Sector.** A block of about 27 days in which TESS observes the same 24° × 96° strip of sky. (B3)

**Shared signal.** The same period and transit time on two stars within 2′: the light of one leaks into the pixels of the other. The star that can really produce the dip is the `source` (at most P2); the other is the `victim` (no alert). Two TIC entries less than 2″ apart are a `duplicate` of the same star (no alert). (A2)

**Sigma (σ).** The symbol for standard deviation. "3σ" means three standard deviations above or below the mean: unlikely by chance, but not impossible when you make many tries. (M1)

**Signal.** A periodic dip in brightness found by the search. The first step of the ladder: it has not passed any test yet. (B3)

**SIMBAD.** An astronomical database (Strasbourg, France) that says what type of object each known star is. The `simbad_type` test queries it. (A2)

**Single transit (monotransit).** A signal with a single observed transit; the period is unknown. PlanetHunter vetoes signals with fewer than 2 transits; single transits need a dedicated detector, which is in the plan. (B4, A1)

**S/N_pink.** A signal-to-noise ratio that also counts red noise, measured on the time scale of the transit (Pont, Zucker and Queloz, 2006). The TESS quick-look pipeline (QLP) requires at least 9; in PlanetHunter, falling below 9 is a soft fail. (M1, M5)

**SNR (signal-to-noise ratio).** The size of the transit compared with the noise, taking into account how many measurements fall inside the transits. PlanetHunter requires SNR ≥ 7.1. (B2, M1)

**Soft fail.** A vetting failure that, on its own, only lowers the score. One soft fail is tolerated; two or more fail the signal. (M5)

**Spectral type.** A classification of stars by temperature: O, B, A, F, G, K, M, from hottest to coolest. The Sun is G2. (B1)

**SPOC (Science Processing Operations Center).** NASA's official pipeline that produces the 2-minute and 20-second TESS light curves. It is the "author" PlanetHunter uses most. (B3)

**Standard deviation (σ).** A measure of how much the values spread around the mean. In light curves, the standard deviation of the out-of-transit points is the noise. (M1)

**Stellar density.** The star's mass divided by its volume. Together with the period, it determines how long a transit should last; a transit too long or too short for the star suggests that the signal comes from another star. It is the basis of the `duration` test. (M2)

**Stellar variability.** Changes in the brightness of the star itself: spots and rotation, pulsations, flares. Partly removed by detrending. (B4)

**Super-Earth.** A rocky planet larger than Earth, about 1 to 2 R⊕. (B1)

**Systematic.** A variation caused by the instrument or the processing, not by the star. Examples: momentum dumps, orbit edges, scattered light. (B4)

## T

**T0.** The time of the middle of a reference transit, in BTJD. Together with the period, it forms the ephemeris. (B2)

**T14.** See **duration**.

**Teff.** Effective temperature, or the temperature of the star's surface, in kelvin. The Sun's is 5,772 K. (B1)

**TESS (Transiting Exoplanet Survey Satellite).** A NASA space telescope launched in 2018 that observes almost the whole sky looking for transits. The source of PlanetHunter's data. (B3)

**TFOP and TFOPWG.** TFOP is the program of follow-up observations of TOIs with other telescopes. TFOPWG is the working group that records the disposition of each TOI. (B3, A6)

**TFOPWG disposition.** The status of a TOI as recorded by the follow-up group: PC (planet candidate), APC (ambiguous candidate), CP (confirmed planet), KP (known planet), FP (false positive), FA (false alarm). (B3)

**Threshold.** The cutoff value of a test, such as SNR ≥ 7.1. In PlanetHunter, they all live in `config/thresholds.yaml`, versioned and commented. (B4, A5)

**TIC (TESS Input Catalog).** A catalog of more than 1.7 billion objects; each star has a number, such as TIC 261136679 (Pi Mensae). It also gives estimated radius, mass and temperature. (B3)

**TLS (Transit Least Squares).** A transit search algorithm that uses a realistic transit model instead of a box. Published by Hippke and Heller in 2019; it is what PlanetHunter uses. (M3, A1)

**Tmag.** The star's brightness on the TESS magnitude scale. A smaller number means a brighter star: 6 is very bright, 13 is faint. (B3)

**TOI (TESS Object of Interest).** An official candidate announced by the TESS team, with a number such as TOI-144.01. It may still be a false positive. (B3)

**TPF (Target Pixel File).** A file with the pixels around a star, at each moment. It makes it possible to build difference images and measure centroids. (A2)

**Transit.** A planet (or another body) passing in front of a star, as seen from our point of view, causing a dip in brightness. (B1, B2)

**Triceratops.** A program that computes FPP and NFPP taking into account the star, the Gaia neighbors and the shape of the transit. Described by Giacalone and collaborators in 2021. (A3)

## U

**U and V shapes.** A planet transit has an almost flat bottom (U); a grazing eclipse of a binary is pointed (V). Grazing planets also make a V. Even so, the `shape` test is a hard fail: a V shape fails the signal on its own, at the cost of a few real grazing planets. (B4, M5)

## V

**Validated planet.** A planet whose false positive probability has been shown to be very small, through a statistical analysis supported by high-resolution imaging, without a measured mass. (B3, A3)

**Verdict.** The result of vetting: `FAIL` with any veto, any hard fail or more than one soft fail; otherwise `PASS_BASIC`. (M5)

**Vetting.** A battery of tests to rule out false positives. PlanetHunter has basic vetting (no internet, tests such as `odd_even`, `secondary`, `shape`, `centroid`) and deep vetting (with internet: difference image, Gaia neighbors, other sectors, FPP). (B4, M5)

**Vetting score.** A grade from 0 to 1 from the vetting. It starts at 1.0; each failed test multiplies it by a weight (0.3 to 0.6) and each test with no data by 0.95; a veto sets it to zero. It does not decide pass or fail (see **verdict**): it ranks the signals, and P0 and P1 require a score of at least 0.8. It is a useful ranking, not a probability (for a probability, see **p_planet, p_rank and p_abs**). (B4, M5)

**Veto.** A serious failure in a vetting test that eliminates the signal immediately, setting the score to zero. Other failures are hard fails or soft fails. (B4, M5)

## W

**White noise.** Random noise, independent from one measurement to the next; it shrinks with the square root of the number of points when you average. (M1)

**wotan.** A Python detrending library, by Hippke and collaborators, that PlanetHunter uses with the biweight filter. (M4, A1)

## Z

**Zooniverse.** A citizen science platform that hosts Planet Hunters TESS and many other projects. (B5)
