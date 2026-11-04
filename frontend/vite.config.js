import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The proxy sends /api/* to the FastAPI server
// the LLM API key can stay on the server.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
