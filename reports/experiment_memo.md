# Experiment Memo: First Gate Placement (gate_30 vs gate_40)

**To:** Product Manager, Cookie Cats
**From:** Product Analytics
**Status:** Decision ready
**Population:** 90,189 new players

---

## Recommendation: **KEEP THE GATE AT LEVEL 30. Do not ship gate_40.**

Moving the first gate from level 30 to level 40 **reduced 7-day retention by 0.82
percentage points** (19.02% → 18.20%), a **4.3% relative decline**. The result is
statistically significant (p = 0.0016) and the confidence interval sits **entirely below
zero**. No metric in the experiment improved.

The decision is not close. We would be accepting a measurable retention cost in exchange
for no demonstrated benefit.

---

## 1. Business question

Cookie Cats places a forced-wait gate that blocks progression until the player waits, asks
friends, or pays. It paces the game and drives monetization. The question: **does moving
that first gate from level 30 to level 40 keep more players around?**

The theory in favour was that a later gate feels less punishing and lets players get more
invested before hitting friction. The data does not support it.

## 2. Experiment setup

| | |
|---|---|
| **Control** | `gate_30` — first gate at level 30 (current design), 44,700 players |
| **Treatment** | `gate_40` — first gate at level 40, 45,489 players |
| **Randomization** | Per player, at install |
| **Analysis** | Intent-to-treat — every randomized player counted in their assigned arm |
| **Split** | 49.56% / 50.44% |

## 3. Key metrics

| Role | Metric | Why |
|---|---|---|
| **Primary** | 7-day retention | Closest available proxy for habit formation and lifetime value. Critically, it is the only metric with enough time for players to actually *reach* the gate — most players are nowhere near level 30 on day 1. |
| Secondary | 1-day retention | Early signal; structurally insensitive to a change that only bites at level 30+ |
| Secondary | Total game rounds | Guardrail on engagement volume |

## 4. Results

| Metric | gate_30 | gate_40 | Difference | Relative | 95% CI | p-value | Read as |
|---|---|---|---|---|---|---|---|
| **7-day retention (primary)** | **19.02%** | **18.20%** | **−0.82 pp** | **−4.3%** | **[−1.33, −0.31] pp** | **0.0016** | **Statistically significant decline** |
| 1-day retention | 44.82% | 44.23% | −0.59 pp | −1.3% | [−1.24, +0.06] pp | 0.074 | Not detected — **43% power**, so not evidence of no effect |
| Game rounds (winsorized mean) | 49.14 | 48.85 | −0.28 | −0.6% | [−1.38, +0.82] | 0.62 | No detectable difference |

**Every metric's point estimate moves against the treatment.** Only 7-day retention reaches
statistical significance; the other two are inconclusive rather than reassuring. **No metric
favours `gate_40`.**

## 5. Statistical evidence

- **Test used:** two-proportion z-test — the standard test for comparing binary rates
  between two randomized groups at this sample size.
- **Well powered on the primary metric.** 89% power against the observed effect; the
  experiment was correctly sized for the question it answered.
- **Confirmed by bootstrap.** 10,000 resamples produced a 95% interval of
  [−1.34, −0.33] pp — matching the analytical interval to within 0.02 pp. **`gate_40` was
  worse in 99.9% of 10,000 simulated re-runs.**
- **Robust to outliers.** Excluding the single anomalous player (49,854 rounds) shifts the
  effect by 0.002 pp. The conclusion does not hinge on any one observation.
- **Mechanism is visible.** Control players visibly stall in the 30–39 round band
  (+0.79 pp vs treatment) — exactly where their gate sits. The feature genuinely shipped.
- **Falsification (negative-control) tests are largely supportive.** A gate can only affect a
  player who reaches it, and a player at level L must have played at least L rounds — so
  players with very few rounds encountered neither gate and should show no effect. They
  don't: <10 rounds shows −0.01 pp (p = 0.95) and <20 rounds shows −0.12 pp (p = 0.45).
  Meanwhile the effect is largest among players deep enough to reach a gate. That pattern is
  what a genuine causal effect looks like rather than a randomization artifact.

**Two caveats that a careful reader should have, stated up front:**

- **1-day retention is unresolved, not clean.** The experiment had only **43% power** to
  detect a D1 effect of the size observed. **The absence of statistical significance on D1
  must not be read as evidence of no effect.** The point estimate is negative (−0.59 pp),
  pointing the same way as the primary metric; we simply could not resolve it.
- **One falsification test came back borderline.** The <30-round subgroup — players who could
  not have reached either gate — shows −0.33 pp at **p = 0.049**, just under the 5%
  threshold. The magnitude is close to zero, but because the test is borderline, **this
  subgroup does not provide clean evidence of a zero effect** and should be read cautiously.
  The tighter subsets (<10, <20 rounds) are clean and this is one of six tests, so it is
  plausibly chance — but it is an unresolved internal-validity question, not a settled one.

## 6. Business impact

**Stated assumptions:** a cohort of 1,000,000 new players; measured retention rates hold;
the experiment population is representative of future players.

> Shipping `gate_40` would cost roughly **8,200 fewer players still active at day 7 per
> million new players** — with a plausible range of **3,100 to 13,300 fewer**.

Retention compounds: fewer D7 players means fewer D30 players, fewer eventual payers, and
a smaller base for organic growth.

**We deliberately do not convert this to revenue.** The dataset contains no ARPU or LTV
data, and any dollar figure would be invented. If Finance supplies an ARPU figure, the
conversion is one multiplication away — but the number must come from the business.

## 7. Risks and limitations

- **Retention is a proxy, not the objective.** A gate is a monetization mechanic. It is
  possible `gate_40` lowers retention while *raising* revenue per player. **This
  experiment cannot test that**, and it is the most important open question. If we had
  reason to expect a large revenue gain, the decision would warrant revisiting — but we
  would need the data to show it.
- **Sample-ratio deviation.** The split is 50.44/49.56, chi-square **p = 0.0086**. This does
  **not** cross our pre-specified SRM detection threshold of p < 0.001, so the experiment is
  not flagged as failed — but the deviation is documented as a potential experiment-health
  concern and is worth a look at the assignment service. Note that unequal arm sizes do not
  by themselves bias a rate comparison; the test accounts for them.
- **One falsification test is borderline.** Players with <30 rounds — who could not have
  reached either gate — showed −0.33 pp at **p = 0.049**. Because that is below the 5%
  threshold, **this subgroup does not give us clean evidence of a zero effect**, and we
  should not describe it as a passed check. Tighter subsets (<10, <20 rounds) are clean and
  this is one of six tests, so chance is a plausible explanation — but it remains
  unresolved, and together with the SRM deviation it is the strongest argument for a
  confirmatory re-run before treating this decision as permanent.
- **D1 retention is underpowered, not null.** 43% power against the observed effect; absence
  of significance is not evidence of absence of effect.
- **7 days is a short horizon.** We cannot see D30 or D90 effects.
- **No segment-level conclusions.** Engagement segments are defined by a post-treatment
  variable, so within-segment comparisons are not randomized comparisons. No segment
  result survived multiple-comparison correction. Nothing in this memo rests on one.
- **Only two positions tested.** We compared level 30 vs level 40. We know nothing about
  level 20, level 35, or no gate at all.

## 8. Next steps

1. **Ship nothing. Keep `gate_30`.** The current design wins on the primary metric.
2. **Test the opposite direction.** The most interesting implication is that the data is
   consistent with *earlier is better* — a hypothesis this experiment never tested. Run
   **gate_20 vs gate_30** as the next experiment.
3. **Instrument revenue before the next gate test.** The inability to observe ARPU is the
   binding limitation on every gate decision we will make. Add revenue-per-player and
   gate-encounter events to the experiment schema.
4. **Extend the observation window to 30 days** to confirm the retention gap persists
   rather than attenuating.
5. **Add level-progression tracking** so we can identify genuinely gate-exposed players
   rather than inferring exposure from round counts. Roughly 63% of this sample never
   reached level 30 — the effect among *exposed* players is necessarily larger than the
   0.82 pp headline, and we currently cannot measure it cleanly.

---

*Full analysis: `notebooks/01`–`04`. Reusable statistical module: `src/experiment_analysis.py`.*
