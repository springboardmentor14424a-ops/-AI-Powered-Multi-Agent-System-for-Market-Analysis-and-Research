import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Any request starting with /api is passed on to the FastAPI backend.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
