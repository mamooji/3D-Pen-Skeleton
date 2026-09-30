export type Paper = "a4" | "letter";

export interface Params {
  detail: number;
  ribs: number | null;
  rings: number | null;
  thickness: number;
  size_cm: number;
  paper: Paper;
  stack: boolean;
  features: boolean;
}

export const DEFAULT_PARAMS: Params = {
  detail: 3,
  ribs: null,
  rings: null,
  thickness: 1,
  size_cm: 15,
  paper: "a4",
  stack: true,
  features: false,
};

export interface Polyline3D {
  color: string;
  pts: [number, number, number][];
}

export interface TemplateResult {
  pages: string[];
  warnings: string[];
  info: {
    ribs: number;
    rings: number;
    pages: number;
    size_mm: [number, number];
    params: Params;
  };
  model: Polyline3D[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

// Used when the response has no message of its own (e.g. it came from Caddy, not the app).
const FALLBACK: Record<number, string> = {
  413: "That photo is too large. Try one under 25 MB.",
  429: "Too many requests. Please wait a minute and try again.",
  502: "The app is restarting. Please try again in a few seconds.",
  503: "The app is busy or restarting. Please try again in a few seconds.",
  504: "The app is busy or restarting. Please try again in a few seconds.",
};

async function check(res: Response): Promise<Response> {
  if (res.ok) return res;
  let msg =
    FALLBACK[res.status] ??
    "Something went wrong on our side. Please try again.";
  try {
    const body = await res.json();
    if (typeof body.detail === "string") msg = body.detail;
  } catch {
    /* not JSON */
  }
  throw new ApiError(msg, res.status);
}

async function request(input: string, init: RequestInit): Promise<Response> {
  try {
    return await check(await fetch(input, init));
  } catch (e) {
    // fetch only throws TypeError when the request never got a response.
    if (e instanceof TypeError)
      throw new ApiError(
        "Can't reach the server. Check your connection and try again.",
        0,
      );
    throw e;
  }
}

export async function segment(
  photo: Blob,
): Promise<{ image_id: string; preview: string }> {
  const form = new FormData();
  form.append("file", photo, "photo");
  return (await request("/api/segment", { method: "POST", body: form })).json();
}

function post(
  path: string,
  imageId: string,
  params: Params,
  signal?: AbortSignal,
) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_id: imageId, params }),
    signal,
  });
}

export async function template(
  imageId: string,
  params: Params,
  signal?: AbortSignal,
): Promise<TemplateResult> {
  return (await post("/api/template", imageId, params, signal)).json();
}

export async function exportPdf(
  imageId: string,
  params: Params,
): Promise<Blob> {
  return (await post("/api/export", imageId, params)).blob();
}
