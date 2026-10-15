// Talking to the backend. Every call goes to /api/..., which Vite forwards to FastAPI on port 8000.

async function request(method, url, body) {
  const response = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try {
    data = await response.json();
  } catch {
    // some error replies have no JSON body
  }
  if (!response.ok) {
    // FastAPI puts our message in "detail". Show it as it is.
    const message = data && typeof data.detail === "string" ? data.detail : `Server replied ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

export const getJSON = (url) => request("GET", url);
export const postJSON = (url, body) => request("POST", url, body);

// Which user is using the app? There is no login yet, so we remember the id the server gave at onboarding.
const KEY = "adaptfit_user_id";
let memoryId = null; // used when the browser blocks localStorage

export function getUserId() {
  try {
    const stored = window.localStorage.getItem(KEY);
    if (stored) return Number(stored);
  } catch {
    // storage blocked: fall through to memory
  }
  return memoryId;
}

export function setUserId(id) {
  memoryId = id;
  try {
    window.localStorage.setItem(KEY, String(id));
  } catch {
    // storage blocked: the id only lives until the page reloads
  }
}

export function clearUserId() {
  memoryId = null;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    // nothing to clear
  }
}

// The user's own id, or the simulated demo persona when nobody has onboarded yet.
export async function resolveUserId() {
  const own = getUserId();
  if (own) return own;
  const demo = await getJSON("/api/demo/user");
  return demo.user_id;
}

// Today's date as YYYY-MM-DD in the user's own time zone (toISOString would give the UTC date).
export function todayISO() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}
