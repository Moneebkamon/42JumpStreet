// Mirrors backend/app/schemas/feed.py
import type { Band, Reason } from "@/types/scan";

export interface FeedItem {
  domain: string;
  source: string;
  simulated: boolean;
  issued_at: string;
  detected_at: string;
  issue_to_detection_s: number;
  processing_ms: number;
  score: number;
  band: Band;
  action: string;
  brand_id: string;
  brand_name: string;
  prefilter_reasons: string[];
  reasons: Reason[];
  status: string;
}

export interface DiscoveryStats {
  events_processed: number;
  domains_seen: number;
  domains_kept: number;
  pass_through_rate: number;
  detections: number;
  flagged: number;
  avg_processing_ms: number;
  avg_issue_to_detection_s: number;
  by_band: Record<string, number>;
  top_brands: { brand_id: string; brand_name: string; count: number }[];
  simulated: boolean;
  live_events: number;
  last_live_run_at: string | null;
  last_live_detection_at: string | null;
}

export interface CheckedItem {
  domain: string;
  checked_at: string;
  source: string;
  simulated: boolean;
  kept: boolean;
  score: number | null;
  band: string;
  brand_name: string;
}

export interface FeedFilters {
  minScore: number;
  brand: string; // brand id, "" for all
}
