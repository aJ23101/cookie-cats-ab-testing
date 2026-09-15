# Power BI assets

Everything needed to build a Power BI dashboard on top of the Cookie Cats experiment
analysis. The statistics are pre-computed in Python and verified against the notebooks —
Power BI handles presentation, not inference.

```
powerbi/
├── data/                    9 import-ready CSVs
├── measures.dax             DAX measures, including a live z-test
├── CLAUDE_PROMPT.md         Prompt for building the dashboard with Claude CLI
└── README.md                This file
```

## Why there is no .pbix in the repo

A `.pbix` is a proprietary binary (a zipped VertiPaq model plus internal layout blobs) and
cannot be authored programmatically — there is no writer library for it. So this folder ships
the **contents** of a dashboard rather than a fake file: the modelled data, the measures, and
a build spec.

The built dashboard lives here as **`cookie-cats-ab-testing.pbix`** and is committed
deliberately — this is a portfolio repo, and being able to download and open the dashboard is
the point.

Worth knowing: a `.pbix` is a binary blob git cannot diff, so every save adds its full size to
history again. If that becomes annoying, save as **File → Save as → Power BI project
(`.pbip`)** instead, which writes JSON/TMDL text folders that git *can* diff. The `.gitignore`
has both options documented.

## The tables

| Table | Rows | Grain | Purpose |
|---|---|---|---|
| `player_facts.csv` | 90,189 | One row per player | The fact table. Drives all live/sliceable measures. |
| `experiment_results.csv` | 2 | One row per metric | Canonical headline results — rates, lift, CI, p-value, projected impact. |
| `power_analysis.csv` | 2 | One row per metric | MDE and achieved power. **The source for the D1 caveat.** |
| `segment_results.csv` | 6 | Metric × segment | Segment effects with Bonferroni / Holm / FDR corrections. |
| `falsification_results.csv` | 7 | One row per subgroup | Negative-control tests by gate exposure, with verdicts. |
| `engagement_bands.csv` | 9 | One row per round band | Distribution by arm — shows the gate mechanism. |
| `bootstrap_distribution.csv` | 10,000 | One row per resample | Bootstrap histogram source. |
| `experiment_health.csv` | 8 | One row per check | Data-quality and experiment-health scorecard. |
| `decision_summary.csv` | 1 | Single row | The recommendation and its headline evidence. |

### Fields worth knowing about in `player_facts.csv`

- `retention_1_flag` / `retention_7_flag` — integer 0/1, **not** boolean. DAX cannot `SUM()` a
  boolean column, so these are pre-cast.
- `gate_exposure` — which gates a player could possibly have reached, derived from round count
  (a player at level L must have played ≥ L rounds). This is what makes the falsification
  tests possible.
- `is_outlier` — flags the single 49,854-round player, so engagement measures can exclude them.
- `engagement_sort`, `round_band_sort`, `gate_exposure_sort` — numeric sort keys. Apply these
  via **Column tools → Sort by column**, or categories will order alphabetically
  (`High, Low, Medium`) instead of logically.

## Measures

`measures.dax` has two kinds, and the distinction matters:

- **Live measures** (sections 1–5) recompute under whatever filters are applied — including a
  full two-proportion z-test written in DAX via `NORM.S.DIST`. Slice by engagement segment and
  the p-value updates. Good for exploration.
- **Headline measures** (section 6) read the pre-computed results table and ignore slicers.
  Use these on the executive page so the cards always match the README.

> **A caution on the live measures.** Because they recompute for any slice, they make it easy
> to produce a significant-looking result by slicing until one appears. That is exactly the
> multiple-comparisons trap the analysis corrects for. Treat anything the live measures
> surface on a filtered view as **exploratory**, never as a finding.

## Statistical guardrails for the dashboard

The analysis is deliberately careful; a dashboard can easily undo that with a green tick in
the wrong place. Carry these through:

| Item | How it must be presented |
|---|---|
| 1-day retention | "Not detected — **43% power**, not evidence of no effect". Never a green tick or "no impact". |
| Segment analysis | Exploratory only. Post-treatment split; no segment survives correction. Label on the page. |
| Falsification tests | Not uniformly passed — the `<30 rounds` test is borderline (p = 0.049). Show it. |
| SRM | p = 0.0086 does **not** cross the pre-specified p < 0.001 threshold; documented as a health concern. |
| `≥40 rounds` effect | Selected on a post-treatment variable. Not causal. Never headline it. |
| Business impact | Retained players only. No revenue data exists — state the assumptions on the page. |

## Regenerating the data

The CSVs are derived from `data/cookie_cats.csv` via `src/experiment_analysis.py`. If the
source data or analysis changes, rebuild them rather than editing by hand.
