// Node module hooks that load https: imports (the kit imports Three.js from a pinned CDN URL), cached on disk.
// Used by the kit tests only: node --import ./recipes/line3d/test/register.mjs --test recipes/line3d/test/
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { homedir } from "node:os";
import { join } from "node:path";

const CACHE = join(process.env.XDG_CACHE_HOME || join(homedir(), ".cache"), "motion-workshop", "https");

export async function resolve(spec, ctx, next) {
  if (spec.startsWith("https://")) return { url: spec, shortCircuit: true };
  if (ctx.parentURL?.startsWith("https://") && /^\.{0,2}\//.test(spec)) return { url: new URL(spec, ctx.parentURL).href, shortCircuit: true };
  return next(spec, ctx);
}

export async function load(url, ctx, next) {
  if (!url.startsWith("https://")) return next(url, ctx);
  const file = join(CACHE, createHash("sha256").update(url).digest("hex") + ".js");
  let source;
  try { source = await readFile(file, "utf8"); } catch {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`fetch ${url}: ${res.status}`);
    source = await res.text();
    await mkdir(CACHE, { recursive: true });
    await writeFile(file, source);
  }
  return { format: "module", source, shortCircuit: true };
}
