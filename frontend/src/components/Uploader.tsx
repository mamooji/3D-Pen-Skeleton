import { useRef, useState } from "react";
import { ImageUp, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  onFile: (file: File) => void;
  busy: boolean;
  cutout: string | null;
}

export default function Uploader({ onFile, busy, cutout }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  function pick(files: FileList | null) {
    const f = files?.[0];
    if (f && f.type.startsWith("image/")) onFile(f);
  }

  const browse = () => !busy && input.current?.click();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Photo</CardTitle>
        <CardDescription>A side view of one object works best.</CardDescription>
      </CardHeader>
      <CardContent>
        <input
          ref={input}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => {
            pick(e.target.files);
            e.target.value = "";
          }}
        />
        <div
          role="button"
          tabIndex={0}
          aria-label="Upload a photo"
          onClick={browse}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && browse()}
          onDragOver={(e) => {
            e.preventDefault();
            setOver(true);
          }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setOver(false);
            if (!busy) pick(e.dataTransfer.files);
          }}
          className={cn(
            "flex min-h-40 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-4 text-center transition-colors outline-none",
            "hover:border-primary/50 hover:bg-muted/50 focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
            over && "border-primary bg-muted",
            busy && "cursor-wait opacity-70",
          )}
        >
          {cutout ? (
            <img src={cutout} alt="Detected object outline" className="max-h-64 rounded-md" />
          ) : (
            <div className="flex size-12 items-center justify-center rounded-full bg-muted">
              {busy ? <Loader2 className="size-6 animate-spin text-muted-foreground" /> : <ImageUp className="size-6 text-muted-foreground" />}
            </div>
          )}
          <div className="flex flex-col items-center gap-2">
            {!cutout && <p className="text-sm text-muted-foreground">Drop a photo here, or</p>}
            <Button
              type="button"
              variant={cutout ? "outline" : "default"}
              size="sm"
              disabled={busy}
              onClick={(e) => {
                e.stopPropagation();
                browse();
              }}
            >
              {busy ? <Loader2 className="animate-spin" /> : <ImageUp />}
              {busy ? "Processing…" : cutout ? "Use another photo" : "Choose photo"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
