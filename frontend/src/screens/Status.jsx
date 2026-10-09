import { useEffect, useState } from "react";

// Connection check: proves client -> server -> database. Open it at #/status.
export default function Status() {
  const [state, setState] = useState({ phase: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`Server replied ${response.status}`);
        return response.json();
      })
      .then((data) => setState({ phase: "ok", data }))
      .catch((error) => {
        if (error.name !== "AbortError") setState({ phase: "error", message: error.message });
      });
    return () => controller.abort();
  }, []);

  const server = state.phase === "ok" ? "ok" : state.phase;
  const database = state.phase === "ok" ? state.data.database : state.phase;

  return (
    <main className="page">
      <h1>AdaptFit</h1>
      <p className="lede">Connection check</p>
      <ul className="checks" aria-live="polite">
        <Check label="Client" status="ok" detail="React is running" />
        <Check label="Server" status={server} detail={state.phase === "error" ? state.message : "FastAPI answered /api/health"} />
        <Check
          label="Database"
          status={database}
          detail={state.phase === "ok" ? `${state.data.tables} tables, schema version ${state.data.schema_version}` : "Waiting for the server"}
        />
      </ul>
      {state.phase === "error" && (
        <p className="hint">
          Start the backend first: <code>uvicorn app.main:app --reload --port 8000</code> inside <code>backend/</code>.
        </p>
      )}
      <p className="hint"><a href="#/index">All wireframe frames</a> &middot; <a href="#/01a">Start the app</a></p>
    </main>
  );
}

function Check({ label, status, detail }) {
  const text = status === "ok" ? "Working" : status === "loading" ? "Checking" : "Failed";
  return (
    <li className={`check ${status}`}>
      <span className="check-label">{label}</span>
      <span className="check-status">{text}</span>
      <span className="check-detail">{detail}</span>
    </li>
  );
}
