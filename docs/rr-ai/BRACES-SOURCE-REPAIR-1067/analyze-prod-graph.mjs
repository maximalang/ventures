// Offline production-graph analysis for braces (lockfile v3).
// Usage: node analyze-prod-graph.mjs <clone-dir>
import { readFileSync } from "node:fs";
import { join } from "node:path";

const clone = process.argv[2];
const lock = JSON.parse(readFileSync(join(clone, "package-lock.json"), "utf8"));
const rootPkg = JSON.parse(readFileSync(join(clone, "package.json"), "utf8"));

const pkgs = lock.packages || {};
// workspace roots
const workspaces = Object.keys(pkgs).filter((k) => k !== "" && pkgs[k].link === true);
const wsDirs = workspaces.map((k) => pkgs[k].resolved); // real dirs

// Build reverse dependency map within prod (non-dev) nodes
function nodeKey(name, fromKey) {
  // resolve nested node_modules path
  const parts = fromKey ? fromKey.split("node_modules/") : [];
  // simple approach: search all keys ending with node_modules/<name>, prefer deepest under fromKey
  let best = null;
  for (const k of Object.keys(pkgs)) {
    if (!k.endsWith("node_modules/" + name)) continue;
    if (fromKey && !k.startsWith(fromKey)) continue;
    if (best === null || k.length > best.length) best = k;
  }
  if (best) return best;
  for (const k of Object.keys(pkgs)) {
    if (k.endsWith("node_modules/" + name)) {
      if (best === null || k.length < best.length) best = k;
    }
  }
  return best;
}

// Find all braces nodes
const bracesNodes = Object.keys(pkgs).filter((k) => k.endsWith("node_modules/braces"));
const out = { bracesNodes: [], prodPaths: [] };
for (const b of bracesNodes) {
  const n = pkgs[b];
  out.bracesNodes.push({ key: b, version: n.version, dev: !!n.dev });
}

// BFS reverse: from each prod braces node, walk up dependents until direct root/workspace deps
const prodBraces = bracesNodes.filter((b) => !pkgs[b].dev);
// map: child -> list of parents (who lists it in dependencies/optional/peer that are installed)
function parentsOf(childKey) {
  const childName = childKey.split("node_modules/").pop();
  const parents = [];
  for (const [k, n] of Object.entries(pkgs)) {
    if (!n || k === childKey) continue;
    const deps = { ...(n.dependencies || {}), ...(n.optionalDependencies || {}) };
    if (Object.prototype.hasOwnProperty.call(deps, childName)) {
      // check this parent could resolve to child (child under parent's subtree or hoisted)
      if (childKey.startsWith(k + "/") || !k.includes("node_modules") || nodeKey(childName, k) === childKey) {
        parents.push(k);
      }
    }
  }
  return parents;
}

// direct deps of root and workspaces (prod only)
const directProd = new Set();
{
  const rd = rootPkg.dependencies || {};
  for (const name of Object.keys(rd)) directProd.add(name);
}
for (const wsKey of workspaces) {
  const realDir = pkgs[wsKey].resolved;
  const wsPkg = JSON.parse(readFileSync(join(clone, realDir, "package.json"), "utf8"));
  for (const name of Object.keys(wsPkg.dependencies || {})) directProd.add(name);
}

const found = [];
const seen = new Set();
function walkUp(key, path) {
  const name = key === "" ? "<root>" : key.split("node_modules/").pop();
  const cur = [...path, key === "" ? "<root>" : name + "@" + (pkgs[key]?.version || "?")];
  if (key === "") { found.push(cur.reverse()); return; }
  if (directProd.has(name) && key.split("node_modules/").length === 1) {
    // direct hoisted dep: next hop is root
    found.push([...cur, "<root-direct:" + name + ">"].reverse());
    return;
  }
  if (seen.has(key + "|" + cur.length)) return;
  seen.add(key + "|" + cur.length);
  const ps = parentsOf(key);
  if (ps.length === 0) { found.push([...cur, "<orphan>"].reverse()); return; }
  for (const p of ps) walkUp(p, cur);
}
for (const b of prodBraces) walkUp(b, []);

// also: which direct root prod deps transitively reach a prod braces node
function reachesBraces(depName) {
  const start = nodeKey(depName, "");
  if (!start) return false;
  const stack = [start]; const vis = new Set();
  while (stack.length) {
    const k = stack.pop();
    if (vis.has(k)) continue; vis.add(k);
    if (k.endsWith("node_modules/braces") && !pkgs[k].dev) return true;
    const n = pkgs[k]; if (!n || n.dev) continue;
    for (const d of Object.keys({ ...(n.dependencies || {}), ...(n.optionalDependencies || {}) })) {
      const dk = nodeKey(d, k); if (dk) stack.push(dk);
    }
  }
  return false;
}
const directToBraces = [...directProd].filter(reachesBraces).sort();

console.log(JSON.stringify({
  rootDeps: Object.keys(rootPkg.dependencies || {}).length,
  rootDevDeps: Object.keys(rootPkg.devDependencies || {}),
  workspaces: rootPkg.workspaces,
  wsDirs,
  bracesNodes: out.bracesNodes,
  prodBracesCount: prodBraces.length,
  directProdDepsReachingBraces: directToBraces,
  pathSamples: found.slice(0, 12),
  pathCount: found.length,
}, null, 2));
