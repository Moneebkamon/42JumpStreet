const SCHEME = /https?:\/\/[^\s<>"'`]+/gi;
const WWW = /(?<![\w/@.])www\.[^\s<>"'`]+/gi;
const BARE = /(?<![\w/@.:-])(?:[a-z0-9-]{1,63}\.)+[a-z]{2,24}(?:\/[^\s<>"'`]*)?(?![\w@])/gi;
const FILE_EXT = new Set(["txt", "pdf", "jpg", "jpeg", "png", "gif", "doc", "docx", "xls", "xlsx", "zip", "mp3", "mp4", "js", "py", "html", "htm", "css", "json", "csv", "exe", "apk", "md"]);
const TRAIL = /[.,;:!?)\]}>"']+$/;

/** Links in shared text, in order, without duplicates (at most `max`). Only extracts: never opens them. */
export function extractLinks(text: string, max = 3): string[] {
  const found: { at: number; end: number; link: string }[] = [];
  const add = (m: RegExpMatchArray) => {
    const at = m.index ?? 0;
    if (found.some((f) => at >= f.at && at < f.end)) return;
    found.push({ at, end: at + m[0].length, link: m[0].replace(TRAIL, "") });
  };
  for (const m of text.matchAll(SCHEME)) add(m);
  for (const m of text.matchAll(WWW)) add(m);
  for (const m of text.matchAll(BARE)) {
    const tld = m[0].split("/")[0].split(".").pop()?.toLowerCase() ?? "";
    if (!FILE_EXT.has(tld)) add(m);
  }
  const out: string[] = [];
  for (const f of found.sort((a, b) => a.at - b.at)) if (f.link && !out.includes(f.link)) out.push(f.link);
  return out.slice(0, max);
}
