# Local Extension Model Testing

This file explains the current BoardBench workflow with the project-local pi extension in `.pi/extensions/boardbench-context.ts`.

## What the extension does

- loads automatically when pi is started from this repo
- defaults to authoring mode with `read`, `grep`, `find`, `ls`, `edit`, `write`, `bash`
- can switch into a restricted readonly workflow mode
- uses the BoardBench workflow allowlist in readonly mode
- offers these commands:
  - `/bb-readonly`
  - `/bb-generate`
  - `/bb-authoring`
  - `/bb-status`

## Allowed workflow paths

Current repo paths:

- `README.md`
- `CURRENT.md`
- `AGENTS.md`
- `QUESTIONS.txt`
- `workflow_description.md`
- `boardbench_checkliste.md`
- `boardbench_checkliste_einschaetzung.md`
- `requirements.txt`
- `code/`
- `code/input/`
- `code/outputs/`
- `code/evaluation_draft.md`
- `code/evaluation.ipynb`
- `.pi/extensions/`

Target-state paths are also allowed already:

- `inputs/`
- `outputs/`
- `prompts/`
- `requirements.txt`
- `evaluation.ipynb`

## Before you start

1. Start pi from the repo root.
2. Make sure you are authenticated for the provider you want to test.
3. List supported models before choosing one.
4. For the notebook workflow, use Python 3.12.3, install `requirements.txt`, and use your local Jupyter setup.

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

## Notebook environment

Create a Python 3.12.3 environment and install the repo dependencies:

```bash
conda create -n boardbench python=3.12.3 -y
conda activate boardbench
python -m pip install -r requirements.txt
```

Then open `code/evaluation.ipynb` in your local Jupyter setup.
If needed, install `notebook` or `ipykernel` separately in your local environment.

## Start pi with the local extension

In the normal case this is enough:

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

- `--no-context-files` disables automatic `AGENTS.md` loading
- the extension still loads unless you explicitly disable extensions
- print mode (`-p`) also uses the extension, but slash commands are not available there

## Extension commands

Inside pi:

```text
/bb-status
/bb-readonly
/bb-generate
/bb-authoring
```

- `/bb-readonly` keeps the session in restricted read-only mode
- `/bb-generate` currently behaves like the restricted readonly workflow mode
- `/bb-authoring` enables editing and bash across the repo
- `/bb-status` shows the current mode

## Current workflow files

- `code/input/prompt.txt`
- `code/input/game_rules.txt`

The evaluation notebook reads the prompt and rule text directly.

## Recommended test patterns

### 1. Safe workflow check

Start pi, then run:

```text
/bb-readonly
```

Prompt example:

```text
Read CURRENT.md, code/input/prompt.txt, and code/input/game_rules.txt.
Summarize the current BoardBench workflow and list the exact files that matter for one manual generation run.
```

### 2. Prompt + rulebook test with explicit file context

```bash
pi --model <provider/model> \
  @README.md \
  @CURRENT.md \
  @code/input/prompt.txt \
  @code/input/game_rules.txt \
  "Use only these files. Explain the workflow and say what output artifacts should be kept."
```

### 3. One-shot model run in print mode

```bash
pi -p --model <provider/model> \
  @code/input/prompt.txt \
  @code/input/game_rules.txt \
  "Use the provided files only and generate the Python module."
```

### 4. Authoring run that writes outputs

Switch first:

```text
/bb-authoring
```

Prompt example:

```text
Read code/input/prompt.txt and code/input/game_rules.txt.

Generate the result.

Then save:
- the full raw answer as code/outputs/<game>__<model>__response.md
- the extracted Python module as code/outputs/<game>__<model>.py
```

## Notebook workflow

`code/evaluation.ipynb` contains the current minimal evaluation flow:

1. edit the inline variables in the setup cell
2. optionally run the `pi` call cell
3. run the generated-code smoke test
4. run the OpenSpiel loading cell and the simple random test cell

The notebook prints only errors.

## Reload after changing the extension

If you edit `.pi/extensions/boardbench-context.ts`, reload inside pi:

```text
/reload
```

## Expected restrictions

In readonly mode:

- `bash` is blocked
- `edit` and `write` are blocked
- file access outside the workflow allowlist is blocked

## Suggested first model test

1. choose `code/input/game_rules.txt`
2. use `code/input/prompt.txt`
3. run one authoring pass
4. inspect the saved files in `code/outputs/`
5. open `code/evaluation.ipynb` with the `Python (boardbench)` kernel
