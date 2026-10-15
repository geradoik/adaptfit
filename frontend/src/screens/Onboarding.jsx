import { useState } from "react";
import { draft, resetDraft } from "../draft.js";
import { postJSON, setUserId } from "../api.js";
import { target } from "../flows.js";
import { Banner, Chips, NumberField, OptionRows, TimeField } from "../forms.jsx";
import { go } from "../router.js";

const SEXES = [{ value: "male", label: "Male" }, { value: "female", label: "Female" }];
const DAYS = [
  { value: "mon", label: "Mon" }, { value: "tue", label: "Tue" }, { value: "wed", label: "Wed" },
  { value: "thu", label: "Thu" }, { value: "fri", label: "Fri" }, { value: "sat", label: "Sat" },
  { value: "sun", label: "Sun" },
];
const GOALS = [
  { value: "build_muscle", label: "Build muscle" }, { value: "get_stronger", label: "Get stronger" },
  { value: "lose_fat", label: "Lose fat" }, { value: "stay_consistent", label: "Stay consistent" },
];
const TRAINING = [
  { value: "novice", label: "Under 1 year" }, { value: "intermediate", label: "1 to 3 years" },
  { value: "advanced", label: "Over 3 years" },
];
const ACTIVITY = [
  { value: "sedentary", label: "Sedentary" }, { value: "light", label: "Light" }, { value: "moderate", label: "Moderate" },
  { value: "very_active", label: "Very active" }, { value: "extra_active", label: "Extra active" },
];
const DIET = [
  { value: "regular_meals", label: "Regular meals" }, { value: "irregular", label: "Irregular" },
  { value: "not_sure", label: "Not sure" },
];
const DEFICITS = [
  { value: "small", label: "Small" }, { value: "moderate", label: "Moderate" }, { value: "large", label: "Large" },
];

// What must be filled in before the user may leave each step.
const REQUIRED = {
  "01a": [["weight", "weight"], ["height", "height"], ["age", "age"], ["sex", "sex"]],
  "01b": [["training_days", "training days"], ["goal", "main goal"], ["training_level", "training experience"],
          ["activity_level", "activity level"]],
  "01c": [],
};

function missingFields(frameId, values) {
  return REQUIRED[frameId]
    .filter(([key]) => (Array.isArray(values[key]) ? values[key].length === 0 : values[key] === ""))
    .map(([, label]) => label);
}

// Turn the text boxes into what the API expects: numbers as numbers, empty answers left out.
function buildPayload(values) {
  const payload = {};
  for (const [key, value] of Object.entries(values)) {
    if (Array.isArray(value)) payload[key] = value;
    else if (value !== "") payload[key] = ["weight", "height", "age", "intake_kcal"].includes(key) ? Number(value) : value;
  }
  return payload;
}

export default function Onboarding({ frameId }) {
  const [values, setValues] = useState({ ...draft });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const set = (key, value) => {
    draft[key] = value; // keep the answers when the user moves to another frame
    setValues({ ...values, [key]: value });
    setError("");
  };

  const goNext = (label) => {
    const missing = missingFields(frameId, values);
    if (missing.length) {
      setError(`Please fill in: ${missing.join(", ")}.`);
      return;
    }
    go(target(frameId, label));
  };

  const finish = async () => {
    setSaving(true);
    setError("");
    try {
      const result = await postJSON("/api/onboarding", buildPayload(values));
      setUserId(result.user_id);
      resetDraft();
      go(target("01c", "Create my profile"));
    } catch (e) {
      setError(e.message);
      setSaving(false);
    }
  };

  return (
    <>
      <main className="body">
        <p className="caption">Step {frameId === "01a" ? 1 : frameId === "01b" ? 2 : 3} of 3. Takes about two minutes.</p>
        {frameId === "01a" && (
          <>
            <NumberField label="Weight" suffix="kg" value={values.weight} onChange={(v) => set("weight", v)} />
            <NumberField label="Height" suffix="cm" value={values.height} onChange={(v) => set("height", v)} />
            <NumberField label="Age" suffix="years" value={values.age} step="1" onChange={(v) => set("age", v)} />
            <p className="caption">Sex (used only for the energy estimate)</p>
            <Chips options={SEXES} value={values.sex} onChange={(v) => set("sex", v)} />
          </>
        )}
        {frameId === "01b" && (
          <>
            <p className="caption">Which days do you plan to train?</p>
            <Chips multiple options={DAYS} value={values.training_days} onChange={(v) => set("training_days", v)} />
            <p className="caption">Main goal</p>
            <OptionRows options={GOALS} value={values.goal} onChange={(v) => set("goal", v)} />
            <p className="caption">How long have you trained regularly?</p>
            <Chips options={TRAINING} value={values.training_level} onChange={(v) => set("training_level", v)} />
            <p className="caption">Outside training, how active are you?</p>
            <Chips options={ACTIVITY} value={values.activity_level} onChange={(v) => set("activity_level", v)} />
          </>
        )}
        {frameId === "01c" && (
          <>
            <TimeField label="Usual bedtime (optional)" value={values.bed_time} onChange={(v) => set("bed_time", v)} />
            <TimeField label="Usual wake time (optional)" value={values.wake_time} onChange={(v) => set("wake_time", v)} />
            <p className="caption">How would you describe your eating?</p>
            <Chips options={DIET} value={values.diet_pattern} onChange={(v) => set("diet_pattern", v)} />
            <p className="caption">Weight-loss target (optional). Skip this if you are not trying to lose weight.</p>
            <Chips options={DEFICITS} value={values.deficit_level} onChange={(v) => set("deficit_level", v)} />
            <NumberField label="Or your daily calories (optional)" suffix="kcal" step="50" value={values.intake_kcal}
              onChange={(v) => set("intake_kcal", v)} />
          </>
        )}
        {error && <Banner kind="error">{error}</Banner>}
      </main>
      <footer className="footer">
        {frameId !== "01c" && (
          <button className="btn primary" onClick={() => goNext("Continue")}>Continue</button>
        )}
        {frameId === "01c" && (
          <button className="btn primary" disabled={saving} onClick={finish}>
            {saving ? "Saving..." : "Create my profile"}
          </button>
        )}
        {frameId !== "01a" && (
          <button className="btn text" onClick={() => go(target(frameId, "Back"))}>Back</button>
        )}
      </footer>
    </>
  );
}
