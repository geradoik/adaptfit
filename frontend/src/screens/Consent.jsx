import { useState } from "react";
import { getConsent, setConsent } from "../api.js";
import { target } from "../flows.js";
import { Banner, Chips } from "../forms.jsx";
import { go } from "../router.js";
 
// Frame 06: privacy and AI explanations. AI answers are OFF until the user turns them on (NFR-6).
export default function Consent() {
  const [on, setOn] = useState(getConsent());
 
  const save = () => {
    setConsent(on);
    go(target("06", "Save choices"));
  };
 
  return (
    <main className="body">
      <Banner>General fitness guidance, not medical advice.</Banner>
      <h2 className="section">AI explanations</h2>
      <p className="line">
        When this is on, your questions and your summary numbers (age, weight, check-in results and metrics) are sent to
        an AI service to write the answer. Your name, email and account id are never sent. When it is off, nothing
        leaves this app and answers come from rules.
      </p>
      <Chips options={[{ value: "off", label: "Off" }, { value: "on", label: "On" }]}
        value={on ? "on" : "off"} onChange={(v) => setOn(v === "on")} />
      <p className="caption">{on ? "AI answers are ON." : "AI answers are OFF (the default)."}</p>
      <h2 className="section">Your data</h2>
      <p className="line">You can download or delete everything we keep about you in Settings.</p>
      <footer className="footer">
        <button className="btn primary" onClick={save}>Save choices</button>
      </footer>
    </main>
  );
}
