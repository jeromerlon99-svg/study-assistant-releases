import { readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const expected = (await readFile(path.join(root, "VERSION"), "utf8")).trim();
const files = [
  ["package.json", JSON.parse(await readFile(path.join(root, "package.json"), "utf8")).version],
  [
    "apps/desktop/package.json",
    JSON.parse(await readFile(path.join(root, "apps/desktop/package.json"), "utf8")).version,
  ],
  [
    "apps/desktop/src-tauri/tauri.conf.json",
    JSON.parse(
      await readFile(path.join(root, "apps/desktop/src-tauri/tauri.conf.json"), "utf8"),
    ).version,
  ],
];

for (const [name, version] of files) {
  if (version !== expected) {
    throw new Error(`${name} has version ${version}; expected ${expected}`);
  }
}

const textManifests = [
  ["apps/desktop/src-tauri/Cargo.toml", new RegExp(`^version\\s*=\\s*"${expected.replaceAll(".", "\\.")}"`, "m")],
  ["services/agent/pyproject.toml", new RegExp(`^version\\s*=\\s*"${expected.replaceAll(".", "\\.")}"`, "m")],
  ["services/agent/src/study_assistant_agent/__init__.py", new RegExp(`^__version__\\s*=\\s*"${expected.replaceAll(".", "\\.")}"`, "m")],
];

for (const [name, pattern] of textManifests) {
  const content = await readFile(path.join(root, name), "utf8");
  if (!pattern.test(content)) {
    throw new Error(`${name} does not declare version ${expected}`);
  }
}

console.log(`All ${files.length + textManifests.length + 1} version sources use ${expected}.`);
