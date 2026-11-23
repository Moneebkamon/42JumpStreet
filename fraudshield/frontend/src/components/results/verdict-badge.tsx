import { BAND_META } from "@/lib/format";
import type { Band } from "@/types/scan";

export function VerdictBadge({ band }: { band: Band }) {
  return (
    <span className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${BAND_META[band].badge}`}>
      {BAND_META[band].label}
    </span>
  );
}
