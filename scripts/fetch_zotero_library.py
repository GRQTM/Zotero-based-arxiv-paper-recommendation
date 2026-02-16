#!/usr/bin/env python3
"""Fetch all readable Zotero items and store them as structured JSON."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request


API_BASE = "https://api.zotero.org"
PAGE_SIZE = 100
RETRY_STATUS = {429, 500, 502, 503, 504}
SKIP_TYPES = {"attachment", "note", "annotation"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def extract_user_id(payload: Any) -> int | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key.lower() == "userid" and isinstance(value, int):
                return value
            nested = extract_user_id(value)
            if nested is not None:
                return nested
    elif isinstance(payload, list):
        for value in payload:
            nested = extract_user_id(value)
            if nested is not None:
                return nested
    return None


def request_json(url: str, headers: dict[str, str], endpoint_name: str, max_retries: int = 5) -> Any:
    for attempt in range(1, max_retries + 1):
        req = request.Request(url=url, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            should_retry = exc.code in RETRY_STATUS and attempt < max_retries
            if should_retry:
                retry_after = exc.headers.get("Retry-After") or exc.headers.get("Backoff")
                delay = int(retry_after) if (retry_after and retry_after.isdigit()) else attempt * 2
                time.sleep(delay)
                continue
            body = exc.read().decode("utf-8", errors="replace")[:200]
            raise RuntimeError(f"HTTP {exc.code} from {endpoint_name}: {body}") from exc
        except error.URLError as exc:
            if attempt >= max_retries:
                raise RuntimeError(f"Network error calling {endpoint_name}: {exc}") from exc
            time.sleep(attempt * 2)
    raise RuntimeError(f"Failed to request {endpoint_name}")


def get_api_key() -> str:
    env_value = os.environ.get("ZOTERO_API_KEY", "").strip()
    if env_value:
        return env_value
    raise RuntimeError("Zotero API key missing. Set ZOTERO_API_KEY.")


def resolve_user_id(api_key: str) -> int:
    headers = {
        "Zotero-API-Key": api_key,
        "Zotero-API-Version": "3",
        "Accept": "application/json",
    }
    key_url = f"{API_BASE}/keys/{api_key}"
    payload = request_json(key_url, headers=headers, endpoint_name="zotero_key_lookup")
    user_id = extract_user_id(payload)
    if user_id is None:
        raise RuntimeError(
            "Could not resolve userID from Zotero key metadata. "
            "Use a user library key with read permission."
        )
    return user_id


def normalize_creators(creators: list[dict[str, Any]] | None) -> list[str]:
    if not creators:
        return []
    names: list[str] = []
    for creator in creators:
        display_name = creator.get("name")
        if isinstance(display_name, str) and display_name.strip():
            names.append(display_name.strip())
            continue
        first = str(creator.get("firstName", "")).strip()
        last = str(creator.get("lastName", "")).strip()
        full = f"{first} {last}".strip()
        if full:
            names.append(full)
    return names


def normalize_tags(tags: list[dict[str, Any]] | None) -> list[str]:
    if not tags:
        return []
    output: list[str] = []
    for tag in tags:
        value = tag.get("tag")
        if isinstance(value, str) and value.strip():
            output.append(value.strip())
    return output


def filter_item(raw_item: dict[str, Any]) -> dict[str, Any] | None:
    data = raw_item.get("data", {})
    item_type = str(data.get("itemType", "")).strip()
    if item_type in SKIP_TYPES:
        return None

    title = str(data.get("title", "")).strip()
    if not title:
        return None

    abstract = str(data.get("abstractNote", "")).strip()
    creators = normalize_creators(data.get("creators"))
    tags = normalize_tags(data.get("tags"))

    return {
        "key": raw_item.get("key"),
        "version": raw_item.get("version"),
        "itemType": item_type,
        "title": title,
        "authors": creators,
        "abstract": abstract,
        "date": data.get("date"),
        "publicationTitle": data.get("publicationTitle"),
        "publisher": data.get("publisher"),
        "doi": data.get("DOI"),
        "url": data.get("url"),
        "language": data.get("language"),
        "tags": tags,
        "extra": data.get("extra"),
    }


def fetch_all_items(api_key: str, user_id: int) -> list[dict[str, Any]]:
    headers = {
        "Zotero-API-Key": api_key,
        "Zotero-API-Version": "3",
        "Accept": "application/json",
    }
    collected: list[dict[str, Any]] = []
    start = 0

    while True:
        query = parse.urlencode(
            {
                "format": "json",
                "limit": PAGE_SIZE,
                "start": start,
                "sort": "dateModified",
                "direction": "desc",
                "include": "data",
            }
        )
        url = f"{API_BASE}/users/{user_id}/items?{query}"
        payload = request_json(url, headers=headers, endpoint_name="zotero_items")
        if not isinstance(payload, list) or not payload:
            break
        collected.extend(payload)
        start += len(payload)
        if len(payload) < PAGE_SIZE:
            break
    return collected


def write_summary(summary_path: Path, payload: dict[str, Any]) -> None:
    items = payload["items"]
    type_counter = Counter(item.get("itemType", "unknown") for item in items)
    venue_counter = Counter(item.get("publicationTitle") for item in items if item.get("publicationTitle"))
    tag_counter = Counter(tag for item in items for tag in item.get("tags", []))

    lines: list[str] = []
    lines.append("# Zotero Library Snapshot")
    lines.append("")
    lines.append(f"- Generated (UTC): {payload['generated_at_utc']}")
    lines.append(f"- User ID: {payload['user_id']}")
    lines.append(f"- Readable items: {payload['total_items']}")
    lines.append("")
    lines.append("## Top Item Types")
    for item_type, count in type_counter.most_common(15):
        lines.append(f"- {item_type}: {count}")
    lines.append("")
    lines.append("## Top Venues")
    for venue, count in venue_counter.most_common(15):
        lines.append(f"- {venue}: {count}")
    lines.append("")
    lines.append("## Top Tags")
    for tag, count in tag_counter.most_common(25):
        lines.append(f"- {tag}: {count}")
    lines.append("")
    lines.append("## Sample Titles")
    for item in items[:30]:
        lines.append(f"- {item['title']}")
    summary_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Zotero library items into JSON.")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--summary", required=True, help="Output Markdown summary path")
    parser.add_argument("--user-id", type=int, default=None, help="Optional explicit Zotero user ID")
    args = parser.parse_args()

    output_path = Path(args.output)
    summary_path = Path(args.summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    api_key = get_api_key()
    user_id = args.user_id if args.user_id is not None else resolve_user_id(api_key)
    raw_items = fetch_all_items(api_key=api_key, user_id=user_id)

    filtered: list[dict[str, Any]] = []
    for raw in raw_items:
        item = filter_item(raw)
        if item is not None:
            filtered.append(item)

    payload = {
        "generated_at_utc": utc_now_iso(),
        "user_id": user_id,
        "total_items": len(filtered),
        "items": filtered,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(summary_path=summary_path, payload=payload)

    print(f"Wrote {len(filtered)} items to {output_path}")
    print(f"Wrote summary to {summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
