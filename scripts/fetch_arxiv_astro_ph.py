#!/usr/bin/env python3
"""Fetch astro-ph submissions from arXiv over a lookback window."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import parse, request
from xml.etree import ElementTree


ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "opensearch": "http://a9.com/-/spec/opensearch/1.1/"}
DEFAULT_BATCH = 200
DEFAULT_MAX_SCAN = 2000

ASTRO_CATEGORIES = [
    "astro-ph",
    "astro-ph.CO",
    "astro-ph.EP",
    "astro-ph.GA",
    "astro-ph.HE",
    "astro-ph.IM",
    "astro-ph.SR",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_text(text: str) -> str:
    return " ".join(text.split())


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def build_query(categories: list[str]) -> str:
    return " OR ".join([f"cat:{cat}" for cat in categories])


def fetch_batch(query: str, start: int, max_results: int) -> str:
    params = {
        "search_query": query,
        "start": str(start),
        "max_results": str(max_results),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{parse.urlencode(params)}"
    req = request.Request(url=url, headers={"User-Agent": "astro-ph-recommender/1.0"}, method="GET")
    with request.urlopen(req, timeout=90) as response:
        return response.read().decode("utf-8")


def parse_entries(feed_xml: str) -> tuple[int, list[dict[str, Any]]]:
    root = ElementTree.fromstring(feed_xml)
    total_node = root.find("opensearch:totalResults", namespaces=ATOM_NS)
    total = int(total_node.text) if (total_node is not None and total_node.text) else 0

    entries: list[dict[str, Any]] = []
    for entry in root.findall("atom:entry", namespaces=ATOM_NS):
        entry_id = clean_text(entry.findtext("atom:id", default="", namespaces=ATOM_NS))
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
        summary = clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
        published = clean_text(entry.findtext("atom:published", default="", namespaces=ATOM_NS))
        updated = clean_text(entry.findtext("atom:updated", default="", namespaces=ATOM_NS))

        authors = []
        for author in entry.findall("atom:author", namespaces=ATOM_NS):
            name = clean_text(author.findtext("atom:name", default="", namespaces=ATOM_NS))
            if name:
                authors.append(name)

        categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", namespaces=ATOM_NS)]
        categories = [cat for cat in categories if cat]

        arxiv_id = entry_id.rstrip("/").split("/")[-1] if entry_id else ""
        entries.append(
            {
                "id": arxiv_id,
                "url": entry_id,
                "title": title,
                "authors": authors,
                "summary": summary,
                "published": published,
                "updated": updated,
                "categories": categories,
            }
        )
    return total, entries


def fetch_recent_astro_ph(days: int, batch_size: int, max_scan: int) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = build_query(ASTRO_CATEGORIES)
    all_recent: dict[str, dict[str, Any]] = {}
    total_scanned = 0
    total_reported = None
    start = 0

    while start < max_scan:
        xml_text = fetch_batch(query=query, start=start, max_results=batch_size)
        reported, entries = parse_entries(xml_text)
        if total_reported is None:
            total_reported = reported
        if not entries:
            break

        older_only = True
        for item in entries:
            total_scanned += 1
            published = parse_time(item["published"])
            if published >= cutoff:
                older_only = False
                all_recent[item["id"]] = item
        if older_only:
            break

        start += len(entries)
        if total_reported is not None and start >= total_reported:
            break

    recent_items = sorted(all_recent.values(), key=lambda x: x["published"], reverse=True)
    return {
        "generated_at_utc": utc_now_iso(),
        "lookback_days": days,
        "cutoff_utc": cutoff.replace(microsecond=0).isoformat(),
        "categories": ASTRO_CATEGORIES,
        "query": query,
        "total_entries_scanned": total_scanned,
        "total_recent_entries": len(recent_items),
        "items": recent_items,
    }


def write_summary(summary_path: Path, payload: dict[str, Any]) -> None:
    category_counter = Counter(cat for item in payload["items"] for cat in item.get("categories", []))
    lines: list[str] = []
    lines.append("# arXiv astro-ph Last 2 Days")
    lines.append("")
    lines.append(f"- Generated (UTC): {payload['generated_at_utc']}")
    lines.append(f"- Lookback days: {payload['lookback_days']}")
    lines.append(f"- Cutoff (UTC): {payload['cutoff_utc']}")
    lines.append(f"- Entries scanned: {payload['total_entries_scanned']}")
    lines.append(f"- Recent astro-ph entries: {payload['total_recent_entries']}")
    lines.append("")
    lines.append("## Category Counts")
    for cat, count in category_counter.most_common():
        lines.append(f"- {cat}: {count}")
    lines.append("")
    lines.append("## Sample Titles")
    for item in payload["items"][:30]:
        lines.append(f"- [{item['id']}] {item['title']}")
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch recent astro-ph papers from arXiv API.")
    parser.add_argument("--days", type=int, default=2, help="Lookback window in days")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH, help="arXiv API batch size")
    parser.add_argument("--max-scan", type=int, default=DEFAULT_MAX_SCAN, help="Max entries to scan")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--summary", required=True, help="Output Markdown summary path")
    args = parser.parse_args()

    output_path = Path(args.output)
    summary_path = Path(args.summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    payload = fetch_recent_astro_ph(days=args.days, batch_size=args.batch_size, max_scan=args.max_scan)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(summary_path, payload)

    print(f"Wrote {payload['total_recent_entries']} entries to {output_path}")
    print(f"Wrote summary to {summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        raise
