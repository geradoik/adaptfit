import { useEffect, useState } from "react";
import { getJSON, getUserId, postJSON, todayISO } from "../api.js";
import { target } from "../flows.js";
import { Banner, Chips, Field, NumberField, TimeField } from "../forms.jsx";
import { go } from "../router.js";

const DAY_NAMES = { mon: "Monday", tue: "Tuesday", wed: "Wednesday", thu: "Thursday", fri: "Friday", sat: "Saturday", sun: "Sunday" };
const PROTEIN = [{ value: "yes", label: "Yes" }, { value: "no", label: "No" }];

export default function CheckIn() {
  const userId = getUserId();
  const [profile, setProfile] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [loadError, setLoadError] = useState("");

  const [date, setDate] = useState(todayISO());
  const [weight, setWeight] = useState("");
  const [done, setDone] = useState([]);
  const [sleepSame, setSleepSame] = useState(true);
  const [bed, setBed] = useState("");
  const [wake, setWake] = useState("");
  const [protein, setProtein] = useState("");
  const [liftOpen, setLiftOpen] = useState(false);
  const [lift, setLift] = useState({ exercise_id: "", weight_used: "", reps: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!userId) return;
    getJSON(`/api/users/${userId}/profile`)
      .then((p) => {
        setProfile(p);
        setWeight(String(p.weight ?? "")); // prefill with the last known weight
      })
      .catch((e) => setLoadError(e.message));
    getJSON("/api/exercises").then(setExercises).catch(() => setExercises([]));
  }, [userId]);

  if (!userId) {
    return (
      <main className="body">
        <Banner>Create your profile first, so the check-in knows your training plan.</Banner>
        <button className="btn primary" onClick={() => go("01a")}>Create my profile</button>
      </main>
    );
  }
  if (loadError) return <main className="body"><Banner kind="error">{loadError}</Banner></main>;
  if (!profile) return <main className="body"><p className="caption">Loading your plan...</p></main>;

  const toggleDay = (day) => setDone(done.includes(day) ? done.filter((d) => d !== day) : [...done, day]);

  const save = async () => {
    setSaving(true);
    setError("");
    const lifts =
      liftOpen && lift.exercise_id && lift.weight_used !== "" && lift.reps !== ""
        ? [{ exercise_id: Number(lift.exercise_id), weight_used: Number(lift.weight_used), reps: Number(lift.reps), sets: 3 }]
        : [];
    const payload = {
      checkin_date: date,
      weight: weight === "" ? null : Number(weight),
      done_days: done,
      sleep: sleepSame ? null : { bed_time: bed, wake_time: wake },
      protein_target_met: protein === "" ? null : protein === "yes",
      lifts,
    };
    try {
      await postJSON(`/api/users/${userId}/checkins`, payload);
      go(target("02a", "Save check-in")); // the Home screen
    } catch (e) {
      setError(e.message);
      setSaving(false);
    }
  };

  const groups = [...new Set(exercises.map((e) => e.muscle_group))];

  return (
    <>
      <main className="body">
        <Field label="Week ending">
          <input type="date" value={date} max={todayISO()} onChange={(e) => setDate(e.target.value)} />
        </Field>

        <h2 className="section">This week's plan</h2>
        {profile.training_days.map((day) => (
          <div key={day} className="session-row">
            <span>{DAY_NAMES[day]}</span>
            <button type="button" className={done.includes(day) ? "chip selected" : "chip"}
              aria-pressed={done.includes(day)} onClick={() => toggleDay(day)}>
              {done.includes(day) ? "Done as planned" : "Mark done"}
            </button>
          </div>
        ))}
        <button className="btn text" onClick={() => go(target("02a", "+ Add something else"))}>+ Add something else</button>

        <h2 className="section">Body</h2>
        <NumberField label="Weight" suffix="kg" value={weight} onChange={setWeight} />

        <h2 className="section">Sleep (optional)</h2>
        <Chips options={[{ value: "same", label: "Same as usual" }]} value={sleepSame ? "same" : ""}
          onChange={(v) => setSleepSame(v === "same")} />
        {!sleepSame && (
          <>
            <TimeField label="Bedtime" value={bed} onChange={setBed} />
            <TimeField label="Wake time" value={wake} onChange={setWake} />
          </>
        )}

        <h2 className="section">Food (optional)</h2>
        <p className="caption">Did you eat protein at each meal this week?</p>
        <Chips options={PROTEIN} value={protein} onChange={setProtein} />

        <button className="btn text" onClick={() => setLiftOpen(!liftOpen)}>
          {liftOpen ? "Hide lifts" : "Log your lifts (optional)"}
        </button>
        {liftOpen && (
          <>
            <p className="caption">Top set only</p>
            <Field label="Exercise">
              <select value={lift.exercise_id} onChange={(e) => setLift({ ...lift, exercise_id: e.target.value })}>
                <option value="">Choose...</option>
                {groups.map((g) => (
                  <optgroup key={g} label={g}>
                    {exercises.filter((x) => x.muscle_group === g).map((x) => (
                      <option key={x.exercise_id} value={x.exercise_id}>{x.name}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </Field>
            <NumberField label="Weight" suffix="kg" value={lift.weight_used} onChange={(v) => setLift({ ...lift, weight_used: v })} />
            <NumberField label="Reps" step="1" value={lift.reps} onChange={(v) => setLift({ ...lift, reps: v })} />
          </>
        )}
        {error && <Banner kind="error">Could not save. Your answers are kept, try again. ({error})</Banner>}
      </main>
      <footer className="footer">
        <button className="btn primary" disabled={saving} onClick={save}>{saving ? "Saving..." : "Save check-in"}</button>
      </footer>
    </>
  );
}
