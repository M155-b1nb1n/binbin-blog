from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from lxml import html


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = PROJECT_ROOT / "public"
BASE_URL = "https://m155-b1nb1n.github.io/binbin-blog"
POST_PATHS = (
    "2026/03/20/practicemisc/",
    "2026/04/17/practiceweb/",
    "2026/05/22/practiceosint/",
)


def fetch_document(url: str):
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 Codex blog verifier"})
    with urlopen(request, timeout=90) as response:
        return html.fromstring(response.read())


def file_document(path: Path):
    return html.fromstring(path.read_bytes())


def article_snapshot(document) -> dict[str, object]:
    nodes = document.xpath("//*[@id='article-container']")
    if not nodes:
        raise RuntimeError("Missing #article-container")
    article = nodes[0]
    return {
        "text": " ".join(article.text_content().split()),
        "images": sorted(article.xpath(".//img/@src")),
    }


def friend_snapshot(document) -> list[tuple[str, str]]:
    result = []
    items = document.xpath(
        "//*[contains(concat(' ', normalize-space(@class), ' '), ' flink-list-item ')]"
    )
    for item in items:
        name = " ".join(
            item.xpath(
                ".//*[contains(concat(' ', normalize-space(@class), ' '), ' flink-item-name ')]//text()"
            )
        ).strip()
        hrefs = ([item.get("href")] if item.get("href") else []) + item.xpath(
            ".//a/@href"
        )
        if name and hrefs:
            result.append((name, hrefs[0].rstrip("/")))
    return sorted(result)


def local_target(url_path: str) -> Path:
    relative = unquote(urlsplit(url_path).path.removeprefix("/binbin-blog/"))
    if not relative or relative.endswith("/"):
        relative += "index.html"
    return PUBLIC_DIR / Path(relative)


def verify_internal_links() -> tuple[list[str], list[str]]:
    missing: set[str] = set()
    wrong_root: set[str] = set()
    for html_path in PUBLIC_DIR.rglob("*.html"):
        document = file_document(html_path)
        for value in document.xpath("//@href | //@src"):
            if value.startswith("/binbin-blog/"):
                if not local_target(value).is_file():
                    missing.add(value)
            elif value.startswith("/") and not value.startswith("//"):
                wrong_root.add(value)
    return sorted(missing), sorted(wrong_root)


def main() -> int:
    post_results = []
    for path in POST_PATHS:
        legacy = article_snapshot(fetch_document(f"{BASE_URL}/{path}"))
        rebuilt = article_snapshot(file_document(PUBLIC_DIR / path / "index.html"))
        post_results.append(
            {
                "path": path,
                "same_text": legacy["text"] == rebuilt["text"],
                "same_images": legacy["images"] == rebuilt["images"],
                "text_length": len(rebuilt["text"]),
                "images": rebuilt["images"],
            }
        )

    old_friends = friend_snapshot(fetch_document(f"{BASE_URL}/links/"))
    new_friends = friend_snapshot(file_document(PUBLIC_DIR / "links" / "index.html"))
    missing, wrong_root = verify_internal_links()
    report = {
        "posts": post_results,
        "friends": {
            "same": old_friends == new_friends,
            "legacy": old_friends,
            "rebuilt": new_friends,
        },
        "internal_links": {"missing": missing, "wrong_root": wrong_root},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    posts_ok = all(item["same_text"] and item["same_images"] for item in post_results)
    return 0 if posts_ok and old_friends == new_friends and not missing and not wrong_root else 1


if __name__ == "__main__":
    sys.exit(main())
