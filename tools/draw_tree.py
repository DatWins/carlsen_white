"""Draw a counted opening tree: a board per position, and each branch labelled
with the move, how many games, and Carlsen's score (White)."""
import os, math, shutil
import chess, chess.svg, cairosvg
from graphviz import Digraph
from common import Node

COLORS = {"square light": "#DEE3E6", "square dark": "#8CA2AD", "margin": "#5B6F79"}

def pick(node, min_games, max_plies, base_ply):
    """Children worth drawing, most-played first."""
    if node.ply - base_ply >= max_plies:
        return []
    kids = [k for k in node.kids.values() if k.n >= min_games]
    return sorted(kids, key=lambda k: -k.n)

def count_nodes(start, min_games, max_plies):
    n, stack = 0, [start]
    while stack:
        x = stack.pop(); n += 1
        stack.extend(pick(x, min_games, max_plies, start.ply))
    return n

def board_png(board, last, img_dir, size):
    arrows = [chess.svg.Arrow(last.from_square, last.to_square, color="#15781B")] if last else []
    svg = chess.svg.board(board=board, size=size, arrows=arrows, colors=COLORS).encode()
    name = board.epd().replace("/", "_").replace(" ", "_") + (f"_{last.uci()}" if last else "") + f"_{size}.png"
    path = os.path.abspath(os.path.join(img_dir, name))
    if not os.path.exists(path):
        tmp = f"{path}.{os.getpid()}.tmp"
        cairosvg.svg2png(bytestring=svg, write_to=tmp)
        os.replace(tmp, path)
    return path

def draw(start, out_png, min_games, max_plies, img_dir, size=260, label_pt=34):
    """start: a Node (the tree starts at the position after start.path())."""
    os.makedirs(img_dir, exist_ok=True)
    base = chess.Board()
    for san in start.path():
        base.push_san(san)
    dot = Digraph(graph_attr={"splines": "ortho", "ranksep": "1.3", "nodesep": "1.0", "bgcolor": "white",
                              "forcelabels": "true", "ordering": "out"},
                  node_attr={"shape": "none"}, edge_attr={"color": "#2b3a44", "arrowsize": "0.9"})
    top = start.n
    last0 = None
    ids = {}
    def nid(x): return "n" + str(ids.setdefault(id(x), len(ids)))
    stack = [(start, base, None)]
    while stack:
        x, b, last = stack.pop()
        dot.node(nid(x), label="", image=board_png(b, last, img_dir, size))
        for k in pick(x, min_games, max_plies, start.ply):
            nb = b.copy(); mv = nb.parse_san(k.san); nb.push(mv)
            num = (k.ply + 1) // 2
            mvtxt = f"{num}.{k.san}" if k.ply % 2 else f"{num}...{k.san}"
            lab = (f'<<FONT COLOR="#1a4fd0" POINT-SIZE="{label_pt}"><B>{mvtxt}</B></FONT><BR/>'
                   f'<FONT COLOR="#555555" POINT-SIZE="{int(label_pt*0.72)}">{k.n} game{"" if k.n == 1 else "s"} · {k.score:.0%}</FONT>>')
            dot.edge(nid(x), nid(k), xlabel=lab, penwidth=f"{1.5 + 7*math.sqrt(k.n/top):.1f}")
            stack.append((k, nb, mv))
    base_name = os.path.splitext(out_png)[0]
    dot.render(base_name, format="png", cleanup=True)
    return base_name + ".png"
