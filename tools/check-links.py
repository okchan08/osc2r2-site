#!/usr/bin/env python3
"""Check the published site for broken references.

    python3 tools/check-links.py

What it verifies, for every .html file under site/:

  * every in-page #fragment resolves to an id on the same page (the nav and the
    skip link are the whole navigation model, so a stale one is a dead end);
  * every relative href/src/srcset resolves to a file that exists on disk, with
    a case-sensitive check — macOS will happily serve Style.css locally and
    GitHub Pages will not;
  * no id is declared twice;
  * every absolute http(s) URL is one of the few that are supposed to exist.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urlparse

SITE = Path(__file__).resolve().parent.parent / "site"

# Absolute URLs the site is allowed to contain. Keep in step with the "URL"
# section of README.md.
ALLOWED_ABSOLUTE = {
    "https://okchan08.github.io/osc2r2-site/",
    "https://okchan08.github.io/osc2r2-site/og.png",
    "https://okchan08.github.io/osc2r2-site/favicon.svg",
    # The contact route. These live on github.com rather than the Pages site, so
    # unlike the four above they survive a move to a custom domain.
    "https://github.com/okchan08/osc2r2-site/issues",
    "https://github.com/okchan08/osc2r2-site/issues/new/choose",
    "https://github.com/okchan08/osc2r2-site/security/advisories/new",
}

# Attributes that name another resource, per tag.
URL_ATTRS = {"href", "src", "poster"}


class Refs(HTMLParser):
    """Collects ids and outgoing references, with line numbers for the report."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: dict[str, int] = {}
        self.duplicate_ids: list[tuple[str, int]] = []
        self.refs: list[tuple[str, int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line = self.getpos()[0]
        for name, value in attrs:
            if value is None:
                continue
            if name == "id":
                if value in self.ids:
                    self.duplicate_ids.append((value, line))
                else:
                    self.ids[value] = line
            elif name in URL_ATTRS:
                self.refs.append((value.strip(), line))
            elif name == "srcset":
                # "a.png 1x, b.png 2x" — take the URL out of each candidate.
                for candidate in value.split(","):
                    parts = candidate.split()
                    if parts:
                        self.refs.append((parts[0], line))


def resolve_case_sensitively(path: Path) -> bool:
    """True if `path` exists with exactly this spelling.

    Path.exists() is case-insensitive on macOS and on Windows, which is the
    difference between a check that passes on a laptop and a page that breaks
    once Pages serves it off a case-sensitive filesystem.
    """
    if not path.exists():
        return False
    current = path.resolve()
    for part in reversed(path.relative_to(SITE).parts):
        siblings = {p.name for p in current.parent.iterdir()}
        if part not in siblings:
            return False
        current = current.parent
    return True


def check(page: Path) -> list[str]:
    parser = Refs()
    parser.feed(page.read_text(encoding="utf-8"))
    rel = page.relative_to(SITE.parent)
    problems: list[str] = []

    for dupe, line in parser.duplicate_ids:
        problems.append(f'{rel}:{line}: id "{dupe}" is declared more than once')

    for ref, line in parser.refs:
        if not ref or ref.startswith(("mailto:", "tel:", "data:", "javascript:")):
            continue

        parsed = urlparse(ref)

        if parsed.scheme in ("http", "https"):
            if ref not in ALLOWED_ABSOLUTE:
                problems.append(
                    f"{rel}:{line}: absolute URL not in ALLOWED_ABSOLUTE: {ref}\n"
                    f"    add it to tools/check-links.py and to README.md's URL "
                    f"section if it is intended"
                )
            continue

        target, fragment = urldefrag(ref)

        if not target:
            # Pure "#id" reference: must exist on this page.
            if fragment and fragment not in parser.ids:
                problems.append(f"{rel}:{line}: no element with id \"{fragment}\"")
            continue

        if target.startswith("/"):
            # Root-relative. Only 404.html is allowed these, and only because it
            # is served from paths that make relative URLs meaningless.
            if page.name != "404.html":
                problems.append(
                    f"{rel}:{line}: root-relative URL hardcodes the Pages "
                    f"subpath: {ref}"
                )
            continue

        if target.endswith("/"):
            # A directory link ("./") resolves to its index.html.
            candidate = (page.parent / unquote(target) / "index.html").resolve()
        else:
            candidate = (page.parent / unquote(target)).resolve()

        try:
            candidate.relative_to(SITE)
        except ValueError:
            problems.append(f"{rel}:{line}: reference escapes site/: {ref}")
            continue

        if not resolve_case_sensitively(candidate):
            problems.append(
                f"{rel}:{line}: {ref} → missing "
                f"{candidate.relative_to(SITE.parent)}"
            )

    return problems


def main() -> int:
    pages = sorted(SITE.rglob("*.html"))
    if not pages:
        print(f"no HTML found under {SITE}", file=sys.stderr)
        return 1

    problems: list[str] = []
    for page in pages:
        problems.extend(check(page))

    for problem in problems:
        print(problem, file=sys.stderr)

    count = len(pages)
    if problems:
        print(
            f"\n{len(problems)} problem(s) in {count} page(s)",
            file=sys.stderr,
        )
        return 1

    print(f"{count} page(s) checked, no broken references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
