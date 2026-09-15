# Prompt for Claude CLI — build the Power BI dashboard

Open a terminal in the **repo root** (`cookie-cats-ab-testing/`), run `claude`, and paste the
prompt below.

Running from the repo root matters: Claude needs to read the CSVs in `powerbi/data/` and the
analysis in `README.md` to get the numbers and the caveats right.

---

## The prompt — copy everything between the lines

---

I need you to help me build a Power BI dashboard for an A/B test analysis that's already
complete. Read these files first so you have the full context:

- `README.md` — the analysis case study, with all headline numbers and limitations
- `reports/experiment_memo.md` — the one-page stakeholder recommendation
- `powerbi/measures.dax` — DAX measures I've already written
- `powerbi/data/*.csv` — nine pre-built tables ready to import

**Background.** This is a mobile game experiment (Cookie Cats) testing whether the first
progression gate should move from level 30 to level 40, across 90,189 players. The conclusion
is **keep gate 30**: 7-day retention dropped 0.82 percentage points (p = 0.0016, 95% CI
[−1.33, −0.31] pp). The analysis is finished and verified — do not recompute or second-guess
the statistics, and do not change any numbers.

**What I want.** A four-page Power BI report that a hiring manager could open and understand
in two minutes, and that a data-savvy interviewer could interrogate for twenty. I'm building
it in Power BI Desktop myself — I need you to give me the exact steps, not do it for me.

**Please produce:**

1. **An import plan.** Which of the nine CSVs to load, what each one is for, which columns to
   hide from the report view, what data types and formatting to set (percentages, decimal
   places), and which columns need "Sort by column" applied so categories order correctly
   (there are `_sort` columns for this — `engagement_sort`, `round_band_sort`,
   `gate_exposure_sort`, `segment_sort`, `sort_order`).

2. **The data model.** Tell me which relationships to create between `player_facts` and the
   results tables — and importantly, tell me where NOT to create one. Several results tables
   are standalone lookups that should stay disconnected. Explain why, because getting this
   wrong silently breaks the measures.

3. **A page-by-page build spec.** For each of the four pages: which visuals, which fields go
   in which wells, which measures, and what the page is supposed to answer. Structure:
   - **Page 1 — Executive summary.** The recommendation, the headline effect, business impact.
     Someone should be able to read the decision without scrolling.
   - **Page 2 — Experiment health.** Sample sizes, SRM, data quality, the outlier, power.
   - **Page 3 — Results deep dive.** Retention by arm with confidence intervals, engagement
     bands showing the gate mechanism, segment analysis.
   - **Page 4 — Statistical evidence.** Bootstrap distribution, falsification tests, the
     CI-vs-bootstrap comparison.

4. **Any additional DAX** the visuals need beyond what's in `measures.dax`.

**Design constraints:**

- Two-colour categorical scheme, colourblind-safe: control `gate_30` = `#2a78d6` (blue),
  treatment `gate_40` = `#eb6834` (orange). Use these consistently on every page — the same
  arm must never change colour between visuals.
- Supporting colours: primary text `#0b0b0b`, secondary `#52514e`, muted/axis `#898781`,
  gridlines `#e1e0d9`, page background `#f9f9f7`, card background `#fcfcfb`, red for a
  negative/critical result `#d03b3b`.
- No pie charts, no 3D, no dual-axis charts, no decorative visuals. Every visual must answer a
  stated question.
- Percentage-point differences should always show their sign and their confidence interval —
  never a bare point estimate.

**Statistical guardrails — these matter more than the visuals.** The analysis is deliberately
careful about several things, and the dashboard must not undo that:

- **1-day retention is NOT a clean null.** It had only 43% power. Any visual showing it must
  label it "not detected — not evidence of no effect", never "no impact" or a green tick.
- **Segment analysis is exploratory only.** Engagement segments are defined by a
  post-treatment variable, so within-segment comparisons are not randomized comparisons. No
  segment survived multiple-comparison correction. The page must say so on the page, not in a
  tooltip.
- **One falsification test is borderline** (<30 rounds, p = 0.049). Do not present the
  falsification tests as uniformly passed. Show the borderline one honestly.
- **SRM:** p = 0.0086 does **not** cross the pre-specified p < 0.001 threshold, so it is not
  flagged as a failure — but it is documented as a health concern. Word it precisely.
- **No revenue figures.** There is no revenue data. Business impact is expressed in retained
  players only, with its assumptions labelled on the page.
- The `≥40 rounds` subgroup effect (−1.78 pp) is **selected on a post-treatment variable** and
  is not a causal estimate. Never headline it.

**Output format.** Give me numbered steps I can follow in Power BI Desktop, grouped by page,
with exact field names and visual types. Write a `powerbi/BUILD_GUIDE.md` file with the whole
thing so I can work through it offline. Ask me about anything ambiguous before writing it.

---

## After Claude gives you the guide

Work through it in Power BI Desktop, then save as `powerbi/cookie_cats_dashboard.pbix`.

If you want the file to be diff-able in git, use **File → Save as → Power BI project (.pbip)**
instead — that saves the report as folders of JSON/TMDL text rather than one binary blob, so
GitHub can show what changed between versions. The `.gitignore` already has a Power BI section
covering both.

## Follow-up prompts worth having ready

Once the first version exists, these tend to be the useful next asks:

- *"Review my dashboard against the statistical guardrails in the original prompt. I'll describe each page — tell me where a visual overstates what the analysis supports."*
- *"Write the tooltip text for every visual on page 3, explaining what the reader is looking at in plain business language."*
- *"Add a 'What would change our mind?' text panel to page 1, based on the limitations in README.md section 10."*
- *"My manager says the dashboard is too statistical. Rewrite the page 1 titles and labels for a non-technical product audience, without weakening any of the caveats."*
