// Move the 18 braces-reaching direct test/build-only deps from dependencies to devDependencies
import { readFileSync, writeFileSync } from "node:fs";
const p = "C:/Users/max/Desktop/all/ventures/.worktrees/rr-braces-source-1067-a7c3/package.json";
const raw = readFileSync(p, "utf8");
const pkg = JSON.parse(raw);
const targets = ["babel-jest","braces","create-jest","expect","jest-circus","jest-cli","jest-config","jest-environment-jsdom","jest-environment-node","jest-haste-map","jest-message-util","jest-resolve","jest-resolve-dependencies","jest-runner","jest-runtime","jest-snapshot","jest-watcher","micromatch"];
const moved = {};
pkg.devDependencies = pkg.devDependencies || {};
for (const t of targets) {
  if (Object.prototype.hasOwnProperty.call(pkg.dependencies, t)) {
    moved[t] = pkg.dependencies[t];
    delete pkg.dependencies[t];
  }
}
for (const [k, v] of Object.entries(moved)) pkg.devDependencies[k] = v;
// sort devDependencies alphabetically for deterministic diff
const sortedDev = {};
for (const k of Object.keys(pkg.devDependencies).sort()) sortedDev[k] = pkg.devDependencies[k];
pkg.devDependencies = sortedDev;
const out = JSON.stringify(pkg, null, 2) + "\n";
// detect original trailing newline / indent
const indentMatch = raw.match(/\n(\s+)"/);
writeFileSync(p, out);
console.log(JSON.stringify({ moved, depsAfter: Object.keys(pkg.dependencies).length, devAfter: Object.keys(pkg.devDependencies).length, indent: indentMatch ? indentMatch[1].length : null, endsWithNewline: raw.endsWith("\n") }, null, 1));
