import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const vite = await createServer({
  appType: "custom",
  configFile: false,
  root,
  resolve: { alias: { "@": root } },
  server: { middlewareMode: true },
});

after(async () => {
  await vite.close();
});

async function readCssTree(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const contents = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        return readCssTree(entryPath);
      }
      return entry.name.endsWith(".css") ? readFile(entryPath, "utf8") : "";
    }),
  );
  return contents.join("\n");
}

test("emits the ProofDesk theme and working-surface styles", async () => {
  const css = await readCssTree(path.join(root, "dist"));

  assert.match(css, /--primary:#6ef0b4/);
  assert.match(css, /--background:#06100e/);
  assert.match(css, /\.surface-panel/);
  assert.match(css, /\.criterion-row/);
  assert.match(css, /\.notice-bar/);
});

test("forwards progress semantics to the primitive", async () => {
  const { Progress } = await vite.ssrLoadModule("/components/ui/progress.tsx");
  const html = renderToStaticMarkup(React.createElement(Progress, { value: 37 }));

  assert.match(html, /aria-valuenow="37"/);
  assert.match(html, /aria-valuetext="37%"/);
  assert.match(html, /data-state="loading"/);
});

test("renders the used badge primitive with its semantic label", async () => {
  const { Badge } = await vite.ssrLoadModule("/components/ui/badge.tsx");
  const html = renderToStaticMarkup(
    React.createElement(Badge, { variant: "outline" }, "Awaiting human review"),
  );

  assert.match(html, /Awaiting human review/);
  assert.match(html, /data-variant="outline"/);
});
