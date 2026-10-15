import { FRAMES, START_FRAME } from "./flows.js";
import { useRoute } from "./router.js";
import { BottomNav, Button, Phone, TopBar } from "./components.jsx";
import Home from "./screens/Home.jsx";
import Status from "./screens/Status.jsx";

// Frames with `screen: "..."` in flows.js draw one of these instead of the generic placeholder.
// Steps 11 to 13 add one entry each.
const SCREENS = {};

// Wireframe-level skeleton: every Figma frame exists and the taps match the prototype connections.
// Real forms and logic replace the placeholder lines screen by screen (see docs/week1-checklist.md).
export default function App() {
  const route = useRoute() || START_FRAME;

  if (route === "status") return <Status />;
  if (route === "index") return <FrameIndex />;

  const frame = FRAMES[route];
  if (!frame) {
    return (
      <Phone>
        <TopBar title="Not found" />
        <p className="pad">No frame called "{route}". <a href="#/index">See all frames</a></p>
      </Phone>
    );
  }

  const Screen = frame.screen ? SCREENS[frame.screen] : null;

  return (
    <Phone>
      <TopBar title={frame.title} back={frame.back} gear={frame.gear} />
      {Screen ? (
        <Screen frameId={route} frame={frame} />
      ) : (
        <>
          <main className={frame.sheet ? "body sheet" : "body"}>
            {frame.step && <p className="caption">{frame.step}</p>}
            {frame.seg && (
              <p className="caption">
                View: <strong>{frame.seg}</strong>
              </p>
            )}
            {frame.live === "home" && <Home />}
            {frame.lines.map((line) => (
              <p key={line} className="line">{line}</p>
            ))}
            {frame.actions.some((a) => a.variant === "row")
              ? frame.actions.map((a) => <Button key={a.label} label={a.label} to={a.to} variant="row" />)
              : null}
          </main>
          <footer className="footer">
            {frame.actions.filter((a) => a.variant !== "row").map((a) => (
              <Button key={a.label} label={a.label} to={a.to} variant={a.variant} />
            ))}
          </footer>
        </>
      )}
      {frame.nav && <BottomNav selected={frame.nav} />}
      <p className="frame-id">Frame {route}</p>
    </Phone>
  );
}

function FrameIndex() {
  return (
    <main className="page">
      <h1>Frames</h1>
      <p className="lede">Jump to any wireframe frame. <a href="#/status">Connection check</a></p>
      <ul className="index">
        {Object.entries(FRAMES).map(([id, f]) => (
          <li key={id}>
            <a href={`#/${id}`}><strong>{id}</strong> {f.title}</a> <span className="caption">{f.group}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
