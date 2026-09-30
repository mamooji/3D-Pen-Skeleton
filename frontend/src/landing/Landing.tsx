import type { ReactNode } from "react";
import {
  ArrowRight,
  ChevronRight,
  ImageUp,
  ListOrdered,
  PenTool,
  Printer,
  Ruler,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { APP_PATH, SITE } from "@/site";

const PIPELINE = [
  { src: "/landing/duck-photo.svg", label: "Your photo", alt: "A side-view picture of a rubber duck" },
  { src: "/landing/duck-template.svg", label: "Printable template", alt: "A printed page of numbered, colored rib and ring outlines" },
  { src: "/landing/duck-frame.svg", label: "Your 3D frame", alt: "The ribs and rings assembled into a 3D duck frame" },
];

const STEPS = [
  {
    icon: ImageUp,
    title: "Upload a photo",
    text: "A side view of one object on a plain background works best. The app cuts it out and builds a 3D shape from its outline.",
  },
  {
    icon: Printer,
    title: "Print the template",
    text: "Pick the size and detail, then download a PDF of numbered ribs and lettered rings. Print it at 100% on A4 or Letter.",
  },
  {
    icon: PenTool,
    title: "Trace and assemble",
    text: "Trace every piece with your 3D pen, peel them off, and stand the ribs up on the outline at their numbered lines.",
  },
];

const FEATURES = [
  { icon: Sparkles, title: "Free, no sign-up", text: "Open the app and start. No account, no watermark." },
  { icon: SlidersHorizontal, title: "Adjustable detail", text: "From a quick 3-rib sketch to a detailed 11-rib frame." },
  { icon: ListOrdered, title: "Numbered and color-coded", text: "Every rib and ring is labeled, with ticks where pieces cross." },
  { icon: Ruler, title: "Real-size printing", text: "Set the size in centimeters. A 50 mm scale bar confirms the print." },
  { icon: ShieldCheck, title: "Your photos stay private", text: "Used only to make your template, then deleted automatically." },
];

// Photos of finished builds, in public/landing/gallery/. The section stays hidden until there's at least one.
const GALLERY: { src: string; alt: string; caption: string }[] = [];

const FAQ: { q: string; a: ReactNode }[] = [
  {
    q: "What kind of photo works best?",
    a: "A side view of a single object on a plain background, with the whole object in the frame. The photo's outline becomes the profile everything else is built from. Cut-outs with a transparent background work too.",
  },
  {
    q: "What do I need?",
    a: "A 3D pen, a printer, and plain paper. Print the PDF at 100% scale (not “fit to page”) and check the 50 mm scale bar with a ruler.",
  },
  {
    q: "How do I put it together?",
    a: "Trace every piece on the printout, peel them off, and stand each numbered rib up on the profile at its matching numbered line. Lettered rings wrap around the ribs, and small ticks show exactly where pieces cross.",
  },
  {
    q: "Is it really free?",
    a: "Yes. There's no account, no watermark, and no limit on downloads.",
  },
  {
    q: "How big will my model be?",
    a: "You choose the size in centimeters before downloading. If a piece won't fit on the page, the app tells you the largest size that does.",
  },
  {
    q: "Can I make it simpler or more detailed?",
    a: "Yes. The Detail slider sets how many ribs and rings you get and how smooth the curves are. Advanced settings let you choose the exact counts, and Thickness makes the shape flatter or rounder.",
  },
  {
    q: "What happens to my photo?",
    a: "It's used only to find the object and build your template. It's kept while you're working on it and deleted automatically a few hours later. It's never shared.",
  },
  {
    q: "Why doesn't my model look quite right?",
    a: "Depth is estimated from the outline, and the object is assumed to be the same front and back. Parts that overlap in the photo, like an arm in front of a body, merge into one shape. Try a clearer side view, or use Thickness if the object is flatter or rounder than it looks.",
  },
];

function TryButton({ size = "lg", className }: { size?: "lg" | "default"; className?: string }) {
  return (
    <Button asChild size={size} className={className}>
      <a href={APP_PATH}>
        Try it free <ArrowRight />
      </a>
    </Button>
  );
}

function Section({ id, title, lead, children }: { id: string; title: string; lead?: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-20 py-16 sm:py-20">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <h2 className="font-heading text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h2>
          {lead && <p className="mt-3 text-muted-foreground">{lead}</p>}
        </div>
        {children}
      </div>
    </section>
  );
}

export default function Landing() {
  return (
    <div className="min-h-svh bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:px-6">
          <a href="/" className="flex items-center gap-2.5">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <PenTool className="size-5" />
            </span>
            <span className="font-heading font-semibold">{SITE.name}</span>
          </a>
          <nav className="ml-auto hidden items-center gap-1 text-sm sm:flex">
            <Button asChild variant="ghost" size="sm">
              <a href="#how">How it works</a>
            </Button>
            <Button asChild variant="ghost" size="sm">
              <a href="#faq">FAQ</a>
            </Button>
          </nav>
          <div className="ml-auto flex items-center gap-2 sm:ml-2">
            <ModeToggle />
            <TryButton size="default" />
          </div>
        </div>
      </header>

      <main>
        <section className="border-b bg-muted/40">
          <div className="mx-auto max-w-6xl px-4 pt-14 pb-16 sm:px-6 sm:pt-20">
            <div className="mx-auto max-w-3xl text-center">
              <h1 className="font-heading text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
                {SITE.headline}
              </h1>
              <p className="mt-5 text-lg text-balance text-muted-foreground">
                Upload a picture of an object and get printable ribs and rings to trace with your 3D pen. Put them
                together and you have a 3D frame of it.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <TryButton className="h-11 px-6 text-base" />
                <Button asChild variant="outline" size="lg" className="h-11 px-6 text-base">
                  <a href="#how">See how it works</a>
                </Button>
              </div>
              <p className="mt-4 text-sm text-muted-foreground">Free. No sign-up. Works on any device.</p>
            </div>

            <ol className="mt-14 grid items-center gap-4 sm:grid-cols-[1fr_auto_1fr_auto_1fr]">
              {PIPELINE.map((p, i) => (
                <PipelineStep key={p.src} {...p} last={i === PIPELINE.length - 1} n={i + 1} />
              ))}
            </ol>
          </div>
        </section>

        <Section id="how" title="How it works" lead="Three steps from a photo on your phone to a frame on your desk.">
          <ol className="grid gap-4 md:grid-cols-3">
            {STEPS.map(({ icon: Icon, title, text }, i) => (
              <li key={title}>
                <Card className="h-full">
                  <CardHeader>
                    <div className="mb-2 flex items-center gap-3">
                      <span className="flex size-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                        <Icon className="size-5" />
                      </span>
                      <span className="text-sm font-medium text-muted-foreground">Step {i + 1}</span>
                    </div>
                    <CardTitle className="text-lg">{title}</CardTitle>
                    <CardDescription className="leading-relaxed">{text}</CardDescription>
                  </CardHeader>
                </Card>
              </li>
            ))}
          </ol>

          <ul className="mt-12 grid gap-x-8 gap-y-6 sm:grid-cols-2 lg:grid-cols-5">
            {FEATURES.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex gap-3 lg:flex-col">
                <Icon className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
                <div>
                  <p className="font-medium">{title}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{text}</p>
                </div>
              </li>
            ))}
          </ul>
        </Section>

        {GALLERY.length > 0 && (
          <div className="border-t bg-muted/40">
            <Section id="examples" title="Made with it" lead="Frames people have built from their own photos.">
              <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {GALLERY.map((g) => (
                  <li key={g.src}>
                    <figure className="overflow-hidden rounded-xl border bg-card">
                      <img src={g.src} alt={g.alt} loading="lazy" className="aspect-[4/3] w-full object-cover" />
                      <figcaption className="px-4 py-3 text-sm text-muted-foreground">{g.caption}</figcaption>
                    </figure>
                  </li>
                ))}
              </ul>
            </Section>
          </div>
        )}

        <div className="border-t">
          <Section id="faq" title="Questions">
            <Card className="mx-auto max-w-3xl py-2">
              <CardContent>
                <Accordion type="single" collapsible>
                  {FAQ.map(({ q, a }) => (
                    <AccordionItem key={q} value={q}>
                      <AccordionTrigger className="text-base">{q}</AccordionTrigger>
                      {/* forceMount keeps answers in the pre-rendered HTML for search engines; closed ones are hidden. */}
                      <AccordionContent forceMount className="leading-relaxed text-muted-foreground">
                        {a}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          </Section>
        </div>

        <section className="border-t bg-primary text-primary-foreground">
          <div className="mx-auto flex max-w-6xl flex-col items-center gap-5 px-4 py-16 text-center sm:px-6">
            <h2 className="font-heading text-2xl font-semibold tracking-tight sm:text-3xl">Got a 3D pen? Pick a photo.</h2>
            <p className="max-w-xl opacity-80">Your first template takes about a minute.</p>
            <Button asChild size="lg" variant="secondary" className="h-11 px-6 text-base">
              <a href={APP_PATH}>
                Try it free <ArrowRight />
              </a>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted-foreground sm:px-6">
          <span suppressHydrationWarning>© {new Date().getFullYear()} {SITE.name}</span>
          <a href={APP_PATH} className="hover:text-foreground">
            Open the app
          </a>
        </div>
      </footer>
    </div>
  );
}

function PipelineStep({ src, label, alt, n, last }: (typeof PIPELINE)[number] & { n: number; last: boolean }) {
  return (
    <>
      <li>
        <figure className="overflow-hidden rounded-xl border bg-card shadow-sm">
          {/* Always on white: these are paper and photo, not UI. */}
          <div className="flex aspect-[4/3] items-center justify-center bg-white p-3">
            <img src={src} alt={alt} width={400} height={300} className="size-full object-contain" />
          </div>
          <figcaption className="flex items-center gap-2 border-t px-4 py-2.5 text-sm font-medium">
            <span className="flex size-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
              {n}
            </span>
            {label}
          </figcaption>
        </figure>
      </li>
      {!last && (
        <li aria-hidden className="flex justify-center text-muted-foreground">
          <ChevronRight className="size-6 rotate-90 sm:rotate-0" />
        </li>
      )}
    </>
  );
}
