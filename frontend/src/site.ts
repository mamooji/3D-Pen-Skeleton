// Product name and copy, shared by the landing page, the tool, each page's <head> (vite.config.ts), and the
// link-preview image (backend/scripts/landing_assets.py: rerun it after changing name or headline).
export const SITE = {
  name: "3D Pen Skeleton",
  headline: "Turn any photo into a 3D-pen template",
  title: "3D Pen Skeleton: turn any photo into a 3D-pen template",
  description:
    "Upload a photo of an object and get a free printable template of numbered ribs and rings. Trace them with your 3D pen and assemble a 3D frame.",
  // Ko-fi page (https://ko-fi.com/...). The Support buttons and post-download prompt stay hidden while this is empty.
  donateUrl: "https://ko-fi.com/mamooji",
  // Who runs the site, how to reach them, and whose laws apply, for the privacy policy and terms.
  // The build fails while any of these is empty (scripts/prerender.mjs).
  operator: "Muhammad Mamooji",
  contactEmail: "mamoojim@hotmail.com",
  governingLaw: "Ontario, Canada",
  // Umami website ID (from the Umami dashboard). The tracker is added to production builds only while this is set.
  umamiWebsiteId: "5fc1c876-9cb8-409a-98d9-8b5c6e4b2fe8",
};

export const APP_PATH = "/app/";
export const PRIVACY_PATH = "/privacy/";
export const TERMS_PATH = "/terms/";
