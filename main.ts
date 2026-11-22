import { copyFileSync, mkdirSync, readFileSync } from "node:fs";

// Entry program for "The agent builds a game from one prompt".
// The post itself is the entry: this program only copies POST.json
// (the X post address) into the output directory, as the kit requires.
// It first validates POST.json so a malformed placeholder fails loudly
// here instead of silently shipping an entry the gate will refuse.
const post = JSON.parse(readFileSync("POST.json", "utf8"));
if (
  typeof post !== "object" || post === null ||
  typeof post.url !== "string" ||
  !/^https:\/\/(www\.|mobile\.)?(x\.com|twitter\.com)\/[^/]+\/status\/\d+$/.test(post.url)
) {
  throw new Error("POST.json must hold {\"url\": \"https://x.com/<handle>/status/<id>\"}");
}
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "out";
mkdirSync(outDir, { recursive: true });
copyFileSync("POST.json", `${outDir}/POST.json`);
