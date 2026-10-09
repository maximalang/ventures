// Where are the 18 braces-reaching direct deps declared, and does shipped code import them?
import { readFileSync } from "node:fs";
import { join } from "node:path";
const clone = process.argv[2];
const targets = ["babel-jest","braces","create-jest","expect","jest-circus","jest-cli","jest-config","jest-environment-jsdom","jest-environment-node","jest-haste-map","jest-message-util","jest-resolve","jest-resolve-dependencies","jest-runner","jest-runtime","jest-snapshot","jest-watcher","micromatch"];
const manifests = {
  "root": join(clone, "package.json"),
  "apps/web": join(clone, "apps/web/package.json"),
  "packages/db": join(clone, "packages/db/package.json"),
};
const decl = {};
for (const [name, p] of Object.entries(manifests)) {
  const pkg = JSON.parse(readFileSync(p, "utf8"));
  for (const section of ["dependencies","devDependencies","optionalDependencies","peerDependencies"]) {
    for (const t of targets) {
      if (pkg[section] && Object.prototype.hasOwnProperty.call(pkg[section], t)) {
        (decl[t] ||= []).push(`${name}:${section}@${pkg[section][t]}`);
      }
    }
  }
}
// also list jest itself and other test tooling declared where
const extra = ["jest","ts-jest","@jest/core","@jest/transform","@types/jest","jest-util","@testing-library/react","@testing-library/jest-dom","identity-obj-proxy","jest-environment-jsdom"];
const declExtra = {};
for (const [name, p] of Object.entries(manifests)) {
  const pkg = JSON.parse(readFileSync(p, "utf8"));
  for (const section of ["dependencies","devDependencies"]) {
    for (const t of extra) {
      if (pkg[section]?.[t]) (declExtra[t] ||= []).push(`${name}:${section}@${pkg[section][t]}`);
    }
  }
}
console.log(JSON.stringify({ decl, declExtra }, null, 2));
