// Background removal in the browser, so the server doesn't have to do it. The model downloads in the background
// when the tool opens (once; the browser keeps it). When it's ready, photos are cut out here; otherwise, or if
// anything goes wrong, the server does it as before.

// Bump the version when the model file changes, so browsers fetch the new one.
export const MODEL_URL = "/models/isnet-general-use-fp16-v1.onnx";
// The longest a cut-out may take here before the server is asked instead.
const RUN_TIMEOUT_MS = 20_000;
// A photo picked while the model is still loading waits for it only if it should be ready this soon.
const MAX_WAIT_MS = 8_000;

export type WorkerRequest =
  | { type: "init"; modelUrl: string }
  | { type: "run"; id: number; image: ImageBitmap };

export type WorkerReply =
  | { type: "progress"; loaded: number; total: number }
  | { type: "ready"; warmupMs: number }
  | { type: "unavailable"; reason: string }
  | { type: "mask"; id: number; mask: Blob; ms: number }
  | { type: "skip"; id: number; reason: string }
  | { type: "error"; id: number; reason: string };

/** mask is null when the server should cut the photo out; reason says why (or how long it took here). */
export interface Cutout {
  mask: Blob | null;
  where: "browser" | "server";
  reason: string;
}

let worker: Worker | null = null;
let state: "idle" | "loading" | "ready" | "unavailable" = "idle";
let unavailableReason = "";
const download = { loaded: 0, total: 0, startedAt: 0 };
let readyWaiters: (() => void)[] = [];
const pending = new Map<number, (reply: WorkerReply) => void>();
let nextId = 1;

/** Start loading the model in the background if this device can run it. Safe to call more than once. */
export function startCutoutModel() {
  if (state !== "idle") return;
  if (!("gpu" in navigator)) return giveUp("no-webgpu");
  const conn = (
    navigator as Navigator & { connection?: { saveData?: boolean } }
  ).connection;
  if (conn?.saveData) return giveUp("save-data");

  state = "loading";
  download.startedAt = performance.now();
  worker = new Worker(new URL("./cutout.worker.ts", import.meta.url), {
    type: "module",
  });
  worker.onmessage = (e: MessageEvent<WorkerReply>) => onReply(e.data);
  worker.onerror = () => giveUp("worker-error");
  post({ type: "init", modelUrl: MODEL_URL });
}

/** Cut the photo out here, or say why the server should do it. */
export async function cutOut(
  photo: Blob,
  onWait?: () => void, // called if the photo has to wait for the model to finish loading
): Promise<Cutout> {
  if (state === "loading" && readySoon()) {
    onWait?.();
    await untilReady(MAX_WAIT_MS);
  }
  if (state !== "ready")
    return server(state === "loading" ? "model-loading" : unavailableReason);

  let image: ImageBitmap;
  try {
    image = await createImageBitmap(photo, { imageOrientation: "from-image" });
  } catch {
    return server("decode"); // e.g. HEIC in some browsers; the server can read it
  }
  const id = nextId++;
  const reply = await new Promise<WorkerReply>((resolve) => {
    const timer = setTimeout(() => {
      pending.delete(id);
      resolve({ type: "error", id, reason: "timeout" });
    }, RUN_TIMEOUT_MS);
    pending.set(id, (r) => {
      clearTimeout(timer);
      resolve(r);
    });
    post({ type: "run", id, image }, [image]);
  });

  if (reply.type === "mask")
    return { mask: reply.mask, where: "browser", reason: `${reply.ms}ms` };
  if (reply.type === "skip") return server(reply.reason);
  // It failed or took too long: don't try again until the page is reloaded.
  const reason = reply.type === "error" ? reply.reason : "unexpected";
  giveUp(reason);
  return server(reason);
}

function server(reason: string): Cutout {
  return { mask: null, where: "server", reason };
}

function post(msg: WorkerRequest, transfer: Transferable[] = []) {
  worker?.postMessage(msg, transfer);
}

function onReply(msg: WorkerReply) {
  switch (msg.type) {
    case "progress":
      download.loaded = msg.loaded;
      download.total = msg.total;
      break;
    case "ready":
      state = "ready";
      wakeWaiters();
      break;
    case "unavailable":
      giveUp(msg.reason);
      break;
    default:
      pending.get(msg.id)?.(msg);
      pending.delete(msg.id);
  }
}

function giveUp(reason: string) {
  state = "unavailable";
  unavailableReason = reason;
  worker?.terminate();
  worker = null;
  for (const resolve of pending.values())
    resolve({ type: "error", id: 0, reason });
  pending.clear();
  wakeWaiters();
}

/** Whether the download should finish within MAX_WAIT_MS at its speed so far. */
function readySoon() {
  const { loaded, total, startedAt } = download;
  if (!loaded || !total) return false;
  if (loaded >= total) return true; // downloaded, now starting up
  const perMs = loaded / (performance.now() - startedAt);
  return (total - loaded) / perMs < MAX_WAIT_MS;
}

function untilReady(ms: number): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    readyWaiters.push(() => {
      clearTimeout(timer);
      resolve();
    });
  });
}

function wakeWaiters() {
  for (const wake of readyWaiters) wake();
  readyWaiters = [];
}
