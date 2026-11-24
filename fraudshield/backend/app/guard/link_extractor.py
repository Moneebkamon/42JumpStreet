"""Pull links out of a chat or SMS text. Only extracts; never opens or expands them."""
import re

MAX_LINKS = 5
_SCHEME = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
_WWW = re.compile(r"(?<![\w/@.])www\.[^\s<>\"'`]+", re.IGNORECASE)
_BARE = re.compile(r"(?<![\w/@.:-])(?:[a-z0-9-]{1,63}\.)+[a-z]{2,24}(?:/[^\s<>\"'`]*)?(?![\w@])", re.IGNORECASE)
_FILE_EXT = {"txt", "pdf", "jpg", "jpeg", "png", "gif", "doc", "docx", "xls", "xlsx", "zip", "mp3", "mp4", "js", "py",
             "html", "htm", "css", "json", "csv", "exe", "apk", "md"}
_TRAIL = ".,;:!?)]}>\"'"


def extract_links(text: str) -> list[str]:
    """Unique links in order of appearance, trailing punctuation removed, at most MAX_LINKS."""
    found: list[tuple[int, str]] = []
    taken: list[tuple[int, int]] = []

    def add(m: re.Match) -> None:
        if any(s <= m.start() < e for s, e in taken):
            return
        taken.append((m.start(), m.end()))
        found.append((m.start(), m.group(0).rstrip(_TRAIL)))

    for m in _SCHEME.finditer(text):
        add(m)
    for m in _WWW.finditer(text):
        add(m)
    for m in _BARE.finditer(text):
        tld = m.group(0).split("/")[0].rsplit(".", 1)[-1].lower()
        if tld not in _FILE_EXT:
            add(m)
    out: list[str] = []
    for _, link in sorted(found):
        if link and link not in out:
            out.append(link)
    return out[:MAX_LINKS]
