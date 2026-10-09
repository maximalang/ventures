// Recompute lockfile dev flags from repaired manifests (prod reachability), preserving versions.
// Edges: dependencies + optionalDependencies + peerDependencies (arborist prod semantics).
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const clone = "C:/Users/max/Desktop/all/ventures/.worktrees/rr-braces-source-1067-a7c3";
const lockRaw = readFileSync(join(clone, "package-lock.json"), "utf8");
const roundtrip = JSON.stringify(JSON.parse(lockRaw), null, 2) + "\n";
console.log("lock roundtrip identical:", roundtrip === lockRaw, lockRaw.length, roundtrip.length);
const lock = JSON.parse(lockRaw);
const pkgs = lock.packages;
const rootPkg = JSON.parse(readFileSync(join(clone, "package.json"), "utf8"));

// workspace link nodes and their real dirs
const links = Object.entries(pkgs).filter(([, n]) => n && n.link).map(([k, n]) => ({ key: k, dir: n.resolved }));
const wsProdDeps = [];
for (const l of links) {
  const wp = JSON.parse(readFileSync(join(clone, l.dir, "package.json"), "utf8"));
  wsProdDeps.push({ linkKey: l.key, deps: wp.dependencies || {}, opt: wp.optionalDependencies || {}, peer: wp.peerDependencies || {} });
}

// resolver: given parent key ("" = root, "apps/web" = ws link dir, or node_modules path), child name
const allKeys = Object.keys(pkgs);
function resolveChild(parentKey, name) {
  // nested first: parentKey + "/node_modules/" + name (also deeper via longest match)
  let best = null;
  const suffix = "node_modules/" + name;
  for (const k of allKeys) {
    if (!k.endsWith(suffix)) continue;
    if (parentKey && parentKey !== "") {
      if (k.startsWith(parentKey + "/node_modules/") || k === parentKey + "/node_modules/" + name) {
        if (!best || k.length > best.length) best = k;
      }
    }
  }
  if (best) return best;
  // hoisted: shortest global match
  let hoist = null;
  for (const k of allKeys) {
    if (k.endsWith(suffix)) { if (!hoist || k.length < hoist.length) hoist = k; }
  }
  return hoist;
}

const prodReach = new Set();
const queue = [];
// roots: root manifest prod deps resolved from ""
for (const [name] of Object.entries(rootPkg.dependencies || {})) {
  const k = resolveChild("", name); if (k) queue.push(k);
}
for (const [name] of Object.entries(rootPkg.optionalDependencies || {})) {
  const k = resolveChild("", name); if (k) queue.push(k);
}
// workspace link nodes are prod roots themselves (workspaces of private root)
for (const w of wsProdDeps) {
  prodReach.add(w.linkKey);
  for (const [name] of Object.entries(w.deps)) { const k = resolveChild(w.linkKey, name); if (k) queue.push(k); }
  for (const [name] of Object.entries(w.opt)) { const k = resolveChild(w.linkKey, name); if (k) queue.push(k); }
}
prodReach.add("");
while (queue.length) {
  const k = queue.pop();
  if (prodReach.has(k)) continue;
  prodReach.add(k);
  const n = pkgs[k];
  if (!n) continue;
  const edges = { ...(n.dependencies || {}), ...(n.optionalDependencies || {}), ...(n.peerDependencies || {}) };
  for (const name of Object.keys(edges)) {
    const ck = resolveChild(k, name);
    if (ck && !prodReach.has(ck)) queue.push(ck);
  }
}

// flip flags
let flippedToDev = 0, flippedToProd = 0;
const flippedNames = [];
for (const k of allKeys) {
  if (k === "") continue;
  const n = pkgs[k];
  if (!n || n.link) continue;
  const shouldBeDev = !prodReach.has(k);
  const isDev = !!n.dev;
  if (shouldBeDev && !isDev) { n.dev = true; flippedToDev++; if (flippedNames.length < 40) flippedNames.push(k); }
  else if (!shouldBeDev && isDev) { delete n.dev; flippedToProd++; }
}
// also devOptional consistency: leave as-is (only dev flag matters for audit omit=dev)
console.log(JSON.stringify({ prodReachCount: prodReach.size, totalNodes: allKeys.length, flippedToDev, flippedToProd, sampleFlipped: flippedNames }, null, 1));
if (flippedToProd > 0) { console.error("UNEXPECTED flip-to-prod; abort write"); process.exit(2); }
const out = JSON.stringify(lock, null, 2) + "\n";
if (!roundtrip === lockRaw) { /* noop */ }
writeFileSync(join(clone, "package-lock.json"), out);
console.log("lock written", out.length);
