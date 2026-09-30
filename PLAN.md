# Launch Plan

Goal: launch the app publicly as fast as possible, cheaply, and able to handle many users at once. Accounts and paid tiers come after launch.

## Where we left off (2026-09-30)

Live on the server's IP (plain HTTP): landing page at `/`, tool at `/app/`, Ko-fi tips. Every push to `main` deploys automatically. Phase 1 §1–3 and most of §5 are done.

**Waiting on:**
- **Stripe review of the Ko-fi account.** Stripe flagged the new, empty Ko-fi page. We added content and "tip" wording and submitted their form. Until it's approved, card payments may be paused; PayPal still works. Never say "donate" or "donations" in public copy: Stripe only allows that for registered charities.

**Next up (pick one):**
- **§4 Legal and analytics:** privacy policy, terms, cookie-free analytics.
- **Phase 0 domain + Cloudflare.** When the domain exists:
  - Add `SITE_ADDRESS=<domain>` to `/opt/skeleton3d/.env` on the server, so Caddy gets an HTTPS certificate.
  - Pass `SITE_URL=https://<domain>` to the Docker build as a build arg. The workflow doesn't pass it yet, and link previews need it for absolute image URLs.
  - Tell Caddy to trust Cloudflare's IP ranges (`trusted_proxies`). Otherwise every visitor shares one IP and one upload rate limit.
  - Point the Ko-fi page's website link at the domain.

**Other loose ends:** the gallery needs photos of real builds.

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

- **Hetzner Cloud, Regular Performance, 3 vCPU / 4 GB / 80 GB** (CA$37.49/mo; Cost-Optimized wasn't available), Ubuntu 24.04. 4 GB is why background removal runs one at a time (`SEGMENT_CONCURRENCY=1`) with a 4 GB swap file. Measured on the server: 2–3 s per upload, ~1.7 GB RAM in use.
- Log in as `deploy` (SSH keys only, passwordless sudo). The IP is in the `VPS_HOST` GitHub secret and the Mac's SSH config (kept out of the repo so Cloudflare can hide it). Authorized keys: the Windows PC, the Mac (`ssh skeleton` via `~/.ssh/config.d/skeleton.conf`), and the GitHub Actions deploy key. To add a machine without SSH, use the Hetzner web console (Rescue → Reset root password, then Console) and append the key with `>>`. Hetzner Cloud Firewall and `ufw` both allow only 22/80/443.
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
- GitHub Secrets: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` (a deploy-only key), `VPS_KNOWN_HOSTS` (the server's SSH host key).
- Images are tagged `latest` + commit SHA. Each deploy pins its SHA as `APP_IMAGE` in `/opt/skeleton3d/.env` and only rewrites that line, so keep other settings (e.g. `SITE_ADDRESS`) in the same file. Roll back by setting `APP_IMAGE` to an earlier SHA and running `docker compose up -d`.
- Processed uploads live in the `uploads` Docker volume and are deleted 6 h after last use.
- The deploy restarts the app, so there's ~20 s of downtime per deploy.

---

## Phase 0: Decisions (now)

- [ ] Buy a domain
- [ ] Pick the product name and branding ("3D Pen Skeleton" is fine as a repo name; a catchier name helps the landing page and social posts)
- [x] Create the Hetzner account and a server (went with 3 vCPU / 4 GB; see Hosting)
- [ ] Create a Cloudflare account and move the domain's DNS there

## Phase 1: Launch (~1–2 weeks)

### 1. Production-proof the tool (do first: this is what would break on launch day)
- [x] **Fix cache eviction.** Only 20 uploads are kept in memory (`backend/app/main.py:22`). With more than 20 concurrent users, people get "Image not found or expired" mid-session. Save prepared masks to disk (or Redis) keyed by hash.
- [x] **Limit concurrent background removals** (~2 at a time, with a queue). rembg already uses every core, so running more at once only slows everyone down and uses more RAM. Show a "Processing…" state in the UI.
- [x] **Downscale photos in the browser** before upload (e.g. 1600 px max side).
- [x] **Rate-limit uploads per IP** (Caddy or app).
- [x] Add a `/api/health` endpoint.
- [x] Split dev dependencies (`pytest`, `httpx`) out of `backend/requirements.txt`.
- [x] Friendly error states in the UI.

### 2. Landing page
- [x] Routing: `/` = landing, `/app` = tool
- [x] Hero with a before-and-after: photo → template → finished 3D-pen build (a generated duck for now; swap in a real build photo when there is one)
- [x] "How it works" in 3 steps
- [ ] Gallery of real examples (section is built and hidden until `GALLERY` in `frontend/src/landing/Landing.tsx` has photos)
- [x] FAQ
- [x] "Try it free" button
- [x] Pre-render the landing page to static HTML at build time (SEO + link previews)
- [x] Open Graph image, favicon, meta tags (set `SITE_URL` once there is a domain, for absolute preview URLs)

### 3. Tips (no backend code)
- [x] Ko-fi (ko-fi.com/mamooji): 0% on one-off tips with Contributor off, only card/PayPal processing fees
- [x] Small button in the header
- [x] Friendly prompt right after PDF export

### 4. Legal and analytics
- [ ] Privacy policy (photos are processed and deleted 6 h after last use; check which country the server is in, and plan for GDPR since EU visitors will use it either way)
- [ ] Terms of use
- [ ] Privacy-friendly analytics without cookies (Plausible, or self-hosted Umami), so no cookie banner is needed

### 5. Infrastructure
- [x] VPS setup: non-root `deploy` user, SSH keys only, `ufw` (22/80/443), Docker + compose plugin, swap file, `unattended-upgrades`
- [x] `Dockerfile` + `docker-compose.yml` + `Caddyfile`
- [x] GitHub Actions workflow: test → build → push to GHCR → deploy over SSH (`.github/workflows/deploy.yml`)
- [ ] DNS A record → VPS, proxied through Cloudflare
- [x] Docker log rotation
- [x] Docker healthcheck using `/api/health`
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
