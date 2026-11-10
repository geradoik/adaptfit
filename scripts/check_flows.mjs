// Checks that frontend/src/flows.js matches the Figma prototype connections (docs/prototype-flows.md).
// Run: npm run check:flows (inside frontend/). Needs only Node.
import { FRAMES, BOTTOM_NAV } from "../frontend/src/flows.js";

const expected = [
  ["01a", "Continue", "01b"], ["01b", "Continue", "01c"], ["01b", "Back", "01a"], ["01c", "Back", "01b"],
  ["01c", "Create my profile", "06"], ["06", "Save choices", "03a"], ["03c", "Start check-in", "02a"],
  ["02a", "+ Add something else", "02b"], ["02b", "Weights", "02c"], ["02b", "Cardio", "02d"],
  ["02c", "Add", "02a"], ["02d", "Add", "02a"], ["02a", "Save check-in", "03a"],
  ["03a", "Why this suggestion?", "04a"], ["03a", "Ask a question", "08"], ["03a", "Compare weeks", "05b"],
  ["05a", "Compare", "05b"], ["05b", "Timeline", "05a"], ["07", "Privacy and AI explanations", "06"],
];

let failures = 0;
const fail = (message) => { failures++; console.error("FAIL", message); };

for (const [frame, label, to] of expected) {
  const action = FRAMES[frame]?.actions.find((a) => a.label === label);
  if (!action) fail(`${frame}: missing button "${label}"`);
  else if (action.to !== to) fail(`${frame}: "${label}" goes to ${action.to}, expected ${to}`);
}
if (FRAMES["03a"].gear !== "07") fail("03a: gear icon should open 07");
for (const frame of ["04a", "04b", "07", "08"]) if (!FRAMES[frame].back) fail(`${frame}: back arrow should go back`);
const tabs = Object.fromEntries(BOTTOM_NAV.map((t) => [t.label, t.to]));
if (tabs["Check-in"] !== "02a" || tabs["Home"] !== "03a" || tabs["History"] !== "05a") fail("BottomNav targets are wrong");
for (const [id, frame] of Object.entries(FRAMES)) {
  for (const a of frame.actions) if (!FRAMES[a.to]) fail(`${id}: "${a.label}" points at unknown frame ${a.to}`);
  if (frame.gear && !FRAMES[frame.gear]) fail(`${id}: gear points at unknown frame ${frame.gear}`);
}

if (failures) { console.error(`${failures} problem(s)`); process.exit(1); }
console.log(`Flows OK: ${expected.length} connections, bottom nav and back arrows match the Figma prototype.`);
