declare global {
  interface Window {
    umami?: {
      track: (event: string, data?: Record<string, string>) => void;
    };
  }
}

/** Count an action in Umami. Does nothing when the tracker isn't loaded (dev, blocked, or not set up yet). */
export function track(event: string, data?: Record<string, string>) {
  try {
    window.umami?.track(event, data);
  } catch {
    /* analytics must never break the app */
  }
}
