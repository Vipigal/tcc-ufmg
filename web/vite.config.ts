import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // data/export/ é servido na raiz: fetch("/index.json"), fetch("/eleicoes/tweets.json")
  publicDir: "../data/export",
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
