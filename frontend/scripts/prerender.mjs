// Render the landing and legal pages into their dist/**/index.html, so search engines and link previews see the
// content without JS. Runs after `vite build` and `vite build --ssr src/landing/entry-server.tsx --outDir dist-ssr`
// (see package.json).
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(import.meta.dirname, "..");
const ssrDir = path.join(root, "dist-ssr");

const { render, paths, site } = await import(
  pathToFileURL(path.join(ssrDir, "entry-server.js")).href
);
const missing = ["operator", "contactEmail", "governingLaw"].filter(
  (k) => !site[k],
);
if (missing.length)
  throw new Error(
    `prerender: set ${missing.join(", ")} in src/site.ts (used by the legal pages)`,
  );

const marker = '<div id="root"></div>';
for (const url of paths) {
  const page = path.join(root, "dist", url, "index.html");
  const html = fs.readFileSync(page, "utf8");
  if (!html.includes(marker))
    throw new Error(`prerender: ${marker} not found in ${page}`);
  fs.writeFileSync(
    page,
    html.replace(marker, `<div id="root">${render(url)}</div>`),
  );
  console.log(`prerendered ${path.relative(root, page)}`);
}
fs.rmSync(ssrDir, { recursive: true, force: true });
