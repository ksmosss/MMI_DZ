
import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import AnalyticsConsentBanner from "./AnalyticsConsentBanner";
import { initAnalytics } from "./analytics";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
    <AnalyticsConsentBanner />
  </React.StrictMode>
);

initAnalytics();
