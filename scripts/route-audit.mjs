#!/usr/bin/env node
import { readdirSync, statSync } from "node:fs";
import path from "node:path";

const appDir = path.resolve("app");

function walkRoutes(current, prefix = "") {
  const entries = readdirSync(current, { withFileTypes: true });
  const result = [];
  for (const entry of entries) {
    if (entry.name.startsWith("_") || entry.name.startsWith(".")) continue;
    const fullPath = path.join(current, entry.name);
    const routePath = path.join(prefix, entry.name);
    if (entry.isDirectory()) {
      const isRouteSegment = ["page.tsx", "route.ts", "layout.tsx"].some((file) => {
        try {
          return statSync(path.join(fullPath, file)).isFile();
        } catch (error) {
          return false;
        }
      });
      if (isRouteSegment) {
        result.push({ segment: routePath.replace(/\\/g, "/"), files: readdirSync(fullPath) });
      }
      result.push(...walkRoutes(fullPath, routePath));
    }
  }
  return result;
}

const routes = walkRoutes(appDir);
console.log(JSON.stringify({ routes }, null, 2));
