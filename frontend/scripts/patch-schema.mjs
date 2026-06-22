/**
 * Downloads the OpenAPI schema from the running Django dev server,
 * deduplicates enum component names (which orval rejects), and saves
 * a patched version to src/lib/schema.json for orval to consume locally.
 *
 * Run: node scripts/patch-schema.mjs
 */
import { writeFileSync } from "fs";
import { createRequire } from "module";

const SCHEMA_URL = "http://localhost:8000/api/schema/?format=json";
const OUTPUT = "./src/lib/schema.json";

const resp = await fetch(SCHEMA_URL);
if (!resp.ok) throw new Error(`Schema fetch failed: ${resp.status}`);
const schema = await resp.json();

// Deduplicate component names by appending _N suffix
const components = schema.components?.schemas ?? {};
const seen = {};
const renames = {};

for (const key of Object.keys(components)) {
  if (key in seen) {
    seen[key]++;
    const newKey = `${key}_${seen[key]}`;
    renames[key] = renames[key] ?? [];
    renames[key].push(newKey);
    components[newKey] = components[key];
    delete components[key];
    console.log(`  renamed duplicate: ${key} → ${newKey}`);
  } else {
    seen[key] = 1;
  }
}

// Update all $ref pointers that reference renamed schemas
const schemaStr = JSON.stringify(schema);
let patched = schemaStr;
for (const [orig, newNames] of Object.entries(renames)) {
  // Only rename refs to the duplicate (2nd occurrence onwards)
  // The first occurrence keeps its name; subsequent ones get _2, _3, etc.
  // Since we already renamed in components, just patch any remaining $refs
  for (const newName of newNames) {
    patched = patched.replaceAll(
      `"#/components/schemas/${newName.replace(/_\d+$/, "")}"`,
      `"#/components/schemas/${newName}"`
    );
  }
}

writeFileSync(OUTPUT, patched);
console.log(`\nSchema written to ${OUTPUT}`);
console.log(`Total schemas: ${Object.keys(JSON.parse(patched).components?.schemas ?? {}).length}`);
