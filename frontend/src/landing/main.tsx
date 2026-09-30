import { createRoot, hydrateRoot } from "react-dom/client";
import LandingRoot from "./Root";
import "../index.css";

const root = document.getElementById("root")!;
// The production build pre-renders the page; the dev server doesn't.
const page = <LandingRoot path={location.pathname} />;
if (root.hasChildNodes()) hydrateRoot(root, page);
else createRoot(root).render(page);
