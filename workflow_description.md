# Local Extension Model Testing

This file explains how to use the project-local pi extension in `.pi/extensions/boardbench-context.ts` to test the BoardBench workflow with supported models.

## What the extension does

- loads automatically when pi is started from this repo
- defaults to a readonly tool set: `read`, `grep`, `find`, `ls`
- blocks `bash`
- blocks file access outside the BoardBench workflow allowlist
- offers these commands:
  - `/bb-readonly`
  - `/bb-authoring`
  - `/bb-status`

## Allowed workflow paths

Current repo paths:

- `README.md`
- `CURRENT.md`
- `AGENTS.md`
- `QUESTIONS.txt`
- `workflow_description.md`
- `code/`
- `code/input_rules/`
- `code/prompts/`
- `code/outputs/`
- `code/evaluation_draft.md`
- `code/compare_to_openspiel.ipynb`
- `.pi/extensions/`

Target-state paths are also allowed already:

- `inputs/`
- `outputs/`
- `prompts/`
- `compare_to_openspiel.ipynb`

## Before you start

1. Start pi from the repo root.
2. Make sure you are authenticated for the provider you want to test.
3. List supported models before choosing one.

Examples:

```bash
pi --list-models claude
pi --list-models gemini
pi --list-models gpt
```

Interactive login / auth options:

```bash
pi
/login
```

Or use environment variables for API-key providers before starting pi.

## Start pi with the local extension

The extension is project-local and auto-discovered from `.pi/extensions/`, so in the normal case this is enough:

```bash
pi
```

Useful stricter variants:

```bash
pi --tools read,grep,find,ls
pi --no-skills --no-prompt-templates
pi --no-context-files --no-skills --no-prompt-templates
```

Notes:

- `--no-context-files` disables automatic `AGENTS.md` loading.
- the extension still loads unless you explicitly disable extensions.
- print mode (`-p`) also uses the extension, but slash commands are not available there.

## Extension commands

Inside pi:

```text
/bb-status
/bb-readonly
/bb-authoring
```

- `/bb-readonly` keeps the session in restricted read-only mode
- `/bb-authoring` also enables `edit` and `write`
- `/bb-status` shows the current mode

## Recommended test patterns

### 1. Safe workflow check (interactive, read-only)

Start pi, then run:

```text
/bb-readonly
```

Prompt example:

```text
Read CURRENT.md, code/prompts/system.md, code/prompts/game_to_python.md, and code/input_rules/rules.txt.
Summarize the current BoardBench workflow and list the exact files that matter for one manual generation run.
```

Use this when you want to check whether a model can understand the workflow without writing files.

### 2. Prompt + rulebook test with explicit file context

You can also pass the files directly on the command line:

```bash
pi --model <provider/model> \
  @README.md \
  @CURRENT.md \
  @code/prompts/system.md \
  @code/prompts/game_to_python.md \
  @code/input_rules/rules.txt \
  "Use only these files. Explain the workflow and say what output artifacts should be kept."
```

This is the most deterministic way to keep context small.

### 3. One-shot model comparison in print mode

```bash
pi -p --model <provider/model> \
  @code/prompts/system.md \
  @code/prompts/game_to_python.md \
  @code/input_rules/rules.txt \
  "Game name: <replace_me>. Use the provided files only and generate the Python module."
```

This is useful when you want comparable runs across several models.

### 4. Authoring run that writes outputs

If you want pi to save files into `code/outputs/`, switch to authoring mode first:

```text
/bb-authoring
```

Prompt example:

```text
Read code/prompts/system.md, code/prompts/game_to_python.md, and code/input_rules/rules.txt.

Generate the result for game name: <replace_me>.

Then save:
- the full raw answer as code/outputs/<game>__<model>__response.md
- the extracted Python module as code/outputs/<game>__<model>.py

Do not edit files outside the BoardBench workflow allowlist.
```

## Switching models

Inside pi:

```text
/model
```

Or start separate runs from the shell:

```bash
pi --model <provider/model>
```

Recommended pattern:

1. pick one rules file
2. keep the same prompt files
3. run the same task across multiple supported models
4. store each raw answer and each extracted `.py` file separately
5. compare later in the notebook

## Reload after changing the extension

If you edit `.pi/extensions/boardbench-context.ts`, reload inside pi:

```text
/reload
```

## Expected restrictions

The extension is intentionally narrow.

Expected behavior:

- `bash` tool calls are blocked
- broad file exploration outside the workflow allowlist is blocked
- in readonly mode, `edit` and `write` are blocked
- if a model needs a file outside the allowlist, ask the user first and then adjust the extension deliberately

## Suggested first model test

A simple first test is:

1. choose `code/input_rules/rules.txt`
2. use the two prompt files in `code/prompts/`
3. run one readonly understanding pass
4. run one authoring pass
5. inspect the saved files in `code/outputs/`
