#!/usr/bin/env python3
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = "https://eegii.dev"
EXTERNAL = ("http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:")
SKIP_DIRS = {".git", ".github", ".idea", "node_modules", "_site"}


class Refs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.found.append((tag, value))


def html_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".html"):
                yield os.path.join(base, name)


def resolve(page, ref):
    path = urlsplit(ref).path
    if not path:
        return None
    if path.startswith("/"):
        target = os.path.join(ROOT, path.lstrip("/"))
    else:
        target = os.path.join(os.path.dirname(page), path)
    target = os.path.normpath(target)
    if os.path.isdir(target):
        target = os.path.join(target, "index.html")
    return target


def check_refs(errors):
    for page in sorted(html_files()):
        rel_page = os.path.relpath(page, ROOT)
        parser = Refs()
        with open(page, encoding="utf-8") as handle:
            parser.feed(handle.read())
        for tag, ref in parser.found:
            if ref.startswith(EXTERNAL) or ref.startswith(("#", "?")):
                continue
            target = resolve(page, ref)
            if target is None:
                continue
            if not os.path.exists(target):
                errors.append(f"{rel_page}: <{tag}> {ref} -> missing {os.path.relpath(target, ROOT)}")


def check_sitemap(errors):
    sitemap = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(sitemap):
        errors.append("sitemap.xml is missing")
        return
    with open(sitemap, encoding="utf-8") as handle:
        body = handle.read()
    for loc in re.findall(r"<loc>\s*(.*?)\s*</loc>", body):
        if not loc.startswith(SITE):
            errors.append(f"sitemap.xml: {loc} is outside {SITE}")
            continue
        path = urlsplit(loc).path
        target = os.path.normpath(os.path.join(ROOT, path.lstrip("/")))
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.exists(target):
            errors.append(f"sitemap.xml: {loc} -> missing {os.path.relpath(target, ROOT)}")


def check_required(errors):
    for name in ("CNAME", "robots.txt", "sitemap.xml", "index.html", "assets/css/style.css"):
        if not os.path.exists(os.path.join(ROOT, name)):
            errors.append(f"required file missing: {name}")
    cname = os.path.join(ROOT, "CNAME")
    if os.path.exists(cname):
        with open(cname, encoding="utf-8") as handle:
            value = handle.read().strip()
        if value != "eegii.dev":
            errors.append(f"CNAME is '{value}', expected 'eegii.dev'")


def main():
    errors = []
    check_refs(errors)
    check_sitemap(errors)
    check_required(errors)
    if errors:
        print(f"site check failed with {len(errors)} problem(s):")
        for line in errors:
            print(f"  - {line}")
        return 1
    print("site check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
