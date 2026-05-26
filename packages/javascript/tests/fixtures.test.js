import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import test from "node:test";

import { cumbin } from "../src/index.js";

const fixturesDir = new URL("../../../fixtures/", import.meta.url);
const fixtureFiles = (await readdir(fixturesDir))
  .filter((name) => name.endsWith(".json"))
  .sort();

for (const file of fixtureFiles) {
  test(`fixture: ${file}`, async () => {
    const fixture = JSON.parse(await readFile(join(fileURLToPath(fixturesDir), file), "utf8"));
    const actual = cumbin(fixture.input, fixture.spec);
    assertRowsAlmostEqual(actual, fixture.expected);
  });
}

function assertRowsAlmostEqual(actual, expected) {
  assert.equal(actual.length, expected.length);

  for (let rowIndex = 0; rowIndex < expected.length; rowIndex += 1) {
    const actualRow = actual[rowIndex];
    const expectedRow = expected[rowIndex];
    const keys = new Set([...Object.keys(actualRow), ...Object.keys(expectedRow)]);

    for (const key of keys) {
      if (typeof expectedRow[key] === "number") {
        assert.ok(
          Math.abs(actualRow[key] - expectedRow[key]) <= 1e-12,
          `row ${rowIndex}.${key}: expected ${expectedRow[key]}, got ${actualRow[key]}`
        );
      } else {
        assert.deepEqual(actualRow[key], expectedRow[key], `row ${rowIndex}.${key}`);
      }
    }
  }
}
