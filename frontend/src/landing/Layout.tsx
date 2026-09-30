import type { ReactNode } from "react";
import { ArrowRight, PenTool } from "lucide-react";
import { ModeToggle } from "@/components/mode-toggle";
import { SupportButton } from "@/components/support";
import { Button } from "@/components/ui/button";
import { APP_PATH, PRIVACY_PATH, SITE, TERMS_PATH } from "@/site";

export function TryButton({
  size = "lg",
  className,
}: {
  size?: "lg" | "default";
  className?: string;
}) {
  return (
    <Button asChild size={size} className={className}>
      <a href={APP_PATH}>
        Try it free <ArrowRight />
      </a>
    </Button>
  );
}

/** Header and footer shared by the landing and legal pages. `nav` sits between the logo and the buttons. */
export function Layout({
  nav,
  children,
}: {
  nav?: ReactNode;
  children: ReactNode;
}) {
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
          {nav && (
            <nav className="ml-auto hidden items-center gap-1 text-sm sm:flex">
              {nav}
            </nav>
          )}
          <div
            className={
              nav
                ? "ml-auto flex items-center gap-2 sm:ml-2"
                : "ml-auto flex items-center gap-2"
            }
          >
            <SupportButton />
            <ModeToggle />
            <TryButton size="default" />
          </div>
        </div>
      </header>

      <main>{children}</main>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted-foreground sm:px-6">
          <span suppressHydrationWarning>
            © {new Date().getFullYear()} {SITE.name}
          </span>
          <div className="flex flex-wrap gap-x-4 gap-y-2">
            {SITE.donateUrl && (
              <a
                href={SITE.donateUrl}
                target="_blank"
                rel="noopener"
                data-umami-event="kofi"
                className="hover:text-foreground"
              >
                Support on Ko-fi
              </a>
            )}
            <a href={PRIVACY_PATH} className="hover:text-foreground">
              Privacy
            </a>
            <a href={TERMS_PATH} className="hover:text-foreground">
              Terms
            </a>
            <a href={APP_PATH} className="hover:text-foreground">
              Open the app
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
