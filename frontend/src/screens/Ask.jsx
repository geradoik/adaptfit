import { useState } from "react";
import { getConsent, postJSON, resolveUserId } from "../api.js";
import { Banner } from "../forms.jsx";
import { go } from "../router.js";
 
// Frame 08: ask a free question. The answer comes from the AI only if the user allowed it, otherwise from rules.
const IDEAS = ["How much weight will I lose at this rate?", "What chest workouts can I do instead?"];
 
export default function Ask() {
  const [question, setQuestion] = useState("");
  const [state, setState] = useState({ phase: "idle" });
  const consent = getConsent();
 
  const submit = async () => {
    setState({ phase: "loading" });
    try {
      const id = await resolveUserId();
      const result = await postJSON(`/api/users/${id}/ask`, { question, consent_llm: getConsent() });
      setState({ phase: "ok", result });
    } catch (e) {
      setState({ phase: "error", message: e.message });
    }
  };
 
  const r = state.result;
  return (
    <main className="body">
      <p className="caption">Ask about your own progress. {consent ? "AI answers are on." : "AI answers are off."}{" "}
        <button className="link" onClick={() => go("06")}>Change</button></p>
      <label className="field">
        <span className="caption">Your question</span>
        <textarea rows={3} maxLength={500} value={question} onChange={(e) => setQuestion(e.target.value)} />
      </label>
      <div className="chips">
        {IDEAS.map((idea) => (
          <button key={idea} type="button" className="chip" onClick={() => setQuestion(idea)}>{idea}</button>
        ))}
      </div>
      <button className="btn primary" disabled={state.phase === "loading" || question.trim().length < 3} onClick={submit}>
        {state.phase === "loading" ? "Thinking..." : "Ask"}
      </button>
 
      {state.phase === "error" && <Banner kind="error">{state.message}</Banner>}
      {r && (
        <>
          {r.fallback_message && <Banner>{r.fallback_message}</Banner>}
          <div className="suggestion">
            <p className="answer">{r.answer}</p>
            <div className="tags">
              <span className="tag">{r.generated_by === "llm" ? "AI" : "Rules"}</span>
              {r.estimate && <span className="tag">Estimate</span>}
            </div>
          </div>
          {r.based_on.length > 0 && <h2 className="section">Based on</h2>}
          {r.based_on.map((b) => (
            <div key={b.metric_type} className="row">
              <strong>{b.label}</strong><span>{b.value_text}</span><span className="caption">{b.window}</span>
            </div>
          ))}
          {r.evidence.length > 0 && <h2 className="section">Evidence</h2>}
          {r.evidence.map((e) => (
            <div key={e.id} className="row column">
              <span><strong>[{e.id}]</strong> {e.description}</span>
              <span className="caption">{e.text}</span>
            </div>
          ))}
        </>
      )}
    </main>
  );
}
