"use client";

import type { FeedFilters } from "@/types/feed";

const SCORE_OPTIONS = [
  { value: 0, label: "All scored domains" },
  { value: 30, label: "Suspicious and above (30+)" },
  { value: 60, label: "High risk and above (60+)" },
];

const SELECT =
  "rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900";

export function FeedFiltersBar({
  value,
  brands,
  onChange,
}: {
  value: FeedFilters;
  brands: { brand_id: string; brand_name: string }[];
  onChange: (next: FeedFilters) => void;
}) {
  return (
    <div className="flex flex-wrap gap-3">
      <label className="space-y-1 text-xs text-zinc-500">
        <span>Risk</span>
        <select
          className={`${SELECT} block`}
          value={value.minScore}
          onChange={(e) => onChange({ ...value, minScore: Number(e.target.value) })}
        >
          {SCORE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <label className="space-y-1 text-xs text-zinc-500">
        <span>Impersonated brand</span>
        <select
          className={`${SELECT} block`}
          value={value.brand}
          onChange={(e) => onChange({ ...value, brand: e.target.value })}
        >
          <option value="">All brands</option>
          {brands.map((b) => (
            <option key={b.brand_id} value={b.brand_id}>
              {b.brand_name}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
