# Publisher-Downloadseiten (Board&Dice)

**Quelle:** https://boardanddice.com/download/

## Ablauf

```bash
conda run -n boardbench python generation/rulebook_fetch/fetch_boardanddice.py ^
  --query teotihuacan ^
  --out inputs/games/_bulk
```

Alle PDFs der Seite:

```bash
conda run -n boardbench python generation/rulebook_fetch/fetch_boardanddice.py --all --out inputs/games/_bulk
```

Das Skript scraped `.pdf`-Links von der Download-Seite. Für andere Publisher: URLs in `fetch_direct.py`-Liste eintragen oder Seite analog erweitern.
