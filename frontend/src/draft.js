// The onboarding answers live here while the user moves between frames 01a, 01b and 01c.
// Each frame is a separate route, so React state alone would be lost on every step.
export const draft = {
  weight: "",
  height: "",
  age: "",
  sex: "",
  training_days: [],
  goal: "",
  training_level: "",
  activity_level: "",
  diet_pattern: "",
  bed_time: "",
  wake_time: "",
  deficit_level: "",
  intake_kcal: "",
};

export function resetDraft() {
  Object.keys(draft).forEach((key) => {
    draft[key] = Array.isArray(draft[key]) ? [] : "";
  });
}
