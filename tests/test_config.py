from planethunter.config import DEFAULT_CONFIG, Config, load_config


def test_repo_config_loads_and_matches_schema():
    cfg = load_config(DEFAULT_CONFIG)
    assert cfg.vetting.sde_min == 9.0
    assert cfg.crossmatch.host_radius_arcsec == 21.0
    assert cfg.search.tls_backend == "fused-pl"


def test_params_hash_changes_with_thresholds():
    a, b = Config(), Config()
    assert a.params_hash() == b.params_hash()
    b.vetting.sde_min = 8.0
    assert a.params_hash() != b.params_hash()


def test_max_workers_env_caps_every_pool(monkeypatch):
    import os

    import pytest

    from planethunter.config import MAX_WORKERS_ENV, SearchConfig, limit_native_threads, max_workers

    monkeypatch.delenv(MAX_WORKERS_ENV, raising=False)
    assert max_workers(None, 12) == 12
    assert max_workers(6, 12) == 6
    monkeypatch.setenv(MAX_WORKERS_ENV, "4")
    assert max_workers(None, 12) == 4
    assert max_workers(8, 12) == 4  # the cap also wins over --workers
    assert max_workers(2, 12) == 2
    assert SearchConfig(workers=0).n_workers() <= 4
    monkeypatch.setenv(MAX_WORKERS_ENV, "0")
    with pytest.raises(ValueError):
        max_workers(None, 12)
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    monkeypatch.setenv("MKL_NUM_THREADS", "3")
    limit_native_threads()
    assert os.environ["OMP_NUM_THREADS"] == "1"
    assert os.environ["MKL_NUM_THREADS"] == "3"  # user setting kept
