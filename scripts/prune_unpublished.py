"""Turn the fetched vault into the site's content/, before Quartz builds it.

1. Publish every note in the folder given (default 'adlab notes') and nothing
   else, plus every file those notes link to or embed ('[[x]]', '![[x.png]]',
   '[..](x)'), matched by file name as Obsidian resolves links. Everything else
   is deleted, so other notes and the images only they use never reach the site.
2. Move the folder's contents to the site root, so URLs stay short
   ('/adlab-data-analysis') while its subfolders become sections.
3. Shorten page titles on the site only: 'adlab model fitting' is shown as
   'model fitting' (the vault keeps the prefix, which keeps names unique there).
4. Subfolders such as '3 Models' get a folder page titled 'Models'; the number
   only orders the sections (see the explorer sortFn in quartz.layout.ts).
5. The note named by --home (default 'ADLab MOC') becomes the home page; links
   to it still work through an alias.
6. List callouts (the Obsidian List Callouts plugin: '- ? **Questions:**'
   with indented bullets under it) become Quartz callouts, coloured by marker
   ('> [!question] Questions' with the bullets inside). Markers on indented
   lines are just removed; Quartz would show them as text.

A note can be hidden with 'draft: true' in its frontmatter.

    python scripts/prune_unpublished.py content ["adlab notes"] [--home "ADLab MOC"]
"""

import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

WIKILINK = re.compile(r"!?\[\[([^\]|#^]+)")
MDLINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)")
FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.S)
PREFIX = re.compile(r"^adlab\s+", re.I)
SECTION_NUMBER = re.compile(r"^\d+\s+")
# marker characters configured in the vault's List Callouts plugin, and the
# Quartz callout type closest to each marker's colour there
CALLOUT_TYPE = {"?": "question", "~": "example", "!": "danger", "@": "tip",
                "$": "success", "&": "warning", "+": "quote", "--": "note"}
MARKER = r"(?:--|[&?!~@$+])"
TOP_CALLOUT = re.compile(rf"^[-*+][ \t]+({MARKER})[ \t]+(.*)$")
LIST_CALLOUT = re.compile(rf"^(\s*[-*+]\s+){MARKER}[ \t]+", re.M)


def list_callouts_to_quartz(text):
    """'- ? **Questions:**' plus its indented lines -> '> [!question] Questions'
    with those lines, dedented, inside the callout."""
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        m = TOP_CALLOUT.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        title = re.sub(r"^\*\*(.*?)\*\*", r"\1", m.group(2).strip()).rstrip(":").strip()
        body = []
        i += 1
        while i < len(lines) and lines[i][:1] in (" ", "\t") and lines[i].strip():
            body.append(lines[i])
            i += 1
        indent = min((len(b) - len(b.lstrip()) for b in body), default=0)
        if out and out[-1].strip():
            out.append("")
        out.append(f"> [!{CALLOUT_TYPE[m.group(1)]}] {title}")
        out.extend(f"> {b[indent:]}" for b in body)
        out.append("")
    return "\n".join(out)
HOME_TITLE = "ADLab"


def set_frontmatter(path, **fields):
    """Add fields to a note's frontmatter unless it already has them."""
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    front, body = (m.group(1), text[m.end():]) if m else ("", text)
    lines = [front] if front.strip() else []
    for key, value in fields.items():
        if not re.search(rf"^{key}\s*:", front, re.M):
            lines.append(f"{key}: {value}")
    path.write_text("---\n" + "\n".join(lines) + "\n---\n" + body, encoding="utf-8")


def quote(s):
    return '"' + s.replace('"', '\\"') + '"'


def main(root, folder, home):
    root = Path(root)
    folder = root / folder
    files = [p for p in root.rglob("*") if p.is_file()]
    published = {p for p in files if p.suffix == ".md" and folder in p.parents}
    if not published:
        sys.exit(f"no notes found in {folder}")

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

    # the folder's contents go to the site root
    for p in sorted(folder.rglob("*")):
        if p.is_file():
            dest = root / p.relative_to(folder)
            if dest.exists():
                sys.exit(f"{p} would overwrite {dest}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), dest)
    notes = [root / p.relative_to(folder) for p in published]

    for d in sorted((d for d in root.rglob("*") if d.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()

    for n in notes:
        text = n.read_text(encoding="utf-8")
        plain = LIST_CALLOUT.sub(r"\1", list_callouts_to_quartz(text))
        if plain != text:
            n.write_text(plain, encoding="utf-8")

    # home page, short titles, section folder pages
    home_note = next((n for n in notes if n.stem == home), None)
    for n in notes:
        if n is home_note:
            n.rename(root / "index.md")
            set_frontmatter(root / "index.md", title=HOME_TITLE, aliases=f"[{quote(home)}]")
        else:
            set_frontmatter(n, title=quote(PREFIX.sub("", n.stem)))
    for d in {n.parent for n in notes if n.parent != root}:
        index = d / "index.md"
        if not index.exists():
            index.write_text(f"---\ntitle: {quote(SECTION_NUMBER.sub('', d.name))}\n---\n",
                             encoding="utf-8")

    print(f"published {len(notes)} notes from '{folder.name}' "
          f"(home: {home_note.stem if home_note else 'none'}) and "
          f"{len(keep) - len(published)} linked files; removed {len(files) - len(keep)} files")


if __name__ == "__main__":
    args = sys.argv[1:]
    home = "ADLab MOC"
    if "--home" in args:
        i = args.index("--home")
        home = args[i + 1]
        del args[i:i + 2]
    main(args[0] if args else "content", args[1] if len(args) > 1 else "adlab notes", home)
