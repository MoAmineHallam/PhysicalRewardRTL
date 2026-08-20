#!/usr/bin/env python3
"""CPU-only sensitivity analysis for the correctness-arm attempt ceiling.

This is an exploratory feasibility diagnostic, not a sealed efficacy analysis
and not part of the frozen primary workflow.  It consumes only the aggregate
counts in the archived revision-5 failure audit; it never reads candidate RTL.
The output intentionally reports multiple explicit assumptions because one
non-stationary trajectory cannot identify a unique failure probability.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform

import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import beta as beta_distribution
from scipy.stats import binom, chi2, nbinom


class RiskAnalysisError(RuntimeError):
    pass


def sha256_raw(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_audit(path: str) -> tuple[dict, list[dict]]:
    with open(path, encoding="utf-8") as handle:
        audit = json.load(handle)
    group = audit.get("group_log_audit", {})
    bins = group.get("bins_250_groups")
    if not isinstance(bins, list) or len(bins) != 18:
        raise RiskAnalysisError("expected exactly 18 archived 250-group bins")
    expected_start = 1
    for row in bins:
        start, end = row.get("groups", [None, None])
        updates = row.get("updates")
        if start != expected_start or end != start + 249:
            raise RiskAnalysisError("250-group bins are not consecutive")
        if not isinstance(updates, int) or not 0 <= updates <= 250:
            raise RiskAnalysisError("invalid update count in a 250-group bin")
        expected_start = end + 1
    if expected_start != 4501:
        raise RiskAnalysisError("bins do not cover groups 1..4500")
    if sum(row["updates"] for row in bins) != group.get("optimizer_updates"):
        raise RiskAnalysisError("bin counts disagree with audited optimizer updates")
    if group.get("attempted_groups") != 4500 or group.get("optimizer_updates") != 215:
        raise RiskAnalysisError("input is not the archived 4500-group/215-update run")
    return audit, bins


def recent_window(bins: list[dict], groups: int) -> dict:
    if groups % 250 or not 0 < groups <= 4500:
        raise RiskAnalysisError("recent window must be a positive multiple of 250")
    chosen = bins[-groups // 250:]
    updates = sum(row["updates"] for row in chosen)
    return {
        "groups": groups,
        "updates": updates,
        "nonflat_rate": updates / groups,
        "source_group_range": [4501 - groups, 4500],
    }


def fixed_rate_scenario(name: str, description: str, probability: float,
                        groups_remaining: int, updates_needed: int) -> dict:
    success = float(binom.sf(updates_needed - 1, groups_remaining, probability))
    failure = float(binom.cdf(updates_needed - 1, groups_remaining, probability))
    quantiles = {}
    for q in (0.1, 0.5, 0.9):
        failures = float(nbinom.ppf(q, updates_needed, probability))
        attempts = failures + updates_needed
        quantiles[str(q)] = None if not math.isfinite(attempts) else int(attempts)
    return {
        "name": name,
        "description": description,
        "assumption": "future groups are independent with one fixed non-flat probability",
        "nonflat_probability": probability,
        "expected_future_updates_before_ceiling": groups_remaining * probability,
        "exact_probability_reach_target_before_ceiling": success,
        "exact_probability_fail_to_reach_target": failure,
        "natural_log_probability_fail_to_reach_target": float(
            binom.logcdf(updates_needed - 1, groups_remaining, probability)),
        "attempts_to_needed_updates_quantiles_untruncated": quantiles,
    }


def monte_carlo_probability_record(successes: int, draws: int) -> dict:
    """Simulation probability plus exact interval for Monte Carlo error only."""
    lower = (0.0 if successes == 0 else
             float(beta_distribution.ppf(0.025, successes, draws - successes + 1)))
    upper = (1.0 if successes == draws else
             float(beta_distribution.ppf(0.975, successes + 1, draws - successes)))
    return {
        "successes": successes,
        "draws": draws,
        "probability": successes / draws,
        "exact_95_percent_interval_for_monte_carlo_error_only": [lower, upper],
    }


def monte_carlo_stationary_posterior(rng: np.random.Generator, draws: int,
                                     observed_updates: int, observed_groups: int,
                                     groups_remaining: int,
                                     updates_needed: int) -> dict:
    # Jeffreys prior Beta(1/2, 1/2), explicitly conditional on stationarity.
    probability = rng.beta(observed_updates + 0.5,
                           observed_groups - observed_updates + 0.5,
                           size=draws)
    future = rng.binomial(groups_remaining, probability)
    successes = int(np.count_nonzero(future >= updates_needed))
    return {
        "name": "stationary_jeffreys_posterior_final_1500",
        "description": "Propagates finite-sample uncertainty in the final-1500 rate but assumes that rate remains stationary.",
        "assumption": "one future probability drawn from the Jeffreys posterior and held fixed for all remaining groups",
        "posterior": {
            "alpha": observed_updates + 0.5,
            "beta": observed_groups - observed_updates + 0.5,
        },
        "monte_carlo_reach_target": monte_carlo_probability_record(successes, draws),
        "future_updates_quantiles": {
            str(q): float(np.quantile(future, q)) for q in (0.01, 0.05, 0.5, 0.95, 0.99)
        },
    }


def monte_carlo_recent_block_bootstrap(rng: np.random.Generator, draws: int,
                                       recent_bins: list[dict],
                                       groups_remaining: int,
                                       updates_needed: int) -> dict:
    if groups_remaining % 250:
        raise RiskAnalysisError("remaining groups must divide into 250-group blocks")
    rates = np.asarray([row["updates"] / 250 for row in recent_bins], dtype=float)
    future_blocks = groups_remaining // 250
    successes = 0
    future_totals = []
    chunk = 10_000
    for start in range(0, draws, chunk):
        n = min(chunk, draws - start)
        selected = rng.choice(rates, size=(n, future_blocks), replace=True)
        total = rng.binomial(250, selected).sum(axis=1)
        successes += int(np.count_nonzero(total >= updates_needed))
        future_totals.append(total)
    future = np.concatenate(future_totals)
    return {
        "name": "last_six_bins_exchangeable_block_bootstrap",
        "description": "Resamples the six final observed 250-group rates for each future 250-group block.",
        "assumption": "the final six bins are exchangeable and future regimes repeat their empirical variability without systematic decay",
        "source_rates": rates.tolist(),
        "future_blocks": future_blocks,
        "monte_carlo_reach_target": monte_carlo_probability_record(successes, draws),
        "future_updates_quantiles": {
            str(q): float(np.quantile(future, q)) for q in (0.01, 0.05, 0.5, 0.95, 0.99)
        },
    }


def monte_carlo_compounding_decay(rng: np.random.Generator, draws: int,
                                  latest_rate: float, decay_ratio: float,
                                  groups_remaining: int,
                                  updates_needed: int) -> dict:
    if groups_remaining % 1500:
        raise RiskAnalysisError("remaining groups must divide into 1500-group blocks")
    probabilities = np.asarray([
        latest_rate * decay_ratio ** index
        for index in range(1, groups_remaining // 1500 + 1)
    ])
    future = np.zeros(draws, dtype=np.int32)
    for probability in probabilities:
        future += rng.binomial(1500, probability, size=draws)
    successes = int(np.count_nonzero(future >= updates_needed))
    return {
        "name": "continued_compounding_1500_group_decay",
        "description": "Stress test that repeats the observed preceding-to-final 1500-group rate ratio in every future 1500-group block.",
        "assumption": "the recent multiplicative decline compounds indefinitely; this is a stress scenario, not an identified forecast",
        "decay_ratio_per_1500_groups": decay_ratio,
        "future_block_probabilities": probabilities.tolist(),
        "expected_future_updates_before_ceiling": float(1500 * probabilities.sum()),
        "monte_carlo_reach_target": monte_carlo_probability_record(successes, draws),
        "future_updates_quantiles": {
            str(q): float(np.quantile(future, q)) for q in (0.01, 0.05, 0.5, 0.95, 0.99)
        },
    }


def late_logistic_trend_test(final_six_bins: list[dict]) -> dict:
    counts = np.asarray([row["updates"] for row in final_six_bins], dtype=float)
    trials = np.full(len(counts), 250.0)
    x = np.arange(len(counts), dtype=float)
    x -= x.mean()

    def negative_log_likelihood(parameters: np.ndarray) -> float:
        probability = np.clip(expit(parameters[0] + parameters[1] * x),
                              1e-12, 1 - 1e-12)
        return float(-np.sum(counts * np.log(probability)
                             + (trials - counts) * np.log1p(-probability)))

    null_probability = counts.sum() / trials.sum()
    null_logit = math.log(null_probability / (1 - null_probability))
    null_nll = negative_log_likelihood(np.asarray([null_logit, 0.0]))
    fit = minimize(negative_log_likelihood, np.asarray([null_logit, 0.0]),
                   method="BFGS")
    if not fit.success and not np.isfinite(fit.fun):
        raise RiskAnalysisError(f"late-trend optimizer failed: {fit.message}")
    likelihood_ratio = max(0.0, 2 * (null_nll - float(fit.fun)))
    return {
        "model": "binomial logistic slope over the final six 250-group bins",
        "source_group_range": [3001, 4500],
        "counts": counts.astype(int).tolist(),
        "fitted_log_odds_slope_per_250_groups": float(fit.x[1]),
        "fitted_odds_ratio_per_250_groups": float(math.exp(fit.x[1])),
        "likelihood_ratio_statistic": likelihood_ratio,
        "chi_square_1df_p_value": float(chi2.sf(likelihood_ratio, 1)),
        "interpretation_rule": "p >= 0.05 means these six bins do not establish a continuing late slope; it does not prove stationarity",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--draws", type=int, default=500_000)
    parser.add_argument("--seed", type=int, default=20260820)
    parser.add_argument("--target-updates", type=int, default=276)
    parser.add_argument("--ceiling-groups", type=int, default=15000)
    args = parser.parse_args()
    if args.draws < 100_000:
        raise RiskAnalysisError("use at least 100000 Monte Carlo draws")

    audit, bins = load_audit(args.audit)
    observed_groups = audit["group_log_audit"]["attempted_groups"]
    observed_updates = audit["group_log_audit"]["optimizer_updates"]
    groups_remaining = args.ceiling_groups - observed_groups
    updates_needed = args.target_updates - observed_updates
    if groups_remaining <= 0 or updates_needed <= 0:
        raise RiskAnalysisError("target/ceiling do not extend the archived failure")

    windows = {str(groups): recent_window(bins, groups)
               for groups in (500, 1000, 1500, 2000)}
    required_rate = updates_needed / groups_remaining
    final_rate = windows["1500"]["nonflat_rate"]
    preceding_1500_updates = sum(row["updates"] for row in bins[-12:-6])
    preceding_1500_rate = preceding_1500_updates / 1500
    recent_decay_ratio = final_rate / preceding_1500_rate

    fixed = [
        fixed_rate_scenario(
            f"stationary_final_{window}_groups",
            f"Holds the empirical final-{window} non-flat rate fixed.",
            windows[str(window)]["nonflat_rate"], groups_remaining, updates_needed)
        for window in (500, 1000, 1500, 2000)
    ]
    fixed.extend([
        fixed_rate_scenario(
            "one_more_recent_ratio_drop_then_stationary",
            "Applies the preceding-to-final 1500-group rate ratio once more, then holds that lower rate fixed.",
            final_rate * recent_decay_ratio, groups_remaining, updates_needed),
        fixed_rate_scenario(
            "half_final_500_rate_then_stationary",
            "Immediately halves the final-500 rate, then holds it fixed.",
            windows["500"]["nonflat_rate"] / 2,
            groups_remaining, updates_needed),
        fixed_rate_scenario(
            "break_even_expected_rate",
            "Uses the rate at which expected future updates equal the 61 updates needed; this is not a safety threshold.",
            required_rate, groups_remaining, updates_needed),
        fixed_rate_scenario(
            "fixed_rate_0_5_percent",
            "Stress case below the break-even expected rate.",
            0.005, groups_remaining, updates_needed),
    ])

    rng = np.random.default_rng(args.seed)
    posterior = monte_carlo_stationary_posterior(
        rng, args.draws, windows["1500"]["updates"], 1500,
        groups_remaining, updates_needed)
    bootstrap = monte_carlo_recent_block_bootstrap(
        rng, args.draws, bins[-6:], groups_remaining, updates_needed)
    compounding = monte_carlo_compounding_decay(
        rng, args.draws, final_rate, recent_decay_ratio,
        groups_remaining, updates_needed)
    trend = late_logistic_trend_test(bins[-6:])

    result = {
        "schema": "exploratory-correctness-completion-risk/1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "classification": "exploratory CPU-only training-feasibility sensitivity analysis; not sealed efficacy evidence and not a primary-study endpoint",
        "source": {
            "audit_path": os.path.abspath(args.audit),
            "audit_sha256_raw": sha256_raw(args.audit),
            "script_path": os.path.abspath(__file__),
            "script_sha256_raw": sha256_raw(__file__),
            "source_fields": [
                "/group_log_audit/attempted_groups",
                "/group_log_audit/optimizer_updates",
                "/group_log_audit/bins_250_groups",
            ],
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "compute": "CPU only; CUDA_VISIBLE_DEVICES was empty at invocation",
        },
        "question": {
            "observed_groups": observed_groups,
            "observed_updates": observed_updates,
            "target_updates": args.target_updates,
            "ceiling_groups": args.ceiling_groups,
            "groups_remaining_after_archived_stop": groups_remaining,
            "updates_needed_after_archived_stop": updates_needed,
            "break_even_expected_nonflat_rate": required_rate,
        },
        "observed_recent_windows": windows,
        "preceding_1500": {
            "groups": [1501, 3000],
            "updates": preceding_1500_updates,
            "nonflat_rate": preceding_1500_rate,
        },
        "preceding_to_final_1500_rate_ratio": recent_decay_ratio,
        "late_trend_test": trend,
        "fixed_rate_scenarios": fixed,
        "monte_carlo_scenarios": [posterior, bootstrap, compounding],
        "monte_carlo_seed": args.seed,
        "monte_carlo_draws_per_scenario": args.draws,
        "interpretation": {
            "identified_single_failure_probability": False,
            "reason": "Only one trajectory is available and its non-flat probability is non-stationary; scenario probabilities answer conditional questions, not the unconditional chance that the live run succeeds.",
            "result": "The 15000-group ceiling is ample if the late rate plateaus, repeats recent-bin variability, or drops once more and then plateaus. It can still fail if the preceding-to-final multiplicative decline continues compounding across future 1500-group windows.",
            "decision": "Do not alter, stop, or extend the active revision-6 run based on this exploratory analysis.",
            "optional_next_diagnostic": "A separately labelled inference-only probe at the archived update-215 adapter can estimate its current independent-seed flat rate, but cannot prove how another 61 optimizer updates will change that rate.",
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(json.dumps({
        "out": args.out,
        "break_even_rate": required_rate,
        "late_trend_p": trend["chi_square_1df_p_value"],
        "stationary_final_1500_success": fixed[2]["exact_probability_reach_target_before_ceiling"],
        "posterior_stationary_success": posterior["monte_carlo_reach_target"]["probability"],
        "recent_block_bootstrap_success": bootstrap["monte_carlo_reach_target"]["probability"],
        "compounding_decay_success": compounding["monte_carlo_reach_target"]["probability"],
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except RiskAnalysisError as exc:
        raise SystemExit(f"FAIL: {exc}")
