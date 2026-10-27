"""Shared helpers: load Carlsen's games, name the openings, build the counted move tree."""
import csv, io, os, re, collections
import chess, chess.pgn

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

def load_openings():
    """Lichess opening names (CC0): position -> (eco, name)."""
    table = {}
    for letter in "abcde":
        with open(os.path.join(DATA, f"{letter}.tsv"), encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                g = chess.pgn.read_game(io.StringIO(row["pgn"]))
                b = g.board()
                for m in g.mainline_moves():
                    b.push(m)
                key = b.epd()
                old = table.get(key)
                if old is None or len(row["name"]) >= len(old[1]):
                    table[key] = (row["eco"], row["name"])
    return table

def surname(name):
    return name.split(",")[0].strip()

def load_games(path=None):
    """Return (games, skipped). Skips Chess960 / odd start positions and games without moves."""
    path = path or os.path.join(DATA, "carlsen_white_all.pgn")
    openings = load_openings()
    games, skipped = [], collections.Counter()
    with open(path, encoding="utf-8", errors="replace") as f:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            h = g.headers
            if "FEN" in h or h.get("Variant"):
                skipped["Chess960 / custom start"] += 1
                continue
            board = g.board()
            sans, name, eco = [], None, h.get("ECO", "")
            for mv in g.mainline_moves():
                sans.append(board.san(mv))
                board.push(mv)
                hit = openings.get(board.epd())
                if hit:
                    eco, name = hit
            if not sans:
                skipped["No moves recorded"] += 1
                continue
            res = h.get("Result", "*")
            year = (h.get("Date", "????")[:4])
            games.append(dict(
                id=len(games), date=h.get("Date", "????.??.??"), year=year if year.isdigit() else "",
                event=h.get("Event", ""), site=h.get("Site", ""), round=h.get("Round", ""),
                black=h.get("Black", "?"), welo=h.get("WhiteElo", ""), belo=h.get("BlackElo", ""),
                result=res, eco=eco, opening=name or "", moves=sans))
    return games, skipped

def score_of(res):          # Carlsen is White
    return {"1-0": 1.0, "1/2-1/2": 0.5, "0-1": 0.0}.get(res, 0.5)

class Node:
    __slots__ = ("san", "ply", "parent", "kids", "n", "w", "d", "l", "games")
    def __init__(self, san=None, ply=0, parent=None):
        self.san, self.ply, self.parent = san, ply, parent
        self.kids, self.n, self.w, self.d, self.l, self.games = {}, 0, 0, 0, 0, []
    @property
    def score(self):
        return (self.w + self.d / 2) / self.n if self.n else 0
    def path(self):
        out, x = [], self
        while x.parent is not None:
            out.append(x.san); x = x.parent
        return out[::-1]

def build_tree(games, max_plies=40):
    root = Node()
    for g in games:
        node = root
        node.n += 1
        for i, san in enumerate(g["moves"][:max_plies]):
            kid = node.kids.get(san)
            if kid is None:
                kid = node.kids[san] = Node(san, i + 1, node)
            node = kid
            node.n += 1
            r = g["result"]
            node.w += r == "1-0"; node.d += r == "1/2-1/2"; node.l += r == "0-1"
            node.games.append(g["id"])
        r = g["result"]
        root.w += r == "1-0"; root.d += r == "1/2-1/2"; root.l += r == "0-1"
    return root

def move_label(ply, san, with_dots=True):
    """ply is 1-based: 1 -> '1.e4', 2 -> '1...e5'"""
    num = (ply + 1) // 2
    return f"{num}.{san}" if ply % 2 else f"{num}...{san}"

def pgn_moves_text(sans, upto=None):
    out = []
    for i, s in enumerate(sans[:upto]):
        out.append(f"{i//2+1}.{s}" if i % 2 == 0 else s)
    return " ".join(out)

# ---------------------------------------------------------------- site structure
FIRST_MOVES = [("e4", "1.e4", "e4"), ("d4", "1.d4", "d4"), ("c4", "1.c4", "c4"), ("Nf3", "1.Nf3", "nf3")]
ANCHOR = {"e4": "1e4", "d4": "1d4", "c4": "1c4", "nf3": "1nf3", "other": "others"}   # section ids on the home page
MIN_REPLY = 15      # a reply with at least this many games gets its own page

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def line_groups(games, root):
    """Pages of games. Returns list of dicts: slug, title, first, reply, ids, node (or None)."""
    pages, used = [], set()
    for san, label, slug in FIRST_MOVES:
        fm = root.kids[san]
        listed = [r for r in sorted(fm.kids.values(), key=lambda k: -k.n) if r.n >= MIN_REPLY]
        for r in listed:
            ids = list(r.games)
            used.update(ids)
            pages.append(dict(slug=f"{slug}-{slugify(r.san)}", title=f"{label} {r.san}", first=slug,
                              reply=r.san, ids=ids, node=r, kind="line"))
        rest = [i for i in fm.games if i not in used]
        if rest:
            pages.append(dict(slug=f"{slug}-other", title=f"{label} — other replies", first=slug,
                              reply=None, ids=rest, node=None, kind="other"))
            used.update(rest)
    rest = [g["id"] for g in games if g["id"] not in used]
    pages.append(dict(slug="other-first-moves", title="Other first moves", first="other",
                      reply=None, ids=rest, node=None, kind="other"))
    return pages

def wdl(ids, games):
    w = sum(games[i]["result"] == "1-0" for i in ids)
    l = sum(games[i]["result"] == "0-1" for i in ids)
    d = len(ids) - w - l
    n = len(ids)
    return dict(n=n, w=w, d=d, l=l, score=(w + d / 2) / n if n else 0)

def families(ids, games, top=3, min_share=0.06):
    """Most common opening names in these games, ignoring rare transposition artefacts."""
    c = collections.Counter(fam_name(games[i]["opening"]) for i in ids)
    out = [(f, n) for f, n in c.most_common(top) if n / max(1, len(ids)) >= min_share]
    return out or c.most_common(1)


# ---------------------------------------------------------------- opening-name groups (the chips)
def fam_name(opening):
    """'Sicilian Defense: Najdorf Variation, English Attack' -> 'Sicilian Defense'"""
    return opening.split(":")[0].split(",")[0].strip() or "unnamed"

def var_name(opening):
    """... -> 'Najdorf Variation' (or '(main line)' when the name has no variation)"""
    parts = opening.split(":", 1)
    v = parts[1].strip().split(",")[0].strip() if len(parts) > 1 else ""
    return v or "(main line)"

def page_groups(page, games, top=10, min_games=3):
    """Opening-name groups for a page: (level, [(label, n), ...]) and games -> label.
    Mixed pages group by opening family; pages dominated by one family group by variation."""
    ids = page["ids"]
    fams = collections.Counter(fam_name(games[i]["opening"]) for i in ids)
    level = 1
    if page["kind"] == "line" and fams and fams.most_common(1)[0][1] >= 0.8 * len(ids):
        level = 2
    key = (lambda g: fam_name(g["opening"])) if level == 1 else (lambda g: var_name(g["opening"]))
    c = collections.Counter(key(games[i]) for i in ids)
    labels = [(f, n) for f, n in c.most_common(top) if n >= min_games]
    chosen = {f for f, _ in labels}
    of_game = {i: (key(games[i]) if key(games[i]) in chosen else "") for i in ids}
    return level, labels, of_game

def group_slug(page_slug, label):
    return f"{page_slug}--{slugify(label)}"
