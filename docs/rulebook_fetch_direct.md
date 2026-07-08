# Direkte PDF-URLs bulk-download

**Quelle:** beliebige öffentliche PDF-Links (Designer, Publisher, Itch.io, …)

## Ablauf

1. URLs in eine Textdatei, eine pro Zeile (`#` = Kommentar).
2. Beispiel liegt unter `generation/rulebook_fetch/examples/direct_urls.txt`.
3. Download:

```bash
conda run -n boardbench python generation/rulebook_fetch/fetch_direct.py ^
  --urls generation/rulebook_fetch/examples/direct_urls.txt ^
  --out inputs/games/_bulk
```

4. Gewünschte PDF nach `inputs/games/<slug>/game_rules.pdf` kopieren.

**Gut für:** neue Spiele mit frei verlinkter Regel (z. B. Mark Steere).
