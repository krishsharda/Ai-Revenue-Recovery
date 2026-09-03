/**
 * Guards `next dev` against a corrupted `.next` directory.
 *
 * `next build` and `next dev` write different chunk layouts into the same
 * `.next` folder. Running a build while (or after) a dev server owns that
 * folder leaves the dev server's manifest pointing at chunks the build has
 * replaced: `main-app.js`, `app-pages-internals.js` and `layout.css` all 404,
 * React never hydrates, and the app degrades to unstyled HTML with dead
 * buttons and a full page load on every link — which reads as "the site is
 * very slow" rather than as an obvious failure.
 *
 * A production build is identifiable by BUILD_ID, which `next dev` never
 * writes. If one is present, the directory is from a build and gets cleared
 * before the dev server starts.
 */
const fs = require("node:fs");
const path = require("node:path");

const distDir = path.join(__dirname, "..", ".next");
const buildIdPath = path.join(distDir, "BUILD_ID");

if (fs.existsSync(buildIdPath)) {
  fs.rmSync(distDir, { recursive: true, force: true });
  console.log("[dev] Cleared .next — it held a production build, which breaks dev chunk resolution.");
}
