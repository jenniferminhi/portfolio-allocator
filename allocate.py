"""
Splits an investment across a list of assets, based on the scenario you choose.

Every asset has a risk rating out of 5, an expected return, and an impact score
for sustainability. Nothing wins on all three, so the scenario decides which
one matters most.

Run it with: python3 allocate.py cautious
             python3 allocate.py growth
             python3 allocate.py sustainable
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# each scenario's three weights add up to 1
SCENARIOS = {
    "cautious":    {"return": 0.25, "impact": 0.15, "safety": 0.60,
                    "max_risk": 2.5, "note": "protect the money first"},
    "balanced":    {"return": 0.40, "impact": 0.25, "safety": 0.35,
                    "max_risk": 3.2, "note": "steady growth without extremes"},
    "growth":      {"return": 0.65, "impact": 0.10, "safety": 0.25,
                    "max_risk": 4.0, "note": "accept risk to chase return"},
    "sustainable": {"return": 0.30, "impact": 0.50, "safety": 0.20,
                    "max_risk": 3.5, "note": "sustainability weighted heaviest"},
}

MAX_WEIGHT = 0.25   # no single asset takes more than a quarter of the money


def load_assets(path="data/assets.csv"):
    return pd.read_csv(path)


# you cant add a percentage to a star rating, so everything goes on the same 0 to 1 scale first
def normalise(series):
    """Rescale a column onto 0 to 1, so a return percentage and a star rating
    can be compared against each other."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return series * 0 + 0.5
    return (series - lo) / (hi - lo)


def score_assets(df, weights):
    df["n_return"] = normalise(df["expected_return_pct"])
    df["n_impact"] = normalise(df["impact_score"])
    # risk gets flipped, otherwise the riskiest asset comes out best, which is backwards
    df["n_safety"] = 1 - normalise(df["risk_stars"])

    df["score"] = (
        df["n_return"] * weights["return"]
        + df["n_impact"] * weights["impact"]
        + df["n_safety"] * weights["safety"]
    )
    return df


def allocate(df, max_risk):
    """Turn scores into percentages, keeping the portfolio diversified and
    under the scenario's risk ceiling."""
    working = df.copy()

    while True:
        working["weight"] = working["score"] / working["score"].sum()
        working["weight"] = working["weight"].clip(upper=MAX_WEIGHT)
        working["weight"] = working["weight"] / working["weight"].sum()

        avg_risk = (working["weight"] * working["risk_stars"]).sum()
        if avg_risk <= max_risk or len(working) <= 3:
            break

        # still too risky, so drop the riskiest asset and work it out again.
        # scaling everything down would not help - the mix would stay the same
        working = working.drop(working["risk_stars"].idxmax())

    return working


def summarise(df):
    return {
        "return": (df["weight"] * df["expected_return_pct"]).sum(),
        "risk": (df["weight"] * df["risk_stars"]).sum(),
        "impact": (df["weight"] * df["impact_score"]).sum(),
    }


def make_chart(df, scenario, path):
    ordered = df.sort_values("weight", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    colours = plt.cm.viridis(ordered["risk_stars"] / 5)
    ax.barh(ordered["asset"], ordered["weight"] * 100, color=colours)
    ax.set_xlabel("Share of portfolio (%)")
    ax.set_title(f"Allocation — {scenario} scenario\n(darker = lower risk)")
    for y, w in enumerate(ordered["weight"]):
        ax.text(w * 100 + 0.3, y, f"{w*100:.1f}%", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"Chart saved to {path}")


def main():
    scenario = sys.argv[1] if len(sys.argv) > 1 else "balanced"
    if scenario not in SCENARIOS:
        print(f"Unknown scenario. Choose from: {', '.join(SCENARIOS)}")
        return

    weights = SCENARIOS[scenario]
    df = score_assets(load_assets(), weights)
    portfolio = allocate(df, weights["max_risk"]).sort_values("weight", ascending=False)
    stats = summarise(portfolio)

    print(f"\nPORTFOLIO ALLOCATION — {scenario.upper()} ({weights['note']})")
    print("=" * 74)
    for _, row in portfolio.iterrows():
        print(f"{row['asset']:<34} {row['weight']*100:5.1f}%   "
              f"risk {row['risk_stars']}★  return {row['expected_return_pct']:.1f}%  "
              f"impact {row['impact_score']}")
    print("=" * 74)
    print(f"Expected return   {stats['return']:.2f}%")
    print(f"Average risk      {stats['risk']:.2f} stars (ceiling {weights['max_risk']})")
    print(f"Average impact    {stats['impact']:.2f} out of 5")

    dropped = set(df["asset"]) - set(portfolio["asset"])
    if dropped:
        print(f"\nExcluded for pushing average risk above the ceiling: {', '.join(dropped)}")

    out = portfolio[["asset", "asset_class", "risk_stars",
                     "expected_return_pct", "impact_score", "weight"]]
    out.to_csv(f"output/allocation_{scenario}.csv", index=False)
    print(f"\nSaved to output/allocation_{scenario}.csv")
    make_chart(portfolio, scenario, f"output/allocation_{scenario}.png")


if __name__ == "__main__":
    main()
