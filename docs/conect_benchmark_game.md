# Conect — neues Benchmark-Spiel

## Warum Conect?

| Kriterium | Conect |
|-----------|--------|
| Neuheit | Entwurf **Mai 2024** (Mark Steere) — sehr unwahrscheinlich in Trainingsdaten |
| Schwierigkeit | 2-Spieler-Abstract, hex, 3 Siegbedingungen — vergleichbar mit Havannah |
| Regel-PDF | https://marksteeregames.com/Conect_rules.pdf (Autor erlaubt Programmierung) |
| OpenSpiel | kein Referenz-Env |
| Regellänge | kurz (~2 Seiten + Figuren) |

Alternativen verworfen: **Umami** (2025, aber kein freies PDF ohne BGG-Login), **Daybreak** (zu schwer/kooperativ), **Leylines** (Euro mit Auktionen — über Pilot-Niveau).

## Einschätzung zur Neuheit

Conect ist als 2024-Spiel deutlich besser als ältere Klassiker, aber **keine Garantie** gegen Trainingsdaten-Leakage bei sehr neuen Modellen: Wenn GPT-5.5 mit Webdaten nach Mai 2024 oder mit späteren Crawls trainiert wurde, kann die frei zugängliche Mark-Steere-Seite enthalten sein. Für die Arbeit sollte Conect daher als *plausibel frisch/low exposure*, nicht als sicher ungesehen, dokumentiert werden.

## Repo-Setup

```bash
conda run -n boardbench python generation/rulebook_fetch/fetch_direct.py ^
  --urls generation/rulebook_fetch/examples/direct_urls.txt ^
  --out inputs/games/conect
# Kopieren: Conect_rules.pdf -> inputs/games/conect/game_rules.pdf

conda run -n boardbench python generation/game_run_workflow.py prepare conect
```

## Generierung (nur pi + codex)

```bash
conda run -n boardbench python generation/run_pi_series.py --game conect --variant oneshot
conda run -n boardbench python generation/run_pi_series.py --game conect --variant agentic
conda run -n boardbench python generation/run_codex_series.py --game conect --variant oneshot
conda run -n boardbench python generation/run_codex_series.py --game conect --variant agentic
```

## Cross-Judge (gpt + codex)

```bash
conda run -n boardbench python generation/run_cross_judges.py --game conect --impl-backend codex --judges gpt,codex
conda run -n boardbench python generation/run_cross_judges.py --game conect --impl-backend gpt --judges gpt,codex
```

Artefakt-Stems: `con_gpt_os`, `con_gpt_ag`, `con_codex_os`, `con_codex_ag`.
