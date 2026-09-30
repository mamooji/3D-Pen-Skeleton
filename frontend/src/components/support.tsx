import { Coffee, X } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { SITE } from "@/site";

const HIDE_KEY = "skeleton3d-support-hidden-until";
const HIDE_DAYS = 30;

/** Link to the donation page. Renders nothing until SITE.donateUrl is set. */
export function SupportButton() {
  if (!SITE.donateUrl) return null;
  return (
    <Button
      asChild
      variant="outline"
      aria-label="Support this project on Ko-fi"
    >
      <a
        href={SITE.donateUrl}
        target="_blank"
        rel="noopener"
        data-umami-event="kofi"
      >
        <Coffee />
        <span className="hidden sm:inline">Support</span>
      </a>
    </Button>
  );
}

/** Whether to show the post-download thank-you, i.e. it hasn't been dismissed recently. */
export function supportPromptWanted(): boolean {
  if (!SITE.donateUrl) return false;
  try {
    return Date.now() > Number(localStorage.getItem(HIDE_KEY) ?? 0);
  } catch {
    return true;
  }
}

function hideForAWhile() {
  try {
    localStorage.setItem(HIDE_KEY, String(Date.now() + HIDE_DAYS * 86_400_000));
  } catch {
    /* storage blocked: it'll just show again next time */
  }
}

/** Shown after a PDF download. Either choice hides it for HIDE_DAYS. */
export function SupportPrompt({ onClose }: { onClose: () => void }) {
  const close = () => {
    hideForAWhile();
    onClose();
  };
  return (
    <Alert className="relative pr-12">
      <Coffee />
      <AlertTitle>Your template is downloading. Enjoy the build!</AlertTitle>
      <AlertDescription>
        <p>
          {SITE.name} is free, with no ads or sign-up. If it saved you some
          time, a small tip on Ko-fi helps keep it running.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button asChild size="sm">
            <a
              href={SITE.donateUrl}
              target="_blank"
              rel="noopener"
              data-umami-event="kofi"
              onClick={close}
            >
              <Coffee /> Buy me a coffee
            </a>
          </Button>
          <Button size="sm" variant="ghost" onClick={close}>
            No thanks
          </Button>
        </div>
      </AlertDescription>
      <Button
        size="icon"
        variant="ghost"
        className="absolute top-2 right-2 size-7"
        aria-label="Close"
        onClick={onClose}
      >
        <X />
      </Button>
    </Alert>
  );
}
