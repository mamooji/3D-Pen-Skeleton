import { lazy, Suspense, useEffect, useState } from "react";
import { AlertCircle, Box, Download, FileText, Loader2, PenTool, TriangleAlert } from "lucide-react";
import { DEFAULT_PARAMS, exportPdf, segment, template, type Params, type TemplateResult } from "./api";
import Uploader from "./components/Uploader";
import Controls from "./components/Controls";
import TemplatePreview from "./components/TemplatePreview";
import { ModeToggle } from "@/components/mode-toggle";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// three.js is large; only load it when the 3D tab is opened.
const Viewer3D = lazy(() => import("./components/Viewer3D"));

export default function App() {
  const [imageId, setImageId] = useState<string | null>(null);
  const [cutout, setCutout] = useState<string | null>(null);
  const [params, setParams] = useState<Params>(DEFAULT_PARAMS);
  const [result, setResult] = useState<TemplateResult | null>(null);
  const [segmenting, setSegmenting] = useState(false);
  const [building, setBuilding] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onFile(file: File) {
    setError(null);
    setSegmenting(true);
    try {
      const r = await segment(file);
      setImageId(r.image_id);
      setCutout(r.preview);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSegmenting(false);
    }
  }

  // Rebuild the template shortly after the user stops moving a slider.
  useEffect(() => {
    if (!imageId) return;
    const ctrl = new AbortController();
    const timer = setTimeout(async () => {
      setBuilding(true);
      try {
        setResult(await template(imageId, params, ctrl.signal));
        setError(null);
      } catch (e) {
        if ((e as Error).name !== "AbortError") setError((e as Error).message);
      } finally {
        if (!ctrl.signal.aborted) setBuilding(false);
      }
    }, 250);
    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  }, [imageId, params]);

  async function onDownload() {
    if (!imageId) return;
    setDownloading(true);
    try {
      const blob = await exportPdf(imageId, params);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "skeleton-template.pdf";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 10_000);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="min-h-svh bg-muted/40">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <PenTool className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-heading text-base leading-tight font-semibold">3D Pen Skeleton</h1>
            <p className="truncate text-sm text-muted-foreground">
              Turn a photo into traceable pieces for a 3D-pen frame.
            </p>
          </div>
          <ModeToggle />
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl items-start gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[340px_1fr]">
        <aside className="flex flex-col gap-4 lg:sticky lg:top-24">
          <Uploader onFile={onFile} busy={segmenting} cutout={cutout} />
          {imageId && (
            <>
              <Controls params={params} resolved={result?.info.params} onChange={setParams} />
              <Button size="lg" className="h-11 w-full text-base" onClick={onDownload} disabled={downloading || !result}>
                {downloading ? <Loader2 className="animate-spin" /> : <Download />}
                {downloading ? "Preparing PDF…" : "Download PDF"}
              </Button>
              {result && (
                <div className="flex flex-wrap justify-center gap-1.5">
                  <Badge variant="secondary">{result.info.ribs} ribs</Badge>
                  <Badge variant="secondary">{result.info.rings} rings</Badge>
                  <Badge variant="secondary">
                    {result.info.pages} page{result.info.pages === 1 ? "" : "s"}
                  </Badge>
                  <Badge variant="outline">
                    {(result.info.size_mm[0] / 10).toFixed(1)} × {(result.info.size_mm[1] / 10).toFixed(1)} cm
                  </Badge>
                </div>
              )}
            </>
          )}
        </aside>

        <main className="flex min-w-0 flex-col gap-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle />
              <AlertTitle>Something went wrong</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {result?.warnings.map((w) => (
            <Alert key={w} className="border-amber-500/40 text-amber-700 dark:text-amber-400">
              <TriangleAlert />
              <AlertTitle>Heads up</AlertTitle>
              <AlertDescription className="text-amber-700/90 dark:text-amber-400/90">{w}</AlertDescription>
            </Alert>
          ))}

          {!imageId && !segmenting && <HowItWorks />}
          {segmenting && <Processing />}

          {result && (
            <Tabs defaultValue="pages" className="gap-4">
              <div className="flex items-center gap-3">
                <TabsList>
                  <TabsTrigger value="pages">
                    <FileText /> Print pages
                  </TabsTrigger>
                  <TabsTrigger value="3d">
                    <Box /> 3D preview
                  </TabsTrigger>
                </TabsList>
                {building && (
                  <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <Loader2 className="size-4 animate-spin" /> Updating…
                  </span>
                )}
              </div>
              <TabsContent value="pages">
                <TemplatePreview pages={result.pages} />
              </TabsContent>
              <TabsContent value="3d">
                <Suspense fallback={<Skeleton className="h-[min(70vh,640px)] w-full rounded-xl" />}>
                  <Viewer3D model={result.model} />
                </Suspense>
              </TabsContent>
            </Tabs>
          )}
        </main>
      </div>
    </div>
  );
}

const STEPS = [
  <>Upload a <strong className="text-foreground">side-view</strong> photo of one object, ideally on a plain background.</>,
  <>The app cuts out the object and uses its outline as the <strong className="text-foreground">profile</strong>.</>,
  <>It rounds the outline into a 3D shape and slices it into numbered <strong className="text-foreground">ribs</strong> (front view) and lettered <strong className="text-foreground">rings</strong> (top view).</>,
  <>Print the PDF at 100%, trace every piece with your 3D pen, then stand the ribs up on the profile at their numbered lines. Small ticks show where pieces meet.</>,
];

function HowItWorks() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">How it works</CardTitle>
        <CardDescription>Upload a photo to get started.</CardDescription>
      </CardHeader>
      <CardContent>
        <ol className="flex flex-col gap-4">
          {STEPS.map((step, i) => (
            <li key={i} className="flex gap-3 text-sm text-muted-foreground">
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                {i + 1}
              </span>
              <span className="pt-0.5 leading-relaxed">{step}</span>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

function Processing() {
  return (
    <div className="flex flex-col gap-4">
      <p className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Finding the object… (the first upload also downloads the cut-out model)
      </p>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-5">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="aspect-[210/297] w-full rounded-sm" />
        ))}
      </div>
    </div>
  );
}
