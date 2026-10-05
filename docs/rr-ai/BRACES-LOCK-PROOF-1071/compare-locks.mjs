// Compare baseline lock vs post-install lock: node inventory, versions,
// consistency fields, dependency edges, dev-flag flips. Read-only analysis.
import { readFileSync, writeFileSync } from "node:fs";
const [a, b, out] = process.argv.slice(2);
const base = JSON.parse(readFileSync(a, "utf8"));
const cur = JSON.parse(readFileSync(b, "utf8"));
const bp = base.packages || {}, cp = cur.packages || {};
const bk = Object.keys(bp).sort(), ck = Object.keys(cp).sort();
const added = ck.filter(k => !(k in bp));
const dropped = bk.filter(k => !(k in cp));
const versionChanges = [];
const fieldChanges = [];
const devFlagChanges = [];
const TRACKED = ["resolved", "integrity", "license", "optional", "peer", "hasInstallScript", "dependencies", "optionalDependencies", "peerDependencies", "bin", "engines"];
for (const k of bk) {
  if (!(k in cp)) continue;
  const x = bp[k], y = cp[k];
  if (x.version !== y.version) versionChanges.push({ node: k, before: x.version, after: y.version });
  for (const f of TRACKED) {
    if (JSON.stringify(x[f]) !== JSON.stringify(y[f])) fieldChanges.push({ node: k, field: f, before: x[f], after: y[f] });
  }
  if (!!x.dev !== !!y.dev) devFlagChanges.push({ node: k, before: !!x.dev, after: !!y.dev, version: y.version });
}
const res = {
  node_count_before: bk.length,
  node_count_after: ck.length,
  nodes_added: added,
  nodes_dropped: dropped,
  version_change_count: versionChanges.length,
  version_changes: versionChanges.slice(0, 20),
  inventory_consistency_field_change_count: fieldChanges.length,
  inventory_consistency_field_changes: fieldChanges.slice(0, 50),
  dev_flag_changes: devFlagChanges,
  root_entry: {
    dependencies_dropped: Object.keys((bp[""] || {}).dependencies || {}).filter(k => !(k in (((cp[""]) || {}).dependencies || {}))),
    devDependencies_added: Object.keys((cp[""] || {}).devDependencies || {}).filter(k => !(k in ((bp[""] || {}).devDependencies || {})))
  },
  braces_node_before: bp["node_modules/braces"],
  braces_node_after: cp["node_modules/braces"]
};
writeFileSync(out, JSON.stringify(res, null, 1));
console.log("nodes", bk.length, "->", ck.length, "| added", added.length, "| dropped", dropped.length, "| verChanges", versionChanges.length, "| fieldChanges", fieldChanges.length, "| devFlagFlips", devFlagChanges.length);
console.log("flips:", JSON.stringify(devFlagChanges));
