"""Greenhouse public job-board adapter.

This adapter only reads the documented public board endpoint. It does not
scrape pages or submit applications.
"""
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class DiscoveredJob:
    external_id: str
    title: str
    description: str
    company: str | None
    location: str | None
    source_url: str | None


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def strip_html(value: str | None) -> str:
    parser = _TextExtractor()
    parser.feed(value or "")
    return parser.text()


def fetch_greenhouse_jobs(board_token: str, timeout: int = 15) -> list[DiscoveredJob]:
    """Fetch published jobs from a Greenhouse board token."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "ResumeAgent/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)

    jobs: list[DiscoveredJob] = []
    for item in payload.get("jobs", []):
        description = strip_html(item.get("content"))
        if not item.get("id") or not item.get("title") or not description:
            continue
        location = (item.get("location") or {}).get("name")
        jobs.append(
            DiscoveredJob(
                external_id=str(item["id"]),
                title=item["title"],
                description=description,
                company=None,
                location=location,
                source_url=item.get("absolute_url"),
            )
        )
    return jobs
