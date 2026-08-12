# Results

Results are separated by artifact type, game, and run:

```text
results/
  scores/<game>/<run>/   JSON, Markdown, CSV, logs, and evaluator evidence
  plots/<game>/<run>/    images only
```

A run is one implementation condition or an explicitly named comparison. New studies normally compare one canonical rulebook and, only when useful, one clarified condition. Plot generators live under `generation/`; `results/plots/` contains no scripts or score data.

Current native Codex defaults:

- implementation generation: `gpt-5.6-sol:low`;
- neutral judges: `gpt-5.6-sol:medium`.

Every new result profile and plot states the settings actually used. Historical runs retain their historical settings.
