// Background removal in the browser: isnet-general-use (fp16) on WebGPU. It mirrors rembg's DisSession, which the
// server runs, so both paths give the same cut-out. See cutout.ts for when it's used.
import * as ort from "onnxruntime-web/webgpu";

import type { WorkerReply, WorkerRequest } from "./cutout";

// The model's fixed input size.
const SIZE = 1024;
const CACHE = "trace3dpen-models";

ort.env.wasm.numThreads = 1; // threads need cross-origin isolation, and the GPU does the work anyway
ort.env.logLevel = "error";

const ctx = self as unknown as {
  onmessage: ((e: MessageEvent<WorkerRequest>) => void) | null;
  postMessage(msg: WorkerReply): void;
};
const reply = (msg: WorkerReply) => ctx.postMessage(msg);

type GPU = {
  requestAdapter(): Promise<{ features: { has(f: string): boolean } } | null>;
};

let session: ort.InferenceSession | null = null;

ctx.onmessage = (e) => {
  const msg = e.data;
  if (msg.type === "init") void init(msg.modelUrl);
  else void cutout(msg.id, msg.image);
};

async function init(modelUrl: string) {
  try {
    const gpu = (navigator as Navigator & { gpu?: GPU }).gpu;
    const adapter = await gpu?.requestAdapter();
    if (!adapter) return reply({ type: "unavailable", reason: "no-webgpu" });
    if (!adapter.features.has("shader-f16"))
      return reply({ type: "unavailable", reason: "no-f16" });

    // No cache in some private windows and on plain-http pages: then it downloads every visit.
    const cache =
      "caches" in self ? await caches.open(CACHE).catch(() => null) : null;
    const cached = await cache?.match(modelUrl).catch(() => undefined);
    const model = cached
      ? new Uint8Array(await cached.arrayBuffer())
      : await download(modelUrl);
    try {
      session = await ort.InferenceSession.create(model, {
        executionProviders: ["webgpu"],
        graphOptimizationLevel: "all",
      });
      // The first run compiles the GPU shaders, so do it now rather than when someone is waiting for a photo.
      const t = performance.now();
      await run(new Float32Array(3 * SIZE * SIZE));
      reply({ type: "ready", warmupMs: Math.round(performance.now() - t) });
    } catch (err) {
      // A bad copy in the cache (e.g. from an interrupted download) would fail every visit: download it again next time.
      if (cached) await cache?.delete(modelUrl).catch(() => {});
      throw err;
    }
    // Keep only a model that loaded and ran.
    if (cache && !cached) await keep(cache, modelUrl, model);
  } catch (err) {
    session = null;
    reply({ type: "unavailable", reason: `error: ${String(err)}` });
  }
}

async function download(url: string): Promise<Uint8Array<ArrayBuffer>> {
  const res = await fetch(url);
  if (!res.ok || !res.body)
    throw new Error(`model download: HTTP ${res.status}`);
  // 0 when unknown (e.g. compressed in transit).
  const total = Number(res.headers.get("Content-Length")) || 0;
  const chunks: Uint8Array[] = [];
  let loaded = 0;
  const reader = res.body.getReader();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.length;
    reply({ type: "progress", loaded, total });
  }
  const model = new Uint8Array(loaded);
  let offset = 0;
  for (const c of chunks) {
    model.set(c, offset);
    offset += c.length;
  }
  return model;
}

/** Save the model for next time, replacing older versions. */
async function keep(cache: Cache, url: string, model: Uint8Array<ArrayBuffer>) {
  try {
    for (const key of await cache.keys())
      if (key.url !== new URL(url, location.href).href) await cache.delete(key);
    await cache.put(url, new Response(model));
  } catch {
    // e.g. out of storage: it downloads again next time
  }
}

async function run(input: Float32Array): Promise<Float32Array> {
  if (!session) throw new Error("model not loaded");
  const feeds = {
    [session.inputNames[0]]: new ort.Tensor("float32", input, [
      1,
      3,
      SIZE,
      SIZE,
    ]),
  };
  const out = await session.run(feeds, [session.outputNames[0]]);
  const pred = out[session.outputNames[0]];
  const data = (await pred.getData()) as Float32Array;
  pred.dispose();
  return data;
}

async function cutout(id: number, image: ImageBitmap) {
  try {
    const canvas = new OffscreenCanvas(SIZE, SIZE);
    const g = canvas.getContext("2d", { willReadFrequently: true });
    if (!g) throw new Error("no 2d canvas");
    g.imageSmoothingQuality = "high";
    // Stretched to a square, as rembg does.
    g.drawImage(image, 0, 0, SIZE, SIZE);
    image.close();
    const px = g.getImageData(0, 0, SIZE, SIZE).data;

    // A photo that's already a cut-out keeps its own transparency (the server checks the same way).
    let transparent = 0;
    for (let i = 3; i < px.length; i += 4) if (px[i] < 128) transparent++;
    const frac = transparent / (SIZE * SIZE);
    if (frac > 0.01 && frac < 0.99)
      return reply({ type: "skip", id, reason: "has-cutout" });

    // rembg: divide by the brightest channel value, subtract 0.5, channels first.
    let max = 0;
    for (let i = 0; i < px.length; i += 4)
      max = Math.max(max, px[i], px[i + 1], px[i + 2]);
    const scale = 1 / Math.max(max, 1e-6);
    const n = SIZE * SIZE;
    const input = new Float32Array(3 * n);
    for (let p = 0, i = 0; p < n; p++, i += 4) {
      input[p] = px[i] * scale - 0.5;
      input[n + p] = px[i + 1] * scale - 0.5;
      input[2 * n + p] = px[i + 2] * scale - 0.5;
    }

    const t = performance.now();
    const pred = await run(input);
    const ms = Math.round(performance.now() - t);

    // rembg: stretch to 0..1, then to 0..255 (truncating). The server resizes it to the photo and thresholds it.
    let lo = Infinity;
    let hi = -Infinity;
    for (const v of pred) {
      if (v < lo) lo = v;
      if (v > hi) hi = v;
    }
    const range = hi - lo || 1;
    const out = new ImageData(SIZE, SIZE);
    for (let p = 0, i = 0; p < n; p++, i += 4) {
      const v = Math.trunc(((pred[p] - lo) / range) * 255);
      out.data[i] = out.data[i + 1] = out.data[i + 2] = v;
      out.data[i + 3] = 255;
    }
    g.putImageData(out, 0, 0);
    const mask = await canvas.convertToBlob({ type: "image/png" });
    reply({ type: "mask", id, mask, ms });
  } catch (err) {
    reply({ type: "error", id, reason: String(err) });
  }
}
