from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

from lxml import etree, html


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = PROJECT_ROOT / "source" / "_posts"
DATA_DIR = PROJECT_ROOT / "source" / "_data"
BASE_URL = "https://m155-b1nb1n.github.io/binbin-blog"
PAGES = (
    ("practicemisc", f"{BASE_URL}/2026/03/20/practicemisc/"),
    ("practiceweb", f"{BASE_URL}/2026/04/17/practiceweb/"),
    ("practiceosint", f"{BASE_URL}/2026/05/22/practiceosint/"),
)


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 Codex blog migration"})
    with urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8")


def inner_html(element: etree._Element) -> str:
    parts = [element.text or ""]
    parts.extend(
        etree.tostring(child, encoding="unicode", method="html")
        for child in element
    )
    return "".join(parts).strip()


def quoted(value: str) -> str:
    # JSON strings are valid YAML strings and preserve Chinese safely.
    return json.dumps(value, ensure_ascii=False)


def local_timestamp(element: etree._Element) -> str:
    match = re.search(
        r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})",
        element.get("title", ""),
    )
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return element.get("datetime", "").replace("T", " ").replace("Z", "")


def extract_post(slug: str, url: str) -> dict[str, object]:
    document = html.fromstring(fetch(url))
    title_candidates = document.xpath(
        "//h1[contains(concat(' ', normalize-space(@class), ' '), ' post-title ')]//text()"
    )
    if not title_candidates:
        title_candidates = document.xpath("//meta[@property='og:title']/@content")
    title = "".join(title_candidates).strip()

    post_meta = document.xpath("//*[@id='post-meta']")
    meta_root = post_meta[0] if post_meta else document
    time_elements = meta_root.xpath(".//time[@datetime]")
    if not time_elements:
        time_elements = document.xpath("//time[@datetime]")
    if not time_elements:
        raise RuntimeError(f"No publish date found for {url}")
    published = time_elements[0]
    date = local_timestamp(published)
    updated_elements = meta_root.xpath(
        ".//time[contains(concat(' ', normalize-space(@class), ' '), ' post-meta-date-updated ')]"
    )
    updated = local_timestamp(updated_elements[0]) if updated_elements else date

    tags = [
        " ".join(text.split())
        for text in document.xpath(
            "//a[contains(concat(' ', normalize-space(@class), ' '), ' post-meta__tags ')]//text()"
        )
        if text.strip()
    ]
    tags = list(dict.fromkeys(tags))
    categories = [
        " ".join(text.split())
        for text in document.xpath(
            "//a[contains(concat(' ', normalize-space(@class), ' '), ' post-meta__categories ')]//text()"
        )
        if text.strip()
    ]
    categories = list(dict.fromkeys(categories))

    article_nodes = document.xpath("//*[@id='article-container']")
    if not article_nodes:
        raise RuntimeError(f"No article body found for {url}")
    body = inner_html(article_nodes[0])
    body = body.replace('src="/img/', 'src="/binbin-blog/img/')
    body = body.replace("src='/img/", "src='/binbin-blog/img/")
    body = body.replace('href="/img/', 'href="/binbin-blog/img/')
    body = body.replace("href='/img/", "href='/binbin-blog/img/")

    plain_text = " ".join(article_nodes[0].text_content().split())
    description = plain_text[:180]

    front_matter = [
        "---",
        f"title: {quoted(title)}",
        f"date: {date}",
        f"updated: {updated}",
        f"description: {quoted(description)}",
    ]
    if tags:
        front_matter.append("tags:")
        front_matter.extend(f"  - {quoted(tag)}" for tag in tags)
    if categories:
        front_matter.append("categories:")
        front_matter.extend(f"  - {quoted(category)}" for category in categories)
    front_matter.extend(["---", ""])

    target = POSTS_DIR / f"{slug}.md"
    target.write_text("\n".join(front_matter) + body + "\n", encoding="utf-8")
    return {
        "slug": slug,
        "title": title,
        "date": date,
        "updated": updated,
        "tags": tags,
        "categories": categories,
        "body_length": len(body),
        "target": str(target),
    }


def extract_links() -> dict[str, object]:
    document = html.fromstring(fetch(f"{BASE_URL}/links/"))
    groups: list[dict[str, object]] = []
    flink_nodes = document.xpath(
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' flink ')]"
    )
    for flink in flink_nodes:
        heading = "".join(flink.xpath("./h2[1]//text()")).strip()
        description = " ".join(
            flink.xpath(
                "./div[contains(concat(' ', normalize-space(@class), ' '), ' flink-desc ')][1]//text()"
            )
        ).strip()
        items = []
        item_nodes = flink.xpath(
            ".//*[contains(concat(' ', normalize-space(@class), ' '), ' flink-list-item ')]"
        )
        for item in item_nodes:
            name = " ".join(
                item.xpath(
                    ".//*[contains(concat(' ', normalize-space(@class), ' '), ' flink-item-name ')]//text()"
                )
            ).strip()
            descr = " ".join(
                item.xpath(
                    ".//*[contains(concat(' ', normalize-space(@class), ' '), ' flink-item-desc ')]//text()"
                )
            ).strip()
            hrefs = ([item.get("href")] if item.get("href") else []) + item.xpath(
                ".//a/@href"
            )
            avatars = item.xpath(".//img/@data-lazy-src | .//img/@src")
            if name and hrefs:
                items.append(
                    {
                        "name": name,
                        "link": hrefs[0],
                        "avatar": avatars[0] if avatars else "",
                        "descr": descr,
                    }
                )
        if heading or items:
            groups.append(
                {
                    "class_name": heading or "友链",
                    "class_desc": description,
                    "link_list": items,
                }
            )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    yaml_lines: list[str] = []
    for group in groups:
        yaml_lines.extend(
            [
                f"- class_name: {quoted(str(group['class_name']))}",
                f"  class_desc: {quoted(str(group['class_desc']))}",
                "  link_list:",
            ]
        )
        for item in group["link_list"]:
            yaml_lines.extend(
                [
                    f"    - name: {quoted(str(item['name']))}",
                    f"      link: {quoted(str(item['link']))}",
                    f"      avatar: {quoted(str(item['avatar']))}",
                    f"      descr: {quoted(str(item['descr']))}",
                ]
            )
    (DATA_DIR / "link.yml").write_text(
        "\n".join(yaml_lines) + "\n", encoding="utf-8"
    )

    links_dir = PROJECT_ROOT / "source" / "links"
    links_dir.mkdir(parents=True, exist_ok=True)
    (links_dir / "index.md").write_text(
        "---\n"
        f"title: {quoted('友链')}\n"
        "type: link\n"
        "comments: false\n"
        "---\n",
        encoding="utf-8",
    )
    return {
        "groups": len(groups),
        "links": sum(len(group["link_list"]) for group in groups),
        "target": str(DATA_DIR / "link.yml"),
    }


def main() -> None:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    extracted = [extract_post(slug, url) for slug, url in PAGES]
    print(
        json.dumps(
            {"posts": extracted, "friends": extract_links()},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
