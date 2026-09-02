"""
Decides how to split money across a list of investments, based on what you tell it
to care about most.

Every investment has three things: how risky it is (1 to 5 stars), how much it is
expected to earn, and how good it is for the environment (1 to 5). Nothing is best
at all three, so you have to choose what matters most. That is what the scenario does.

Run it with: python3 allocate.py cautious
             python3 allocate.py growth
             python3 allocate.py sustainable
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# each scenario says what to care about most. the three numbers always add up to 1,
# so cautious spends 60% of its attention on staying safe and growth spends 65% on earning
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

MAX_WEIGHT = 0.25   # no single investment gets more than a quarter of the money,
                    # so it never puts everything in one place


def load_assets(path="data/assets.csv"):
    return pd.read_csv(path)


# you cant add a percentage to a star rating. it is like adding your height to your
# shoe size, and the bigger number wins just for being bigger. so everything is put
# onto the same 0 to 1 scale first, where 0 is the lowest and 1 is the highest
def normalise(series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return series * 0 + 0.5
    return (series - lo) / (hi - lo)


def score_assets(df, weights):
    df["n_return"] = normalise(df["expected_return_pct"])
    df["n_impact"] = normalise(df["impact_score"])
    # a high return is good and a high impact score is good, but a high risk is bad.
    # so risk gets turned round here. without this the program would think the most
    # dangerous investment was the best one
    df["n_safety"] = 1 - normalise(df["risk_stars"])

    df["score"] = (
        df["n_return"] * weights["return"]
        + df["n_impact"] * weights["impact"]
        + df["n_safety"] * weights["safety"]
    )
    return df


def allocate(df, max_risk):
    """Turn the scores into percentages of the money, spread out and not too risky."""
    working = df.copy()

    while True:
        working["weight"] = working["score"] / working["score"].sum()
        working["weight"] = working["weight"].clip(upper=MAX_WEIGHT)
        working["weight"] = working["weight"] / working["weight"].sum()

        avg_risk = (working["weight"] * working["risk_stars"]).sum()
        if avg_risk <= max_risk or len(working) <= 3:
            break

        # the whole portfolio is still too risky, so take out the riskiest investment
        # and work it all out again. just making everything smaller would not help,
        # because the mix would stay exactly the same
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
