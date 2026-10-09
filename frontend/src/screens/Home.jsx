import { useEffect, useState } from "react";
import { MetricCard } from "../components.jsx";

// Live metrics from the trend engine for the simulated demo persona (GET /api/demo/metrics).
const round = (n, d) => Number(n).toFixed(d);

function pick(metrics, type) {
  return metrics.find((m) => m.metric_type === type || m.metric_type.startsWith(`${type}:`));
}

function show(metric, format) {
  return metric && metric.status === "ok" ? format(metric) : null;
}

export default function Home() {
  const [state, setState] = useState({ phase: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/demo/metrics", { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`Server replied ${r.status}`);
        return r.json();
      })
      .then((data) => setState({ phase: "ok", data }))
      .catch((e) => {
        if (e.name !== "AbortError") setState({ phase: "error", message: e.message });
      });
    return () => controller.abort();
  }, []);

  if (state.phase === "loading") return <p className="caption pad">Loading metrics...</p>;
  if (state.phase === "error")
    return (
      <p className="banner pad">
        Could not reach the server ({state.message}). Start the backend: <code>uvicorn app.main:app --reload</code>
      </p>
    );

  const { metrics, as_of: asOf } = state.data;
  const adherence = pick(metrics, "adherence_pct");
  const weight = pick(metrics, "weight_trend_kg_per_week");
  const sleep = pick(metrics, "sleep_consistency_min");
  const strength = pick(metrics, "strength_progression_pct_per_week");
  const tdee = pick(metrics, "tdee_kcal");
  const loss = pick(metrics, "expected_loss_kg_per_week");
  const muscle = pick(metrics, "muscle_gain_kg_per_week");
  const compare = pick(metrics, "loss_vs_expected_ratio");

  const statusText = {
    on_track: "On track",
    slower_than_expected: "Slower than expected",
    faster_than_expected: "Faster than expected (check this is safe)",
  };

  return (
    <>
      <p className="banner">Simulated persona "Sam", as of {asOf}. Numbers are computed by rules, not by the AI.</p>
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
          value={show(compare, (m) => statusText[m.detail.status])} />
      </div>
    </>
  );
}
