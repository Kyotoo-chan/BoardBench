# GLM-5.2 testen

**Anbieter:** [Z.ai](https://z.ai) — OpenAI-kompatible Chat-API.

## Schnelltest (API-Key)

1. Key holen: https://z.ai/manage-apikey/apikey-list
2. Einmaliger Request:

```bash
curl -X POST "https://api.z.ai/api/paas/v4/chat/completions" ^
  -H "Authorization: Bearer %ZAI_API_KEY%" ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"glm-5.2\",\"messages\":[{\"role\":\"user\",\"content\":\"Say OK.\"}],\"thinking\":{\"type\":\"enabled\"},\"reasoning_effort\":\"max\"}"
```

## Python (OpenAI-SDK)

```python
from openai import OpenAI

client = OpenAI(api_key="YOUR_ZAI_KEY", base_url="https://api.z.ai/api/paas/v4")
resp = client.chat.completions.create(
    model="glm-5.2",
    messages=[{"role": "user", "content": "Kurz: was ist Havannah?"}],
    extra_body={"thinking": {"type": "enabled"}, "reasoning_effort": "max"},
)
print(resp.choices[0].message.content)
```

- **1M Context:** Modell-ID `glm-5.2[1m]`
- **OpenRouter:** `z-ai/glm-5.2`
- **Coding-CLI:** Z.ai Coding Plan; Endpoint `https://api.z.ai/api/coding/paas/v4` (Claude-Code/Cline-kompatibel)

Für BoardBench-Generierung müsste ein neuer Backend-Eintrag in `generation/llm_cli.py` analog zu `pi`/`codex` ergänzt werden — aktuell nicht im Pilot.

## BoardBench workflow (neu)

GLM-Generation mit Kosten-Tracking:

```bash
python generation/run_glm_series.py --game exploding_kittens --all-variants
```

Volle Pipeline (Generation + base checks + Cross-Judges gpt/codex):

```bash
python generation/run_glm_pipeline.py --game exploding_kittens
```

### Token- und Kosten-Dateien

Serienlog (eine CSV, keine JSON-Artefakte pro Lauf):

- `outputs/glm_usage_log.csv`

Agentic-Transcript steht in `outputs/<stem>.md` (nicht als separates JSON).

### Preisvariablen für USD-Schätzung

Setze die Modellpreise (pro 1M Tokens) als Umgebungsvariablen:

```powershell
setx GLM_PRICE_INPUT_PER_1M "0.00"
setx GLM_PRICE_OUTPUT_PER_1M "0.00"
setx GLM_PRICE_REASONING_PER_1M "0.00"
```

Wenn Preisvariablen fehlen, werden Tokens trotzdem geloggt, aber Kosten bleiben `n/a`.
