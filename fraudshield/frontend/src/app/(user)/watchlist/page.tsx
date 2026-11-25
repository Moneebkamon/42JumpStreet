import { WatchlistView } from "./watchlist-view";

// Members' pages render only after the session check in the browser, so there is nothing to validate for instant navigation.
export const instant = false;

export default function WatchlistPage() {
  return <WatchlistView />;
}
