const ID = "G-ZQ09Q8ZCHM";
const KEY = "taskflow_analytics_consent";

declare global {
  interface Window {
    dataLayer?: IArguments[];
    gtag?: (...args: unknown[]) => void;
  }
}

export type AnalyticsConsent = "accepted" | "rejected" | null;

export function getAnalyticsConsent(): AnalyticsConsent {
  const value = localStorage.getItem(KEY);
  return value === "accepted" || value === "rejected" ? value : null;
}

export function initAnalytics(): void {
  if (getAnalyticsConsent() !== "accepted") return;
  if (window.gtag) return;

  window.dataLayer = window.dataLayer || [];

  window.gtag = function () {
    window.dataLayer!.push(arguments);
  };

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${ID}`;
  document.head.appendChild(script);

  window.gtag("js", new Date());
  window.gtag("config", ID, { send_page_view: true });
}

export function setAnalyticsConsent(allowed: boolean): void {
  localStorage.setItem(KEY, allowed ? "accepted" : "rejected");

  if (allowed) {
    location.reload();
  } else {
    location.reload();
  }
}

export function trackEvent(name: string): void {
  if (getAnalyticsConsent() !== "accepted") return;
  window.gtag?.("event", name);
}