import { notFound } from "next/navigation";

// TODO(DELETE LATER - privacy): checking WhatsApp / SMS / email messages is switched off, so this page is hidden.
// The old page is in ./watchlist-view.tsx and ./../../components/user/whatsapp-card.tsx. Delete them together.
export default function WatchlistPage() {
  notFound();
}
