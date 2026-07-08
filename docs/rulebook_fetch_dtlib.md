# Dice Tower Library bulk-download

**Quelle:** https://cs.uwaterloo.ca/~dtompkin/dtlib/dtlibrary.html (kein Login)

## Ablauf

1. Spielname oder Teilstring wählen.
2. Skript parst `dtlibrary.html` und lädt aus `archive/dtlib/`:

```bash
conda run -n boardbench python generation/rulebook_fetch/fetch_dtlib.py ^
  --query havannah ^
  --out inputs/games/_bulk
```

3. Optional `--limit 10` oder `--all` (vorsichtig, tausende PDFs).

Dateiname: `{Spieltitel}__{original.pdf}`.

**Gut für:** etablierte Brettspiele mit durchsuchbarem Index. **Schlecht für:** sehr neue Nischen-Titel (fehlen oft).
