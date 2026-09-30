import path from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { SITE } from "./src/site";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

/** Fill each page's <!--head--> with its title, description, and link-preview tags. */
function siteHead(): Plugin {
  // Absolute URLs for link previews and the canonical link, once the site has a domain (e.g. https://example.com).
  const siteUrl = (process.env.SITE_URL ?? "").replace(/\/$/, "");
  return {
    name: "site-head",
    transformIndexHtml(html, ctx) {
      const isApp = ctx.filename.replace(/\\/g, "/").endsWith("/app/index.html");
      const title = isApp ? `Make a template · ${SITE.name}` : SITE.title;
      const pagePath = isApp ? "/app/" : "/";
      const tags = [
        `<title>${esc(title)}</title>`,
        `<meta name="description" content="${esc(SITE.description)}" />`,
        `<meta property="og:type" content="website" />`,
        `<meta property="og:site_name" content="${esc(SITE.name)}" />`,
        `<meta property="og:title" content="${esc(title)}" />`,
        `<meta property="og:description" content="${esc(SITE.description)}" />`,
        `<meta property="og:image" content="${siteUrl}/og.png" />`,
        `<meta property="og:image:width" content="1200" />`,
        `<meta property="og:image:height" content="630" />`,
        `<meta name="twitter:card" content="summary_large_image" />`,
        ...(siteUrl
          ? [`<link rel="canonical" href="${siteUrl}${pagePath}" />`, `<meta property="og:url" content="${siteUrl}${pagePath}" />`]
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
      input: {
        landing: path.resolve(__dirname, "index.html"),
        app: path.resolve(__dirname, "app/index.html"),
      },
    },
  },
  server: {
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
