import { renderToString } from "react-dom/server";
import LandingRoot from "./Root";

export function render(): string {
  return renderToString(<LandingRoot />);
}
