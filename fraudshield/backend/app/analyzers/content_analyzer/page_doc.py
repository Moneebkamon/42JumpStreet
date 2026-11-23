"""Parse a PageSnapshot once so every content analyzer can share the result."""
from dataclasses import dataclass

from bs4 import BeautifulSoup

from app.analyzers.url_analyzer.normalizer import NormalizedURL, normalize
from app.sandbox.snapshot import PageSnapshot

MAX_TEXT_CHARS = 20_000
_HIDDEN_PARENTS = {"script", "style", "noscript", "template", "head", "title"}


@dataclass
class PageDoc:
    snapshot: PageSnapshot
    soup: BeautifulSoup
    text: str  # visible text only
    title: str
    final: NormalizedURL  # the URL the browser ended up on


def build_page_doc(snapshot: PageSnapshot, fallback: NormalizedURL) -> PageDoc:
    soup = BeautifulSoup(snapshot.html, "html.parser")
    pieces = (s.strip() for s in soup.find_all(string=True) if s.parent.name not in _HIDDEN_PARENTS)
    text = " ".join(p for p in pieces if p)[:MAX_TEXT_CHARS]
    title = snapshot.title or (soup.title.get_text(strip=True) if soup.title else "")
    try:
        final = normalize(snapshot.final_url)
    except ValueError:
        final = fallback
    return PageDoc(snapshot=snapshot, soup=soup, text=text, title=title, final=final)
