
import { useState } from "react";
import {
  getAnalyticsConsent,
  setAnalyticsConsent,
  type AnalyticsConsent,
} from "./analytics";

export default function AnalyticsConsentBanner() {
  const [consent, setConsent] = useState<AnalyticsConsent>(
    getAnalyticsConsent
  );

  if (consent !== null) return null;

  function choose(allowed: boolean) {
    setAnalyticsConsent(allowed);
    setConsent(allowed ? "accepted" : "rejected");
  }

  return (
    <aside
      role="dialog"
      aria-label="Настройка аналитики"
      style={{
        position: "fixed",
        bottom: 20,
        left: 20,
        right: 20,
        maxWidth: 560,
        margin: "auto",
        padding: 20,
        background: "#fff",
        color: "#172b4d",
        borderRadius: 12,
        boxShadow: "0 4px 24px #0003",
        zIndex: 9999,
      }}
    >
      <strong>Аналитика TaskFlow</strong>
      <p>
        Разрешить использование Google Analytics 4
        для сбора статистики использования приложения?
      </p>
      <div style={{ display: "flex", gap: 12 }}>
        <button type="button" onClick={() => choose(false)}>
          Отклонить
        </button>
        <button type="button" onClick={() => choose(true)}>
          Разрешить аналитику
        </button>
      </div>
    </aside>
  );
}
