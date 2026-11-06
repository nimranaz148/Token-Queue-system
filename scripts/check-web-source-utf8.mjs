import { readdir, readFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";

const sourceRoot = resolve("apps/web/src");
const sourceExtensions = new Set([".ts", ".tsx", ".js", ".jsx", ".css", ".svg", ".json"]);
const decoder = new TextDecoder("utf-8", { fatal: true });
let checked = 0;
let failed = false;

async function inspect(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      await inspect(path);
    } else if (sourceExtensions.has(extname(path))) {
      checked += 1;
      try {
        decoder.decode(await readFile(path));
      } catch (error) {
        failed = true;
        console.error(`Invalid UTF-8 source: ${path} (${error.message})`);
      }
    }
  }
}

await inspect(sourceRoot);

if (failed) {
  process.exitCode = 1;
} else {
  console.log(`UTF-8 source check passed (${checked} files).`);
}
