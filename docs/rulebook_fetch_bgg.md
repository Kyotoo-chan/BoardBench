# BGG-Regeln bulk-download

**Quelle:** https://boardgamegeek.com/files/boardgame/all (Login nötig zum Download)

## Ablauf

1. Im Browser bei BGG einloggen.
2. Cookies als Netscape-Datei exportieren (Browser-Extension) → z. B. `%USERPROFILE%\.boardbench_bgg_cookies.txt`
3. Filepage-ID aus der BGG-URL nehmen (`/filepage/303599` → `303599`).
4. Download:

```bash
conda run -n boardbench python generation/rulebook_fetch/fetch_bgg.py ^
  --filepage 303599 ^
  --out inputs/games/_bulk/umami_rules.pdf ^
  --cookies %USERPROFILE%\.boardbench_bgg_cookies.txt
```

Mehrere Filepages: `--filepage` mehrfach, `--out` als Verzeichnis.

**Hinweis:** BGG-ToS beachten; für Thesis-Artefakte einzelne, bewusst gewählte Regeln reichen meist.
