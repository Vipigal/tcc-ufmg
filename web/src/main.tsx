import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import App, { RootRedirect } from "./App";
import { applyTheme, browserStorage, readTheme } from "./lib/theme";
import "./styles.css";

// tema antes do primeiro render, para não piscar claro → escuro
applyTheme(readTheme(browserStorage));

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/:evento" element={<App mode="overview" />} />
        <Route path="/:evento/comparar/:a/:b" element={<App mode="compare" />} />
        <Route path="/:evento/:community" element={<App mode="reader" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
