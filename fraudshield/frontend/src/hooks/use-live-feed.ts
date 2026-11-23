"use client";

import { useCallback } from "react";

import { fetchFeed, fetchStats } from "@/lib/api-client";
import type { FeedFilters } from "@/types/feed";

import { usePolling } from "./use-polling";

const REFRESH_MS = 5000;

/** The feed (filtered) and the discovery figures, both refreshed every few seconds. */
export function useLiveFeed(filters: FeedFilters) {
  const { minScore, brand } = filters;
  const feedFetcher = useCallback(
    (signal: AbortSignal) => fetchFeed({ minScore, brand }, signal),
    [minScore, brand],
  );
  const feed = usePolling(feedFetcher, REFRESH_MS);
  const stats = usePolling(fetchStats, REFRESH_MS);
  return { feed, stats };
}
