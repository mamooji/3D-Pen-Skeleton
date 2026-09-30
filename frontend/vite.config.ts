import path from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { APP_PATH, PRIVACY_PATH, SITE, TERMS_PATH } from "./src/site";

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

// Every HTML page: its source file, public path, and <title>. Legal pages share the landing page's entry script.
const PAGES: Record<
  string,
  { path: string; title: string; description?: string }
> = {
  "index.html": { path: "/", title: SITE.title },
  "app/index.html": { path: APP_PATH, title: `Make a template · ${SITE.name}` },
  "privacy/index.html": {
    path: PRIVACY_PATH,
    title: `Privacy policy · ${SITE.name}`,
    description: `How ${SITE.name} handles your photos and data.`,
  },
  "terms/index.html": {
    path: TERMS_PATH,
    title: `Terms of use · ${SITE.name}`,
  },
};

// Apply the saved theme before first paint (see src/components/theme-provider.tsx).
const THEME_SCRIPT = `<script>
      try {
        var t = localStorage.getItem("skeleton3d-theme") || "system";
        var d = t === "dark" || (t === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
        document.documentElement.classList.toggle("dark", d);
        document.documentElement.style.colorScheme = d ? "dark" : "light";
      } catch (e) {}
    </script>`;

/** Fill each page's <!--head--> with its title, description, link-preview tags, theme script, and analytics. */
function siteHead(): Plugin {
  // Absolute URLs for link previews and the canonical link, once the site has a domain (e.g. https://example.com).
  const siteUrl = (process.env.SITE_URL ?? "").replace(/\/$/, "");
  return {
    name: "site-head",
    transformIndexHtml(html, ctx) {
      const file = path.relative(__dirname, ctx.filename).replace(/\\/g, "/");
      const page = PAGES[file];
      if (!page)
        throw new Error(
          `site-head: ${file} is missing from PAGES in vite.config.ts`,
        );
      const description = page.description ?? SITE.description;
      const tags = [
        `<title>${esc(page.title)}</title>`,
        `<meta name="description" content="${esc(description)}" />`,
        `<meta property="og:type" content="website" />`,
        `<meta property="og:site_name" content="${esc(SITE.name)}" />`,
        `<meta property="og:title" content="${esc(page.title)}" />`,
        `<meta property="og:description" content="${esc(description)}" />`,
        `<meta property="og:image" content="${siteUrl}/og.png" />`,
        `<meta property="og:image:width" content="1200" />`,
        `<meta property="og:image:height" content="630" />`,
        `<meta name="twitter:card" content="summary_large_image" />`,
        ...(siteUrl
          ? [
              `<link rel="canonical" href="${siteUrl}${page.path}" />`,
              `<meta property="og:url" content="${siteUrl}${page.path}" />`,
            ]
          : []),
        `<link rel="icon" href="/favicon.svg" type="image/svg+xml" />`,
        `<link rel="apple-touch-icon" href="/apple-touch-icon.png" />`,
        THEME_SCRIPT,
        // Cookie-free, self-hosted analytics. Caddy forwards /stats/script.js and /stats/api/send to Umami.
        ...(SITE.umamiWebsiteId && !ctx.server
          ? [
              `<script defer src="/stats/script.js" data-website-id="${esc(SITE.umamiWebsiteId)}" data-do-not-track="true"></script>`,
            ]
          : []),
      ];
      return html.replace("<!--head-->", tags.join("\n    "));
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), siteHead()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  build: {
    // The three.js chunk (~550 kB) is lazy-loaded only when the 3D tab opens.
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      input: Object.keys(PAGES).map((file) => path.resolve(__dirname, file)),
    },
  },
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
