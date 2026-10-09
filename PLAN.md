# Launch Plan

Goal: launch the app publicly as fast as possible, cheaply, and able to handle many users at once. Accounts and paid tiers come after launch.

## Where we left off (2026-10-09)

Live at **https://trace3dpen.com** (Cloudflare in front, a Cloudflare Origin CA certificate on Caddy): landing page at `/`, tool at `/app/`, Ko-fi tips. Every push to `main` deploys automatically. The product is named **Trace 3D Pen** to match the domain. Phase 1 §1–5 are done; next up is building a few models to photograph, then launch posts.

**Uptime monitor:** UptimeRobot (free plan) runs a keyword check on `https://trace3dpen.com/api/health` for `"ok":true` every 5 minutes and emails on failure.

**Frontend formatting:** Prettier (defaults plus Tailwind class sorting) in `frontend/`. CI fails on unformatted code, so run `npm run format` before pushing, and after `shadcn add` (the CLI writes files without semicolons).

**Ko-fi:** Stripe approved the account, so card tips work. The page's website link points to https://trace3dpen.com. Never say "donate" or "donations" in public copy: Stripe only allows that for registered charities.

**§4 legal and analytics: done.** Privacy policy at `/privacy/`, terms at `/terms/`, Umami counting visits and the `upload`, `pdf-download`, and `kofi` events. Dashboard: `ssh -L 3000:localhost:3000 skeleton`, then http://localhost:3000. Keep the privacy policy in sync with what the code and Cloudflare actually do.

**Domain `trace3dpen.com`** (bought at Squarespace, DNS on Cloudflare's free plan) is live, with Cloudflare SSL/TLS on **Full (strict)**. Caddy trusts Cloudflare's IP ranges and passes the real visitor IP to the app and Umami, `www` redirects to the bare domain, and the server's IP no longer serves the site. `SITE_ADDRESS=trace3dpen.com www.trace3dpen.com` is in the server's `.env`.

**Origin certificate:** Caddy serves a Cloudflare Origin CA certificate for `trace3dpen.com` and `*.trace3dpen.com`, valid until **2041-10-05**. Only Cloudflare trusts it, so it works only with the proxy on and Full (strict). It's in `/opt/skeleton3d/certs/` (`origin.pem`, `origin.key`) on the server only, never in the repo. It replaced Let's Encrypt, whose renewals would have had to reach the server through Cloudflare, which gets risky once the firewall only allows Cloudflare. To replace it: Cloudflare → SSL/TLS → Origin Server → Create Certificate, copy both files over the old ones, then `docker compose restart caddy`. Keep in Cloudflare: Scrape Shield's **Email Address Obfuscation** off (it rewrites the contact email and breaks React hydration), and Web Analytics' automatic setup, Rocket Loader, and Bot Fight Mode off (they'd add scripts or cookies the privacy policy doesn't mention).

**Phase 2 (background removal in the browser):** built and tested locally on 2026-10-09; see the Phase 2 checklist for what's left (deploy, Cloudflare Cache Rule, phone testing, then downsizing).

**Next up:**
1. **Build a few models** (in progress) and photograph them: these feed both the launch posts and the landing page gallery (add them to `GALLERY` in `frontend/src/landing/Landing.tsx`; photos go in `frontend/public/landing/gallery/`).
2. **Launch posts:** r/3Dpen, 3D-pen Facebook groups, and short TikToks/Shorts showing photo → template → build. Claude can draft the Reddit post and a video script. On hold until there are photos.

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
- Log in as `deploy` (SSH keys only, passwordless sudo). The IP is in the `VPS_HOST` GitHub secret and the Mac's SSH config (kept out of the repo so Cloudflare can hide it). Authorized keys: the Windows PC, the Mac (`ssh skeleton` via `~/.ssh/config.d/skeleton.conf`), and the GitHub Actions deploy key. To add a machine without SSH, use the Hetzner web console (Rescue → Reset root password, then Console) and append the key with `>>`. **Hetzner Cloud Firewall** (the real gate): TCP 22 and ICMP from anywhere, TCP 80 and 443 **only from Cloudflare's IP ranges** (https://www.cloudflare.com/ips/), so the site can't be reached around Cloudflare. Keep ICMP: path MTU discovery needs it. If Cloudflare adds ranges, update both the firewall rules and `trusted_proxies` in `caddy/Caddyfile`. `ufw` also allows only 22/80/443, but Docker's published ports bypass it, so it doesn't actually filter 80/443.
- When resizing, choose **"CPU and RAM only"** so the disk doesn't grow and a downgrade stays possible.
- **Cloudflare** (free plan) in front: DDoS protection, static caching, hides the origin IP.
- After Phase 2 moves background removal to the browser, downsize to ~2 vCPU / 4 GB (~€4–5/mo).

Why Hetzner: the cheapest compute by far (DigitalOcean/Linode ~3–4×, Render/Railway/Fly ~$25–50+ for 2 GB+). The price is flat, so going viral makes it slower, not more expensive. Serverless is a poor fit: cold starts load a 1.5 GB model, and the in-memory cache doesn't survive across instances.

## Deploy architecture

```
push to main ─► GitHub Actions: tests + format check ─► build image ─► push to ghcr.io
                                                                  │
                                                                  ▼
                          SSH into VPS: docker compose pull && up -d
                                                   │
   Internet ─► Cloudflare ─► Caddy (HTTPS, :443) ─► app container (:8000)
```

- Multi-stage `Dockerfile`: Node builds `frontend/dist`, Python slim runs uvicorn with **one worker**. The rembg model is downloaded during the build and ships in the image.
- `docker-compose.yml`: `app` + `caddy` (Cloudflare Origin CA certificate mounted from `/opt/skeleton3d/certs/`, no default upload size limit) + `umami` and `umami-db` (analytics; Caddy exposes only `/stats/script.js` and `/stats/api/send`, and the dashboard is on the server's `127.0.0.1:3000`).
- GitHub Secrets: `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY` (a deploy-only key), `VPS_KNOWN_HOSTS` (the server's SSH host key).
- Images are tagged `latest` + commit SHA. Each deploy pins its SHA as `APP_IMAGE` in `/opt/skeleton3d/.env` and only rewrites that line, so keep other settings (e.g. `SITE_ADDRESS`) in the same file. Roll back by setting `APP_IMAGE` to an earlier SHA and running `docker compose up -d`.
- Processed uploads live in the `uploads` Docker volume and are deleted 6 h after last use.
- The deploy restarts the app, so there's ~20 s of downtime per deploy.

---

## Phase 0: Decisions (now)

- [x] Buy a domain: `trace3dpen.com` (Squarespace)
- [x] Pick the product name: **Trace 3D Pen**, to match the domain (the repo, server paths, and image name still say "skeleton")
- [x] Create the Hetzner account and a server (went with 3 vCPU / 4 GB; see Hosting)
- [x] Create a Cloudflare account and move the domain's DNS there

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
- [x] Privacy policy at `/privacy/` (server in Ashburn, US; covers GDPR basics). The app no longer writes access logs, so the policy can say IP addresses aren't logged. Keep the policy in sync with what the code actually stores.
- [x] Terms of use at `/terms/`
- [x] Self-hosted Umami, no cookies, so no cookie banner is needed (dashboard via SSH tunnel, see "Where we left off")

### 5. Infrastructure
- [x] VPS setup: non-root `deploy` user, SSH keys only, `ufw` (22/80/443), Docker + compose plugin, swap file, `unattended-upgrades`
- [x] `Dockerfile` + `docker-compose.yml` + `caddy/Caddyfile`
- [x] GitHub Actions workflow: test → build → push to GHCR → deploy over SSH (`.github/workflows/deploy.yml`)
- [x] DNS A record → VPS, proxied through Cloudflare
- [x] Docker log rotation
- [x] Docker healthcheck using `/api/health`
- [x] Uptime monitor (UptimeRobot, keyword check on `/api/health`)

### Launch
- [ ] Post in r/3Dpen, 3D-pen Facebook groups, and short TikToks/Shorts showing photo → template → build

## Phase 2: Background removal in the browser

This removes ~90% of server load and lets the VPS shrink to ~€4–5/mo.

- [x] Run background removal on the user's device: onnxruntime-web 1.30 on **WebGPU** in a Web Worker (`frontend/src/lib/cutout.ts`, `cutout.worker.ts`), copying rembg's pre/post-processing exactly. ~250 ms per photo on an M1 Pro (server: 2–3 s).
- [x] **No WASM fallback** (decided 2026-10-09): on phones a 1024² ISNet on the CPU would take tens of seconds and ~1 GB, and fp16 runs poorly there. Browsers without WebGPU or `shader-f16`, with Data Saver on, or hitting any error or a 20 s timeout use the server instead.
- [x] Upload the photo **plus a separate grayscale mask** (the model's raw 1024×1024 output), not a transparent PNG: browsers blacken fully transparent pixels, which would spoil the preview's faded background. `/api/segment` takes an optional `mask`, stretches and thresholds it like rembg, skips the queue (still rate limited), and includes it in the cache key.
- [x] Keep server-side rembg as the fallback (unchanged)
- [x] Model: `isnet-general-use` (Apache-2.0) converted to **fp16 (90 MB)** with its 11 training-only outputs removed. Same masks as fp32 on 16 test photos. int8 (46 MB), silueta (44 MB), and u2netp (4.6 MB) were all clearly worse. Made by `backend/scripts/browser_model.py`, in its own Docker build stage, served at `/models/isnet-general-use-fp16-v1.onnx` (bump the version in the name and in `cutout.ts` if it changes). Browsers keep it in Cache Storage, saved only after it loads and runs.
- [x] Parity in Chrome (Apple GPU): 15/16 test photos give the same template as the server (sizes within 1 mm). The odd one out is a row of overlapping shoes, which neither path cuts out usefully.
- [x] The `upload` event in Umami now has `cutout` (`browser`/`server`) and `reason`. Privacy policy updated.
- [ ] Deploy, then add the **Cloudflare Cache Rule** for `/models/*` and `*.wasm` (Cloudflare doesn't cache those extensions by default; Caddy already sends `immutable` cache headers for `/assets/*` and `/models/*`)
- [ ] Test on real phones (iPhone Safari 26, Android Chrome) and check the browser/server split in Umami
- [ ] Downsize the VPS once most uploads are cut out in the browser

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
