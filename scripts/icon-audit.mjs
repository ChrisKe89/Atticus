#!/usr/bin/env node
import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const TARGET_DIRECTORIES = ["app", "components"];
const ICON_IMPORT_REGEX = /import\s+{([^}]+)}\s+from\s+['"]lucide-react['"]/g;
const ICON_NAME_REGEX = /^[A-Z][A-Za-z0-9]*$/;

function walk(dir) {
  const entries = readdirSync(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (entry.name.startsWith(".") || entry.name.startsWith("_")) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walk(fullPath));
    } else if (entry.isFile() && /\.(tsx|ts|jsx|js)$/.test(entry.name)) {
      files.push(fullPath);
    }
  }
  return files;
}

function auditFile(file) {
  const source = readFileSync(file, "utf8");
  const matches = [];
  let match;
  while ((match = ICON_IMPORT_REGEX.exec(source)) !== null) {
    matches.push({ importBlock: match[1], index: match.index });
  }
  const violations = [];
  for (const { importBlock, index } of matches) {
    const rawIcons = importBlock.split(",");
    for (const rawIcon of rawIcons) {
      const icon = rawIcon.trim();
      if (!icon) continue;
      const [name] = icon.split(/\s+as\s+/i);
      if (!ICON_NAME_REGEX.test(name)) {
        violations.push({ file, icon: name.trim(), position: index });
      }
    }
  }
  return violations;
}

const allViolations = [];
for (const dir of TARGET_DIRECTORIES) {
  if (!statSync(dir, { throwIfNoEntry: false })) {
    continue;
  }
  const files = walk(dir);
  for (const file of files) {
    allViolations.push(...auditFile(file));
  }
}

if (allViolations.length > 0) {
  console.error("Found invalid lucide-react icon imports:");
  for (const violation of allViolations) {
    console.error(`  ${violation.file}: ${violation.icon || "<empty>"}`);
  }
  process.exit(1);
}

console.log("Lucide icon imports look good.");
