import { StrictMode } from "react";
import { ThemeProvider } from "@/components/theme-provider";
import Landing from "./Landing";

// Rendered to static HTML at build time (entry-server.tsx) and hydrated in the browser (main.tsx).
export default function LandingRoot() {
  return (
    <StrictMode>
      <ThemeProvider>
        <Landing />
      </ThemeProvider>
    </StrictMode>
  );
}
