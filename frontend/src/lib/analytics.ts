declare global {
  interface Window {
    umami?: { track: (event: string) => void };
  }
}

/** Count an action in Umami. Does nothing when the tracker isn't loaded (dev, blocked, or not set up yet). */
export function track(event: string) {
  try {
    window.umami?.track(event);
  } catch {
    /* analytics must never break the app */
  }
}
