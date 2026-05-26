# cumbin

Dependency-free browser ESM cumulative binning for JavaScript and Observable notebooks.

```js
import { cumbin } from "cumbin";
```

In Observable:

```js
import { cumbin, summarizeBins } from "npm:cumbin"
```

Or, with a direct UNPKG dynamic import:

```js
cumbin = (await import("https://unpkg.com/cumbin@0.2.1/cumbin.js?module")).default
```

`index.js` is also included as a compatibility alias.

```js
rows = cumbin(
  [
    { label: "A", value: 12 },
    { label: "B", value: 3 },
    { label: "C", value: 17 }
  ],
  { value: "value", binSize: 10 }
)
```

The module exports `cumbin`, `cumulativeBins`, `summarizeBins`, and `normalizeSpec`.
