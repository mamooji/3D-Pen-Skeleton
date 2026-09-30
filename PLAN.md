# Launch Plan

Goal: launch the app publicly as fast as possible, cheaply, and able to handle many users at once. Accounts and paid tiers come after launch.

## Key numbers (measured on an M1 Pro, 1600×1200 photo)

| Step | Time | Memory |
|---|---|---|
| Background removal (rembg, `isnet-general-use`) | ~1.3 s | ~1.45 GB |
| Everything else in upload (inflate, crop, fields) | ~0.1 s | ~120 MB |
| Rebuild template (slider change) | ~0.03 s | — |
| PDF export | ~0 s | — |

- Only the upload is expensive; slider changes are nearly free.
- Background removal is ~95% of CPU and ~90% of RAM. Expect 2–4 s per upload on a VPS.

## Hosting

- **Hetzner Cloud, shared x86, 4 vCPU / 8 GB** (~€8–15/mo), in the location closest to the audience.
- When resizing, choose **"CPU and RAM only"** so the disk doesn't grow and a downgrade stays possible.
- **Cloudflare** (free plan) in front: DDoS protection, static caching, hides the origin IP.
- After Phase 2 moves background removal to the browser, downsize to ~2 vCPU / 4 GB (~€4–5/mo).

Why Hetzner: the cheapest compute by far (DigitalOcean/Linode ~3–4×, Render/Railway/Fly ~$25–50+ for 2 GB+). The price is flat, so going viral makes it slower, not more expensive. Serverless is a poor fit: cold starts load a 1.5 GB model, and the in-memory cache doesn't survive across instances.

## Deploy architecture

```
push to main ─► GitHub Actions: tests ─► build image ─► push to ghcr.io
                                                   │
                                                   ▼
                          SSH into VPS: docker compose pull && up -d
                                                   │
   Internet ─► Cloudflare ─► Caddy (HTTPS, :443) ─► app container (:8000)
```

- Multi-stage `Dockerfile`: Node builds `frontend/dist`, Python slim runs uvicorn with **one worker**. The rembg model is downloaded during the build and ships in the image.
- `docker-compose.yml`: `app` + `caddy` (automatic Let's Encrypt, no default upload size limit).
- GitHub Secrets: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` (a deploy-only key).
- Images are tagged `latest` + commit SHA. Roll back by pinning an earlier SHA and running `up -d`.

---

## Phase 0: Decisions (now)

- [ ] Buy a domain
- [ ] Pick the product name and branding ("3D Pen Skeleton" is fine as a repo name; a catchier name helps the landing page and social posts)
- [ ] Create the Hetzner account and a 4 vCPU / 8 GB server
- [ ] Create a Cloudflare account and move the domain's DNS there

## Phase 1: Launch (~1–2 weeks)

### 1. Production-proof the tool (do first: this is what would break on launch day)
- [ ] **Fix cache eviction.** Only 20 uploads are kept in memory (`backend/app/main.py:22`). With more than 20 concurrent users, people get "Image not found or expired" mid-session. Save prepared masks to disk (or Redis) keyed by hash.
- [ ] **Limit concurrent background removals** (~2 at a time, with a queue). rembg already uses every core, so running more at once only slows everyone down and uses more RAM. Show a "Processing…" state in the UI.
- [ ] **Downscale photos in the browser** before upload (e.g. 1600 px max side).
- [ ] **Rate-limit uploads per IP** (Caddy or app).
- [ ] Add a `/api/health` endpoint.
- [ ] Split dev dependencies (`pytest`, `httpx`) out of `backend/requirements.txt`.
- [ ] Friendly error states in the UI.

### 2. Landing page
- [ ] Routing: `/` = landing, `/app` = tool
- [ ] Hero with a before-and-after: photo → template → finished 3D-pen build
- [ ] "How it works" in 3 steps
- [ ] Gallery of real examples
- [ ] FAQ
- [ ] "Try it free" button
- [ ] Pre-render the landing page to static HTML at build time (SEO + link previews)
- [ ] Open Graph image, favicon, meta tags

### 3. Donations (no backend code)
- [ ] Stripe Payment Link (or Ko-fi / Buy Me a Coffee)
- [ ] Small button in the header
- [ ] Friendly prompt right after PDF export

### 4. Legal and analytics
- [ ] Privacy policy (photos are processed and not kept; the server is EU-hosted, so GDPR applies)
- [ ] Terms of use
- [ ] Privacy-friendly analytics without cookies (Plausible, or self-hosted Umami), so no cookie banner is needed

### 5. Infrastructure
- [ ] VPS setup: non-root `deploy` user, SSH keys only, `ufw` (22/80/443), Docker + compose plugin, swap file, `unattended-upgrades`
- [ ] `Dockerfile` + `docker-compose.yml` + `Caddyfile`
- [ ] GitHub Actions workflow: test → build → push to GHCR → deploy over SSH
- [ ] DNS A record → VPS, proxied through Cloudflare
- [ ] Docker log rotation
- [ ] Docker healthcheck using `/api/health`
- [ ] Uptime monitor (UptimeRobot / BetterStack)

### Launch
- [ ] Post in r/3Dpen, 3D-pen Facebook groups, and short TikToks/Shorts showing photo → template → build

## Phase 2: Background removal in the browser (soon after launch)

This removes ~90% of server load and lets the VPS shrink to ~€4–5/mo.

- [ ] Run background removal on the user's device with onnxruntime-web (WebGPU, WASM fallback)
- [ ] Upload the resulting transparent PNG. The backend already skips rembg for transparent PNGs.
- [ ] Keep server-side rembg as a fallback for devices that can't run the model
- [ ] Look for a smaller model than the current ~180 MB one that's still good enough. It's downloaded once per visitor, then cached.
- [ ] **License check:** use `isnet-general-use` (the current model) or another permissively licensed model. Avoid `@imgly/background-removal` (AGPL) and BRIA RMBG (no commercial use).
- [ ] Downsize the VPS

## Phase 3: Accounts (once there's real usage)

The tool stays fully usable without an account. Accounts unlock saving.

- [ ] Supabase: auth (Google + email magic link), Postgres, file storage
- [ ] The React app handles sign-in; FastAPI checks the Supabase JWT on protected endpoints
- [ ] "My templates": save the photo, settings, and PDF, and reopen them later
- [ ] "Sign in to save this template" prompt after export

## Phase 4: Earn more than donations (only if traffic justifies it)

- [ ] "Supporter" tier via Stripe Checkout + webhooks, tied to accounts. Perks could be unlimited saved templates, larger or more detailed templates, a badge, and early access. The core tool stays free.
- [ ] Community gallery: builds shared next to their templates (brings people back, adds search content, feeds the landing page)

## Scaling path (only when needed)

1. Upgrade the Hetzner box in place (minutes)
2. Multiple workers sharing the disk/Redis cache
3. A separate server just for background removal
