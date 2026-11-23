"""What the sandbox hands back after loading a page. Plain data, no browser objects."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PageSnapshot:
    requested_url: str
    final_url: str
    status: int | None
    title: str
    html: str
    redirect_chain: tuple[str, ...]  # requested URL first, final URL last
    network_hosts: tuple[str, ...] = ()  # hosts the page was allowed to contact
    blocked_hosts: tuple[str, ...] = ()  # hosts the guard refused (private/internal or non-web)
    truncated: bool = False
