# Requirements traceability

Every requirement in the proposal (FR-1 to FR-14 as numbered there, NFR-1 to NFR-8) maps to at least one ticket. IDs starting with P- are proposed additions that the build needs but the Chapter 3 list does not contain yet. Add them to the document so the report and the code agree.

## Proposed additions

| ID | Requirement |
|---|---|
| P-1 | Simulation module: generate synthetic personas and run them across timepoints (needed by Objective 4). |
| P-2 | Sleep consistency and strength progression metrics (named in the Design Phase but missing from the FR list). |
| P-3 | Safety guardrails and a visible not-medical-advice notice. |
| P-4 | Rule-based fallback when the LLM service is unavailable. |
| P-5 | Export and delete a user's data. |

## Requirement to tickets

| Requirement | Tickets |
|---|---|
| FR-1 | T-05, T-10 |
| FR-2 | T-05, T-10 |
| FR-3 | T-03, T-05, T-11 |
| FR-4 | T-11 |
| FR-5 | T-03, T-05, T-14 |
| FR-6 | T-03, T-15 |
| FR-7 | T-04, T-12 |
| FR-8 | T-03, T-04, T-05, T-12, T-31 |
| FR-9 | T-06, T-16, T-33 |
| FR-12 | T-06, T-17, T-33 |
| FR-13 | T-03, T-05, T-21, T-22, T-25 |
| FR-14 | T-03, T-05, T-23 |
| NFR-1 | T-25, T-28 |
| NFR-3 | T-03, T-14, T-38 |
| NFR-4 | T-06, T-16, T-17, T-19, T-35 |
| NFR-5 | T-05, T-10, T-32 |
| NFR-6 | T-03, T-05, T-26, T-35 |
| NFR-7 | T-03, T-04, T-21, T-23, T-35 |
| NFR-8 | T-06, T-16, T-17, T-19, T-20, T-35 |
| P-1 | T-29, T-30, T-31, T-34, T-36, T-37 |
| P-2 | T-06, T-19, T-20 |
| P-3 | T-27, T-35 |
| P-4 | T-28, T-35 |
| P-5 | T-32 |

## Tickets by week

| Ticket | Week | Title | Requirements |
|---|---|---|---|
| T-01 | 1 | Create GitHub repo, push the starter project, enable CI | - |
| T-02 | 1 | Import tickets and set up the project board | - |
| T-03 | 1 | Build the 6 wireframes in Figma | FR-3, FR-5, FR-6, FR-8, FR-13, FR-14, NFR-3, NFR-6, NFR-7 |
| T-04 | 1 | Check the database schema against the ER diagram | FR-7, FR-8, NFR-7 |
| T-05 | 1 | Review the API endpoint list | FR-1, FR-2, FR-3, FR-5, FR-8, FR-13, FR-14, NFR-5, NFR-6 |
| T-06 | 1 | Write the metric formulas with worked examples | FR-9, FR-12, NFR-4, NFR-8, P-2 |
| T-07 | 1 | Message the supervisor about ethics, the checkpoint and the submission date | - |
| T-08 | 1 | Finalise the questionnaire | - |
| T-09 | 1 | Run the hello-world check end to end | - |
| T-10 | 2 | Registration and login | FR-1, FR-2, NFR-5 |
| T-11 | 2 | Onboarding form and baseline profile | FR-3, FR-4 |
| T-12 | 2 | Versioned snapshots: create and retrieve by date | FR-7, FR-8 |
| T-13 | 2 | Send the questionnaire | - |
| T-14 | 3 | Weekly check-in form | FR-5, NFR-3 |
| T-15 | 3 | One-tap 'done as planned' logging | FR-6 |
| T-16 | 3 | Adherence percentage with unit tests | FR-9, NFR-4, NFR-8 |
| T-17 | 3 | Weight trend with unit tests | FR-12, NFR-4, NFR-8 |
| T-18 | 3 | Collect questionnaire responses | - |
| T-19 | 4 | Sleep consistency and minimum-data rules | P-2, NFR-4, NFR-8 |
| T-20 | 4 | Strength progression estimate (cut first if behind) | P-2, NFR-8 |
| T-21 | 4 | Evidence rule set, versioned and separate from code | FR-13, NFR-7 |
| T-22 | 4 | Rule-based suggestions | FR-13 |
| T-23 | 4 | 'Why this suggestion' display | FR-14, NFR-7 |
| T-24 | 4 | Analyse the questionnaire and refine priorities | - |
| T-25 | 5 | Server-side LLM call and prompt builder | FR-13, NFR-1 |
| T-26 | 5 | Consent gate before any external LLM call | NFR-6 |
| T-27 | 5 | Guardrails and the not-medical-advice notice | P-3 |
| T-28 | 5 | Fallback when the LLM is unavailable | P-4, NFR-1 |
| T-29 | 6 | Persona generator | P-1 |
| T-30 | 6 | Run personas through weeks 1, 6 and 12 | P-1 |
| T-31 | 6 | Profile comparison view: week 1 against week 12 | FR-8, P-1 |
| T-32 | 6 | Data export and delete | P-5, NFR-5 |
| T-33 | 6 | Profile dashboard visuals (stretch) | FR-9, FR-12 |
| T-34 | 6 | Third persona (stretch) | P-1 |
| T-35 | 7 | Integration and guardrail tests | NFR-4, NFR-6, NFR-7, NFR-8, P-3, P-4 |
| T-36 | 7 | Evaluation script and results tables | P-1 |
| T-37 | 7 | Raw logs versus computed metrics comparison (only if supervisor approves) | P-1 |
| T-38 | 7 | Usability walkthrough with 3-5 students (optional) | NFR-3 |
| T-39 | 7 | Feature freeze | - |
| T-40 | 8 | Add implementation, results and limitations to the document; update the Gantt chart | - |
| T-41 | 8 | Demo script with an offline fallback | - |
| T-42 | 8 | Update slides and rehearse | - |

Numbering gaps in the proposal: FR-10, FR-11 and NFR-2 do not exist. Keep the numbers as submitted, or renumber the document once and update this file.
