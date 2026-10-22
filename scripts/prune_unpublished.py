"""Strip the fetched vault down to what the site publishes, before Quartz builds it.

Keeps the notes with 'publish: true' in their frontmatter, plus every file those
notes link to or embed ('[[x]]', '![[x.png]]', '[..](x)'), matched by file name as
Obsidian resolves links. Everything else in content/ is deleted, so unpublished
notes and the images only they use never reach the site (Quartz's ExplicitPublish
filter alone would still copy every attachment).

    python scripts/prune_unpublished.py content
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote

PUBLISH = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
WIKILINK = re.compile(r"!?\[\[([^\]|#^]+)")
MDLINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")


def is_published(text):
    m = PUBLISH.match(text)
    return bool(m and re.search(r"^publish:\s*true\s*$", m.group(1), re.M | re.I))


def main(root):
    root = Path(root)
    files = [p for p in root.rglob("*") if p.is_file()]
    notes = {p: p.read_text(encoding="utf-8", errors="ignore") for p in files if p.suffix == ".md"}
    published = {p for p, text in notes.items() if is_published(text)}

    # every link target named in a published note, as a file name with and without extension
    targets = set()
    for p in published:
        for raw in WIKILINK.findall(notes[p]) + MDLINK.findall(notes[p]):
            name = Path(unquote(raw).strip()).name.lower()
            if name and "://" not in raw:
                targets.add(name)

    keep = set(published)
    for p in files:
        if p.suffix != ".md" and (p.name.lower() in targets or p.stem.lower() in targets):
            keep.add(p)

    for p in files:
        if p not in keep:
            p.unlink()
    for d in sorted((d for d in root.rglob("*") if d.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()

    n_assets = len(keep) - len(published)
    print(f"kept {len(published)} published notes and {n_assets} linked files; "
          f"removed {len(files) - len(keep)} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "content")
