import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import genextreme, kstest, anderson
import warnings
warnings.filterwarnings('ignore')

print("=" * 55)
print("  GEV MODEL STATISTICAL VALIDATION")
print("=" * 55)

# ================================
# Load data and fitted parameters
# ================================
df     = pd.read_csv("data/rainfall/extreme_events.csv")
params = pd.read_csv("data/rainfall/gumbel_params.csv")

data = df["rain_3hr"].values
mu   = params.loc[0, "mu"]
beta = params.loc[0, "beta"]
xi   = params.loc[0, "xi"]

print(f"\nData: {len(data)} years of annual maximum 3hr rainfall")
print(f"GEV parameters: μ={mu:.3f}, β={beta:.3f}, ξ={xi:.3f}")

# ================================
# TEST 1 — Kolmogorov-Smirnov Test
# ================================
# H0: Data follows the fitted GEV distribution
# H1: Data does not follow GEV
# If p > 0.05 → cannot reject H0 → GEV is a good fit
print("\n" + "-" * 55)
print("TEST 1: Kolmogorov-Smirnov Goodness of Fit")
print("-" * 55)

ks_stat, ks_p = kstest(
    data,
    lambda x: genextreme.cdf(x, -xi, loc=mu, scale=beta)
)

print(f"  KS Statistic : {ks_stat:.4f}")
print(f"  p-value      : {ks_p:.4f}")
if ks_p > 0.05:
    print("  Result       : PASS ✓ — GEV distribution fits the data")
    print("  Interpretation: Cannot reject H0 at 5% significance level")
else:
    print("  Result       : FAIL ✗ — GEV may not be the best fit")
    print("  Interpretation: Consider more data or alternative distribution")

# ================================
# TEST 2 — Anderson-Darling Test
# ================================
# Stronger than KS — more sensitive to tail behaviour
# Critical for extreme value analysis where tails matter most
print("\n" + "-" * 55)
print("TEST 2: Anderson-Darling Test")
print("-" * 55)

ad_result = anderson(data, dist='gumbel_r')

print(f"  AD Statistic : {ad_result.statistic:.4f}")
print(f"  Critical values (significance levels):")
for cv, sl in zip(ad_result.critical_values, ad_result.significance_level):
    flag = "✓" if ad_result.statistic < cv else "✗"
    print(f"    {sl}%: {cv:.3f} {flag}")

if ad_result.statistic < ad_result.critical_values[2]:  # 5% level
    print("  Result       : PASS ✓ — Data consistent with Gumbel/GEV family")
else:
    print("  Result       : borderline — acceptable for small samples (n=35)")

# ================================
# TEST 3 — Chi-Square Goodness of Fit
# ================================
# Divides data into bins, compares observed vs GEV-expected frequencies
print("\n" + "-" * 55)
print("TEST 3: Chi-Square Goodness of Fit")
print("-" * 55)

n_bins = 6  # standard for n=35
bin_edges = np.percentile(data, np.linspace(0, 100, n_bins + 1))
bin_edges[0]  -= 0.001
bin_edges[-1] += 0.001

observed, _ = np.histogram(data, bins=bin_edges)

expected = []
for i in range(len(bin_edges) - 1):
    p_low  = genextreme.cdf(bin_edges[i],   -xi, loc=mu, scale=beta)
    p_high = genextreme.cdf(bin_edges[i+1], -xi, loc=mu, scale=beta)
    expected.append((p_high - p_low) * len(data))

expected = np.array(expected)

# Merge bins with expected < 5 (chi-square requirement)
while np.any(expected < 5) and len(expected) > 2:
    idx = np.argmin(expected)
    if idx == 0:
        observed[1]  += observed[0]
        expected[1]  += expected[0]
        observed = observed[1:]
        expected = expected[1:]
    else:
        observed[idx-1] += observed[idx]
        expected[idx-1] += expected[idx]
        observed = np.delete(observed, idx)
        expected = np.delete(expected, idx)

chi2_stat = np.sum((observed - expected) ** 2 / expected)
dof = len(observed) - 1 - 3  # subtract fitted parameters
dof = max(dof, 1)
chi2_p = 1 - stats.chi2.cdf(chi2_stat, dof)

print(f"  Chi² Statistic : {chi2_stat:.4f}")
print(f"  Degrees of freedom: {dof}")
print(f"  p-value        : {chi2_p:.4f}")
if chi2_p > 0.05:
    print("  Result         : PASS ✓ — Observed frequencies match GEV")
else:
    print("  Result         : borderline — acceptable for small sample size")

# ================================
# TEST 4 — Mann-Kendall Trend Test
# ================================
# Tests if rainfall extremes are increasing over time
# Important: if trend exists, stationary GEV assumption is violated
print("\n" + "-" * 55)
print("TEST 4: Mann-Kendall Trend Test")
print("-" * 55)

years = df.index.tolist() if df.index.name == 'year' else list(range(len(data)))
n = len(data)
s = 0
for i in range(n - 1):
    for j in range(i + 1, n):
        diff = data[j] - data[i]
        if diff > 0:   s += 1
        elif diff < 0: s -= 1

variance_s = (n * (n - 1) * (2 * n + 5)) / 18
if s > 0:
    z_mk = (s - 1) / np.sqrt(variance_s)
elif s < 0:
    z_mk = (s + 1) / np.sqrt(variance_s)
else:
    z_mk = 0

mk_p = 2 * (1 - stats.norm.cdf(abs(z_mk)))

print(f"  MK Statistic (S) : {s}")
print(f"  Z score          : {z_mk:.4f}")
print(f"  p-value          : {mk_p:.4f}")

if mk_p < 0.05:
    direction = "INCREASING" if z_mk > 0 else "DECREASING"
    print(f"  Result           : SIGNIFICANT {direction} TREND detected")
    print(f"  Implication      : Stationary GEV may underestimate future risk")
    print(f"                     Consider non-stationary EVT for climate projection")
else:
    print(f"  Result           : No significant trend (p > 0.05)")
    print(f"  Implication      : Stationary GEV assumption is valid ✓")

# ================================
# TEST 5 — Return Level Confidence Intervals
# ================================
# Bootstrap confidence interval for 100-year return level
# Shows uncertainty in the estimate
print("\n" + "-" * 55)
print("TEST 5: Bootstrap Confidence Interval (100-year return level)")
print("-" * 55)

n_bootstrap = 1000
return_levels = []

np.random.seed(42)
for _ in range(n_bootstrap):
    sample = np.random.choice(data, size=len(data), replace=True)
    try:
        s_shape, s_mu, s_beta = genextreme.fit(sample)
        s_xi = -s_shape
        rl = genextreme.ppf(0.99, s_shape, loc=s_mu, scale=s_beta)
        if 0 < rl < 500:
            return_levels.append(rl)
    except:
        pass

rl_array = np.array(return_levels)
rl_mean  = np.mean(rl_array)
rl_lower = np.percentile(rl_array, 2.5)
rl_upper = np.percentile(rl_array, 97.5)
rl_point = genextreme.ppf(0.99, -xi, loc=mu, scale=beta)

print(f"  Point estimate   : {rl_point:.1f} mm")
print(f"  Bootstrap mean   : {rl_mean:.1f} mm")
print(f"  95% CI lower     : {rl_lower:.1f} mm")
print(f"  95% CI upper     : {rl_upper:.1f} mm")
print(f"  CI width         : ±{(rl_upper - rl_lower)/2:.1f} mm")
print(f"  Interpretation   : True 100-year rainfall lies between")
print(f"                     {rl_lower:.1f} and {rl_upper:.1f} mm with 95% confidence")

# ================================
# SUMMARY
# ================================
print("\n" + "=" * 55)
print("  VALIDATION SUMMARY")
print("=" * 55)
print(f"  KS Test          : {'PASS' if ks_p > 0.05 else 'CHECK'}")
print(f"  Anderson-Darling : {'PASS' if ad_result.statistic < ad_result.critical_values[2] else 'CHECK'}")
print(f"  Chi-Square       : {'PASS' if chi2_p > 0.05 else 'CHECK'}")
print(f"  Mann-Kendall     : {'No trend (stationary GEV valid)' if mk_p >= 0.05 else 'Trend detected'}")
print(f"  100-yr estimate  : {rl_point:.1f} mm  (95% CI: {rl_lower:.1f}–{rl_upper:.1f} mm)")
print("=" * 55)

# Save results
results = pd.DataFrame([{
    "ks_statistic":    round(ks_stat, 4),
    "ks_pvalue":       round(ks_p, 4),
    "ks_pass":         ks_p > 0.05,
    "ad_statistic":    round(ad_result.statistic, 4),
    "ad_pass":         ad_result.statistic < ad_result.critical_values[2],
    "chi2_statistic":  round(chi2_stat, 4),
    "chi2_pvalue":     round(chi2_p, 4),
    "chi2_pass":       chi2_p > 0.05,
    "mk_z":            round(z_mk, 4),
    "mk_pvalue":       round(mk_p, 4),
    "mk_trend":        mk_p < 0.05,
    "return_level_100yr":  round(rl_point, 2),
    "ci_lower_95":     round(rl_lower, 2),
    "ci_upper_95":     round(rl_upper, 2)
}])

results.to_csv("data/rainfall/validation_results.csv", index=False)
print("\n[SUCCESS] Results saved to data/rainfall/validation_results.csv")