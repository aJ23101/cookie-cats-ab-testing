"""
experiment_analysis.py

Reusable helper functions for analyzing A/B experiments with binary
(conversion/retention) outcomes and continuous engagement outcomes.

Written for the Cookie Cats gate_30 vs. gate_40 experiment, but every
function is generic: pass in a DataFrame, the column names, and the
group labels, and it will work on any two-arm A/B test with a similar
shape (one row per randomized unit).

Dependencies: pandas, numpy, scipy, statsmodels
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint


# --------------------------------------------------------------------------
# 1. Experiment summary / data quality
# --------------------------------------------------------------------------

def experiment_summary(df: pd.DataFrame, id_col: str, group_col: str) -> dict:
    """
    Produce a data-quality / sanity-check summary for an experiment dataset.

    What it does: counts rows, unique units, duplicates, missing values,
    and the group split.
    Why we use it: before trusting any A/B result, we need to confirm the
    dataset is clean (one row per randomized unit, no leakage between arms).
    What the result means: a dict of facts an analyst should report before
    doing any statistical testing.
    """
    n_rows = len(df)
    n_unique_ids = df[id_col].nunique()
    n_duplicate_ids = df[id_col].duplicated().sum()
    n_duplicate_rows = df.duplicated().sum()
    missing = df.isnull().sum().to_dict()
    group_counts = df[group_col].value_counts().to_dict()
    group_share = df[group_col].value_counts(normalize=True).to_dict()

    # each unit should appear in exactly one group
    units_multi_group = (
        df.groupby(id_col)[group_col].nunique().gt(1).sum()
    )

    return {
        "n_rows": n_rows,
        "n_unique_ids": n_unique_ids,
        "n_duplicate_ids": int(n_duplicate_ids),
        "n_duplicate_rows": int(n_duplicate_rows),
        "missing_values": missing,
        "group_counts": group_counts,
        "group_share": group_share,
        "units_in_multiple_groups": int(units_multi_group),
    }


def randomization_check(
    df: pd.DataFrame,
    group_col: str,
    expected_ratio: dict | None = None,
) -> dict:
    """
    Sample Ratio Mismatch (SRM) check via a chi-square goodness-of-fit test.

    What it does: compares the observed split between arms to the expected
    split (default: equal allocation) using a chi-square test.
    Why we use it: if traffic is not split the way the randomization was
    designed, the experiment may be broken (e.g. a logging bug, a targeting
    bug) and the results should not be trusted regardless of the p-value on
    the outcome metric.
    What the result means: a small p-value (conventionally < 0.001 is used
    for SRM, since SRM checks are run on very large samples and should be
    conservative) suggests the allocation is NOT what was intended.
    """
    counts = df[group_col].value_counts()
    groups = list(counts.index)
    observed = counts.values.astype(float)
    n = observed.sum()

    if expected_ratio is None:
        expected_share = {g: 1 / len(groups) for g in groups}
    else:
        total = sum(expected_ratio.values())
        expected_share = {g: v / total for g, v in expected_ratio.items()}

    expected = np.array([expected_share[g] * n for g in groups])
    chi2, p_value = stats.chisquare(f_obs=observed, f_exp=expected)

    return {
        "groups": groups,
        "observed_counts": dict(zip(groups, observed.tolist())),
        "expected_counts": dict(zip(groups, expected.tolist())),
        "chi2_statistic": float(chi2),
        "p_value": float(p_value),
        "srm_detected": bool(p_value < 0.001),
    }


# --------------------------------------------------------------------------
# 2. Conversion / retention rate calculations
# --------------------------------------------------------------------------

def calculate_conversion_rate(df: pd.DataFrame, metric_col: str, group_col: str) -> pd.DataFrame:
    """
    Calculate conversion/retention rate (mean of a 0/1 or boolean column) per group.

    What it does: groups by `group_col` and computes the mean and count of
    `metric_col` (treated as a binary indicator).
    Why we use it: retention/conversion metrics are proportions, so the
    sample mean of a 0/1 column IS the rate.
    What the result means: a table of rate, successes, and sample size per
    group, which feeds directly into the proportion test.
    """
    grouped = df.groupby(group_col)[metric_col].agg(["mean", "sum", "count"])
    grouped = grouped.rename(columns={"mean": "rate", "sum": "successes", "count": "n"})
    return grouped


def calculate_lift(rate_control: float, rate_treatment: float) -> dict:
    """
    Calculate absolute and relative lift of treatment vs. control.

    What it does: computes (treatment - control) and (treatment - control) / control.
    Why we use it: absolute lift (percentage points) and relative lift (%)
    answer different business questions and should both be reported.
    What the result means: positive absolute_diff/relative_lift = treatment
    outperforms control on this metric; negative = control outperforms.
    """
    absolute_diff = rate_treatment - rate_control
    relative_lift = (rate_treatment - rate_control) / rate_control if rate_control != 0 else np.nan
    return {
        "control_rate": rate_control,
        "treatment_rate": rate_treatment,
        "absolute_diff": absolute_diff,
        "absolute_diff_pp": absolute_diff * 100,
        "relative_lift": relative_lift,
        "relative_lift_pct": relative_lift * 100 if not np.isnan(relative_lift) else np.nan,
    }


# --------------------------------------------------------------------------
# 3. Hypothesis testing for proportions
# --------------------------------------------------------------------------

def proportion_test(
    successes_control: int,
    n_control: int,
    successes_treatment: int,
    n_treatment: int,
    alternative: str = "two-sided",
) -> dict:
    """
    Two-proportion z-test comparing control vs. treatment.

    What it does: runs a two-sample z-test for proportions (via
    statsmodels.stats.proportion.proportions_ztest), which is appropriate
    for large-sample binary outcome comparisons like retention rates.
    Why we use it: retention is a binary (0/1) outcome per user, and with
    tens of thousands of independent users per arm, the normal
    approximation to the binomial is accurate (np and n(1-p) are both
    well above the usual rule-of-thumb of 5). A z-test for proportions is
    the standard, appropriate test here (equivalent to a chi-square test
    of independence for a 2x2 table in the two-sided case).
    What the result means: p_value < alpha indicates the observed
    difference is unlikely to arise from chance alone under the null
    hypothesis that both groups have the same true retention rate.
    """
    count = np.array([successes_treatment, successes_control])
    nobs = np.array([n_treatment, n_control])
    z_stat, p_value = proportions_ztest(count, nobs, alternative=alternative)
    return {
        "z_statistic": float(z_stat),
        "p_value": float(p_value),
        "alternative": alternative,
        "significant_at_0.05": bool(p_value < 0.05),
    }


def confidence_interval(
    successes: int,
    n: int,
    method: str = "wilson",
    alpha: float = 0.05,
) -> tuple:
    """
    Confidence interval for a single proportion.

    What it does: computes a (1 - alpha) CI for a proportion using the
    Wilson score interval by default.
    Why we use it: the Wilson interval has better coverage than the naive
    normal-approximation interval, especially away from p = 0.5, and is a
    standard choice for retention/conversion-rate reporting.
    What the result means: a range of plausible true population rates
    given the observed sample.
    """
    lower, upper = proportion_confint(successes, n, alpha=alpha, method=method)
    return float(lower), float(upper)


def diff_confidence_interval(
    successes_control: int,
    n_control: int,
    successes_treatment: int,
    n_treatment: int,
    alpha: float = 0.05,
) -> dict:
    """
    Confidence interval for the DIFFERENCE between two proportions
    (treatment - control), using the standard normal-approximation
    (Wald) interval on the difference.

    What it does: computes point estimate +/- z * SE, where SE is the
    pooled/unpooled standard error of the difference in proportions.
    Why we use it: the CI on the difference (not just each group's CI) is
    what actually tells us whether the effect is likely to be zero.
    What the result means: if the interval excludes 0, the difference is
    statistically significant at the corresponding alpha.
    """
    p1 = successes_control / n_control
    p2 = successes_treatment / n_treatment
    diff = p2 - p1
    se = np.sqrt(p1 * (1 - p1) / n_control + p2 * (1 - p2) / n_treatment)
    z = stats.norm.ppf(1 - alpha / 2)
    return {
        "diff": diff,
        "lower": diff - z * se,
        "upper": diff + z * se,
        "se": se,
        "alpha": alpha,
    }


# --------------------------------------------------------------------------
# 4. Bootstrap
# --------------------------------------------------------------------------

def bootstrap_effect(
    df: pd.DataFrame,
    metric_col: str,
    group_col: str,
    control_label,
    treatment_label,
    n_iterations: int = 10000,
    statistic: str = "mean",
    random_state: int = 42,
) -> dict:
    """
    Bootstrap the sampling distribution of (treatment - control) for a metric.

    What it does: repeatedly resamples each group WITH replacement (same
    size as the original group), recomputes the chosen statistic
    (default: mean) for each resampled group, and records the difference.
    Why we use it: bootstrapping estimates the uncertainty of the
    treatment effect without relying on a normality assumption -- useful
    as a cross-check against the analytical CI, and essential for metrics
    like the mean of a heavily skewed variable (e.g. game rounds) where
    the normal approximation is less trustworthy.
    What the result means: the 2.5th/97.5th percentiles of the bootstrap
    distribution form a 95% bootstrap confidence interval for the effect.
    """
    rng = np.random.default_rng(random_state)
    control_vals = df.loc[df[group_col] == control_label, metric_col].to_numpy()
    treatment_vals = df.loc[df[group_col] == treatment_label, metric_col].to_numpy()

    stat_fn = np.mean if statistic == "mean" else np.median

    n_c, n_t = len(control_vals), len(treatment_vals)
    diffs = np.empty(n_iterations)
    for i in range(n_iterations):
        c_sample = control_vals[rng.integers(0, n_c, n_c)]
        t_sample = treatment_vals[rng.integers(0, n_t, n_t)]
        diffs[i] = stat_fn(t_sample) - stat_fn(c_sample)

    lower, upper = np.percentile(diffs, [2.5, 97.5])
    return {
        "n_iterations": n_iterations,
        "statistic": statistic,
        "observed_diff": float(stat_fn(treatment_vals) - stat_fn(control_vals)),
        "bootstrap_mean_diff": float(diffs.mean()),
        "bootstrap_std": float(diffs.std()),
        "ci_lower": float(lower),
        "ci_upper": float(upper),
        "distribution": diffs,
    }


# --------------------------------------------------------------------------
# 5. Segment analysis
# --------------------------------------------------------------------------

def segment_analysis(
    df: pd.DataFrame,
    metric_col: str,
    group_col: str,
    segment_col: str,
    control_label,
    treatment_label,
) -> pd.DataFrame:
    """
    Compare the treatment effect on a binary metric across segments.

    What it does: for each level of `segment_col`, computes control rate,
    treatment rate, absolute difference, and a z-test p-value.
    Why we use it: an average effect can hide meaningful heterogeneity
    (e.g. the treatment might help highly-engaged users but hurt casual
    ones). Segment analysis makes this visible.
    What the result means: this is EXPLORATORY by construction. If the
    segment variable is measured post-treatment (i.e. it could itself be
    affected by the treatment), any differences across segments should
    NOT be interpreted causally -- see the caller's documentation for the
    multiple-comparisons caveat.

    Caution: if `segment_col` is derived from post-treatment behavior
    (e.g. engagement level based on total game rounds), segment membership
    itself may be an outcome of the treatment. Treat results as
    descriptive/hypothesis-generating only.
    """
    rows = []
    for seg_value, seg_df in df.groupby(segment_col, observed=True):
        rates = calculate_conversion_rate(seg_df, metric_col, group_col)
        if control_label not in rates.index or treatment_label not in rates.index:
            continue
        c = rates.loc[control_label]
        t = rates.loc[treatment_label]
        lift = calculate_lift(c["rate"], t["rate"])
        test = proportion_test(int(c["successes"]), int(c["n"]), int(t["successes"]), int(t["n"]))
        rows.append({
            "segment": seg_value,
            "n_control": int(c["n"]),
            "n_treatment": int(t["n"]),
            "control_rate": c["rate"],
            "treatment_rate": t["rate"],
            "absolute_diff_pp": lift["absolute_diff_pp"],
            "relative_lift_pct": lift["relative_lift_pct"],
            "p_value": test["p_value"],
            "significant_at_0.05": test["significant_at_0.05"],
        })
    return pd.DataFrame(rows)
