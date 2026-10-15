// Frame map for the Figma wireframes. One entry per frame; `actions` mirror the prototype connections
// `back: true` means the top-bar back arrow goes to the previous frame (browser history).
// `nav: true` shows the BottomNav (Home, Check-in, History).

export const START_FRAME = "01a";

export const BOTTOM_NAV = [
  { label: "Home", to: "03a" },
  { label: "Check-in", to: "02a" },
  { label: "History", to: "05a" },
];

export const FRAMES = {
  "01a": {
    title: "Set your starting point", step: "Step 1 of 3", group: "Onboarding", screen: "onboarding",
    lines: ["About you: weight (kg), height (cm), age, sex.", "Takes about two minutes. You can update any answer later."],
    actions: [{ label: "Continue", to: "01b", variant: "primary" }],
  },
  "01b": {
    title: "Training", step: "Step 2 of 3", group: "Onboarding", screen: "onboarding",
    lines: ["Which days do you plan to train? Main goal. Training experience.", "Chips: Mon to Sun; Build muscle, Get stronger, Lose fat, Stay consistent."],
    actions: [{ label: "Continue", to: "01c", variant: "primary" }, { label: "Back", to: "01a", variant: "text" }],
  },
  "01c": {
    title: "Habits", step: "Step 3 of 3", group: "Onboarding", screen: "onboarding",
    lines: ["Usual bedtime and wake time. Eating pattern. Activity level.", "Optional: calorie target or deficit level (small, moderate, large)."],
    actions: [{ label: "Create my profile", to: "06", variant: "primary" }, { label: "Back", to: "01b", variant: "text" }],
  },
  "06": {
    title: "Before we start", group: "Consent",
    lines: ["General fitness guidance, not medical advice.", "AI explanations: off by default. Only summary numbers are ever sent.", "Your data: export or delete."],
    actions: [{ label: "Save choices", to: "03a", variant: "primary" }],
  },
  "03a": {
    title: "This week", group: "Home", nav: "Home", gear: "07", live: "home",
    lines: [],
    actions: [{ label: "Why this suggestion?", to: "04a", variant: "secondary" }, { label: "Compare weeks", to: "05b", variant: "text" }],
  },
  "03c": {
    title: "This week", group: "Home", nav: "Home", gear: "07",
    lines: ["Log your first check-in", "Metrics appear after your second check-in."],
    actions: [{ label: "Start check-in", to: "02a", variant: "primary" }],
  },
  "02a": {
    title: "Weekly check-in", group: "Check-in", nav: "Check-in", screen: "checkin",
    lines: ["This week's plan: tap a session to mark it done.", "Body: weight. Sleep (optional): same as usual. Food (optional). Lifts (optional): top set only."],
    actions: [{ label: "+ Add something else", to: "02b", variant: "text" }, { label: "Save check-in", to: "03a", variant: "primary" }],
  },
  "02b": {
    title: "Add activity", group: "Check-in", sheet: true,
    lines: ["What did you do?"],
    actions: [{ label: "Weights", to: "02c", variant: "secondary" }, { label: "Cardio", to: "02d", variant: "secondary" }],
  },
  "02c": {
    title: "Add weights", group: "Check-in", sheet: true,
    lines: ["Pick a muscle group, then an exercise."],
    actions: [{ label: "Add", to: "02a", variant: "primary" }],
  },
  "02d": {
    title: "Add cardio", group: "Check-in", sheet: true,
    lines: ["Intensity: light, moderate, hard. Time: under 15, 15-30, 30-60, 60+ min."],
    actions: [{ label: "Add", to: "02a", variant: "primary" }],
  },
  "04a": {
    title: "Suggestion", group: "Suggestion", back: true, screen: "why",
    lines: ["Based on: the metrics behind this suggestion.", "Evidence: the rule and citation (rule set v1).", "General fitness guidance, not medical advice."],
    actions: [],
  },
  "04b": {
    title: "Suggestion (AI unavailable)", group: "Suggestion", back: true,
    lines: ["Showing the rule-based suggestion because the AI service could not be reached."],
    actions: [],
  },
  "05a": {
    title: "History", group: "History", nav: "History", seg: "Timeline",
    lines: ["Newest first: date, Baseline or Check-in, weight, change."],
    actions: [{ label: "Compare", to: "05b", variant: "chip" }],
  },
  "05b": {
    title: "History", group: "History", nav: "History", seg: "Compare",
    lines: ["From and To dates. Weight, adherence, sleep consistency, suggestion."],
    actions: [{ label: "Timeline", to: "05a", variant: "chip" }],
  },
  "07": {
    title: "Settings", group: "Settings", back: true,
    lines: [],
    actions: [{ label: "Privacy and AI explanations", to: "06", variant: "row" }],
  },
};

// Where a button leads, read from the map above so the screens never repeat a frame id by hand.
export function target(frameId, label) {
  const action = FRAMES[frameId].actions.find((a) => a.label === label);
  if (!action) throw new Error(`Frame ${frameId} has no button "${label}"`);
  return action.to;
}
