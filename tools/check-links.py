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

And, for the files search engines read rather than people:

  * robots.txt and sitemap.xml exist and point at SITE_URL;
  * sitemap.xml lists exactly the pages that are meant to be indexed — every
    page without <meta name="robots" content="noindex">, and no others;
  * every indexable page declares the rel=canonical that the sitemap claims
    for it.

Those three are the ones that go wrong silently: a page added without a sitemap
entry, or a move to a new domain that updates the HTML and forgets the sitemap,
breaks nothing a browser can see.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urlparse

SITE = Path(__file__).resolve().parent.parent / "site"

# Where the site is published, with the trailing slash. Canonical URLs, the
# sitemap, and robots.txt all have to agree with this; changing it here is what
# turns a move to a custom domain into a checked operation rather than a search
# and replace. Keep in step with the "URL" section of README.md.
SITE_URL = "https://okchan08.github.io/osc2r2-site/"

# Absolute URLs the site is allowed to contain.
ALLOWED_ABSOLUTE = {
    SITE_URL,
    SITE_URL + "og.png",
    SITE_URL + "favicon.svg",
    # The VS Code extension listing. Off-site, so it also survives a move.
    "https://marketplace.visualstudio.com/items?itemName=okchan08.openscenario2",
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
        self.canonical: str | None = None
        self.noindex = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line = self.getpos()[0]
        attr = {name: (value or "") for name, value in attrs}

        if tag == "link" and "canonical" in attr.get("rel", "").lower().split():
            self.canonical = attr.get("href", "").strip()
        elif tag == "meta" and attr.get("name", "").lower() == "robots":
            self.noindex = "noindex" in attr.get("content", "").lower()

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


def parse(page: Path) -> Refs:
    parser = Refs()
    parser.feed(page.read_text(encoding="utf-8"))
    return parser


def check(page: Path, parser: Refs) -> list[str]:
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


def page_url(page: Path) -> str:
    """The public URL of a page under site/, as the sitemap must spell it."""
    rel = page.relative_to(SITE).as_posix()
    if rel.endswith("index.html"):
        # A directory is served by its index.html, and the canonical spelling of
        # a directory keeps the trailing slash.
        rel = rel.removesuffix("index.html")
    return SITE_URL + rel


def check_robots() -> list[str]:
    """robots.txt exists and declares the sitemap at the current SITE_URL."""
    robots = SITE / "robots.txt"
    if not robots.exists():
        return ["site/robots.txt: missing"]

    want = f"Sitemap: {SITE_URL}sitemap.xml"
    lines = robots.read_text(encoding="utf-8").splitlines()
    if not any(line.strip() == want for line in lines):
        return [f'site/robots.txt: no "{want}" line']
    return []


def check_sitemap(parsed: dict[Path, Refs]) -> list[str]:
    """The sitemap lists every indexable page, and only those.

    Indexable means "does not say noindex". 404.html says it, so it stays out;
    anything new that does not say it has to be listed.
    """
    sitemap = SITE / "sitemap.xml"
    if not sitemap.exists():
        return ["site/sitemap.xml: missing"]

    # Read by regex rather than by an XML parser: <loc> is the only element
    # this cares about, and xml.etree needs pyexpat, which is a C extension a
    # broken local Python can be missing. The rest of this tool runs anywhere
    # python3 does, and so should this.
    text = sitemap.read_text(encoding="utf-8")
    listed = {m.strip() for m in re.findall(r"<loc>(.*?)</loc>", text, re.S)}
    if not listed:
        return ["site/sitemap.xml: no <loc> entries"]
    expected = {
        page_url(page) for page, refs in parsed.items() if not refs.noindex
    }

    problems = [
        f"site/sitemap.xml: lists {url}, which is not an indexable page"
        for url in sorted(listed - expected)
    ]
    problems += [
        f"site/sitemap.xml: does not list {url}\n"
        f"    add it, or mark the page noindex if it is not meant to be found"
        for url in sorted(expected - listed)
    ]
    return problems


def check_canonical(page: Path, parser: Refs) -> list[str]:
    """An indexable page names itself as canonical; a noindex page need not."""
    if parser.noindex:
        return []

    rel = page.relative_to(SITE.parent)
    want = page_url(page)
    if parser.canonical is None:
        return [f"{rel}: no <link rel=canonical>; it should be {want}"]
    if parser.canonical != want:
        return [f"{rel}: canonical is {parser.canonical}, expected {want}"]
    return []


def main() -> int:
    pages = sorted(SITE.rglob("*.html"))
    if not pages:
        print(f"no HTML found under {SITE}", file=sys.stderr)
        return 1

    parsed = {page: parse(page) for page in pages}

    problems: list[str] = []
    for page, refs in parsed.items():
        problems.extend(check(page, refs))
        problems.extend(check_canonical(page, refs))
    problems.extend(check_robots())
    problems.extend(check_sitemap(parsed))

    for problem in problems:
        print(problem, file=sys.stderr)

    count = len(pages)
    if problems:
        print(
            f"\n{len(problems)} problem(s) in {count} page(s)",
            file=sys.stderr,
        )
        return 1

    print(f"{count} page(s) checked, no broken references; sitemap agrees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
