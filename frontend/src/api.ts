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

async function check(res: Response): Promise<Response> {
  if (res.ok) return res;
  let msg = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body.detail === "string") msg = body.detail;
  } catch {
    /* not JSON */
  }
  throw new Error(msg);
}

export async function segment(file: File): Promise<{ image_id: string; preview: string }> {
  const form = new FormData();
  form.append("file", file);
  const res = await check(await fetch("/api/segment", { method: "POST", body: form }));
  return res.json();
}

function post(path: string, imageId: string, params: Params, signal?: AbortSignal) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_id: imageId, params }),
    signal,
  });
}

export async function template(imageId: string, params: Params, signal?: AbortSignal): Promise<TemplateResult> {
  return (await check(await post("/api/template", imageId, params, signal))).json();
}

export async function exportPdf(imageId: string, params: Params): Promise<Blob> {
  return (await check(await post("/api/export", imageId, params))).blob();
}
