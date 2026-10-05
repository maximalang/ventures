// Surgical move: 18 target lines from dependencies block to devDependencies block, LF preserved.
import { readFileSync, writeFileSync } from "node:fs";
const p = process.argv[2];
const raw = readFileSync(p, "utf8");
if (raw.includes("\r")) { console.error("CRLF detected - abort"); process.exit(2); }
const targets = new Set(["babel-jest","braces","create-jest","expect","jest-circus","jest-cli","jest-config","jest-environment-jsdom","jest-environment-node","jest-haste-map","jest-message-util","jest-resolve","jest-resolve-dependencies","jest-runner","jest-runtime","jest-snapshot","jest-watcher","micromatch"]);
const lines = raw.split("\n");
const depStart = lines.findIndex((l) => l === '  "dependencies": {');
const devStart = lines.findIndex((l) => l === '  "devDependencies": {');
if (depStart < 0 || devStart < 0) { console.error("blocks not found"); process.exit(2); }
const captured = {};
const removeIdx = [];
for (let i = depStart + 1; i < lines.length && lines[i] !== "  }" && lines[i] !== "  },"; i++) {
  const m = lines[i].match(/^    "([^"]+)": "([^"]+)",?$/);
  if (m && targets.has(m[1])) {
    if (!lines[i].endsWith(",")) { console.error("target is last entry (no comma): " + lines[i]); process.exit(2); }
    captured[m[1]] = m[2];
    removeIdx.push(i);
  }
}
if (removeIdx.length !== 18) { console.error("captured " + removeIdx.length + " != 18"); process.exit(2); }
const devEntries = {};
let devEnd = -1;
for (let i = devStart + 1; i < lines.length; i++) {
  if (lines[i] === "  },") { devEnd = i; break; }
  const m = lines[i].match(/^    "([^"]+)": "([^"]+)",?$/);
  if (m) devEntries[m[1]] = m[2];
}
if (devEnd < 0) { console.error("dev block end not found"); process.exit(2); }
for (const [k, v] of Object.entries(captured)) devEntries[k] = v;
const sorted = Object.keys(devEntries).sort();
const newDevLines = sorted.map((k, idx) => `    "${k}": "${devEntries[k]}"${idx === sorted.length - 1 ? "" : ","}`);
const removeSet = new Set(removeIdx);
const out = [];
for (let i = 0; i < lines.length; i++) { if (!removeSet.has(i)) out.push(lines[i]); }
const dStart2 = out.findIndex((l) => l === '  "devDependencies": {');
let dEnd2 = -1;
for (let i = dStart2 + 1; i < out.length; i++) { if (out[i] === "  },") { dEnd2 = i; break; } }
out.splice(dStart2 + 1, dEnd2 - dStart2 - 1, ...newDevLines);
const result = out.join("\n");
JSON.parse(result);
writeFileSync(p, result);
console.log(JSON.stringify({ movedCount: removeIdx.length, moved: captured, devCount: sorted.length }, null, 1));
