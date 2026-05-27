# cumbin

Cumulative bins by value from tabular data.

Example with values below and `binSize = 10`:

```
[
  { label: "A", value: 12},
  { label: "B", value: 3},
  { label: "C", value: 17}
]
```

It returns 4 bins with explicit overflow attribution:

```
[
  { label: "A", value: 12, bin: 0, bin_start: 0, bin_end: 10, amount: 10, source_index: 0, source_start: 0, source_end: 12, source_amount: 12, source_fraction: 0.8333333333333334 },
  { label: "A", value: 12, bin: 1, bin_start: 10, bin_end: 20, amount: 2, source_index: 0, source_start: 0, source_end: 12, source_amount: 12, source_fraction: 0.16666666666666666 },
  { label: "B", value: 3, bin: 1, bin_start: 10, bin_end: 20, amount: 3, source_index: 1, source_start: 12, source_end: 15, source_amount: 3, source_fraction: 1 },
  { label: "C", value: 17, bin: 1, bin_start: 10, bin_end: 20, amount: 7, source_index: 2, source_start: 15, source_end: 32, source_amount: 17, source_fraction: 0.4117647058823529 },
]
```

That can be illustrated as:

<img width="591" height="432" alt="Image" src="https://github.com/user-attachments/assets/8a9ecc9a-cc29-4028-9e49-c84a4f69ac49" />


## JavaScript Usage

```js
import { cumbin } from "cumbin";

const rows = cumbin(
  [
    { label: "A", value: 12 },
    { label: "B", value: 3 },
    { label: "C", value: 17 }
  ],
  { value: "value", binSize: 10 }
);
```

In Observable notebooks, import the npm package directly:

```js
import { cumbin, summarizeBins } from "npm:cumbin"
```

For direct UNPKG imports:

```js
cumbin = (await import("https://unpkg.com/cumbin@0.2.1/cumbin.js?module")).default
```

`index.js` is also included as a compatibility alias.

```python
from cumbin import cumbin

rows = cumbin(
    [
        {"label": "A", "value": 12},
        {"label": "B", "value": 3},
        {"label": "C", "value": 17},
    ],
    {"value": "value", "binSize": 10},
)
```

The row value contains:

```json
{
  "label": "A",
  "value": 12,
  "bin": 0,
  "bin_start": 0,
  "bin_end": 10,
  "amount": 10,
  "source_index": 0,
  "source_start": 0,
  "source_end": 12,
  "source_amount": 12,
  "source_fraction": 0.8333333333333334
}
```

Each output row preserves source fields and adds:

- `bin`: zero-based bin index.
- `bin_start`, `bin_end`: bin extent.
- `amount`: overlap amount contributed to the bin.
- `source_index`: original row index.
- `source_start`, `source_end`: source cumulative interval.
- `source_amount`: original interval size.
- `source_fraction`: `amount / source_amount`.

## Python Usage

```python
from cumbin import cumbin

rows = cumbin(
    [
        {"label": "A", "value": 12},
        {"label": "B", "value": 3},
        {"label": "C", "value": 17},
    ],
    {"value": "value", "binSize": 10},
)
```

The output is the same as the JavaScript version, with the same fields and semantics.

<img width="609" height="286" alt="Image" src="https://github.com/user-attachments/assets/0caf9984-22eb-42d6-a3b3-69a9e79cee1b" />

## JavaScript And Python APIs

The canonical output is tidy tabular data shared by both packages:

- The JavaScript package is a dependency-free browser ESM module exporting `cumbin`, `cumulativeBins`, `summarizeBins`, and `normalizeSpec`.
- The Python package exports `cumbin`, `cumulative_bins`, and `summarize_bins`.
- Optional Pandas helpers live in `cumbin.pandas`, including `cumbin_frame` for DataFrame workflows.
- Downstream plotting or analysis code should consume the returned rows directly instead of relying on package-specific visualization adapters.

## Development

Run the shared fixture tests:

```sh
npm test
```

Run only one implementation:

```sh
npm run test:js
npm run test:py
```

The tests intentionally read the same files under `fixtures/`, so behavioral changes must update the shared contract rather than one language wrapper.

## Credits

Original idea by [@fil](https://observablehq.com/@fil/cumulative-binning) in Observable.