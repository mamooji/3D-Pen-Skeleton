import { createRoot, hydrateRoot } from "react-dom/client";
import LandingRoot from "./Root";
import "../index.css";

const root = document.getElementById("root")!;
// The production build pre-renders the page; the dev server doesn't.
if (root.hasChildNodes()) hydrateRoot(root, <LandingRoot />);
else createRoot(root).render(<LandingRoot />);
