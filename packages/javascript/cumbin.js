const OUTPUT_FIELDS = {
  bin: "bin",
  binStart: "bin_start",
  binEnd: "bin_end",
  amount: "amount",
  sourceIndex: "source_index",
  sourceStart: "source_start",
  sourceEnd: "source_end",
  sourceAmount: "source_amount",
  sourceFraction: "source_fraction"
};

export function cumbin(data, spec = {}) {
  const config = normalizeSpec(spec);
  const cursors = new Map();
  const output = [];

  Array.from(data).forEach((row, sourceIndex) => {
    const groupKey = keyFor(row, config.groupBy);
    const cursor = cursors.has(groupKey) ? cursors.get(groupKey) : config.origin;
    const sourceEnd = config.cumulative
      ? numberFrom(read(row, config.cumulative), config.cumulative)
      : cursor + numberFrom(read(row, config.value), config.value);
    const sourceStart = cursor;
    const sourceAmount = sourceEnd - sourceStart;

    if (sourceAmount < 0) {
      throw new RangeError("cumbin requires non-negative amounts and monotone cumulative endpoints");
    }

    cursors.set(groupKey, sourceEnd);

    if (sourceAmount === 0) {
      return;
    }

    for (const segment of splitInterval(sourceStart, sourceEnd, config)) {
      const base = config.includeSource && isRecord(row) ? { ...row } : {};
      output.push({
        ...base,
        [OUTPUT_FIELDS.bin]: segment.bin,
        [OUTPUT_FIELDS.binStart]: segment.binStart,
        [OUTPUT_FIELDS.binEnd]: segment.binEnd,
        [OUTPUT_FIELDS.amount]: segment.amount,
        [OUTPUT_FIELDS.sourceIndex]: sourceIndex,
        [OUTPUT_FIELDS.sourceStart]: sourceStart,
        [OUTPUT_FIELDS.sourceEnd]: sourceEnd,
        [OUTPUT_FIELDS.sourceAmount]: sourceAmount,
        [OUTPUT_FIELDS.sourceFraction]: segment.amount / sourceAmount
      });
    }
  });

  return output;
}

export const cumulativeBins = cumbin;

export function summarizeBins(rows, options = {}) {
  const groupFields = arrayOf(options.groupBy ?? []);
  const amountField = options.amount ?? OUTPUT_FIELDS.amount;
  const groups = new Map();

  for (const row of rows) {
    const key = JSON.stringify([
      row[OUTPUT_FIELDS.bin],
      row[OUTPUT_FIELDS.binStart],
      row[OUTPUT_FIELDS.binEnd],
      ...groupFields.map((field) => row[field])
    ]);

    if (!groups.has(key)) {
      groups.set(key, {
        [OUTPUT_FIELDS.bin]: row[OUTPUT_FIELDS.bin],
        [OUTPUT_FIELDS.binStart]: row[OUTPUT_FIELDS.binStart],
        [OUTPUT_FIELDS.binEnd]: row[OUTPUT_FIELDS.binEnd],
        [amountField]: 0,
        count: 0
      });
      for (const field of groupFields) {
        groups.get(key)[field] = row[field];
      }
    }

    const current = groups.get(key);
    current[amountField] += numberFrom(row[OUTPUT_FIELDS.amount], OUTPUT_FIELDS.amount);
    current.count += 1;
  }

  return Array.from(groups.values());
}

export function normalizeSpec(spec) {
  const value = spec.value ?? spec.amount;
  const cumulative = spec.cumulative;
  const thresholds = spec.thresholds == null ? null : spec.thresholds.map(Number);
  const binSize = spec.binSize ?? spec.bin_size;
  const origin = spec.origin == null ? 0 : numberFrom(spec.origin, "origin");

  if ((value == null) === (cumulative == null)) {
    throw new TypeError("cumbin requires exactly one of value or cumulative");
  }

  if ((binSize == null) === (thresholds == null)) {
    throw new TypeError("cumbin requires exactly one of binSize or thresholds");
  }

  if (thresholds) {
    for (let index = 1; index < thresholds.length; index += 1) {
      if (!(thresholds[index] > thresholds[index - 1])) {
        throw new RangeError("cumbin thresholds must be strictly increasing");
      }
    }
  }

  const normalizedBinSize = binSize == null ? null : numberFrom(binSize, "binSize");
  if (normalizedBinSize != null && normalizedBinSize <= 0) {
    throw new RangeError("cumbin binSize must be positive");
  }

  return {
    value,
    cumulative,
    binSize: normalizedBinSize,
    thresholds,
    origin,
    groupBy: spec.groupBy ?? spec.group_by,
    includeSource: spec.includeSource ?? spec.include_source ?? true
  };
}

function splitInterval(start, end, config) {
  if (config.thresholds) {
    return splitByThresholds(start, end, config.thresholds);
  }

  return splitByRegularBins(start, end, config.origin, config.binSize);
}

function splitByRegularBins(start, end, origin, binSize) {
  const segments = [];
  let bin = Math.floor((start - origin) / binSize);

  while (origin + bin * binSize < end) {
    const binStart = origin + bin * binSize;
    const binEnd = binStart + binSize;
    const overlapStart = Math.max(start, binStart);
    const overlapEnd = Math.min(end, binEnd);
    const amount = overlapEnd - overlapStart;

    if (amount > 0) {
      segments.push({ bin, binStart, binEnd, amount });
    }

    bin += 1;
  }

  return segments;
}

function splitByThresholds(start, end, thresholds) {
  const segments = [];

  for (let bin = 0; bin < thresholds.length - 1; bin += 1) {
    const binStart = thresholds[bin];
    const binEnd = thresholds[bin + 1];

    if (binStart >= end) {
      break;
    }

    const overlapStart = Math.max(start, binStart);
    const overlapEnd = Math.min(end, binEnd);
    const amount = overlapEnd - overlapStart;

    if (amount > 0) {
      segments.push({ bin, binStart, binEnd, amount });
    }
  }

  return segments;
}

function read(row, accessor) {
  if (typeof accessor === "function") {
    return accessor(row);
  }

  return row?.[accessor];
}

function keyFor(row, groupBy) {
  if (groupBy == null) {
    return "";
  }

  const values = arrayOf(groupBy).map((field) => read(row, field));
  return JSON.stringify(values);
}

function arrayOf(value) {
  if (Array.isArray(value)) {
    return value;
  }

  return value == null ? [] : [value];
}

function numberFrom(value, field) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    throw new TypeError(`cumbin expected a finite number for ${String(field)}`);
  }

  return number;
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

export default cumbin;
