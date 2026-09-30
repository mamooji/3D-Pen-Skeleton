// Render the landing page into dist/index.html, so search engines and link previews see the content without JS.
// Runs after `vite build` and `vite build --ssr src/landing/entry-server.tsx --outDir dist-ssr` (see package.json).
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(import.meta.dirname, "..");
const ssrDir = path.join(root, "dist-ssr");
const page = path.join(root, "dist", "index.html");

const { render } = await import(pathToFileURL(path.join(ssrDir, "entry-server.js")).href);
const html = fs.readFileSync(page, "utf8");
const marker = '<div id="root"></div>';
if (!html.includes(marker)) throw new Error(`prerender: ${marker} not found in dist/index.html`);
fs.writeFileSync(page, html.replace(marker, `<div id="root">${render()}</div>`));
fs.rmSync(ssrDir, { recursive: true, force: true });
console.log("prerendered dist/index.html");
