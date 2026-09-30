import { renderToString } from "react-dom/server";
import { SITE } from "@/site";
import LandingRoot, { PAGES } from "./Root";

export const paths = Object.keys(PAGES);
export const site = SITE;

export function render(path: string): string {
  return renderToString(<LandingRoot path={path} />);
}
