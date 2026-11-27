import { useEffect, useState } from "react";
import { getJSON, resolveUserId } from "../api.js";
import { go } from "../router.js";

// Frames 05a (Timeline) and 05b (Compare).
// One screen file for both, because they share the same data and the same Timeline / Compare switch.
// frameId tells us which one to draw: "05a" is the timeline, "05b" is the comparison.

// 72.3 becomes "72.3 kg". A missing number becomes a dash.
function kg(value) {
  return value == null ? "-" : Number(value).toFixed(1) + " kg";
}

// -0.4 becomes "-0.4", 2 becomes "+2". Zero and missing values get no sign.
function signed(value, decimals) {
  if (value == null) {
    return "-";
  }
  const text = Number(value).toFixed(decimals);
  return value > 0 ? "+" + text : text;
}

// A metric that might be missing: "83%" or "Not enough data yet".
function metricText(value, unit) {
  return value == null ? "Not enough data yet" : Number(value).toFixed(0) + unit;
}

// The switch at the top: Timeline | Compare.
function Switch({ frameId }) {
  return (
    <div className="chips" role="group" aria-label="History view">
      <button className={frameId === "05a" ? "chip selected" : "chip"} onClick={() => go("05a")}>
        Timeline
      </button>
      <button className={frameId === "05b" ? "chip selected" : "chip"} onClick={() => go("05b")}>
        Compare
      </button>
    </div>
  );
}

// Frame 05a: one row per saved profile snapshot, newest first.
export function TimelineView({ entries }) {
  return (
    <div>
      {entries.map((entry) => (
        <div className="row" key={entry.snapshot_id}>
          <strong>{entry.date}</strong>
          <span>{entry.kind}</span>
          <span>{kg(entry.weight)}</span>
          <span className="caption">{entry.change == null ? "start" : signed(entry.change, 1) + " kg"}</span>
        </div>
      ))}
    </div>
  );
}

// Frame 05b: the table with From, To and Change columns, then the two suggestions.
export function CompareView({ result }) {
  const from = result.from;
  const to = result.to;
  const change = result.change;
  return (
    <>
      <div className="compare-head">
        <span></span>
        <span>{from.date}</span>
        <span>{to.date}</span>
        <span>Change</span>
      </div>
      <div className="compare-row">
        <span>Weight</span>
        <span>{kg(from.weight)}</span>
        <span>{kg(to.weight)}</span>
        <strong>{signed(change.weight, 1)} kg</strong>
      </div>
      <div className="compare-row">
        <span>Adherence</span>
        <span>{metricText(from.adherence_pct, "%")}</span>
        <span>{metricText(to.adherence_pct, "%")}</span>
        <strong>{change.adherence_pct == null ? "-" : signed(change.adherence_pct, 0) + " pts"}</strong>
      </div>
      <div className="compare-row">
        <span>Sleep consistency</span>
        <span>{metricText(from.sleep_consistency_min, " min")}</span>
        <span>{metricText(to.sleep_consistency_min, " min")}</span>
        <strong>{change.sleep_consistency_min == null ? "-" : signed(change.sleep_consistency_min, 0) + " min"}</strong>
      </div>
      <p className="caption">Adherence uses the 4 weeks up to each date. Sleep consistency uses the last 4 check-ins up to each date. A lower sleep number means steadier sleep.</p>

      <h2 className="section">Suggestion on {from.date}</h2>
      <p className="line">{from.suggestion || "No suggestion was saved for this date."}</p>
      <h2 className="section">Suggestion on {to.date}</h2>
      <p className="line">{to.suggestion || "No suggestion was saved for this date."}</p>
    </>
  );
}

export default function History({ frameId }) {
  const [entries, setEntries] = useState(null);   // the timeline, or null while loading
  const [userId, setUserId] = useState(null);
  const [fromDay, setFromDay] = useState("");
  const [toDay, setToDay] = useState("");
  const [result, setResult] = useState(null);     // the comparison, or null
  const [error, setError] = useState("");

  // Load the timeline once. It also gives us the check-in dates for the two drop-downs.
  useEffect(() => {
    async function load() {
      try {
        const id = await resolveUserId();
        const data = await getJSON("/api/users/" + id + "/history");
        const dates = data.entries.filter((e) => e.kind === "Check-in").map((e) => e.date);
        setUserId(id);
        setEntries(data.entries);
        // Start with the two newest check-ins (dates are newest first).
        if (dates.length >= 2) {
          setToDay(dates[0]);
          setFromDay(dates[1]);
        }
      } catch (e) {
        setError(e.message);
      }
    }
    load();
  }, []);

  // Ask for the comparison whenever the chosen dates change.
  useEffect(() => {
    if (frameId !== "05b" || !userId || !fromDay || !toDay) {
      return;
    }
    async function loadCompare() {
      try {
        const url = "/api/users/" + userId + "/compare?from_date=" + fromDay + "&to_date=" + toDay;
        setResult(await getJSON(url));
        setError("");
      } catch (e) {
        setResult(null);
        setError(e.message);
      }
    }
    loadCompare();
  }, [frameId, userId, fromDay, toDay]);

  if (error && entries == null) {
    return <p className="banner error">Could not load history ({error}).</p>;
  }
  if (entries == null) {
    return <p className="caption pad">Loading history...</p>;
  }

  // Check-in dates, oldest first, for the drop-downs.
  const dates = entries.filter((e) => e.kind === "Check-in").map((e) => e.date).reverse();

  return (
    <main className="body">
      <Switch frameId={frameId} />

      {frameId === "05a" && (
        entries.length === 0
          ? <p className="line">Nothing here yet. Your history starts with your first check-in.</p>
          : <TimelineView entries={entries} />
      )}

      {frameId === "05b" && (
        dates.length < 2 ? (
          <>
            <p className="line">Log at least two check-ins to compare weeks.</p>
            <button className="btn primary" onClick={() => go("02a")}>Start check-in</button>
          </>
        ) : (
          <>
            <div className="field-row">
              <label className="field">
                <span className="caption">From</span>
                <select value={fromDay} onChange={(e) => setFromDay(e.target.value)}>
                  {dates.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </label>
              <label className="field">
                <span className="caption">To</span>
                <select value={toDay} onChange={(e) => setToDay(e.target.value)}>
                  {dates.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </label>
            </div>
            {error && <p className="banner error">{error}</p>}
            {result && <CompareView result={result} />}
          </>
        )
      )}
    </main>
  );
}
