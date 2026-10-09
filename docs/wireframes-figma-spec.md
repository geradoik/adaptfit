# Figma wireframe build spec

Six screens (nine frames) for a phone-size, mobile-first web app. These are low-fidelity grayscale wireframes: structure and wording first, colour and brand later. Follow the sections in order. Each screen lists the requirement it satisfies, so you can annotate frames and reuse them in the report.

## 1. File setup

1. New Figma design file named `AdaptFit wireframes`. Pages: `Components`, `Wireframes`, `Flow`.
2. On `Wireframes`, create frames at **390 × 844** (device frame "iPhone 14"). Name them `01a Onboarding - About you` and so on, using the numbering below.
3. Layout grid on every frame: **4 columns, margin 16, gutter 16**. Add a second grid of type Grid, size **8**, to keep spacing on the 8-pt scale.
4. Spacing scale: 4, 8, 12, 16, 24, 32. Nothing else. Minimum tap target **44 × 44**.
5. Colour styles (grayscale only):

| Style | Hex | Use |
|---|---|---|
| Ink | #151515 | text, selected fills |
| Grey 600 | #555555 | secondary text |
| Grey 300 | #C8C8C8 | borders |
| Grey 100 | #EFEFEF | placeholder fills, sparkline boxes |
| Paper | #FFFFFF | screen background |

6. Text styles (font Inter): Title 24/32 bold, Heading 18/24 bold, Body 16/24 regular, Caption 13/18 regular, Button 16/24 semibold.
7. Build every frame with **Auto Layout** (vertical, padding 16, gap 16 unless stated). Resize rules: children "Fill container" horizontally, "Hug contents" vertically.
8. Layer names follow `Screen / Section / Element` (for example `Check-in / Plan / Session row`).

## 2. Components (build these first, on the `Components` page)

| Component | Spec | Variants |
|---|---|---|
| TopBar | Height 56. Title centred, optional back arrow left, optional action right. | with back / without back |
| Button | Height 48, fill width, radius 8, Button text style. | Primary (Ink fill, white text), Secondary (1 px Ink border), Text (no border); states Default, Pressed, Disabled |
| InputRow | Caption label above, field 48 high with 1 px Grey 300 border, optional unit suffix on the right. | Default, Focus, Error (error caption below) |
| OptionChip | Height 44, hug width, 1 px border, 12 px horizontal padding. | Unselected, Selected (Ink fill, white text) |
| NumberStepper | Minus button 44 × 44, value in the middle, plus button 44 × 44. | Default |
| StepIndicator | Caption text "Step 2 of 3" with three short bars, the current bar in Ink. | step 1, 2, 3 |
| SessionRow | Height 64. Left: session title (Body bold) and detail (Caption). Right: toggle labelled "Done as planned" and a Text button "Edit". | Not done, Done |
| MetricCard | Width fills half the row. Caption label, value in Title style, caption window ("last 4 weeks"), 100 × 24 Grey 100 box as sparkline placeholder. | With value, Not enough data (value replaced by "Not enough data yet") |
| Tag | Height 24, 1 px border, Caption text. | Rules, AI-written, Estimate |
| Banner | Full width, padding 12, 1 px border, Caption text. | Info, Notice |
| BottomSheet | Rounded top corners, drag handle, title, content. Height hugs content, maximum 60% of the screen. | n/a |
| BottomNav | Height 64 plus 34 safe area. Three tabs: Home, Check-in, History; selected tab has an Ink top border and bold label. | Home, Check-in, History selected |

## 3. Screens

### 01 Onboarding (three frames: 01a, 01b, 01c)
*Satisfies FR-3, FR-4, NFR-3. Keep each step short so a beginner is not put off.*

Common structure: TopBar without back on 01a, with back on 01b and 01c. Under it a StepIndicator. Heading "Set your starting point". Body "Takes about two minutes. You can update any answer later." Content area, then a sticky footer (padding 16): Primary button, and a Text button "Back" on steps 2 and 3.

- **01a About you:** InputRow "Weight" with suffix `kg` (NumberStepper), InputRow "Height" with suffix `cm`. Button "Continue".
- **01b Training:** Caption "Which days do you plan to train?" and seven OptionChips Mon to Sun (multi-select). Caption "Main goal" and four full-width option rows, one selectable: Build muscle, Get stronger, Lose fat, Stay consistent. Button "Continue".
- **01c Habits:** Two time inputs "Usual bedtime" and "Usual wake time". Caption "How would you describe your eating?" and three OptionChips (Regular meals, Irregular, Not sure). Button "Create my profile".

Notes: the goal and eating options are placeholders. Replace them with wording that comes out of the questionnaire (ticket T-24). The eating question needs decision D-7. Error state: a Caption under the field reads "Enter a number".

### 02 Weekly check-in (three frames: 02a, 02b, 02c)
*Satisfies FR-5, FR-6, FR-7, NFR-3. The whole screen should take about a minute.*

**02a Main screen.** TopBar "Weekly check-in". Caption under it: "Week of Mon 19 Oct". Then, top to bottom:

1. Heading "This week's plan". Three SessionRows (for example "Mon: Upper body", "Wed: Legs", "Fri: Full body"). Tapping the toggle marks a whole session done in one tap (FR-6). A Text button "+ Add something else" opens frame 02b.
2. Heading "Body". NumberStepper for weight prefilled with last week's value. Caption "Last week: 72.4 kg".
3. Heading "Sleep (optional)". Row with an OptionChip "Same as usual" selected by default; if deselected, two time inputs appear.
4. Heading "Food (optional)". Body "Did you eat protein at each meal this week?" Two OptionChips: Yes, No. (Two values because the database stores true or false.)
5. A collapsed row "Log your lifts (optional)". When expanded it shows up to three rows, each with an exercise picker and weight × reps for the top set only. Caption "Top set only".
6. Sticky footer: Primary "Save check-in".

States to draw: saving (button shows a spinner, disabled), saved (toast "Check-in saved. Your profile has a new version."), error (Banner above the footer, "Could not save. Your answers are kept, try again.").

**02b Add activity, level 1 (bottom sheet).** Title "Add activity". Three full-width rows: Weights, Cardio, Rest day.

**02c Add activity, level 2 (same sheet).** Two versions:
- *Weights:* a row of muscle-group OptionChips (Chest, Back, Legs, Shoulders, Arms, Core) acting as a filter, and below it the exercise list for the selected group. Button "Add".
- *Cardio:* a row of OptionChips for intensity (Light, Moderate, Hard), a row for time (under 15, 15-30, 30-60, 60+ min). Button "Add". Cardio storage needs decision D-1.

The sheet is the second level; there is no third level (NFR-3).

### 03 Home (dashboard)
*Satisfies FR-9, FR-12, FR-13, FR-14, NFR-4.*

TopBar "This week" with a settings icon on the right. If the user has too little data, show an Info Banner: "Metrics appear after your second check-in." Then:

1. A 2 × 2 grid of MetricCards: Adherence, Weight trend, Sleep consistency, Strength (draw this one greyed out; it is the first feature to cut). Each has a with-value and a not-enough-data version.
2. A Suggestion card: Caption "This week's suggestion", Body text (two to three lines), a row of Tags (Rules or AI-written, and Estimate if it contains a projection), and a Secondary button "Why this suggestion?".
3. A Text button "Compare weeks".
4. BottomNav with Home selected.

Empty state (day 0): replace the grid and card with Heading "Log your first check-in" and a Primary button "Start check-in".

### 04 Suggestion detail ("Why this suggestion")
*Satisfies FR-14, NFR-7, NFR-6, P-3, P-4.*

TopBar with back, title "Suggestion". Title style headline for the suggestion, then Body text. Tag row. Then:

1. Heading "Based on". One row per source metric: name, value, and window, for example "Adherence 75%, last 4 weeks".
2. Heading "Evidence". One row per rule: a one-line description, the citation in Caption style, and a small "Rule set v1" Tag.
3. Banner (Notice): "General fitness guidance, not medical advice."
4. Heading "How this was written". When AI explanations are on: "Written with an AI service. Only summary numbers were sent, never your name or email." When off: "Rule-based suggestion. Turn on AI explanations in Settings to get a written version."

Draw a variant for when the AI service is unavailable: Banner "Showing the rule-based suggestion because the AI service could not be reached."

### 05 History and compare (two frames: 05a, 05b)
*Satisfies FR-7, FR-8. The compare view is the one to use in your demo.*

- **05a Timeline:** TopBar "History", a two-option segmented control (Timeline, Compare). A list of rows, newest first: date, a Tag ("Baseline" or "Check-in"), weight, and a change chip against the previous row ("+0.4 kg"). Empty state: "History appears after your first check-in." BottomNav with History selected.
- **05b Compare:** two date pickers "From" and "To". Below, a three-column table: Metric, From, To, with rows Weight, Adherence, Sleep consistency and Suggestion. A Caption "Change" column on the right.

### 06 Consent and notice
*Satisfies NFR-6, P-3, P-5. Shown once after onboarding and again from Settings (the settings icon on Home opens a plain list that links here).*

TopBar "Before we start". Then, in order:

1. Banner (Notice): "AdaptFit gives general fitness guidance. It is not medical advice."
2. Heading "AI explanations". A switch, **off by default**. Body: "If on, summary numbers such as your adherence and weight trend are sent to an external AI service to write your suggestion. Your name and email are never sent." Caption: "If off, you still get rule-based suggestions."
3. Heading "Your data". Two Text buttons: "Export my data" and "Delete my account".
4. Sticky footer: Primary "Save choices".

The text must match what the system really does, so re-check it when ticket T-25 is built.

## 4. Prototype flows (on the `Flow` page)

Connect with the Prototype tab, trigger On tap, animation Instant or Move in:

- 01a → 01b → 01c → 06 → 03
- 03 "Start check-in" and BottomNav "Check-in" → 02a. Saving → 03 with the toast.
- 02a "+ Add something else" → 02b → 02c → back to 02a
- 03 "Why this suggestion?" → 04
- 03 "Compare weeks" and BottomNav "History" → 05a. The segmented control switches to 05b.

## 5. Finish

1. Add a yellow sticky note on each frame with its requirement IDs.
2. Draw the empty, loading and error states listed above.
3. Export all frames as PNG at 2x for the report (File → Export).
4. Share the file with view access to your supervisor.
