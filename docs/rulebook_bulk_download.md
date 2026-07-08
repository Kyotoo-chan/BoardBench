# Spielanleitungs-PDFs in Masse

Kurzüberblick der Quellen und passenden Skripte unter `generation/rulebook_fetch/`.

| Quelle | Umfang | Login | Skript |
|--------|--------|-------|--------|
| [BoardGameGeek Files](https://boardgamegeek.com/files/boardgame/all) | sehr groß, community + Publisher | ja | `fetch_bgg.py` |
| [Dice Tower Library](https://cs.uwaterloo.ca/~dtompkin/dtlib/) | ~1000+ Regeln, oft ältere Titel | nein | `fetch_dtlib.py` |
| [Board&Dice Downloads](https://boardanddice.com/download/) | Publisher-Katalog | nein | `fetch_boardanddice.py` |
| [board-game-rules.com](https://board-game-rules.com/) | Index, oft Links zu Publishern | meist nein | manuell / `fetch_direct.py` |
| Designer-Seiten (z. B. Mark Steere) | einzelne freie PDFs | nein | `fetch_direct.py` |

**Empfehlung für BoardBench:** erst `fetch_direct.py` für bekannte URLs, dann `fetch_dtlib.py --query <name>` für etablierte Spiele, BGG nur wenn nötig (Cookie-Export).

Details je Quelle: `docs/rulebook_fetch_*.md`.
