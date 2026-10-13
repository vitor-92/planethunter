-- PlanetHunter DuckDB schema. Idempotent (CREATE IF NOT EXISTS).
-- Units: time BTJD, period days, depth ppm, duration hours, separation arcsec.

CREATE TABLE IF NOT EXISTS targets (
    tic_id BIGINT PRIMARY KEY,
    ra_deg DOUBLE, dec_deg DOUBLE, pmra_mas_yr DOUBLE, pmdec_mas_yr DOUBLE,
    tmag DOUBLE, teff_k DOUBLE, logg_cgs DOUBLE, radius_rsun DOUBLE, mass_msun DOUBLE,
    crowdsap DOUBLE,
    updated_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS lightcurves (
    tic_id BIGINT, sector INTEGER, author VARCHAR,
    camera INTEGER, ccd INTEGER, procver VARCHAR, data_release INTEGER,
    source_file VARCHAR, sha256 VARCHAR, n_points INTEGER, path VARCHAR,
    ingested_at TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (tic_id, sector, author)
);

CREATE TABLE IF NOT EXISTS search_runs (
    run_id VARCHAR PRIMARY KEY,
    mode VARCHAR, sector INTEGER, author VARCHAR,
    pipeline_version VARCHAR, params_hash VARCHAR, params_json VARCHAR,
    n_targets INTEGER, n_done INTEGER, n_signals INTEGER, n_errors INTEGER,
    started_at TIMESTAMP, finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS search_done (
    run_id VARCHAR, tic_id BIGINT, status VARCHAR, n_signals INTEGER,
    elapsed_s DOUBLE, error VARCHAR,
    PRIMARY KEY (run_id, tic_id)
);

CREATE SEQUENCE IF NOT EXISTS signal_seq;

CREATE TABLE IF NOT EXISTS signals (
    signal_id BIGINT PRIMARY KEY DEFAULT nextval('signal_seq'),
    run_id VARCHAR, tic_id BIGINT, sectors VARCHAR, author VARCHAR, iteration INTEGER,
    period_days DOUBLE, period_err_days DOUBLE, t0_btjd DOUBLE, duration_hours DOUBLE,
    depth_ppm DOUBLE, sde DOUBLE, snr DOUBLE, n_transits INTEGER,
    odd_even_mismatch_sigma DOUBLE, rp_rs DOUBLE, fap DOUBLE, edge_transit_fraction DOUBLE,
    detrend_window_days DOUBLE, alias_factor INTEGER, transit_times_json VARCHAR,
    pipeline_version VARCHAR, params_hash VARCHAR,
    created_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS crossmatch (
    signal_id BIGINT PRIMARY KEY,
    match_class VARCHAR, host_known BOOLEAN,
    matched_name VARCHAR, matched_source VARCHAR, alias VARCHAR,
    phase_consistent BOOLEAN, separation_arcsec DOUBLE, match_type VARCHAR, host_eb BOOLEAN,
    n_host_objects INTEGER, n_nearby_objects INTEGER,
    mirror_ages_json VARCHAR, notes VARCHAR,
    checked_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS vetting (
    signal_id BIGINT PRIMARY KEY,
    level VARCHAR,              -- basic | deep
    score DOUBLE, verdict VARCHAR,
    vetoed_by VARCHAR, failed VARCHAR, deep_pending VARCHAR,
    fit_depth_ppm DOUBLE, fit_t14_hours DOUBLE, fit_tau_frac DOUBLE, fit_rp_rs DOUBLE,
    fpp DOUBLE, nfpp DOUBLE, p_planet DOUBLE,
    tests_json VARCHAR, params_hash VARCHAR,
    vetted_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS candidates (
    signal_id BIGINT PRIMARY KEY,
    tic_id BIGINT, run_id VARCHAR,
    match_class VARCHAR, verdict VARCHAR, score DOUBLE,
    severity VARCHAR,           -- P1 | P2 | NONE (P0 requires deep vetting)
    review_status VARCHAR,      -- pending | approved | rejected | follow_up
    review_note VARCHAR, reviewed_at TIMESTAMP,
    dossier_path VARCHAR,
    updated_at TIMESTAMP DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS alerts (
    signal_id BIGINT, channel VARCHAR, severity VARCHAR,
    status VARCHAR,             -- sent | pending | failed | dry_run
    message VARCHAR, error VARCHAR,
    created_at TIMESTAMP DEFAULT current_timestamp
);
