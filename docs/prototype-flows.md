# Prototype flows (Figma, page "Wireframes")

Trigger On tap, action Navigate to, animation Instant. The app skeleton (`frontend/src/flows.js`) implements exactly this table and `npm run check:flows` verifies it.

| From | Element | Opens |
|---|---|---|
| 01a | Button "Continue" | 01b |
| 01b | Button "Continue" | 01c |
| 01b | Button "Back" | 01a |
| 01c | Button "Back" | 01b |
| 01c | Button "Create my profile" | 06 |
| 06 | Button "Save choices" | 03a |
| 03c | Button "Start check-in" | 02a |
| Any screen with BottomNav | Tab "Check-in" | 02a |
| Any screen with BottomNav | Tab "Home" | 03a |
| Any screen with BottomNav | Tab "History" | 05a |
| 02a | Button "+ Add something else" | 02b |
| 02b | Button "Weights" | 02c |
| 02b | Button "Cardio" | 02d |
| 02c, 02d | Button "Add" | 02a |
| 02a | Button "Save check-in" | 03a |
| 03a | Button "Why this suggestion?" | 04a |
| 03a | Button "Compare weeks" | 05b |
| 05a | Chip "Compare" | 05b |
| 05b | Chip "Timeline" | 05a |
| 03a | Gear icon | 07 |
| 07 | Row "Privacy and AI explanations" | 06 |
| 04a, 04b, 07 | Back arrow | Back (previous frame) |

Frame 03b is not in this map; add it here and in `flows.js` if it exists in your Figma file.
