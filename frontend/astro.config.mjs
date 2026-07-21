import { defineConfig } from "astro/config";

// Fully static output. The build fetches content from the backend RPC API
// (VITE_API_URL) and renders every page — da at the root, /en/ and /de/
// path-prefixed — so the deployed site is plain HTML on S3/CloudFront.
export default defineConfig({
  site: "https://www.aalumvej26.dk",
  trailingSlash: "always",
  build: {
    format: "directory",
  },
});
