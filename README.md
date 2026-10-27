# Carlsen with White

Every opening Magnus Carlsen has played with White, from the big picture down to the games.

- **Home page**: the big-picture tree, then one section per first move (1.e4, 1.d4, 1.c4, 1.Nf3, others).
- **Tree pages** (`trees/…`): zoomable trees. The thicker the branch, the more often he plays it; each branch shows the number of games and his score.
- **Line pages** (`lines/…`): every game in that line, with a board to replay it, a search box, opening filters and sorting.

Source: a SCID export of Carlsen's White games (1,992 games, 2000–2026). 34 Chess960 games and 12 games with no moves are left out, which leaves 1,946.
Opening names come from the [Lichess opening list](https://github.com/lichess-org/chess-openings) (CC0).

## Rebuild it on your own computer (Windows)

You need Python, [Graphviz](https://graphviz.org/download/) (tick "Add to PATH") and [Hugo extended](https://gohugo.io/installation/).

```
pip install chess graphviz cairosvg pillow
python tools/build_trees.py     # draws the trees (takes several minutes)
python tools/build_pages.py     # writes the line pages and the home page sections
hugo server                     # look at it at http://localhost:1313
```

To use a different list of games, replace `data/carlsen_white_all.pgn` and run the two scripts again.
Pushing to GitHub publishes the site: in the repo, Settings → Pages → Source must be **GitHub Actions**.

## What is where

| Folder | What it holds |
|---|---|
| `data/` | the games (PGN) and the Lichess opening names |
| `tools/` | the Python scripts and the page templates |
| `static/trees/`, `static/lines/` | the generated tree and game pages |
| `content/en/homepage/` | the generated home page sections |
| `layouts/`, `themes/` | the Hugo site design |
