# Changing requirements (from the metrics work, 9 Oct 2026)

Track each as a change request against the proposal's FR and NFR list. Calorie input is **optional** (decided 9 Oct).

| ID | The system shall | Type | Schema or UI impact | Built? |
|---|---|---|---|---|
| CR-1 | Collect age (or date of birth) and sex at onboarding | New | `profile_snapshots.age`, `.sex`; frames 01a-01c | Schema yes, form no |
| CR-2 | Compute BMR (Mifflin-St Jeor) and TDEE from onboarded data and show a +/-10% range | New | `profile_snapshots.activity_level`; metrics engine; dashboard | Engine yes |
| CR-3 | Accept an **optional** daily intake estimate or deficit level; with neither, show no expected-loss figure | New | `intake_kcal`, `deficit_level` (both nullable) | Engine and schema yes |
| CR-4 | Compute expected weight-loss rate, capped at 1% of body weight per week, labelled "early-weeks estimate" | New | Metrics engine; dashboard label | Engine yes |
| CR-5 | Collect training level at onboarding and show a muscle-gain range labelled "heuristic" | New | `training_level`; metrics engine | Engine yes |
| CR-6 | Return "not enough data" instead of a number when minimum data is missing | Change | All metrics | Yes |
| CR-7 | Compare measured weight trend with expected loss and flag "faster than expected" | New | Dashboard status; safety guardrail link (P-3) | Engine yes, flag UI no |
| CR-8 | Label any benchmark without a read source as "illustrative" | Constraint | Strength benchmark pending | Pending source |
| CR-9 | Show the gap between logged sleep times and onboarded targets | Proposed | Sleep metric extension | No |

Also open: D-8, add age and sex to the onboarding form and API (`POST /onboarding`); update the ER diagram (Figure 4.3) with the new `profile_snapshots` columns before the final report.
