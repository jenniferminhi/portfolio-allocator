# Portfolio Allocator

A Python tool that splits an investment across a list of assets, depending on what you
tell it to prioritise.

![Cautious allocation](output/allocation_cautious.png)

## Why I built it

At an Aviva Investors insight day I was put in a team of four and given 15 minutes to
decide how to split an investment across different asset classes, then justify it against
the firm's priorities including sustainability. Each option came with a risk rating out
of five stars, an expected return and an impact score. Our team won the presentation.

The hard part was that nothing won on all three measures. The highest returns carried the
highest risk, and the options with the strongest impact were rarely the most profitable.
We had to decide what we were optimising for and defend it.

I built this so the trade-off is written down rather than argued once. Change the scenario
and you can see the answer change.

This is my second Python project.

## How it decides

Every asset has a risk rating from 1 to 5, an expected return, and an impact score.

The three are measured in completely different units, so each one is first rescaled onto
0 to 1 — otherwise you would be adding a percentage to a star rating. Risk gets flipped
into safety, because low risk is the good direction.

Each asset then gets a weighted score, using the weights from whichever scenario you
picked. Scores become percentages of the portfolio, with two rules on top:

- no asset takes more than 25%, so the money stays spread out
- the portfolio's average risk has to stay under the scenario's ceiling. If it doesn't,
  the riskiest asset is dropped and the whole thing is recalculated

The second rule is the interesting one. Scaling everything down proportionally wouldn't
lower the average risk, because the mix would stay the same. Removing a holding actually
changes it.

## The scenarios

| Scenario | Return | Impact | Safety | Risk ceiling |
|---|---|---|---|---|
| `cautious` | 25% | 15% | 60% | 2.5 stars |
| `balanced` | 40% | 25% | 35% | 3.2 stars |
| `growth` | 65% | 10% | 25% | 4.0 stars |
| `sustainable` | 30% | 50% | 20% | 3.5 stars |

## Running it

```bash
pip install pandas matplotlib
python3 allocate.py cautious
python3 allocate.py growth
```

## What the trade-off looks like

| | cautious | growth |
|---|---|---|
| Top holding | UK government bonds, 14.3% | Emerging market equities, 14.0% |
| Expected return | 5.53% | 6.68% |
| Average risk | 2.46 stars | 3.09 stars |
| Average impact | 3.17 | 2.94 |

One extra percentage point of return costs 0.63 of a risk star and 0.23 of impact. That
comparison is the whole point of the tool.

## The data

`data/assets.csv` holds illustrative figures for demonstrating the method, not live
market data.

## What I'd change next

Real return figures from published fund factsheets instead of illustrative ones, and a
minimum allocation per asset class so the portfolio can't drop bonds entirely.
