"""Stage 1b: one small tree per opening name on each line page (e.g. only the Ruy Lopez games of 1.e4 e5).
Run from the repo root:  python tools/build_variations.py [page-slug ...]"""
import os, sys, base64, shutil
from multiprocessing import Pool
from PIL import Image
import common, draw_tree as D

ROOT = os.path.abspath(os.path.join(common.HERE, ".."))
BUILD = os.path.join(ROOT, "build"); IMG = os.path.join(BUILD, "boards")

def tree_for(task):
    page_slug, title, path, label, ids = task
    games, _ = common.load_games(); 
    sub = [games[i] for i in ids]
    sroot = common.build_tree(sub)
    node = sroot
    for san in path:
        node = node.kids[san]
    while len(node.kids) == 1:          # start where the games first differ
        node = next(iter(node.kids.values()))
    shared = common.pgn_moves_text(node.path())
    # pick how deep to draw: keep every branch for small groups, only the common ones for big groups, ~45 boards at most
    n_games = len(ids); depth, m = 6, 1
    for d in (16, 12, 10, 8, 6):
        mm = 1
        while D.count_nodes(node, mm, d) > 45:
            mm += 1
        if mm <= max(2, n_games // 15) or d == 6:
            depth, m = d, mm
            break
    slug = common.group_slug(page_slug, label)
    png = os.path.join(BUILD, f"{slug}.png")
    D.draw(node, png, m, depth, IMG)
    im = Image.open(png).convert("RGB")
    q = im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:64 * 3]
    bright = max(range(64), key=lambda k: sum(pal[3 * k:3 * k + 3])); pal[3 * bright:3 * bright + 3] = [255, 255, 255]
    q.putpalette(pal)
    out = os.path.join(ROOT, "static", "trees", slug); os.makedirs(out, exist_ok=True)
    q.save(os.path.join(out, "tree.png"), optimize=True)
    w = min(1000, im.size[0]); im.resize((w, max(1, int(w * im.size[1] / im.size[0]))), Image.LANCZOS).save(os.path.join(out, "preview.jpg"), quality=82, optimize=True)
    tpl = open(os.path.join(common.HERE, "viewer_template.html"), encoding="utf-8").read()
    html = (tpl.replace("__IMG__", "tree.png").replace("__TITLE__", f"{title} – {label} ({shared})")
               .replace("__BACK__", f"../../lines/{page_slug}/").replace("__BACKTXT__", "Games"))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)
    os.remove(png)
    return f"{slug}|{shared}|{len(ids)}|{slug:40s} {len(ids):4d} games  min={m} depth={depth} boards={D.count_nodes(node, m, depth)} {im.size}"

def main(only=None):
    games, _ = common.load_games(); root = common.build_tree(games)
    tasks = []
    for p in common.line_groups(games, root):
        if p["node"] is None or (only and p["slug"] not in only):
            continue
        level, labels, of_game = common.page_groups(p, games)
        if len(labels) < 2 and level == 1:
            continue
        path = p["node"].path()
        for label, n in labels:
            ids = [i for i in p["ids"] if of_game[i] == label]
            tasks.append((p["slug"], f"Carlsen with White – {p['title']}", path, label, ids))
    print(len(tasks), "trees", flush=True)
    import json
    mpath = os.path.join(BUILD, "variations.json")
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    with Pool(2) as pool:
        for line in pool.imap_unordered(tree_for, tasks):
            slug, shared, n, msg = line.split("|", 3)
            manifest[slug] = {"moves": shared, "n": int(n)}
            print(msg, flush=True)
            json.dump(manifest, open(mpath, "w"), indent=1)

if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
