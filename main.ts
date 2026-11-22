import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

// Entry program for "The agent builds a game from one prompt".
// The post itself is the entry: this program only copies POST.json
// (the X post address) into the output directory, as the kit requires.
// It first validates POST.json so a malformed placeholder fails loudly
// here instead of silently shipping an entry the gate will refuse.
//
// NOTE: the grader runs `node /bot/main.ts` from an arbitrary working
// directory, so POST.json must be resolved against this file's own
// directory, never against process.cwd().
const botDir = import.meta.dirname;
const postPath = join(botDir, "POST.json");
const post = JSON.parse(readFileSync(postPath, "utf8"));
if (
  typeof post !== "object" || post === null ||
  typeof post.url !== "string" ||
  !/^https:\/\/(www\.|mobile\.)?(x\.com|twitter\.com)\/[^/]+\/status\/\d+$/.test(post.url)
) {
  throw new Error("POST.json must hold {\"url\": \"https://x.com/<handle>/status/<id>\"}");
}
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "out";
mkdirSync(outDir, { recursive: true });
copyFileSync(postPath, join(outDir, "POST.json"));
