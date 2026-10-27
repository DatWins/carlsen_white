"""Stage 1: draw the opening trees and write the zoomable viewer pages.
Run from the repo root:  python tools/build_trees.py"""
import os, sys, base64
from PIL import Image
import common, draw_tree as D

ROOT = os.path.abspath(os.path.join(common.HERE, ".."))
BUILD = os.path.join(ROOT, "build"); os.makedirs(BUILD, exist_ok=True)
IMG = os.path.join(BUILD, "boards")

def auto_min(node, max_plies, cap, start=2):
    m = start
    while D.count_nodes(node, m, max_plies) > cap:
        m += 1
    return m

def make(slug, node, title, max_plies, cap, back, backtxt, only=None):
    if only and slug not in only:
        return
    m = auto_min(node, max_plies, cap)
    nodes = D.count_nodes(node, m, max_plies)
    png = os.path.join(BUILD, f"{slug}.png")
    D.draw(node, png, m, max_plies, IMG)
    im = Image.open(png).convert("RGB")
    q = im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:64 * 3]
    bright = max(range(64), key=lambda k: sum(pal[3 * k:3 * k + 3])); pal[3 * bright:3 * bright + 3] = [255, 255, 255]
    q.putpalette(pal)
    small = os.path.join(BUILD, f"{slug}.q.png"); q.save(small, optimize=True)
    out = os.path.join(ROOT, "static", "trees", slug); os.makedirs(out, exist_ok=True)
    w = 1000; im.resize((w, int(w * im.size[1] / im.size[0])), Image.LANCZOS).save(os.path.join(out, "preview.jpg"), quality=82, optimize=True)
    tpl = open(os.path.join(common.HERE, "viewer_template.html"), encoding="utf-8").read()
    html = (tpl.replace("__IMG__", "data:image/png;base64," + base64.b64encode(open(small, "rb").read()).decode())
               .replace("__TITLE__", title).replace("__BACK__", back).replace("__BACKTXT__", backtxt))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)
    print(f"{slug:18s} min={m:3d} boards={nodes:3d} {im.size} -> {os.path.getsize(small)//1024} KB", flush=True)

def main(only=None):
    games, _ = common.load_games(); root = common.build_tree(games)
    make("big-picture", root, "Carlsen with White – the big picture", 8, 60, "../../", "Repertoire", only)
    for san, label, slug in common.FIRST_MOVES:
        make(slug, root.kids[san], f"Carlsen with White – {label}", 14, 90, f"../../#{common.ANCHOR[slug]}", "Repertoire", only)
    for p in common.line_groups(games, root):
        if p["node"] is not None:
            make(p["slug"], p["node"], f"Carlsen with White – {p['title']}", 16, 100, f"../../lines/{p['slug']}/", "Games", only)

if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
