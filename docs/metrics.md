# AdaptFit metric definitions (trend engine)

Implemented in `backend/app/metrics.py` (pure functions) and `backend/app/metrics_service.py` (database read and store). The LLM never computes these; it only explains them (FR-9, NFR-7). When data is thin the engine returns `not_enough_data` and stores nothing. The same content, with the evidence discussion, is in the Word/Docs document "AdaptFit Metrics and Formulas".

## Summary

| Metric (`metric_type`) | Formula | Minimum data | Unit |
|---|---|---|---|
| `bmr_kcal` | Men: 10w + 6.25h - 5a + 5. Women: 10w + 6.25h - 5a - 161 (Mifflin-St Jeor) | weight, height, age, sex | kcal/day (range +/-10%) |
| `tdee_kcal` | BMR x activity factor: sedentary 1.2, light 1.375, moderate 1.55, very active 1.725, extra active 1.9 | BMR inputs + activity level | kcal/day (range +/-10%) |
| `expected_loss_kg_per_week` | min(max(D, 0) x 7 / 7700, 0.01 x weight) where D = TDEE - intake, or 250/500/750 for a small/moderate/large deficit level | TDEE + **optional** intake or deficit level | kg/week |
| `muscle_gain_kg_per_week` | weight x r x s, r by training level (below), s = 1 men, 0.5 women | weight, training level, sex | kg/week (low-high range) |
| `weight_trend_kg_per_week` | (mean weight in (T-14, T] - mean weight in (T-28, T-14]) / 2 | 1 point in each window | kg/week |
| `adherence_pct` | sum(min(completed, scheduled)) / sum(scheduled) x 100 over the last 4 logged weeks | 2 weeks with a schedule | % |
| `sleep_consistency_min` | (SD of bed minutes since 18:00 + SD of wake minutes) / 2, sample SD, last 4 entries | 3 entries with both times | minutes (lower = steadier) |
| `strength_progression_pct_per_week:<exercise>` | (last e1RM - first e1RM) / first e1RM / weeks between, e1RM = w x (1 + reps/30), best set per date | 2 dates at least 7 days apart | %/week |
| `loss_vs_expected_ratio` | Q = weight trend / -(expected loss). Below 0.75 slower than expected; 0.75 to 1.25 on track; above 1.25 faster than expected (flag for safety) | weight trend + expected loss | ratio |

Muscle-gain rates r (weekly, fraction of body weight): novice 0.0023-0.0035, intermediate 0.0012-0.0023, advanced 0.0006-0.0012. **This is a practitioner heuristic, not a peer-reviewed table.** The app labels it "heuristic".

## Rules the code follows
- **Calorie input is optional (CR-3).** Intake wins over deficit level; with neither, expected loss is `not_enough_data`. A zero or negative deficit gives 0.0, never a negative loss.
- **Expected loss is an early-weeks upper bound.** Hall et al. (2011) show the static 3,500 kcal/lb rule overestimates long-term loss. The result is labelled "early-weeks estimate".
- **Week** = Monday-start calendar week of `checkin_date`. A **completed session** is a distinct `session_day` in that week's workout logs, so four exercises in one session count once.
- **Weight date** = `COALESCE(checkin_date, date(created_at))`, so the onboarding snapshot counts.
- **Bedtime** is minutes since 18:00 so 23:30 (330) and 00:30 (390) are 60 apart.
- **Epley** is trusted only for 1 to 10 reps and a positive load.
- Results are stored at full precision; round only for display. `not_enough_data` results are never stored.

## Worked examples (all are unit tests)
- Man, 70 kg, 175 cm, 21, moderate: BMR 1693.75, TDEE 2625 (range 2360-2890).
- TDEE 2625, intake 2125: D = 500, expected loss 0.45 kg/week. A 4000 kcal TDEE at 1500 intake is capped at 1% of 60 kg = 0.6.
- 70 kg novice man: realistic muscle gain 0.16-0.24 kg/week; woman half.
- Weeks (3,3),(3,2),(3,3),(3,1): 9/12 = 75.0%. Weeks (3,3),(4,3): 6/7 = 85.7%.
- Older mean 72.0, recent mean 71.6: -0.2 kg/week.
- 60 kg x 8 gives e1RM 76.0; 65 kg x 8 gives 82.3.
- Beds 23:00, 23:30, 00:00, 23:15 and wakes 06:30, 06:30, 07:00, 06:45: about 20.0 min.
- Demo persona "Sam" (`python -m app.demo_seed`): adherence 91.7%, weight trend -0.425 kg/week, expected loss 0.455, ratio 0.935 (on track).

## Evidence and verification status
Opened in full: Hall et al. 2011 (*The Lancet*). Title and link confirmed only: Frankenfield 2005 and 2013, Morton 2018, Ralston 2017 and 2018, Windred 2024. From memory, check before citing: Mifflin 1990 link. The strength benchmark for the study comparison is **not yet sourced**: extract a number from Ralston et al. and cite the table. Until then it is labelled "illustrative". Full references with links are in the Docs document.

## Limitations (state these in the report)
- Self-reported, so adherence and sleep are only as honest as the logs.
- Weight trend compares two windows; it is noisy and ignores water-weight swings.
- Mifflin-St Jeor can be off by about 10% for an individual.
- Sleep consistency is a plain SD in minutes, not the validated Sleep Regularity Index. Windred et al. (2024) link regularity to mortality, but a 2025 analysis found the result depends on which software computes the index.
- These are descriptive coaching metrics, not clinical measures.
