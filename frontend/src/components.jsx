import { BOTTOM_NAV } from "./flows.js";
import { go, goBack } from "./router.js";

export function Phone({ children }) {
  return <div className="phone">{children}</div>;
}

export function TopBar({ title, back, gear }) {
  return (
    <header className="topbar">
      {back ? (
        <button className="icon-btn" aria-label="Back" onClick={goBack}>&larr;</button>
      ) : (
        <span className="icon-btn placeholder" />
      )}
      <h1>{title}</h1>
      {gear ? (
        <button className="icon-btn" aria-label="Settings" onClick={() => go(gear)}>&#9881;</button>
      ) : (
        <span className="icon-btn placeholder" />
      )}
    </header>
  );
}

export function Button({ label, to, variant = "primary" }) {
  return (
    <button className={`btn ${variant}`} onClick={() => go(to)}>
      {label}
    </button>
  );
}

export function BottomNav({ selected }) {
  return (
    <nav className="bottom-nav" aria-label="Main">
      {BOTTOM_NAV.map((tab) => (
        <button key={tab.label} className={tab.label === selected ? "tab selected" : "tab"} onClick={() => go(tab.to)}>
          {tab.label}
        </button>
      ))}
    </nav>
  );
}

export function MetricCard({ label, value, window, estimate }) {
  const missing = value == null;
  return (
    <div className="metric-card">
      <p className="caption">{label}</p>
      <p className={missing ? "metric-value muted" : "metric-value"}>{missing ? "Not enough data yet" : value}</p>
      <p className="caption">{window}</p>
      {estimate && !missing && <span className="tag">Estimate</span>}
    </div>
  );
}
