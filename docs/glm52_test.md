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
