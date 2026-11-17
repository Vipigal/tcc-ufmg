import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ThemeProvider } from "./App";
import { applyTheme, browserStorage, readTheme } from "./lib/theme";
import { HOW_PATH } from "./lib/paths";
import { EventPage } from "./pages/EventPage";
import { Home } from "./pages/Home";
import { HowItWorks } from "./pages/HowItWorks";
import "./styles.css";

applyTheme(readTheme(browserStorage));

const root = document.getElementById("root");
if (!root) throw new Error("sem #root no index.html");

createRoot(root).render(
  <StrictMode>
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path={HOW_PATH} element={<HowItWorks />} />
          <Route path="/:evento" element={<EventPage />} />
          <Route path="/:evento/:community" element={<EventPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  </StrictMode>,
);
