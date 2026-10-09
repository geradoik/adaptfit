import { useEffect, useState } from "react";

// Tiny hash router (no dependency). "#/02a" shows frame 02a; "#/index" lists every frame; "#/status" is the
// connection check. The browser back button and `history.back()` work because each change adds a history entry.
function readRoute() {
  const hash = window.location.hash.replace(/^#\/?/, "");
  return hash || "";
}

export function useRoute() {
  const [route, setRoute] = useState(readRoute);
  useEffect(() => {
    const onChange = () => setRoute(readRoute());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

export function go(route) {
  window.location.hash = `/${route}`;
}

export function goBack() {
  window.history.back();
}
