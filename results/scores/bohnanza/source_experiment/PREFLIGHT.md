# Bohnanza source-sensitivity preflight

Status: **not cleared for generation — awaiting isolation decision and final user Go**

No experimental implementation run has started.

## Frozen design

Four conditions, three fresh generations each:

1. `pdf_only`: canonical publisher PDF only;
2. `json_clean`: canonical PDF plus canonical component JSON;
3. `json_mutated`: canonical PDF plus mutated component JSON;
4. `pdf_mutated`: mutated PDF plus canonical component JSON.

Strict sequential round-robin order:

```text
pdf_only_1 → json_clean_1 → json_mutated_1 → pdf_mutated_1
pdf_only_2 → json_clean_2 → json_mutated_2 → pdf_mutated_2
pdf_only_3 → json_clean_3 → json_mutated_3 → pdf_mutated_3
```

Each completed generation is copied to `outputs/` and locally evaluated before the next model call. Progress is atomically written to `results/scores/bohnanza/source_experiment/progress.json`. A quota-like error stops the launcher; rerunning skips completed generations. After all generations, 36 neutral judges run strictly sequentially and are also resumable.

## Preregistered source mutations

JSON:

- J1: two Ackerbohnen award two coins instead of field 3;
- J2: Weinbrand thresholds become `2/4/6/8` instead of `4/7/9/11`;
- J3: the cross-variant catalog falsely states that all 157 listed cards are simultaneously active in the Ackerbohnen variant.

PDF:

- P1: only the active player may harvest;
- P2: only the active player draws three cards in variant phase 4;
- P3: hand sorting is explicitly allowed.

The hidden mutation registry maps all six mutations to frozen deterministic scenarios. The current suite has 37 scenarios; the added hand-sort prohibition scenario passes against the prior canonical implementation.

## Frozen evaluator hashes

See `checks/mutations/bohnanza_source_experiment.json` for the authoritative hash map and mutation-to-scenario mapping.

- rubric: `bohnanza-source-experiment-2026-07-18`
- scenarios: 37
- suite: `b4379824582b08eba24b3262ab593d01fdb078dbd6a483963ac36bdf2e1f7265`
- adapter: `e480e6ffa83602745c860ab7f821ddf1996c82af0dc7397ec32d3c36bdcc66bb`
- canonical PDF: `11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d`
- canonical JSON: `52ff2e99097389173165badc8176b64c35b11c83b8c9d4f0ee854d61e6ee0f46`
- mutated PDF: `224d2bdd529f6bc712e2ef9e8edfc42a9f53900f7974f535d4c7ca59c4f31b8c`
- mutated JSON: `1d1c5614c689a39a4019057673c1cad77c8ad2dc564dc2c5b4f7bb08c8ae721a`

## Validation

- 27 preparation/unit tests passed.
- Experiment dry-run confirms the 12-call round-robin order.
- Current implementation against the frozen suite: 36 PASS, 1 known FAIL (out-of-turn harvesting), 0 crashes, full evaluated coverage.
- Mutated PDF has 11 pages and contains all three exact preregistered replacement rules.
- The canonical JSON is byte-for-byte identical to the user-supplied `bohnanza_bohnenwerte.json`; the mutated JSON keeps the same schema and changes only the three preregistered logical fields.

## Isolation canary — failed

Codex was launched in a fresh temporary packet with `workspace-write`. A canary file existed outside that packet in the repository. The probe explicitly attempted the external path and returned:

```text
READ:BOARD_BENCH_CANARY_7d94c1e2
```

The raw response, events, and usage are preserved under `preflight/canary_*`. Therefore `workspace-write` restricts writes but does **not** provide hard read isolation on this Windows host. The prior logical controls still apply (`--ephemeral`, ignored user/project rules, opaque temp packet, no evaluator files in the packet, fresh session, audited event log), but a model could technically read repository tests if it deliberately discovered their absolute paths.

## Decision required before final Go

Choose one:

1. **Hard isolation:** run Codex inside a container/OS boundary where only the source packet is mounted. Docker is installed but its daemon was not running during preflight. This needs setup and a second canary.
2. **Audited logical isolation:** proceed with the temp packet and `workspace-write`, explicitly report that repository reads were technically possible, and audit every event log for external paths.

The launcher remains in dry-run state until this decision and the user's final Go.
