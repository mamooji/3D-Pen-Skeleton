import { StrictMode, type JSX } from "react";
import { ThemeProvider } from "@/components/theme-provider";
import { PRIVACY_PATH, TERMS_PATH } from "@/site";
import Landing from "./Landing";
import { Privacy, Terms } from "./Legal";

// Pages that share this entry, by URL path. Each has an HTML file in PAGES (vite.config.ts).
export const PAGES: Record<string, () => JSX.Element> = {
  "/": Landing,
  [PRIVACY_PATH]: Privacy,
  [TERMS_PATH]: Terms,
};

// Rendered to static HTML at build time (entry-server.tsx) and hydrated in the browser (main.tsx).
export default function LandingRoot({ path }: { path: string }) {
  const Page = PAGES[path] ?? Landing;
  return (
    <StrictMode>
      <ThemeProvider>
        <Page />
      </ThemeProvider>
    </StrictMode>
  );
}
