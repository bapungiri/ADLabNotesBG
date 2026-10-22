"""Strip the fetched vault down to what the site publishes, before Quartz builds it.

Publishes every note in the folder(s) given (default 'adlab notes') and nothing
else, plus every file those notes link to or embed ('[[x]]', '![[x.png]]',
'[..](x)'), matched by file name as Obsidian resolves links. Everything else in
content/ is deleted, so other notes and the images only they use never reach the
site. The published folder's contents are moved to the site root, so pages keep
short URLs ('/adlab-data-analysis', not '/adlab-notes/adlab-data-analysis').
A note can still be hidden with 'draft: true' in its frontmatter.

    python scripts/prune_unpublished.py content ["adlab notes" ...]
"""

import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

WIKILINK = re.compile(r"!?\[\[([^\]|#^]+)")
MDLINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")


def main(root, folders):
    root = Path(root)
    folders = [root / f for f in folders]
    files = [p for p in root.rglob("*") if p.is_file()]
    site_index = root / "index.md"  # the home page, copied in by the workflow
    published = {
        p for p in files
        if p.suffix == ".md" and (p == site_index or any(f in p.parents for f in folders))
    }

    # every link target named in a published note, as a file name with and without extension
    targets = set()
    for p in published:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for raw in WIKILINK.findall(text) + MDLINK.findall(text):
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

    # published folders' contents go to the site root (short URLs, flat explorer)
    for f in folders:
        if not f.is_dir():
            continue
        for p in sorted(f.rglob("*")):
            if p.is_file():
                dest = root / p.relative_to(f)
                if dest.exists():
                    sys.exit(f"{p} would overwrite {dest}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), dest)

    for d in sorted((d for d in root.rglob("*") if d.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()

    n_notes = len(published) - (site_index in published)
    print(f"published {n_notes} notes from {[f.name for f in folders]} and "
          f"{len(keep) - len(published)} linked files; removed {len(files) - len(keep)} files")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0] if args else "content", args[1:] or ["adlab notes"])
