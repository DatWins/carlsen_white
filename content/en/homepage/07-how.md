---
title: "How This Is Made"
header_menu_title: "How It Works"
navigation_menu_title: "How It Works"
weight: 7
header_menu: false
---
The games come from a SCID database of Carlsen's games with White: 1,992 games from 2000 to 2026. 34 Chess960 games and 12 games with no moves recorded are left out, which leaves the **1,946** games on this site.

Every game is replayed move by move and added to one tree, counting how many games pass through each position and how Carlsen scored there.

## Tools
- [python-chess](https://github.com/niklasf/python-chess) reads the games and draws the boards
- [Graphviz](https://graphviz.org/) lays out the branches
- [Lichess opening names](https://github.com/lichess-org/chess-openings) (CC0) give each game its opening name
- [chess.js](https://github.com/jhlywa/chess.js) replays the games in your browser
- [Hugo](https://gohugo.io/) builds the site
