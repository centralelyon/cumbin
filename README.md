# cumbin

Cumulative bins by value from tabular data.

Example: given values `[12, 3, 17]` and `binSize = 10`, cumulative intervals are `[0, 12)`, `[12, 15)`, and `[15, 32)`. `cumbin` splits those intervals across bins `[0, 10)`, `[10, 20)`, `[20, 30)`, and `[30, 40)`, returning one row per source/bin overlap.


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
