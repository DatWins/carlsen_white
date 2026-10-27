"""Stage 2: write the line pages (with the game viewer) and the home-page sections.
Run from the repo root:  python tools/build_pages.py"""
import os, json, html
import common

ROOT = os.path.abspath(os.path.join(common.HERE, ".."))
esc = html.escape

def fmt_wdl(s):
    return f"+{s['w']} ={s['d']} −{s['l']}"

def line_page(p, games, tpl, pieces, chessjs):
    ids = p["ids"]
    st = common.wdl(ids, games)
    fams = common.families(ids, games, 3)
    if p["kind"] == "line":
        dek = "Mostly " + ", ".join(f"{esc(f)} ({n})" for f, n in fams)
    elif p["first"] == "other":
        dek = "Everything else Carlsen has opened with: 1.b3, 1.g3, 1.a3, 1.e3, 1.Nc3, 1.b4, 1.a4, 1.f4, 1.c3 and 1.f3"
    else:
        dek = "The less common replies to " + p["title"].split(" ")[0]
    first_label = {"e4": "1.e4", "d4": "1.d4", "c4": "1.c4", "nf3": "1.Nf3", "other": "Other first moves"}[p["first"]]
    level, labels, of_game = common.page_groups(p, games)
    mpath = os.path.join(ROOT, "build", "variations.json")
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    chips, trees = [], {}
    for label, n in labels:
        slug = common.group_slug(p["slug"], label)
        has = slug in manifest and os.path.exists(os.path.join(ROOT, "static", "trees", slug, "preview.jpg"))
        chips.append([label, n])
        if has:
            trees[label] = {"slug": slug, "moves": manifest[slug]["moves"], "n": manifest[slug]["n"]}
    rows = []
    for i in ids:
        g = games[i]
        rows.append([g["date"], g["event"], g["site"], g["round"], g["black"], g["welo"], g["belo"],
                     g["result"], g["eco"], g["opening"], " ".join(g["moves"]), of_game[i]])
    tree = ""
    if os.path.exists(os.path.join(ROOT, "static", "trees", p["slug"], "preview.jpg")):
        tree = (f'    <a class="tree" id="treeLink" href="../../trees/{p["slug"]}/"><img id="treeImg" src="../../trees/{p["slug"]}/preview.jpg" '
                f'alt="Opening tree for {esc(p["title"])}"><span id="treeCap">Open the zoomable tree &rarr;</span></a>\n'
                f'    <div class="stats" id="treeNote"></div>\n')
    back = f"../../#{common.ANCHOR[p['first']]}"
    out = (tpl.replace("__TITLE__", esc(p["title"])).replace("__KICKER__", f"Carlsen with White · {first_label}")
              .replace("__DEK__", dek).replace("__TREE__", tree).replace("__BACKHREF__", back).replace("__BACKTXT__", "Repertoire")
              .replace("__PIECES__", pieces).replace("__CHESSJS__", chessjs)
              .replace("__DATA__", json.dumps({"games": rows, "chips": chips, "trees": trees}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))
    d = os.path.join(ROOT, "static", "lines", p["slug"]); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(out)
    return st

def front(title, menu, weight):
    return f'---\ntitle: "{title}"\nheader_menu_title: "{menu}"\nnavigation_menu_title: "{menu}"\nweight: {weight}\nheader_menu: true\n---\n'

def card(p, st, fams):
    names = " · ".join(f for f, _ in fams[:3])
    return (f'{{{{< linecard href="lines/{p["slug"]}/" title="{p["title"]}" n="{st["n"]}" w="{st["w"]}" d="{st["d"]}" l="{st["l"]}" '
            f'score="{st["score"]:.0%}" names="{names}" >}}}}\n')

def main():
    games, skipped = common.load_games(); root = common.build_tree(games)
    pages = common.line_groups(games, root)
    tpl = open(os.path.join(common.HERE, "line_template.html"), encoding="utf-8").read()
    pieces = open(os.path.join(common.HERE, "pieces.css"), encoding="utf-8").read()
    chessjs = open(os.path.join(common.HERE, "chess.js"), encoding="utf-8").read()
    stats = {}
    for p in pages:
        stats[p["slug"]] = line_page(p, games, tpl, pieces, chessjs)
        print(f"{p['slug']:18s} {stats[p['slug']]['n']:4d} games", flush=True)

    total = common.wdl([g["id"] for g in games], games)
    ch = os.path.join(ROOT, "content", "en", "homepage"); os.makedirs(ch, exist_ok=True)
    for f in os.listdir(ch):
        if f.endswith(".md"): os.remove(os.path.join(ch, f))
    open(os.path.join(ch, "index.md"), "w").write("---\nheadless: true\n---\n")

    # 01 overview
    rows = []
    for san, label, slug in common.FIRST_MOVES:
        ids = root.kids[san].games
        s = common.wdl(ids, games)
        rows.append(f"- **[{label}](#{common.ANCHOR[slug]})** — {s['n']} games, {fmt_wdl(s)}, {s['score']:.0%}")
    other_ids = [g["id"] for g in games if g["moves"][0] not in {m for m, _, _ in common.FIRST_MOVES}]
    so = common.wdl(other_ids, games)
    rows.append(f"- **[Other first moves](#others)** — {so['n']} games, {fmt_wdl(so)}, {so['score']:.0%}")
    first_games = {n: root.kids[n].n for n in ("e4", "d4", "c4", "Nf3")}
    open(os.path.join(ch, "01-big-picture.md"), "w", encoding="utf-8").write(
        front("The Big Picture", "Big Picture", 1) +
        f"Every opening Magnus Carlsen has played with White: **{total['n']:,} games**, {fmt_wdl(total)}, a score of **{total['score']:.0%}**. "
        "The thicker the branch, the more often he plays it.\n\n"
        "[![Carlsen's White repertoire, the big picture](trees/big-picture/preview.jpg)](trees/big-picture/)\n\n"
        "- [Open the zoomable tree](trees/big-picture/)\n\n"
        "## By first move\n" + "\n".join(rows) + "\n")

    # 02-05 first moves, 06 other
    weight = 2
    for san, label, slug in common.FIRST_MOVES:
        ids = root.kids[san].games
        s = common.wdl(ids, games); fams = common.families(ids, games, 4)
        cards = "".join(card(p, stats[p["slug"]], common.families(p["ids"], games, 3)) for p in pages if p["first"] == slug)
        body = (front(label, label, weight) +
                f"**{s['n']} games**, {fmt_wdl(s)}, score **{s['score']:.0%}**. Most often: " +
                ", ".join(f"{esc(f)} ({n})" for f, n in fams) + ".\n\n"
                f"[![{label} opening tree](trees/{slug}/preview.jpg)](trees/{slug}/)\n\n"
                f"- [Open the zoomable tree](trees/{slug}/)\n\n"
                "## Choose a line\nEach line opens the tree for it and every game, with a board to replay them.\n\n"
                "{{< linecards >}}\n" + cards + "{{< /linecards >}}\n")
        open(os.path.join(ch, f"{weight:02d}-{slug}.md"), "w", encoding="utf-8").write(body); weight += 1
    p = [x for x in pages if x["slug"] == "other-first-moves"][0]
    body = (front("Other first moves", "Others", weight) +
            f"**{so['n']} games** with 1.b3, 1.g3, 1.a3 and other less common first moves, {fmt_wdl(so)}, score **{so['score']:.0%}**.\n\n"
            "{{< linecards >}}\n" + card(p, stats[p["slug"]], common.families(p["ids"], games, 3)) + "{{< /linecards >}}\n")
    open(os.path.join(ch, f"{weight:02d}-other-first-moves.md"), "w", encoding="utf-8").write(body); weight += 1

    # how
    open(os.path.join(ch, f"{weight:02d}-how.md"), "w", encoding="utf-8").write(
        front("How This Is Made", "How It Works", weight).replace("header_menu: true", "header_menu: false") +
        f"The games come from a SCID database of Carlsen's games with White: 1,992 games from 2000 to 2026. "
        f"{skipped['Chess960 / custom start']} Chess960 games and {skipped['No moves recorded']} games with no moves recorded are left out, "
        f"which leaves the **{total['n']:,}** games on this site.\n\n"
        "Every game is replayed move by move and added to one tree, counting how many games pass through each position and how Carlsen scored there.\n\n"
        "## Tools\n"
        "- [python-chess](https://github.com/niklasf/python-chess) reads the games and draws the boards\n"
        "- [Graphviz](https://graphviz.org/) lays out the branches\n"
        "- [Lichess opening names](https://github.com/lichess-org/chess-openings) (CC0) give each game its opening name\n"
        "- [chess.js](https://github.com/jhlywa/chess.js) replays the games in your browser\n"
        "- [Hugo](https://gohugo.io/) builds the site\n")
    json.dump(stats, open(os.path.join(ROOT, "build", "stats.json"), "w"))
    print("home sections written")

if __name__ == "__main__":
    main()
