"""Lightweight machine learning: ranking probability p_rank (and display-only p_abs) from the
basic-vetting results. Logistic regression + Platt scaling, numpy inference from JSON; the ML
only lowers severity (see ml/calibrate.py and alerts/severity.py)."""
