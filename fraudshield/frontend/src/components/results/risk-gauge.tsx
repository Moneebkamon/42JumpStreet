import { BAND_META } from "@/lib/format";
import type { Band } from "@/types/scan";

const ARC_LENGTH = Math.PI * 50; // half circle, radius 50

/** Half-circle gauge showing the 0-100 risk score. */
export function RiskGauge({ score, band }: { score: number; band: Band }) {
  const filled = ARC_LENGTH * (Math.min(100, Math.max(0, score)) / 100);
  return (
    <div className="relative mx-auto w-48" role="img" aria-label={`Risk score ${score} out of 100`}>
      <svg viewBox="0 0 120 70" className="w-full">
        <path
          d="M10 60 A50 50 0 0 1 110 60"
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          className="stroke-zinc-200 dark:stroke-zinc-800"
        />
        <path
          d="M10 60 A50 50 0 0 1 110 60"
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${ARC_LENGTH}`}
          className={BAND_META[band].stroke}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center leading-none">
        <span className="text-4xl font-semibold tabular-nums">{score}</span>
        <span className="text-sm text-zinc-500"> / 100</span>
      </div>
    </div>
  );
}
