type YmFunction = ((...args: unknown[]) => void) & {
  a?: unknown[][];
  l?: number;
};

declare global {
  interface Window {
    ym?: YmFunction;
  }
}

const id = Number(import.meta.env.VITE_METRIKA_ID || 0);

export function trackEvent(name: string): void {
  if (id > 0 && window.ym) {
    window.ym(id, 'reachGoal', name);
  }
}

export function initAnalytics(): void {
  if (!Number.isInteger(id) || id < 1) return;

  if (!window.ym) {
    const queued = ((...args: unknown[]) => {
      queued.a?.push(args);
    }) as YmFunction;

    queued.a = [];
    queued.l = Date.now();
    window.ym = queued;
  }

  const src = 'https://mc.yandex.ru/metrika/tag.js';

  if (!document.querySelector(`script[src="${src}"]`)) {
    const script = document.createElement('script');
    script.async = true;
    script.src = src;
    document.head.appendChild(script);
  }

  window.ym?.(id, 'init', {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
  });
}