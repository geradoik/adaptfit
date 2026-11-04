import { useEffect, useState } from "react";
import { getJSON, resolveUserId } from "../api.js";
import { Banner } from "../forms.jsx";

// Frame 04a: the suggestion, the numbers it is based on, and the rule (with citation) behind it.
export default function Why() {
  const [state, setState] = useState({ phase: "loading" });

  useEffect(() => {
    resolveUserId()
      .then((id) => getJSON(`/api/users/${id}/suggestion`))
      .then((data) => setState({ phase: "ok", data }))
      .catch((e) => setState(e.status === 404 ? { phase: "none" } : { phase: "error", message: e.message }));
  }, []);

  if (state.phase === "loading") return <main className="body"><p className="caption">Loading...</p></main>;
  if (state.phase === "error") return <main className="body"><Banner kind="error">{state.message}</Banner></main>;
  if (state.phase === "none")
    return <main className="body"><Banner>No suggestion yet. Save a weekly check-in and one appears here.</Banner></main>;

  const s = state.data;
  return (
    <main className="body">
      <h2 className="headline">{s.text}</h2>
      <div className="tags">{s.tags.map((t) => <span key={t} className="tag">{t}</span>)}</div>

      <h2 className="section">Based on</h2>
      {s.based_on.length === 0 && <p className="caption">No metrics yet: there is not enough data.</p>}
      {s.based_on.map((b) => (
        <div key={b.metric_type} className="row">
          <strong>{b.label}</strong>
          <span>{b.value_text}</span>
          <span className="caption">{b.window}</span>
        </div>
      ))}

      <h2 className="section">Evidence</h2>
      {s.evidence.map((e) => (
        <div key={e.description} className="row column">
          <span>{e.description}</span>
          <span className="caption">{e.citation}</span>
          <span className="tag">Rule set {e.version}</span>
        </div>
      ))}

      <Banner>{s.disclaimer}</Banner>
      <h2 className="section">How this was written</h2>
      <p className="line">{s.how_written}</p>
    </main>
  );
}
