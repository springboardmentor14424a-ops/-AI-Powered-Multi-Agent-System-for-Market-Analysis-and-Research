import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The proxy keeps frontend and API on the same origin in development,
// so the HTTP-only auth cookie works without any CORS tricks.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
});
