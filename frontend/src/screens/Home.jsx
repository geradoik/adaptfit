import { useEffect, useState } from "react";
import { clearUserId, getJSON, getUserId, resolveUserId } from "../api.js";
import { MetricCard } from "../components.jsx";
import { Banner } from "../forms.jsx";
import { go } from "../router.js";

// Frame 03a: live metrics and this week's suggestion. Shows the user's own data after onboarding,
// otherwise the simulated demo persona "Sam".
const round = (n, d) => Number(n).toFixed(d);

function pick(metrics, type) {
  return metrics.find((m) => m.metric_type === type || m.metric_type.startsWith(`${type}:`));
}

function show(metric, format) {
  return metric && metric.status === "ok" ? format(metric) : null;
}

const STATUS_TEXT = {
  on_track: "On track",
  slower_than_expected: "Slower than expected",
  faster_than_expected: "Faster than expected (check this is safe)",
};

export default function Home() {
  const [state, setState] = useState({ phase: "loading" });
  const isDemo = getUserId() === null;

  useEffect(() => {
    let cancelled = false;
    resolveUserId()
      .then(async (id) => {
        const metrics = await getJSON(`/api/users/${id}/metrics`);
        // A 404 just means "no suggestion yet", which is a normal state, not an error.
        const suggestion = await getJSON(`/api/users/${id}/suggestion`).catch((e) =>
          e.status === 404 ? null : Promise.reject(e));
        if (!cancelled) setState({ phase: "ok", metrics, suggestion });
      })
      .catch((e) => !cancelled && setState({ phase: "error", message: e.message }));
    return () => { cancelled = true; };
  }, []);

  if (state.phase === "loading") return <p className="caption pad">Loading metrics...</p>;
  if (state.phase === "error")
    return (
      <Banner kind="error">
        Could not reach the server ({state.message}). Start the backend: <code>uvicorn app.main:app --reload</code>
      </Banner>
    );

  const { metrics: report, suggestion } = state;
  const metrics = report.metrics;
  const adherence = pick(metrics, "adherence_pct");
  const weight = pick(metrics, "weight_trend_kg_per_week");
  const sleep = pick(metrics, "sleep_consistency_min");
  const strength = pick(metrics, "strength_progression_pct_per_week");
  const tdee = pick(metrics, "tdee_kcal");
  const loss = pick(metrics, "expected_loss_kg_per_week");
  const muscle = pick(metrics, "muscle_gain_kg_per_week");
  const compare = pick(metrics, "loss_vs_expected_ratio");

  return (
    <>
      <Banner>
        {isDemo
          ? `Simulated persona "Sam", as of ${report.as_of}. Numbers are computed by rules, not by the AI.`
          : "Your numbers, computed by rules. Metrics appear after your second check-in."}
      </Banner>

      <div className="suggestion">
        <p className="caption">This week's suggestion</p>
        {suggestion ? (
          <>
            <p>{suggestion.text}</p>
            <div className="tags">{suggestion.tags.map((t) => <span key={t} className="tag">{t}</span>)}</div>
          </>
        ) : (
          <p>Save a weekly check-in and your first suggestion appears here.</p>
        )}
      </div>

      <div className="grid">
        <MetricCard label="Adherence" window="last 4 weeks" value={show(adherence, (m) => `${round(m.value, 0)}%`)} />
        <MetricCard label="Weight trend" window="last 2 weeks" value={show(weight, (m) => `${round(m.value, 2)} kg/wk`)} />
        <MetricCard label="Sleep consistency" window="last 4 check-ins" value={show(sleep, (m) => `${round(m.value, 0)} min`)} />
        <MetricCard label="Strength" window="top-set trend" value={show(strength, (m) => `${round(m.value, 1)}%/wk`)} />
      </div>
      <h2 className="section">Energy and targets</h2>
      <div className="grid">
        <MetricCard label="Daily energy (TDEE)" window="range +/-10%" estimate
          value={show(tdee, (m) => `${round(m.value, 0)} kcal`)} />
        <MetricCard label="Expected loss" window="early-weeks estimate" estimate
          value={show(loss, (m) => `${round(m.value, 2)} kg/wk`)} />
        <MetricCard label="Realistic muscle gain" window="heuristic range" estimate
          value={show(muscle, (m) => `${round(m.detail.low, 2)}-${round(m.detail.high, 2)} kg/wk`)} />
        <MetricCard label="Loss vs expected" window="measured / expected"
          value={show(compare, (m) => STATUS_TEXT[m.detail.status])} />
      </div>

      {isDemo ? (
        <button className="btn text" onClick={() => go("01a")}>Create my own profile</button>
      ) : (
        <button className="btn text" onClick={() => { clearUserId(); window.location.reload(); }}>
          Switch to the demo persona
        </button>
      )}
    </>
  );
}
