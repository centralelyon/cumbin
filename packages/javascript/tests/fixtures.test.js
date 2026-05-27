import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import test from "node:test";

import { cumbin, normalizeSpec, summarizeBins } from "../cumbin.js";

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

test("single bin when cumulative total equals bin size", () => {
  const rows = cumbin(
    [
      { label: "A", value: 12 },
      { label: "B", value: 3 },
      { label: "C", value: 17 }
    ],
    { value: "value", binSize: 32 }
  );

  assert.equal(rows.length, 3);
  assert.deepEqual([...new Set(rows.map((row) => row.bin))], [0]);
  assert.deepEqual(rows.map((row) => row.amount), [12, 3, 17]);
  assert.deepEqual(rows.map((row) => [row.bin_start, row.bin_end]), [
    [0, 32],
    [0, 32],
    [0, 32]
  ]);
});

test("cumulative mode accepts an empty string field name", () => {
  const rows = cumbin(
    [
      { "": 4 },
      { "": 11 }
    ],
    { cumulative: "", binSize: 10 }
  );

  assert.deepEqual(rows.map((row) => row.amount), [4, 6, 1]);
  assert.deepEqual(rows.map((row) => row.source_start), [0, 4, 4]);
  assert.deepEqual(rows.map((row) => row.source_end), [4, 11, 11]);
});

test("rejects thresholds with fewer than two boundaries", () => {
  assert.throws(
    () => normalizeSpec({ value: "value", thresholds: [0] }),
    /thresholds must include at least two boundaries/
  );
});

test("rejects non-finite thresholds", () => {
  assert.throws(
    () => normalizeSpec({ value: "value", thresholds: [0, Number.NaN] }),
    /expected a finite number for thresholds/
  );
});

test("includeSource false only emits transform fields", () => {
  const rows = cumbin(
    [{ label: "A", value: 12 }],
    { value: "value", binSize: 10, includeSource: false }
  );

  assert.deepEqual(rows, [
    {
      bin: 0,
      bin_start: 0,
      bin_end: 10,
      amount: 10,
      source_index: 0,
      source_start: 0,
      source_end: 12,
      source_amount: 12,
      source_fraction: 10 / 12
    },
    {
      bin: 1,
      bin_start: 10,
      bin_end: 20,
      amount: 2,
      source_index: 0,
      source_start: 0,
      source_end: 12,
      source_amount: 12,
      source_fraction: 2 / 12
    }
  ]);
});

test("summarizeBins aggregates amounts by bin and group fields", () => {
  const rows = cumbin(
    [
      { group: "north", value: 6 },
      { group: "south", value: 4 },
      { group: "north", value: 7 }
    ],
    { value: "value", binSize: 10, groupBy: "group" }
  );

  assert.deepEqual(summarizeBins(rows, { groupBy: "group" }), [
    { bin: 0, bin_start: 0, bin_end: 10, amount: 10, count: 2, group: "north" },
    { bin: 0, bin_start: 0, bin_end: 10, amount: 4, count: 1, group: "south" },
    { bin: 1, bin_start: 10, bin_end: 20, amount: 3, count: 1, group: "north" }
  ]);
});

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
